"""Technical indicator engine, pure pandas/numpy implementations.

Implemented here (instead of pandas-ta) to stay compatible with numpy 2.x
and to keep every formula unit-testable. All functions take a DataFrame
with Open/High/Low/Close/Volume columns indexed by date.
"""
import math

import numpy as np
import pandas as pd


# ---------- moving averages ----------

def sma(series: pd.Series, length: int) -> pd.Series:
    return series.rolling(length).mean()


def ema(series: pd.Series, length: int) -> pd.Series:
    return series.ewm(span=length, adjust=False).mean()


def _rma(series: pd.Series, length: int) -> pd.Series:
    """Wilder's smoothing (used by RSI/ATR/ADX)."""
    return series.ewm(alpha=1 / length, adjust=False).mean()


# ---------- momentum ----------

def rsi(close: pd.Series, length: int = 14) -> pd.Series:
    delta = close.diff()
    gain = _rma(delta.clip(lower=0), length)
    loss = _rma(-delta.clip(upper=0), length)
    rs = gain / loss.replace(0, np.nan)
    out = 100 - 100 / (1 + rs)
    return out.fillna(100.0).where(loss.notna(), np.nan)


def macd(close: pd.Series, fast: int = 12, slow: int = 26, signal: int = 9):
    line = ema(close, fast) - ema(close, slow)
    sig = ema(line, signal)
    return line, sig, line - sig


def stochastic(high, low, close, k: int = 14, d: int = 3, smooth: int = 3):
    lowest = low.rolling(k).min()
    highest = high.rolling(k).max()
    raw_k = 100 * (close - lowest) / (highest - lowest).replace(0, np.nan)
    k_line = raw_k.rolling(smooth).mean()
    d_line = k_line.rolling(d).mean()
    return k_line, d_line


def roc(close: pd.Series, length: int = 12) -> pd.Series:
    return close.pct_change(length) * 100


def cci(high, low, close, length: int = 20) -> pd.Series:
    tp = (high + low + close) / 3
    ma = tp.rolling(length).mean()
    md = (tp - ma).abs().rolling(length).mean()
    return (tp - ma) / (0.015 * md.replace(0, np.nan))


# ---------- volatility ----------

def true_range(high, low, close) -> pd.Series:
    prev_close = close.shift(1)
    return pd.concat(
        [high - low, (high - prev_close).abs(), (low - prev_close).abs()], axis=1
    ).max(axis=1)


def atr(high, low, close, length: int = 14) -> pd.Series:
    return _rma(true_range(high, low, close), length)


def bollinger(close: pd.Series, length: int = 20, mult: float = 2.0):
    mid = sma(close, length)
    sd = close.rolling(length).std(ddof=0)
    return mid + mult * sd, mid, mid - mult * sd


# ---------- trend ----------

def adx(high, low, close, length: int = 14):
    up = high.diff()
    down = -low.diff()
    plus_dm = pd.Series(np.where((up > down) & (up > 0), up, 0.0), index=high.index)
    minus_dm = pd.Series(np.where((down > up) & (down > 0), down, 0.0), index=high.index)
    tr = _rma(true_range(high, low, close), length)
    plus_di = 100 * _rma(plus_dm, length) / tr.replace(0, np.nan)
    minus_di = 100 * _rma(minus_dm, length) / tr.replace(0, np.nan)
    dx = 100 * (plus_di - minus_di).abs() / (plus_di + minus_di).replace(0, np.nan)
    return _rma(dx, length), plus_di, minus_di


def supertrend(high, low, close, length: int = 10, mult: float = 3.0):
    """Returns (trend_line, direction) where direction is +1 bullish / -1 bearish."""
    hl2 = (high + low) / 2
    a = atr(high, low, close, length)
    upper = hl2 + mult * a
    lower = hl2 - mult * a

    n = len(close)
    st = np.full(n, np.nan)
    direction = np.full(n, 1)
    fu = upper.to_numpy()
    fl = lower.to_numpy()
    c = close.to_numpy()

    final_upper = fu.copy()
    final_lower = fl.copy()
    for i in range(1, n):
        if math.isnan(fu[i]) or math.isnan(c[i - 1]):
            continue
        final_upper[i] = fu[i] if (fu[i] < final_upper[i - 1] or c[i - 1] > final_upper[i - 1]) else final_upper[i - 1]
        final_lower[i] = fl[i] if (fl[i] > final_lower[i - 1] or c[i - 1] < final_lower[i - 1]) else final_lower[i - 1]
        if c[i] > final_upper[i]:
            direction[i] = 1
        elif c[i] < final_lower[i]:
            direction[i] = -1
        else:
            direction[i] = direction[i - 1]
        st[i] = final_lower[i] if direction[i] == 1 else final_upper[i]
    return (
        pd.Series(st, index=close.index),
        pd.Series(direction, index=close.index),
    )


def ichimoku(high, low, close):
    conv = (high.rolling(9).max() + low.rolling(9).min()) / 2
    base = (high.rolling(26).max() + low.rolling(26).min()) / 2
    span_a = ((conv + base) / 2).shift(26)
    span_b = ((high.rolling(52).max() + low.rolling(52).min()) / 2).shift(26)
    return conv, base, span_a, span_b


# ---------- volume ----------

def obv(close: pd.Series, volume: pd.Series) -> pd.Series:
    direction = np.sign(close.diff()).fillna(0)
    return (direction * volume).cumsum()


def cmf(high, low, close, volume, length: int = 20) -> pd.Series:
    rng = (high - low).replace(0, np.nan)
    mfm = ((close - low) - (high - close)) / rng
    mfv = mfm * volume
    return mfv.rolling(length).sum() / volume.rolling(length).sum().replace(0, np.nan)


def rolling_vwap(high, low, close, volume, length: int = 20) -> pd.Series:
    tp = (high + low + close) / 3
    pv = tp * volume
    return pv.rolling(length).sum() / volume.rolling(length).sum().replace(0, np.nan)


# ---------- master computation ----------

def compute_all(df: pd.DataFrame) -> pd.DataFrame:
    """Append all indicator columns to a copy of the OHLCV frame."""
    out = df.copy()
    h, l, c, v = out["High"], out["Low"], out["Close"], out["Volume"]

    for n in (20, 50, 100, 200):
        out[f"SMA{n}"] = sma(c, n)
        out[f"EMA{n}"] = ema(c, n)

    out["RSI14"] = rsi(c)
    out["MACD"], out["MACD_SIGNAL"], out["MACD_HIST"] = macd(c)
    out["STOCH_K"], out["STOCH_D"] = stochastic(h, l, c)
    out["ROC12"] = roc(c)
    out["CCI20"] = cci(h, l, c)

    out["ATR14"] = atr(h, l, c)
    out["BB_UPPER"], out["BB_MID"], out["BB_LOWER"] = bollinger(c)

    out["ADX14"], out["PLUS_DI"], out["MINUS_DI"] = adx(h, l, c)
    out["ST_LINE"], out["ST_DIR"] = supertrend(h, l, c)
    out["ICHI_CONV"], out["ICHI_BASE"], out["ICHI_A"], out["ICHI_B"] = ichimoku(h, l, c)

    out["OBV"] = obv(c, v)
    out["CMF20"] = cmf(h, l, c, v)
    out["VWAP20"] = rolling_vwap(h, l, c, v)
    out["VOL_SMA20"] = sma(v.astype(float), 20)

    return out


def _val(x):
    if x is None:
        return None
    try:
        f = float(x)
    except (TypeError, ValueError):
        return None
    if math.isnan(f) or math.isinf(f):
        return None
    return round(f, 4)


def snapshot(enriched: pd.DataFrame) -> dict:
    """Latest value of every indicator, JSON-safe."""
    last = enriched.iloc[-1]
    cols = [c for c in enriched.columns if c not in ("Open", "High", "Low", "Close", "Volume")]
    snap = {col: _val(last[col]) for col in cols}
    snap["close"] = _val(last["Close"])
    snap["volume"] = int(last["Volume"]) if not math.isnan(last["Volume"]) else None
    return snap
