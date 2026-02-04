# pages/05_Regression.py
from __future__ import annotations

import streamlit as st
import pandas as pd
import plotly.express as px

from processiq.ui import set_page, df_preview, kpi_row, warn_empty
from processiq.data import coerce_numeric
from processiq.models import ols
from processiq.shared import get_working_df
from processiq.columns import numeric_like_columns

set_page("Regression", icon="📉")

st.title("Regression")
st.caption("Fast OLS regression (screening / directionality).")
st.caption("Only numeric-like columns are shown.")

# ---- Data source (shared or upload) ----
df, name = get_working_df(key_prefix="regression")
if df is None:
    warn_empty("Upload a dataset here OR load one in Data Explorer and use the shared dataset.")
    st.stop()

df_preview(df)

st.divider()

numeric_cols = numeric_like_columns(df)
if len(numeric_cols) < 2:
    st.warning("Need at least 2 numeric-like columns for regression.")
    st.stop()

y_col = st.selectbox("Response (Y)", numeric_cols, index=0, key="reg_y")
x_pool = [c for c in numeric_cols if c != y_col]

x_cols = st.multiselect(
    "Predictors (X)",
    x_pool,
    default=x_pool[: min(3, len(x_pool))],
    key="reg_x",
)

if not x_cols:
    st.info("Select at least one predictor.")
    st.stop()

# Coerce + align
y = coerce_numeric(df[y_col])
X = df[x_cols].apply(coerce_numeric)

try:
    res = ols(y, X)
except Exception as e:
    st.error("Regression could not be fit with the selected columns.")
    st.caption(f"Details: {e}")
    st.stop()

kpi_row([("n", f"{res.n}"), ("R²", f"{res.r2:.3f}"), ("Adj R²", f"{res.adj_r2:.3f}")])

# Interpretation callout (simple + valuable)
if res.r2 >= 0.7:
    st.success("Model fit: strong (R² ≥ 0.70). Validate assumptions and check residuals for production decisions.")
elif res.r2 >= 0.4:
    st.warning("Model fit: moderate (0.40 ≤ R² < 0.70). Useful for directionality, may miss nonlinearities/interactions.")
else:
    st.info("Model fit: weak (R² < 0.40). Consider additional predictors, transforms, interactions, or non-linear models.")

st.divider()

coef_df = pd.DataFrame(
    {
        "term": list(res.params.keys()),
        "coef": list(res.params.values()),
        "p_value": [res.pvalues.get(k, float("nan")) for k in res.params.keys()],
    }
)

st.subheader("Coefficients")
st.dataframe(coef_df, use_container_width=True)

st.subheader("Quick plot (first predictor vs Y)")
x0 = x_cols[0]
plot_df = pd.concat([y.rename(y_col), X[x0].rename(x0)], axis=1).dropna()

if plot_df.empty:
    st.warning("No valid rows after cleaning numeric values.")
    st.stop()

fig = px.scatter(plot_df, x=x0, y=y_col, trendline="ols")
st.plotly_chart(fig, use_container_width=True)
