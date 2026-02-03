from __future__ import annotations
from dataclasses import dataclass
import pandas as pd
import statsmodels.api as sm
import statsmodels.formula.api as smf

@dataclass
class GRRResult:
    n: int
    parts: int
    operators: int
    repeats: int
    var_repeat: float
    var_repro: float
    var_part: float
    var_total: float
    pct_grr: float
    pct_repeat: float
    pct_repro: float
    pct_part: float

def gage_rr_crossed_anova(df: pd.DataFrame, part_col: str, op_col: str, y_col: str) -> GRRResult:
    d = df[[part_col, op_col, y_col]].copy()
    d[y_col] = pd.to_numeric(d[y_col], errors="coerce")
    d = d.dropna()

    n = len(d)
    if n < 6:
        raise ValueError("Not enough data. Need Part × Operator with repeats.")

    parts = d[part_col].nunique()
    ops = d[op_col].nunique()

    cell_counts = d.groupby([part_col, op_col]).size()
    repeats = int(cell_counts.min()) if len(cell_counts) else 0
    if repeats < 2:
        raise ValueError("Need at least 2 repeats per Part×Operator cell (min cell count).")

    # Fit two-way model with interaction
    formula = f"{y_col} ~ C({part_col}) + C({op_col}) + C({part_col}):C({op_col})"
    model = smf.ols(formula, data=d).fit()

    aov = sm.stats.anova_lm(model, typ=2).copy()

    # Robust: compute mean squares ourselves (some statsmodels versions don't include it)
    if "sum_sq" not in aov.columns or "df" not in aov.columns:
        raise ValueError(f"Unexpected ANOVA table columns: {list(aov.columns)}")

    aov["mean_sq"] = aov["sum_sq"] / aov["df"]

    # Robust: find the correct row keys (index labels can vary slightly)
    idx = list(aov.index)

    def find_row(contains: str) -> str:
        matches = [r for r in idx if contains in str(r)]
        if not matches:
            raise ValueError(f"Could not find ANOVA row containing '{contains}'. Rows: {idx}")
        return matches[0]

    row_part = find_row(f"C({part_col})")
    row_op = find_row(f"C({op_col})")
    row_int = find_row(f"C({part_col}):C({op_col})")
    row_err = find_row("Residual")

    ms_part = float(aov.loc[row_part, "mean_sq"])
    ms_op   = float(aov.loc[row_op, "mean_sq"])
    ms_int  = float(aov.loc[row_int, "mean_sq"])
    ms_err  = float(aov.loc[row_err, "mean_sq"])

    # Variance components (common crossed GRR approximation)
    var_repeat = ms_err
    var_repro_main = max((ms_op - ms_int) / (parts * repeats), 0.0)
    var_int = max((ms_int - ms_err) / repeats, 0.0)

    # Include interaction in reproducibility bucket (common in practice)
    var_repro_total = var_repro_main + var_int
    var_part = max((ms_part - ms_int) / (ops * repeats), 0.0)

    var_grr = var_repeat + var_repro_total
    var_total = var_grr + var_part

    def pct(v: float) -> float:
        return 100.0 * (v / var_total) if var_total > 0 else float("nan")

    return GRRResult(
        n=n, parts=parts, operators=ops, repeats=repeats,
        var_repeat=var_repeat, var_repro=var_repro_total, var_part=var_part, var_total=var_total,
        pct_grr=pct(var_grr), pct_repeat=pct(var_repeat), pct_repro=pct(var_repro_total), pct_part=pct(var_part)
    )
