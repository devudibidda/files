from fastapi import APIRouter

from .. import ai_analysis

router = APIRouter(prefix="/api", tags=["ai"])


@router.get("/stocks/{symbol}/ai-analysis")
def ai_analysis_status(symbol: str):
    return ai_analysis.status(symbol)


@router.post("/stocks/{symbol}/ai-analysis/refresh")
def ai_analysis_refresh(symbol: str):
    return ai_analysis.request_generation(symbol)
