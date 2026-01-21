import sqlite3
from typing import Optional


def get_connection(db_path: str) -> sqlite3.Connection:

	conn = sqlite3.connect(db_path)
	conn.execute("PRAGMA foreign_keys = ON;")
	return conn


def init_db(conn: sqlite3.Connection) -> None:

	cur = conn.cursor()

	cur.execute(
		"""
		CREATE TABLE IF NOT EXISTS projects (
			project_id TEXT PRIMARY KEY
		);
		"""
	)

	cur.execute(
		"""
		CREATE TABLE IF NOT EXISTS subjects (
			subject_id TEXT PRIMARY KEY,
			project_id TEXT NOT NULL,
			indication TEXT NOT NULL,
			treatment TEXT NOT NULL,
			response TEXT,
			gender TEXT NOT NULL,
			FOREIGN KEY (project_id) REFERENCES projects(project_id)
		);
		"""
	)

	cur.execute(
		"""
		CREATE TABLE IF NOT EXISTS samples (
			sample_id TEXT PRIMARY KEY,
			subject_id TEXT NOT NULL,
			sample_type TEXT NOT NULL,
			time_from_treatment_start INTEGER NOT NULL,
			FOREIGN KEY (subject_id) REFERENCES subjects(subject_id)
		);
		"""
	)

	cur.execute(
		"""
		CREATE TABLE IF NOT EXISTS populations (
			population_id INTEGER PRIMARY KEY AUTOINCREMENT,
			name TEXT UNIQUE NOT NULL
		);
		"""
	)

	cur.execute(
		"""
		CREATE TABLE IF NOT EXISTS cell_counts (
			sample_id TEXT NOT NULL,
			population_id INTEGER NOT NULL,
			count INTEGER NOT NULL,
			PRIMARY KEY (sample_id, population_id),
			FOREIGN KEY (sample_id) REFERENCES samples(sample_id),
			FOREIGN KEY (population_id) REFERENCES populations(population_id)
		);
		"""
	)

	cur.execute(
		"""
		CREATE INDEX IF NOT EXISTS idx_subjects_indication
			ON subjects(indication);
		"""
	)
	cur.execute(
		"""
		CREATE INDEX IF NOT EXISTS idx_subjects_treatment
			ON subjects(treatment);
		"""
	)
	cur.execute(
		"""
		CREATE INDEX IF NOT EXISTS idx_subjects_response
			ON subjects(response);
		"""
	)
	cur.execute(
		"""
		CREATE INDEX IF NOT EXISTS idx_subjects_gender
			ON subjects(gender);
		"""
	)
	cur.execute(
		"""
		CREATE INDEX IF NOT EXISTS idx_samples_sample_type
			ON samples(sample_type);
		"""
	)
	cur.execute(
		"""
		CREATE INDEX IF NOT EXISTS idx_samples_time_from_treatment_start
			ON samples(time_from_treatment_start);
		"""
	)
	cur.execute(
		"""
		CREATE INDEX IF NOT EXISTS idx_cell_counts_population_id
			ON cell_counts(population_id);
		"""
	)

	conn.commit()


__all__ = ["get_connection", "init_db"]
