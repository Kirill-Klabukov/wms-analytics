#!/usr/bin/env python3
"""
analytics.py — STEP 2: Exploratory Data Analysis & Visualisation

Loads the prepared CSV outputs from data_preparation.py and produces:
  • Summary statistics
  • Daily / weekly grouped analyses
  • Worker productivity comparison
  • Product activity comparison
  • Time-series plots, bar charts, histograms, correlation heatmaps
  • Basic anomaly detection (Z-score + IQR)

All charts are saved as PNG files in an `output_charts/` sub-folder.
"""

import os
import sys
import warnings
from pathlib import Path

import numpy as np
import pandas as pd
import matplotlib
matplotlib.use("Agg")  # non-interactive backend for headless rendering
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
import seaborn as sns

warnings.filterwarnings("ignore")
sns.set_theme(style="whitegrid", palette="muted", font_scale=1.05)

# ---------------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------------
BASE_DIR = Path(__file__).resolve().parent
CHART_DIR = BASE_DIR / "output_charts"
CHART_DIR.mkdir(exist_ok=True)

PRODUCTS_CSV = BASE_DIR / "prepared_products.csv"
WORKERS_CSV = BASE_DIR / "prepared_workers.csv"


# ===========================================================================
# Data loaders
# ===========================================================================

def load_products(path: Path = PRODUCTS_CSV) -> pd.DataFrame:
    """Load prepared product data and parse date columns."""
    df = pd.read_csv(path, low_memory=False)
    for col in ("start_time", "end_time", "expiration"):
        if col in df.columns:
            df[col] = pd.to_datetime(df[col], errors="coerce")
    if "date" in df.columns:
        df["date"] = pd.to_datetime(df["date"], errors="coerce")
    return df


def load_workers(path: Path = WORKERS_CSV) -> pd.DataFrame:
    """Load prepared worker data and parse date columns."""
    df = pd.read_csv(path, low_memory=False)
    for col in ("prompt_date", "input_date"):
        if col in df.columns:
            df[col] = pd.to_datetime(df[col], errors="coerce")
    if "date" in df.columns:
        df["date"] = pd.to_datetime(df["date"], errors="coerce")
    return df


# ===========================================================================
# Summary statistics
# ===========================================================================

def print_summary_statistics(products: pd.DataFrame, workers: pd.DataFrame) -> None:
    """Print descriptive statistics for both datasets."""
    print("\n" + "=" * 72)
    print("  SUMMARY STATISTICS — Products")
    print("=" * 72)
    key_cols = [c for c in (
        "duration_sec_final", "quantity_pcs", "daily_product_ops_count",
        "worker_daily_ops", "worker_daily_qty",
    ) if c in products.columns]
    print(products[key_cols].describe().round(2).to_string())

    print(f"\nProducts per label:\n{products['product_label'].value_counts().to_string()}")
    print(f"\nTop 10 workers by # operations:")
    print(products["worker"].value_counts().head(10).to_string())
    print(f"\nProcess type distribution:")
    print(products["process"].value_counts().to_string())

    print("\n" + "=" * 72)
    print("  SUMMARY STATISTICS — Workers")
    print("=" * 72)
    key_cols = [c for c in (
        "response_time_sec", "employee_daily_actions",
        "employee_daily_avg_response_sec", "employee_weekly_actions",
    ) if c in workers.columns]
    print(workers[key_cols].describe().round(2).to_string())

    print(f"\nEmployees:\n{workers['employee_name'].value_counts().to_string()}")
    print(f"\nDialog type distribution:")
    print(workers["dialog_type"].value_counts().to_string())
    print(f"\nDevice usage:")
    print(workers["device"].value_counts().head(10).to_string())


# ===========================================================================
# Grouped analyses
# ===========================================================================

def grouped_analysis(products: pd.DataFrame, workers: pd.DataFrame) -> None:
    """Print daily / weekly grouped summaries."""
    print("\n" + "=" * 72)
    print("  DAILY / WEEKLY GROUPED ANALYSIS — Products")
    print("=" * 72)

    daily_prod = products.groupby("date").agg(
        total_ops=("process", "count"),
        total_qty=("quantity_pcs", "sum"),
        avg_duration=("duration_sec_final", "mean"),
        unique_workers=("worker", "nunique"),
    ).round(2)
    print("\nDaily product summary (first 15 days):")
    print(daily_prod.head(15).to_string())

    weekly_prod = products.groupby("week_number").agg(
        total_ops=("process", "count"),
        total_qty=("quantity_pcs", "sum"),
        avg_duration=("duration_sec_final", "mean"),
        unique_workers=("worker", "nunique"),
    ).round(2)
    print("\nWeekly product summary:")
    print(weekly_prod.to_string())

    print("\n" + "=" * 72)
    print("  WORKER PRODUCTIVITY COMPARISON")
    print("=" * 72)
    worker_prod = products.groupby("worker").agg(
        total_ops=("process", "count"),
        total_qty=("quantity_pcs", "sum"),
        avg_duration=("duration_sec_final", "mean"),
        active_days=("date", "nunique"),
    ).round(2)
    worker_prod["ops_per_day"] = (worker_prod["total_ops"] / worker_prod["active_days"]).round(1)
    worker_prod.sort_values("total_ops", ascending=False, inplace=True)
    print(worker_prod.to_string())

    print("\n" + "=" * 72)
    print("  PRODUCT ACTIVITY COMPARISON")
    print("=" * 72)
    product_comp = products.groupby("product_label").agg(
        total_ops=("process", "count"),
        total_qty=("quantity_pcs", "sum"),
        avg_duration=("duration_sec_final", "mean"),
        unique_workers=("worker", "nunique"),
        unique_processes=("process", "nunique"),
    ).round(2)
    print(product_comp.to_string())

    print("\n" + "=" * 72)
    print("  DAILY / WEEKLY GROUPED ANALYSIS — Workers")
    print("=" * 72)
    daily_worker = workers.groupby(["employee_name", "date"]).agg(
        total_actions=("dialog_type", "count"),
        avg_response_sec=("response_time_sec", "mean"),
    ).round(2)
    print("\nDaily worker summary (first 20 rows):")
    print(daily_worker.head(20).to_string())

    weekly_worker = workers.groupby(["employee_name", "week_number"]).agg(
        total_actions=("dialog_type", "count"),
        avg_response_sec=("response_time_sec", "mean"),
    ).round(2)
    print("\nWeekly worker summary:")
    print(weekly_worker.to_string())


# ===========================================================================
# Visualisation helpers
# ===========================================================================

def _save(fig: plt.Figure, name: str) -> None:
    """Save a figure and close it."""
    path = CHART_DIR / name
    fig.savefig(path, dpi=150, bbox_inches="tight")
    plt.close(fig)
    print(f"  ✓ Saved {path.name}")


# ===========================================================================
# Product visualisations
# ===========================================================================

def plot_product_daily_timeseries(products: pd.DataFrame) -> None:
    """Time-series: daily operations count per product."""
    daily = (
        products.groupby(["date", "product_label"])
        .size()
        .rename("ops_count")
        .reset_index()
    )
    fig, ax = plt.subplots(figsize=(14, 5))
    for label, grp in daily.groupby("product_label"):
        ax.plot(grp["date"], grp["ops_count"], marker=".", markersize=3, label=label)
    ax.set_title("Daily Operations Count per Product")
    ax.set_xlabel("Date")
    ax.set_ylabel("Number of Operations")
    ax.legend()
    ax.xaxis.set_major_formatter(mdates.DateFormatter("%Y-%m-%d"))
    fig.autofmt_xdate()
    _save(fig, "product_daily_ops_timeseries.png")


def plot_product_daily_quantity_timeseries(products: pd.DataFrame) -> None:
    """Time-series: daily total quantity handled per product."""
    daily = (
        products.groupby(["date", "product_label"])
        .agg(total_qty=("quantity_pcs", "sum"))
        .reset_index()
    )
    fig, ax = plt.subplots(figsize=(14, 5))
    for label, grp in daily.groupby("product_label"):
        ax.plot(grp["date"], grp["total_qty"], marker=".", markersize=3, label=label)
    ax.set_title("Daily Total Quantity Handled per Product")
    ax.set_xlabel("Date")
    ax.set_ylabel("Quantity (pcs)")
    ax.legend()
    ax.xaxis.set_major_formatter(mdates.DateFormatter("%Y-%m-%d"))
    fig.autofmt_xdate()
    _save(fig, "product_daily_qty_timeseries.png")


def plot_product_process_distribution(products: pd.DataFrame) -> None:
    """Bar chart: operation count by process type, split by product."""
    ct = products.groupby(["process", "product_label"]).size().unstack(fill_value=0)
    fig, ax = plt.subplots(figsize=(14, 6))
    ct.plot.barh(ax=ax)
    ax.set_title("Operations by Process Type and Product")
    ax.set_xlabel("Count")
    ax.set_ylabel("Process")
    ax.legend(title="Product")
    _save(fig, "product_process_distribution.png")


def plot_product_hourly_histogram(products: pd.DataFrame) -> None:
    """Histogram: operation start-time distribution by hour."""
    fig, ax = plt.subplots(figsize=(10, 5))
    for label, grp in products.groupby("product_label"):
        ax.hist(grp["hour"], bins=24, range=(0, 24), alpha=0.55, label=label, edgecolor="white")
    ax.set_title("Hourly Activity Distribution (Products)")
    ax.set_xlabel("Hour of Day")
    ax.set_ylabel("Number of Operations")
    ax.set_xticks(range(0, 25))
    ax.legend()
    _save(fig, "product_hourly_histogram.png")


def plot_product_duration_histogram(products: pd.DataFrame) -> None:
    """Histogram: operation duration distribution (capped at 99th pct)."""
    dur = products["duration_sec_final"].dropna()
    cap = dur.quantile(0.99)
    dur = dur[dur <= cap]
    fig, ax = plt.subplots(figsize=(10, 5))
    ax.hist(dur, bins=60, edgecolor="white", color="steelblue")
    ax.set_title("Operation Duration Distribution (≤ 99th percentile)")
    ax.set_xlabel("Duration (seconds)")
    ax.set_ylabel("Count")
    _save(fig, "product_duration_histogram.png")


def plot_worker_productivity_bar(products: pd.DataFrame) -> None:
    """Bar chart: top-15 workers by total operations (from product logs)."""
    worker_ops = (
        products.groupby("worker")
        .agg(total_ops=("process", "count"), total_qty=("quantity_pcs", "sum"))
        .sort_values("total_ops", ascending=False)
        .head(15)
    )
    fig, axes = plt.subplots(1, 2, figsize=(16, 6))

    worker_ops["total_ops"].plot.barh(ax=axes[0], color="teal")
    axes[0].set_title("Top 15 Workers — Total Operations")
    axes[0].set_xlabel("Operations")
    axes[0].invert_yaxis()

    worker_ops["total_qty"].plot.barh(ax=axes[1], color="coral")
    axes[1].set_title("Top 15 Workers — Total Quantity")
    axes[1].set_xlabel("Quantity (pcs)")
    axes[1].invert_yaxis()

    fig.suptitle("Worker Productivity Comparison (Product Logs)", fontsize=13)
    fig.tight_layout(rect=[0, 0, 1, 0.95])
    _save(fig, "worker_productivity_bar.png")


def plot_product_correlation_heatmap(products: pd.DataFrame) -> None:
    """Correlation heatmap of key numeric product features."""
    num_cols = [
        "duration_sec_final", "quantity_pcs", "hour", "day_of_week",
        "week_number", "daily_product_ops_count",
        "worker_daily_ops", "worker_daily_qty", "worker_daily_duration_sec",
        "weekly_product_ops", "weekly_product_qty",
    ]
    num_cols = [c for c in num_cols if c in products.columns]
    corr = products[num_cols].corr()
    fig, ax = plt.subplots(figsize=(12, 10))
    sns.heatmap(corr, annot=True, fmt=".2f", cmap="coolwarm", center=0, ax=ax,
                square=True, linewidths=0.5)
    ax.set_title("Product Features — Correlation Heatmap")
    _save(fig, "product_correlation_heatmap.png")


def plot_product_weekday_boxplot(products: pd.DataFrame) -> None:
    """Box-plot of daily operation counts by weekday."""
    daily = (
        products.groupby(["date", "weekday_name", "day_of_week"])
        .size()
        .rename("ops")
        .reset_index()
        .sort_values("day_of_week")
    )
    order = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]
    order = [d for d in order if d in daily["weekday_name"].unique()]
    fig, ax = plt.subplots(figsize=(10, 5))
    sns.boxplot(data=daily, x="weekday_name", y="ops", order=order, ax=ax, palette="Set2")
    ax.set_title("Daily Operations Distribution by Weekday (Products)")
    ax.set_xlabel("Day of Week")
    ax.set_ylabel("Operations per Day")
    _save(fig, "product_weekday_boxplot.png")


# ===========================================================================
# Worker visualisations
# ===========================================================================

def plot_worker_daily_timeseries(workers: pd.DataFrame) -> None:
    """Time-series: daily action count per employee."""
    daily = (
        workers.groupby(["date", "employee_name"])
        .size()
        .rename("actions")
        .reset_index()
    )
    fig, ax = plt.subplots(figsize=(14, 5))
    for name, grp in daily.groupby("employee_name"):
        ax.plot(grp["date"], grp["actions"], marker=".", markersize=3, label=name)
    ax.set_title("Daily Actions Count per Employee")
    ax.set_xlabel("Date")
    ax.set_ylabel("Number of Actions")
    ax.legend()
    ax.xaxis.set_major_formatter(mdates.DateFormatter("%Y-%m-%d"))
    fig.autofmt_xdate()
    _save(fig, "worker_daily_actions_timeseries.png")


def plot_worker_response_time_histogram(workers: pd.DataFrame) -> None:
    """Histogram: response time distribution per employee (capped @ 99th pct)."""
    fig, ax = plt.subplots(figsize=(10, 5))
    for name, grp in workers.groupby("employee_name"):
        rt = grp["response_time_sec"].dropna()
        cap = rt.quantile(0.99)
        rt = rt[rt <= cap]
        ax.hist(rt, bins=60, alpha=0.55, label=name, edgecolor="white")
    ax.set_title("Response Time Distribution per Employee (≤ 99th pct)")
    ax.set_xlabel("Response Time (seconds)")
    ax.set_ylabel("Count")
    ax.legend()
    _save(fig, "worker_response_time_histogram.png")


def plot_worker_hourly_activity(workers: pd.DataFrame) -> None:
    """Bar chart: hourly activity per employee."""
    hourly = (
        workers.groupby(["employee_name", "hour"])
        .size()
        .rename("actions")
        .reset_index()
    )
    fig, ax = plt.subplots(figsize=(12, 5))
    for name, grp in hourly.groupby("employee_name"):
        ax.bar(grp["hour"] + (0 if name == hourly["employee_name"].unique()[0] else 0.35),
               grp["actions"], width=0.35, label=name, alpha=0.8)
    ax.set_title("Hourly Activity Distribution per Employee")
    ax.set_xlabel("Hour of Day")
    ax.set_ylabel("Total Actions")
    ax.set_xticks(range(0, 25))
    ax.legend()
    _save(fig, "worker_hourly_activity.png")


def plot_worker_dialog_type_bar(workers: pd.DataFrame) -> None:
    """Bar chart: dialog type breakdown per employee."""
    ct = workers.groupby(["dialog_type", "employee_name"]).size().unstack(fill_value=0)
    fig, ax = plt.subplots(figsize=(10, 5))
    ct.plot.barh(ax=ax)
    ax.set_title("Dialog Type Breakdown per Employee")
    ax.set_xlabel("Count")
    ax.set_ylabel("Dialog Type")
    ax.legend(title="Employee")
    _save(fig, "worker_dialog_type_bar.png")


def plot_worker_correlation_heatmap(workers: pd.DataFrame) -> None:
    """Correlation heatmap for numeric worker features."""
    num_cols = [
        "response_time_sec", "hour", "day_of_week", "week_number",
        "employee_daily_actions", "employee_daily_avg_response_sec",
        "employee_daily_total_response_sec", "employee_weekly_actions",
        "employee_weekly_avg_response_sec", "employee_hourly_action_count",
        "employee_dialog_type_count", "session_id",
    ]
    num_cols = [c for c in num_cols if c in workers.columns]
    corr = workers[num_cols].corr()
    fig, ax = plt.subplots(figsize=(12, 10))
    sns.heatmap(corr, annot=True, fmt=".2f", cmap="coolwarm", center=0, ax=ax,
                square=True, linewidths=0.5)
    ax.set_title("Worker Features — Correlation Heatmap")
    _save(fig, "worker_correlation_heatmap.png")


def plot_worker_weekly_comparison(workers: pd.DataFrame) -> None:
    """Grouped bar chart: weekly actions per employee."""
    weekly = (
        workers.groupby(["employee_name", "week_number"])
        .size()
        .rename("actions")
        .reset_index()
    )
    fig, ax = plt.subplots(figsize=(14, 5))
    for name, grp in weekly.groupby("employee_name"):
        ax.bar(grp["week_number"] + (0 if name == weekly["employee_name"].unique()[0] else 0.35),
               grp["actions"], width=0.35, label=name, alpha=0.8)
    ax.set_title("Weekly Actions per Employee")
    ax.set_xlabel("ISO Week Number")
    ax.set_ylabel("Total Actions")
    ax.legend()
    _save(fig, "worker_weekly_comparison.png")


# ===========================================================================
# Anomaly detection
# ===========================================================================

def detect_anomalies_zscore(series: pd.Series, threshold: float = 2.5) -> pd.Series:
    """Return boolean mask where values are anomalous (|z| > threshold)."""
    mean = series.mean()
    std = series.std()
    if std == 0:
        return pd.Series(False, index=series.index)
    z = (series - mean).abs() / std
    return z > threshold


def detect_anomalies_iqr(series: pd.Series, factor: float = 1.5) -> pd.Series:
    """Return boolean mask using the IQR method."""
    q1 = series.quantile(0.25)
    q3 = series.quantile(0.75)
    iqr = q3 - q1
    lower = q1 - factor * iqr
    upper = q3 + factor * iqr
    return (series < lower) | (series > upper)


def anomaly_detection_products(products: pd.DataFrame) -> None:
    """Detect and report anomalies in product data."""
    print("\n" + "=" * 72)
    print("  ANOMALY DETECTION — Products")
    print("=" * 72)

    # 1. Unusually high / low activity days -----------------------------------
    daily_ops = (
        products.groupby("date")
        .size()
        .rename("ops")
        .reset_index()
    )
    daily_ops["anomaly_zscore"] = detect_anomalies_zscore(daily_ops["ops"])
    daily_ops["anomaly_iqr"] = detect_anomalies_iqr(daily_ops["ops"])
    anomalous_days = daily_ops[daily_ops["anomaly_zscore"] | daily_ops["anomaly_iqr"]]
    if anomalous_days.empty:
        print("  No anomalous activity days detected (products).")
    else:
        print(f"\n  Anomalous activity days ({len(anomalous_days)}):")
        print(anomalous_days.to_string(index=False))

    # Plot with anomalies highlighted
    fig, ax = plt.subplots(figsize=(14, 5))
    ax.plot(daily_ops["date"], daily_ops["ops"], marker=".", color="steelblue", label="Normal")
    if not anomalous_days.empty:
        ax.scatter(anomalous_days["date"], anomalous_days["ops"],
                   color="red", s=60, zorder=5, label="Anomaly")
    mean_val = daily_ops["ops"].mean()
    std_val = daily_ops["ops"].std()
    ax.axhline(mean_val, color="gray", linestyle="--", label=f"Mean ({mean_val:.0f})")
    ax.axhline(mean_val + 2.5 * std_val, color="salmon", linestyle=":", label="+2.5σ")
    ax.axhline(max(0, mean_val - 2.5 * std_val), color="salmon", linestyle=":", label="-2.5σ")
    ax.set_title("Daily Product Operations — Anomaly Detection")
    ax.set_xlabel("Date")
    ax.set_ylabel("Operations")
    ax.legend(fontsize=8)
    ax.xaxis.set_major_formatter(mdates.DateFormatter("%Y-%m-%d"))
    fig.autofmt_xdate()
    _save(fig, "anomaly_product_daily_ops.png")

    # 2. Outlier operation durations ------------------------------------------
    dur = products["duration_sec_final"].dropna()
    dur_anomaly_z = detect_anomalies_zscore(dur, threshold=3.0)
    dur_anomaly_iqr = detect_anomalies_iqr(dur, factor=1.5)
    n_outlier_z = dur_anomaly_z.sum()
    n_outlier_iqr = dur_anomaly_iqr.sum()
    print(f"\n  Duration outliers (Z-score > 3):  {n_outlier_z:,}  ({n_outlier_z / len(dur) * 100:.2f}%)")
    print(f"  Duration outliers (IQR × 1.5):    {n_outlier_iqr:,}  ({n_outlier_iqr / len(dur) * 100:.2f}%)")

    # Show top outliers by duration
    outlier_mask = dur_anomaly_z | dur_anomaly_iqr
    if outlier_mask.any():
        top = products.loc[dur[outlier_mask].nlargest(10).index,
                           ["start_time", "worker", "process", "product_label", "duration_sec_final"]]
        print("\n  Top 10 longest outlier operations:")
        print(top.to_string(index=False))

    # Duration box-plot with outliers
    fig, ax = plt.subplots(figsize=(10, 4))
    sns.boxplot(x=products["duration_sec_final"], ax=ax, color="lightblue", fliersize=2)
    ax.set_title("Operation Duration — Box Plot (Outlier View)")
    ax.set_xlabel("Duration (seconds)")
    _save(fig, "anomaly_product_duration_boxplot.png")


def anomaly_detection_workers(workers: pd.DataFrame) -> None:
    """Detect and report anomalies in worker data."""
    print("\n" + "=" * 72)
    print("  ANOMALY DETECTION — Workers")
    print("=" * 72)

    # 1. Unusually high / low activity days per employee ----------------------
    for emp in workers["employee_name"].unique():
        emp_df = workers[workers["employee_name"] == emp]
        daily = emp_df.groupby("date").size().rename("actions").reset_index()
        daily["anomaly_z"] = detect_anomalies_zscore(daily["actions"])
        daily["anomaly_iqr"] = detect_anomalies_iqr(daily["actions"])
        anom = daily[daily["anomaly_z"] | daily["anomaly_iqr"]]
        if anom.empty:
            print(f"\n  [{emp}] No anomalous activity days.")
        else:
            print(f"\n  [{emp}] Anomalous activity days ({len(anom)}):")
            print(anom.to_string(index=False))

    # Plot per-employee anomaly overlay
    fig, axes = plt.subplots(len(workers["employee_name"].unique()), 1,
                              figsize=(14, 4 * len(workers["employee_name"].unique())),
                              sharex=True)
    if not hasattr(axes, "__iter__"):
        axes = [axes]
    for ax, emp in zip(axes, workers["employee_name"].unique()):
        emp_df = workers[workers["employee_name"] == emp]
        daily = emp_df.groupby("date").size().rename("actions").reset_index()
        daily["anomaly"] = detect_anomalies_zscore(daily["actions"]) | detect_anomalies_iqr(daily["actions"])
        ax.plot(daily["date"], daily["actions"], marker=".", color="steelblue")
        anom = daily[daily["anomaly"]]
        if not anom.empty:
            ax.scatter(anom["date"], anom["actions"], color="red", s=50, zorder=5)
        mean_val = daily["actions"].mean()
        std_val = daily["actions"].std()
        ax.axhline(mean_val, color="gray", linestyle="--")
        ax.axhline(mean_val + 2.5 * std_val, color="salmon", linestyle=":")
        ax.axhline(max(0, mean_val - 2.5 * std_val), color="salmon", linestyle=":")
        ax.set_title(f"Daily Actions — {emp}")
        ax.set_ylabel("Actions")
    axes[-1].set_xlabel("Date")
    axes[-1].xaxis.set_major_formatter(mdates.DateFormatter("%Y-%m-%d"))
    fig.autofmt_xdate()
    fig.tight_layout()
    _save(fig, "anomaly_worker_daily_actions.png")

    # 2. Outlier response times -----------------------------------------------
    rt = workers["response_time_sec"].dropna()
    rt_anomaly_z = detect_anomalies_zscore(rt, threshold=3.0)
    rt_anomaly_iqr = detect_anomalies_iqr(rt, factor=1.5)
    n_z = rt_anomaly_z.sum()
    n_iqr = rt_anomaly_iqr.sum()
    print(f"\n  Response-time outliers (Z > 3):   {n_z:,}  ({n_z / len(rt) * 100:.2f}%)")
    print(f"  Response-time outliers (IQR×1.5): {n_iqr:,}  ({n_iqr / len(rt) * 100:.2f}%)")

    top = workers.loc[rt[rt_anomaly_z | rt_anomaly_iqr].nlargest(10).index,
                      ["input_date", "employee_name", "dialog_type", "response_time_sec"]]
    if not top.empty:
        print("\n  Top 10 longest outlier response times:")
        print(top.to_string(index=False))

    fig, ax = plt.subplots(figsize=(10, 4))
    cap99 = rt.quantile(0.99)
    rt_capped = rt[rt <= cap99]
    for emp in workers["employee_name"].unique():
        emp_rt = workers.loc[workers["employee_name"] == emp, "response_time_sec"].dropna()
        emp_rt = emp_rt[emp_rt <= cap99]
        ax.hist(emp_rt, bins=60, alpha=0.5, label=emp, edgecolor="white")
    ax.set_title("Response Time Distribution with Outlier Threshold (≤ 99th pct)")
    ax.set_xlabel("Response Time (sec)")
    ax.set_ylabel("Count")
    ax.legend()
    _save(fig, "anomaly_worker_response_time.png")


# ===========================================================================
# Main orchestrator
# ===========================================================================

def main() -> None:
    print("=" * 72)
    print("  STEP 2 — Analytics & Visualisation")
    print("=" * 72)

    # --- Load data -----------------------------------------------------------
    print("\nLoading prepared CSVs …")
    products = load_products()
    workers = load_workers()
    print(f"  Products: {len(products):,} rows, {products.shape[1]} cols")
    print(f"  Workers:  {len(workers):,} rows, {workers.shape[1]} cols")

    # --- Summary statistics --------------------------------------------------
    print_summary_statistics(products, workers)

    # --- Grouped analyses ----------------------------------------------------
    grouped_analysis(products, workers)

    # --- Visualisations ------------------------------------------------------
    print("\n" + "=" * 72)
    print("  GENERATING CHARTS")
    print("=" * 72)

    # Product charts
    plot_product_daily_timeseries(products)
    plot_product_daily_quantity_timeseries(products)
    plot_product_process_distribution(products)
    plot_product_hourly_histogram(products)
    plot_product_duration_histogram(products)
    plot_worker_productivity_bar(products)
    plot_product_correlation_heatmap(products)
    plot_product_weekday_boxplot(products)

    # Worker charts
    plot_worker_daily_timeseries(workers)
    plot_worker_response_time_histogram(workers)
    plot_worker_hourly_activity(workers)
    plot_worker_dialog_type_bar(workers)
    plot_worker_correlation_heatmap(workers)
    plot_worker_weekly_comparison(workers)

    # --- Anomaly detection ---------------------------------------------------
    anomaly_detection_products(products)
    anomaly_detection_workers(workers)

    print("\n" + "=" * 72)
    print(f"  Analytics complete. Charts saved to: {CHART_DIR}")
    print("=" * 72)


if __name__ == "__main__":
    main()
