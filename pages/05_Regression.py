from __future__ import annotations
import streamlit as st
import pandas as pd
import plotly.express as px
from processiq.ui import set_page, df_preview, kpi_row, warn_empty
from processiq.data import load_table, infer_numeric_columns, coerce_numeric
from processiq.models import ols

set_page("Regression", icon="📉")

st.title("Regression")
st.caption("Fast OLS regression (for screening / directionality).")

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

numeric_cols = infer_numeric_columns(df)
if len(numeric_cols) < 2:
    st.warning("Need at least 2 numeric-like columns.")
    st.stop()

y_col = st.selectbox("Response (Y)", numeric_cols, index=0)
x_cols = st.multiselect("Predictors (X)", [c for c in numeric_cols if c != y_col], default=[c for c in numeric_cols if c != y_col][:2])
if not x_cols:
    st.info("Select at least one predictor.")
    st.stop()

y = coerce_numeric(df[y_col])
X = df[x_cols].apply(coerce_numeric)

res = ols(y, X)
kpi_row([("n", f"{res.n}"), ("R²", f"{res.r2:.3f}"), ("Adj R²", f"{res.adj_r2:.3f}")])

st.divider()
coef_df = pd.DataFrame({
    "term": list(res.params.keys()),
    "coef": list(res.params.values()),
    "p_value": [res.pvalues.get(k, float("nan")) for k in res.params.keys()],
})
st.subheader("Coefficients")
st.dataframe(coef_df, use_container_width=True)

st.subheader("Quick plot (first predictor vs Y)")
x0 = x_cols[0]
plot_df = pd.concat([y.rename(y_col), X[x0].rename(x0)], axis=1).dropna()
fig = px.scatter(plot_df, x=x0, y=y_col, trendline="ols")
st.plotly_chart(fig, use_container_width=True)
