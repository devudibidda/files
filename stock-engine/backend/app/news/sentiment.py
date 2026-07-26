"""Headline sentiment: VADER tuned with a small finance lexicon."""
from vaderSentiment.vaderSentiment import SentimentIntensityAnalyzer

_FINANCE_LEXICON = {
    # bullish
    "surge": 2.5, "surges": 2.5, "rally": 2.2, "rallies": 2.2, "soar": 2.8,
    "soars": 2.8, "jump": 1.8, "jumps": 1.8, "gain": 1.5, "gains": 1.5,
    "upgrade": 2.2, "upgrades": 2.2, "upgraded": 2.2, "outperform": 2.0,
    "beat": 1.8, "beats": 1.8, "record high": 2.5, "breakout": 1.8,
    "bullish": 2.2, "buyback": 1.5, "dividend": 1.0, "bonus": 1.2,
    "profit": 1.5, "profits": 1.5, "multibagger": 2.5, "order win": 2.0,
    # bearish
    "slump": -2.5, "slumps": -2.5, "plunge": -2.8, "plunges": -2.8,
    "crash": -3.0, "crashes": -3.0, "fall": -1.5, "falls": -1.5,
    "drop": -1.5, "drops": -1.5, "downgrade": -2.2, "downgrades": -2.2,
    "downgraded": -2.2, "underperform": -2.0, "miss": -1.8, "misses": -1.8,
    "bearish": -2.2, "fraud": -3.2, "scam": -3.2, "probe": -1.8,
    "penalty": -1.8, "default": -2.5, "loss": -1.8, "losses": -1.8,
    "layoff": -2.0, "layoffs": -2.0, "sell-off": -2.5, "selloff": -2.5,
    "weak": -1.2, "pledge": -1.0, "resigns": -1.5, "debt": -1.0,
}

_analyzer = SentimentIntensityAnalyzer()
_analyzer.lexicon.update(_FINANCE_LEXICON)


def score_text(text: str) -> float:
    """Compound sentiment in [-1, 1]."""
    return _analyzer.polarity_scores(text)["compound"]


def label_for(compound: float) -> str:
    if compound >= 0.25:
        return "positive"
    if compound <= -0.25:
        return "negative"
    return "neutral"


def aggregate(scores: list[float]) -> dict:
    """Overall sentiment across headlines, recency handled by caller ordering."""
    if not scores:
        return {"score": 0.0, "label": "neutral", "count": 0}
    # newest headlines matter more: linear decay weights
    n = len(scores)
    weights = [1 - 0.5 * i / max(n - 1, 1) for i in range(n)]
    avg = sum(s * w for s, w in zip(scores, weights)) / sum(weights)
    return {"score": round(avg, 3), "label": label_for(avg), "count": n}
