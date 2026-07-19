"""Artifact retrieval endpoints for The Hive API."""

from typing import Any

from fastapi import APIRouter, HTTPException

from memory.redis.client import get_redis_client

router = APIRouter(tags=["Artifacts"])


@router.get("/workflows/{workflow_id}/artifacts")
async def list_workflow_artifacts(workflow_id: str) -> dict[str, list]:
    """List all artifacts for a workflow.

    Args:
        workflow_id: Workflow ID

    Returns:
        List of artifacts
    """
    redis = get_redis_client()

    # Get workflow status
    status_data = redis.get(f"workflow:{workflow_id}:status")

    if not status_data:
        raise HTTPException(status_code=404, detail="Workflow not found")

    artifacts = status_data.get("artifacts", {})

    return {
        "workflow_id": workflow_id,
        "artifacts": [
            {
                "type": artifact_type,
                "artifact": artifact_data,
            }
            for artifact_type, artifact_data in artifacts.items()
        ],
    }


@router.get("/workflows/{workflow_id}/artifacts/{artifact_type}")
async def get_artifact(workflow_id: str, artifact_type: str) -> dict[str, Any]:
    """Get a specific artifact from a workflow.

    Args:
        workflow_id: Workflow ID
        artifact_type: Type of artifact (spec, design, code)

    Returns:
        Artifact data
    """
    redis = get_redis_client()

    # Get workflow status
    status_data = redis.get(f"workflow:{workflow_id}:status")

    if not status_data:
        raise HTTPException(status_code=404, detail="Workflow not found")

    artifacts = status_data.get("artifacts", {})

    if artifact_type not in artifacts:
        raise HTTPException(
            status_code=404, detail=f"Artifact {artifact_type} not found"
        )

    return {
        "workflow_id": workflow_id,
        "artifact_type": artifact_type,
        "artifact": artifacts[artifact_type],
    }
