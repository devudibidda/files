"""Tests for the Upstox provider (primary) and its Yahoo fallback wiring.

All HTTP is mocked: no test touches the live Upstox API or any token.
"""
import json
from pathlib import Path

import pandas as pd
import pytest

from app.data import fetcher, upstox_chart
from app.data.symbols import EQUITIES, ETFS

MAPPING_PATH = Path(upstox_chart.__file__).resolve().parent / "upstox_instruments.json"


def _candle_payload(candles):
    return {"status": "success", "data": {"candles": candles}}


def _quote_payload(last_price=None, ohlc=None, volume=None):
    entry = {"ohlc": ohlc or {}, "volume": volume}
    if last_price is not None:
        entry["last_price"] = last_price
    return {"status": "success", "data": {"NSE_EQ:RELIANCE": entry}}


# ---- mapping ----

def test_mapping_covers_universe_and_uses_exact_keys():
    mapping = json.loads(MAPPING_PATH.read_text())
    assert mapping["RELIANCE"] == "NSE_EQ|INE002A01018"
    assert mapping["JPL"] == "NSE_EQ|INE0BJO01010"
    # MOTHERSON must be the EQ equity row, not the D1 debenture row.
    assert mapping["MOTHERSON"] == "NSE_EQ|INE775A01035"
    assert mapping["^NSEI"] == "NSE_INDEX|Nifty 50"
    assert mapping["^BSESN"] == "BSE_INDEX|SENSEX"
    assert mapping["^NSEBANK"] == "NSE_INDEX|Nifty Bank"
    assert mapping["^CNXIT"] == "NSE_INDEX|Nifty IT"
    assert mapping["^INDIAVIX"] == "NSE_INDEX|India VIX"
    assert all(
        v.startswith(("NSE_EQ|", "NSE_INDEX|", "BSE_INDEX|"))
        for v in mapping.values()
    )
    mapped_eq = sum(1 for s, _n, _s in EQUITIES if s in mapping)
    mapped_etf = sum(1 for s, _n, _s in ETFS if s in mapping)
    assert (mapped_eq, mapped_etf) == (122, 18)


def test_instrument_key_lookup_and_unmapped():
    assert upstox_chart.instrument_key("RELIANCE") == "NSE_EQ|INE002A01018"
    assert upstox_chart.instrument_key("reliance.ns") == "NSE_EQ|INE002A01018"
    for sym in ("TATAMOTORS", "ZOMATO", "LTIM", "ICICINXT50", "UTINIFTETF"):
        assert upstox_chart.instrument_key(sym) is None
    # Indices are mapped to Upstox index keys (verified live 2026-11-01),
    # so they no longer fall back to Yahoo on Render.
    assert upstox_chart.instrument_key("^NSEI") == "NSE_INDEX|Nifty 50"
    assert upstox_chart.instrument_key("^BSESN") == "BSE_INDEX|SENSEX"


# ---- candle parsing ----

def test_parse_daily_candles_normalizes_to_midnight():
    payload = _candle_payload([
        ["2026-10-30T00:00:00+05:30", 1170.4, 1174.6, 1152.5, 1164.9, 14753650, 0],
        ["2026-10-29T00:00:00+05:30", 1159.0, 1182.1, 1155.6, 1167.4, 20939623, 0],
    ])
    df = upstox_chart.parse_candles(payload, "1d")
    assert df is not None
    assert len(df) == 2
    assert all(ts.hour == 0 and ts.minute == 0 for ts in df.index)
    assert df.attrs["source"] == "upstox"
    assert df["Close"].iloc[-1] == 1164.9
    assert df["Volume"].iloc[-1] == 14753650


def test_parse_candles_sorts_and_skips_null_closes():
    payload = _candle_payload([
        ["2026-10-30T00:00:00+05:30", 1170.4, 1174.6, 1152.5, 1164.9, 100, 0],
        ["2026-10-29T00:00:00+05:30", 1159.0, 1182.1, 1155.6, None, 100, 0],
        ["2026-10-28T00:00:00+05:30", 1194.5, 1204.3, 1156.4, 1158.0, 100, 0],
    ])
    df = upstox_chart.parse_candles(payload, "1d")
    assert df is not None
    assert list(df["Close"]) == [1158.0, 1164.9]


def test_parse_intraday_keeps_times():
    payload = _candle_payload([
        ["2026-10-30T09:15:00+05:30", 1170.4, 1171.0, 1170.0, 1170.8, 5000, 0],
        ["2026-10-30T09:16:00+05:30", 1170.8, 1172.0, 1170.5, 1171.5, 6000, 0],
    ])
    df = upstox_chart.parse_candles(payload, "5m")
    assert df is not None
    assert any(ts.hour or ts.minute for ts in df.index)


def test_parse_candles_rejects_bad_payloads():
    assert upstox_chart.parse_candles(None, "1d") is None
    assert upstox_chart.parse_candles({}, "1d") is None
    assert upstox_chart.parse_candles({"status": "error", "data": {}}, "1d") is None
    assert upstox_chart.parse_candles(_candle_payload([]), "1d") is None


# ---- quote parsing ----

def test_parse_quote_prefers_last_price():
    q = upstox_chart.parse_quote(_quote_payload(
        last_price=1165.5,
        ohlc={"open": 1170.4, "high": 1174.6, "low": 1152.5, "close": 1164.9},
        volume=12345,
    ))
    assert q["price"] == 1165.5
    assert q["dayOpen"] == 1170.4
    assert q["volume"] == 12345


def test_parse_quote_falls_back_to_ohlc_close():
    q = upstox_chart.parse_quote(_quote_payload(
        ohlc={"open": 1170.4, "high": 1174.6, "low": 1152.5, "close": 1164.9},
    ))
    assert q["price"] == 1164.9
    assert upstox_chart.parse_quote({"status": "error"}) is None
    assert upstox_chart.parse_quote({"status": "success", "data": {}}) is None


# ---- bounded HTTP behaviour ----

class _Resp:
    def __init__(self, status, payload=None):
        self.status_code = status
        self._payload = payload or {}

    def json(self):
        return self._payload


def test_get_retries_network_errors_at_most_twice(monkeypatch):
    calls = []
    monkeypatch.setenv("UPSTOX_ANALYTICS_TOKEN", "dummy")
    monkeypatch.setattr(
        upstox_chart.requests, "get",
        lambda *a, **k: (calls.append((a, k)), (_ for _ in ()).throw(ConnectionError("down")))[1],
    )
    assert upstox_chart._get("/v2/market-quote/quotes") is None
    assert len(calls) == 2


def test_get_does_not_retry_auth_or_quota_errors(monkeypatch):
    for status in (401, 403, 429):
        calls = []
        monkeypatch.setenv("UPSTOX_ANALYTICS_TOKEN", "dummy")
        monkeypatch.setattr(
            upstox_chart.requests, "get",
            lambda *a, **k: (calls.append(k), _Resp(status))[1],
        )
        assert upstox_chart._get("/v2/market-quote/quotes") is None
        assert len(calls) == 1


def test_get_sends_bearer_and_honest_ua_without_redirects(monkeypatch):
    seen = {}
    monkeypatch.setenv("UPSTOX_ANALYTICS_TOKEN", "dummy-token")
    monkeypatch.setattr(
        upstox_chart.requests, "get",
        lambda *a, **k: (seen.update(k), _Resp(200, {"status": "success"}))[1],
    )
    assert upstox_chart._get("/v2/market-quote/quotes") == {"status": "success"}
    assert seen["headers"]["Authorization"] == "Bearer dummy-token"
    assert seen["headers"]["User-Agent"] == "TrendWise/1.0"
    assert seen["allow_redirects"] is False
    assert seen["timeout"] == 20


# ---- fetch URL construction ----

def test_fetch_candles_daily_url(monkeypatch):
    seen = {}
    monkeypatch.setenv("UPSTOX_ANALYTICS_TOKEN", "dummy")
    monkeypatch.setattr(
        upstox_chart, "_get",
        lambda path, params=None: (seen.update(path=path), _candle_payload([
            ["2026-10-30T00:00:00+05:30", 1, 2, 3, 4, 5, 0],
        ]))[1],
    )
    df = upstox_chart.fetch_candles("RELIANCE", "1y", "1d")
    assert df is not None
    assert seen["path"].startswith("/v2/historical-candle/NSE_EQ%7CINE002A01018/day/")
    # Upstox takes (to_date, from_date) in that order.
    parts = seen["path"].rsplit("/", 2)
    assert parts[1] >= parts[2]


def test_fetch_candles_intraday_only_for_today(monkeypatch):
    monkeypatch.setenv("UPSTOX_ANALYTICS_TOKEN", "dummy")
    calls = []
    monkeypatch.setattr(
        upstox_chart, "_get",
        lambda path, params=None: (calls.append(path), _candle_payload([]))[1],
    )
    # 5-day intraday is not served by Upstox v2 intraday: no HTTP at all,
    # so the fetcher falls back to Yahoo for that range.
    assert upstox_chart.fetch_candles("RELIANCE", "5d", "15m") is None
    assert calls == []
    assert upstox_chart.fetch_candles("RELIANCE", "1d", "5m") is None
    assert calls[0].startswith("/v2/historical-candle/intraday/NSE_EQ%7CINE002A01018/1minute")


def test_fetch_skips_unmapped_symbols_without_http(monkeypatch):
    monkeypatch.setenv("UPSTOX_ANALYTICS_TOKEN", "dummy")
    monkeypatch.setattr(
        upstox_chart, "_get",
        lambda *a, **k: (_ for _ in ()).throw(AssertionError("must not call")),
    )
    assert upstox_chart.fetch_candles("ZOMATO", "1y", "1d") is None
    assert upstox_chart.fetch_quote("ZOMATO") is None


# ---- fetcher wiring: Upstox first, Yahoo fallback ----

class _DummyCache:
    def get(self, key):
        return None

    def set(self, key, value, ttl):
        pass


def _frame(monkeypatch, closes=(100.0, 101.0, 102.0)):
    from tests.conftest import make_ohlcv
    return make_ohlcv(list(closes))


def test_fetcher_prefers_upstox_and_skips_yahoo(monkeypatch, uptrend):
    monkeypatch.setattr(fetcher, "cache", _DummyCache())
    monkeypatch.setattr(fetcher.upstox_chart, "available", lambda: True)
    monkeypatch.setattr(fetcher.upstox_chart, "fetch_candles", lambda *a: uptrend)
    monkeypatch.setattr(
        fetcher, "fetch_chart",
        lambda *a: (_ for _ in ()).throw(AssertionError("yahoo must not be called")),
    )
    df = fetcher.get_history("RELIANCE", "1y")
    assert df is not None
    assert len(df) == len(uptrend)


def test_fetcher_falls_back_to_yahoo_when_upstox_fails(monkeypatch, uptrend):
    monkeypatch.setattr(fetcher, "cache", _DummyCache())
    monkeypatch.setattr(fetcher.upstox_chart, "available", lambda: True)
    monkeypatch.setattr(fetcher.upstox_chart, "fetch_candles", lambda *a: None)
    monkeypatch.setattr(fetcher, "fetch_chart", lambda *a: uptrend)
    df = fetcher.get_history("RELIANCE", "1y")
    assert df is not None
    assert len(df) == len(uptrend)


def test_fetcher_skips_upstox_when_no_token(monkeypatch, uptrend):
    monkeypatch.setattr(fetcher, "cache", _DummyCache())
    monkeypatch.setattr(fetcher.upstox_chart, "available", lambda: False)
    monkeypatch.setattr(
        fetcher.upstox_chart, "fetch_candles",
        lambda *a: (_ for _ in ()).throw(AssertionError("upstox must not be called")),
    )
    monkeypatch.setattr(fetcher, "fetch_chart", lambda *a: uptrend)
    assert fetcher.get_history("RELIANCE", "1y") is not None


def test_get_quote_refreshes_live_price(monkeypatch):
    from tests.conftest import make_ohlcv
    frame = make_ohlcv([100.0, 101.0, 102.0])
    monkeypatch.setattr(fetcher, "cache", _DummyCache())
    monkeypatch.setattr(fetcher, "get_history", lambda *a: frame)
    monkeypatch.setattr(fetcher.upstox_chart, "available", lambda: True)
    monkeypatch.setattr(fetcher.upstox_chart, "fetch_quote", lambda *a: {
        "price": 105.0, "dayOpen": 103.0, "dayHigh": 106.0, "dayLow": 102.5,
        "volume": 999,
    })
    q = fetcher.get_quote("RELIANCE")
    assert q["price"] == 105.0
    assert q["prevClose"] == 101.0
    assert q["change"] == 4.0
    assert q["dayHigh"] == 106.0
    assert q["volume"] == 999
    assert q["high52w"] is not None


def test_get_quote_keeps_frame_values_when_quote_fails(monkeypatch):
    from tests.conftest import make_ohlcv
    frame = make_ohlcv([100.0, 101.0, 102.0])
    monkeypatch.setattr(fetcher, "cache", _DummyCache())
    monkeypatch.setattr(fetcher, "get_history", lambda *a: frame)
    monkeypatch.setattr(fetcher.upstox_chart, "available", lambda: True)
    monkeypatch.setattr(fetcher.upstox_chart, "fetch_quote", lambda *a: None)
    q = fetcher.get_quote("RELIANCE")
    assert q["price"] == 102.0
    assert q["change"] == 1.0
