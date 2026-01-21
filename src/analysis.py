from typing import Any, Dict, Tuple

import pandas as pd

from . import queries
from .stats import welch_ttest_by_population


def responder_vs_nonresponder_analysis(conn) -> Tuple[pd.DataFrame, pd.DataFrame]:

	filters: Dict[str, Any] = {
		"indication": "melanoma",
		"treatment": "miraclib",
		"sample_type": "PBMC",
	}
	freq_df = queries.get_frequency_table(conn, filters=filters)
	if freq_df.empty:
		return freq_df, pd.DataFrame(
			columns=["population", "mean_yes", "mean_no", "p_value", "p_adj", "significant"]
		)
	stats_df = welch_ttest_by_population(freq_df)
	return freq_df, stats_df


def baseline_subset_analysis(conn):

	return queries.get_baseline_subset_metrics(conn)


__all__ = [
	"responder_vs_nonresponder_analysis",
	"baseline_subset_analysis",
]
