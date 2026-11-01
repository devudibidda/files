"""Build the TrendWise symbol -> Upstox instrument_key mapping.

Source: Upstox's public complete instruments file (no auth needed):
    https://assets.upstox.com/market-quote/instruments/exchange/complete.json.gz
Matching rule: exact trading_symbol match within exchange NSE, segment
NSE_EQ only. Nothing is guessed: a TrendWise symbol with no exact match
is left unmapped and reported, and at runtime unmapped symbols fall back
to the Yahoo provider.

Usage:
    python3 scripts/build_upstox_mapping.py <instruments.json.gz> [out.json]
Defaults: /tmp/upstox_complete.json.gz -> app/data/upstox_instruments.json
"""
import gzip
import json
import sys
from pathlib import Path

BACKEND = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(BACKEND))

from app.data.symbols import EQUITIES, ETFS  # noqa: E402


def build(instruments_path: Path) -> tuple[dict, list, list]:
    with gzip.open(instruments_path, "rt") as f:
        items = json.load(f)
    by_symbol: dict[str, str] = {}
    dupes: dict[str, set] = {}
    for it in items:
        if it.get("exchange") != "NSE" or it.get("segment") != "NSE_EQ":
            continue
        sym = (it.get("trading_symbol") or "").upper()
        key = it.get("instrument_key")
        if not sym or not key:
            continue
        # One trading_symbol can appear twice in NSE_EQ (e.g. MOTHERSON
        # has both an EQ equity row and a D1 debenture row). The equity
        # row (instrument_type EQ) is the tradable stock; prefer it.
        if sym in by_symbol:
            if by_symbol[sym] != key:
                dupes.setdefault(sym, set()).update([by_symbol[sym], key])
            if it.get("instrument_type") == "EQ":
                by_symbol[sym] = key
        else:
            by_symbol[sym] = key
    mapping: dict[str, str] = {}
    unmapped: list[str] = []
    for group in (EQUITIES, ETFS):
        for sym, _name, _sector in group:
            key = by_symbol.get(sym.upper())
            if key:
                mapping[sym] = key
            else:
                unmapped.append(sym)
    return mapping, unmapped, sorted(dupes)


def main() -> None:
    src = Path(sys.argv[1]) if len(sys.argv) > 1 else Path("/tmp/upstox_complete.json.gz")
    out = (
        Path(sys.argv[2])
        if len(sys.argv) > 2
        else BACKEND / "app" / "data" / "upstox_instruments.json"
    )
    mapping, unmapped, dupes = build(src)
    out.write_text(json.dumps(mapping, indent=1, sort_keys=True) + "\n")
    n_eq = len(EQUITIES)
    n_etf = len(ETFS)
    mapped_eq = sum(1 for s, _n, _s in EQUITIES if s in mapping)
    mapped_etf = sum(1 for s, _n, _s in ETFS if s in mapping)
    print(f"equities: {mapped_eq}/{n_eq} mapped")
    print(f"etfs:     {mapped_etf}/{n_etf} mapped")
    print(f"total:    {len(mapping)}/{n_eq + n_etf}")
    print(f"unmapped: {unmapped}")
    print(f"duplicate NSE_EQ trading_symbols with differing keys: {dupes}")
    print(f"wrote {out}")


if __name__ == "__main__":
    main()
