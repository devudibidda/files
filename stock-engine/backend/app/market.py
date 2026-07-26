"""Market overview: indices, movers, breadth."""
from concurrent.futures import ThreadPoolExecutor

from .data.cache import cached
from .data.fetcher import get_quote
from .data.symbols import ALL_SYMBOLS, INDICES

# Liquid subset scanned for gainers/losers/breadth
_SCAN_UNIVERSE = [e["symbol"] for e in ALL_SYMBOLS if e["type"] == "equity"][:60]


def _fetch_quotes(symbols: list[str]) -> list[dict]:
    with ThreadPoolExecutor(max_workers=8) as pool:
        results = list(pool.map(get_quote, symbols))
    return [q for q in results if q]


def market_overview() -> dict:
    return cached("market:overview", 300, _market_overview)


def _market_overview() -> dict:
    indices = []
    for idx in INDICES:
        q = get_quote(idx["symbol"])
        if q:
            q["name"] = idx["name"]
            indices.append(q)

    quotes = _fetch_quotes(_SCAN_UNIVERSE)
    by_symbol = {e["symbol"]: e for e in ALL_SYMBOLS}
    for q in quotes:
        meta = by_symbol.get(q["symbol"], {})
        q["name"] = meta.get("name")
        q["sector"] = meta.get("sector")

    movers = [q for q in quotes if q.get("changePct") is not None]
    movers.sort(key=lambda q: q["changePct"], reverse=True)
    advancers = sum(1 for q in movers if q["changePct"] > 0)
    decliners = sum(1 for q in movers if q["changePct"] < 0)

    return {
        "indices": indices,
        "topGainers": movers[:6],
        "topLosers": movers[-6:][::-1],
        "breadth": {
            "advancers": advancers,
            "decliners": decliners,
            "unchanged": len(movers) - advancers - decliners,
        },
    }
