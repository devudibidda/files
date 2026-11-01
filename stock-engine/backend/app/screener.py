"""Screener: run the analysis engine across the universe and filter."""
from concurrent.futures import ThreadPoolExecutor
from functools import partial

from .data.cache import cached
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


def scan_universe(type_: str | None = None) -> list[dict]:
    """Analyze the whole universe (cached); heavy on first run, cheap after."""
    key = f"screener:universe:{type_ or 'all'}"

    def run():
        symbols = [e["symbol"] for e in ALL_SYMBOLS if type_ in (None, e["type"])]
        # No news fetch: screener rows don't show sentiment, and the per-symbol
        # RSS fetch is what made a cold scan take minutes (and drop). The
        # single-stock page still calls analyze() with news on by default.
        with ThreadPoolExecutor(max_workers=8) as pool:
            reports = list(pool.map(partial(analyze, include_news=False), symbols))
        return [_row(r) for r in reports if r]

    return cached(key, 600, run)


def run_scan(scan: str, type_: str | None = None, limit: int = 50) -> list[dict]:
    rows = [r for r in scan_universe(type_) if _matches(r, scan)]
    rows.sort(key=lambda r: r["score"], reverse=scan not in ("sell", "overbought"))
    return rows[:limit]
