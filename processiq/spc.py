from __future__ import annotations
from dataclasses import dataclass
import numpy as np
import pandas as pd

# Constants for Xbar-R (n=2..10), A2, D3, D4 from standard SPC tables
XBAR_R_CONST = {
    2:  (1.880, 0.000, 3.267),
    3:  (1.023, 0.000, 2.574),
    4:  (0.729, 0.000, 2.282),
    5:  (0.577, 0.000, 2.114),
    6:  (0.483, 0.000, 2.004),
    7:  (0.419, 0.076, 1.924),
    8:  (0.373, 0.136, 1.864),
    9:  (0.337, 0.184, 1.816),
    10: (0.308, 0.223, 1.777),
}

@dataclass
class ChartLine:
    center: float
    lcl: float | None
    ucl: float | None

def imr(x: pd.Series) -> tuple[pd.DataFrame, ChartLine, ChartLine]:
    x = pd.to_numeric(x, errors="coerce").dropna().reset_index(drop=True)
    xi = x.to_numpy()
    n = len(xi)
    mr = np.abs(np.diff(xi))
    xbar = float(np.mean(xi)) if n else float("nan")
    mrbar = float(np.mean(mr)) if len(mr) else float("nan")

    # Individuals limits using sigma = MRbar/d2, d2=1.128
    sigma = mrbar / 1.128 if np.isfinite(mrbar) and mrbar > 0 else np.nan
    ucl_x = xbar + 3 * sigma if np.isfinite(sigma) else None
    lcl_x = xbar - 3 * sigma if np.isfinite(sigma) else None

    # MR limits: UCL = 3.267*MRbar, LCL=0 for MR of 2
    ucl_mr = 3.267 * mrbar if np.isfinite(mrbar) else None
    lcl_mr = 0.0 if np.isfinite(mrbar) else None

    df = pd.DataFrame({"X": x, "MR": pd.Series([np.nan] + mr.tolist())})
    return df, ChartLine(xbar, lcl_x, ucl_x), ChartLine(mrbar, lcl_mr, ucl_mr)

def xbar_r(df: pd.DataFrame, value_col: str, subgroup_col: str):
    d = df[[subgroup_col, value_col]].copy()
    d[value_col] = pd.to_numeric(d[value_col], errors="coerce")
    d = d.dropna()
    g = d.groupby(subgroup_col)[value_col]
    xbar = g.mean()
    r = g.max() - g.min()
    n = int(g.size().mode().iloc[0]) if len(g) else 0  # most common subgroup size

    const = XBAR_R_CONST.get(n)
    if const is None:
        raise ValueError("Subgroup size must be 2..10 and consistent. (Mode used; adjust data if mixed.)")
    A2, D3, D4 = const
    xbarbar = float(xbar.mean()) if len(xbar) else float("nan")
    rbar = float(r.mean()) if len(r) else float("nan")

    x_ucl = xbarbar + A2 * rbar
    x_lcl = xbarbar - A2 * rbar
    r_ucl = D4 * rbar
    r_lcl = D3 * rbar

    out = pd.DataFrame({subgroup_col: xbar.index, "Xbar": xbar.values, "R": r.values})
    return out, ChartLine(xbarbar, x_lcl, x_ucl), ChartLine(rbar, r_lcl, r_ucl), n

def p_chart(df: pd.DataFrame, defect_col: str, n_col: str):
    d = df[[defect_col, n_col]].copy()
    d[defect_col] = pd.to_numeric(d[defect_col], errors="coerce")
    d[n_col] = pd.to_numeric(d[n_col], errors="coerce")
    d = d.dropna()
    if len(d) == 0:
        raise ValueError("No valid rows.")
    p = d[defect_col] / d[n_col]
    pbar = float((d[defect_col].sum()) / (d[n_col].sum()))
    se = np.sqrt(pbar * (1 - pbar) / d[n_col])
    ucl = (pbar + 3 * se).clip(upper=1.0)
    lcl = (pbar - 3 * se).clip(lower=0.0)
    out = d.copy()
    out["p"] = p
    out["UCL"] = ucl
    out["LCL"] = lcl
    return out, pbar
