"""Tests for the local Ollama AI analysis layer (no Ollama needed)."""
import app.ai_analysis as ai


def _quote():
    return {
        "name": "Reliance Industries",
        "sector": "Energy",
        "price": 1300.0,
        "prevClose": 1290.0,
        "changePct": 0.78,
        "dayLow": 1285.0,
        "dayHigh": 1310.0,
        "low52w": 1100.0,
        "high52w": 1500.0,
        "volume": 5000000,
    }


def _report():
    return {
        "verdict": "Strong Buy",
        "score": 61.3,
        "confidence": 68,
        "summary": "Strong Buy: most indicators lean bullish.",
        "weeklyTrend": {"state": "bullish", "reason": "Weekly close above the 10-week EMA."},
        "newsSentiment": {"label": "positive", "score": 0.4, "count": 5},
        "votes": [
            {"indicator": "RSI14", "state": "bullish", "reason": "RSI at 62."},
            {"indicator": "MACD", "state": "bullish", "reason": "MACD above signal."},
        ],
    }


def test_build_prompt_uses_only_supplied_numbers():
    prompt = ai.build_prompt("RELIANCE", _quote(), _report())
    assert "Strong Buy" in prompt
    assert "61.3" in prompt
    assert "1300.0" in prompt
    assert "RSI14" in prompt
    assert "Do not invent numbers" in prompt


def test_cache_roundtrip(monkeypatch, tmp_path):
    db = tmp_path / "test.db"
    monkeypatch.setattr(ai, "SQLITE_PATH", str(db))
    assert ai.load_cached("RELIANCE") is None
    ai._save("RELIANCE", "Test analysis text.", 1300.0, "Strong Buy")
    cached = ai.load_cached("reliance")
    assert cached is not None
    assert cached["status"] == "ready"
    assert cached["text"] == "Test analysis text."
    assert cached["verdict"] == "Strong Buy"


def test_generate_and_store_with_mocked_ollama(monkeypatch, tmp_path):
    db = tmp_path / "test.db"
    monkeypatch.setattr(ai, "SQLITE_PATH", str(db))
    monkeypatch.setattr(ai, "get_quote", lambda symbol: _quote())
    monkeypatch.setattr(ai, "analyze", lambda symbol: _report())
    monkeypatch.setattr(ai, "_ollama_generate", lambda prompt: "Verdict: agrees with Strong Buy.")
    ai._generate_and_store("RELIANCE")
    cached = ai.load_cached("RELIANCE")
    assert cached is not None
    assert cached["text"] == "Verdict: agrees with Strong Buy."


def test_generate_failure_records_error_not_crash(monkeypatch, tmp_path):
    db = tmp_path / "test.db"
    monkeypatch.setattr(ai, "SQLITE_PATH", str(db))
    monkeypatch.setattr(ai, "get_quote", lambda symbol: None)
    monkeypatch.setattr(ai, "analyze", lambda symbol: None)
    ai._generate_and_store("BOGUS")
    assert ai.load_cached("BOGUS") is None
    assert "BOGUS" in ai._errors


class _FakeResp:
    def __init__(self, payload):
        import json as _json

        self._body = _json.dumps(payload).encode("utf-8")

    def read(self):
        return self._body

    def __enter__(self):
        return self

    def __exit__(self, *exc):
        return False


def test_nim_generate_parses_chat_completion(monkeypatch):
    monkeypatch.setattr(ai, "NIM_API_KEY", "test-key")
    monkeypatch.setattr(ai, "NIM_MODEL", "deepseek-ai/deepseek-v4.1-flash")
    seen = {}

    def fake_urlopen(req, timeout=None):
        seen["url"] = req.full_url
        seen["auth"] = req.headers.get("Authorization")
        return _FakeResp(
            {"choices": [{"message": {"content": "Verdict: agrees with Strong Buy."}}]}
        )

    monkeypatch.setattr("urllib.request.urlopen", fake_urlopen)
    text = ai._nim_generate("prompt")
    assert text == "Verdict: agrees with Strong Buy."
    assert seen["url"].endswith("/chat/completions")
    assert seen["auth"] == "Bearer test-key"


def test_nim_failure_falls_back_to_local(monkeypatch, tmp_path):
    import io
    import urllib.error

    db = tmp_path / "test.db"
    monkeypatch.setattr(ai, "SQLITE_PATH", str(db))
    monkeypatch.setattr(ai, "AI_PROVIDER", "nim")
    monkeypatch.setattr(ai, "NIM_API_KEY", "bad-key")
    monkeypatch.setattr(ai, "get_quote", lambda symbol: _quote())
    monkeypatch.setattr(ai, "analyze", lambda symbol: _report())
    monkeypatch.setattr(ai, "_ollama_generate", lambda prompt: "Local fallback text.")

    def failing_urlopen(req, timeout=None):
        raise urllib.error.HTTPError(req.full_url, 401, "Unauthorized", {}, io.BytesIO(b"{}"))

    monkeypatch.setattr("urllib.request.urlopen", failing_urlopen)
    ai._generate_and_store("RELIANCE")
    cached = ai.load_cached("RELIANCE")
    assert cached is not None
    assert cached["text"] == "Local fallback text."
    assert cached["model"] == ai.MODEL


def test_nim_missing_key_falls_back_to_local(monkeypatch, tmp_path):
    db = tmp_path / "test.db"
    monkeypatch.setattr(ai, "SQLITE_PATH", str(db))
    monkeypatch.setattr(ai, "AI_PROVIDER", "nim")
    monkeypatch.setattr(ai, "NIM_API_KEY", "")
    monkeypatch.setattr(ai, "get_quote", lambda symbol: _quote())
    monkeypatch.setattr(ai, "analyze", lambda symbol: _report())
    monkeypatch.setattr(ai, "_ollama_generate", lambda prompt: "Local fallback text.")
    ai._generate_and_store("RELIANCE")
    cached = ai.load_cached("RELIANCE")
    assert cached is not None
    assert cached["text"] == "Local fallback text."
