from __future__ import annotations

from pathlib import Path
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
SAMPLE_DIR = ROOT / "sample_data"

QUALITY_PATH = SAMPLE_DIR / "processiq_sample_quality_data.csv"
GRR_PATH = SAMPLE_DIR / "processiq_sample_gage_rr_crossed.csv"

def load_sample_quality() -> pd.DataFrame:
    if not QUALITY_PATH.exists():
        raise FileNotFoundError(f"Missing sample file: {QUALITY_PATH}")
    return pd.read_csv(QUALITY_PATH)

def load_sample_grr() -> pd.DataFrame:
    if not GRR_PATH.exists():
        raise FileNotFoundError(f"Missing sample file: {GRR_PATH}")
    return pd.read_csv(GRR_PATH)
