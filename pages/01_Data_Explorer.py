from __future__ import annotations
import streamlit as st
import plotly.express as px
from processiq.ui import set_page, df_preview, warn_empty
from processiq.data import load_table, infer_numeric_columns, coerce_numeric

set_page("Data Explorer", icon="🗂️")

st.title("Data Explorer")
st.caption("Upload → filter → plot → export.")

uploaded = st.file_uploader("Upload CSV or Excel", type=["csv","xlsx","xls"])
loaded = load_table(uploaded)

if not loaded:
    warn_empty()
    st.stop()

df = loaded.df
#Save as the shared dataset
from processiq.state import set_df
set_def(df, loaded.source_name)
st.success(f"Loaded dataset: {loaded.source_name} (saved for other tools)")
df_preview(df, max_rows=50)

st.divider()
st.subheader("Filter")
cols = df.columns.tolist()
filter_col = st.selectbox("Column", ["(none)"] + cols)
if filter_col != "(none)":
    values = df[filter_col].dropna().unique().tolist()
    selected = st.multiselect("Keep values", values, default=values[: min(10, len(values))])
    if selected:
        df = df[df[filter_col].isin(selected)]

st.subheader("Plot")
numeric_cols = infer_numeric_columns(df)
x = st.selectbox("X", cols, index=0)
y_choices = numeric_cols if numeric_cols else cols
y = st.selectbox("Y", y_choices, index=0)
chart = st.radio("Chart type", ["Scatter", "Line", "Box", "Histogram"], horizontal=True)

plot_df = df.copy()
plot_df[y] = coerce_numeric(plot_df[y])

if chart == "Scatter":
    fig = px.scatter(plot_df, x=x, y=y)
elif chart == "Line":
    fig = px.line(plot_df, x=x, y=y)
elif chart == "Box":
    fig = px.box(plot_df, x=x, y=y)
else:
    fig = px.histogram(plot_df, x=y, nbins=40, marginal="box")

st.plotly_chart(fig, use_container_width=True)

st.divider()
st.subheader("Export filtered data")
st.download_button("Download CSV", df.to_csv(index=False).encode("utf-8"), file_name="processiq_filtered.csv", mime="text/csv")
