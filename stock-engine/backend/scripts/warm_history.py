#!/usr/bin/env python3
"""Refresh the persistent daily-candle store for every mapped symbol.

Usage (from the backend directory, with the service environment):
    python3 scripts/warm_history.py

Idempotent: symbols already synced today are skipped, weekends are
no-ops (no new completed bar can appear), and failures are reported
without stopping the run. Run once after deploying the store to
pre-populate it, and daily after market close (see the systemd timer
on the server) so no user request ever triggers a bulk download.
"""

import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from app.data import history_store, upstox_chart  # noqa: E402


def main() -> int:
    backend = Path(__file__).resolve().parents[1]
    mapping = json.loads((backend / "app" / "data" / "upstox_instruments.json").read_text())
    symbols = sorted(mapping)
    if not upstox_chart.available():
        print("UPSTOX_ANALYTICS_TOKEN is not set; nothing to sync.")
        return 1
    synced = skipped = failed = 0
    for symbol in symbols:
        try:
            if not history_store.needs_sync(symbol):
                skipped += 1
                continue
            fresh = upstox_chart.fetch_candles(symbol, "2y", "1d")
            if fresh is None or fresh.empty:
                failed += 1
                continue
            history_store.upsert(symbol, fresh)
            history_store.mark_synced(symbol)
            synced += 1
        except Exception as exc:  # noqa: BLE001 - report and continue
            print(f"WARN {symbol}: {exc}")
            failed += 1
    print(f"synced={synced} skipped={skipped} failed={failed} of {len(symbols)}")
    return 0 if failed == 0 else 1


if __name__ == "__main__":
    sys.exit(main())
