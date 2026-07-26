"""Market data layer on top of yfinance, with TTL caching.

All functions return plain pandas objects / dicts and never raise on
provider hiccups — they return None so callers can respond 503/404 cleanly.
"""
import logging
import math

import pandas as pd
import yfinance as yf

from ..config import DEMO_MODE, HISTORY_TTL, QUOTE_TTL
from .cache import cache
from .demo import demo_history
from .symbols import to_yahoo

log = logging.getLogger(__name__)

# yfinance range → (period, interval) presets
RANGE_PRESETS = {
    "1mo": ("1mo", "1d"),
    "3mo": ("3mo", "1d"),
    "6mo": ("6mo", "1d"),
    "1y": ("1y", "1d"),
    "2y": ("2y", "1d"),
    "5y": ("5y", "1wk"),
    "max": ("max", "1mo"),
    "1d": ("1d", "5m"),
    "5d": ("5d", "15m"),
}


def _clean(value):
    if value is None:
        return None
    if isinstance(value, float) and (math.isnan(value) or math.isinf(value)):
        return None
    return value


def get_history(symbol: str, range_: str = "1y", interval: str | None = None) -> pd.DataFrame | None:
    """Daily/intraday OHLCV as a DataFrame with Open/High/Low/Close/Volume columns."""
    period, default_interval = RANGE_PRESETS.get(range_, ("1y", "1d"))
    interval = interval or default_interval
    ticker = to_yahoo(symbol)
    key = f"hist:{ticker}:{period}:{interval}"
    cached_df = cache.get(key)
    if cached_df is not None:
        return cached_df

    df = None
    if DEMO_MODE != "on":
        try:
            df = yf.Ticker(ticker).history(period=period, interval=interval, auto_adjust=True)
        except Exception as exc:
            log.warning("history fetch failed for %s: %s", ticker, exc)
    if (df is None or df.empty) and DEMO_MODE in ("auto", "on"):
        # trading days per range
        days = {"1d": 5, "5d": 10, "1mo": 22, "3mo": 66, "6mo": 130, "1y": 250, "2y": 500, "5y": 900, "max": 1200}.get(range_, 250)
        df = demo_history(symbol, days)
    if df is None or df.empty:
        return None
    source = df.attrs.get("source", "live")
    df = df[["Open", "High", "Low", "Close", "Volume"]].dropna(subset=["Close"])
    df.attrs["source"] = source
    # Intraday history is fresher; cache it briefly
    ttl = HISTORY_TTL if interval in ("1d", "1wk", "1mo") else 300
    cache.set(key, df, ttl)
    return df


def get_quote(symbol: str) -> dict | None:
    """Lightweight quote built from recent daily candles (no fragile fast_info)."""
    ticker = to_yahoo(symbol)
    key = f"quote:{ticker}"
    q = cache.get(key)
    if q is not None:
        return q
    df = get_history(symbol, "3mo")
    if df is None or len(df) < 2:
        return None
    last, prev = df.iloc[-1], df.iloc[-2]
    year = get_history(symbol, "1y")
    high_52w = float(year["High"].max()) if year is not None else None
    low_52w = float(year["Low"].min()) if year is not None else None
    price = float(last["Close"])
    prev_close = float(prev["Close"])
    change = price - prev_close
    q = {
        "symbol": symbol.upper().removesuffix(".NS"),
        "yahoo": ticker,
        "price": round(price, 2),
        "prevClose": round(prev_close, 2),
        "change": round(change, 2),
        "changePct": round(change / prev_close * 100, 2) if prev_close else None,
        "dayOpen": _clean(round(float(last["Open"]), 2)),
        "dayHigh": _clean(round(float(last["High"]), 2)),
        "dayLow": _clean(round(float(last["Low"]), 2)),
        "volume": int(last["Volume"]) if not math.isnan(last["Volume"]) else None,
        "high52w": _clean(round(high_52w, 2)) if high_52w else None,
        "low52w": _clean(round(low_52w, 2)) if low_52w else None,
        "asOf": last.name.isoformat() if hasattr(last.name, "isoformat") else str(last.name),
        "source": df.attrs.get("source", "live"),
    }
    cache.set(key, q, QUOTE_TTL)
    return q


def history_to_candles(df: pd.DataFrame) -> list[dict]:
    """Serialize OHLCV for the frontend chart (lightweight-charts format)."""
    out = []
    for ts, row in df.iterrows():
        t = ts.date().isoformat() if hasattr(ts, "date") else str(ts)
        out.append({
            "time": t,
            "open": round(float(row["Open"]), 2),
            "high": round(float(row["High"]), 2),
            "low": round(float(row["Low"]), 2),
            "close": round(float(row["Close"]), 2),
            "volume": int(row["Volume"]) if not math.isnan(row["Volume"]) else 0,
        })
    return out
