"""Deterministic synthetic OHLCV generator.

Used when the live provider is unreachable (sandboxes, rate limits) so the
whole stack stays runnable and demoable. Series are seeded per symbol, so
RELIANCE always looks like the same chart across runs.
"""
import hashlib

import numpy as np
import pandas as pd

# Rough price anchors so demo charts feel plausible per symbol
_BASE_PRICES = {
    "RELIANCE": 2900, "TCS": 3900, "HDFCBANK": 1650, "INFY": 1550,
    "ICICIBANK": 1200, "SBIN": 820, "ITC": 440, "TATAMOTORS": 950,
    "NIFTYBEES": 260, "GOLDBEES": 65, "BANKBEES": 520, "^NSEI": 24500,
    "^BSESN": 80500, "^NSEBANK": 52000,
}


def _seed(symbol: str) -> int:
    return int(hashlib.sha256(symbol.upper().encode()).hexdigest()[:8], 16)


_FULL_DAYS = 1200


def demo_history(symbol: str, days: int = 500) -> pd.DataFrame:
    """Always generates the same full series per symbol, then slices —
    so every chart range shows a consistent price history."""
    full = _full_history(symbol)
    df = full.tail(min(days, _FULL_DAYS)).copy()
    df.attrs["source"] = "demo"
    return df


def _full_history(symbol: str) -> pd.DataFrame:
    key = symbol.upper().removesuffix(".NS").removesuffix(".BO")
    days = _FULL_DAYS
    rng = np.random.RandomState(_seed(key))
    base = _BASE_PRICES.get(key, float(rng.randint(80, 4000)))

    # regime-switching random walk: alternating drift blocks feel like real trends
    n_blocks = -(-days // 60)
    drifts = rng.choice([-0.0012, -0.0004, 0.0004, 0.0009, 0.0015], n_blocks)
    drift = np.repeat(drifts, 60)[:days]
    vol = rng.uniform(0.010, 0.022)
    returns = rng.normal(drift, vol)
    closes = base * np.cumprod(1 + returns)

    idx = pd.bdate_range(end=pd.Timestamp.today().normalize(), periods=days)
    close = pd.Series(closes, index=idx)
    open_ = close.shift(1).fillna(close.iloc[0]) * (1 + rng.normal(0, 0.003, days))
    spread = np.abs(rng.normal(0.008, 0.004, days))
    high = pd.concat([open_, close], axis=1).max(axis=1) * (1 + spread)
    low = pd.concat([open_, close], axis=1).min(axis=1) * (1 - spread)
    volume = pd.Series(
        rng.lognormal(13.5, 0.6, days) * (1 + np.abs(returns) * 25), index=idx
    ).round()

    df = pd.DataFrame(
        {"Open": open_, "High": high, "Low": low, "Close": close, "Volume": volume}
    ).round(2)
    df.attrs["source"] = "demo"
    return df
