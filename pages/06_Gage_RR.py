# pages/06_Gage_RR.py
from __future__ import annotations

import streamlit as st
import pandas as pd

from processiq.ui import set_page, df_preview, kpi_row, warn_empty
from processiq.msa import gage_rr_crossed_anova
from processiq.shared import get_working_df
from processiq.columns import categorical_columns, numeric_like_columns

set_page("Gage R&R (Crossed)", icon="🧪")

st.title("Gage R&R (Crossed, ANOVA)")
st.caption("Part × Operator with repeats. Outputs variance components + % contribution.")
st.caption("Only compatible columns are shown (Part/Operator categorical, Measurement numeric-like).")

# ---- Data source (shared or upload) ----
df, name = get_working_df(key_prefix="gage_rr")
if df is None:
    warn_empty("Upload a dataset here OR load one in Data Explorer and use the shared dataset.")
    st.stop()

df_preview(df)

st.divider()

cat_cols = categorical_columns(df, max_unique=500)
num_cols = numeric_like_columns(df)

if not cat_cols:
    st.warning("No categorical-like columns detected (needed for Part and Operator).")
    st.stop()
if not num_cols:
    st.warning("No numeric-like columns detected (needed for Measurement).")
    st.stop()

part_col = st.selectbox("Part column", cat_cols, key="grr_part")
op_col = st.selectbox("Operator column", [c for c in cat_cols if c != part_col] or cat_cols, key="grr_op")
y_col = st.selectbox("Measurement column", num_cols, key="grr_y")

st.caption("Data requirement: each Part×Operator cell should have repeated measurements (≥2 recommended).")

try:
    res = gage_rr_crossed_anova(df, part_col=part_col, op_col=op_col, y_col=y_col)
except Exception as e:
    st.error("Gage R&R could not be computed with the selected columns.")
    st.caption(f"Details: {e}")
    st.stop()

kpi_row(
    [
        ("n", f"{res.n}"),
        ("Parts", f"{res.parts}"),
        ("Operators", f"{res.operators}"),
        ("Repeats (min cell)", f"{res.repeats}"),
        ("%GRR", f"{res.pct_grr:.1f}%"),
        ("%Repeat", f"{res.pct_repeat:.1f}%"),
        ("%Repro (+int)", f"{res.pct_repro:.1f}%"),
        ("%Part", f"{res.pct_part:.1f}%"),
    ]
)

# Interpretation callout (very helpful for non-MSA folks)
if res.pct_grr <= 10:
    st.success("MSA interpretation: Excellent (≤10% GRR). Measurement system is generally acceptable.")
elif res.pct_grr <= 30:
    st.warning("MSA interpretation: Marginal (10–30% GRR). May be acceptable depending on risk/cost; consider improvements.")
else:
    st.error("MSA interpretation: Poor (>30% GRR). Measurement system likely needs improvement before capability/SPC decisions.")

st.divider()

st.subheader("Variance components")
out = pd.DataFrame(
    {
        "component": ["Repeatability (EV)", "Reproducibility (+interaction)", "Part-to-Part", "Total"],
        "variance": [res.var_repeat, res.var_repro, res.var_part, res.var_total],
        "pct_total": [res.pct_repeat, res.pct_repro, res.pct_part, 100.0],
    }
)
st.dataframe(out, use_container_width=True)

st.caption("Tip: We can add %Study Var and ndc (number of distinct categories) next.")
