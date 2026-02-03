from __future__ import annotations
import streamlit as st
import pandas as pd
from processiq.ui import set_page, df_preview, kpi_row, warn_empty
from processiq.data import load_table
from processiq.msa import gage_rr_crossed_anova

set_page("Gage R&R (Crossed)", icon="🧪")

st.title("Gage R&R (Crossed, ANOVA)")
st.caption("Part × Operator with repeats. Outputs variance components + % contribution.")

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

cols = df.columns.tolist()
part_col = st.selectbox("Part column", cols)
op_col = st.selectbox("Operator column", cols)
y_col = st.selectbox("Measurement column", cols)

try:
    res = gage_rr_crossed_anova(df, part_col=part_col, op_col=op_col, y_col=y_col)
except Exception as e:
    st.error(str(e))
    st.stop()

kpi_row([
    ("n", f"{res.n}"),
    ("Parts", f"{res.parts}"),
    ("Operators", f"{res.operators}"),
    ("Repeats (min cell)", f"{res.repeats}"),
    ("%GRR", f"{res.pct_grr:.1f}%"),
    ("%Repeat", f"{res.pct_repeat:.1f}%"),
    ("%Repro (+int)", f"{res.pct_repro:.1f}%"),
    ("%Part", f"{res.pct_part:.1f}%"),
])

st.divider()
st.subheader("Variance components")
out = pd.DataFrame({
    "component": ["Repeatability (EV)", "Reproducibility (+interaction)", "Part-to-Part", "Total"],
    "variance": [res.var_repeat, res.var_repro, res.var_part, res.var_total],
    "pct_total": [res.pct_repeat, res.pct_repro, res.pct_part, 100.0],
})
st.dataframe(out, use_container_width=True)

st.caption("Tip: if you want %Study Var and ndc (number of distinct categories), we can add that next.")
