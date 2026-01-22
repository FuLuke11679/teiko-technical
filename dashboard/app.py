import sqlite3
import sys
from pathlib import Path

import pandas as pd
import plotly.express as px
import streamlit as st


PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
	sys.path.insert(0, str(PROJECT_ROOT))

from src.analysis import baseline_subset_analysis, responder_vs_nonresponder_analysis
from src.db import get_connection
from src.queries import get_frequency_table


DB_DEFAULT_PATH = "cellcounts.sqlite"


def _get_db_path() -> Path:

	return Path(DB_DEFAULT_PATH)


@st.cache_data(show_spinner=False)
def load_frequency_table_cached(db_path: str) -> pd.DataFrame:

	conn = get_connection(db_path)
	try:
		return get_frequency_table(conn, filters=None)
	finally:
		conn.close()


@st.cache_data(show_spinner=False)
def responder_analysis_cached(db_path: str):

	conn = get_connection(db_path)
	try:
		return responder_vs_nonresponder_analysis(conn)
	finally:
		conn.close()


@st.cache_data(show_spinner=False)
def baseline_subset_cached(db_path: str):

	conn = get_connection(db_path)
	try:
		return baseline_subset_analysis(conn)
	finally:
		conn.close()


def _render_data_overview(db_path: str) -> None:

	st.subheader("Cell Population Frequency Table")
	freq_df = load_frequency_table_cached(db_path)
	if freq_df.empty:
		st.info("No data available. Ensure the database has been loaded with the CSV.")
		return

	st.dataframe(freq_df)

	csv_bytes = freq_df.to_csv(index=False).encode("utf-8")
	st.download_button(
		label="Download frequency table as CSV",
		data=csv_bytes,
		file_name="frequency_table.csv",
		mime="text/csv",
	)

	population_order = ["b_cell", "cd4_t_cell", "cd8_t_cell", "nk_cell", "monocyte"]

	st.markdown("### Distribution of Population Frequencies")
	fig = px.histogram(
		freq_df,
		x="percentage",
		facet_col="population",
		marginal="rug",
		nbins=30,
		category_orders={"population": population_order},
		labels={"percentage": "Frequency (%)"},
	)
	fig.update_layout(height=400, margin=dict(l=10, r=10, t=30, b=10))
	st.plotly_chart(fig, use_container_width=True)


def _render_responder_vs_nonresponder(db_path: str) -> None:

	st.subheader("Responder vs Non-Responder Analysis")
	freq_df, stats_df = responder_analysis_cached(db_path)
	if freq_df.empty:
		st.info("No responder/non-responder data available for melanoma patients treated with miraclib.")
		return

	population_order = ["b_cell", "cd4_t_cell", "cd8_t_cell", "nk_cell", "monocyte"]

	st.markdown("### Boxplots By Population")
	fig = px.box(
		freq_df,
		x="response",
		y="percentage",
		color="response",
		facet_col="population",
		category_orders={"population": population_order, "response": ["no", "yes"]},
		labels={"response": "Response", "percentage": "Frequency (%)"},
	)
	fig.update_layout(height=400, margin=dict(l=10, r=10, t=30, b=10))
	st.plotly_chart(fig, use_container_width=True)

	st.markdown("### Statistics Summary (T Test)")
	if not stats_df.empty:
		stats_display = stats_df.copy()

		population_order = ["b_cell", "cd4_t_cell", "cd8_t_cell", "nk_cell", "monocyte"]
		stats_display["population"] = pd.Categorical(
			stats_display["population"],
			categories=population_order,
			ordered=True,
		)
		stats_display = stats_display.sort_values("population")

		stats_display["mean_yes"] = stats_display["mean_yes"].round(2)
		stats_display["mean_no"] = stats_display["mean_no"].round(2)
		stats_display["p_value"] = stats_display["p_value"].map(lambda v: f"{v:.3g}" if pd.notna(v) else "NA")
		stats_display["p_adj"] = stats_display["p_adj"].map(lambda v: f"{v:.3g}" if pd.notna(v) else "NA")
		st.dataframe(stats_display)
	else:
		st.info("No statistical results available (insufficient data for tests).")


def _render_subset_analysis(db_path: str) -> None:

	st.subheader("Baseline Subset Analysis (Melanoma, Miraclib, PBMC, Day 0)")
	samples_per_project, subjects_by_response, subjects_by_gender, avg_bcell = baseline_subset_cached(db_path)

	st.markdown("### Number of Samples per Project")
	if samples_per_project.empty:
		st.info("No baseline samples found for the specified cohort.")
	else:
		st.dataframe(samples_per_project)

	col1, col2 = st.columns(2)
	with col1:
		st.markdown("### Subjects: Responders vs Non-Responders")
		if subjects_by_response.empty:
			st.info("No responder/non-responder information available.")
		else:
			st.dataframe(subjects_by_response)

	with col2:
		st.markdown("### Subjects: Males vs Females")
		if subjects_by_gender.empty:
			st.info("No gender information available.")
		else:
			st.dataframe(subjects_by_gender)

	st.markdown("### Average B cell Count for Male Responders at Baseline")
	if avg_bcell is None:
		st.info("No baseline B cell counts found for male responders.")
	else:
		st.metric("Average B cell count", f"{avg_bcell:.2g}")


def main() -> None:

	st.set_page_config(page_title="Teiko Technical Dashboard", layout="wide")
	st.title("Teiko Technical – Immune Cell Profiling Dashboard")

	db_path = _get_db_path()
	if not db_path.exists():
		st.error(
			f"Database file '{db_path}' not found. "
			"Run 'python -m src.load_db --csv data/cell-count.csv --db cellcounts.sqlite' first."
		)
		return

	tabs = st.tabs([
		"Data Overview",
		"Responder vs Non-Responder",
		"Subset Analysis",
	])

	with tabs[0]:
		_render_data_overview(str(db_path))

	with tabs[1]:
		_render_responder_vs_nonresponder(str(db_path))

	with tabs[2]:
		_render_subset_analysis(str(db_path))


if __name__ == "__main__":
	main()
