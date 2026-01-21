import argparse
from typing import Dict, List

import pandas as pd

from .db import get_connection, init_db


REQUIRED_COLUMNS_ALIASES: Dict[str, List[str]] = {
	"project_id": ["project", "project_id"],
	"subject_id": ["subject", "subject_id", "patient_id"],
	"indication": ["indication", "condition"],
	"treatment": ["treatment"],
	"response": ["response"],
	"gender": ["gender", "sex"],
	"sample_id": ["sample", "sample_id"],
	"sample_type": ["sample_type"],
	"time_from_treatment_start": ["time_from_treatment_start"],
}


EXPECTED_POPULATIONS = [
	"b_cell",
	"cd8_t_cell",
	"cd4_t_cell",
	"nk_cell",
	"monocyte",
]


def _resolve_columns(df: pd.DataFrame) -> Dict[str, str]:

	mapping: Dict[str, str] = {}
	lower_cols = {c.lower(): c for c in df.columns}
	for logical, aliases in REQUIRED_COLUMNS_ALIASES.items():
		found = None
		for alias in aliases:
			if alias.lower() in lower_cols:
				found = lower_cols[alias.lower()]
				break
		if found is None:
			raise ValueError(f"Missing required column for '{logical}'. Aliases: {aliases}")
		mapping[logical] = found

	return mapping


def _detect_population_columns(df: pd.DataFrame) -> List[str]:

	lower_cols = {c.lower(): c for c in df.columns}
	populations: List[str] = []
	for expected in EXPECTED_POPULATIONS:
		if expected.lower() in lower_cols:
			populations.append(lower_cols[expected.lower()])
		else:
			raise ValueError(f"Missing expected immune population column '{expected}' in CSV")
	return populations


def load_csv_to_db(csv_path: str, db_path: str) -> None:

	df = pd.read_csv(csv_path)
	column_map = _resolve_columns(df)
	population_cols = _detect_population_columns(df)

	conn = get_connection(db_path)
	init_db(conn)

	cur = conn.cursor()

	try:
		cur.execute("BEGIN")

		projects = sorted(df[column_map["project_id"]].unique())
		cur.executemany(
			"INSERT OR IGNORE INTO projects (project_id) VALUES (?)",
			[(p,) for p in projects],
		)

		subjects_records = {}
		for _, row in df.iterrows():
			subject_id = str(row[column_map["subject_id"]])
			if subject_id in subjects_records:
				continue
			project_id = str(row[column_map["project_id"]])
			indication = str(row[column_map["indication"]])
			treatment = str(row[column_map["treatment"]])
			response_val = row[column_map["response"]]
			response = str(response_val) if pd.notna(response_val) and str(response_val) != "" else None
			gender = str(row[column_map["gender"]])
			subjects_records[subject_id] = (
				subject_id,
				project_id,
				indication,
				treatment,
				response,
				gender,
			)

		cur.executemany(
			"""
			INSERT OR IGNORE INTO subjects (
				subject_id, project_id, indication, treatment, response, gender
			) VALUES (?, ?, ?, ?, ?, ?)
			""",
			list(subjects_records.values()),
		)

		samples_records = {}
		for _, row in df.iterrows():
			sample_id = str(row[column_map["sample_id"]])
			if sample_id in samples_records:
				continue
			subject_id = str(row[column_map["subject_id"]])
			sample_type = str(row[column_map["sample_type"]])
			time_from_start = int(row[column_map["time_from_treatment_start"]])
			samples_records[sample_id] = (
				sample_id,
				subject_id,
				sample_type,
				time_from_start,
			)

		cur.executemany(
			"""
			INSERT OR IGNORE INTO samples (
				sample_id, subject_id, sample_type, time_from_treatment_start
			) VALUES (?, ?, ?, ?)
			""",
			list(samples_records.values()),
		)

		cur.executemany(
			"INSERT OR IGNORE INTO populations (name) VALUES (?)",
			[(name,) for name in EXPECTED_POPULATIONS],
		)

		cur.execute("SELECT population_id, name FROM populations")
		pop_id_map = {name: pid for pid, name in cur.fetchall()}

		cell_count_rows = []
		for _, row in df.iterrows():
			sample_id = str(row[column_map["sample_id"]])
			for expected, col in zip(EXPECTED_POPULATIONS, population_cols):
				value = int(row[col])
				population_id = pop_id_map[expected]
				cell_count_rows.append((sample_id, population_id, value))

		cur.executemany(
			"""
			INSERT OR REPLACE INTO cell_counts (
				sample_id, population_id, count
			) VALUES (?, ?, ?)
			""",
			cell_count_rows,
		)

		conn.commit()
	except Exception:
		conn.rollback()
		raise
	finally:
		conn.close()


def _parse_args() -> argparse.Namespace:

	parser = argparse.ArgumentParser(description="Load cell count CSV into SQLite database")
	parser.add_argument("--csv", required=True, help="Path to cell-count.csv")
	parser.add_argument("--db", required=True, help="Path to SQLite database file to create or update")
	return parser.parse_args()


def main() -> None:

	args = _parse_args()
	load_csv_to_db(args.csv, args.db)


if __name__ == "__main__":
	main()
