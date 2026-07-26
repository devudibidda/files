import sys
from pathlib import Path

import numpy as np
import pandas as pd
import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))


def make_ohlcv(closes: list[float], start="2024-01-01") -> pd.DataFrame:
    """Build a plausible OHLCV frame from a close series."""
    idx = pd.bdate_range(start, periods=len(closes))
    close = pd.Series(closes, index=idx, dtype=float)
    open_ = close.shift(1).fillna(close.iloc[0])
    high = pd.concat([open_, close], axis=1).max(axis=1) * 1.01
    low = pd.concat([open_, close], axis=1).min(axis=1) * 0.99
    volume = pd.Series(1_000_000.0, index=idx)
    return pd.DataFrame(
        {"Open": open_, "High": high, "Low": low, "Close": close, "Volume": volume}
    )


@pytest.fixture
def uptrend() -> pd.DataFrame:
    """Steady 250-day uptrend 100 → ~340 with mild noise."""
    rng = np.random.RandomState(42)
    closes = 100 * np.cumprod(1 + rng.normal(0.005, 0.004, 250))
    return make_ohlcv(list(closes))


@pytest.fixture
def downtrend() -> pd.DataFrame:
    rng = np.random.RandomState(7)
    closes = 300 * np.cumprod(1 + rng.normal(-0.005, 0.004, 250))
    return make_ohlcv(list(closes))


@pytest.fixture
def sideways() -> pd.DataFrame:
    rng = np.random.RandomState(3)
    closes = 200 + np.cumsum(rng.normal(0, 0.5, 250))
    return make_ohlcv(list(closes))
