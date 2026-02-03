from __future__ import annotations
from dataclasses import dataclass
from typing import Optional, List
import pandas as pd
import streamlit as st

SUPPORTED_EXTS = (".csv", ".xlsx", ".xls")

@dataclass
class LoadedData:
    df: pd.DataFrame
    source_name: str

def load_table(uploaded_file) -> Optional[LoadedData]:
    if uploaded_file is None:
        return None
    name = uploaded_file.name
    lower = name.lower()
    try:
        if lower.endswith(".csv"):
            df = pd.read_csv(uploaded_file)
        elif lower.endswith((".xlsx", ".xls")):
            df = pd.read_excel(uploaded_file)
        else:
            st.error(f"Unsupported file type. Please upload: {', '.join(SUPPORTED_EXTS)}")
            return None
    except Exception as e:
        st.error(f"Could not read file: {e}")
        return None

    df.columns = [str(c).strip() for c in df.columns]
    return LoadedData(df=df, source_name=name)

def coerce_numeric(s: pd.Series) -> pd.Series:
    return pd.to_numeric(s, errors="coerce")

def infer_numeric_columns(df: pd.DataFrame, min_frac: float = 0.8) -> List[str]:
    out = []
    for c in df.columns:
        x = pd.to_numeric(df[c], errors="coerce")
        if x.notna().mean() >= min_frac and x.notna().sum() >= 3:
            out.append(c)
    return out
