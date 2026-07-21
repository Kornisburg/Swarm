"""Prometheus metrics endpoint for The Hive."""

from fastapi import APIRouter, Response
from prometheus_client import CONTENT_TYPE_LATEST, generate_latest

from observability.exporters.prometheus import get_prometheus_exporter

router = APIRouter(tags=["Metrics"])


@router.get("/metrics")
async def metrics_endpoint() -> Response:
    """Expose Prometheus metrics."""
    exporter = get_prometheus_exporter()
    data = generate_latest(exporter.registry)
    return Response(content=data, media_type=CONTENT_TYPE_LATEST)
