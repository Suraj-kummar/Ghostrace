from __future__ import annotations
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.gzip import GZipMiddleware
import structlog

from .config import get_settings
from .database import create_all_tables
from .api import auth, projects, sessions, analytics
from .api import health as health_api
from .api import traces as traces_api
from .api.v1 import ingest
from .middleware import TimingMiddleware, RequestIDMiddleware

logger = structlog.get_logger()


@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("Initializing database tables...")
    await create_all_tables()
    logger.info("Database tables initialized.")
    yield


settings = get_settings()

app = FastAPI(
    title="Ghostrace API",
    description="AI Agent Observability Backend",
    version="0.1.0",
    lifespan=lifespan,
)

# ── Middleware (outermost → innermost) ────────────────────────────────────────
app.add_middleware(GZipMiddleware, minimum_size=1000)
app.add_middleware(TimingMiddleware)
app.add_middleware(RequestIDMiddleware)
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.allowed_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ── Routers ───────────────────────────────────────────────────────────────────
app.include_router(health_api.router)
app.include_router(ingest.router, prefix="/v1", tags=["SDK Ingestion"])
app.include_router(auth.router, prefix="/api/auth", tags=["Authentication"])
app.include_router(projects.router, prefix="/api/projects", tags=["Projects"])
app.include_router(analytics.router, prefix="/api/projects", tags=["Analytics"])
app.include_router(sessions.router, prefix="/api/sessions", tags=["Sessions"])
app.include_router(traces_api.router)


@app.get("/")
def read_root():
    return {
        "status": "healthy",
        "service": "ghostrace-backend",
        "version": "0.1.0",
        "environment": settings.environment,
        "docs": "/docs",
    }
