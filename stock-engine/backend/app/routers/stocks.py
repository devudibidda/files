from fastapi import APIRouter, HTTPException, Query

from ..data.fetcher import get_history, get_quote, history_to_candles
from ..data.symbols import ALL_SYMBOLS, lookup, search
from ..indicators.engine import compute_all
from ..news.rss import market_news, stock_news
from ..signals.analysis import analyze

router = APIRouter(prefix="/api", tags=["stocks"])


@router.get("/symbols/search")
def symbols_search(q: str = Query(..., min_length=1), limit: int = 15):
    return {"results": search(q, limit)}


@router.get("/etfs")
def list_etfs():
    return {"results": [e for e in ALL_SYMBOLS if e["type"] == "etf"]}


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
        def series(col):
            vals = enriched[col]
            return [
                {"time": ts.date().isoformat(), "value": round(float(v), 2)}
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
def stock_analysis(symbol: str):
    report = analyze(symbol)
    if not report:
        raise HTTPException(404, f"Not enough data to analyze '{symbol}'")
    return report


@router.get("/stocks/{symbol}/news")
def stock_news_route(symbol: str):
    return {"symbol": symbol.upper(), "items": stock_news(symbol)}


@router.get("/news/market")
def market_news_route():
    return {"items": market_news()}
