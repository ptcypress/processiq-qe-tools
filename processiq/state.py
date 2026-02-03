from __future__ import annotations
import streamlit as st
import pandas as pd

KEY_DF = "processiq_df"
KEY_NAME = "processiq_source_name"

def set_df(df: pd.DataFrame, source_name: str = "") -> None:
    st.session_state[KEY_DF] = df
    st.session_state[KEY_NAME] = source_name

def get_df():
    return st.session_state.get(KEY_DF), st.session_state.get(KEY_NAME, "")

def clear_df():
    st.session_state.pop(KEY_DF, None)
    st.session_state.pop(KEY_NAME, None)
