from fastapi import APIRouter, HTTPException, Query

from .. import mf
from ..mf import CATEGORIES

router = APIRouter(prefix="/api/mutual-funds", tags=["mutual-funds"])


@router.get("/search")
def mf_search(q: str = Query(..., min_length=1), limit: int = 15):
    if mf.scheme_list() is None:
        raise HTTPException(503, "Mutual fund data source is temporarily unavailable")
    return {"results": mf.search_schemes(q, limit)}


@router.get("/leaders")
def mf_leaders(category: str = Query(...), limit: int = Query(5, ge=1, le=10)):
    if category not in CATEGORIES:
        raise HTTPException(400, f"Unknown category '{category}'. Valid: {', '.join(CATEGORIES)}")
    result = mf.category_leaders(category, limit)
    if not result:
        raise HTTPException(503, "Mutual fund data source is temporarily unavailable")
    return result


@router.get("/{code}")
def mf_detail(code: int):
    report = mf.fund_report(code)
    if not report:
        raise HTTPException(404, f"No mutual fund data for scheme code '{code}'")
    return report
