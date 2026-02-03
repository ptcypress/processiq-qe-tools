# processiq/shared.py
from __future__ import annotations

import streamlit as st

from processiq.data import load_table
from processiq.state import get_df, clear_df


def get_working_df(
    label: str = "Upload CSV or Excel",
    key_prefix: str = "default",
):
    """
    Return a dataframe either from shared session_state or from uploader.

    key_prefix is required to avoid Streamlit DuplicateElementId errors
    when the same helper is used across multiple pages.
    """
    shared_df, shared_name = get_df()

    if shared_df is not None:
        c1, c2 = st.columns([3, 1])
        with c1:
            st.info(f"Shared dataset available: {shared_name}")
        with c2:
            if st.button("Clear shared", key=f"{key_prefix}_clear_shared"):
                clear_df()
                st.rerun()

        use_shared = st.checkbox(
            "Use shared dataset",
            value=True,
            key=f"{key_prefix}_use_shared",
        )
        if use_shared:
            return shared_df.copy(), shared_name

    uploaded = st.file_uploader(
        label,
        type=["csv", "xlsx", "xls"],
        key=f"{key_prefix}_uploader",
    )
    loaded = load_table(uploaded)
    if loaded is None:
        return None, ""
    return loaded.df, loaded.source_name
