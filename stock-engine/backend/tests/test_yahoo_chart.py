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
