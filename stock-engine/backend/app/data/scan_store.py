"""Persistent store for computed scan results (screener, ETF leaders).

A full scan takes ~90 seconds cold, so results are stored in SQLite
and served instantly until the next warm or an explicit refresh. The
store is what makes the Screener, ETF and Calls pages fast after a
restart: the in-memory cache alone cannot survive one.

Tables live in the same SQLite file as the candle store and the
watchlists (see config.SQLITE_PATH). On an ephemeral disk the store
is simply empty and callers fall back to computing, as before.
"""

import json
import logging
import sqlite3
from datetime import datetime

from ..config import SQLITE_PATH
from .history_store import IST

log = logging.getLogger(__name__)


def _conn() -> sqlite3.Connection:
    conn = sqlite3.connect(SQLITE_PATH)
    conn.execute(
        """CREATE TABLE IF NOT EXISTS scan_rows (
            scan_key TEXT NOT NULL,
            symbol TEXT NOT NULL,
            row_json TEXT NOT NULL,
            PRIMARY KEY (scan_key, symbol)
        )"""
    )
    conn.execute(
        """CREATE TABLE IF NOT EXISTS scan_meta (
            scan_key TEXT PRIMARY KEY,
            computed_at TEXT NOT NULL
        )"""
    )
    conn.execute(
        """CREATE TABLE IF NOT EXISTS docs (
            doc_key TEXT PRIMARY KEY,
            doc_json TEXT NOT NULL,
            computed_at TEXT NOT NULL
        )"""
    )
    return conn


def _now_iso() -> str:
    return datetime.now(IST).isoformat(timespec="seconds")


def save_scan(scan_key: str, rows: list[dict]) -> str:
    """Replace the stored rows for a scan key. Returns computed_at."""
    computed_at = _now_iso()
    conn = _conn()
    try:
        conn.execute("DELETE FROM scan_rows WHERE scan_key = ?", (scan_key,))
        conn.executemany(
            "INSERT INTO scan_rows (scan_key, symbol, row_json) VALUES (?, ?, ?)",
            [(scan_key, r["symbol"], json.dumps(r)) for r in rows],
        )
        conn.execute(
            "INSERT OR REPLACE INTO scan_meta (scan_key, computed_at) VALUES (?, ?)",
            (scan_key, computed_at),
        )
        conn.commit()
    finally:
        conn.close()
    return computed_at


def load_scan(scan_key: str) -> tuple[list[dict] | None, str | None]:
    """Stored rows and their computed_at, or (None, None) when empty."""
    conn = _conn()
    try:
        meta = conn.execute(
            "SELECT computed_at FROM scan_meta WHERE scan_key = ?", (scan_key,)
        ).fetchone()
        if meta is None:
            return None, None
        rows = conn.execute(
            "SELECT row_json FROM scan_rows WHERE scan_key = ? ORDER BY symbol",
            (scan_key,),
        ).fetchall()
    finally:
        conn.close()
    if not rows:
        return None, None
    return [json.loads(r[0]) for r in rows], meta[0]


def save_doc(doc_key: str, doc: dict) -> str:
    """Store one computed document (for example the market overview)."""
    computed_at = _now_iso()
    conn = _conn()
    try:
        conn.execute(
            "INSERT OR REPLACE INTO docs (doc_key, doc_json, computed_at) VALUES (?, ?, ?)",
            (doc_key, json.dumps(doc), computed_at),
        )
        conn.commit()
    finally:
        conn.close()
    return computed_at


def load_doc(doc_key: str) -> tuple[dict | None, str | None]:
    """Stored document and its computed_at, or (None, None) when empty."""
    conn = _conn()
    try:
        row = conn.execute(
            "SELECT doc_json, computed_at FROM docs WHERE doc_key = ?", (doc_key,)
        ).fetchone()
    finally:
        conn.close()
    if row is None:
        return None, None
    return json.loads(row[0]), row[1]
