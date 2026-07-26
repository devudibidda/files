import math

import numpy as np
import pandas as pd

from app.indicators import engine
from tests.conftest import make_ohlcv


def test_sma_known_values():
    s = pd.Series([1, 2, 3, 4, 5], dtype=float)
    result = engine.sma(s, 3)
    assert math.isnan(result.iloc[1])
    assert result.iloc[2] == 2.0
    assert result.iloc[4] == 4.0


def test_ema_converges_to_constant():
    s = pd.Series([50.0] * 100)
    assert abs(engine.ema(s, 20).iloc[-1] - 50.0) < 1e-9


def test_rsi_extremes():
    up = pd.Series(np.linspace(100, 200, 60))
    down = pd.Series(np.linspace(200, 100, 60))
    assert engine.rsi(up).iloc[-1] > 99
    assert engine.rsi(down).iloc[-1] < 1


def test_rsi_bounded(sideways):
    r = engine.rsi(sideways["Close"]).dropna()
    assert ((r >= 0) & (r <= 100)).all()


def test_macd_sign_in_trends(uptrend, downtrend):
    line_up, _, _ = engine.macd(uptrend["Close"])
    line_dn, _, _ = engine.macd(downtrend["Close"])
    assert line_up.iloc[-1] > 0
    assert line_dn.iloc[-1] < 0


def test_bollinger_ordering(sideways):
    upper, mid, lower = engine.bollinger(sideways["Close"])
    tail = slice(-100, None)
    assert (upper.iloc[tail] >= mid.iloc[tail]).all()
    assert (mid.iloc[tail] >= lower.iloc[tail]).all()


def test_atr_positive(uptrend):
    a = engine.atr(uptrend["High"], uptrend["Low"], uptrend["Close"]).dropna()
    assert (a > 0).all()


def test_adx_strong_trend_vs_chop(uptrend, sideways):
    adx_up, plus_di, minus_di = engine.adx(uptrend["High"], uptrend["Low"], uptrend["Close"])
    adx_flat, _, _ = engine.adx(sideways["High"], sideways["Low"], sideways["Close"])
    assert adx_up.iloc[-1] > adx_flat.iloc[-1]
    assert plus_di.iloc[-1] > minus_di.iloc[-1]


def test_supertrend_direction(uptrend, downtrend):
    _, dir_up = engine.supertrend(uptrend["High"], uptrend["Low"], uptrend["Close"])
    _, dir_dn = engine.supertrend(downtrend["High"], downtrend["Low"], downtrend["Close"])
    assert dir_up.iloc[-1] == 1
    assert dir_dn.iloc[-1] == -1


def test_stochastic_bounds(sideways):
    k, d = engine.stochastic(sideways["High"], sideways["Low"], sideways["Close"])
    k, d = k.dropna(), d.dropna()
    assert ((k >= 0) & (k <= 100)).all()
    assert ((d >= 0) & (d <= 100)).all()


def test_obv_rises_in_uptrend(uptrend):
    o = engine.obv(uptrend["Close"], uptrend["Volume"])
    assert o.iloc[-1] > o.iloc[20]


def test_compute_all_and_snapshot(uptrend):
    enriched = engine.compute_all(uptrend)
    snap = engine.snapshot(enriched)
    # every value must be JSON-safe (no NaN/inf)
    for key, val in snap.items():
        if isinstance(val, float):
            assert not math.isnan(val), key
            assert not math.isinf(val), key
    assert snap["RSI14"] is not None
    assert snap["EMA200"] is not None
    assert snap["ST_DIR"] in (1, -1)


def test_short_history_does_not_crash():
    df = make_ohlcv([100, 101, 102, 103, 104])
    enriched = engine.compute_all(df)
    snap = engine.snapshot(enriched)
    assert snap["close"] == 104
    assert snap["SMA200"] is None
