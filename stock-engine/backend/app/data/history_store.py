"""Persistent daily-candle store (SQLite) for the 1d history path.

Completed daily bars never change, so they are stored on disk and
reused across sessions and restarts instead of being re-downloaded
every hour. Only today's bar is ever live: it is appended in memory
from the market-quote overlay and never stored as a completed bar.

Sync rule (IST calendar days):
- An empty store syncs on first request, any day of the week.
- Otherwise sync at most once per calendar day, and never on Sat/Sun,
  since no new completed bar can appear on a weekend.
- A sync fetches the 2y daily frame from Upstox and upserts only bars
  with date < today, so a partial provider response can never delete
  stored history. The sync date is recorded even when no new bar
  appears (holidays), so a holiday costs one sync, not one per request.

Only Upstox-sourced frames are stored. Unmapped symbols keep the
existing provider path untouched. On an ephemeral disk (Render free
tier) a cold store simply falls back to the provider path; on a
persistent disk (the Oracle VM) the store survives restarts.
"""

import logging
import sqlite3
from datetime import date, datetime, time
from zoneinfo import ZoneInfo

import pandas as pd

from ..config import SQLITE_PATH

log = logging.getLogger(__name__)

IST = ZoneInfo("Asia/Kolkata")
MARKET_OPEN = time(9, 15)


def _conn() -> sqlite3.Connection:
    conn = sqlite3.connect(SQLITE_PATH)
    conn.execute(
        """CREATE TABLE IF NOT EXISTS candles (
            symbol TEXT NOT NULL,
            day TEXT NOT NULL,
            open REAL,
            high REAL,
            low REAL,
            close REAL,
            volume REAL,
            PRIMARY KEY (symbol, day)
        )"""
    )
    conn.execute(
        """CREATE TABLE IF NOT EXISTS meta (
            key TEXT PRIMARY KEY,
            value TEXT NOT NULL
        )"""
    )
    return conn


def today_ist() -> date:
    return datetime.now(IST).date()


def appendable_today(now: datetime | None = None) -> bool:
    """True when a live quote can stand in for today's bar.

    Only on weekdays at or after the 9:15 IST open. Before the open
    (or on weekends) the quote still reflects the previous close, so
    appending it as today would fabricate a bar.
    """
    now = now or datetime.now(IST)
    if now.tzinfo is None:
        now = now.replace(tzinfo=IST)
    else:
        now = now.astimezone(IST)
    return now.weekday() < 5 and now.time() >= MARKET_OPEN


def _sync_key(symbol: str) -> str:
    return f"sync:{symbol.upper()}"


def last_sync(symbol: str) -> str | None:
    conn = _conn()
    try:
        row = conn.execute(
            "SELECT value FROM meta WHERE key = ?", (_sync_key(symbol),)
        ).fetchone()
        return row[0] if row else None
    finally:
        conn.close()


def mark_synced(symbol: str, day: date | None = None) -> None:
    day = day or today_ist()
    conn = _conn()
    try:
        conn.execute(
            "INSERT OR REPLACE INTO meta (key, value) VALUES (?, ?)",
            (_sync_key(symbol), day.isoformat()),
        )
        conn.commit()
    finally:
        conn.close()


def has_bars(symbol: str) -> bool:
    conn = _conn()
    try:
        row = conn.execute(
            "SELECT 1 FROM candles WHERE symbol = ? LIMIT 1",
            (symbol.upper(),),
        ).fetchone()
        return row is not None
    finally:
        conn.close()


def needs_sync(symbol: str) -> bool:
    """True when the stored completed bars may be missing a day."""
    if not has_bars(symbol):
        return True
    today = today_ist()
    synced = last_sync(symbol)
    if synced is not None and synced >= today.isoformat():
        return False
    if today.weekday() >= 5:
        return False
    return True


def upsert(symbol: str, df: pd.DataFrame) -> int:
    """Store completed bars (date < today) from a provider frame.

    Upsert only: bars already stored are replaced, never deleted, so a
    truncated provider response cannot destroy history. Returns the
    number of bars written.
    """
    symbol = symbol.upper()
    today = today_ist().isoformat()
    rows = []
    for ts, row in df.iterrows():
        stamp = pd.Timestamp(ts)
        if stamp.tzinfo is None:
            stamp = stamp.tz_localize(IST)
        else:
            stamp = stamp.tz_convert(IST)
        day = stamp.date().isoformat()
        if day >= today:
            continue
        close = row["Close"]
        if pd.isna(close):
            continue
        rows.append((
            symbol,
            day,
            None if pd.isna(row["Open"]) else float(row["Open"]),
            None if pd.isna(row["High"]) else float(row["High"]),
            None if pd.isna(row["Low"]) else float(row["Low"]),
            float(close),
            None if pd.isna(row["Volume"]) else float(row["Volume"]),
        ))
    if not rows:
        return 0
    conn = _conn()
    try:
        conn.executemany(
            "INSERT OR REPLACE INTO candles"
            " (symbol, day, open, high, low, close, volume)"
            " VALUES (?, ?, ?, ?, ?, ?, ?)",
            rows,
        )
        conn.commit()
    finally:
        conn.close()
    return len(rows)


def load(symbol: str, days: int) -> pd.DataFrame | None:
    """Stored bars for the last `days` calendar days, or None if empty.

    The frame index is midnight IST (daily bars, never intraday), with
    the same OHLCV columns the fetcher serves, and source "upstox".
    """
    today = today_ist()
    start = (today.fromordinal(today.toordinal() - days)).isoformat()
    conn = _conn()
    try:
        rows = conn.execute(
            "SELECT day, open, high, low, close, volume FROM candles"
            " WHERE symbol = ? AND day >= ? ORDER BY day",
            (symbol.upper(), start),
        ).fetchall()
    finally:
        conn.close()
    if not rows:
        return None
    index = pd.DatetimeIndex(
        [pd.Timestamp(day).tz_localize(IST) for day, *_ in rows]
    )
    df = pd.DataFrame(
        {
            "Open": [r[1] for r in rows],
            "High": [r[2] for r in rows],
            "Low": [r[3] for r in rows],
            "Close": [r[4] for r in rows],
            "Volume": [r[5] for r in rows],
        },
        index=index,
    )
    df.attrs["source"] = "upstox"
    return df
