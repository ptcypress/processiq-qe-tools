# pages/04_Pareto.py
from __future__ import annotations

import streamlit as st
import pandas as pd
import plotly.express as px

from processiq.ui import set_page, df_preview, warn_empty
from processiq.shared import get_working_df
from processiq.columns import categorical_columns

set_page("Pareto", icon="📊")

st.title("Pareto")
st.caption("Top contributors by category (counts) + cumulative percentage.")
st.caption("Only category-like columns are shown.")

# ---- Data source (shared or upload) ----
df, name = get_working_df(key_prefix="pareto")
if df is None:
    warn_empty("Upload a dataset here OR load one in Data Explorer and use the shared dataset.")
    st.stop()

df_preview(df)

st.divider()

cat_cols = categorical_columns(df, max_unique=150)
if not cat_cols:
    # fallback: allow any column if none detected
    st.warning("No obvious categorical columns detected. Showing all columns as fallback.")
    cat_cols = df.columns.tolist()

cat_col = st.selectbox("Category column", cat_cols, key="pareto_cat")
top_n = st.slider("Show top N categories", 5, 75, 15, key="pareto_topn")

# Clean + count
s = df[cat_col].astype(str).fillna("(blank)")
counts = (
    s.value_counts(dropna=False)
    .head(top_n)
    .reset_index()
)
counts.columns = ["Category", "Count"]
counts["CumCount"] = counts["Count"].cumsum()
counts["CumPct"] = 100 * counts["CumCount"] / counts["Count"].sum()

# Interpretation
if len(counts):
    top_share = float(counts["CumPct"].iloc[min(2, len(counts) - 1)])  # top 3 cumulative %
    st.info(f"Top 3 categories account for ~{top_share:.1f}% of counts (within the displayed top N).")

# Charts
fig = px.bar(counts, x="Category", y="Count", title="Pareto (Counts)")
st.plotly_chart(fig, use_container_width=True)

fig2 = px.line(counts, x="Category", y="CumPct", markers=True, title="Cumulative %")
fig2.update_yaxes(range=[0, 100])
st.plotly_chart(fig2, use_container_width=True)

st.subheader("Table")
st.dataframe(counts, use_container_width=True)
