"""
ResQNet — FastAPI Application
"Persistent intelligence for crisis response."
"""
from __future__ import annotations

import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
import os

from app.config import settings
from app.db.engine import create_db_and_tables, init_vector_index

# Configure logging
logging.basicConfig(
    level=logging.DEBUG if settings.debug else logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)
logger = logging.getLogger("resqnet")


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Startup: initialize DB tables and vector index."""
    logger.info(f"🚀 ResQNet starting — provider: {settings.ai_provider}")
    await create_db_and_tables()
    await init_vector_index()
    # Create uploads dir for S3 mock
    os.makedirs(settings.local_upload_dir, exist_ok=True)
    logger.info("✅ ResQNet ready")
    yield
    logger.info("🛑 ResQNet shutting down")


app = FastAPI(
    title="ResQNet API",
    description="Persistent-memory AI coordination system for disaster response",
    version="1.0.0",
    lifespan=lifespan,
)

# ── CORS ──────────────────────────────────────────────────────────────────────
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ── Routes ────────────────────────────────────────────────────────────────────
from app.api import auth, incidents, reports, resources, alerts, agent, sync, evidence, memories, dashboard, requests_api, locations

app.include_router(auth.router)
app.include_router(incidents.router)
app.include_router(reports.router)
app.include_router(resources.router)
app.include_router(alerts.router)
app.include_router(agent.router)
app.include_router(sync.router)
app.include_router(evidence.router)
app.include_router(memories.router)
app.include_router(dashboard.router)
app.include_router(requests_api.router)
app.include_router(locations.router)


# ── Health check ──────────────────────────────────────────────────────────────
@app.get("/health")
async def health():
    return {
        "status": "ok",
        "service": "ResQNet",
        "ai_provider": settings.ai_provider,
        "s3_mock": settings.use_s3_mock,
        "lambda_mock": settings.use_lambda_mock,
    }


@app.get("/")
async def root():
    return {"message": "ResQNet API — persistent intelligence for crisis response"}
