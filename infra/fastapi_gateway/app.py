"""FastAPI application for The Hive."""

import logging
import sys

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware

from observability.exporters.jaeger import generate_request_id, get_logger, request_id_ctx, JSONFormatter
from .routes import artifacts, health, metrics, status, workflows

# Patch uvicorn's access logger to use JSON format
_logger = logging.getLogger("uvicorn.access")
_logger.handlers.clear()
_handler = logging.StreamHandler(sys.stdout)
_handler.setFormatter(JSONFormatter())
_logger.addHandler(_handler)
_logger.propagate = False

# Also JSONify the error logger
_logger_err = logging.getLogger("uvicorn.error")
_logger_err.handlers.clear()
_handler_err = logging.StreamHandler(sys.stdout)
_handler_err.setFormatter(JSONFormatter())
_logger_err.addHandler(_handler_err)
_logger_err.propagate = False

logger = get_logger("hive.api")

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


@app.middleware("http")
async def request_id_middleware(request: Request, call_next):
    """Attach a request ID to every request."""
    req_id = request.headers.get("X-Request-Id", generate_request_id())
    request_id_ctx.set(req_id)
    response = await call_next(request)
    response.headers["X-Request-Id"] = req_id
    return response


# Include routers
app.include_router(health.router)
app.include_router(workflows.router)
app.include_router(status.router)
app.include_router(artifacts.router)
app.include_router(metrics.router)


@app.on_event("startup")
async def startup_event():
    """Initialize application on startup."""
    logger.info("Starting Hive application", event="startup")

    # Initialize database
    from memory.postgres.client import get_postgres_client

    postgres = get_postgres_client()
    postgres.create_tables()
    if not postgres.health_check():
        logger.warning("PostgreSQL health check failed (may be starting up)", component="database")
    else:
        logger.info("PostgreSQL connection established", component="database")

    # Initialize Redis connection
    from memory.redis.client import get_redis_client

    redis = get_redis_client()
    if not redis.health_check():
        logger.warning("Redis health check failed (may be starting up)", component="redis")
    else:
        logger.info("Redis connection established", component="redis")

    # Initialize Chroma vector store
    try:
        from memory.vectorstore.chroma_store import get_vector_store

        chroma = get_vector_store()
        if not chroma.health_check():
            logger.warning("Chroma health check failed (may be starting up)", component="vector_store")
    except Exception as exc:
        logger.warning("Chroma initialization failed", component="vector_store", error=str(exc))

    # Register agents with the orchestrator
    try:
        from .routes.workflows import _register_all_agents

        _register_all_agents()
    except Exception as exc:
        logger.error("Agent registration failed", error=str(exc))

    logger.info("Hive application startup complete", event="startup")


@app.on_event("shutdown")
async def shutdown_event():
    """Cleanup on shutdown."""
    logger.info("Shutting down Hive application", event="shutdown")
