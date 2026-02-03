from __future__ import annotations
import streamlit as st
import plotly.graph_objects as go
from processiq.ui import set_page, df_preview, warn_empty
from processiq.data import load_table, infer_numeric_columns, coerce_numeric
from processiq.spc import imr, xbar_r, p_chart

set_page("Control Charts", icon="📈")

st.title("Control Charts")
st.caption("I‑MR, Xbar‑R, and p-chart for quick stability checks.")

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

    fig1 = go.Figure()
    fig1.add_trace(go.Scatter(y=dd["X"], mode="lines+markers", name="X"))
    fig1.add_hline(y=xline.center, line_dash="dash", annotation_text="CL")
    if xline.ucl is not None: fig1.add_hline(y=xline.ucl, line_dash="dot", annotation_text="UCL")
    if xline.lcl is not None: fig1.add_hline(y=xline.lcl, line_dash="dot", annotation_text="LCL")
    fig1.update_layout(title="Individuals (I) Chart", xaxis_title="Order", yaxis_title=col)
    st.plotly_chart(fig1, use_container_width=True)

    fig2 = go.Figure()
    fig2.add_trace(go.Scatter(y=dd["MR"], mode="lines+markers", name="MR"))
    fig2.add_hline(y=mrline.center, line_dash="dash", annotation_text="CL")
    if mrline.ucl is not None: fig2.add_hline(y=mrline.ucl, line_dash="dot", annotation_text="UCL")
    if mrline.lcl is not None: fig2.add_hline(y=mrline.lcl, line_dash="dot", annotation_text="LCL")
    fig2.update_layout(title="Moving Range (MR) Chart", xaxis_title="Order", yaxis_title="MR")
    st.plotly_chart(fig2, use_container_width=True)

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
