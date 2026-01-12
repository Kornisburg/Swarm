"""Health check endpoints for The Hive API."""

from fastapi import APIRouter

router = APIRouter(tags=["Health"])


@router.get("/health")
async def health_check():
    """Health check endpoint.

    Returns:
        Health status response
    """
    # TODO: Add actual health checks for dependencies
    return {
        "status": "healthy",
        "timestamp": "2026-01-11T10:00:00Z",
        "version": "0.1.0",
        "components": {
            "orchestrator": "healthy",
            "database": "healthy",
            "redis": "healthy",
            "vector_store": "healthy",
        },
    }
