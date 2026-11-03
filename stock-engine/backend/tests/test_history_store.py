"""Tests for the persistent daily-candle store and its fetcher wiring."""

from datetime import date

import pandas as pd
import pytest

from app.data import fetcher
from app.data.cache import cache


def _frame_for_dates(dates, closes):
    index = pd.DatetimeIndex([pd.Timestamp(d) for d in dates])
    return pd.DataFrame(
        {
            "Open": closes,
            "High": [c * 1.01 for c in closes],
            "Low": [c * 0.99 for c in closes],
            "Close": closes,
            "Volume": [1_000_000.0] * len(closes),
        },
        index=index,
    )


@pytest.fixture
def store(tmp_path, monkeypatch):
    """history_store pointed at a throwaway SQLite file."""
    from app.data import history_store

    monkeypatch.setattr(history_store, "SQLITE_PATH", str(tmp_path / "hist.db"))
    return history_store


def test_upsert_load_round_trip(store):
    dates = pd.bdate_range("2026-10-01", periods=10)
    closes = [100.0 + i for i in range(10)]
    assert store.upsert("RELIANCE", _frame_for_dates(dates, closes)) == 10
    frame = store.load("RELIANCE", 365)
    assert frame is not None
    assert len(frame) == 10
    assert list(frame["Close"]) == closes
    assert str(frame.index.tz) == "Asia/Kolkata"
    assert frame.attrs["source"] == "upstox"


def test_upsert_stores_only_completed_bars(store, monkeypatch):
    monkeypatch.setattr(store, "today_ist", lambda: date(2026, 11, 3))
    dates = ["2026-10-30", "2026-11-02", "2026-11-03"]
    store.upsert("RELIANCE", _frame_for_dates(dates, [100.0, 101.0, 102.0]))
    frame = store.load("RELIANCE", 365)
    assert list(frame.index.date.astype(str)) == ["2026-10-30", "2026-11-02"]


def test_upsert_never_deletes(store):
    store.upsert("RELIANCE", _frame_for_dates(pd.bdate_range("2026-10-01", periods=5), [100.0] * 5))
    store.upsert("RELIANCE", _frame_for_dates(pd.bdate_range("2026-10-07", periods=3), [200.0] * 3))
    frame = store.load("RELIANCE", 365)
    # Oct 7 overlaps both frames: 5 + 3 - 1 = 7 unique days, and the
    # second upsert replaces Oct 7's bar.
    assert len(frame) == 7
    assert frame.loc["2026-10-07"]["Close"] == 200.0


def test_needs_sync_rules(store, monkeypatch):
    assert store.needs_sync("RELIANCE") is True
    store.upsert("RELIANCE", _frame_for_dates(["2026-11-02"], [100.0]))
    monkeypatch.setattr(store, "today_ist", lambda: date(2026, 11, 3))
    store.mark_synced("RELIANCE")
    assert store.needs_sync("RELIANCE") is False
    store.mark_synced("RELIANCE", day=date(2026, 11, 2))
    assert store.needs_sync("RELIANCE") is True
    monkeypatch.setattr(store, "today_ist", lambda: date(2026, 11, 7))
    assert store.needs_sync("RELIANCE") is False


def test_load_slices_by_days(store, monkeypatch):
    monkeypatch.setattr(store, "today_ist", lambda: date(2026, 11, 3))
    dates = pd.bdate_range("2025-01-01", periods=480)
    store.upsert("RELIANCE", _frame_for_dates(dates, [100.0] * len(dates)))
    frame = store.load("RELIANCE", 30)
    assert frame is not None
    assert frame.index.min().date().isoformat() >= "2026-10-04"
    assert frame.index.max().date().isoformat() == "2026-11-02"


def test_load_coerces_null_volume_to_nan(store):
    import math

    frame = _frame_for_dates(["2026-10-30", "2026-11-02"], [100.0, 101.0])
    frame.loc["2026-11-02", "Volume"] = float("nan")
    store.upsert("RELIANCE", frame)
    loaded = store.load("RELIANCE", 365)
    assert loaded["Volume"].iloc[0] == 1_000_000.0
    assert math.isnan(loaded["Volume"].iloc[1])


def test_fetcher_quote_survives_null_volume_bar(store, monkeypatch):
    from app.data import upstox_chart

    frame = _frame_for_dates(["2026-10-30", "2026-11-02"], [100.0, 101.0])
    frame.loc["2026-11-02", "Volume"] = float("nan")
    store.upsert("RELIANCE", frame)
    store.mark_synced("RELIANCE")
    monkeypatch.setattr(upstox_chart, "available", lambda: True)
    monkeypatch.setattr(upstox_chart, "instrument_key", lambda symbol: "NSE_EQ|TEST")
    monkeypatch.setattr(upstox_chart, "fetch_candles", lambda *a: (_ for _ in ()).throw(AssertionError("store should serve")))
    monkeypatch.setattr(upstox_chart, "fetch_quote", lambda symbol: None)
    monkeypatch.setattr(store, "appendable_today", lambda: False)
    cache.clear()
    quote = fetcher.get_quote("RELIANCE")
    assert quote is not None
    assert quote["volume"] is None
    assert quote["price"] == 101.0
    cache.clear()


def test_fetcher_serves_second_call_from_store(store, monkeypatch):
    from app.data import upstox_chart

    calls = {"n": 0}

    def fake_candles(symbol, range_, interval):
        calls["n"] += 1
        return _frame_for_dates(
            pd.bdate_range("2025-01-01", periods=300),
            [100.0 + i * 0.1 for i in range(300)],
        )

    monkeypatch.setattr(upstox_chart, "available", lambda: True)
    monkeypatch.setattr(upstox_chart, "instrument_key", lambda symbol: "NSE_EQ|TEST")
    monkeypatch.setattr(upstox_chart, "fetch_candles", fake_candles)
    monkeypatch.setattr(upstox_chart, "fetch_quote", lambda symbol: (_ for _ in ()).throw(AssertionError("no live call expected")))
    monkeypatch.setattr(store, "appendable_today", lambda: False)
    cache.clear()

    first = fetcher.get_history("RELIANCE", "1y", None)
    assert first is not None and len(first) > 0
    assert calls["n"] == 1
    assert store.has_bars("RELIANCE")

    cache.clear()
    second = fetcher.get_history("RELIANCE", "1y", None)
    assert second is not None and len(second) == len(first)
    assert calls["n"] == 1
    cache.clear()
