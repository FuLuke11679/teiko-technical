# Teiko Technical – Immune Cell Profiling Dashboard

## Quickstart

1. Create and activate a virtual environment (optional but recommended):

	 ```bash
	 python -m venv .venv
	 source .venv/bin/activate  # macOS / Linux
	 # .venv\Scripts\activate  # Windows
	 ```

2. Install dependencies:

	 ```bash
	 pip install -r requirements.txt
	 ```

3. Load the CSV data into SQLite:

	 ```bash
	 python -m src.load_db --csv data/cell-count.csv --db cellcounts.sqlite
	 ```

4. Launch the Streamlit dashboard:

	 ```bash
	 streamlit run dashboard/app.py
	 ```

## Schema and Scaling Rationale

The platform uses a normalized SQLite schema defined in `src/db.py`:

- `projects(project_id)` – study or trial identifier
- `subjects(subject_id, project_id, indication, treatment, response, gender)` – patient-level metadata
- `samples(sample_id, subject_id, sample_type, time_from_treatment_start)` – longitudinal samples (e.g., day 0, 7, 14 PBMC)
- `populations(population_id, name)` – immune cell populations (e.g., `b_cell`, `cd8_t_cell`)
- `cell_counts(sample_id, population_id, count)` – raw cell counts per population per sample

This design:

- Scales to hundreds of projects without changing the schema
- Supports additional immune populations by inserting rows into `populations`
- Enables efficient cohort filtering via indexes on indication, treatment, response, gender, sample_type, time_from_treatment_start, and population_id

## Code Structure Overview

- `src/db.py` – SQLite connection helper and schema creation (tables + indexes)
- `src/load_db.py` – CLI loader:
	- Reads `data/cell-count.csv` with pandas
	- Resolves column aliases (e.g., `subject` / `subject_id` / `patient_id`, `sex` / `gender`)
	- Detects immune population columns (`b_cell`, `cd8_t_cell`, `cd4_t_cell`, `nk_cell`, `monocyte`)
	- Inserts projects, subjects, samples, populations, and cell counts inside a single transaction
- `src/queries.py` – Query layer:
	- `get_frequency_table(conn, filters)` – returns long-format cell frequency table per sample and population
	- `get_baseline_subset_metrics(conn)` – computes counts and averages for the baseline subset analysis
- `src/stats.py` – Statistical utilities:
	- Welch’s t-test per population (responders vs non-responders)
	- Benjamini–Hochberg FDR correction
- `src/analysis.py` – Orchestration:
	- `responder_vs_nonresponder_analysis(conn)` – filters melanoma PBMC miraclib cohort and runs statistics
	- `baseline_subset_analysis(conn)` – wraps baseline queries for the dashboard
- `dashboard/app.py` – Streamlit + Plotly dashboard implementation

## Dashboard Usage

The dashboard reads exclusively from the SQLite database (not directly from CSV). It exposes three tabs:

- **Data Overview**
	- Displays the full population frequency table
	- Provides a CSV download of the table
- **Responder vs Non-Responder**
	- Restricts to melanoma patients treated with miraclib (PBMC samples)
	- Shows boxplots of relative frequencies (%) per population, split by response (yes/no)
	- Displays a statistics table with group means, p-values, FDR-adjusted p-values, and a significance level (α = 0.05)
- **Subset Analysis**
	- Filters to melanoma, PBMC, miraclib, baseline (time_from_treatment_start = 0)
	- Shows number of samples per project
	- Counts subjects by response (yes/no) and gender (M/F)
	- Reports the average B cell count for male responders at baseline

Expensive queries and computations are cached with `@st.cache_data` to keep the dashboard responsive.
