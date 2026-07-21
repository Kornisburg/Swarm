"""Health check endpoints for The Hive API."""

from datetime import UTC, datetime

from fastapi import APIRouter

from memory.postgres.client import get_postgres_client
from memory.redis.client import get_redis_client
from memory.vectorstore.chroma_store import get_vector_store

router = APIRouter(tags=["Health"])


@router.get("/health")
async def health_check():
    """Health check endpoint with real dependency verification."""

    checks = {}

    # Check PostgreSQL
    try:
        pg = get_postgres_client()
        checks["database"] = "healthy" if pg.health_check() else "degraded"
    except Exception:
        checks["database"] = "unhealthy"

    # Check Redis
    try:
        redis = get_redis_client()
        checks["redis"] = "healthy" if redis.health_check() else "degraded"
    except Exception:
        checks["redis"] = "unhealthy"

    # Check Chroma (optional — may not be running)
    try:
        chroma = get_vector_store()
        checks["vector_store"] = "healthy" if chroma.health_check() else "degraded"
    except Exception:
        checks["vector_store"] = "unavailable"

    overall = "healthy"
    for status in checks.values():
        if status == "unhealthy":
            overall = "degraded"
            break
        if status == "degraded":
            overall = "degraded"

    return {
        "status": overall,
        "timestamp": datetime.now(UTC).isoformat(),
        "version": "0.1.0",
        "components": checks,
    }
