from fastapi import APIRouter, Query

from ..db.store import add_watchlist, get_signal_history, get_watchlist, remove_watchlist

router = APIRouter(prefix="/api", tags=["watchlist"])


@router.get("/watchlist")
def read_watchlist(client_id: str = Query(..., min_length=8)):
    return {"symbols": get_watchlist(client_id)}


@router.post("/watchlist")
def create_watchlist_entry(client_id: str = Query(..., min_length=8), symbol: str = Query(...)):
    return {"symbols": add_watchlist(client_id, symbol)}


@router.delete("/watchlist")
def delete_watchlist_entry(client_id: str = Query(..., min_length=8), symbol: str = Query(...)):
    return {"symbols": remove_watchlist(client_id, symbol)}


@router.get("/stocks/{symbol}/signal-history")
def signal_history(symbol: str, limit: int = 90):
    return {"symbol": symbol.upper(), "history": get_signal_history(symbol, limit)}
