from __future__ import annotations
import streamlit as st
import plotly.graph_objects as go
from processiq.ui import set_page, df_preview, warn_empty
from processiq.data import load_table, infer_numeric_columns, coerce_numeric
from processiq.spc import imr, xbar_r, p_chart, nelson_rules_1_2_3_4, imr_sigma_from_mrbar

set_page("Control Charts", icon="📈")

st.title("Control Charts")
st.caption("I‑MR, Xbar‑R, and p-chart for quick stability checks.")

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

from processiq.state import get_df, clear_df
shared_df, shared_name = get_df()

use_shared = False
if shared_df is not None:
    c1, c2 = st.columns([3,1])
    with c1:
        st.info(f"Shared dataset available: {shared_name}")
    with c2:
        if st.button("Clear shared"):
            clear_df()
            st.rerun()
    use_shared = st.checkbox("Use shared dataset", value=True)

if use_shared and shared_df is not None:
    df = shared_df.copy()
    df_preview(df)
else:
    uploaded = st.file_uploader("Upload CSV or Excel", type=["csv","xlsx","xls"])
    loaded = load_table(uploaded)
    if not loaded:
        warn_empty()
        st.stop()
    df = loaded.df
    df_preview(df)


chart_type = st.radio("Chart type", ["I‑MR (Individuals)", "Xbar‑R (Subgroup)", "p-chart (Attribute)"], horizontal=True)

st.divider()

if chart_type == "I‑MR (Individuals)":
    numeric_cols = infer_numeric_columns(df)
    if not numeric_cols:
        st.warning("No numeric-like columns detected.")
        st.stop()
    col = st.selectbox("Measurement column", numeric_cols)
    x = coerce_numeric(df[col]).dropna()
    dd, xline, mrline = imr(x)
    sigma = imr_sigma_from_mrbar(mrline.center)
    viol = nelson_rules_1_2_3_4(dd["X"], center=xline.center, sigma=sigma if sigma else float("nan"))

    # mark violating indices for highlighting
    viol_idx = set(viol["index"].astype(int).tolist()) if len(viol) else set()

    fig1 = go.Figure()
    # Base line
    fig1.add_trace(go.Scatter(y=dd["X"], mode="lines", name="X"))

    # Points (normal vs flagged)
    yvals = dd["X"].to_numpy()
    xvals = list(range(len(yvals)))
    flag_mask = [i in viol_idx for i in xvals]

    fig1.add_trace(go.Scatter(
        x=[xvals[i] for i in range(len(xvals)) if not flag_mask[i]],
        y=[yvals[i] for i in range(len(yvals)) if not flag_mask[i]],
        mode="markers",
        name="In-control pts"
    ))

    fig1.add_trace(go.Scatter(
        x=[xvals[i] for i in range(len(xvals)) if flag_mask[i]],
        y=[yvals[i] for i in range(len(yvals)) if flag_mask[i]],
        mode="markers",
        name="Rule violations"
    ))

    
    fig1.add_hline(y=xline.center, line_dash="dash", annotation_text="CL")
    if xline.ucl is not None: fig1.add_hline(y=xline.ucl, line_dash="dot", annotation_text="UCL")
    if xline.lcl is not None: fig1.add_hline(y=xline.lcl, line_dash="dot", annotation_text="LCL")
    fig1.update_layout(title="Individuals (I) Chart", xaxis_title="Order", yaxis_title=col)
    st.plotly_chart(fig1, use_container_width=True)
    st.subheader("Run rule violations")
    if len(viol):
        st.dataframe(viol, use_container_width=True)
    else:
        st.write("No Nelson rule violations detected (R1–R4).")


    fig2 = go.Figure()
    fig2.add_trace(go.Scatter(y=dd["MR"], mode="lines+markers", name="MR"))
    fig2.add_hline(y=mrline.center, line_dash="dash", annotation_text="CL")
    if mrline.ucl is not None: fig2.add_hline(y=mrline.ucl, line_dash="dot", annotation_text="UCL")
    if mrline.lcl is not None: fig2.add_hline(y=mrline.lcl, line_dash="dot", annotation_text="LCL")
    fig2.update_layout(title="Moving Range (MR) Chart", xaxis_title="Order", yaxis_title="MR")
    st.plotly_chart(fig2, use_container_width=True)
    st.subheader("Run rule violations")
    if len(viol):
        st.dataframe(viol, use_container_width=True)
    else:
        st.write("No Nelson rule violations detected (R1–R4).")


elif chart_type == "Xbar‑R (Subgroup)":
    numeric_cols = infer_numeric_columns(df)
    if not numeric_cols:
        st.warning("No numeric-like columns detected.")
        st.stop()
    value_col = st.selectbox("Measurement column", numeric_cols)
    subgroup_col = st.selectbox("Subgroup column (e.g., sample_id, time bucket)", df.columns.tolist())

    try:
        out, xline, rline, n = xbar_r(df, value_col=value_col, subgroup_col=subgroup_col)
    except Exception as e:
        st.error(str(e))
        st.stop()

    fig1 = go.Figure()
    fig1.add_trace(go.Scatter(x=out[subgroup_col], y=out["Xbar"], mode="lines+markers", name="Xbar"))
    fig1.add_hline(y=xline.center, line_dash="dash", annotation_text="CL")
    fig1.add_hline(y=xline.ucl, line_dash="dot", annotation_text="UCL")
    fig1.add_hline(y=xline.lcl, line_dash="dot", annotation_text="LCL")
    fig1.update_layout(title=f"X̄ Chart (n={n})", xaxis_title=subgroup_col, yaxis_title=f"Mean {value_col}")
    st.plotly_chart(fig1, use_container_width=True)

    fig2 = go.Figure()
    fig2.add_trace(go.Scatter(x=out[subgroup_col], y=out["R"], mode="lines+markers", name="R"))
    fig2.add_hline(y=rline.center, line_dash="dash", annotation_text="CL")
    fig2.add_hline(y=rline.ucl, line_dash="dot", annotation_text="UCL")
    fig2.add_hline(y=rline.lcl, line_dash="dot", annotation_text="LCL")
    fig2.update_layout(title="R Chart", xaxis_title=subgroup_col, yaxis_title="Range")
    st.plotly_chart(fig2, use_container_width=True)

else:
    defect_col = st.selectbox("Defectives column (count)", df.columns.tolist())
    n_col = st.selectbox("Sample size column (n)", df.columns.tolist())
    try:
        out, pbar = p_chart(df, defect_col=defect_col, n_col=n_col)
    except Exception as e:
        st.error(str(e))
        st.stop()

    fig = go.Figure()
    fig.add_trace(go.Scatter(y=out["p"], mode="lines+markers", name="p"))
    fig.add_trace(go.Scatter(y=out["UCL"], mode="lines", name="UCL"))
    fig.add_trace(go.Scatter(y=out["LCL"], mode="lines", name="LCL"))
    fig.add_hline(y=pbar, line_dash="dash", annotation_text="CL")
    fig.update_layout(title="p-chart", xaxis_title="Row order", yaxis_title="Proportion defective")
    st.plotly_chart(fig, use_container_width=True)
