Teiko Technical – AI Coding Agent Instructions (Authoritative)

You are an AI coding agent continuing work on this repository after the Streamlit dashboard entrypoint has been tested and runs successfully:

streamlit run dashboard/app.py


Your task is to complete and polish the project end-to-end so it fully satisfies the Teiko Technical assignment (Parts 1–4), is reproducible in GitHub Codespaces, and is suitable for submission.

Do not ask clarification questions. Inspect the repository and proceed.

1. Project Overview

This repository implements a biomedical data analysis platform for immune cell profiling in cancer treatment studies.

The platform:

Ingests immune cell count data from a longitudinal clinical study

Stores it in a normalized SQLite relational database

Computes population-level frequencies and statistical comparisons

Presents results in an interactive Streamlit dashboard

Biological Context

Sample type: PBMC (Peripheral Blood Mononuclear Cells)

Immune populations:

b_cell

cd8_t_cell

cd4_t_cell

nk_cell

monocyte

Treatments:

miraclib

phauximab

none

Indications:

melanoma

carcinoma

healthy

Timepoints:

baseline (day 0)

day 7

day 14

2. Architecture (Do Not Change)
Data Pipeline

Source CSV: data/cell-count.csv (≈10,500 samples)

Database: SQLite (cellcounts.sqlite)

Query Layer: src/queries.py

Analysis Layer: src/analysis.py, src/stats.py

Visualization: Streamlit + Plotly (dashboard/app.py)

Canonical Commands
python -m src.load_db --csv data/cell-count.csv --db cellcounts.sqlite
streamlit run dashboard/app.py


Always use python -m for scripts inside src

The SQLite file is generated, not committed

Paths must be relative (no absolute paths)

3. Required Database Schema (Part 1)

Implement and enforce the following normalized schema in src/db.py:

Tables

projects

project_id TEXT PRIMARY KEY

subjects

subject_id TEXT PRIMARY KEY

project_id TEXT

indication TEXT

treatment TEXT

response TEXT (yes / no)

gender TEXT

FK → projects

samples

sample_id TEXT PRIMARY KEY

subject_id TEXT

sample_type TEXT

time_from_treatment_start INTEGER

FK → subjects

populations

population_id INTEGER PRIMARY KEY AUTOINCREMENT

name TEXT UNIQUE

cell_counts

sample_id TEXT

population_id INTEGER

count INTEGER

PRIMARY KEY (sample_id, population_id)

FK → samples, populations

Indexing (Required)

Add indexes on:

subjects.indication

subjects.treatment

subjects.response

subjects.gender

samples.sample_type

samples.time_from_treatment_start

cell_counts.population_id

Rationale

This schema must:

Scale to hundreds of projects

Support many immune populations without schema changes

Enable efficient cohort filtering and statistical analysis

4. CSV Loader Requirements (Part 1)

In src/load_db.py:

Implement a CLI:

python -m src.load_db --csv data/cell-count.csv --db cellcounts.sqlite

Loader Behavior

Read CSV using pandas

Detect and validate required columns

Support common aliases:

subject / subject_id / patient_id

sample / sample_id

sex / gender

Detect immune population columns dynamically:

Expected: b_cell, cd8_t_cell, cd4_t_cell, nk_cell, monocyte

Insert data using one transaction

Insert populations once, map name → population_id

Fail fast with a clear error if required columns are missing

5. Part 2 – Cell Population Frequency Table

Implement in src/queries.py:

get_frequency_table(conn, filters: dict | None) -> pd.DataFrame

Output (Long Format)

Each row represents one population in one sample:

sample	total_count	population	count	percentage

Where:

total_count = sum of all 5 populations per sample

percentage = (count / total_count) * 100

Filtering

Support optional filters:

project

indication

treatment

response

gender

sample_type

time_from_treatment_start

6. Part 3 – Statistical Analysis (Responder vs Non-Responder)
Scope

Only include:

indication == "melanoma"

treatment == "miraclib"

sample_type == "PBMC"

Statistical Requirements

Use relative frequencies (%)

Compare responders vs non-responders

Perform Welch’s t-test per population

Apply Benjamini–Hochberg FDR correction

Implementation

src/stats.py

Welch t-test

FDR correction (statsmodels)

src/analysis.py

Orchestrates filtering + stats

Returns:

long dataframe (for plotting)

stats summary dataframe

Dashboard (Required)

In dashboard/app.py:

Boxplots (Plotly) per population

Split by response (yes / no)

Table showing:

means

p-values

adjusted p-values

significance flag (α = 0.05)

7. Part 4 – Subset Analysis (Baseline Effects)

Query the database to identify:

Filter

indication == "melanoma"

sample_type == "PBMC"

treatment == "miraclib"

time_from_treatment_start == 0

Required Outputs

Number of samples per project

Number of subjects:

responders vs non-responders

Number of subjects:

males vs females

Among melanoma males:

average B cell count for responders at baseline

display with two significant figures

raw counts (not percentages)

All queries must come from SQLite.

8. Dashboard Requirements

The Streamlit app must include:

Tabs

Data Overview

Frequency table (Part 2)

Downloadable CSV

Responder vs Non-Responder

Boxplots + statistics (Part 3)

Subset Analysis

Exact counts requested in Part 4

Performance

Cache expensive operations using @st.cache_data

Do not reload CSV inside the dashboard

9. Submission Polish
README.md (Required Sections)

Quickstart (exact commands)

Schema explanation + scaling rationale

Code structure overview

Dashboard usage notes

Repo Hygiene

Add .gitignore:

.venv/

__pycache__/

*.sqlite

outputs/

Friendly error messages

Deterministic outputs

10. Final Verification Checklist

The following must work from a clean environment:

pip install -r requirements.txt
python -m src.load_db --csv data/cell-count.csv --db cellcounts.sqlite
streamlit run dashboard/app.py


The dashboard must:

Show Part 2 frequency table

Show Part 3 plots + stats with significant populations identified

Show Part 4 counts and B-cell average

Read only from SQLite, not directly from CSV

Proceed to implement all missing or incomplete components now.
Make code changes directly, then summarize what was changed and how to verify.