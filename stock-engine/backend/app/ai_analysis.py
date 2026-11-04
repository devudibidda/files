"""Local AI analysis: plain-language explanation of a technical verdict.

Runs entirely on the host machine through Ollama (localhost:11434, no
external API). Generation is slow on CPU (about 1-3 minutes for an 8B
model on 2 cores), so results are cached one per symbol per trading day
(Asia/Kolkata date) in the same SQLite file as the rest of the app, and
generation runs in a background thread with single-flight per symbol.

On hosts without Ollama (for example Render) generation fails fast with
a clear error and the endpoint reports the feature as unavailable.
"""
import json
import logging
import os
import sqlite3
import threading
import urllib.request
from datetime import datetime
from zoneinfo import ZoneInfo

from .config import SQLITE_PATH
from .data.fetcher import get_quote
from .signals.analysis import analyze

log = logging.getLogger(__name__)

MODEL = os.getenv("AI_MODEL", "qwen3:8b")
OLLAMA_URL = os.getenv("OLLAMA_URL", "http://127.0.0.1:11434")
NUM_CTX = 8192
NUM_PREDICT = 600
GENERATE_TIMEOUT = 600

_lock = threading.Lock()
_running: set[str] = set()
_errors: dict[str, str] = {}


def _today_ist() -> str:
    return datetime.now(ZoneInfo("Asia/Kolkata")).date().isoformat()


def _conn() -> sqlite3.Connection:
    conn = sqlite3.connect(SQLITE_PATH)
    conn.execute(
        """CREATE TABLE IF NOT EXISTS ai_analysis (
            symbol TEXT NOT NULL,
            day TEXT NOT NULL,
            model TEXT NOT NULL,
            text TEXT NOT NULL,
            price REAL,
            verdict TEXT,
            computed_at TEXT NOT NULL,
            PRIMARY KEY (symbol, day)
        )"""
    )
    return conn


def build_prompt(symbol: str, quote: dict, report: dict) -> str:
    """Pack the quote plus technical report into one short prompt."""
    votes = report.get("votes", [])
    vote_lines = [
        "- {ind}: {state} ({reason})".format(
            ind=v.get("indicator"), state=v.get("state"), reason=v.get("reason")
        )
        for v in votes
    ]
    data = (
        "Stock: {name} ({symbol}), sector {sector}\n"
        "Live price: Rs {price} (prev close Rs {prev}, change {chg}% | "
        "day range Rs {low}-{high} | 52-week range Rs {low52}-{high52} | "
        "volume {vol})\n"
        "Technical verdict: {verdict} (score {score}, confidence {conf}%)\n"
        "Summary: {summary}\n"
        "Weekly trend: {wstate} ({wreason})\n"
        "News sentiment: {nlabel} (score {nscore}, {ncount} items)\n"
        "Indicator votes:\n{votes}"
    ).format(
        name=quote.get("name", symbol),
        symbol=symbol,
        sector=quote.get("sector", "?"),
        price=quote.get("price"),
        prev=quote.get("prevClose"),
        chg=quote.get("changePct"),
        low=quote.get("dayLow"),
        high=quote.get("dayHigh"),
        low52=quote.get("low52w"),
        high52=quote.get("high52w"),
        vol=quote.get("volume"),
        verdict=report.get("verdict"),
        score=report.get("score"),
        conf=report.get("confidence"),
        summary=report.get("summary"),
        wstate=report.get("weeklyTrend", {}).get("state"),
        wreason=report.get("weeklyTrend", {}).get("reason"),
        nlabel=report.get("newsSentiment", {}).get("label"),
        nscore=report.get("newsSentiment", {}).get("score"),
        ncount=report.get("newsSentiment", {}).get("count"),
        votes="\n".join(vote_lines),
    )
    return (
        "You are a stock analysis assistant. Using ONLY the data below, "
        "write a concise analysis in plain language, under 200 words, "
        "with exactly these sections:\n"
        "1) Verdict: one line, agree or disagree with the technical verdict and why.\n"
        "2) Key drivers: 3-4 bullets, each tied to a specific number from the data.\n"
        "3) Risks: 2 bullets.\n"
        "4) What to watch: 1-2 bullets on price levels or events that would change the view.\n"
        "Do not invent numbers, news, or events. Do not give a buy or sell recommendation.\n\n"
        + data
    )


def _ollama_generate(prompt: str) -> str:
    """One non-streaming Ollama call. Thinking off: qwen3 otherwise burns
    tokens on a hidden reasoning trace before answering."""
    body = json.dumps(
        {
            "model": MODEL,
            "prompt": prompt,
            "stream": False,
            "think": False,
            "options": {
                "temperature": 0.3,
                "num_ctx": NUM_CTX,
                "num_predict": NUM_PREDICT,
            },
        }
    ).encode("utf-8")
    req = urllib.request.Request(
        OLLAMA_URL.rstrip("/") + "/api/generate",
        data=body,
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    try:
        with urllib.request.urlopen(req, timeout=GENERATE_TIMEOUT) as resp:
            payload = json.loads(resp.read().decode("utf-8"))
    except OSError as exc:
        raise RuntimeError(
            "AI analysis is not available on this server (Ollama unreachable)"
        ) from exc
    text = (payload.get("response") or "").strip()
    if not text:
        raise RuntimeError("Ollama returned an empty response")
    return text


def load_cached(symbol: str) -> dict | None:
    symbol = symbol.upper()
    day = _today_ist()
    with _lock, _conn() as conn:
        row = conn.execute(
            "SELECT model, text, price, verdict, computed_at FROM ai_analysis "
            "WHERE symbol=? AND day=?",
            (symbol, day),
        ).fetchone()
    if not row:
        return None
    return {
        "symbol": symbol,
        "status": "ready",
        "model": row[0],
        "text": row[1],
        "price": row[2],
        "verdict": row[3],
        "computedAt": row[4],
    }


def _save(symbol: str, text: str, price, verdict) -> None:
    symbol = symbol.upper()
    with _lock, _conn() as conn:
        conn.execute(
            "INSERT OR REPLACE INTO ai_analysis "
            "(symbol, day, model, text, price, verdict, computed_at) "
            "VALUES (?,?,?,?,?,?,?)",
            (
                symbol,
                _today_ist(),
                MODEL,
                text,
                price,
                verdict,
                datetime.now(ZoneInfo("Asia/Kolkata")).isoformat(),
            ),
        )


def _generate_and_store(symbol: str) -> None:
    symbol = symbol.upper()
    try:
        quote = get_quote(symbol)
        report = analyze(symbol)
        if not quote or not report:
            raise RuntimeError(f"Not enough data to analyze '{symbol}'")
        text = _ollama_generate(build_prompt(symbol, quote, report))
        _save(symbol, text, quote.get("price"), report.get("verdict"))
        with _lock:
            _errors.pop(symbol, None)
    except Exception as exc:
        log.warning("AI analysis failed for %s: %s", symbol, exc)
        with _lock:
            _errors[symbol] = str(exc)
    finally:
        with _lock:
            _running.discard(symbol)


def status(symbol: str) -> dict:
    """Current state for one symbol: ready, generating, or missing."""
    symbol = symbol.upper()
    cached = load_cached(symbol)
    if cached:
        return cached
    with _lock:
        running = symbol in _running
        error = _errors.get(symbol)
    if running:
        return {"symbol": symbol, "status": "generating", "model": MODEL}
    result: dict = {"symbol": symbol, "status": "missing", "model": MODEL}
    if error:
        result["lastError"] = error
    return result


def request_generation(symbol: str) -> dict:
    """Start background generation unless one is already running or a
    fresh result exists. Returns the current status."""
    symbol = symbol.upper()
    cached = load_cached(symbol)
    if cached:
        return cached
    with _lock:
        if symbol in _running:
            return {"symbol": symbol, "status": "generating", "model": MODEL}
        _running.add(symbol)
        _errors.pop(symbol, None)
    thread = threading.Thread(target=_generate_and_store, args=(symbol,), daemon=True)
    thread.start()
    return {"symbol": symbol, "status": "generating", "model": MODEL}
