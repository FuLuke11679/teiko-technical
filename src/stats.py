from typing import Tuple

import numpy as np
import pandas as pd
from scipy import stats as sp_stats
from statsmodels.stats.multitest import multipletests


def welch_ttest_by_population(freq_df: pd.DataFrame) -> pd.DataFrame:

	data = freq_df.copy()
	data = data[data["response"].isin(["yes", "no"])]
	if data.empty:
		return pd.DataFrame(
			columns=["population", "mean_yes", "mean_no", "p_value", "p_adj", "significant"]
		)

	populations = sorted(data["population"].unique())
	rows = []
	for pop in populations:
		sub = data[data["population"] == pop]
		yes_vals = sub.loc[sub["response"] == "yes", "percentage"].astype(float)
		no_vals = sub.loc[sub["response"] == "no", "percentage"].astype(float)
		if len(yes_vals) < 2 or len(no_vals) < 2:
			p_val = np.nan
		else:
			_, p_val = sp_stats.ttest_ind(yes_vals, no_vals, equal_var=False, nan_policy="omit")
		rows.append(
			{
				"population": pop,
				"mean_yes": float(yes_vals.mean()) if len(yes_vals) else np.nan,
				"mean_no": float(no_vals.mean()) if len(no_vals) else np.nan,
				"p_value": float(p_val) if not np.isnan(p_val) else np.nan,
			}
		)

	stats_df = pd.DataFrame(rows)
	valid = stats_df["p_value"].notna()
	if valid.any():
		rejected, p_adj, _, _ = multipletests(stats_df.loc[valid, "p_value"], alpha=0.05, method="fdr_bh")
		stats_df.loc[valid, "p_adj"] = p_adj
		stats_df.loc[valid, "significant"] = rejected
	stats_df["p_adj"] = stats_df["p_adj"].astype(float)
	stats_df["significant"] = stats_df["significant"].fillna(False).astype(bool)
	return stats_df


__all__ = ["welch_ttest_by_population"]
