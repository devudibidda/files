"""The scan path must not fetch per-symbol news; the single-stock path must.

Screener rows (screener._row) don't include newsSentiment, so the RSS fetch
inside analyze() is pure overhead across the 145-symbol universe — it was
what made a cold scan take minutes and drop. The dashboard Strong Buy
section goes through the same scan path (api.screener('strong_buy')), so it
benefits automatically.
"""

from app.data.cache import cache
from app.news import rss
from app.signals import analysis
from app import screener


def _fake_report(symbol):
    return {
        "symbol": symbol,
        "name": symbol,
        "sector": "Test",
        "type": "equity",
        "price": 100.0,
        "score": 80.0,
        "verdict": "Strong Buy",
        "confidence": 90,
        "indicators": {
            "RSI14": 60.0,
            "ADX14": 30.0,
            "ST_DIR": 1,
            "volume": 2_000_000.0,
            "VOL_SMA20": 1_000_000.0,
            "SMA50": 110.0,
            "SMA200": 90.0,
        },
        "stats": {"distFromHigh52wPct": -2.0},
    }


def test_analyze_default_still_fetches_news(monkeypatch, uptrend):
    uptrend.attrs["source"] = "live"
    calls = []
    monkeypatch.setattr(analysis, "get_history", lambda s, r="2y", i="1d": uptrend)
    monkeypatch.setattr(rss, "stock_news",
                        lambda s: calls.append(s) or [{"sentiment": 1.0}])

    report = analysis._analyze("RELIANCE")
    assert calls == ["RELIANCE"]
    assert report["newsSentiment"]["scoreAdjustment"] == 10.0


def test_analyze_without_news_skips_rss(monkeypatch, uptrend):
    uptrend.attrs["source"] = "live"
    calls = []
    monkeypatch.setattr(analysis, "get_history", lambda s, r="2y", i="1d": uptrend)
    monkeypatch.setattr(rss, "stock_news", lambda s: calls.append(s))

    report = analysis._analyze("RELIANCE", include_news=False)
    assert calls == []
    assert report["newsSentiment"] == {"score": 0.0, "label": "neutral", "count": 0,
                                       "scoreAdjustment": 0.0}


def test_scan_universe_passes_include_news_false(monkeypatch):
    cache.clear()
    calls = []

    def fake_analyze(symbol, include_news=True):
        calls.append((symbol, include_news))
        return _fake_report(symbol)

    monkeypatch.setattr(screener, "analyze", fake_analyze)
    monkeypatch.setattr(screener, "ALL_SYMBOLS", [
        {"symbol": "AAA", "type": "equity"},
        {"symbol": "BBB", "type": "equity"},
    ])

    rows = screener.scan_universe()
    assert [c[0] for c in calls] == ["AAA", "BBB"]
    assert all(c[1] is False for c in calls)
    assert len(rows) == 2 and rows[0]["symbol"] == "AAA"
    cache.clear()


def test_analyze_cache_separates_news_variants(monkeypatch):
    cache.clear()
    calls = []

    def fake_analyze(symbol, account_size=100000, risk_pct=1.0, include_news=True):
        calls.append(include_news)
        return {"symbol": symbol, "news": include_news}

    monkeypatch.setattr(analysis, "_analyze", fake_analyze)
    analysis.analyze("TESTSYM", include_news=True)
    analysis.analyze("TESTSYM", include_news=False)
    analysis.analyze("TESTSYM", include_news=True)
    # Two distinct cache keys (news on/off); the repeat call is a cache hit.
    assert calls == [True, False]
    cache.clear()
