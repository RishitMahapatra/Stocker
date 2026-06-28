"""
Stocker — FastAPI Application Entry Point
"""

import asyncio
import uvicorn
from contextlib import asynccontextmanager
from datetime import datetime, timezone

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from backend.config import FRONTEND_URL, APP_HOST, APP_PORT
from backend.database import create_all_tables


_scheduler_instance = None


@asynccontextmanager
async def lifespan(app: FastAPI):
    global _scheduler_instance

    # Startup
    print("[main] Starting Stocker API ...")
    create_all_tables()

    from backend.scheduler import start_scheduler, run_full_pipeline
    _scheduler_instance = start_scheduler()

    # Initial pipeline run on startup (non-blocking — fire and forget)
    asyncio.create_task(run_full_pipeline())

    yield

    # Shutdown
    print("[main] Shutting down Stocker API ...")
    if _scheduler_instance:
        from backend.scheduler import stop_scheduler
        stop_scheduler(_scheduler_instance)


app = FastAPI(title="Stocker API", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=[FRONTEND_URL, "http://localhost:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ── Routers ──────────────────────────────
from backend.api.routes_market import router as market_router
from backend.api.routes_signals import router as signals_router
from backend.api.routes_portfolio import router as portfolio_router

app.include_router(market_router)
app.include_router(signals_router)
app.include_router(portfolio_router)


# ── Health check ─────────────────────────
@app.get("/health", response_model=None)
async def health():
    return {"status": "ok", "time": datetime.now(timezone.utc).isoformat()}


if __name__ == "__main__":
    uvicorn.run("backend.main:app", host=APP_HOST, port=APP_PORT, reload=True)
