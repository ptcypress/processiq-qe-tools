from __future__ import annotations
from dataclasses import dataclass
import pandas as pd
import statsmodels.api as sm

@dataclass
class RegressionResult:
    r2: float
    adj_r2: float
    n: int
    params: dict
    pvalues: dict

def ols(y: pd.Series, X: pd.DataFrame) -> RegressionResult:
    df = pd.concat([y, X], axis=1).dropna()
    y2 = df.iloc[:, 0]
    X2 = df.iloc[:, 1:]
    X2 = sm.add_constant(X2, has_constant="add")
    model = sm.OLS(y2, X2).fit()
    return RegressionResult(
        r2=float(model.rsquared),
        adj_r2=float(model.rsquared_adj),
        n=int(model.nobs),
        params={k: float(v) for k, v in model.params.to_dict().items()},
        pvalues={k: float(v) for k, v in model.pvalues.to_dict().items()},
    )
