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

    # Estimate repeats as the minimum count per Part×Op cell
    cell_counts = d.groupby([part_col, op_col]).size()
    repeats = int(cell_counts.min()) if len(cell_counts) else 0
    if repeats < 2:
        raise ValueError("Need at least 2 repeats per Part×Operator cell (min cell count).")

    # Two-way random effects ANOVA approximation using fixed effects model and mean squares.
    # Model: y ~ C(part) + C(op) + C(part):C(op)
    model = smf.ols(f"{y_col} ~ C({part_col}) + C({op_col}) + C({part_col}):C({op_col})", data=d).fit()
    aov = sm.stats.anova_lm(model, typ=2)

    

    # statsmodels ANOVA table doesn't always include mean_sq; compute it
    aov = aov.copy()
    aov["mean_sq"] = aov["sum_sq"] / aov["df"]

    ms_part = float(aov.loc[f"C({part_col})", "mean_sq"])
    ms_op   = float(aov.loc[f"C({op_col})", "mean_sq"])
    ms_int  = float(aov.loc[f"C({part_col}):C({op_col})", "mean_sq"])
    ms_err  = float(aov.loc["Residual", "mean_sq"])


    # Variance components (common GR&R approximation):
    var_repeat = ms_err
    var_repro = max((ms_op - ms_int) / (parts * repeats), 0.0)
    var_int = max((ms_int - ms_err) / repeats, 0.0)
    # Some methods include interaction in reproducibility; we'll include it there.
    var_repro_total = var_repro + var_int
    var_part = max((ms_part - ms_int) / (ops * repeats), 0.0)

    var_grr = var_repeat + var_repro_total
    var_total = var_grr + var_part

    def pct(v): 
        return 100.0 * (v / var_total) if var_total > 0 else float("nan")

    return GRRResult(
        n=n, parts=parts, operators=ops, repeats=repeats,
        var_repeat=var_repeat, var_repro=var_repro_total, var_part=var_part, var_total=var_total,
        pct_grr=pct(var_grr), pct_repeat=pct(var_repeat), pct_repro=pct(var_repro_total), pct_part=pct(var_part)
    )
