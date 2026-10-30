from app.data.yahoo_chart import parse_chart_payload


def _payload(closes, opens=None, volumes=None):
    n = len(closes)
    return {
        "timestamp": [1793331900 + 86400 * i for i in range(n)],
        "indicators": {
            "quote": [{
                "open": opens if opens is not None else closes,
                "high": closes,
                "low": closes,
                "close": closes,
                "volume": volumes if volumes is not None else [1000] * n,
            }],
            "adjclose": [{"adjclose": closes}],
        },
    }


def test_parse_daily_normalizes_to_midnight():
    df = parse_chart_payload(_payload([1164.9, 1168.0]), "1d")
    assert df is not None
    assert len(df) == 2
    assert all(ts.hour == 0 and ts.minute == 0 for ts in df.index)
    assert df.attrs["source"] == "live"
    assert df["Close"].iloc[-1] == 1168.0


def test_parse_skips_null_closes():
    df = parse_chart_payload(_payload([1164.9, None, 1168.0]), "1d")
    assert df is not None
    assert len(df) == 2
    assert list(df["Close"]) == [1164.9, 1168.0]


def test_parse_intraday_keeps_times():
    df = parse_chart_payload(_payload([1164.9, 1165.2]), "5m")
    assert df is not None
    assert any(ts.hour or ts.minute for ts in df.index)


def test_parse_empty_returns_none():
    assert parse_chart_payload(None, "1d") is None
    assert parse_chart_payload({}, "1d") is None
    assert parse_chart_payload(
        {"timestamp": [], "indicators": {"quote": [{"close": []}]}}, "1d"
    ) is None


def test_fetch_chart_backs_off_on_429_then_succeeds(monkeypatch):
    """A 429 must not trigger an instant host failover: the round backs off
    and retries, and a later 200 still yields a frame."""
    from app.data import yahoo_chart

    calls = []

    class Resp:
        def __init__(self, status, payload=None):
            self.status_code = status
            self._payload = payload

        def json(self):
            return {"chart": {"result": [self._payload]}}

    responses = [
        Resp(429),
        Resp(200, _payload([1164.9, 1168.0])),
    ]

    def fake_get(url, params=None, headers=None, timeout=None):
        calls.append(url)
        return responses.pop(0)

    sleeps = []
    monkeypatch.setattr(yahoo_chart.requests, "get", fake_get)
    monkeypatch.setattr(yahoo_chart.time, "sleep", lambda s: sleeps.append(s))
    monkeypatch.setattr(yahoo_chart, "_MIN_GAP", 0)

    df = yahoo_chart.fetch_chart("RELIANCE.NS", "1y", "1d")
    assert df is not None
    assert df["Close"].iloc[-1] == 1168.0
    # First call hit query1 and 429'd; the retry waited before succeeding.
    assert calls[0].startswith("https://query1.finance.yahoo.com/")
    assert any(s >= 2.0 for s in sleeps)


def test_fetch_chart_honors_retry_after(monkeypatch):
    """A 429 carrying Retry-After waits that long (not just the backoff)."""
    from app.data import yahoo_chart

    class Resp:
        def __init__(self, status, payload=None, headers=None):
            self.status_code = status
            self._payload = payload
            self.headers = headers or {}

        def json(self):
            return {"chart": {"result": [self._payload]}}

    responses = [
        Resp(429, headers={"Retry-After": "30"}),
        Resp(200, _payload([1164.9, 1168.0])),
    ]

    monkeypatch.setattr(
        yahoo_chart.requests, "get",
        lambda *a, **k: responses.pop(0),
    )
    sleeps = []
    monkeypatch.setattr(yahoo_chart.time, "sleep", lambda s: sleeps.append(s))
    monkeypatch.setattr(yahoo_chart, "_MIN_GAP", 0)

    df = yahoo_chart.fetch_chart("RELIANCE.NS", "1y", "1d")
    assert df is not None
    assert sleeps == [30.0]


def test_fetch_chart_gives_up_after_429_rounds(monkeypatch):
    """Persistent 429s across all rounds return None, not a partial frame."""
    from app.data import yahoo_chart

    class Resp:
        status_code = 429

        def json(self):
            raise AssertionError("should not parse a 429 body")

    monkeypatch.setattr(yahoo_chart.requests, "get", lambda *a, **k: Resp())
    monkeypatch.setattr(yahoo_chart.time, "sleep", lambda s: None)
    monkeypatch.setattr(yahoo_chart, "_MIN_GAP", 0)

    assert yahoo_chart.fetch_chart("RELIANCE.NS", "1y", "1d") is None
