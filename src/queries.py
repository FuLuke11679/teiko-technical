from typing import Any, Dict, Iterable, List, Optional

import pandas as pd


FILTER_COLUMN_MAPPING = {
	"project": "pr.project_id",
	"indication": "subj.indication",
	"treatment": "subj.treatment",
	"response": "subj.response",
	"gender": "subj.gender",
	"sample_type": "s.sample_type",
	"time_from_treatment_start": "s.time_from_treatment_start",
}


def _build_filters(filters: Optional[Dict[str, Any]]) -> tuple[str, List[Any]]:

	if not filters:
		return "", []

	clauses: List[str] = []
	params: List[Any] = []
	for key, value in filters.items():
		if key not in FILTER_COLUMN_MAPPING or value is None:
			continue
		column = FILTER_COLUMN_MAPPING[key]
		clauses.append(f"{column} = ?")
		params.append(value)
	if not clauses:
		return "", []
	return " WHERE " + " AND ".join(clauses), params


def get_frequency_table(conn, filters: Optional[Dict[str, Any]] = None) -> pd.DataFrame:

	where_sql, params = _build_filters(filters)

	query = f"""
		WITH sample_totals AS (
			SELECT
				cc.sample_id,
				SUM(cc.count) AS total_count
			FROM cell_counts cc
			GROUP BY cc.sample_id
		)
		SELECT
			s.sample_id AS sample,
			st.total_count,
			p.name AS population,
			cc.count,
			subj.response
		FROM cell_counts cc
		JOIN samples s ON cc.sample_id = s.sample_id
		JOIN subjects subj ON s.subject_id = subj.subject_id
		JOIN projects pr ON subj.project_id = pr.project_id
		JOIN populations p ON cc.population_id = p.population_id
		JOIN sample_totals st ON st.sample_id = s.sample_id
		{where_sql}
	"""

	df = pd.read_sql_query(query, conn, params=params)
	if df.empty:
		return df
	df["percentage"] = df["count"] / df["total_count"] * 100.0
	return df


def get_baseline_subset_metrics(conn) -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame, float | None]:

	base_filters = {
		"indication": "melanoma",
		"treatment": "miraclib",
		"sample_type": "PBMC",
		"time_from_treatment_start": 0,
	}

	where_sql, params = _build_filters(base_filters)

	samples_per_project = pd.read_sql_query(
		f"""
		SELECT pr.project_id AS project, COUNT(*) AS n_samples
		FROM samples s
		JOIN subjects subj ON s.subject_id = subj.subject_id
		JOIN projects pr ON subj.project_id = pr.project_id
		{where_sql}
		GROUP BY pr.project_id
		ORDER BY pr.project_id
		""",
		conn,
		params=params,
	)

	subjects_by_response = pd.read_sql_query(
		f"""
		SELECT subj.response AS response, COUNT(DISTINCT subj.subject_id) AS n_subjects
		FROM samples s
		JOIN subjects subj ON s.subject_id = subj.subject_id
		JOIN projects pr ON subj.project_id = pr.project_id
		{where_sql}
		GROUP BY subj.response
		ORDER BY subj.response
		""",
		conn,
		params=params,
	)

	subjects_by_gender = pd.read_sql_query(
		f"""
		SELECT subj.gender AS gender, COUNT(DISTINCT subj.subject_id) AS n_subjects
		FROM samples s
		JOIN subjects subj ON s.subject_id = subj.subject_id
		JOIN projects pr ON subj.project_id = pr.project_id
		{where_sql}
		GROUP BY subj.gender
		ORDER BY subj.gender
		""",
		conn,
		params=params,
	)

	male_filters = {"indication": "melanoma", "gender": "M", "response": "yes", "time_from_treatment_start": 0}
	male_where, male_params = _build_filters(male_filters)

	bcell_df = pd.read_sql_query(
		f"""
		SELECT cc.count AS b_cell_count
		FROM cell_counts cc
		JOIN populations p ON cc.population_id = p.population_id
		JOIN samples s ON cc.sample_id = s.sample_id
		JOIN subjects subj ON s.subject_id = subj.subject_id
		JOIN projects pr ON subj.project_id = pr.project_id
		{male_where} AND p.name = 'b_cell'
		""",
		conn,
		params=male_params,
	)

	avg_bcell = float(bcell_df["b_cell_count"].mean()) if not bcell_df.empty else None

	return samples_per_project, subjects_by_response, subjects_by_gender, avg_bcell


__all__ = [
	"get_frequency_table",
	"get_baseline_subset_metrics",
]
