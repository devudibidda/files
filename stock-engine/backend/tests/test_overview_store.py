"""Tests for the persisted market overview and bounded news feeds."""

import io
import urllib.error

import pytest

from app.data import scan_store
from app.data.cache import cache


@pytest.fixture
def sstore(tmp_path, monkeypatch):
    monkeypatch.setattr(scan_store, "SQLITE_PATH", str(tmp_path / "docs.db"))
    return scan_store


def test_doc_store_round_trip(sstore):
    doc = {"indices": [], "breadth": {"advancers": 3, "decliners": 2}}
    computed_at = sstore.save_doc("market:overview", doc)
    loaded, at = sstore.load_doc("market:overview")
    assert loaded["breadth"] == doc["breadth"]
    assert loaded["computedAt"] == computed_at
    assert at == computed_at
    assert sstore.load_doc("missing") == (None, None)


def test_overview_serves_from_store(sstore, monkeypatch):
    from app import market

    doc = {"indices": [], "topGainers": [], "topLosers": [],
           "breadth": {"advancers": 1, "decliners": 0, "unchanged": 0}}
    sstore.save_doc("market:overview", doc)
    monkeypatch.setattr(market, "_market_overview",
                        lambda: (_ for _ in ()).throw(AssertionError("store should serve")))
    cache.clear()
    try:
        result = market.market_overview()
        assert result["breadth"] == doc["breadth"]
        assert result["computedAt"]
    finally:
        cache.clear()


def test_refresh_overview_forces_compute_and_saves(sstore, monkeypatch):
    from app import market

    fresh = {"indices": [], "topGainers": [], "topLosers": [],
             "breadth": {"advancers": 2, "decliners": 1, "unchanged": 0}}
    monkeypatch.setattr(market, "_market_overview", lambda: dict(fresh))
    cache.clear()
    try:
        result = market.refresh_overview()
        assert result["computedAt"]
        loaded, _ = sstore.load_doc("market:overview")
        assert loaded["breadth"] == fresh["breadth"]
        assert market.market_overview()["computedAt"] == result["computedAt"]
    finally:
        cache.clear()


def test_parse_feed_failure_returns_empty(monkeypatch):
    from app.news import rss

    def boom(url, timeout=None):
        raise urllib.error.URLError("boom")

    monkeypatch.setattr("urllib.request.urlopen", boom)
    assert rss._parse_feed("Test", "http://example.invalid/rss", 5) == []


def test_parse_feed_success(monkeypatch):
    from app.news import rss

    feed = (b'<?xml version="1.0"?><rss version="2.0"><channel>'
            b'<item><title>Markets rise</title><link>http://example.invalid/1</link></item>'
            b'</channel></rss>')
    monkeypatch.setattr("urllib.request.urlopen", lambda url, timeout=None: io.BytesIO(feed))
    items = rss._parse_feed("Test", "http://example.invalid/rss", 5)
    assert len(items) == 1
    assert items[0]["title"] == "Markets rise"
