# pages/03_Capability.py
from __future__ import annotations

import numpy as np
import streamlit as st
import plotly.express as px
import plotly.graph_objects as go

from processiq.ui import set_page, df_preview, warn_empty, kpi_row
from processiq.data import coerce_numeric
from processiq.shared import get_working_df
from processiq.columns import numeric_like_columns


def _parse_optional_float(s: str | None) -> float | None:
    if s is None:
        return None
    s = str(s).strip()
    if s == "":
        return None
    try:
        return float(s)
    except Exception:
        return None


def _mr_within_sigma(x: np.ndarray) -> float | None:
    """Within sigma estimate using Moving Range of 2 (d2=1.128)."""
    if x.size < 2:
        return None
    mr = np.abs(np.diff(x))
    if mr.size == 0:
        return None
    mrbar = float(np.mean(mr))
    if not np.isfinite(mrbar) or mrbar <= 0:
        return None
    return mrbar / 1.128


def _capability(mean: float, s: float, lsl: float | None, usl: float | None):
    if s is None or not np.isfinite(s) or s <= 0:
        return None, None
    cp = None
    cpk = None
    if lsl is not None and usl is not None:
        cp = (usl - lsl) / (6 * s)
    if usl is not None:
        cpu = (usl - mean) / (3 * s)
        cpk = cpu if cpk is None else min(cpk, cpu)
    if lsl is not None:
        cpl = (mean - lsl) / (3 * s)
        cpk = cpl if cpk is None else min(cpk, cpl)
    return cp, cpk


def _ppm_expected_normal(mean: float, s: float, lsl: float | None, usl: float | None) -> float | None:
    if s is None or not np.isfinite(s) or s <= 0:
        return None
    try:
        from scipy.stats import norm  # type: ignore
        p_low = norm.cdf(lsl, loc=mean, scale=s) if lsl is not None else 0.0
        p_high = 1 - norm.cdf(usl, loc=mean, scale=s) if usl is not None else 0.0
        return (p_low + p_high) * 1_000_000
    except Exception:
        return None


set_page("Process Capability", icon="🎯")

st.title("Process Capability")
st.caption("Histogram + capability indices (Cp/Cpk and Pp/Ppk) with optional Target line.")
st.caption("Only numeric-like columns are shown.")

# ---- Data source (shared or upload) ----
df, name = get_working_df(key_prefix="capability")
if df is None:
    warn_empty("Upload a dataset here OR load one in Data Explorer and use the shared dataset.")
    st.stop()

df_preview(df)

st.divider()

num_cols = numeric_like_columns(df)
if not num_cols:
    st.warning("No numeric-like columns detected for capability.")
    st.stop()

col = st.selectbox("Measurement column", num_cols, key="cap_col")

x_series = coerce_numeric(df[col]).dropna()
x = x_series.to_numpy()
if x.size < 5:
    st.warning("Not enough numeric data after cleaning (need at least ~5 points).")
    st.stop()

# ---- Spec + target inputs ----
c1, c2, c3 = st.columns(3)
with c1:
    lsl_in = st.text_input("LSL (optional)", value="", key="cap_lsl")
with c2:
    usl_in = st.text_input("USL (optional)", value="", key="cap_usl")
with c3:
    tgt_in = st.text_input("Target / Nominal (optional)", value="", key="cap_tgt")

lsl = _parse_optional_float(lsl_in)
usl = _parse_optional_float(usl_in)

target = _parse_optional_float(tgt_in)
if target is None and (lsl is not None and usl is not None):
    target = (lsl + usl) / 2.0  # fallback midpoint if blank

# ---- Stats ----
mean = float(np.mean(x))
stdev_overall = float(np.std(x, ddof=1)) if x.size > 1 else float("nan")
stdev_within = _mr_within_sigma(x)

pp, ppk = _capability(mean, stdev_overall, lsl, usl)
cp, cpk = (None, None)
if stdev_within is not None:
    cp, cpk = _capability(mean, stdev_within, lsl, usl)

# Observed PPM
oos = 0
if lsl is not None:
    oos += int(np.sum(x < lsl))
if usl is not None:
    oos += int(np.sum(x > usl))
obs_ppm = (oos / x.size) * 1_000_000

# Expected PPM (normal, overall sigma)
exp_ppm = _ppm_expected_normal(mean, stdev_overall, lsl, usl)

# Decision label
score = ppk if ppk is not None else cpk
label = "—"
if score is not None and np.isfinite(score):
    if score >= 1.33:
        label = "PASS (≥ 1.33)"
    elif score >= 1.00:
        label = "BORDERLINE (1.00–1.33)"
    else:
        label = "FAIL (< 1.00)"

# ---- KPIs ----
kpi_row(
    [
        ("N", f"{x.size:,}"),
        ("Mean", f"{mean:.5g}"),
        ("Stdev (overall)", f"{stdev_overall:.5g}"),
        ("Stdev (within)", f"{stdev_within:.5g}" if stdev_within is not None else "—"),
    ]
)

kpi_row(
    [
        ("Cp", f"{cp:.3f}" if cp is not None else "—"),
        ("Cpk", f"{cpk:.3f}" if cpk is not None else "—"),
        ("Pp", f"{pp:.3f}" if pp is not None else "—"),
        ("Ppk", f"{ppk:.3f}" if ppk is not None else "—"),
    ]
)

kpi_row(
    [
        ("Decision", label),
        ("Observed OOS", f"{oos:,}"),
        ("Observed PPM", f"{obs_ppm:,.0f}"),
        ("Expected PPM (normal)", f"{exp_ppm:,.0f}" if exp_ppm is not None else "—"),
    ]
)

# ---- Interpretation ----
st.subheader("Interpretation")
if target is not None:
    offset = mean - target
    st.info(f"Centering: Mean − Target = {offset:+.4g} (Target line is shown on the chart).")
else:
    st.info("Centering: No target provided. (If you enter LSL & USL and leave Target blank, midpoint is used.)")

if label.startswith("PASS"):
    st.success("Capability: looks capable. (Assuming process is stable.)")
elif label.startswith("BORDERLINE"):
    st.warning("Capability: borderline. Risk depends on cost/criticality and tail behavior.")
elif label.startswith("FAIL"):
    st.error("Capability: not capable. Reduce variation and/or re-center.")
else:
    st.caption("Capability indices require at least one spec limit and valid variation estimates.")

st.caption("Reminder: If the process is not stable, capability numbers can be misleading.")

# ---- Plot ----
st.subheader("Histogram with normal curves")

nbins = st.slider("Bins", min_value=10, max_value=80, value=30, step=1, key="cap_bins")

fig = px.histogram(x, nbins=nbins, histnorm="probability density")
fig.update_layout(xaxis_title=col, yaxis_title="Density")

# Spec lines
if lsl is not None:
    fig.add_vline(x=lsl, line_dash="dot", annotation_text="LSL", annotation_position="top")
if usl is not None:
    fig.add_vline(x=usl, line_dash="dot", annotation_text="USL", annotation_position="top")

# Mean + Target lines
fig.add_vline(x=mean, line_dash="dash", annotation_text="Mean", annotation_position="top")
if target is not None:
    fig.add_vline(x=target, line_dash="solid", annotation_text="Target", annotation_position="top")

# Normal curves
xx = np.linspace(float(np.min(x)), float(np.max(x)), 300)
try:
    from scipy.stats import norm  # type: ignore

    yy_overall = norm.pdf(xx, loc=mean, scale=stdev_overall)
    fig.add_trace(go.Scatter(x=xx, y=yy_overall, mode="lines", name="Overall normal"))

    if stdev_within is not None and stdev_within > 0:
        yy_within = norm.pdf(xx, loc=mean, scale=stdev_within)
        fig.add_trace(go.Scatter(x=xx, y=yy_within, mode="lines", name="Within normal", line=dict(dash="dash")))
except Exception:
    st.info("Normal curve overlay requires scipy. (Histogram + indices still valid.)")

st.plotly_chart(fig, use_container_width=True)

st.caption(
    "If Target is left blank, ProcessIQ uses the midpoint between LSL and USL (when both are provided). "
    "Overall normal uses long-term variation (Pp/Ppk). Within normal uses short-term variation via moving range (Cp/Cpk)."
)
