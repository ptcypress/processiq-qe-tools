from __future__ import annotations
import streamlit as st
import pandas as pd

def set_page(title: str, icon: str = "🧠", layout: str = "wide"):
    st.set_page_config(page_title=title, page_icon=icon, layout=layout)

def kpi_row(items: list[tuple[str, str]]):
    cols = st.columns(len(items))
    for i, (label, value) in enumerate(items):
        cols[i].metric(label, value)

def df_preview(df: pd.DataFrame, max_rows: int = 25):
    st.caption(f"Preview ({min(len(df), max_rows)} of {len(df)} rows)")
    st.dataframe(df.head(max_rows), use_container_width=True)

def warn_empty(msg: str = "Upload data to begin."):
    st.info(msg)
