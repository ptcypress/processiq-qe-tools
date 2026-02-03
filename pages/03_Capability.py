from __future__ import annotations
import streamlit as st
import numpy as np
import plotly.express as px
from scipy import stats
from scipy.stats import norm
from processiq.ui import set_page, df_preview, kpi_row, warn_empty
from processiq.data import load_table, infer_numeric_columns, coerce_numeric
from processiq.metrics import capability
from processiq.shared import get_working_df

set_page("Capability", icon="🎯")

st.title("Capability")
st.caption("Cp/Cpk (within) and Pp/Ppk (overall) with quick visuals.")

df, name = get_working_df(key_prefix="capability")
if df is None:
    warn_empty("Upload a dataset here OR load one in Data Explorer and use the shared dataset.")
    st.stop()

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
oos = 0
if lsl is not None:
    oos += int((x < lsl).sum())
if usl is not None:
    oos += int((x > usl).sum())
obs_ppm = (oos / len(x)) * 1_000_000 if len(x) else float("nan")

st.divider()
fig = px.histogram(x.to_frame(name=col), x=col, nbins=40, marginal="box")
xx = np.linspace(x.min(), x.max(), 300)
yy = norm.pdf(xx, loc=res.mean, scale=res.stdev_overall)
fig.add_trace(
    go.Scatter(
        x=xx,
        y=yy,
        mode="lines",
        name="Overall normal",
        line=dict(width=2)
    )
)
if lsl is not None:
    fig.add_vline(x=lsl, line_dash="dot", annotation_text="LSL")
if usl is not None:
    fig.add_vline(x=usl, line_dash="dot", annotation_text="USL")
st.plotly_chart(fig, use_container_width=True)

if do_norm and len(x) >= 8:
    st.subheader("Normality (Anderson-Darling)")
    ad = stats.anderson(x, dist="norm")
    st.write(f"AD statistic: **{ad.statistic:.4f}**")
    st.write("Critical values (for normal):")
    st.dataframe({"significance_%": ad.significance_level, "critical_value": ad.critical_values}, use_container_width=True)
    st.caption("Rule of thumb: if AD statistic > critical value at a chosen significance level, reject normality.")

exp_ppm = None
if res.stdev_overall is not None and res.stdev_overall > 0:
    from scipy.stats import norm
    mu = res.mean
    s = res.stdev_overall
    p_low = norm.cdf(lsl, loc=mu, scale=s) if lsl is not None else 0.0
    p_high = 1 - norm.cdf(usl, loc=mu, scale=s) if usl is not None else 0.0
    exp_ppm = (p_low + p_high) * 1_000_000

score = res.ppk if res.ppk is not None else res.cpk
label = "—"
if score is not None:
    if score >= 1.33:
        label = "PASS (≥ 1.33)"
    elif score >= 1.00:
        label = "BORDERLINE (1.00–1.33)"
    else:
        label = "FAIL (< 1.00)"

kpi_row([
    ("Decision", label),
    ("Observed OOS", f"{oos}"),
    ("Observed PPM", f"{obs_ppm:,.0f}" if np.isfinite(obs_ppm) else "—"),
    ("Expected PPM (normal)", f"{exp_ppm:,.0f}" if exp_ppm is not None else "—"),
])


