"""News aggregation from free RSS feeds (no API keys required).

Market-wide feeds: Economic Times Markets, Moneycontrol, LiveMint.
Per-stock news: Google News RSS query scoped to Indian finance topics.
"""
import calendar
import logging

import feedparser

from ..config import NEWS_TTL
from ..data.cache import cached
from ..data.symbols import lookup
from .sentiment import label_for, score_text

log = logging.getLogger(__name__)

MARKET_FEEDS = [
    ("Economic Times", "https://economictimes.indiatimes.com/markets/rssfeeds/1977021501.cms"),
    ("Moneycontrol", "https://www.moneycontrol.com/rss/marketreports.xml"),
    ("LiveMint", "https://www.livemint.com/rss/markets"),
]

GOOGLE_NEWS = (
    "https://news.google.com/rss/search?"
    "q={query}%20stock%20when:7d&hl=en-IN&gl=IN&ceid=IN:en"
)

# Shown when feeds are unreachable (sandboxes) so the UI stays demoable
_DEMO_HEADLINES = [
    ("Markets end higher as banking heavyweights extend gains", "Demo Wire"),
    ("FIIs turn net buyers; midcaps outperform benchmarks", "Demo Wire"),
    ("Q1 earnings season: IT majors guide for steady demand", "Demo Wire"),
    ("RBI holds rates; commentary keeps easing hopes alive", "Demo Wire"),
    ("Crude cools off, easing pressure on OMC margins", "Demo Wire"),
]


def _parse_feed(source: str, url: str, limit: int) -> list[dict]:
    try:
        feed = feedparser.parse(url)
    except Exception as exc:
        log.warning("rss fetch failed for %s: %s", source, exc)
        return []
    items = []
    for entry in feed.entries[:limit]:
        title = getattr(entry, "title", "").strip()
        if not title:
            continue
        published = None
        if getattr(entry, "published_parsed", None):
            published = calendar.timegm(entry.published_parsed)
        compound = score_text(title)
        items.append({
            "title": title,
            "link": getattr(entry, "link", None),
            "source": source,
            "publishedAt": published,
            "sentiment": round(compound, 3),
            "sentimentLabel": label_for(compound),
        })
    return items


def _demo_items() -> list[dict]:
    out = []
    for title, source in _DEMO_HEADLINES:
        compound = score_text(title)
        out.append({
            "title": title, "link": None, "source": source, "publishedAt": None,
            "sentiment": round(compound, 3), "sentimentLabel": label_for(compound),
        })
    return out


def market_news(limit: int = 25) -> list[dict]:
    def fetch():
        items: list[dict] = []
        for source, url in MARKET_FEEDS:
            items.extend(_parse_feed(source, url, limit))
        if not items:
            return _demo_items()
        items.sort(key=lambda x: x["publishedAt"] or 0, reverse=True)
        return items[:limit]

    return cached("news:market", NEWS_TTL, fetch)


def stock_news(symbol: str, limit: int = 12) -> list[dict]:
    entry = lookup(symbol)
    query = (entry["name"] if entry else symbol).replace(" ", "%20")

    def fetch():
        items = _parse_feed("Google News", GOOGLE_NEWS.format(query=query), limit)
        if not items:
            return _demo_items()[:limit]
        return items

    return cached(f"news:{symbol.upper()}", NEWS_TTL, fetch)
