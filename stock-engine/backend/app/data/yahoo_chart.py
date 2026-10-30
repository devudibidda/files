"""Live OHLCV from Yahoo Finance's public chart API (no API key needed).

yfinance's own HTTP layer times out from sandboxed hosts, while the
underlying chart endpoint answers fine, so we call it directly with
plain requests. There is no synthetic data anywhere in this module:
on any failure it returns None and callers surface an honest error.
"""
import logging

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


def fetch_chart(ticker: str, range_: str, interval: str) -> pd.DataFrame | None:
    """Fetch OHLCV for a Yahoo ticker, or None when the feed fails."""
    for host in _HOSTS:
        try:
            resp = requests.get(
                f"https://{host}/v8/finance/chart/{ticker}",
                params={"range": range_, "interval": interval},
                headers=_UA,
                timeout=20,
            )
            if resp.status_code != 200:
                log.warning("chart API %s -> HTTP %s for %s", host, resp.status_code, ticker)
                continue
            result = (resp.json().get("chart", {}).get("result") or [None])[0]
            df = parse_chart_payload(result, interval)
            if df is not None:
                return df
            log.warning("chart API %s returned no usable bars for %s", host, ticker)
        except Exception as exc:
            log.warning("chart fetch failed for %s via %s: %s", ticker, host, exc)
    return None
