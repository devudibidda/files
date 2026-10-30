from fastapi import APIRouter, HTTPException, Query

from ..advisor import PROFILES, build_portfolio, profile_for

router = APIRouter(prefix="/api/advisor", tags=["advisor"])

HORIZONS = ("short", "medium", "long")
REACTIONS = ("panic", "hold", "invest")


@router.get("/portfolio")
def advisor_portfolio(
    horizon: str = Query(..., description="short | medium | long"),
    reaction: str = Query(..., description="panic | hold | invest"),
):
    if horizon not in HORIZONS:
        raise HTTPException(400, f"Unknown horizon '{horizon}'. Valid: {', '.join(HORIZONS)}")
    if reaction not in REACTIONS:
        raise HTTPException(400, f"Unknown reaction '{reaction}'. Valid: {', '.join(REACTIONS)}")
    profile = profile_for(horizon, reaction)
    result = build_portfolio(profile)
    if not result:
        raise HTTPException(503, "Could not build a starter portfolio right now")
    return result


@router.get("/profiles")
def advisor_profiles():
    return {
        "profiles": [
            {"id": pid, "label": meta["label"], "line": meta["line"],
             "slots": [{"role": r, "allocationPct": p} for r, p in meta["slots"]]}
            for pid, meta in PROFILES.items()
        ]
    }
