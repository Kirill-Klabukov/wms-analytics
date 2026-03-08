<p align="center">
  <img src="https://img.shields.io/badge/python-3.9+-3776AB?style=for-the-badge&logo=python&logoColor=white" />
  <img src="https://img.shields.io/badge/streamlit-1.x-FF4B4B?style=for-the-badge&logo=streamlit&logoColor=white" />
  <img src="https://img.shields.io/badge/plotly-5.x-3F4F75?style=for-the-badge&logo=plotly&logoColor=white" />
  <img src="https://img.shields.io/badge/pandas-2.x-150458?style=for-the-badge&logo=pandas&logoColor=white" />
  <img src="https://img.shields.io/badge/license-MIT-green?style=for-the-badge" />
</p>

<h1 align="center">📦 WMS Analytics Console</h1>

<p align="center">
  <b>End-to-end warehouse data pipeline — from raw Excel logs to a production-grade interactive dashboard.</b><br/>
  Data preparation · Exploratory analytics · Anonymization · Multi-page Streamlit UI
</p>

<p align="center">
  <img src="https://img.shields.io/badge/records-380k+-blue?style=flat-square" />
  <img src="https://img.shields.io/badge/charts-18_static_+_interactive-orange?style=flat-square" />
  <img src="https://img.shields.io/badge/pages-8_dashboard_modules-purple?style=flat-square" />
</p>

---

## Table of Contents

- [Overview](#overview)
- [Features](#features)
- [Project Structure](#project-structure)
- [Quick Start](#quick-start)
- [Pipeline Stages](#pipeline-stages)
  - [1. Data Preparation](#1-data-preparation)
  - [2. Exploratory Analytics](#2-exploratory-analytics)
  - [3. Anonymization](#3-anonymization)
  - [4. Interactive Dashboard](#4-interactive-dashboard)
- [Dashboard Pages](#dashboard-pages)
- [Data Schema](#data-schema)
- [Configuration](#configuration)
- [Requirements](#requirements)
- [License](#license)

---

## Overview

This project processes **warehouse management system (WMS) logs** — product movement records and employee input logs — through a complete analytics pipeline:

```
Raw Excel files  →  Cleaned CSVs  →  Static charts  →  Interactive dashboard
```

**Input:** 4 Excel files (~380 K rows total) from a pharmaceutical warehouse  
**Output:** Prepared datasets, 18 static PNG charts, and a multi-page Streamlit dashboard with dark/light theme, anomaly detection, and CSV export.

---

## Features

| Category | Details |
|:---------|:--------|
| **Data Prep** | Column standardization (Slovak → English), datetime parsing, deduplication, feature engineering (30+ derived columns) |
| **Analytics** | Summary statistics, time-series decomposition, distribution analysis, correlation heatmaps, Z-score & IQR anomaly detection |
| **Anonymization** | 357 real names replaced with fictional ones, employee IDs masked, equipment codes generalized |
| **Dashboard** | 8 dedicated pages, sidebar navigation, contextual filters, dark/light theme toggle, adjustable chart heights, FAQ with glossary |
| **Export** | Filtered data downloadable as CSV directly from the UI |

---

## Project Structure

```
dataanalyza/
├── data_preparation.py      # Stage 1 — Load, clean, engineer features
├── analytics.py             # Stage 2 — EDA, static charts, anomaly detection
├── anonymize.py             # Stage 3 — Replace real names with fictional ones
├── dashboard.py             # Stage 4 — Multi-page Streamlit dashboard (1 170 LOC)
│
├── ALGIRIN.xlsx             # Raw product log — SKU 3167C-2 (13.6 K rows)
├── Canesten crm der *.xlsx  # Raw product log — SKU 4975D   (54.7 K rows)
├── Employee_Input_Log 1.xlsx # Raw employee log — Employee A (234.7 K rows)
├── Employee_Input_Log 2.xlsx # Raw employee log — Employee B  (80.3 K rows)
│
├── prepared_products.csv    # Cleaned product operations   (67 449 rows × 38 cols)
├── prepared_workers.csv     # Cleaned employee actions     (314 428 rows × 36 cols)
│
├── output_charts/           # 18 static PNG visualizations
│   ├── product_*.png        # 9 product-focused charts
│   ├── worker_*.png         # 5 employee-focused charts
│   └── anomaly_*.png        # 4 anomaly detection charts
│
├── .gitignore
└── README.md
```

---

## Quick Start

### 1. Clone & install

```bash
git clone https://github.com/Kirill-Klabukov/wms-analytics.git
cd wms-analytics
pip install -r requirements.txt
```

### 2. Run the full pipeline (optional — prepared CSVs are included)

```bash
python data_preparation.py   # → prepared_products.csv, prepared_workers.csv
python analytics.py          # → output_charts/*.png
python anonymize.py          # → overwrites CSVs with anonymized data
```

### 3. Launch the dashboard

```bash
streamlit run dashboard.py
```

Open **http://localhost:8501** in your browser.

> **Note:** If `streamlit` is not on your PATH (e.g. macOS system Python), use:  
> `python -m streamlit run dashboard.py`

---

## Pipeline Stages

### 1. Data Preparation

**`data_preparation.py`** (414 LOC)

- Loads 4 Excel files with `openpyxl`
- Standardizes Slovak column names to English `snake_case`
- Parses datetime columns with timezone-naive handling
- Removes duplicates (900 product + 545 worker records)
- Engineers 30+ features:
  - Temporal: `hour`, `day_of_week`, `weekday_name`, `week_number`, `month`, `is_weekend`
  - Duration: `computed_duration_sec`, `duration_sec_final`, `duration_min`
  - Aggregates: `daily_product_ops_count`, `worker_daily_ops`, `worker_daily_qty`
  - Weekly: `weekly_product_ops`, `weekly_product_qty`
  - Categories: `process_category`
  - Sessions: `session_id` (30-min gap threshold)

### 2. Exploratory Analytics

**`analytics.py`** (659 LOC)

Generates **18 publication-ready charts** to `output_charts/`:

| Chart | Description |
|:------|:------------|
| `product_daily_ops_timeseries` | Daily operation count trend by product |
| `product_daily_qty_timeseries` | Daily quantity moved by product |
| `product_duration_histogram` | Duration distribution with 99th percentile cap |
| `product_hourly_histogram` | Operations per hour of day |
| `product_process_distribution` | Process type frequency |
| `product_weekday_boxplot` | Ops/day distribution by weekday |
| `product_correlation_heatmap` | Feature correlation matrix |
| `worker_daily_actions_timeseries` | Daily employee actions |
| `worker_hourly_activity` | Hourly activity pattern |
| `worker_dialog_type_bar` | Dialog type breakdown |
| `worker_response_time_histogram` | Response time distribution |
| `worker_productivity_bar` | Employee productivity comparison |
| `worker_weekly_comparison` | Weekly action trend |
| `worker_correlation_heatmap` | Employee feature correlations |
| `anomaly_product_daily_ops` | Operations anomaly detection |
| `anomaly_product_duration_boxplot` | Duration outlier visualization |
| `anomaly_worker_daily_actions` | Employee activity anomalies |
| `anomaly_worker_response_time` | Response time outliers |

### 3. Anonymization

**`anonymize.py`** (215 LOC)

- Maps **357 unique real names** → fictional names
- Employee IDs: `JBEL` → `EMP_A`, `KKLA` → `EMP_B`
- Equipment codes: `FAJBEL` → `FAEMP_A`, `FAKKLA` → `FAEMP_B`
- Cleans `screen_heading` and `json_text` fields (regex replacement)
- Overwrites prepared CSVs in-place

### 4. Interactive Dashboard

**`dashboard.py`** (1 173 LOC)

Multi-page Streamlit application with 8 modules — see next section.

---

## Dashboard Pages

| # | Page | Icon | Description |
|:-:|:-----|:----:|:------------|
| 1 | **Dashboard** | 📊 | Executive overview — 6 KPIs, ops/activity trends, product split donut, top workers bar, process breakdown, hourly heatmap |
| 2 | **Operations** | ⚙️ | Process analytics — daily/weekly toggle, metric selector, process volume bars, duration histogram + box marginal, weekday & hourly patterns |
| 3 | **Products** | 📦 | Product comparison — side-by-side KPI cards, overlaid trends, quantity flow, duration box plots, correlation matrix |
| 4 | **Workforce** | 👷 | Two sub-tabs: *Warehouse Workers* (ranking, drill-down, process mix) and *Employee Input Logs* (actions, response times, dialog types, weekly trends, correlations) |
| 5 | **Anomalies** | 🔍 | Statistical outlier detection — Z-Score / IQR / Combined, configurable thresholds, per-employee charts, duration & response-time outlier tables |
| 6 | **Data Explorer** | 🗂️ | Browse & export — column selector, row count, CSV download for both datasets |
| 7 | **Settings** | ⚡ | Dark/light theme, chart height, anomaly defaults, tips toggle, chart preview |
| 8 | **Help & FAQ** | ❓ | Page descriptions, chart reading guide (8 chart types), filter/navigation/export how-tos, domain glossary |

### Theme Support

| Dark Mode | Light Mode |
|:---------:|:----------:|
| Professional dark UI with blue accent | Clean light theme with clear contrast |

Switch via sidebar buttons (🌙 / ☀️) or the Settings page.

---

## Data Schema

<details>
<summary><b>Product Operations</b> — <code>prepared_products.csv</code> (38 columns)</summary>

| Column | Type | Description |
|:-------|:-----|:------------|
| `warehouse` | str | Warehouse code |
| `source_position` | str | Origin location |
| `target_position` | str | Destination location |
| `process` | str | WMS process type (e.g. "341 - Shipping Detail") |
| `start_time` | datetime | Operation start timestamp |
| `end_time` | datetime | Operation end timestamp |
| `duration_sec` | float | Raw duration in seconds |
| `worker` | str | Anonymized worker name |
| `source_lp` / `target_lp` | str | License plate identifiers |
| `product_number` | str | SKU code |
| `batch` | str | Production batch |
| `expiration` | datetime | Product expiration date |
| `quantity_pcs` | float | Pieces moved |
| `purchase_order` / `sales_order` | str | Order references |
| `product_label` | str | Human-readable product name |
| `date` | date | Extracted date |
| `hour` | int | Hour of day (0–23) |
| `day_of_week` | int | ISO weekday (0=Mon … 6=Sun) |
| `weekday_name` | str | Day name |
| `week_number` | int | ISO week |
| `is_weekend` | bool | Saturday or Sunday |
| `duration_sec_final` | float | Cleaned duration |
| `daily_product_ops_count` | int | Total ops for this product on this day |
| `worker_daily_ops` | int | Worker's total ops on this day |
| `worker_daily_qty` | float | Worker's total quantity on this day |
| `process_category` | str | High-level process grouping |

</details>

<details>
<summary><b>Employee Input Logs</b> — <code>prepared_workers.csv</code> (36 columns)</summary>

| Column | Type | Description |
|:-------|:-----|:------------|
| `warehouse` | str | Warehouse code |
| `employee_id` | str | Anonymized ID (EMP_A, EMP_B) |
| `employee_name` | str | Anonymized name |
| `device` | str | Handheld device identifier |
| `equipment` | str | Anonymized equipment code |
| `prompt_date` | datetime | System prompt timestamp |
| `input_date` | datetime | Employee response timestamp |
| `dialog_type` | str | UI dialog type (LIST, PROMPT, etc.) |
| `screen_heading` | str | Screen title |
| `response_time_sec` | float | Time between prompt and input |
| `employee_daily_actions` | int | Employee's total actions on this day |
| `employee_daily_avg_response_sec` | float | Avg response time that day |
| `employee_weekly_actions` | int | Weekly action count |
| `employee_hourly_action_count` | int | Actions in this hour |
| `session_id` | int | Computed session identifier |

</details>

---

## Configuration

All configuration is available in the **Settings** page at runtime:

| Setting | Options | Default |
|:--------|:--------|:--------|
| Theme | Dark / Light | Dark |
| Chart height | 250–600 px | 400 px |
| Show tips | On / Off | On |
| Anomaly method | Z-Score / IQR / Combined | Z-Score |
| Z-Score threshold | 1.5–4.0 | 2.5 |
| IQR factor | 1.0–3.0 | 1.5 |

---

## Requirements

```
python >= 3.9
pandas >= 1.5
numpy >= 1.21
openpyxl >= 3.0
matplotlib >= 3.5
seaborn >= 0.12
streamlit >= 1.24
plotly >= 5.14
```

Install all at once:

```bash
pip install pandas numpy openpyxl matplotlib seaborn streamlit plotly
```

---

## License

This project is released under the **MIT License**. See [LICENSE](LICENSE) for details.

---

<p align="center">
  <sub>Built with ❤️ using Python, Streamlit & Plotly</sub>
</p>
