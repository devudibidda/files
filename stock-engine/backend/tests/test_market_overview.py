"""Tests for the market overview: Upstox indices, one shared fetch pool,
and the hard-bounded Yahoo fallback for indices.

All HTTP is mocked: no test touches the live Upstox API or any token.
"""
import time

import pytest

from app import market
from app.data import fetcher, upstox_chart, yahoo_chart
from app.data.symbols import INDICES

EXPECTED_INDEX_KEYS = {
    "^NSEI": "NSE_INDEX|Nifty 50",
    "^BSESN": "BSE_INDEX|SENSEX",
    "^NSEBANK": "NSE_INDEX|Nifty Bank",
    "^CNXIT": "NSE_INDEX|Nifty IT",
    "^INDIAVIX": "NSE_INDEX|India VIX",
}


class _DummyCache:
    def get(self, key):
        return None

    def set(self, key, value, ttl):
        pass


class _Resp:
    def __init__(self, status):
        self.status_code = status
        self.headers = {}

    def json(self):
        return {}


# ---- index keys (verified live 2026-11-01) ----

def test_index_keys_mapped_to_verified_upstox_keys():
    assert len(INDICES) == 5
    for sym, key in EXPECTED_INDEX_KEYS.items():
        assert upstox_chart.instrument_key(sym) == key


def test_index_candle_payload_parses_with_zero_volume():
    # Index candles carry volume 0; the frame must still parse and the
    # last close must match the quote's last price.
    payload = {"status": "success", "data": {"candles": [
        ["2026-10-30T00:00:00+05:30", 22964.5, 23118.1, 22905.1, 23053.1, 0, 0],
        ["2026-10-29T00:00:00+05:30", 22690.65, 22961.95, 22656.75, 22936.75, 0, 0],
    ]}}
    df = upstox_chart.parse_candles(payload, "1d")
    assert df is not None
    assert df["Close"].iloc[-1] == 23053.1
    assert df.attrs["source"] == "upstox"


def test_index_quote_payload_parses():
    q = upstox_chart.parse_quote({"status": "success", "data": {"NSE_INDEX:Nifty 50": {
        "last_price": 23053.1,
        "ohlc": {"open": 22964.5, "high": 23118.1, "low": 22905.1, "close": 23053.1},
        "volume": 0,
    }}})
    assert q["price"] == 23053.1
    assert q["dayHigh"] == 23118.1


# ---- overview shape with mocked quotes ----

def _fake_quote_factory(calls):
    def _fake(symbol, fast=False):
        calls.append((symbol, fast))
        if symbol.startswith("^"):
            return {"symbol": symbol, "changePct": 0.5, "price": 100.0}
        n = abs(hash(symbol)) % 20 - 10
        return {"symbol": symbol, "changePct": float(n), "price": 100.0 + n}
    return _fake


def test_overview_returns_upstox_indices_in_order(monkeypatch):
    calls = []
    monkeypatch.setattr(market, "get_quote", _fake_quote_factory(calls))
    out = market._market_overview()
    assert [idx["symbol"] for idx in out["indices"]] == [i["symbol"] for i in INDICES]
    assert [idx["name"] for idx in out["indices"]] == [i["name"] for i in INDICES]
    # Indices use the bounded fallback; equities keep the full chain.
    for sym, fast in calls:
        assert fast is (sym in EXPECTED_INDEX_KEYS)
    assert len(out["topGainers"]) == 6
    assert len(out["topLosers"]) == 6
    total = out["breadth"]
    assert total["advancers"] + total["decliners"] + total["unchanged"] == 60


def test_overview_omits_failed_indices_without_stalling(monkeypatch):
    def _fake(symbol, fast=False):
        if symbol.startswith("^"):
            return None
        return {"symbol": symbol, "changePct": 1.0, "price": 100.0}

    monkeypatch.setattr(market, "get_quote", _fake)
    out = market._market_overview()
    assert out["indices"] == []
    assert len(out["topGainers"]) == 6


def test_overview_fetches_indices_and_equities_in_parallel(monkeypatch):
    def _slow(symbol, fast=False):
        time.sleep(0.2)
        return {"symbol": symbol, "changePct": 1.0, "price": 100.0}

    monkeypatch.setattr(market, "get_quote", _slow)
    start = time.monotonic()
    out = market._market_overview()
    elapsed = time.monotonic() - start
    # 65 symbols x 0.2s = 13s sequential; one 8-worker pool finishes in ~2s.
    assert elapsed < 6.0
    assert len(out["indices"]) == 5
    assert out["breadth"]["advancers"] == 60


# ---- bounded Yahoo fallback ----

def test_yahoo_fast_mode_makes_a_single_attempt(monkeypatch):
    calls = []
    monkeypatch.setattr(
        yahoo_chart.requests, "get",
        lambda *a, **k: (calls.append(k), _Resp(429))[1],
    )
    assert yahoo_chart.fetch_chart("^NSEI", "1y", "1d", fast=True) is None
    assert len(calls) == 1
    assert calls[0]["timeout"] == 10


def test_yahoo_full_mode_still_retries(monkeypatch):
    calls = []
    monkeypatch.setattr(
        yahoo_chart.requests, "get",
        lambda *a, **k: (calls.append(k), _Resp(429))[1],
    )
    monkeypatch.setattr(yahoo_chart.time, "sleep", lambda *a: None)
    assert yahoo_chart.fetch_chart("^NSEI", "1y", "1d") is None
    # 4 rounds x 1 host in fast-host order... full mode tries both hosts
    # per round but breaks the host loop on 429, so one call per round.
    assert len(calls) == 4


def test_index_quote_threads_bounded_fallback(monkeypatch):
    calls = []
    monkeypatch.setattr(fetcher, "cache", _DummyCache())
    monkeypatch.setattr(fetcher.upstox_chart, "available", lambda: False)
    monkeypatch.setattr(
        fetcher, "fetch_chart",
        lambda *a, **k: (calls.append((a, k)), None)[1],
    )
    assert fetcher.get_quote("^NSEI", fast=True) is None
    assert len(calls) == 1
    # Positional call: (ticker, period, interval, fast_fallback).
    assert calls[0][0] == ("^NSEI", "1y", "1d", True)


def test_equity_quote_keeps_full_fallback_by_default(monkeypatch):
    calls = []
    monkeypatch.setattr(fetcher, "cache", _DummyCache())
    monkeypatch.setattr(fetcher.upstox_chart, "available", lambda: False)
    monkeypatch.setattr(
        fetcher, "fetch_chart",
        lambda *a, **k: (calls.append((a, k)), None)[1],
    )
    assert fetcher.get_quote("RELIANCE") is None
    assert calls[0][0] == ("RELIANCE.NS", "1y", "1d", False)
