"""Live OHLCV from Yahoo Finance's public chart API (no API key needed).

yfinance's own HTTP layer times out from sandboxed hosts, while the
underlying chart endpoint answers fine, so we call it directly with
plain requests. There is no synthetic data anywhere in this module:
on any failure it returns None and callers surface an honest error.
"""
import logging
import threading
import time

import pandas as pd
import requests

log = logging.getLogger(__name__)

_HOSTS = ("query1.finance.yahoo.com", "query2.finance.yahoo.com")
_UA = {
    "User-Agent": (
        "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 "
        "Chrome/120 Safari/537.36"
    )
}
# Yahoo rate-limits shared hosting IPs (Render free shares one egress IP
# with many other apps), and our overview/screener bursts used to trip it
# instantly: 60-145 symbols fetched at 8 concurrent workers. A process-wide
# gap between calls plus backoff on 429 keeps us under the limit instead
# of hammering a tripped quota with immediate host failovers.
# Tuning history: 0.3s gaps + 2s/8s backoffs (Oct 30) got only 1 of 60
# overview symbols through on Render, so round 2 goes much slower: 1s
# gaps and up to 60s backoffs, honoring Yahoo's Retry-After when sent.
# Cost: a cold overview takes ~60s+; its 5-min cache means only the first
# load after expiry pays that.
_MIN_GAP = 1.0  # seconds between Yahoo calls, across all threads
_BACKOFFS = (0.0, 5.0, 20.0, 60.0)  # waits before retry rounds after a 429
_CALL_LOCK = threading.Lock()
_LAST_CALL = 0.0


def _throttle():
    """Space Yahoo calls at least _MIN_GAP apart, process-wide."""
    global _LAST_CALL
    with _CALL_LOCK:
        wait = _MIN_GAP - (time.monotonic() - _LAST_CALL)
        if wait > 0:
            time.sleep(wait)
        _LAST_CALL = time.monotonic()
# Intervals whose bars are calendar buckets, not intraday timestamps.
_BUCKET_INTERVALS = ("1d", "1wk", "1mo")


def parse_chart_payload(result: dict, interval: str) -> pd.DataFrame | None:
    """Turn one chart-API result into an OHLCV frame, or None if unusable."""
    if not result:
        return None
    timestamps = result.get("timestamp") or []
    quotes = (result.get("indicators", {}).get("quote") or [None])[0] or {}
    closes = quotes.get("close") or []
    if not timestamps or not closes:
        return None
    n = min(len(timestamps), len(closes))
    adj = (result.get("indicators", {}).get("adjclose") or [None])[0] or {}
    adjcloses = adj.get("adjclose") or []

    def at(key, i):
        arr = quotes.get(key)
        return arr[i] if arr is not None and i < len(arr) else None

    rows = []
    for i in range(n):
        close = closes[i]
        if close is None:
            continue
        factor = 1.0
        if i < len(adjcloses) and adjcloses[i] is not None and close:
            factor = adjcloses[i] / close
        def scaled(key):
            v = at(key, i)
            return None if v is None else v * factor
        rows.append({
            "ts": timestamps[i],
            "Open": scaled("open"),
            "High": scaled("high"),
            "Low": scaled("low"),
            "Close": close * factor,
            "Volume": at("volume", i),
        })
    if not rows:
        return None
    df = pd.DataFrame(rows).set_index(
        pd.to_datetime([r["ts"] for r in rows], unit="s", utc=True)
        .tz_convert("Asia/Kolkata")
    ).drop(columns=["ts"])
    if interval in _BUCKET_INTERVALS:
        # Daily/weekly/monthly bars arrive stamped at market open; normalize
        # to midnight so they are never mistaken for intraday bars.
        df.index = df.index.normalize()
    df.attrs["source"] = "live"
    return df


def fetch_chart(ticker: str, range_: str, interval: str, fast: bool = False) -> pd.DataFrame | None:
    """Fetch OHLCV for a Yahoo ticker, or None when the feed fails.

    On a 429 the other host is NOT tried immediately (it shares the same
    per-IP quota, so an instant failover just doubles the burst); instead
    the round backs off and retries, up to 3 rounds.

    fast=True is the hard-bounded mode used for index fallback in the
    overview: a single attempt against the first host with a short
    timeout and no backoff chain, so a dead Yahoo feed costs seconds,
    not minutes, and the caller simply omits that index.
    """
    rounds = (0.0,) if fast else _BACKOFFS
    hosts = _HOSTS[:1] if fast else _HOSTS
    timeout = 10 if fast else 20
    retry_after = 0.0
    for round_no, backoff in enumerate(rounds):
        wait = max(backoff, retry_after)
        if wait:
            time.sleep(wait)
        retry_after = 0.0
        for host in hosts:
            _throttle()
            try:
                resp = requests.get(
                    f"https://{host}/v8/finance/chart/{ticker}",
                    params={"range": range_, "interval": interval},
                    headers=_UA,
                    timeout=timeout,
                )
            except Exception as exc:
                log.warning("chart fetch failed for %s via %s: %s", ticker, host, exc)
                continue
            if resp.status_code == 429:
                raw = (getattr(resp, "headers", {}) or {}).get("Retry-After")
                try:
                    retry_after = min(float(raw), 60.0) if raw is not None else 0.0
                except (TypeError, ValueError):
                    retry_after = 0.0
                log.warning(
                    "chart API %s -> HTTP 429 for %s (round %d)",
                    host, ticker, round_no,
                )
                break
            if resp.status_code != 200:
                log.warning("chart API %s -> HTTP %s for %s", host, resp.status_code, ticker)
                continue
            result = (resp.json().get("chart", {}).get("result") or [None])[0]
            df = parse_chart_payload(result, interval)
            if df is not None:
                return df
            log.warning("chart API %s returned no usable bars for %s", host, ticker)
    return None
