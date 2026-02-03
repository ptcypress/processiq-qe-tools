# pages/02_Control_Charts.py
from __future__ import annotations

import streamlit as st
import pandas as pd
import plotly.graph_objects as go

from processiq.ui import set_page, df_preview, warn_empty
from processiq.data import infer_numeric_columns, coerce_numeric
from processiq.spc import (
    imr,
    xbar_r,
    p_chart,
    nelson_rules_1_2_3_4,
    imr_sigma_from_mrbar,
)
from processiq.shared import get_working_df

set_page("Control Charts", icon="📈")

st.title("Control Charts")
st.caption("I-MR, Xbar-R, and attribute charts for quick stability checks.")

# ---- Data source (shared or upload) ----
df, name = get_working_df(key_prefix="control_charts")
if df is None:
    warn_empty("Upload a dataset here OR load one in Data Explorer and use the shared dataset.")
    st.stop()

df_preview(df)

st.divider()

chart_type = st.radio(
    "Chart type",
    ["I-MR (Individuals)", "Xbar-R (Subgroup)", "p-chart (Attribute)", "np-chart", "c-chart", "u-chart"],
    horizontal=True,
)

st.divider()

# =========================
# I-MR
# =========================
if chart_type == "I-MR (Individuals)":
    numeric_cols = infer_numeric_columns(df)
    if not numeric_cols:
        st.warning("No numeric-like columns detected.")
        st.stop()

    col = st.selectbox("Measurement column", numeric_cols)
    x = coerce_numeric(df[col]).dropna()

    dd, xline, mrline = imr(x)

    sigma = imr_sigma_from_mrbar(mrline.center)
    viol = nelson_rules_1_2_3_4(dd["X"], center=xline.center, sigma=sigma if sigma else float("nan"))
    viol_idx = set(viol["index"].astype(int).tolist()) if len(viol) else set()

    # Individuals chart
    fig1 = go.Figure()
    fig1.add_trace(go.Scatter(y=dd["X"], mode="lines", name="X"))

    yvals = dd["X"].to_numpy()
    xvals = list(range(len(yvals)))
    flag_mask = [i in viol_idx for i in xvals]

    fig1.add_trace(
        go.Scatter(
            x=[xvals[i] for i in range(len(xvals)) if not flag_mask[i]],
            y=[yvals[i] for i in range(len(yvals)) if not flag_mask[i]],
            mode="markers",
            name="In-control pts",
        )
    )
    fig1.add_trace(
        go.Scatter(
            x=[xvals[i] for i in range(len(xvals)) if flag_mask[i]],
            y=[yvals[i] for i in range(len(yvals)) if flag_mask[i]],
            mode="markers",
            name="Rule violations",
        )
    )

    fig1.add_hline(y=xline.center, line_dash="dash", annotation_text="CL")
    if xline.ucl is not None:
        fig1.add_hline(y=xline.ucl, line_dash="dot", annotation_text="UCL")
    if xline.lcl is not None:
        fig1.add_hline(y=xline.lcl, line_dash="dot", annotation_text="LCL")

    fig1.update_layout(title="Individuals (I) Chart", xaxis_title="Order", yaxis_title=col)
    st.plotly_chart(fig1, use_container_width=True)

    # MR chart
    fig2 = go.Figure()
    fig2.add_trace(go.Scatter(y=dd["MR"], mode="lines+markers", name="MR"))
    fig2.add_hline(y=mrline.center, line_dash="dash", annotation_text="CL")
    if mrline.ucl is not None:
        fig2.add_hline(y=mrline.ucl, line_dash="dot", annotation_text="UCL")
    if mrline.lcl is not None:
        fig2.add_hline(y=mrline.lcl, line_dash="dot", annotation_text="LCL")

    fig2.update_layout(title="Moving Range (MR) Chart", xaxis_title="Order", yaxis_title="MR")
    st.plotly_chart(fig2, use_container_width=True)

    # Violations table (once)
    st.subheader("Run rule violations")
    if len(viol):
        st.dataframe(viol, use_container_width=True)
    else:
        st.write("No Nelson rule violations detected (R1–R4).")


# =========================
# Xbar-R
# =========================
elif chart_type == "Xbar-R (Subgroup)":
    numeric_cols = infer_numeric_columns(df)
    if not numeric_cols:
        st.warning("No numeric-like columns detected.")
        st.stop()

    value_col = st.selectbox("Measurement column", numeric_cols)
    subgroup_col = st.selectbox("Subgroup column", df.columns.tolist())

    d = df[[subgroup_col, value_col]].copy()
    d[value_col] = pd.to_numeric(d[value_col], errors="coerce")
    d = d.dropna()

    if d.empty:
        st.error("No valid rows after cleaning. Check column selections.")
        st.stop()

    # xbar_r expects a vector and subgroup IDs; keep order as in file
    dd, xbar_line, r_line = xbar_r(d[value_col], d[subgroup_col])

    # Xbar chart
    fig1 = go.Figure()
    fig1.add_trace(go.Scatter(y=dd["Xbar"], mode="lines+markers", name="Xbar"))
    fig1.add_hline(y=xbar_line.center, line_dash="dash", annotation_text="CL")
    if xbar_line.ucl is not None:
        fig1.add_hline(y=xbar_line.ucl, line_dash="dot", annotation_text="UCL")
    if xbar_line.lcl is not None:
        fig1.add_hline(y=xbar_line.lcl, line_dash="dot", annotation_text="LCL")
    fig1.update_layout(title="Xbar Chart", xaxis_title="Subgroup order", yaxis_title=f"Mean({value_col})")
    st.plotly_chart(fig1, use_container_width=True)

    # R chart
    fig2 = go.Figure()
    fig2.add_trace(go.Scatter(y=dd["R"], mode="lines+markers", name="R"))
    fig2.add_hline(y=r_line.center, line_dash="dash", annotation_text="CL")
    if r_line.ucl is not None:
        fig2.add_hline(y=r_line.ucl, line_dash="dot", annotation_text="UCL")
    if r_line.lcl is not None:
        fig2.add_hline(y=r_line.lcl, line_dash="dot", annotation_text="LCL")
    fig2.update_layout(title="R Chart", xaxis_title="Subgroup order", yaxis_title="Range")
    st.plotly_chart(fig2, use_container_width=True)


# =========================
# p-chart
# =========================
elif chart_type == "p-chart (Attribute)":
    defect_col = st.selectbox("Defectives column (count)", df.columns.tolist())
    n_col = st.selectbox("Sample size column (n)", df.columns.tolist())

    d = df[[defect_col, n_col]].copy()
    d[defect_col] = pd.to_numeric(d[defect_col], errors="coerce")
    d[n_col] = pd.to_numeric(d[n_col], errors="coerce")
    d = d.dropna()

    if d.empty:
        st.error("No valid rows after cleaning. Check column selections.")
        st.stop()

    dd, p_line = p_chart(d[defect_col], d[n_col])

    fig = go.Figure()
    fig.add_trace(go.Scatter(y=dd["p"], mode="lines+markers", name="p"))
    fig.add_trace(go.Scatter(y=dd["UCL"], mode="lines", name="UCL"))
    fig.add_trace(go.Scatter(y=dd["LCL"], mode="lines", name="LCL"))
    fig.add_hline(y=p_line.center, line_dash="dash", annotation_text="CL")
    fig.update_layout(title="p-chart", xaxis_title="Order", yaxis_title="Fraction defective")
    st.plotly_chart(fig, use_container_width=True)


# =========================
# np-chart
# =========================
elif chart_type == "np-chart":
    defect_col = st.selectbox("Defectives column (count)", df.columns.tolist())
    n_col = st.selectbox("Sample size column (n)", df.columns.tolist())

    d = df[[defect_col, n_col]].copy()
    d[defect_col] = pd.to_numeric(d[defect_col], errors="coerce")
    d[n_col] = pd.to_numeric(d[n_col], errors="coerce")
    d = d.dropna()

    if d.empty:
        st.error("No valid rows after cleaning. Check column selections.")
        st.stop()

    pbar = d[defect_col].sum() / d[n_col].sum()
    npbar = pbar * d[n_col]
    sigma = (d[n_col] * pbar * (1 - pbar)) ** 0.5

    d["np"] = d[defect_col]
    d["UCL"] = (npbar + 3 * sigma).clip(lower=0)
    d["LCL"] = (npbar - 3 * sigma).clip(lower=0)

    fig = go.Figure()
    fig.add_trace(go.Scatter(y=d["np"], mode="lines+markers", name="np"))
    fig.add_trace(go.Scatter(y=d["UCL"], mode="lines", name="UCL"))
    fig.add_trace(go.Scatter(y=d["LCL"], mode="lines", name="LCL"))
    fig.update_layout(title="np-chart", xaxis_title="Order", yaxis_title="Number defective")
    st.plotly_chart(fig, use_container_width=True)


# =========================
# c-chart
# =========================
elif chart_type == "c-chart":
    c_col = st.selectbox("Defects column (count)", df.columns.tolist())
    c = pd.to_numeric(df[c_col], errors="coerce").dropna().reset_index(drop=True)

    if c.empty:
        st.error("No valid rows after cleaning. Check column selection.")
        st.stop()

    cbar = float(c.mean())
    ucl = cbar + 3 * (cbar**0.5)
    lcl = max(cbar - 3 * (cbar**0.5), 0.0)

    fig = go.Figure()
    fig.add_trace(go.Scatter(y=c, mode="lines+markers", name="c"))
    fig.add_hline(y=cbar, line_dash="dash", annotation_text="CL")
    fig.add_hline(y=ucl, line_dash="dot", annotation_text="UCL")
    fig.add_hline(y=lcl, line_dash="dot", annotation_text="LCL")
    fig.update_layout(title="c-chart", xaxis_title="Order", yaxis_title="Defect count")
    st.plotly_chart(fig, use_container_width=True)


# =========================
# u-chart
# =========================
elif chart_type == "u-chart":
    c_col = st.selectbox("Defects column (count)", df.columns.tolist())
    n_col = st.selectbox("Units/area column (n)", df.columns.tolist())

    d = df[[c_col, n_col]].copy()
    d[c_col] = pd.to_numeric(d[c_col], errors="coerce")
    d[n_col] = pd.to_numeric(d[n_col], errors="coerce")
    d = d.dropna()

    if d.empty:
        st.error("No valid rows after cleaning. Check column selections.")
        st.stop()

    u = d[c_col] / d[n_col]
    ubar = float(d[c_col].sum() / d[n_col].sum())
    se = (ubar / d[n_col]) ** 0.5

    d["u"] = u
    d["UCL"] = ubar + 3 * se
    d["LCL"] = (ubar - 3 * se).clip(lower=0.0)

    fig = go.Figure()
    fig.add_trace(go.Scatter(y=d["u"], mode="lines+markers", name="u"))
    fig.add_trace(go.Scatter(y=d["UCL"], mode="lines", name="UCL"))
    fig.add_trace(go.Scatter(y=d["LCL"], mode="lines", name="LCL"))
    fig.add_hline(y=ubar, line_dash="dash", annotation_text="CL")
    fig.update_layout(title="u-chart", xaxis_title="Order", yaxis_title="Defects per unit")
    st.plotly_chart(fig, use_container_width=True)
