import logging
from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles

from . import scheduler
from .config import CORS_ORIGINS, DISCLAIMER
from .routers import advisor, market, mutual_funds, stocks, watchlist

logging.basicConfig(level=logging.INFO, format="%(levelname)s %(name)s: %(message)s")


@asynccontextmanager
async def lifespan(_: FastAPI):
    scheduler.start()
    yield
    scheduler.stop()


app = FastAPI(
    title="TrendWise API",
    description="Indian stock & ETF technical analysis engine. " + DISCLAIMER,
    version="1.0.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=CORS_ORIGINS,
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(stocks.router)
app.include_router(advisor.router)
app.include_router(market.router)
app.include_router(mutual_funds.router)
app.include_router(watchlist.router)


@app.get("/api/health")
def health():
    return {"status": "ok", "dataSource": "live", "disclaimer": DISCLAIMER}


# ---- Serve the built frontend (single-process deployment) ----
# When frontend/dist exists (production build), serve its assets and fall
# back to index.html for SPA routes. API routes above take precedence.
DIST = Path(__file__).resolve().parents[2] / "frontend" / "dist"
if (DIST / "index.html").is_file():
    app.mount("/assets", StaticFiles(directory=DIST / "assets"), name="assets")

    @app.get("/{full_path:path}")
    async def spa_fallback(full_path: str):
        if full_path == "api" or full_path.startswith("api/"):
            raise HTTPException(404, "Unknown API route")
        return FileResponse(DIST / "index.html")
