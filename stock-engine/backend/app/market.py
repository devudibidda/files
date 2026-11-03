"""Market overview: indices, movers, breadth."""
from concurrent.futures import ThreadPoolExecutor

from .data import scan_store
from .data.cache import cache, cached
from .data.fetcher import get_quote
from .data.symbols import ALL_SYMBOLS, INDICES

# Liquid subset scanned for gainers/losers/breadth
_SCAN_UNIVERSE = [e["symbol"] for e in ALL_SYMBOLS if e["type"] == "equity"][:60]


def _fetch_quotes(symbols: list[str], fast_symbols: frozenset[str] = frozenset()) -> list[dict]:
    """Fetch quotes for many symbols through one shared worker pool.

    Symbols in fast_symbols get the hard-bounded Yahoo fallback
    (single quick attempt): overview indices use it so a dead feed
    costs seconds instead of stalling the whole page. All other
    symbols keep the full fallback chain.
    """
    def _one(sym: str):
        return get_quote(sym, fast=True) if sym in fast_symbols else get_quote(sym)

    with ThreadPoolExecutor(max_workers=8) as pool:
        return [q for q in pool.map(_one, symbols) if q]


def market_overview() -> dict:
    """Indices, movers, breadth: memory cache, then stored doc, then compute.

    The stored doc is what keeps the dashboard instant after a restart:
    the old memory-only cache left the first post-restart visitor paying
    for the full 65-quote fetch behind a blank page skeleton.
    """
    hit = cache.get("market:overview")
    if hit is not None:
        return hit
    doc, _ = scan_store.load_doc("market:overview")
    if doc is not None:
        cache.set("market:overview", doc, 300)
        return doc

    def run():
        result = _market_overview()
        result["computedAt"] = scan_store.save_doc("market:overview", result)
        return result

    return cached("market:overview", 300, run)


def refresh_overview() -> dict:
    """Force a fresh overview, bypassing caches, and persist it."""
    result = _market_overview()
    result["computedAt"] = scan_store.save_doc("market:overview", result)
    cache.set("market:overview", result, 300)
    return result


def _market_overview() -> dict:
    # Indices and equities go through ONE pool together. They used to
    # be sequential (indices first, then the equity pool), so a stalled
    # Yahoo index blocked the entire page before the scan even started.
    index_symbols = [idx["symbol"] for idx in INDICES]
    results = _fetch_quotes(index_symbols + _SCAN_UNIVERSE, fast_symbols=set(index_symbols))
    by_quote = {q["symbol"]: q for q in results}

    indices = []
    for idx in INDICES:
        q = by_quote.get(idx["symbol"])
        if q:
            q["name"] = idx["name"]
            indices.append(q)

    quotes = [by_quote[s] for s in _SCAN_UNIVERSE if s in by_quote]
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
