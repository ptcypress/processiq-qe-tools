from __future__ import annotations
import streamlit as st
import pandas as pd
import plotly.express as px
from processiq.ui import set_page, df_preview, warn_empty
from processiq.data import load_table

set_page("Pareto", icon="📊")

st.title("Pareto")
st.caption("Top contributors by category (counts) + cumulative percentage.")

from processiq.state import get_df, clear_df
shared_df, shared_name = get_df()

use_shared = False
if shared_df is not None:
    c1, c2 = st.columns([3,1])
    with c1:
        st.info(f"Using shared dataset: {shared_name}")
    with c2:
        if st.button("Clear"):
            clear_df()
            st.rerun()
    use_shared = st.checkbox("Use shared dataset", value=True)

uploaded = st.file_uploader("Upload CSV or Excel", type=["csv","xlsx","xls"])
loaded = load_table(uploaded)
if not loaded:
    warn_empty()
    st.stop()

df = loaded.df
df_preview(df)

cat_col = st.selectbox("Category column", df.columns.tolist())
top_n = st.slider("Show top N categories", 5, 50, 15)

counts = df[cat_col].astype(str).value_counts(dropna=False).head(top_n).reset_index()
counts.columns = ["Category", "Count"]
counts["CumCount"] = counts["Count"].cumsum()
counts["CumPct"] = 100 * counts["CumCount"] / counts["Count"].sum()

fig = px.bar(counts, x="Category", y="Count")
st.plotly_chart(fig, use_container_width=True)

fig2 = px.line(counts, x="Category", y="CumPct", markers=True)
st.plotly_chart(fig2, use_container_width=True)

st.dataframe(counts, use_container_width=True)
