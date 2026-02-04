# pages/02_Control_Charts.py
from __future__ import annotations

import streamlit as st
import pandas as pd
import plotly.graph_objects as go

from processiq.ui import set_page, df_preview, warn_empty
from processiq.data import coerce_numeric
from processiq.spc import (
    imr,
    xbar_r,
    p_chart,
    nelson_rules_1_2_3_4,
    imr_sigma_from_mrbar,
)
from processiq.shared import get_working_df
from processiq.columns import (
    numeric_like_columns,
    count_like_columns,
    positive_numeric_like_columns,
    subgroup_columns_xbarr,
)
from processiq.reporting import Report
from processiq.report_builder import ReportSection, add_section

set_page("Control Charts", icon="📈")

st.title("Control Charts")
st.caption("I-MR, Xbar-R, and attribute charts for quick stability checks.")
st.caption("Only compatible columns are shown for each chart type.")

df, dataset_name = get_working_df(key_prefix="control_charts")
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

report_figs: list[tuple[str, object]] = []
report_tables: list[tuple[str, pd.DataFrame]] = []
report_inputs: list[str] = []
report_interp: list[str] = []
badge_text: str | None = None
badge_level: str = "success"

# ========================= I-MR =========================
if chart_type == "I-MR (Individuals)":
    num_cols = numeric_like_columns(df)
    if not num_cols:
        st.warning("No numeric-like columns detected for I-MR.")
        st.stop()

    col = st.selectbox("Measurement column", num_cols, key="cc_imr_col")
    x = coerce_numeric(df[col]).dropna()

    if len(x) < 3:
        st.warning("Not enough numeric data points for I-MR (need at least 3).")
        st.stop()

    dd, xline, mrline = imr(x)
    sigma = imr_sigma_from_mrbar(mrline.center)
    viol = nelson_rules_1_2_3_4(dd["X"], center=xline.center, sigma=sigma if sigma else float("nan"))
    viol_idx = set(viol["index"].astype(int).tolist()) if len(viol) else set()

    report_inputs += [
        "<b>Chart:</b> I-MR",
        f"<b>Measurement:</b> {col}",
    ]

    if len(viol):
        st.error(f"Unstable: {len(viol)} run rule violation(s) detected. Investigate special cause before capability.")
        rule_counts = viol["rule"].value_counts().to_dict()
        st.caption("Rule counts: " + ", ".join([f"{k}={v}" for k, v in rule_counts.items()]))
        report_interp.append(f"Unstable: {len(viol)} run rule violation(s) detected (R1–R4).")
        badge_text = f"Stability: UNSTABLE ({len(viol)} violation(s))"
        badge_level = "error"
    else:
        st.success("Stable: no run rule violations detected (R1–R4).")
        report_interp.append("Stable: no run rule violations detected (R1–R4).")
        badge_text = "Stability: STABLE (no violations)"
        badge_level = "success"

    # Individuals chart
    fig1 = go.Figure()
    fig1.add_trace(go.Scatter(y=dd["X"], mode="lines", name="X"))

    yvals = dd["X"].to_numpy()
    xvals = list(range(len(yvals)))
    flag_mask = [i in viol_idx for i in xvals]

    fig1.add_trace(go.Scatter(
        x=[xvals[i] for i in range(len(xvals)) if not flag_mask[i]],
        y=[yvals[i] for i in range(len(yvals)) if not flag_mask[i]],
        mode="markers",
        name="In-control pts",
    ))
    fig1.add_trace(go.Scatter(
        x=[xvals[i] for i in range(len(xvals)) if flag_mask[i]],
        y=[yvals[i] for i in range(len(yvals)) if flag_mask[i]],
        mode="markers",
        name="Rule violations",
    ))

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

    st.subheader("Run rule violations")
    if len(viol):
        st.dataframe(viol, use_container_width=True)
    else:
        st.write("No Nelson rule violations detected (R1–R4).")

    report_figs += [("Individuals (I) Chart", fig1), ("Moving Range (MR) Chart", fig2)]
    if len(viol):
        report_tables.append(("Run rule violations", viol))

# ========================= Xbar-R =========================
elif chart_type == "Xbar-R (Subgroup)":
    value_cols = numeric_like_columns(df)
    group_cols = subgroup_columns_xbarr(df)

    if not value_cols:
        st.warning("No numeric-like measurement columns found for Xbar-R.")
        st.stop()
    if not group_cols:
        st.warning("No valid subgroup columns found (need consistent subgroup sizes 2..10).")
        st.stop()

    value_col = st.selectbox("Measurement column", value_cols, key="cc_xbarr_val")
    subgroup_col = st.selectbox("Subgroup column", group_cols, key="cc_xbarr_grp")

    out, xbar_line, r_line, n = xbar_r(df, value_col=value_col, subgroup_col=subgroup_col)
    st.caption(f"Detected subgroup size: n = {n}")

    report_inputs += [
        "<b>Chart:</b> Xbar-R",
        f"<b>Measurement:</b> {value_col}",
        f"<b>Subgroup:</b> {subgroup_col} (n={n})",
    ]
    badge_text = "Xbar-R chart generated (interpret stability visually)"
    badge_level = "warn"

    fig1 = go.Figure()
    fig1.add_trace(go.Scatter(y=out["Xbar"], mode="lines+markers", name="Xbar"))
    fig1.add_hline(y=xbar_line.center, line_dash="dash", annotation_text="CL")
    fig1.add_hline(y=xbar_line.ucl, line_dash="dot", annotation_text="UCL")
    fig1.add_hline(y=xbar_line.lcl, line_dash="dot", annotation_text="LCL")
    fig1.update_layout(title="Xbar Chart", xaxis_title="Subgroup order", yaxis_title=f"Mean({value_col})")
    st.plotly_chart(fig1, use_container_width=True)

    fig2 = go.Figure()
    fig2.add_trace(go.Scatter(y=out["R"], mode="lines+markers", name="R"))
    fig2.add_hline(y=r_line.center, line_dash="dash", annotation_text="CL")
    fig2.add_hline(y=r_line.ucl, line_dash="dot", annotation_text="UCL")
    fig2.add_hline(y=r_line.lcl, line_dash="dot", annotation_text="LCL")
    fig2.update_layout(title="R Chart", xaxis_title="Subgroup order", yaxis_title="Range")
    st.plotly_chart(fig2, use_container_width=True)

    report_figs += [("Xbar Chart", fig1), ("R Chart", fig2)]

# ========================= p-chart =========================
elif chart_type == "p-chart (Attribute)":
    count_cols = count_like_columns(df)
    n_cols = positive_numeric_like_columns(df)

    if not count_cols:
        st.warning("No count-like columns found for defectives.")
        st.stop()
    if not n_cols:
        st.warning("No positive numeric-like columns found for sample size n.")
        st.stop()

    defect_col = st.selectbox("Defectives column (count)", count_cols, key="cc_p_def")
    n_col = st.selectbox("Sample size column (n)", n_cols, key="cc_p_n")

    out, pbar = p_chart(df, defect_col=defect_col, n_col=n_col)

    report_inputs += [
        "<b>Chart:</b> p-chart",
        f"<b>Defectives:</b> {defect_col}",
        f"<b>n:</b> {n_col}",
    ]
    badge_text = "p-chart generated (interpret stability visually)"
    badge_level = "warn"

    fig = go.Figure()
    fig.add_trace(go.Scatter(y=out["p"], mode="lines+markers", name="p"))
    fig.add_trace(go.Scatter(y=out["UCL"], mode="lines", name="UCL"))
    fig.add_trace(go.Scatter(y=out["LCL"], mode="lines", name="LCL"))
    fig.add_hline(y=pbar, line_dash="dash", annotation_text="CL")
    fig.update_layout(title="p-chart", xaxis_title="Order", yaxis_title="Fraction defective")
    st.plotly_chart(fig, use_container_width=True)

    report_figs.append(("p-chart", fig))

# ========================= np-chart =========================
elif chart_type == "np-chart":
    count_cols = count_like_columns(df)
    n_cols = positive_numeric_like_columns(df)

    if not count_cols:
        st.warning("No count-like columns found for defectives.")
        st.stop()
    if not n_cols:
        st.warning("No positive numeric-like columns found for sample size n.")
        st.stop()

    defect_col = st.selectbox("Defectives column (count)", count_cols, key="cc_np_def")
    n_col = st.selectbox("Sample size column (n)", n_cols, key="cc_np_n")

    d = df[[defect_col, n_col]].copy()
    d[defect_col] = pd.to_numeric(d[defect_col], errors="coerce")
    d[n_col] = pd.to_numeric(d[n_col], errors="coerce")
    d = d.dropna()
    d = d[(d[n_col] > 0) & (d[defect_col] >= 0)]
    if d.empty:
        st.warning("No valid rows after cleaning.")
        st.stop()

    pbar = d[defect_col].sum() / d[n_col].sum()
    npbar = pbar * d[n_col]
    sigma = (d[n_col] * pbar * (1 - pbar)) ** 0.5
    d["np"] = d[defect_col]
    d["UCL"] = (npbar + 3 * sigma).clip(lower=0)
    d["LCL"] = (npbar - 3 * sigma).clip(lower=0)

    report_inputs += [
        "<b>Chart:</b> np-chart",
        f"<b>Defectives:</b> {defect_col}",
        f"<b>n:</b> {n_col}",
    ]
    badge_text = "np-chart generated (interpret stability visually)"
    badge_level = "warn"

    fig = go.Figure()
    fig.add_trace(go.Scatter(y=d["np"], mode="lines+markers", name="np"))
    fig.add_trace(go.Scatter(y=d["UCL"], mode="lines", name="UCL"))
    fig.add_trace(go.Scatter(y=d["LCL"], mode="lines", name="LCL"))
    fig.update_layout(title="np-chart", xaxis_title="Order", yaxis_title="Number defective")
    st.plotly_chart(fig, use_container_width=True)

    report_figs.append(("np-chart", fig))

# ========================= c-chart =========================
elif chart_type == "c-chart":
    count_cols = count_like_columns(df)
    if not count_cols:
        st.warning("No count-like columns found for c-chart.")
        st.stop()

    c_col = st.selectbox("Defects column (count)", count_cols, key="cc_c_col")
    c = pd.to_numeric(df[c_col], errors="coerce").dropna().reset_index(drop=True)
    if c.empty:
        st.warning("No valid rows after cleaning.")
        st.stop()

    cbar = float(c.mean())
    ucl = cbar + 3 * (cbar**0.5)
    lcl = max(cbar - 3 * (cbar**0.5), 0.0)

    report_inputs += [
        "<b>Chart:</b> c-chart",
        f"<b>Defects:</b> {c_col}",
    ]
    badge_text = "c-chart generated (interpret stability visually)"
    badge_level = "warn"

    fig = go.Figure()
    fig.add_trace(go.Scatter(y=c, mode="lines+markers", name="c"))
    fig.add_hline(y=cbar, line_dash="dash", annotation_text="CL")
    fig.add_hline(y=ucl, line_dash="dot", annotation_text="UCL")
    fig.add_hline(y=lcl, line_dash="dot", annotation_text="LCL")
    fig.update_layout(title="c-chart", xaxis_title="Order", yaxis_title="Defect count")
    st.plotly_chart(fig, use_container_width=True)

    report_figs.append(("c-chart", fig))

# ========================= u-chart =========================
elif chart_type == "u-chart":
    count_cols = count_like_columns(df)
    n_cols = positive_numeric_like_columns(df)

    if not count_cols:
        st.warning("No count-like columns found for defects.")
        st.stop()
    if not n_cols:
        st.warning("No positive numeric-like columns found for units/area (n).")
        st.stop()

    c_col = st.selectbox("Defects column (count)", count_cols, key="cc_u_c")
    n_col = st.selectbox("Units/area column (n)", n_cols, key="cc_u_n")

    d = df[[c_col, n_col]].copy()
    d[c_col] = pd.to_numeric(d[c_col], errors="coerce")
    d[n_col] = pd.to_numeric(d[n_col], errors="coerce")
    d = d.dropna()
    d = d[(d[n_col] > 0) & (d[c_col] >= 0)]
    if d.empty:
        st.warning("No valid rows after cleaning.")
        st.stop()

    u = d[c_col] / d[n_col]
    ubar = float(d[c_col].sum() / d[n_col].sum())
    se = (ubar / d[n_col]) ** 0.5
    d["u"] = u
    d["UCL"] = ubar + 3 * se
    d["LCL"] = (ubar - 3 * se).clip(lower=0.0)

    report_inputs += [
        "<b>Chart:</b> u-chart",
        f"<b>Defects:</b> {c_col}",
        f"<b>Units/area:</b> {n_col}",
    ]
    badge_text = "u-chart generated (interpret stability visually)"
    badge_level = "warn"

    fig = go.Figure()
    fig.add_trace(go.Scatter(y=d["u"], mode="lines+markers", name="u"))
    fig.add_trace(go.Scatter(y=d["UCL"], mode="lines", name="UCL"))
    fig.add_trace(go.Scatter(y=d["LCL"], mode="lines", name="LCL"))
    fig.add_hline(y=ubar, line_dash="dash", annotation_text="CL")
    fig.update_layout(title="u-chart", xaxis_title="Order", yaxis_title="Defects per unit")
    st.plotly_chart(fig, use_container_width=True)

    report_figs.append(("u-chart", fig))

# ---- Export report + Add to builder ----
st.divider()
st.subheader("Export / Add to Report Builder")

rep = Report(
    title="ProcessIQ Report — Control Charts",
    subtitle=f"Tool: Control Charts • {chart_type}",
    dataset_name=dataset_name or "(unknown)",
)

rep.add_card("Inputs", "<br/>".join(report_inputs) if report_inputs else f"<b>Chart:</b> {chart_type}")
if report_interp:
    rep.add_card("Interpretation", "<br/>".join(report_interp))
if badge_text:
    rep.add_badge("Status", badge_text, level=badge_level)

for title, fig in report_figs:
    rep.add_figure(title, fig)
for title, table in report_tables:
    rep.add_table(title, table)

colA, colB = st.columns(2)

with colA:
    html = rep.render_html().encode("utf-8")
    st.download_button(
        "Download HTML report",
        data=html,
        file_name=rep.file_name("processiq_control_charts_report"),
        mime="text/html",
        use_container_width=True,
        key="cc_dl_html",
    )

with colB:
    if st.button("Add to Report Builder", use_container_width=True, key="cc_add_rb"):
        add_section(
            ReportSection(
                tool="Control Charts",
                subtitle=chart_type,
                dataset_name=dataset_name or "(unknown)",
                inputs_html="<br/>".join(report_inputs) if report_inputs else f"<b>Chart:</b> {chart_type}",
                interpretation_html="<br/>".join(report_interp) if report_interp else "",
                kpis=[],  # keep v1 simple for control charts
                badge_text=badge_text,
                badge_level=badge_level,
                figures=report_figs,
                tables=report_tables,
            )
        )
        st.success("Added Control Charts section to Report Builder.")
