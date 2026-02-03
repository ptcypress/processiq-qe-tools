from __future__ import annotations
from dataclasses import dataclass
import numpy as np
import pandas as pd

@dataclass
class CapabilityResult:
    n: int
    mean: float
    stdev_within: float | None
    stdev_overall: float | None
    cp: float | None
    cpk: float | None
    pp: float | None
    ppk: float | None

def _stdev_within_i_mr(x: np.ndarray) -> float | None:
    # Estimate within sigma using MRbar / d2 (d2 for MR of 2 is 1.128)
    if len(x) < 2:
        return None
    mr = np.abs(np.diff(x))
    mrbar = float(np.mean(mr)) if len(mr) else float("nan")
    if not np.isfinite(mrbar) or mrbar <= 0:
        return None
    return mrbar / 1.128

def capability(x: pd.Series, lsl: float | None, usl: float | None) -> CapabilityResult:
    x = pd.to_numeric(x, errors="coerce").dropna().to_numpy()
    n = int(len(x))
    if n == 0:
        return CapabilityResult(0, float("nan"), None, None, None, None, None, None)

    mean = float(np.mean(x))
    st_overall = float(np.std(x, ddof=1)) if n > 1 else None
    st_within = _stdev_within_i_mr(x)

    def calc_cp(st):
        if st is None or not np.isfinite(st) or st <= 0 or lsl is None or usl is None:
            return None
        return (usl - lsl) / (6 * st)

    def calc_cpk(st):
        if st is None or not np.isfinite(st) or st <= 0 or lsl is None or usl is None:
            return None
        return min((usl - mean) / (3 * st), (mean - lsl) / (3 * st))

    def calc_ppk(st):
        if st is None or not np.isfinite(st) or st <= 0:
            return None
        terms = []
        if usl is not None:
            terms.append((usl - mean) / (3 * st))
        if lsl is not None:
            terms.append((mean - lsl) / (3 * st))
        return min(terms) if terms else None

    cp = calc_cp(st_within)
    cpk = calc_cpk(st_within)
    pp = calc_cp(st_overall)
    ppk = calc_ppk(st_overall)

    return CapabilityResult(n=n, mean=mean, stdev_within=st_within, stdev_overall=st_overall, cp=cp, cpk=cpk, pp=pp, ppk=ppk)
