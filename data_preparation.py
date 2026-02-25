#!/usr/bin/env python3
"""
data_preparation.py — STEP 1: Data Preparation (ML & Analytics Ready)

Loads raw Excel log files for products and workers, standardises columns,
parses datetimes, cleans missing values / duplicates, engineers analytical
features, and writes prepared CSVs.

Product files:
  - ALGIRIN.xlsx             (product ALGIRIN / SUKL 3167C-2)
  - Canesten crm der 1x50 g (tuba Al).xlsx  (product Canesten / SUKL 4975D)

Worker / Employee files:
  - Employee_Input_Log 1.xlsx  (employee 1)
  - Employee_Input_Log 2.xlsx  (employee 2)

Outputs:
  - prepared_products.csv
  - prepared_workers.csv
"""

import os
import sys
import warnings
from pathlib import Path

import numpy as np
import pandas as pd

warnings.filterwarnings("ignore")

# ---------------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------------
BASE_DIR = Path(__file__).resolve().parent

PRODUCT_FILES = [
    BASE_DIR / "ALGIRIN.xlsx",
    BASE_DIR / "Canesten crm der 1x50 g (tuba Al).xlsx",
]

WORKER_FILES = [
    BASE_DIR / "Employee_Input_Log 1.xlsx",
    BASE_DIR / "Employee_Input_Log 2.xlsx",
]

OUTPUT_PRODUCTS = BASE_DIR / "prepared_products.csv"
OUTPUT_WORKERS = BASE_DIR / "prepared_workers.csv"

# Column renaming maps -------------------------------------------------------
# Product files share 19 common columns; the 20th is a SUKL code column whose
# name differs per file.  We rename everything to lowercase snake_case.
PRODUCT_COLUMN_MAP = {
    "Sklad": "warehouse",
    "Zdrojová pozícia": "source_position",
    "Cieľová pozícia": "target_position",
    "Proces": "process",
    "Začiatok": "start_time",
    "Koniec": "end_time",
    "Čas[sek]": "duration_sec",
    "Pracovník": "worker",
    "Zdrojová LP": "source_lp",
    "Cieľová  LP": "target_lp",      # note: double space in original
    "Číslo produktu": "product_number",
    "Šarža": "batch",
    "Exspirácia": "expiration",
    "Množstvo [ks]": "quantity_pcs",
    "Nákupná objednávka": "purchase_order",
    "Predajná objednávka": "sales_order",
    "Riadok obj.": "order_line",
    "Zdrojová MLP": "source_mlp",
    "Cieľová MLP": "target_mlp",
}

WORKER_COLUMN_MAP = {
    "Sklad": "warehouse",
    "Employee ID": "employee_id",
    "Employee Name": "employee_name",
    "Device": "device",
    "Equipment": "equipment",
    "Solution Environment": "solution_environment",
    "Prompt Date": "prompt_date",
    "Input Date": "input_date",
    "Dialog Type": "dialog_type",
    "Screen Heading": "screen_heading",
    "Screen Text": "screen_text",
    "System Message": "system_message",
    "Dialog Prompt": "dialog_prompt",
    "Dialog Field": "dialog_field",
    "Screen Options": "screen_options",
    "User Input": "user_input",
    "JSON Text": "json_text",
}


# ===========================================================================
# Utility helpers
# ===========================================================================

def _report(msg: str) -> None:
    """Console logger helper."""
    print(f"  ▸ {msg}")


def _report_missing(df: pd.DataFrame, label: str) -> None:
    """Print a missing-value summary for a DataFrame."""
    missing = df.isnull().sum()
    missing = missing[missing > 0]
    if missing.empty:
        _report(f"[{label}] No missing values detected.")
    else:
        _report(f"[{label}] Missing values per column:")
        for col, cnt in missing.items():
            pct = cnt / len(df) * 100
            _report(f"    {col}: {cnt:,} ({pct:.1f}%)")


def _report_duplicates(df: pd.DataFrame, label: str) -> int:
    """Report and return the number of duplicate rows."""
    n = df.duplicated().sum()
    _report(f"[{label}] Duplicate rows: {n:,}")
    return n


# ===========================================================================
# PRODUCT data: load, clean, feature-engineer
# ===========================================================================

def load_product_files(file_paths: list[Path]) -> pd.DataFrame:
    """Load one or more product xlsx files and concatenate them."""
    frames = []
    for fp in file_paths:
        _report(f"Loading {fp.name}  …")
        df = pd.read_excel(fp, sheet_name="Sheet1")

        # Identify the SUKL column (the last one, whose name differs per file)
        sukl_col = [c for c in df.columns if c.startswith("SUKL")]
        if sukl_col:
            # Extract the SUKL code value from the column name itself as a
            # product label, then drop the (entirely-null) column.
            product_label = sukl_col[0].replace("SUKL", "").strip()
            df["product_label"] = product_label
            df.drop(columns=sukl_col, inplace=True)

        # Rename shared columns
        df.rename(columns=PRODUCT_COLUMN_MAP, inplace=True)

        # Tag the source file
        df["source_file"] = fp.name

        frames.append(df)
        _report(f"  → {len(df):,} rows loaded.")

    combined = pd.concat(frames, ignore_index=True)
    _report(f"Combined product rows: {len(combined):,}")
    return combined


def clean_product_data(df: pd.DataFrame) -> pd.DataFrame:
    """Parse types, coerce datetimes, handle missing values, remove dups."""

    # -- Datetime columns -----------------------------------------------------
    for col in ("start_time", "end_time"):
        df[col] = pd.to_datetime(df[col], errors="coerce", infer_datetime_format=True)

    # Expiration may contain sentinel "1/1/1900"; parse then replace junk
    df["expiration"] = pd.to_datetime(df["expiration"], errors="coerce", infer_datetime_format=True)
    sentinel_mask = df["expiration"] < pd.Timestamp("2000-01-01")
    _report(f"Expiration sentinel dates (< 2000) replaced with NaT: {sentinel_mask.sum():,}")
    df.loc[sentinel_mask, "expiration"] = pd.NaT

    # -- Numeric columns -------------------------------------------------------
    df["duration_sec"] = pd.to_numeric(df["duration_sec"], errors="coerce").fillna(0).astype(int)
    df["quantity_pcs"] = pd.to_numeric(df["quantity_pcs"], errors="coerce").fillna(0).astype(int)
    df["purchase_order"] = pd.to_numeric(df["purchase_order"], errors="coerce")
    df["order_line"] = pd.to_numeric(df["order_line"], errors="coerce")

    # -- Missing-value report & handling ----------------------------------------
    _report_missing(df, "products")

    # For order-related columns that are structurally optional (purchase_order,
    # sales_order, order_line, source_mlp, target_mlp, source_lp, target_lp,
    # source_position, target_position), NaN is acceptable and meaningful
    # ("not applicable for this process type").  We leave them as-is.

    # -- Duplicates -------------------------------------------------------------
    n_dup = _report_duplicates(df, "products")
    if n_dup > 0:
        df.drop_duplicates(inplace=True)
        _report(f"  → removed {n_dup:,} duplicate rows.")

    df.reset_index(drop=True, inplace=True)
    return df


def engineer_product_features(df: pd.DataFrame) -> pd.DataFrame:
    """Create time-based and aggregation features for product data."""

    # --- Time-based features from start_time ---------------------------------
    df["date"] = df["start_time"].dt.date
    df["hour"] = df["start_time"].dt.hour
    df["day_of_week"] = df["start_time"].dt.dayofweek          # 0=Mon
    df["weekday_name"] = df["start_time"].dt.day_name()
    df["week_number"] = df["start_time"].dt.isocalendar().week.astype(int)
    df["month"] = df["start_time"].dt.month
    df["is_weekend"] = df["day_of_week"].isin([5, 6]).astype(int)

    # --- Operation duration (recomputed from timestamps) ---------------------
    # The raw `duration_sec` column exists; also compute from timestamps and
    # keep the more reliable one.
    df["computed_duration_sec"] = (
        (df["end_time"] - df["start_time"]).dt.total_seconds().clip(lower=0)
    )
    # Use original where available and non-zero; fall back to computed
    df["duration_sec_final"] = np.where(
        df["duration_sec"] > 0,
        df["duration_sec"],
        df["computed_duration_sec"],
    )
    df["duration_min"] = (df["duration_sec_final"] / 60).round(2)

    # --- Per-product activity frequency (operations per product per day) ------
    product_day_freq = (
        df.groupby(["product_label", "date"])
        .size()
        .rename("daily_product_ops_count")
        .reset_index()
    )
    df = df.merge(product_day_freq, on=["product_label", "date"], how="left")

    # --- Per-worker productivity: operations & total quantity per worker/day --
    worker_day = (
        df.groupby(["worker", "date"])
        .agg(
            worker_daily_ops=("process", "count"),
            worker_daily_qty=("quantity_pcs", "sum"),
            worker_daily_duration_sec=("duration_sec_final", "sum"),
        )
        .reset_index()
    )
    df = df.merge(worker_day, on=["worker", "date"], how="left")

    # --- Weekly aggregation: ops per week per product -------------------------
    product_week = (
        df.groupby(["product_label", "week_number"])
        .agg(weekly_product_ops=("process", "count"), weekly_product_qty=("quantity_pcs", "sum"))
        .reset_index()
    )
    df = df.merge(product_week, on=["product_label", "week_number"], how="left")

    # --- Process category encoding (useful for ML) ----------------------------
    df["process_category"] = df["process"].str.split(" - ").str[0].str.strip()

    _report(f"Product features engineered. Final shape: {df.shape}")
    return df


# ===========================================================================
# WORKER data: load, clean, feature-engineer
# ===========================================================================

def load_worker_files(file_paths: list[Path]) -> pd.DataFrame:
    """Load employee input log xlsx files and concatenate."""
    frames = []
    for fp in file_paths:
        _report(f"Loading {fp.name}  …")
        df = pd.read_excel(fp, sheet_name="Sheet1")
        df.rename(columns=WORKER_COLUMN_MAP, inplace=True)
        df["source_file"] = fp.name
        frames.append(df)
        _report(f"  → {len(df):,} rows loaded.")

    combined = pd.concat(frames, ignore_index=True)
    _report(f"Combined worker rows: {len(combined):,}")
    return combined


def clean_worker_data(df: pd.DataFrame) -> pd.DataFrame:
    """Parse types, coerce datetimes, handle missing values, remove dups."""

    # -- Datetime columns -----------------------------------------------------
    for col in ("prompt_date", "input_date"):
        df[col] = pd.to_datetime(df[col], errors="coerce", infer_datetime_format=True)

    # -- Missing-value report --------------------------------------------------
    _report_missing(df, "workers")

    # Structurally optional fields (screen_heading, screen_text, system_message,
    # dialog_prompt, dialog_field, screen_options, user_input) are NaN when
    # not applicable for a given dialog type.  We leave these as-is.

    # -- Duplicates ------------------------------------------------------------
    n_dup = _report_duplicates(df, "workers")
    if n_dup > 0:
        df.drop_duplicates(inplace=True)
        _report(f"  → removed {n_dup:,} duplicate rows.")

    df.reset_index(drop=True, inplace=True)
    return df


def engineer_worker_features(df: pd.DataFrame) -> pd.DataFrame:
    """Create time-based and productivity features for worker data."""

    # --- Time-based features from input_date ---------------------------------
    df["date"] = df["input_date"].dt.date
    df["hour"] = df["input_date"].dt.hour
    df["day_of_week"] = df["input_date"].dt.dayofweek
    df["weekday_name"] = df["input_date"].dt.day_name()
    df["week_number"] = df["input_date"].dt.isocalendar().week.astype(int)
    df["month"] = df["input_date"].dt.month
    df["is_weekend"] = df["day_of_week"].isin([5, 6]).astype(int)

    # --- Response / interaction duration (time between prompt and input) ------
    df["response_time_sec"] = (
        (df["input_date"] - df["prompt_date"]).dt.total_seconds().clip(lower=0)
    )
    df["response_time_min"] = (df["response_time_sec"] / 60).round(4)

    # --- Per-employee daily activity count ------------------------------------
    emp_day = (
        df.groupby(["employee_id", "date"])
        .agg(
            employee_daily_actions=("dialog_type", "count"),
            employee_daily_avg_response_sec=("response_time_sec", "mean"),
            employee_daily_total_response_sec=("response_time_sec", "sum"),
        )
        .reset_index()
    )
    df = df.merge(emp_day, on=["employee_id", "date"], how="left")

    # --- Per-employee weekly activity -----------------------------------------
    emp_week = (
        df.groupby(["employee_id", "week_number"])
        .agg(
            employee_weekly_actions=("dialog_type", "count"),
            employee_weekly_avg_response_sec=("response_time_sec", "mean"),
        )
        .reset_index()
    )
    df = df.merge(emp_week, on=["employee_id", "week_number"], how="left")

    # --- Hourly activity distribution per employee ----------------------------
    emp_hour = (
        df.groupby(["employee_id", "hour"])
        .size()
        .rename("employee_hourly_action_count")
        .reset_index()
    )
    df = df.merge(emp_hour, on=["employee_id", "hour"], how="left")

    # --- Dialog-type frequency per employee -----------------------------------
    emp_dialog = (
        df.groupby(["employee_id", "dialog_type"])
        .size()
        .rename("employee_dialog_type_count")
        .reset_index()
    )
    df = df.merge(emp_dialog, on=["employee_id", "dialog_type"], how="left")

    # --- Session detection: new session if gap > 30 min ----------------------
    df.sort_values(["employee_id", "input_date"], inplace=True)
    df["prev_input_date"] = df.groupby("employee_id")["input_date"].shift(1)
    df["gap_sec"] = (df["input_date"] - df["prev_input_date"]).dt.total_seconds()
    df["new_session"] = ((df["gap_sec"] > 1800) | (df["gap_sec"].isna())).astype(int)
    df["session_id"] = df.groupby("employee_id")["new_session"].cumsum()
    df.drop(columns=["prev_input_date", "gap_sec", "new_session"], inplace=True)

    # --- Device usage count per employee --------------------------------------
    emp_device = (
        df.groupby(["employee_id", "device"])
        .size()
        .rename("employee_device_usage_count")
        .reset_index()
    )
    df = df.merge(emp_device, on=["employee_id", "device"], how="left")

    df.reset_index(drop=True, inplace=True)
    _report(f"Worker features engineered. Final shape: {df.shape}")
    return df


# ===========================================================================
# MAIN
# ===========================================================================

def main() -> None:
    print("=" * 72)
    print("  STEP 1 — Data Preparation")
    print("=" * 72)

    # ---- Products -----------------------------------------------------------
    print("\n── Product Data ──────────────────────────────────────────────")
    products = load_product_files(PRODUCT_FILES)
    products = clean_product_data(products)
    products = engineer_product_features(products)
    products.to_csv(OUTPUT_PRODUCTS, index=False)
    _report(f"Saved → {OUTPUT_PRODUCTS.name}  ({len(products):,} rows, {products.shape[1]} cols)")

    # ---- Workers ------------------------------------------------------------
    print("\n── Worker (Employee) Data ────────────────────────────────────")
    workers = load_worker_files(WORKER_FILES)
    workers = clean_worker_data(workers)
    workers = engineer_worker_features(workers)
    workers.to_csv(OUTPUT_WORKERS, index=False)
    _report(f"Saved → {OUTPUT_WORKERS.name}  ({len(workers):,} rows, {workers.shape[1]} cols)")

    print("\n" + "=" * 72)
    print("  Data preparation complete.")
    print("=" * 72)


if __name__ == "__main__":
    main()
