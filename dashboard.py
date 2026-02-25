#!/usr/bin/env python3
"""
WMS Analytics Console — Production Dashboard
=============================================
Multi-page warehouse analytics with light/dark theming,
contextual filters, FAQ, and settings.

Launch:
    streamlit run dashboard.py
"""

import warnings
from pathlib import Path

import numpy as np
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st

warnings.filterwarnings("ignore")
BASE_DIR = Path(__file__).resolve().parent

# ═══════════════════════════════════════════════════════════════════════════
# 1. PAGE CONFIG & SESSION STATE
# ═══════════════════════════════════════════════════════════════════════════

st.set_page_config(
    page_title="WMS Analytics Console",
    page_icon="📦",
    layout="wide",
    initial_sidebar_state="expanded",
)

# Defaults ---------------------------------------------------------------
if "theme" not in st.session_state:
    st.session_state["theme"] = "dark"
if "page" not in st.session_state:
    st.session_state["page"] = "Dashboard"
if "charts_height" not in st.session_state:
    st.session_state["charts_height"] = 400
if "show_tips" not in st.session_state:
    st.session_state["show_tips"] = True
if "anomaly_method" not in st.session_state:
    st.session_state["anomaly_method"] = "Z-Score"
if "z_threshold" not in st.session_state:
    st.session_state["z_threshold"] = 2.5
if "iqr_factor" not in st.session_state:
    st.session_state["iqr_factor"] = 1.5

PAGES = [
    ("📊", "Dashboard"),
    ("⚙️", "Operations"),
    ("📦", "Products"),
    ("👷", "Workforce"),
    ("🔍", "Anomalies"),
    ("🗂️", "Data Explorer"),
    ("⚡", "Settings"),
    ("❓", "Help & FAQ"),
]

# ═══════════════════════════════════════════════════════════════════════════
# 2. THEME ENGINE
# ═══════════════════════════════════════════════════════════════════════════

THEMES = {
    "dark": {
        "bg":           "#0e1117",
        "sidebar_bg":   "#0e1420",
        "card_bg":      "linear-gradient(135deg,#1a1f2e,#232b3d)",
        "card_border":  "#2d3748",
        "card_label":   "#8899aa",
        "card_value":   "#e2e8f0",
        "text":         "#cbd5e1",
        "text_muted":   "#64748b",
        "border":       "#1e293b",
        "accent":       "#3b82f6",
        "nav_bg":       "#111827",
        "nav_active":   "#1e40af",
        "nav_text":     "#94a3b8",
        "header_bg":    "#0e1117",
        "section_text": "#94a3b8",
        "plotly_tpl":   "plotly_dark",
        "plotly_paper": "rgba(0,0,0,0)",
        "plotly_plot":  "rgba(17,24,39,0.6)",
        "plotly_font":  "#cbd5e1",
        "plotly_grid":  "rgba(55,65,81,0.5)",
        "heatmap_scale":"Blues",
    },
    "light": {
        "bg":           "#ffffff",
        "sidebar_bg":   "#f8fafc",
        "card_bg":      "linear-gradient(135deg,#f1f5f9,#e2e8f0)",
        "card_border":  "#cbd5e1",
        "card_label":   "#64748b",
        "card_value":   "#1e293b",
        "text":         "#334155",
        "text_muted":   "#94a3b8",
        "border":       "#e2e8f0",
        "accent":       "#2563eb",
        "nav_bg":       "#f1f5f9",
        "nav_active":   "#2563eb",
        "nav_text":     "#64748b",
        "header_bg":    "#ffffff",
        "section_text": "#475569",
        "plotly_tpl":   "plotly_white",
        "plotly_paper": "rgba(255,255,255,0)",
        "plotly_plot":  "rgba(248,250,252,0.8)",
        "plotly_font":  "#334155",
        "plotly_grid":  "rgba(203,213,225,0.5)",
        "heatmap_scale":"Blues",
    },
}

COLORWAY = ["#3b82f6", "#f59e0b", "#10b981", "#ef4444", "#8b5cf6",
            "#ec4899", "#06b6d4", "#f97316", "#14b8a6", "#a855f7"]


def T() -> dict:
    """Current theme dict."""
    return THEMES[st.session_state["theme"]]


def inject_css():
    t = T()
    st.markdown(f"""
    <style>
    /* === Global === */
    .main .block-container {{ padding-top: 0.8rem; }}
    header[data-testid="stHeader"] {{ background: {t["header_bg"]}; }}

    /* === KPI cards === */
    div[data-testid="stMetric"] {{
        background: {t["card_bg"]};
        border: 1px solid {t["card_border"]};
        border-radius: 8px;
        padding: 12px 16px;
        box-shadow: 0 2px 6px rgba(0,0,0,.12);
    }}
    div[data-testid="stMetric"] label {{
        color: {t["card_label"]} !important; font-size: 0.78rem;
    }}
    div[data-testid="stMetric"] [data-testid="stMetricValue"] {{
        color: {t["card_value"]} !important; font-size: 1.4rem;
    }}

    /* === Sidebar === */
    section[data-testid="stSidebar"] {{
        background: {t["sidebar_bg"]};
        border-right: 1px solid {t["border"]};
    }}
    section[data-testid="stSidebar"] .stMarkdown h3 {{
        color: {t["text_muted"]};
        font-size: 0.7rem;
        text-transform: uppercase;
        letter-spacing: 0.12em;
        margin: 0.6rem 0 0.25rem 0;
        border-bottom: 1px solid {t["border"]};
        padding-bottom: 4px;
    }}

    /* === Tabs === */
    .stTabs [data-baseweb="tab-list"] {{
        gap: 0; background: {t["nav_bg"]}; border-radius: 6px; padding: 3px;
    }}
    .stTabs [data-baseweb="tab"] {{
        border-radius: 4px; padding: 7px 18px; font-weight: 500; color: {t["nav_text"]};
    }}
    .stTabs [aria-selected="true"] {{
        background: {t["nav_active"]} !important; color: #fff !important;
    }}

    /* === Data tables === */
    .stDataFrame {{ border: 1px solid {t["border"]}; border-radius: 6px; }}

    /* === Expanders === */
    .streamlit-expanderHeader {{ font-weight: 600; color: {t["text"]}; }}

    /* === Branding === */
    #MainMenu, footer {{ visibility: hidden; }}

    /* === Section title === */
    .sec-title {{
        font-size: 0.92rem; font-weight: 600; color: {t["section_text"]};
        text-transform: uppercase; letter-spacing: 0.06em;
        border-left: 3px solid {t["accent"]}; padding-left: 10px;
        margin: 1rem 0 0.5rem 0;
    }}

    /* === Page header bar === */
    .page-header {{
        display: flex; align-items: center; gap: 10px;
        padding: 6px 0 10px 0; margin-bottom: 4px;
        border-bottom: 1px solid {t["border"]};
    }}
    .page-header h2 {{ margin: 0; font-size: 1.3rem; color: {t["text"]}; }}
    .page-header .subtitle {{ color: {t["text_muted"]}; font-size: 0.82rem; }}

    /* === Info card (FAQ) === */
    .info-card {{
        background: {t["nav_bg"]}; border: 1px solid {t["border"]};
        border-radius: 8px; padding: 16px 20px; margin-bottom: 10px;
    }}
    .info-card h4 {{ margin: 0 0 6px 0; color: {t["accent"]}; font-size: 0.95rem; }}
    .info-card p  {{ margin: 0; color: {t["text"]}; font-size: 0.85rem; line-height: 1.5; }}

    /* === Tip banner === */
    .tip-banner {{
        background: {t["nav_bg"]}; border-left: 3px solid {t["accent"]};
        border-radius: 0 6px 6px 0; padding: 8px 14px; margin-bottom: 12px;
        font-size: 0.8rem; color: {t["text_muted"]};
    }}
    </style>
    """, unsafe_allow_html=True)


def sec(text: str):
    st.markdown(f'<div class="sec-title">{text}</div>', unsafe_allow_html=True)


def page_hdr(icon: str, title: str, subtitle: str = ""):
    sub = f'<span class="subtitle"> — {subtitle}</span>' if subtitle else ""
    st.markdown(f'<div class="page-header"><h2>{icon} {title}{sub}</h2></div>',
                unsafe_allow_html=True)


def tip(text: str):
    if st.session_state.get("show_tips", True):
        st.markdown(f'<div class="tip-banner">💡 <b>Tip:</b> {text}</div>',
                    unsafe_allow_html=True)


def info_card(title: str, body: str):
    st.markdown(f'<div class="info-card"><h4>{title}</h4><p>{body}</p></div>',
                unsafe_allow_html=True)


# ═══════════════════════════════════════════════════════════════════════════
# 3. PLOTLY HELPER
# ═══════════════════════════════════════════════════════════════════════════

def _fig(fig, h=None):
    """Apply theme + height to any Plotly figure."""
    t = T()
    height = h or st.session_state["charts_height"]
    fig.update_layout(
        template=t["plotly_tpl"],
        paper_bgcolor=t["plotly_paper"],
        plot_bgcolor=t["plotly_plot"],
        font=dict(color=t["plotly_font"], size=12),
        margin=dict(l=40, r=20, t=50, b=40),
        legend=dict(bgcolor="rgba(0,0,0,0)", font_size=11),
        colorway=COLORWAY,
        height=height,
    )
    fig.update_xaxes(gridcolor=t["plotly_grid"])
    fig.update_yaxes(gridcolor=t["plotly_grid"])
    return fig


# ═══════════════════════════════════════════════════════════════════════════
# 4. DATA LOADING
# ═══════════════════════════════════════════════════════════════════════════

@st.cache_data(show_spinner="Loading product data…")
def load_products() -> pd.DataFrame:
    df = pd.read_csv(BASE_DIR / "prepared_products.csv", low_memory=False)
    for c in ("start_time", "end_time", "expiration", "date"):
        if c in df.columns:
            df[c] = pd.to_datetime(df[c], errors="coerce")
    return df


@st.cache_data(show_spinner="Loading worker data…")
def load_workers() -> pd.DataFrame:
    df = pd.read_csv(BASE_DIR / "prepared_workers.csv", low_memory=False)
    for c in ("prompt_date", "input_date", "date"):
        if c in df.columns:
            df[c] = pd.to_datetime(df[c], errors="coerce")
    return df


# ═══════════════════════════════════════════════════════════════════════════
# 5. ANOMALY HELPERS
# ═══════════════════════════════════════════════════════════════════════════

def zscore_mask(s: pd.Series, thr: float = 2.5) -> pd.Series:
    mean, std = s.mean(), s.std()
    if std == 0:
        return pd.Series(False, index=s.index)
    return ((s - mean).abs() / std) > thr


def iqr_mask(s: pd.Series, f: float = 1.5) -> pd.Series:
    q1, q3 = s.quantile(0.25), s.quantile(0.75)
    iqr = q3 - q1
    return (s < q1 - f * iqr) | (s > q3 + f * iqr)


def anomaly_mask(s: pd.Series) -> pd.Series:
    m = st.session_state["anomaly_method"]
    z = st.session_state["z_threshold"]
    i = st.session_state["iqr_factor"]
    if m == "Z-Score":
        return zscore_mask(s, z)
    if m == "IQR":
        return iqr_mask(s, i)
    return zscore_mask(s, z) | iqr_mask(s, i)


# ═══════════════════════════════════════════════════════════════════════════
# 6. SIDEBAR  —  Navigation + contextual filters
# ═══════════════════════════════════════════════════════════════════════════

def render_sidebar(products: pd.DataFrame, workers: pd.DataFrame) -> dict:
    with st.sidebar:
        # ---------- branding ----------
        t = T()
        st.markdown(
            f'<div style="text-align:center;padding:8px 0 2px 0;">'
            f'<span style="font-size:1.5rem;">📦</span><br>'
            f'<b style="color:{t["text"]};font-size:1.05rem;">WMS Analytics</b><br>'
            f'<span style="color:{t["text_muted"]};font-size:0.72rem;">Warehouse Console v2.0</span>'
            f'</div>', unsafe_allow_html=True)

        # ---------- navigation ----------
        st.markdown("### Navigation")
        labels = [f"{icon}  {name}" for icon, name in PAGES]
        idx = next((i for i, (_, n) in enumerate(PAGES) if n == st.session_state["page"]), 0)
        chosen = st.radio("Go to", labels, index=idx, label_visibility="collapsed", key="nav_radio")
        page_name = chosen.split("  ", 1)[1]
        st.session_state["page"] = page_name

        # ---------- quick theme toggle ----------
        st.markdown("### Appearance")
        ql, qr = st.columns(2)
        with ql:
            if st.button("🌙 Dark", use_container_width=True,
                         disabled=st.session_state["theme"] == "dark"):
                st.session_state["theme"] = "dark"
                st.rerun()
        with qr:
            if st.button("☀️ Light", use_container_width=True,
                         disabled=st.session_state["theme"] == "light"):
                st.session_state["theme"] = "light"
                st.rerun()

        # ---------- contextual filters ----------
        needs_product_filter = page_name in ("Dashboard", "Operations", "Products",
                                              "Workforce", "Anomalies", "Data Explorer")
        needs_worker_filter = page_name in ("Dashboard", "Workforce", "Anomalies", "Data Explorer")

        st.markdown("### Date Range")
        all_dates = pd.concat([products["date"].dropna(), workers["date"].dropna()])
        min_d, max_d = all_dates.min().date(), all_dates.max().date()
        date_range = st.date_input("Period", value=(min_d, max_d),
                                   min_value=min_d, max_value=max_d, key="dr")

        sel_products, sel_processes, sel_workers, sel_employees = [], [], [], []

        if needs_product_filter:
            st.markdown("### Product Filters")
            product_opts = sorted(products["product_label"].unique())
            sel_products = st.multiselect("Product", product_opts,
                                          default=product_opts, key="f_prod")

            process_opts = sorted(products["process"].unique())
            sel_processes = st.multiselect("Process Type", process_opts,
                                           default=process_opts, key="f_proc")

            worker_opts = sorted(products["worker"].unique())
            with st.expander(f"Workers ({len(worker_opts)})", expanded=False):
                s = st.text_input("Search…", key="wrk_s")
                flt = [w for w in worker_opts if s.lower() in w.lower()] if s else worker_opts
                sel_workers = st.multiselect("Select", flt, default=flt, key="f_wrk")
        else:
            sel_products = sorted(products["product_label"].unique())
            sel_processes = sorted(products["process"].unique())
            sel_workers = sorted(products["worker"].unique())

        if needs_worker_filter:
            st.markdown("### Employee Filters")
            emp_opts = sorted(workers["employee_name"].unique())
            sel_employees = st.multiselect("Employee", emp_opts,
                                           default=emp_opts, key="f_emp")
        else:
            sel_employees = sorted(workers["employee_name"].unique())

        # ---------- filter summary ----------
        st.markdown("---")
        st.caption(f"📊 **{page_name}**")

    return {
        "date_range": date_range,
        "products": sel_products,
        "processes": sel_processes,
        "workers": sel_workers,
        "employees": sel_employees,
    }


def apply_filters(products: pd.DataFrame, workers: pd.DataFrame, f: dict):
    dr = f["date_range"]
    if isinstance(dr, (list, tuple)) and len(dr) == 2:
        d0, d1 = pd.Timestamp(dr[0]), pd.Timestamp(dr[1])
    else:
        d0, d1 = products["date"].min(), products["date"].max()
    p = products[
        (products["date"] >= d0) & (products["date"] <= d1)
        & products["product_label"].isin(f["products"])
        & products["worker"].isin(f["workers"])
        & products["process"].isin(f["processes"])
    ].copy()
    w = workers[
        (workers["date"] >= d0) & (workers["date"] <= d1)
        & workers["employee_name"].isin(f["employees"])
    ].copy()
    return p, w


# ═══════════════════════════════════════════════════════════════════════════
# 7. PAGES
# ═══════════════════════════════════════════════════════════════════════════

# ── 7.1 Dashboard ────────────────────────────────────────────────────────

def page_dashboard(p: pd.DataFrame, w: pd.DataFrame):
    page_hdr("📊", "Dashboard", "Executive overview")
    tip("This page shows high-level KPIs and trends. Use sidebar filters to narrow the date range or product scope.")

    k1, k2, k3, k4, k5, k6 = st.columns(6)
    k1.metric("Operations", f"{len(p):,}")
    k2.metric("Employee Actions", f"{len(w):,}")
    k3.metric("Avg Duration", f"{p['duration_sec_final'].mean():.1f}s" if len(p) else "—")
    k4.metric("Total Quantity", f"{p['quantity_pcs'].sum():,}")
    k5.metric("Active Workers", f"{p['worker'].nunique():,}")
    k6.metric("Active Employees", f"{w['employee_name'].nunique():,}")

    cl, cr = st.columns(2)
    with cl:
        sec("Operations Trend")
        d = p.groupby("date").size().reset_index(name="ops")
        fig = px.area(d, x="date", y="ops")
        _fig(fig, 260)
        fig.update_traces(fill="tozeroy", line_color="#3b82f6",
                          fillcolor="rgba(59,130,246,.15)")
        fig.update_layout(xaxis_title="", yaxis_title="Ops / day", showlegend=False)
        st.plotly_chart(fig, use_container_width=True)
    with cr:
        sec("Employee Activity Trend")
        d2 = w.groupby("date").size().reset_index(name="actions")
        fig2 = px.area(d2, x="date", y="actions")
        _fig(fig2, 260)
        fig2.update_traces(fill="tozeroy", line_color="#f59e0b",
                           fillcolor="rgba(245,158,11,.15)")
        fig2.update_layout(xaxis_title="", yaxis_title="Actions / day", showlegend=False)
        st.plotly_chart(fig2, use_container_width=True)

    ca, cb, cc = st.columns(3)
    with ca:
        sec("Product Split")
        ps = p.groupby("product_label").size().reset_index(name="count")
        fig3 = px.pie(ps, values="count", names="product_label", hole=0.55)
        _fig(fig3, 280)
        fig3.update_traces(textposition="inside", textinfo="percent+label")
        fig3.update_layout(showlegend=False)
        st.plotly_chart(fig3, use_container_width=True)
    with cb:
        sec("Top 10 Workers")
        t10 = p.groupby("worker").size().nlargest(10).reset_index(name="ops")
        fig4 = px.bar(t10, y="worker", x="ops", orientation="h", text="ops")
        _fig(fig4, 280)
        fig4.update_traces(marker_color="#3b82f6", textposition="outside", textfont_size=10)
        fig4.update_layout(yaxis={"categoryorder": "total ascending"}, xaxis_title="", yaxis_title="")
        st.plotly_chart(fig4, use_container_width=True)
    with cc:
        sec("Process Breakdown")
        pr = p["process"].value_counts().head(10).reset_index()
        pr.columns = ["process", "count"]
        fig5 = px.bar(pr, y="process", x="count", orientation="h", text="count")
        _fig(fig5, 280)
        fig5.update_traces(marker_color="#10b981", textposition="outside", textfont_size=10)
        fig5.update_layout(yaxis={"categoryorder": "total ascending"}, xaxis_title="", yaxis_title="")
        st.plotly_chart(fig5, use_container_width=True)

    sec("Hourly Activity Heatmap")
    if len(p):
        hd = p.groupby(["day_of_week", "hour"]).size().reset_index(name="count")
        hp = hd.pivot(index="day_of_week", columns="hour", values="count").fillna(0)
        lbls = ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"]
        hp.index = [lbls[i] if i < len(lbls) else str(i) for i in hp.index]
        fig6 = px.imshow(hp, color_continuous_scale=T()["heatmap_scale"],
                         labels=dict(x="Hour", y="Day", color="Ops"))
        _fig(fig6, 240)
        fig6.update_layout(xaxis=dict(dtick=1))
        st.plotly_chart(fig6, use_container_width=True)


# ── 7.2 Operations ──────────────────────────────────────────────────────

def page_operations(p: pd.DataFrame):
    page_hdr("⚙️", "Operations", "Process & duration analytics")
    tip("Toggle Daily/Weekly aggregation and split by product to compare operation patterns.")

    ct1, ct2, ct3 = st.columns([2, 2, 1])
    with ct1:
        agg = st.radio("Aggregation", ["Daily", "Weekly"], horizontal=True, key="ops_agg")
    with ct2:
        met = st.selectbox("Metric", ["Operation Count", "Total Quantity",
                                       "Avg Duration (s)"], key="ops_met")
    with ct3:
        split = st.checkbox("Split by product", True, key="ops_split")

    grp = ["date"] if agg == "Daily" else ["week_number"]
    x_col = grp[0]
    if split:
        grp.append("product_label")
    spec = {"Operation Count": ("process", "count"),
            "Total Quantity": ("quantity_pcs", "sum"),
            "Avg Duration (s)": ("duration_sec_final", "mean")}
    src, fn = spec[met]
    data = p.groupby(grp).agg(value=(src, fn)).reset_index()
    color = "product_label" if split and "product_label" in data.columns else None
    fig = px.line(data, x=x_col, y="value", color=color, markers=True,
                  title=f"{met} — {agg}")
    _fig(fig)
    fig.update_layout(xaxis_title="", yaxis_title=met)
    st.plotly_chart(fig, use_container_width=True)

    c1, c2 = st.columns(2)
    with c1:
        sec("Process Type Volume")
        gp = ["process"] + (["product_label"] if split else [])
        pv = p.groupby(gp).size().reset_index(name="count")
        fig2 = px.bar(pv, y="process", x="count",
                      color="product_label" if split else None, orientation="h")
        _fig(fig2)
        fig2.update_layout(yaxis={"categoryorder": "total ascending"}, yaxis_title="", xaxis_title="Count")
        st.plotly_chart(fig2, use_container_width=True)
    with c2:
        sec("Duration Distribution")
        cap = p["duration_sec_final"].quantile(0.99) if len(p) else 100
        dd = p[p["duration_sec_final"] <= cap]
        fig3 = px.histogram(dd, x="duration_sec_final",
                            color="product_label" if split else None,
                            nbins=60, marginal="box")
        _fig(fig3)
        fig3.update_layout(xaxis_title="Duration (s)", yaxis_title="Count")
        st.plotly_chart(fig3, use_container_width=True)

    c3, c4 = st.columns(2)
    with c3:
        sec("Weekday Pattern")
        day_order = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]
        wd = p.groupby(["date", "weekday_name", "day_of_week"]).size().reset_index(name="ops")
        fig4 = px.box(wd, x="weekday_name", y="ops", category_orders={"weekday_name": day_order})
        _fig(fig4, 360)
        fig4.update_layout(xaxis_title="", yaxis_title="Ops / day")
        st.plotly_chart(fig4, use_container_width=True)
    with c4:
        sec("Hourly Distribution")
        hr = p.groupby(["hour"] + (["product_label"] if split else [])).size().reset_index(name="count")
        fig5 = px.bar(hr, x="hour", y="count",
                      color="product_label" if split and "product_label" in hr.columns else None,
                      barmode="group")
        _fig(fig5, 360)
        fig5.update_layout(xaxis=dict(dtick=1), xaxis_title="Hour", yaxis_title="Count")
        st.plotly_chart(fig5, use_container_width=True)


# ── 7.3 Products ────────────────────────────────────────────────────────

def page_products(p: pd.DataFrame):
    page_hdr("📦", "Products", "Product comparison")
    tip("Compare KPIs side-by-side and overlay daily trends for each product SKU.")

    prods = sorted(p["product_label"].unique())
    if not prods:
        st.info("No product data in selected range.")
        return
    cols = st.columns(len(prods))
    for i, pr in enumerate(prods):
        sub = p[p["product_label"] == pr]
        with cols[i]:
            st.markdown(f"**{pr}**")
            st.metric("Operations", f"{len(sub):,}")
            st.metric("Quantity", f"{sub['quantity_pcs'].sum():,}")
            st.metric("Avg Duration", f"{sub['duration_sec_final'].mean():.1f}s")
            st.metric("Workers", f"{sub['worker'].nunique()}")

    sec("Daily Operations Overlay")
    dl = p.groupby(["date", "product_label"]).size().reset_index(name="ops")
    fig = px.line(dl, x="date", y="ops", color="product_label", markers=True)
    _fig(fig, 360)
    fig.update_layout(xaxis_title="", yaxis_title="Operations")
    st.plotly_chart(fig, use_container_width=True)

    c1, c2 = st.columns(2)
    with c1:
        sec("Quantity Over Time")
        dq = p.groupby(["date", "product_label"]).agg(qty=("quantity_pcs", "sum")).reset_index()
        fig2 = px.line(dq, x="date", y="qty", color="product_label", markers=True)
        _fig(fig2, 340)
        st.plotly_chart(fig2, use_container_width=True)
    with c2:
        sec("Duration Comparison")
        fig3 = px.box(p, x="product_label", y="duration_sec_final",
                      color="product_label", points=False)
        _fig(fig3, 340)
        fig3.update_layout(xaxis_title="", yaxis_title="Duration (s)", showlegend=False)
        st.plotly_chart(fig3, use_container_width=True)

    sec("Feature Correlation Matrix")
    nf = ["duration_sec_final", "quantity_pcs", "hour", "day_of_week",
          "week_number", "daily_product_ops_count", "worker_daily_ops", "worker_daily_qty"]
    nf = [c for c in nf if c in p.columns]
    corr = p[nf].corr().round(2)
    fig4 = px.imshow(corr, text_auto=True, color_continuous_scale="RdBu_r",
                     zmin=-1, zmax=1, aspect="auto")
    _fig(fig4, 460)
    st.plotly_chart(fig4, use_container_width=True)


# ── 7.4 Workforce ───────────────────────────────────────────────────────

def page_workforce(p: pd.DataFrame, w: pd.DataFrame):
    page_hdr("👷", "Workforce", "Worker & employee performance")

    view_tab1, view_tab2 = st.tabs(["🏗️ Warehouse Workers", "🖥️ Employee Input Logs"])

    with view_tab1:
        _wf_product(p)
    with view_tab2:
        _wf_employee(w)


def _wf_product(p: pd.DataFrame):
    tip("Rank warehouse workers by different metrics and drill down into individual performance.")

    stats = p.groupby("worker").agg(
        total_ops=("process", "count"),
        total_qty=("quantity_pcs", "sum"),
        avg_duration=("duration_sec_final", "mean"),
        active_days=("date", "nunique"),
    ).reset_index()
    stats["ops_per_day"] = (stats["total_ops"] / stats["active_days"]).round(1)
    stats.sort_values("total_ops", ascending=False, inplace=True)

    c1, c2 = st.columns([1, 3])
    with c1:
        top_n = st.slider("Top N", 5, min(80, len(stats)), 20, key="wf_n")
        sort_by = st.selectbox("Rank by", ["total_ops", "total_qty", "ops_per_day",
                                            "avg_duration", "active_days"], key="wf_s")
    top = stats.nlargest(top_n, sort_by)
    with c2:
        sec(f"Top {top_n} — {sort_by.replace('_', ' ').title()}")
        fig = px.bar(top, y="worker", x=sort_by, orientation="h", text=sort_by,
                     color="ops_per_day", color_continuous_scale="Viridis")
        _fig(fig, max(350, top_n * 22))
        fig.update_traces(textposition="outside", texttemplate="%{text:.0f}", textfont_size=10)
        fig.update_layout(yaxis={"categoryorder": "total ascending"}, yaxis_title="", xaxis_title="")
        st.plotly_chart(fig, use_container_width=True)

    st.markdown("---")
    sec("Worker Detail Drill-Down")
    sel = st.selectbox("Select worker", stats["worker"].tolist(), key="wf_d")
    wd = p[p["worker"] == sel]

    m1, m2, m3, m4 = st.columns(4)
    m1.metric("Total Ops", f"{len(wd):,}")
    m2.metric("Total Qty", f"{wd['quantity_pcs'].sum():,}")
    m3.metric("Avg Duration", f"{wd['duration_sec_final'].mean():.1f}s")
    m4.metric("Active Days", f"{wd['date'].nunique()}")

    cA, cB = st.columns(2)
    with cA:
        dw = wd.groupby("date").size().reset_index(name="ops")
        fig2 = px.bar(dw, x="date", y="ops", title=f"Daily Operations — {sel}")
        _fig(fig2, 300)
        fig2.update_traces(marker_color="#3b82f6")
        fig2.update_layout(xaxis_title="", yaxis_title="Ops")
        st.plotly_chart(fig2, use_container_width=True)
    with cB:
        pw = wd["process"].value_counts().reset_index()
        pw.columns = ["process", "count"]
        fig3 = px.pie(pw, values="count", names="process", hole=0.5,
                      title=f"Process Mix — {sel}")
        _fig(fig3, 300)
        st.plotly_chart(fig3, use_container_width=True)

    with st.expander("📋 Full Worker Statistics Table", expanded=False):
        st.dataframe(stats.round(2), use_container_width=True, height=400)


def _wf_employee(w: pd.DataFrame):
    tip("Compare employee performance across actions, response times, and session counts.")

    es = w.groupby("employee_name").agg(
        total_actions=("dialog_type", "count"),
        avg_response_sec=("response_time_sec", "mean"),
        active_days=("date", "nunique"),
        total_sessions=("session_id", "nunique"),
    ).reset_index()
    es["actions_per_day"] = (es["total_actions"] / es["active_days"]).round(1)
    es.sort_values("total_actions", ascending=False, inplace=True)

    ecols = st.columns(min(len(es), 6))
    for i, (_, r) in enumerate(es.iterrows()):
        if i >= len(ecols):
            break
        with ecols[i]:
            st.markdown(f"**{r['employee_name']}**")
            st.metric("Actions", f"{r['total_actions']:,.0f}")
            st.metric("Actions/Day", f"{r['actions_per_day']:.0f}")
            st.metric("Avg Response", f"{r['avg_response_sec']:.1f}s")
            st.metric("Sessions", f"{r['total_sessions']:,.0f}")

    c1, c2 = st.columns(2)
    with c1:
        sec("Daily Actions Comparison")
        dl = w.groupby(["date", "employee_name"]).size().reset_index(name="actions")
        fig = px.line(dl, x="date", y="actions", color="employee_name", markers=True)
        _fig(fig, 360)
        fig.update_layout(xaxis_title="", yaxis_title="Actions")
        st.plotly_chart(fig, use_container_width=True)
    with c2:
        sec("Hourly Activity Pattern")
        hr = w.groupby(["hour", "employee_name"]).size().reset_index(name="actions")
        fig2 = px.bar(hr, x="hour", y="actions", color="employee_name", barmode="group")
        _fig(fig2, 360)
        fig2.update_layout(xaxis=dict(dtick=1), xaxis_title="Hour", yaxis_title="Actions")
        st.plotly_chart(fig2, use_container_width=True)

    c3, c4 = st.columns(2)
    with c3:
        sec("Dialog Type Breakdown")
        dt = w.groupby(["dialog_type", "employee_name"]).size().reset_index(name="count")
        fig3 = px.bar(dt, y="dialog_type", x="count", color="employee_name", orientation="h")
        _fig(fig3, 340)
        fig3.update_layout(yaxis_title="", xaxis_title="Count")
        st.plotly_chart(fig3, use_container_width=True)
    with c4:
        sec("Response Time Distribution")
        cap = w["response_time_sec"].quantile(0.99) if len(w) else 100
        rt = w[w["response_time_sec"] <= cap]
        fig4 = px.histogram(rt, x="response_time_sec", color="employee_name",
                            nbins=60, marginal="box")
        _fig(fig4, 340)
        fig4.update_layout(xaxis_title="Response Time (s)", yaxis_title="Count")
        st.plotly_chart(fig4, use_container_width=True)

    sec("Weekly Trend")
    wk = w.groupby(["week_number", "employee_name"]).size().reset_index(name="actions")
    fig5 = px.bar(wk, x="week_number", y="actions", color="employee_name", barmode="group")
    _fig(fig5, 340)
    fig5.update_layout(xaxis_title="ISO Week", yaxis_title="Actions")
    st.plotly_chart(fig5, use_container_width=True)

    sec("Employee Feature Correlations")
    nc = ["response_time_sec", "hour", "day_of_week", "week_number",
          "employee_daily_actions", "employee_daily_avg_response_sec",
          "employee_weekly_actions", "employee_hourly_action_count", "session_id"]
    nc = [c for c in nc if c in w.columns]
    if nc:
        corr = w[nc].corr().round(2)
        fig6 = px.imshow(corr, text_auto=True, color_continuous_scale="RdBu_r",
                         zmin=-1, zmax=1, aspect="auto")
        _fig(fig6, 440)
        st.plotly_chart(fig6, use_container_width=True)


# ── 7.5 Anomalies ───────────────────────────────────────────────────────

def page_anomalies(p: pd.DataFrame, w: pd.DataFrame):
    page_hdr("🔍", "Anomalies", "Statistical outlier detection")
    tip("Adjust detection method and thresholds in ⚡ Settings. Red X markers indicate anomalous days.")

    c1, c2, c3 = st.columns([1.5, 1, 2.5])
    with c1:
        st.session_state["anomaly_method"] = st.selectbox(
            "Method", ["Z-Score", "IQR", "Combined"],
            index=["Z-Score", "IQR", "Combined"].index(st.session_state["anomaly_method"]),
            key="an_m_page")
    with c2:
        st.session_state["z_threshold"] = st.number_input(
            "Z threshold", 1.5, 4.0, st.session_state["z_threshold"], 0.1, key="an_z_page")
        st.session_state["iqr_factor"] = st.number_input(
            "IQR factor", 1.0, 3.0, st.session_state["iqr_factor"], 0.1, key="an_i_page")

    tab_ops, tab_emp = st.tabs(["📦 Operation Anomalies", "👷 Employee Anomalies"])

    with tab_ops:
        _anom_operations(p)
    with tab_emp:
        _anom_employees(w)


def _anom_operations(p: pd.DataFrame):
    sec("Daily Activity Anomalies")
    dly = p.groupby("date").agg(ops=("process", "count"),
                                 qty=("quantity_pcs", "sum"),
                                 avg_dur=("duration_sec_final", "mean")).reset_index()
    dly["anomaly"] = anomaly_mask(dly["ops"])
    mv, sv = dly["ops"].mean(), dly["ops"].std()
    z_t = st.session_state["z_threshold"]

    fig = go.Figure()
    nrm, anm = dly[~dly["anomaly"]], dly[dly["anomaly"]]
    fig.add_trace(go.Scatter(x=nrm["date"], y=nrm["ops"], mode="lines+markers",
                             name="Normal", marker=dict(size=4, color="#3b82f6"),
                             line=dict(color="#3b82f6")))
    if len(anm):
        fig.add_trace(go.Scatter(x=anm["date"], y=anm["ops"], mode="markers",
                                 name="Anomaly", marker=dict(size=12, color="#ef4444",
                                 symbol="x", line=dict(width=2, color="#fff"))))
    fig.add_hline(y=mv, line_dash="dash", line_color="#64748b", annotation_text=f"Mean: {mv:.0f}")
    fig.add_hline(y=mv + z_t * sv, line_dash="dot", line_color="#f59e0b", annotation_text=f"+{z_t}σ")
    fig.add_hline(y=max(0, mv - z_t * sv), line_dash="dot", line_color="#f59e0b", annotation_text=f"-{z_t}σ")
    _fig(fig, 380)
    fig.update_layout(xaxis_title="", yaxis_title="Operations")
    st.plotly_chart(fig, use_container_width=True)

    if len(anm):
        st.warning(f"**{len(anm)} anomalous day(s) detected**")
        st.dataframe(anm[["date", "ops", "qty", "avg_dur"]].round(2), use_container_width=True)
    else:
        st.success("No anomalous activity days in selected period.")

    sec("Duration Outliers")
    dur = p["duration_sec_final"].dropna()
    dm = anomaly_mask(dur)
    no = int(dm.sum())
    om1, om2, om3 = st.columns(3)
    om1.metric("Total Operations", f"{len(dur):,}")
    om2.metric("Duration Outliers", f"{no:,}")
    om3.metric("Outlier %", f"{no / max(len(dur),1) * 100:.2f}%")

    if no > 0:
        top_o = p.loc[dur[dm].nlargest(20).index,
                      ["start_time", "worker", "process", "product_label",
                       "duration_sec_final", "quantity_pcs"]]
        st.dataframe(top_o, use_container_width=True)

    fig2 = px.box(p, x="product_label", y="duration_sec_final",
                  color="product_label", points="outliers")
    _fig(fig2, 340)
    fig2.update_layout(xaxis_title="", yaxis_title="Duration (s)", showlegend=False)
    st.plotly_chart(fig2, use_container_width=True)


def _anom_employees(w: pd.DataFrame):
    z_t = st.session_state["z_threshold"]
    for emp in sorted(w["employee_name"].unique()):
        sec(f"{emp} — Daily Activity")
        ed = w[w["employee_name"] == emp]
        de = ed.groupby("date").size().rename("actions").reset_index()
        de["anomaly"] = anomaly_mask(de["actions"])
        me, se = de["actions"].mean(), de["actions"].std()

        fe = go.Figure()
        ne, ae = de[~de["anomaly"]], de[de["anomaly"]]
        fe.add_trace(go.Scatter(x=ne["date"], y=ne["actions"], mode="lines+markers",
                                name="Normal", marker=dict(size=4, color="#3b82f6"),
                                line=dict(color="#3b82f6")))
        if len(ae):
            fe.add_trace(go.Scatter(x=ae["date"], y=ae["actions"], mode="markers",
                                    name="Anomaly", marker=dict(size=12, color="#ef4444", symbol="x")))
        fe.add_hline(y=me, line_dash="dash", line_color="#64748b")
        if se > 0:
            fe.add_hline(y=me + z_t * se, line_dash="dot", line_color="#f59e0b")
        _fig(fe, 300)
        fe.update_layout(xaxis_title="", yaxis_title="Actions")
        st.plotly_chart(fe, use_container_width=True)
        if len(ae):
            st.warning(f"{len(ae)} anomalous day(s) for {emp}")
            st.dataframe(ae[["date", "actions"]], use_container_width=True)

    sec("Response Time Outliers")
    rt = w["response_time_sec"].dropna()
    rm = anomaly_mask(rt)
    nr = int(rm.sum())
    r1, r2, r3 = st.columns(3)
    r1.metric("Total Actions", f"{len(rt):,}")
    r2.metric("Response Outliers", f"{nr:,}")
    r3.metric("Outlier %", f"{nr / max(len(rt),1) * 100:.2f}%")
    if nr > 0:
        tr = w.loc[rt[rm].nlargest(20).index,
                   ["input_date", "employee_name", "dialog_type",
                    "screen_heading", "response_time_sec"]]
        st.dataframe(tr, use_container_width=True)


# ── 7.6 Data Explorer ───────────────────────────────────────────────────

def page_data(p: pd.DataFrame, w: pd.DataFrame):
    page_hdr("🗂️", "Data Explorer", "Browse & export filtered data")
    tip("Select columns to display, then download as CSV. Data reflects your active sidebar filters.")

    tab_p, tab_w = st.tabs(["📦 Product Operations", "👷 Employee Input Logs"])

    with tab_p:
        c1, c2 = st.columns([3, 1])
        with c2:
            st.metric("Rows", f"{len(p):,}")
            csv_p = p.to_csv(index=False).encode("utf-8")
            st.download_button("⬇ Download CSV", csv_p, "filtered_products.csv",
                               "text/csv", key="dl_p")
        with c1:
            ac = list(p.columns)
            dc = ["date", "worker", "process", "product_label",
                  "quantity_pcs", "duration_sec_final", "hour", "weekday_name"]
            dc = [c for c in dc if c in ac]
            cs = st.multiselect("Columns", ac, default=dc, key="dc_p")
        st.dataframe(p[cs] if cs else p, use_container_width=True, height=600)

    with tab_w:
        c3, c4 = st.columns([3, 1])
        with c4:
            st.metric("Rows", f"{len(w):,}")
            csv_w = w.to_csv(index=False).encode("utf-8")
            st.download_button("⬇ Download CSV", csv_w, "filtered_workers.csv",
                               "text/csv", key="dl_w")
        with c3:
            aw = list(w.columns)
            dw = ["date", "employee_name", "employee_id", "dialog_type",
                  "screen_heading", "response_time_sec", "hour", "weekday_name"]
            dw = [c for c in dw if c in aw]
            cw = st.multiselect("Columns", aw, default=dw, key="dc_w")
        st.dataframe(w[cw] if cw else w, use_container_width=True, height=600)


# ── 7.7 Settings ────────────────────────────────────────────────────────

def page_settings():
    page_hdr("⚡", "Settings", "Customize your experience")

    sec("Appearance")
    c1, c2 = st.columns(2)
    with c1:
        theme_choice = st.radio("Theme", ["dark", "light"],
                                index=0 if st.session_state["theme"] == "dark" else 1,
                                format_func=lambda x: "🌙 Dark Mode" if x == "dark" else "☀️ Light Mode",
                                key="set_theme", horizontal=True)
        if theme_choice != st.session_state["theme"]:
            st.session_state["theme"] = theme_choice
            st.rerun()
    with c2:
        st.session_state["show_tips"] = st.toggle("Show tips on pages",
                                                   value=st.session_state["show_tips"],
                                                   key="set_tips")

    sec("Charts")
    st.session_state["charts_height"] = st.slider(
        "Default chart height (px)", 250, 600, st.session_state["charts_height"], 25, key="set_ch")

    st.markdown("")
    st.markdown(f"Preview: chart height = **{st.session_state['charts_height']}px**")
    demo = px.bar(x=["A", "B", "C", "D"], y=[28, 55, 43, 91], title="Chart Height Preview")
    _fig(demo)
    st.plotly_chart(demo, use_container_width=True)

    sec("Anomaly Detection Defaults")
    c3, c4, c5 = st.columns(3)
    with c3:
        st.session_state["anomaly_method"] = st.selectbox(
            "Method", ["Z-Score", "IQR", "Combined"],
            index=["Z-Score", "IQR", "Combined"].index(st.session_state["anomaly_method"]),
            key="set_an_m")
    with c4:
        st.session_state["z_threshold"] = st.number_input(
            "Z-Score threshold", 1.5, 4.0, st.session_state["z_threshold"], 0.1, key="set_z")
    with c5:
        st.session_state["iqr_factor"] = st.number_input(
            "IQR factor", 1.0, 3.0, st.session_state["iqr_factor"], 0.1, key="set_i")

    info_card("Z-Score Method",
              "Flags values that deviate more than N standard deviations from the mean. "
              "Lower threshold = more sensitive.")
    info_card("IQR Method",
              "Uses the interquartile range (Q3 − Q1). Values outside Q1 − f·IQR … Q3 + f·IQR "
              "are flagged. Lower factor = more sensitive.")
    info_card("Combined",
              "Flags a value if EITHER Z-Score or IQR marks it as anomalous. Most sensitive option.")

    sec("Data Info")
    st.info("Data source files are in the workspace directory. "
            "Prepared CSVs were generated by `data_preparation.py` and anonymized by `anonymize.py`.")
    st.caption("WMS Analytics Console v2.0 — Built with Streamlit + Plotly")


# ── 7.8 Help & FAQ ──────────────────────────────────────────────────────

def page_faq():
    page_hdr("❓", "Help & FAQ", "Quick reference guide")

    sec("Pages Overview")
    info_card("📊 Dashboard",
              "High-level KPIs and trends at a glance — total operations, quantities, "
              "active workers, daily trends, product split, and an hourly activity heatmap.")
    info_card("⚙️ Operations",
              "Deep dive into warehouse operations: toggle daily/weekly aggregation, "
              "compare process types, view duration distributions, "
              "and discover weekday & hourly patterns.")
    info_card("📦 Products",
              "Side-by-side product comparison — KPI scorecards, overlaid daily trends, "
              "quantity flow over time, duration box plots, and a feature correlation heatmap.")
    info_card("👷 Workforce",
              "Two views: (1) Warehouse Workers ranked by throughput with per-worker drill-down; "
              "(2) Employee Input Logs with actions/day, response times, dialog types, and weekly trends.")
    info_card("🔍 Anomalies",
              "Statistical outlier detection on daily activity and durations. "
              "Choose Z-Score, IQR, or Combined method. Red X markers highlight anomalous days.")
    info_card("🗂️ Data Explorer",
              "Browse the raw filtered dataset — choose columns, sort, search, "
              "and download as CSV for external analysis.")

    sec("Understanding the Charts")

    with st.expander("📈 Area / Line Charts"):
        st.markdown(
            "**What they show:** Time series of a metric (operations, actions, quantity) per day or week.\n\n"
            "**How to read:** The X-axis is time, Y-axis is the metric value. "
            "Multiple colored lines mean the data is split by product or employee.\n\n"
            "**Tip:** Hover over any point to see the exact value and date."
        )

    with st.expander("📊 Bar Charts (Horizontal / Vertical)"):
        st.markdown(
            "**What they show:** Categorical comparison — e.g. which process type or worker has the most ops.\n\n"
            "**How to read:** Bar length = metric value. Bars are sorted by value for easy ranking.\n\n"
            "**Tip:** Grouped bars (side-by-side colors) compare categories across a split dimension."
        )

    with st.expander("🍩 Donut / Pie Charts"):
        st.markdown(
            "**What they show:** Proportional breakdown of a whole — e.g. product split.\n\n"
            "**How to read:** Slice size = proportion. Percentages are displayed on each slice.\n\n"
            "**Tip:** Used sparingly — only for 2-5 categories. For more, bar charts are shown instead."
        )

    with st.expander("📦 Box Plots"):
        st.markdown(
            "**What they show:** Distribution summary — median, quartiles, and outliers.\n\n"
            "**How to read:** The box spans Q1–Q3 (middle 50% of data). "
            "The line inside is the median. Whiskers extend to 1.5× IQR. "
            "Dots beyond whiskers are individual outliers.\n\n"
            "**Tip:** Compare boxes side-by-side to see which group has more variation."
        )

    with st.expander("🔥 Heatmaps"):
        st.markdown(
            "**What they show:** Activity density across two dimensions (e.g. day-of-week × hour).\n\n"
            "**How to read:** Darker color = higher value. "
            "Rows are one dimension, columns the other.\n\n"
            "**Tip:** Look for hot spots — e.g. peak hours on certain weekdays."
        )

    with st.expander("🎯 Correlation Matrix"):
        st.markdown(
            "**What it shows:** Pairwise linear correlation between numeric features.\n\n"
            "**How to read:** Values range from −1 (strong negative) to +1 (strong positive). "
            "0 means no linear relationship. Red = negative, Blue = positive.\n\n"
            "**Tip:** Strong correlations (> |0.5|) may indicate related features or redundancy."
        )

    with st.expander("🔍 Anomaly Detection Charts"):
        st.markdown(
            "**What they show:** Daily time series with flagged outlier days.\n\n"
            "**How to read:** Blue line = normal values. Red X = anomalous day. "
            "Dashed line = mean. Dotted lines = threshold boundaries.\n\n"
            "**Tip:** Adjust Z-threshold or IQR factor in Settings (or on the Anomalies page) "
            "to tune sensitivity. Lower values → more anomalies flagged."
        )

    with st.expander("📊 Histograms with Marginal Box"):
        st.markdown(
            "**What they show:** Frequency distribution of a continuous variable "
            "(e.g. duration, response time).\n\n"
            "**How to read:** X-axis = value range, Y-axis = frequency count. "
            "The small box plot on top summarizes the same distribution.\n\n"
            "**Tip:** Look for multiple peaks (bimodal) which may indicate different process groups."
        )

    sec("Filters & Navigation")

    with st.expander("How do sidebar filters work?"):
        st.markdown(
            "Filters in the sidebar apply globally to the current page. "
            "**Date Range** limits all data to the selected period. "
            "**Product / Process / Worker** multi-selects narrow the product operations dataset. "
            "**Employee** multi-select narrows the employee input log dataset.\n\n"
            "Filters are contextual — only relevant filters appear for each page. "
            "The filter count at the bottom shows how many records match."
        )

    with st.expander("How to switch pages?"):
        st.markdown(
            "Use the **Navigation** radio list in the sidebar. "
            "Each page has a dedicated icon and focuses on a specific category of analysis. "
            "Your filter selections persist when switching pages."
        )

    with st.expander("How to change the theme?"):
        st.markdown(
            "Use the 🌙/☀️ buttons in the sidebar, or go to **⚡ Settings** for the full theme toggle. "
            "Your preference persists during the session."
        )

    with st.expander("How to export data?"):
        st.markdown(
            "Go to **🗂️ Data Explorer**, select the columns you need, "
            "and click **⬇ Download CSV**. The export reflects your current filter selection."
        )

    sec("Glossary")
    gls = {
        "Operations": "Individual warehouse product movements — picks, puts, relocations, etc.",
        "Employee Actions": "Input log entries from handheld devices — scans, confirmations, responses.",
        "Duration": "Time in seconds between operation start and end (product logs).",
        "Response Time": "Time in seconds between system prompt and employee input (input logs).",
        "Session ID": "A computed identifier grouping sequential employee actions into work sessions.",
        "Process Category": "Derived grouping of raw process type codes into higher-level categories.",
        "Z-Score": "Number of standard deviations a value is from the mean.",
        "IQR": "Interquartile Range — distance between 25th and 75th percentiles.",
    }
    for term, defn in gls.items():
        st.markdown(f"**{term}** — {defn}")

    st.markdown("---")
    st.caption("WMS Analytics Console v2.0  •  Data anonymized  •  Built with Streamlit + Plotly")


# ═══════════════════════════════════════════════════════════════════════════
# 8. MAIN
# ═══════════════════════════════════════════════════════════════════════════

def main():
    inject_css()

    products_raw = load_products()
    workers_raw = load_workers()

    filters = render_sidebar(products_raw, workers_raw)
    p, w = apply_filters(products_raw, workers_raw, filters)

    # Filter summary in sidebar
    with st.sidebar:
        st.caption(
            f"Ops: **{len(p):,}** / {len(products_raw):,}   |   "
            f"Actions: **{len(w):,}** / {len(workers_raw):,}")

    # Route to current page
    page = st.session_state["page"]
    if page == "Dashboard":
        page_dashboard(p, w)
    elif page == "Operations":
        page_operations(p)
    elif page == "Products":
        page_products(p)
    elif page == "Workforce":
        page_workforce(p, w)
    elif page == "Anomalies":
        page_anomalies(p, w)
    elif page == "Data Explorer":
        page_data(p, w)
    elif page == "Settings":
        page_settings()
    elif page == "Help & FAQ":
        page_faq()


if __name__ == "__main__":
    main()
