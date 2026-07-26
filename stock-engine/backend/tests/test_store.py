import importlib


def _fresh_store(tmp_path, monkeypatch):
    monkeypatch.setenv("SQLITE_PATH", str(tmp_path / "test.db"))
    from app import config
    importlib.reload(config)
    from app.db import store
    importlib.reload(store)
    return store


def test_watchlist_crud(tmp_path, monkeypatch):
    store = _fresh_store(tmp_path, monkeypatch)
    cid = "client-abc-123"
    assert store.get_watchlist(cid) == []
    assert store.add_watchlist(cid, "reliance") == ["RELIANCE"]
    assert store.add_watchlist(cid, "TCS") == ["RELIANCE", "TCS"]
    # idempotent add
    assert store.add_watchlist(cid, "TCS") == ["RELIANCE", "TCS"]
    # isolated per client
    assert store.get_watchlist("other-client-999") == []
    assert store.remove_watchlist(cid, "RELIANCE") == ["TCS"]


def test_signal_history_dedupes_per_day(tmp_path, monkeypatch):
    store = _fresh_store(tmp_path, monkeypatch)
    store.record_signal("INFY", 42.0, "Buy", 1500.0)
    store.record_signal("INFY", 55.0, "Buy", 1510.0)  # same day → replaces
    hist = store.get_signal_history("INFY")
    assert len(hist) == 1
    assert hist[0]["score"] == 55.0
    assert hist[0]["verdict"] == "Buy"
