"""Screener: run the analysis engine across the universe and filter."""
import threading
from concurrent.futures import ThreadPoolExecutor
from functools import partial

from .data import scan_store
from .data.cache import cache, cached
from .data.symbols import ALL_SYMBOLS
from .signals.analysis import analyze

SCANS = {
    "all": "All symbols ranked by score",
    "strong_buy": "Strong Buy signals",
    "buy": "All Buy signals",
    "sell": "Sell / Strong Sell signals",
    "oversold": "RSI below 30 (oversold)",
    "overbought": "RSI above 70 (overbought)",
    "golden_cross": "50-SMA above 200-SMA regime",
    "near_52w_high": "Within 5% of 52-week high",
    "high_volume": "Volume 1.5× above 20-day average",
    "trending": "Strong trend (ADX ≥ 25)",
}


def _row(report: dict) -> dict:
    ind = report["indicators"]
    return {
        "symbol": report["symbol"],
        "name": report["name"],
        "sector": report["sector"],
        "type": report["type"],
        "price": report["price"],
        "score": report["score"],
        "verdict": report["verdict"],
        "confidence": report["confidence"],
        "summary": report.get("summary"),
        "tradePlan": report.get("tradePlan"),
        "source": report.get("dataSource", "live"),
        "rsi": ind.get("RSI14"),
        "adx": ind.get("ADX14"),
        "supertrend": "bullish" if ind.get("ST_DIR") == 1 else "bearish",
        "distFromHigh52wPct": report["stats"]["distFromHigh52wPct"],
        "volRatio": round(ind["volume"] / ind["VOL_SMA20"], 2)
        if ind.get("volume") and ind.get("VOL_SMA20") else None,
        "goldenCross": (ind.get("SMA50") or 0) > (ind.get("SMA200") or 0)
        if ind.get("SMA50") and ind.get("SMA200") else None,
    }


def _matches(row: dict, scan: str) -> bool:
    if scan == "strong_buy":
        return row["verdict"] == "Strong Buy"
    if scan == "buy":
        return row["verdict"] in ("Buy", "Strong Buy")
    if scan == "sell":
        return row["verdict"] in ("Sell", "Strong Sell")
    if scan == "oversold":
        return row["rsi"] is not None and row["rsi"] < 30
    if scan == "overbought":
        return row["rsi"] is not None and row["rsi"] > 70
    if scan == "golden_cross":
        return row["goldenCross"] is True
    if scan == "near_52w_high":
        return row["distFromHigh52wPct"] is not None and row["distFromHigh52wPct"] >= -5
    if scan == "high_volume":
        return row["volRatio"] is not None and row["volRatio"] >= 1.5
    if scan == "trending":
        return row["adx"] is not None and row["adx"] >= 25
    return True


def _scan_key(type_: str | None) -> str:
    return f"screener:universe:{type_ or 'all'}"


def _compute_scan(type_: str | None) -> list[dict]:
    """Run the analysis engine across the universe (no cache)."""
    symbols = [e["symbol"] for e in ALL_SYMBOLS if type_ in (None, e["type"])]
    # No news fetch: screener rows don't show sentiment, and the per-symbol
    # RSS fetch is what made a cold scan take minutes (and drop). The
    # single-stock page still calls analyze() with news on by default.
    with ThreadPoolExecutor(max_workers=8) as pool:
        reports = list(pool.map(partial(analyze, include_news=False), symbols))
    return [_row(r) for r in reports if r]


def scan_universe(type_: str | None = None) -> list[dict]:
    """Analyze the whole universe: memory cache, then stored rows, then compute.

    A compute also persists its rows, so the next request (and the next
    restart) serves from the store instead of paying for a full scan.
    """
    key = _scan_key(type_)
    hit = cache.get(key)
    if hit is not None:
        return hit
    stored, _ = scan_store.load_scan(key)
    if stored is not None:
        cache.set(key, stored, 600)
        return stored

    def run():
        rows = _compute_scan(type_)
        scan_store.save_scan(key, rows)
        return rows

    return cached(key, 600, run)


def scan_computed_at(type_: str | None = None) -> str | None:
    """When the stored rows for a scan were computed, or None."""
    _, computed_at = scan_store.load_scan(_scan_key(type_))
    return computed_at


_refreshing: set[str] = set()
_refresh_lock = threading.Lock()


def refresh_scan(type_: str | None = None) -> tuple[list[dict] | None, str | None, bool]:
    """Force a fresh scan, bypassing caches, and persist it.

    Returns (rows, computed_at, was_running). When another refresh for
    the same key is already running, returns (None, old computed_at,
    True) instead of stacking a second full scan.
    """
    key = _scan_key(type_)
    with _refresh_lock:
        if key in _refreshing:
            return None, scan_computed_at(type_), True
        _refreshing.add(key)
    try:
        rows = _compute_scan(type_)
        computed_at = scan_store.save_scan(key, rows)
        cache.set(key, rows, 600)
        return rows, computed_at, False
    finally:
        with _refresh_lock:
            _refreshing.discard(key)


# Quality bar for published calls: only setups the engine itself rates
# as reasonably confident. (Risk-reward is 1.5 by construction in the
# trade plan, so it is not a useful filter here.)
BUY_MIN_CONFIDENCE = 60
SELL_MIN_CONFIDENCE = 60
CALLS_LIMIT = 10


def _call_row(row: dict) -> dict:
    plan = row.get("tradePlan") or {}
    return {
        "symbol": row["symbol"],
        "name": row["name"],
        "sector": row["sector"],
        "price": row["price"],
        "score": row["score"],
        "verdict": row["verdict"],
        "confidence": row["confidence"],
        "summary": row.get("summary"),
        "action": plan.get("action"),
        "entryZone": plan.get("entryZone"),
        "stopLoss": plan.get("stopLoss"),
        "target1": plan.get("target1"),
        "target2": plan.get("target2"),
        "riskReward": plan.get("riskReward"),
    }


def build_calls(rows: list[dict]) -> dict:
    """Curated Buy/Sell calls from scan rows: few, high-quality only."""
    buys = []
    sells = []
    for row in rows:
        plan = row.get("tradePlan") or {}
        if row["verdict"] in ("Buy", "Strong Buy") and plan.get("action") in ("BUY", "BUY_ON_DIP"):
            if row["confidence"] >= BUY_MIN_CONFIDENCE:
                buys.append(_call_row(row))
        elif row["verdict"] in ("Sell", "Strong Sell") and plan.get("action") == "AVOID_OR_EXIT":
            if row["confidence"] >= SELL_MIN_CONFIDENCE:
                sells.append(_call_row(row))
    buys.sort(key=lambda r: r["score"], reverse=True)
    sells.sort(key=lambda r: r["score"])
    return {"buyCalls": buys[:CALLS_LIMIT], "sellCalls": sells[:CALLS_LIMIT]}


def run_scan(scan: str, type_: str | None = None, limit: int = 50) -> list[dict]:
    rows = [r for r in scan_universe(type_) if _matches(r, scan)]
    rows.sort(key=lambda r: r["score"], reverse=scan not in ("sell", "overbought"))
    return rows[:limit]
