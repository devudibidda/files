from fastapi import APIRouter, HTTPException, Query

from ..market import market_overview
from ..screener import SCANS, build_calls, refresh_scan, run_scan, scan_computed_at, scan_universe

router = APIRouter(prefix="/api", tags=["market"])


@router.get("/market/overview")
def overview():
    return market_overview()


@router.get("/screener/scans")
def list_scans():
    return {"scans": [{"id": k, "label": v} for k, v in SCANS.items()]}


@router.get("/screener")
def screener(
    scan: str = Query("buy"),
    type: str | None = Query(None, pattern="^(equity|etf)$"),
    limit: int = 50,
):
    if scan not in SCANS:
        raise HTTPException(400, f"Unknown scan '{scan}'. Valid: {', '.join(SCANS)}")
    return {"scan": scan, "label": SCANS[scan], "results": run_scan(scan, type, limit),
            "computedAt": scan_computed_at(type)}


@router.post("/screener/refresh")
def screener_refresh():
    rows, computed_at, was_running = refresh_scan(None)
    if was_running:
        return {"status": "running", "computedAt": computed_at}
    return {"status": "refreshed", "computedAt": computed_at, "rows": len(rows)}


@router.get("/calls")
def calls():
    """Curated Buy/Sell calls from the latest scan: quality first."""
    rows = scan_universe(None)
    result = build_calls(rows)
    result["computedAt"] = scan_computed_at(None)
    return result
