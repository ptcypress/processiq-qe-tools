# processiq/columns.py
from __future__ import annotations

import numpy as np
import pandas as pd


def numeric_columns(df: pd.DataFrame) -> list[str]:
    """Strict numeric dtype columns."""
    cols: list[str] = []
    for c in df.columns:
        if pd.api.types.is_numeric_dtype(df[c]):
            cols.append(c)
    return cols


def numeric_like_columns(df: pd.DataFrame, min_valid: int = 5) -> list[str]:
    """
    Columns that can be coerced to numeric with at least min_valid non-null values.
    Useful when data arrives as strings but is really numeric.
    """
    cols: list[str] = []
    for c in df.columns:
        s = pd.to_numeric(df[c], errors="coerce")
        if int(s.notna().sum()) >= min_valid:
            cols.append(c)
    return cols


def count_like_columns(df: pd.DataFrame, min_valid: int = 5) -> list[str]:
    """
    Columns suitable for count data: integer dtype OR numeric values that are
    essentially integers (e.g., 5.0, 12.0) with enough valid values.
    """
    cols: list[str] = []
    for c in df.columns:
        s = pd.to_numeric(df[c], errors="coerce").dropna()
        if len(s) < min_valid:
            continue
        # "integer-like" within tiny tolerance
        if np.all(np.isclose(s.to_numpy(), np.round(s.to_numpy()), atol=1e-9)):
            cols.append(c)
    return cols


def positive_numeric_like_columns(df: pd.DataFrame, min_valid: int = 5) -> list[str]:
    """Numeric-like columns where valid values are mostly > 0 (good for n, area, units)."""
    cols: list[str] = []
    for c in df.columns:
        s = pd.to_numeric(df[c], errors="coerce").dropna()
        if len(s) < min_valid:
            continue
        # Require that at least 95% are > 0
        if (s > 0).mean() >= 0.95:
            cols.append(c)
    return cols


def subgroup_columns_xbarr(df: pd.DataFrame, min_groups: int = 2) -> list[str]:
    """
    Candidate subgroup columns for Xbar-R where subgroup sizes are consistent
    (all equal) and within a typical range (2..10).
    """
    cols: list[str] = []
    for c in df.columns:
        s = df[c].dropna()
        if s.empty:
            continue

        counts = s.value_counts()
        if len(counts) < min_groups:
            continue

        sizes = counts.to_numpy()
        if sizes.min() < 2:
            continue
        if sizes.max() > 10:
            continue
        if not np.all(sizes == sizes[0]):
            continue

        cols.append(c)

    return cols


def categorical_columns(df: pd.DataFrame, max_unique: int = 75) -> list[str]:
    """Good for grouping/filtering without being too high-cardinality."""
    cols: list[str] = []
    for c in df.columns:
        s = df[c]
        if pd.api.types.is_object_dtype(s) or pd.api.types.is_categorical_dtype(s) or pd.api.types.is_bool_dtype(s):
            nunq = s.nunique(dropna=True)
            if nunq <= max_unique:
                cols.append(c)
    return cols
