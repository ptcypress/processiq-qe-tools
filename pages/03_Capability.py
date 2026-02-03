from __future__ import annotations
import streamlit as st
import numpy as np
import plotly.express as px
from scipy import stats
from processiq.ui import set_page, df_preview, kpi_row, warn_empty
from processiq.data import load_table, infer_numeric_columns, coerce_numeric
from processiq.metrics import capability

set_page("Capability", icon="🎯")

st.title("Capability")
st.caption("Cp/Cpk (within) and Pp/Ppk (overall) with quick visuals.")

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
if not numeric_cols:
    st.warning("No numeric-like columns detected.")
    st.stop()

col = st.selectbox("Measurement column", numeric_cols)

c1, c2, c3 = st.columns(3)
with c1:
    lsl_s = st.text_input("LSL (optional)", value="")
with c2:
    usl_s = st.text_input("USL (optional)", value="")
with c3:
    do_norm = st.checkbox("Normality check (Anderson-Darling)", value=False)

def parse_float(s):
    s = str(s).strip()
    if s == "":
        return None
    try:
        return float(s)
    except:
        return None

lsl = parse_float(lsl_s)
usl = parse_float(usl_s)

x = coerce_numeric(df[col]).dropna()
res = capability(x, lsl, usl)

kpi_row([
    ("n", f"{res.n}"),
    ("Mean", f"{res.mean:.6g}"),
    ("σ within (I-MR)", f"{res.stdev_within:.6g}" if res.stdev_within is not None else "—"),
    ("σ overall", f"{res.stdev_overall:.6g}" if res.stdev_overall is not None else "—"),
    ("Cp", f"{res.cp:.3f}" if res.cp is not None else "—"),
    ("Cpk", f"{res.cpk:.3f}" if res.cpk is not None else "—"),
    ("Pp", f"{res.pp:.3f}" if res.pp is not None else "—"),
    ("Ppk", f"{res.ppk:.3f}" if res.ppk is not None else "—"),
])

st.divider()
fig = px.histogram(x.to_frame(name=col), x=col, nbins=40, marginal="box")
st.plotly_chart(fig, use_container_width=True)

if do_norm and len(x) >= 8:
    st.subheader("Normality (Anderson-Darling)")
    ad = stats.anderson(x, dist="norm")
    st.write(f"AD statistic: **{ad.statistic:.4f}**")
    st.write("Critical values (for normal):")
    st.dataframe({"significance_%": ad.significance_level, "critical_value": ad.critical_values}, use_container_width=True)
    st.caption("Rule of thumb: if AD statistic > critical value at a chosen significance level, reject normality.")
