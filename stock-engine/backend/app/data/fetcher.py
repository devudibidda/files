"""Market data layer: Upstox first, Yahoo Finance's chart API as fallback.

Live data only, there is no synthetic fallback anywhere in this module.
All functions return plain pandas objects / dicts and never raise on
provider hiccups, they return None so callers can respond 503/404 cleanly.
"""
import logging
import math

import pandas as pd

from ..config import HISTORY_TTL, QUOTE_TTL
from .cache import cache
from .symbols import to_yahoo
from . import upstox_chart
from .yahoo_chart import fetch_chart

log = logging.getLogger(__name__)

# chart API range → interval presets
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


def get_history(symbol: str, range_: str = "1y", interval: str | None = None, fast_fallback: bool = False) -> pd.DataFrame | None:
    """Daily/intraday OHLCV as a DataFrame with Open/High/Low/Close/Volume columns.

    fast_fallback=True bounds the Yahoo fallback to a single quick
    attempt (used for overview indices, where a dead feed must cost
    seconds, not the full backoff chain).
    """
    period, default_interval = RANGE_PRESETS.get(range_, ("1y", "1d"))
    interval = interval or default_interval
    ticker = to_yahoo(symbol)
    key = f"hist:{ticker}:{period}:{interval}"
    cached_df = cache.get(key)
    if cached_df is not None:
        return cached_df

    # Upstox first when configured; Yahoo fallback covers unmapped
    # symbols, unsupported ranges, and Upstox outages.
    df = None
    if upstox_chart.available():
        df = upstox_chart.fetch_candles(symbol, range_, interval)
    if df is None:
        # Positional fast flag: keeps the existing *args-only test
        # doubles working (they predate the flag).
        df = fetch_chart(ticker, period, interval, fast_fallback)
    if df is None or df.empty:
        return None
    source = df.attrs.get("source", "live")
    df = df[["Open", "High", "Low", "Close", "Volume"]].dropna(subset=["Close"])
    df.attrs["source"] = source
    # Intraday history is fresher; cache it briefly
    ttl = HISTORY_TTL if interval in ("1d", "1wk", "1mo") else 300
    cache.set(key, df, ttl)
    return df


def get_quote(symbol: str, fast: bool = False) -> dict | None:
    """Lightweight quote built from recent daily candles (no fragile fast_info).

    Uses the 1y frame alone: its last two bars give price/prevClose/day
    OHLC and its full span gives the 52-week extremes, so a quote costs
    one Yahoo fetch instead of two (the old 3mo + 1y pair).

    fast=True bounds the Yahoo fallback to a single quick attempt; it
    only matters when Upstox cannot serve the symbol (overview indices
    use it so a dead feed cannot stall the page).
    """
    ticker = to_yahoo(symbol)
    key = f"quote:{ticker}"
    q = cache.get(key)
    if q is not None:
        return q
    df = get_history(symbol, "1y", None, fast)
    if df is None or len(df) < 2:
        return None
    last, prev = df.iloc[-1], df.iloc[-2]
    high_52w = float(df["High"].max())
    low_52w = float(df["Low"].min())
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
    # Live refresh: when Upstox answers, its quote is today's traded price
    # while the daily frame's last bar may be yesterday's close. Only the
    # price/day-OHLC/volume fields move; prevClose, 52-week extremes and
    # asOf stay frame-derived, and any quote failure keeps frame values.
    if upstox_chart.available():
        live = upstox_chart.fetch_quote(symbol)
        if live and live.get("price"):
            price = float(live["price"])
            q["price"] = round(price, 2)
            q["change"] = round(price - prev_close, 2)
            q["changePct"] = round((price - prev_close) / prev_close * 100, 2) if prev_close else None
            for field, live_key in (
                ("dayOpen", "dayOpen"),
                ("dayHigh", "dayHigh"),
                ("dayLow", "dayLow"),
            ):
                if live.get(live_key) is not None:
                    q[field] = _clean(round(float(live[live_key]), 2))
            if live.get("volume") is not None:
                q["volume"] = int(live["volume"])
    cache.set(key, q, QUOTE_TTL)
    return q


def is_intraday(df: pd.DataFrame) -> bool:
    """True when candles carry time-of-day (5m/15m bars), not just dates.

    Daily bars from the chart API are normalized to midnight; intraday bars carry
    market hours. The chart library needs distinct time keys per bar, so
    intraday data must not be collapsed to dates.
    """
    for ts in df.index[:10]:
        try:
            if ts.hour or ts.minute or ts.second:
                return True
        except AttributeError:
            continue
    return False


def time_key(ts, intraday: bool):
    """Chart time key: unix seconds for intraday, YYYY-MM-DD for daily+.

    lightweight-charts accepts one time format per series, so callers must
    use the same intraday flag for candles and overlays of one response.
    """
    if intraday:
        return int(ts.timestamp())
    return ts.date().isoformat() if hasattr(ts, "date") else str(ts)


def history_to_candles(df: pd.DataFrame) -> list[dict]:
    """Serialize OHLCV for the frontend chart (lightweight-charts format)."""
    intraday = is_intraday(df)
    out = []
    for ts, row in df.iterrows():
        out.append({
            "time": time_key(ts, intraday),
            "open": round(float(row["Open"]), 2),
            "high": round(float(row["High"]), 2),
            "low": round(float(row["Low"]), 2),
            "close": round(float(row["Close"]), 2),
            "volume": int(row["Volume"]) if not math.isnan(row["Volume"]) else 0,
        })
    return out
