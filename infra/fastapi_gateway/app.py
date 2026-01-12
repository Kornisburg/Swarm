"""FastAPI application for The Hive."""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from .routes import health, workflows, status, artifacts

app = FastAPI(
    title="The Hive - Multi-Agent Engineering System",
    description="AI-powered coding workflow orchestration",
    version="0.1.0",
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(health.router)
app.include_router(workflows.router)
app.include_router(status.router)
app.include_router(artifacts.router)


@app.on_event("startup")
async def startup_event():
    """Initialize application on startup."""
    # Initialize database
    from ...memory.postgres.client import get_postgres_client
    postgres = get_postgres_client()
    postgres.create_tables()

    # Initialize Redis connection
    from ...memory.redis.client import get_redis_client
    redis = get_redis_client()
    if not redis.health_check():
        raise RuntimeError("Redis connection failed")


@app.on_event("shutdown")
async def shutdown_event():
    """Cleanup on shutdown."""
    pass
