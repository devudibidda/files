from fastapi import APIRouter, HTTPException, Query

from ..data.fetcher import get_history, get_quote, history_to_candles, is_intraday, time_key
from ..data.symbols import ALL_SYMBOLS, lookup, search
from ..indicators.engine import compute_all
from ..news.rss import market_news, stock_news
from ..screener import refresh_scan, scan_computed_at, scan_universe
from ..signals.analysis import analyze
from ..signals.backtest import backtest

router = APIRouter(prefix="/api", tags=["stocks"])


@router.get("/symbols/search")
def symbols_search(q: str = Query(..., min_length=1), limit: int = 15):
    return {"results": search(q, limit)}


@router.get("/etfs")
def list_etfs():
    return {"results": [e for e in ALL_SYMBOLS if e["type"] == "etf"]}


@router.get("/etfs/leaders")
def etf_leaders():
    """Top 3 ETFs per category, ranked by composite signal score."""
    rows = scan_universe("etf")
    cats: dict[str, list] = {}
    for r in rows:
        cats.setdefault(r["sector"] or "Other", []).append(r)
    categories = []
    for cat, items in sorted(cats.items()):
        items.sort(key=lambda r: r["score"], reverse=True)
        categories.append({"category": cat, "leaders": items[:3]})
    return {
        "categories": categories,
        "computedAt": scan_computed_at("etf"),
        "method": "ETFs ranked by TrendWise composite signal score within each "
                  "category. Scores are technical signals, not investment advice.",
    }


@router.post("/etfs/leaders/refresh")
def etf_leaders_refresh():
    rows, computed_at, was_running = refresh_scan("etf")
    if was_running:
        return {"status": "running", "computedAt": computed_at}
    return {"status": "refreshed", "computedAt": computed_at, "rows": len(rows)}


@router.get("/stocks/{symbol}/quote")
def stock_quote(symbol: str):
    q = get_quote(symbol)
    if not q:
        raise HTTPException(404, f"No data for symbol '{symbol}'")
    meta = lookup(symbol)
    if meta:
        q.update({"name": meta["name"], "sector": meta["sector"], "type": meta["type"]})
    return q


@router.get("/stocks/{symbol}/history")
def stock_history(
    symbol: str,
    range: str = "1y",
    interval: str | None = None,
    overlays: bool = True,
):
    df = get_history(symbol, range, interval)
    if df is None:
        raise HTTPException(404, f"No history for symbol '{symbol}'")
    payload = {
        "symbol": symbol.upper().removesuffix(".NS"),
        "range": range,
        "source": df.attrs.get("source", "live"),
        "candles": history_to_candles(df),
    }
    if overlays and len(df) >= 20:
        enriched = compute_all(df)
        intraday = is_intraday(df)
        def series(col):
            vals = enriched[col]
            return [
                {"time": time_key(ts, intraday), "value": round(float(v), 2)}
                for ts, v in vals.items() if v == v  # skip NaN
            ]
        payload["overlays"] = {
            "ema20": series("EMA20"),
            "ema50": series("EMA50"),
            "ema200": series("EMA200"),
            "bbUpper": series("BB_UPPER"),
            "bbLower": series("BB_LOWER"),
            "supertrend": series("ST_LINE"),
            "rsi": series("RSI14"),
            "macd": series("MACD"),
            "macdSignal": series("MACD_SIGNAL"),
            "macdHist": series("MACD_HIST"),
        }
    return payload


@router.get("/stocks/{symbol}/analysis")
def stock_analysis(
    symbol: str,
    account_size: float = Query(100000, gt=0),
    risk_pct: float = Query(1.0, gt=0, le=100),
):
    report = analyze(symbol, account_size, risk_pct)
    if not report:
        raise HTTPException(404, f"Not enough data to analyze '{symbol}'")
    return report


@router.get("/stocks/{symbol}/backtest")
def stock_backtest(symbol: str):
    report = backtest(symbol)
    if not report:
        raise HTTPException(404, f"Not enough data to backtest '{symbol}'")
    return report


@router.get("/stocks/{symbol}/news")
def stock_news_route(symbol: str):
    return {"symbol": symbol.upper(), "items": stock_news(symbol)}


@router.get("/news/market")
def market_news_route():
    return {"items": market_news()}
