from __future__ import annotations
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import structlog

from .config import get_settings
from .database import create_all_tables
from .api import auth, projects, sessions, analytics
from .api.v1 import ingest

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

# CORS Middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.allowed_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include Routers
app.include_router(ingest.router, prefix="/v1", tags=["SDK Ingestion"])
app.include_router(auth.router, prefix="/api/auth", tags=["Authentication"])
app.include_router(projects.router, prefix="/api/projects", tags=["Projects"])
app.include_router(analytics.router, prefix="/api/projects", tags=["Analytics"])
app.include_router(sessions.router, prefix="/api/sessions", tags=["Sessions"])


@app.get("/")
def read_root():
    return {"status": "healthy", "service": "ghostrace-backend", "version": "0.1.0"}
