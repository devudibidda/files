from fastapi import APIRouter, HTTPException, Query

from ..market import market_overview
from ..screener import SCANS, run_scan

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
    return {"scan": scan, "label": SCANS[scan], "results": run_scan(scan, type, limit)}
