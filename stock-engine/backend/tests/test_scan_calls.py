"""Tests for the persistent scan store and the curated Calls view."""

import pytest

from app.data import scan_store
from app.data.cache import cache


@pytest.fixture
def sstore(tmp_path, monkeypatch):
    monkeypatch.setattr(scan_store, "SQLITE_PATH", str(tmp_path / "scans.db"))
    return scan_store


def _row(symbol, verdict, confidence, score, action=None, rr=None):
    return {
        "symbol": symbol,
        "name": symbol,
        "sector": "Test",
        "type": "equity",
        "price": 100.0,
        "score": score,
        "verdict": verdict,
        "confidence": confidence,
        "summary": "test",
        "tradePlan": {"action": action, "riskReward": rr} if action else None,
    }


def test_scan_store_round_trip(sstore):
    rows = [_row("AAA", "Buy", 70, 50.0, "BUY", 2.0)]
    computed_at = sstore.save_scan("screener:universe:all", rows)
    loaded, at = sstore.load_scan("screener:universe:all")
    assert loaded == rows
    assert at == computed_at
    assert sstore.load_scan("screener:universe:etf") == (None, None)


def test_scan_store_overwrite_replaces(sstore):
    sstore.save_scan("k", [_row("AAA", "Buy", 70, 50.0, "BUY", 2.0)])
    sstore.save_scan("k", [_row("BBB", "Sell", 70, -50.0, "AVOID_OR_EXIT", None)])
    loaded, _ = sstore.load_scan("k")
    assert [r["symbol"] for r in loaded] == ["BBB"]


def test_build_calls_quality_filters():
    from app.screener import build_calls

    rows = [
        _row("GOOD1", "Strong Buy", 75, 70.0, "BUY", 2.0),
        _row("GOOD2", "Buy", 65, 60.0, "BUY_ON_DIP", 1.6),
        _row("EDGE", "Buy", 60, 65.0, "BUY", 1.2),
        _row("LOWCONF", "Buy", 50, 80.0, "BUY", 3.0),
        _row("NOPLAN", "Buy", 80, 90.0),
        _row("HOLD", "Hold", 80, 10.0, "WAIT", None),
        _row("BAD1", "Strong Sell", 72, -70.0, "AVOID_OR_EXIT", None),
        _row("BAD2", "Sell", 55, -60.0, "AVOID_OR_EXIT", None),
    ]
    calls = build_calls(rows)
    assert [c["symbol"] for c in calls["buyCalls"]] == ["GOOD1", "EDGE", "GOOD2"]
    assert [c["symbol"] for c in calls["sellCalls"]] == ["BAD1"]


def test_build_calls_ranking_and_cap():
    from app.screener import build_calls

    rows = [_row(f"B{i:02d}", "Buy", 70, float(i), "BUY", 2.0) for i in range(12)]
    rows += [_row(f"S{i:02d}", "Sell", 70, -float(i), "AVOID_OR_EXIT", None) for i in range(12)]
    calls = build_calls(rows)
    assert len(calls["buyCalls"]) == 10
    assert calls["buyCalls"][0]["symbol"] == "B11"
    assert len(calls["sellCalls"]) == 10
    assert calls["sellCalls"][0]["symbol"] == "S11"


def test_scan_universe_serves_from_store(sstore, monkeypatch):
    from app import screener

    rows = [_row("AAA", "Buy", 70, 50.0, "BUY", 2.0)]
    sstore.save_scan("screener:universe:all", rows)
    monkeypatch.setattr(screener, "_compute_scan", lambda *a: (_ for _ in ()).throw(AssertionError("store should serve")))
    cache.clear()
    assert screener.scan_universe(None) == rows
    cache.clear()


def test_refresh_scan_debounce(sstore, monkeypatch):
    from app import screener

    monkeypatch.setattr(screener, "_compute_scan", lambda type_: [_row("AAA", "Buy", 70, 50.0, "BUY", 2.0)])
    rows, _, was_running = screener.refresh_scan(None)
    assert was_running is False
    assert [r["symbol"] for r in rows] == ["AAA"]
    screener._refreshing.add("screener:universe:all")
    try:
        rows, _, was_running = screener.refresh_scan(None)
        assert was_running is True
        assert rows is None
    finally:
        screener._refreshing.discard("screener:universe:all")
