"""Persistence layer: watchlists + daily signal history.

Uses Supabase (free Postgres) via its REST API when SUPABASE_URL/KEY are
set; otherwise falls back to a local SQLite file so the app runs with
zero external setup. See supabase_schema.sql for the hosted tables.
"""
import logging
import sqlite3
import threading
from datetime import date

import httpx

from ..config import SQLITE_PATH, SUPABASE_KEY, SUPABASE_URL

log = logging.getLogger(__name__)

_use_supabase = bool(SUPABASE_URL and SUPABASE_KEY)
_lock = threading.Lock()


# ---------- SQLite backend ----------

def _conn() -> sqlite3.Connection:
    conn = sqlite3.connect(SQLITE_PATH)
    conn.execute(
        """CREATE TABLE IF NOT EXISTS watchlist (
            client_id TEXT NOT NULL,
            symbol TEXT NOT NULL,
            added_at TEXT DEFAULT CURRENT_TIMESTAMP,
            PRIMARY KEY (client_id, symbol)
        )"""
    )
    conn.execute(
        """CREATE TABLE IF NOT EXISTS signal_history (
            symbol TEXT NOT NULL,
            day TEXT NOT NULL,
            score REAL NOT NULL,
            verdict TEXT NOT NULL,
            price REAL,
            PRIMARY KEY (symbol, day)
        )"""
    )
    return conn


# ---------- Supabase REST helpers ----------

def _sb_headers() -> dict:
    return {
        "apikey": SUPABASE_KEY,
        "Authorization": f"Bearer {SUPABASE_KEY}",
        "Content-Type": "application/json",
        "Prefer": "resolution=merge-duplicates,return=minimal",
    }


def _sb(method: str, table: str, *, params=None, json_body=None) -> httpx.Response | None:
    url = f"{SUPABASE_URL.rstrip('/')}/rest/v1/{table}"
    try:
        return httpx.request(method, url, headers=_sb_headers(), params=params, json=json_body, timeout=10)
    except Exception as exc:
        log.warning("supabase %s %s failed: %s", method, table, exc)
        return None


# ---------- public API ----------

def get_watchlist(client_id: str) -> list[str]:
    if _use_supabase:
        r = _sb("GET", "watchlist", params={"client_id": f"eq.{client_id}", "select": "symbol"})
        return [row["symbol"] for row in r.json()] if r is not None and r.status_code == 200 else []
    with _lock, _conn() as conn:
        rows = conn.execute(
            "SELECT symbol FROM watchlist WHERE client_id=? ORDER BY added_at", (client_id,)
        ).fetchall()
    return [r[0] for r in rows]


def add_watchlist(client_id: str, symbol: str) -> list[str]:
    symbol = symbol.upper()
    if _use_supabase:
        _sb("POST", "watchlist", json_body={"client_id": client_id, "symbol": symbol})
    else:
        with _lock, _conn() as conn:
            conn.execute(
                "INSERT OR IGNORE INTO watchlist (client_id, symbol) VALUES (?, ?)", (client_id, symbol)
            )
    return get_watchlist(client_id)


def remove_watchlist(client_id: str, symbol: str) -> list[str]:
    symbol = symbol.upper()
    if _use_supabase:
        _sb("DELETE", "watchlist", params={"client_id": f"eq.{client_id}", "symbol": f"eq.{symbol}"})
    else:
        with _lock, _conn() as conn:
            conn.execute("DELETE FROM watchlist WHERE client_id=? AND symbol=?", (client_id, symbol))
    return get_watchlist(client_id)


def record_signal(symbol: str, score: float, verdict: str, price: float | None) -> None:
    """One snapshot per symbol per day; safe to call repeatedly."""
    day = date.today().isoformat()
    symbol = symbol.upper()
    if _use_supabase:
        _sb("POST", "signal_history",
            json_body={"symbol": symbol, "day": day, "score": score, "verdict": verdict, "price": price})
        return
    try:
        with _lock, _conn() as conn:
            conn.execute(
                "INSERT OR REPLACE INTO signal_history (symbol, day, score, verdict, price) VALUES (?,?,?,?,?)",
                (symbol, day, score, verdict, price),
            )
    except Exception as exc:
        log.warning("signal history write failed: %s", exc)


def get_signal_history(symbol: str, limit: int = 90) -> list[dict]:
    symbol = symbol.upper()
    if _use_supabase:
        r = _sb("GET", "signal_history",
                params={"symbol": f"eq.{symbol}", "select": "day,score,verdict,price",
                        "order": "day.desc", "limit": str(limit)})
        return list(reversed(r.json())) if r is not None and r.status_code == 200 else []
    with _lock, _conn() as conn:
        rows = conn.execute(
            "SELECT day, score, verdict, price FROM signal_history WHERE symbol=? ORDER BY day DESC LIMIT ?",
            (symbol, limit),
        ).fetchall()
    return [{"day": d, "score": s, "verdict": v, "price": p} for d, s, v, p in reversed(rows)]
