# pages/01_Data_Explorer.py
from __future__ import annotations

import streamlit as st
import plotly.express as px

from processiq.ui import set_page, df_preview, warn_empty
from processiq.data import load_table, infer_numeric_columns, coerce_numeric
from processiq.state import set_df, get_df, clear_df
from processiq.sample import load_sample_quality, load_sample_grr

set_page("Data Explorer", icon="🗂️")

st.title("Data Explorer")
st.caption("Upload → filter → plot → export.")

# ---------------------------
# Quick-start: built-in samples
# ---------------------------
c1, c2, c3 = st.columns([1, 1, 1])
with c1:
    if st.button("Load sample (Quality)", use_container_width=True, key="de_load_sample_quality"):
        df = load_sample_quality()
        set_df(df, "Sample: Quality dataset")
        st.success("Loaded sample quality dataset (saved for other tools).")
        st.rerun()

with c2:
    if st.button("Load sample (Gage R&R)", use_container_width=True, key="de_load_sample_grr"):
        df = load_sample_grr()
        set_df(df, "Sample: Gage R&R dataset")
        st.success("Loaded sample Gage R&R dataset (saved for other tools).")
        st.rerun()

with c3:
    if st.button("Clear shared dataset", use_container_width=True, key="de_clear_shared"):
        clear_df()
        st.info("Cleared shared dataset.")
        st.rerun()

st.divider()

# ---------------------------
# Data source: shared OR upload
# ---------------------------
shared_df, shared_name = get_df()

use_shared = False
if shared_df is not None:
    st.info(f"Shared dataset available: {shared_name}")
    use_shared = st.checkbox("Use shared dataset", value=True, key="de_use_shared")

if use_shared and shared_df is not None:
    df = shared_df.copy()
    source_name = shared_name
else:
    uploaded = st.file_uploader("Upload CSV or Excel", type=["csv", "xlsx", "xls"], key="de_uploader")
    loaded = load_table(uploaded)
    if not loaded:
        warn_empty("Upload a dataset above, or click a sample dataset button.")
        st.stop()

    df = loaded.df
    source_name = loaded.source_name

    # Save uploaded file as the shared dataset
    set_df(df, source_name)
    st.success(f"Loaded dataset: {source_name} (saved for other tools)")

df_preview(df, max_rows=50)

# ---------------------------
# Filter
# ---------------------------
st.divider()
st.subheader("Filter")

cols = df.columns.tolist()
filter_col = st.selectbox("Column", ["(none)"] + cols, key="de_filter_col")

df_filt = df.copy()
if filter_col != "(none)":
    values = df_filt[filter_col].dropna().unique().tolist()
    selected = st.multiselect(
        "Keep values",
        values,
        default=values[: min(10, len(values))],
        key="de_filter_values",
    )
    if selected:
        df_filt = df_filt[df_filt[filter_col].isin(selected)]

# ---------------------------
# Plot
# ---------------------------
st.subheader("Plot")

numeric_cols = infer_numeric_columns(df_filt)
x = st.selectbox("X", cols, index=0, key="de_x")
y_choices = numeric_cols if numeric_cols else cols
y = st.selectbox("Y", y_choices, index=0, key="de_y")
chart = st.radio("Chart type", ["Scatter", "Line", "Box", "Histogram"], horizontal=True, key="de_chart")

plot_df = df_filt.copy()
plot_df[y] = coerce_numeric(plot_df[y])

if chart == "Scatter":
    fig = px.scatter(plot_df, x=x, y=y)
elif chart == "Line":
    fig = px.line(plot_df, x=x, y=y)
elif chart == "Box":
    fig = px.box(plot_df, x=x, y=y)
else:
    fig = px.histogram(plot_df, x=y, nbins=40, marginal="box")

st.plotly_chart(fig, use_container_width=True)

# ---------------------------
# Export
# ---------------------------
st.divider()
st.subheader("Export filtered data")

st.download_button(
    "Download filtered CSV",
    df_filt.to_csv(index=False).encode("utf-8"),
    file_name="processiq_filtered.csv",
    mime="text/csv",
    key="de_download_csv",
)
