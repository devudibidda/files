"""Walk-forward backtest of the indicator-only Buy signal.

Method, kept deliberately honest:
- Daily history (2y) with indicators computed ONCE. Every indicator used
  (SMA/EMA/RSI/MACD/Stochastic/Bollinger/ADX/Ichimoku/Supertrend/CMF/VWAP/
  volume) is trailing, so scoring day t from the slice [:t+1] never peeks
  at future prices.
- Signal on day t = Buy/Strong Buy verdict, with the same weekly-timeframe
  soften rule the live analysis applies (weekly trend from data up to t).
- News sentiment is EXCLUDED: historical headlines are unavailable, and
  using today's news would leak the future.
- Forward returns measured at 10 and 20 trading days; win = return > 0.
- Windows overlap (a signal can fire on consecutive days), so signals are
  not independent trades — the result is a hit-rate diagnostic, not a
  trading record. Past signals do not predict future returns.
"""
import logging

import pandas as pd

from ..data.cache import cached
from ..data.fetcher import get_history
from ..indicators.engine import compute_all
from .analysis import _weekly_trend
from .scoring import collect_votes, composite_score, verdict_for

log = logging.getLogger(__name__)

WARMUP = 200
HORIZONS = (10, 20)


def _walk(enriched: pd.DataFrame, df: pd.DataFrame) -> list[dict]:
    """Per-signal forward returns for every indicator-only Buy day."""
    signals = []
    closes = enriched["Close"]
    n = len(enriched)
    for t in range(WARMUP, n - max(HORIZONS)):
        window = enriched.iloc[: t + 1]
        score = composite_score(collect_votes(window))
        weekly = _weekly_trend(df.iloc[: t + 1])
        if weekly["state"] == "bearish" and score > 0:
            score = round(score * 0.7, 1)
        elif weekly["state"] == "bullish" and score < 0:
            score = round(score * 0.7, 1)
        if verdict_for(score) not in ("Buy", "Strong Buy"):
            continue
        entry = float(closes.iloc[t])
        signals.append(
            {h: float(closes.iloc[t + h] / entry - 1) for h in HORIZONS}
        )
    return signals


def _horizon_stats(signals: list[dict], h: int) -> dict:
    if not signals:
        return {"winRate": None, "avgReturn": None}
    rets = [s[h] for s in signals]
    wins = sum(1 for r in rets if r > 0)
    return {
        "winRate": round(wins / len(rets) * 100, 1),
        "avgReturn": round(sum(rets) / len(rets) * 100, 2),
    }


def backtest(symbol: str) -> dict | None:
    return cached(f"backtest:{symbol.upper()}", 3600, lambda: _backtest(symbol))


def _backtest(symbol: str) -> dict | None:
    df = get_history(symbol, "2y", "1d")
    if df is None or len(df) < WARMUP + max(HORIZONS) + 5:
        return None
    enriched = compute_all(df)
    signals = _walk(enriched, df)

    closes = enriched["Close"]
    n = len(enriched)
    baseline = [
        float(closes.iloc[t + 20] / closes.iloc[t] - 1)
        for t in range(WARMUP, n - 20)
    ]
    h10, h20 = _horizon_stats(signals, 10), _horizon_stats(signals, 20)

    return {
        "symbol": symbol.upper().removesuffix(".NS"),
        "signals": len(signals),
        "winRate10d": h10["winRate"],
        "avgReturn10d": h10["avgReturn"],
        "winRate20d": h20["winRate"],
        "avgReturn20d": h20["avgReturn"],
        "baseline20d": round(sum(baseline) / len(baseline) * 100, 2) if baseline else None,
        "periodDays": len(df),
        "asOf": df.index[-1].date().isoformat() if hasattr(df.index[-1], "date") else str(df.index[-1]),
        "dataSource": df.attrs.get("source", "live"),
        "method": "Indicator-only Buy/Strong Buy signals (weekly filter applied, "
                  "news sentiment excluded); forward returns at 10/20 trading days; "
                  "overlapping windows — a hit-rate diagnostic, not a trading record.",
    }
