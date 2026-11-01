"""Live OHLCV from Upstox's API (primary provider; Yahoo is the fallback).

Upstox access: the Analytics Token is a 1-year, read-only token generated
on the Developer Apps page. It is read from the UPSTOX_ANALYTICS_TOKEN
environment variable at call time (never stored in code or in this repo)
and sent as a Bearer token. Historical candles also answer without a
token, but the token is always sent when configured, because the live
quote endpoint requires it.

Cloudflare on api.upstox.com blocks default library user-agents (HTTP
403 error 1010), so every call sends an honest identifying User-Agent.
Redirects are refused, every call has a timeout, and each call is tried
at most twice: auth/quota failures (401/403/429) are not retried at all,
since retrying them cannot help and the fetcher falls back to Yahoo.

On any failure the fetchers return None and the caller falls back to
Yahoo or surfaces an honest error. There is no synthetic data here.
"""
import json
import logging
import os
from datetime import datetime, timedelta
from pathlib import Path
from zoneinfo import ZoneInfo

import pandas as pd
import requests

log = logging.getLogger(__name__)

_BASE = "https://api.upstox.com"
_HEADERS = {
    "User-Agent": "TrendWise/1.0",
    "Accept": "application/json",
}
_TIMEOUT = 20
_MAX_ATTEMPTS = 2  # one initial try + one retry, per call, never more

# Yahoo-style range -> days of daily history to request from Upstox.
_RANGE_DAYS = {
    "1mo": 30,
    "3mo": 90,
    "6mo": 180,
    "1y": 365,
    "2y": 730,
    "5y": 1825,
    "max": 3650,
}
# Yahoo interval -> Upstox historical-candle interval.
_DAILY_INTERVALS = {"1d": "day", "1wk": "week", "1mo": "month"}
_INTRADAY_INTERVALS = {"5m": "1minute", "15m": "30minute"}

_MAPPING: dict | None = None


def _token() -> str:
    return os.getenv("UPSTOX_ANALYTICS_TOKEN", "")


def available() -> bool:
    """True when a token is configured (mapping is checked per symbol)."""
    return bool(_token())


def _load_mapping() -> dict:
    global _MAPPING
    if _MAPPING is None:
        path = Path(__file__).resolve().parent / "upstox_instruments.json"
        try:
            _MAPPING = json.loads(path.read_text())
        except Exception as exc:
            log.warning("upstox instrument mapping unreadable: %s", exc)
            _MAPPING = {}
    return _MAPPING


def instrument_key(symbol: str) -> str | None:
    """Map a TrendWise symbol to its Upstox instrument key, or None.

    Accepts a bare NSE code or a Yahoo-style ticker. Symbols with no exact
    match in the instruments file are unmapped by design (never guessed)
    and the caller falls back to Yahoo.
    """
    key = symbol.upper().removesuffix(".NS").removesuffix(".BO")
    return _load_mapping().get(key)


def parse_candles(payload: dict, interval: str) -> pd.DataFrame | None:
    """Turn an Upstox historical-candle payload into an OHLCV frame.

    Upstox candles are [timestamp, open, high, low, close, volume, oi]
    arrays; timestamps are ISO strings in IST.
    """
    if not payload or payload.get("status") != "success":
        return None
    candles = (payload.get("data") or {}).get("candles") or []
    rows = []
    for c in candles:
        if not c or len(c) < 6 or c[4] is None:
            continue
        rows.append({
            "ts": c[0],
            "Open": c[1],
            "High": c[2],
            "Low": c[3],
            "Close": c[4],
            "Volume": c[5],
        })
    if not rows:
        return None
    df = pd.DataFrame(rows).set_index(
        pd.to_datetime([r["ts"] for r in rows])
    ).drop(columns=["ts"])
    df.index = df.index.tz_convert("Asia/Kolkata") if df.index.tz is not None else df.index.tz_localize("Asia/Kolkata")
    if interval in _DAILY_INTERVALS:
        # Daily/weekly/monthly bars are calendar buckets; normalize to
        # midnight so they are never mistaken for intraday bars.
        df.index = df.index.normalize()
    df = df.sort_index()
    df.attrs["source"] = "upstox"
    return df


def parse_quote(payload: dict) -> dict | None:
    """Turn an Upstox market-quote payload into live price fields."""
    if not payload or payload.get("status") != "success":
        return None
    data = payload.get("data") or {}
    if not data:
        return None
    entry = next(iter(data.values()))
    ohlc = entry.get("ohlc") or {}
    price = entry.get("last_price")
    if price is None:
        price = ohlc.get("close")
    if price is None:
        return None
    return {
        "price": float(price),
        "dayOpen": ohlc.get("open"),
        "dayHigh": ohlc.get("high"),
        "dayLow": ohlc.get("low"),
        "volume": entry.get("volume"),
    }


def _get(path: str, params: dict | None = None) -> dict | None:
    """GET one Upstox endpoint with at most _MAX_ATTEMPTS tries.

    Returns the parsed JSON body on HTTP 200, else None. 401/403/429
    are not retried: the token or quota will not heal within a scan,
    and the fetcher's Yahoo fallback is the right next step.
    """
    token = _token()
    headers = dict(_HEADERS)
    if token:
        headers["Authorization"] = f"Bearer {token}"
    for attempt in range(_MAX_ATTEMPTS):
        try:
            resp = requests.get(
                _BASE + path,
                params=params,
                headers=headers,
                timeout=_TIMEOUT,
                allow_redirects=False,
            )
        except Exception as exc:
            log.warning("upstox %s failed (attempt %d): %s", path, attempt + 1, exc)
            continue
        if resp.status_code == 200:
            try:
                return resp.json()
            except Exception as exc:
                log.warning("upstox %s returned unparsable JSON: %s", path, exc)
                return None
        if resp.status_code in (401, 403, 429):
            log.warning("upstox %s -> HTTP %s (not retried)", path, resp.status_code)
            return None
        log.warning("upstox %s -> HTTP %s (attempt %d)", path, resp.status_code, attempt + 1)
    return None


def _enc(key: str) -> str:
    return key.replace("|", "%7C")


def fetch_candles(symbol: str, range_: str, interval: str) -> pd.DataFrame | None:
    """Fetch OHLCV for a TrendWise symbol via Upstox, or None.

    Daily/weekly/monthly ranges use the historical-candle endpoint with
    an explicit date window. Intraday is only supported for today's bars
    (Upstox v2 intraday returns the current day), so any other intraday
    range returns None and the caller falls back to Yahoo.
    """
    key = instrument_key(symbol)
    if key is None:
        return None
    enc = _enc(key)
    if interval in _DAILY_INTERVALS:
        up_interval = _DAILY_INTERVALS[interval]
        today = datetime.now(ZoneInfo("Asia/Kolkata")).date()
        days = _RANGE_DAYS.get(range_, 365)
        # Upstox takes (to_date, from_date) in that order.
        to_date = today.isoformat()
        from_date = (today - timedelta(days=days)).isoformat()
        payload = _get(f"/v2/historical-candle/{enc}/{up_interval}/{to_date}/{from_date}")
        return parse_candles(payload, interval) if payload else None
    if interval in _INTRADAY_INTERVALS:
        if range_ != "1d":
            return None
        up_interval = _INTRADAY_INTERVALS[interval]
        payload = _get(f"/v2/historical-candle/intraday/{enc}/{up_interval}")
        return parse_candles(payload, interval) if payload else None
    return None


def fetch_quote(symbol: str) -> dict | None:
    """Fetch live price fields for a TrendWise symbol, or None."""
    key = instrument_key(symbol)
    if key is None:
        return None
    payload = _get("/v2/market-quote/quotes", params={"instrument_key": key})
    return parse_quote(payload) if payload else None
