"""Full analysis report orchestrator."""
import pandas as pd

from ..config import ANALYSIS_TTL, DISCLAIMER
from ..data.cache import cached
from ..data.fetcher import get_history
from ..data.symbols import lookup
from ..indicators.engine import compute_all, ema, rsi, snapshot
from .levels import pivot_points, support_resistance
from .scoring import collect_votes, composite_score, confidence_for, verdict_for
from .trade_plan import build_trade_plan


def _weekly_trend(df: pd.DataFrame) -> dict:
    """Higher-timeframe check on weekly candles."""
    weekly = df.resample("W").agg(
        {"Open": "first", "High": "max", "Low": "min", "Close": "last", "Volume": "sum"}
    ).dropna()
    if len(weekly) < 12:
        return {"state": "unknown", "reason": "Not enough weekly history."}
    close = weekly["Close"]
    e10, e40 = ema(close, 10), ema(close, 40)
    r = rsi(close, 14)
    last_close, last_e10 = float(close.iloc[-1]), float(e10.iloc[-1])
    last_e40 = float(e40.iloc[-1]) if pd.notna(e40.iloc[-1]) else None
    last_rsi = float(r.iloc[-1]) if pd.notna(r.iloc[-1]) else 50.0

    bullish = last_close > last_e10 and (last_e40 is None or last_e10 > last_e40)
    bearish = last_close < last_e10 and (last_e40 is None or last_e10 < last_e40)
    if bullish and last_rsi > 50:
        return {"state": "bullish",
                "reason": f"Weekly close is above the 10-week EMA with weekly RSI at {last_rsi:.0f} — "
                          "the higher timeframe supports long trades."}
    if bearish and last_rsi < 50:
        return {"state": "bearish",
                "reason": f"Weekly close is below the 10-week EMA with weekly RSI at {last_rsi:.0f} — "
                          "the higher timeframe is against long trades."}
    return {"state": "neutral",
            "reason": f"Weekly trend is transitioning (weekly RSI {last_rsi:.0f}) — no clear higher-timeframe edge."}


def _trend_summary(votes: list[dict], score: float, verdict: str, weekly: dict) -> str:
    bull = [v["indicator"] for v in votes if v["vote"] > 0]
    bear = [v["indicator"] for v in votes if v["vote"] < 0]
    parts = [
        f"{len(bull)} of {len(votes)} indicators lean bullish"
        if len(bull) >= len(bear)
        else f"{len(bear)} of {len(votes)} indicators lean bearish",
        f"composite score {score:+.0f}",
        f"weekly timeframe {weekly['state']}",
    ]
    return f"{verdict}: " + ", ".join(parts) + "."


def analyze(symbol: str) -> dict | None:
    return cached(f"analysis:{symbol.upper()}", ANALYSIS_TTL, lambda: _analyze(symbol))


def _analyze(symbol: str) -> dict | None:
    df = get_history(symbol, "2y", "1d")
    if df is None or len(df) < 60:
        return None

    enriched = compute_all(df)
    snap = snapshot(enriched)
    votes = collect_votes(enriched)
    score = composite_score(votes)
    verdict = verdict_for(score)
    weekly = _weekly_trend(df)

    # Higher-timeframe filter: soften a daily Buy when the weekly is against it
    adjusted_score = score
    if weekly["state"] == "bearish" and score > 0:
        adjusted_score = round(score * 0.7, 1)
        verdict = verdict_for(adjusted_score)
    elif weekly["state"] == "bullish" and score < 0:
        adjusted_score = round(score * 0.7, 1)
        verdict = verdict_for(adjusted_score)

    # News sentiment nudges the score by up to ±10 (reported separately too)
    news_sentiment = {"score": 0.0, "label": "neutral", "count": 0}
    try:
        from ..news.rss import stock_news
        from ..news.sentiment import aggregate
        headlines = stock_news(symbol) or []
        news_sentiment = aggregate([h["sentiment"] for h in headlines])
        news_adj = round(max(-10.0, min(10.0, news_sentiment["score"] * 20)), 1)
    except Exception:
        news_adj = 0.0
    adjusted_score = round(max(-100.0, min(100.0, adjusted_score + news_adj)), 1)
    verdict = verdict_for(adjusted_score)

    lvl = support_resistance(df)
    pivots = pivot_points(df)
    plan = build_trade_plan(enriched, verdict, lvl)
    confidence = confidence_for(votes, adjusted_score)

    meta = lookup(symbol) or {}
    price = float(df["Close"].iloc[-1])
    high52 = float(df["High"].tail(252).max())
    low52 = float(df["Low"].tail(252).min())

    return {
        "symbol": symbol.upper().removesuffix(".NS"),
        "name": meta.get("name"),
        "sector": meta.get("sector"),
        "type": meta.get("type", "equity"),
        "price": round(price, 2),
        "score": adjusted_score,
        "rawScore": score,
        "verdict": verdict,
        "confidence": confidence,
        "summary": _trend_summary(votes, adjusted_score, verdict, weekly),
        "weeklyTrend": weekly,
        "newsSentiment": {**news_sentiment, "scoreAdjustment": news_adj},
        "votes": votes,
        "indicators": snap,
        "levels": lvl,
        "pivots": pivots,
        "tradePlan": plan,
        "stats": {
            "high52w": round(high52, 2),
            "low52w": round(low52, 2),
            "distFromHigh52wPct": round((price - high52) / high52 * 100, 1),
            "distFromLow52wPct": round((price - low52) / low52 * 100, 1),
            "atrPct": round(float(enriched["ATR14"].iloc[-1]) / price * 100, 2)
            if pd.notna(enriched["ATR14"].iloc[-1]) else None,
        },
        "dataSource": df.attrs.get("source", "live"),
        "asOf": df.index[-1].date().isoformat() if hasattr(df.index[-1], "date") else str(df.index[-1]),
        "disclaimer": DISCLAIMER,
    }
