"""Status query endpoints for The Hive API."""

from fastapi import APIRouter, HTTPException

from ...models.schemas import WorkflowStatus
from ....memory.redis.client import get_redis_client

router = APIRouter(tags=["Status"])


@router.get("/workflows/{workflow_id}/status", response_model=WorkflowStatus)
async def get_workflow_status(workflow_id: str) -> WorkflowStatus:
    """Get current status of a workflow.

    Args:
        workflow_id: Workflow ID

    Returns:
        Workflow status
    """
    redis = get_redis_client()

    # Get status from Redis
    status_data = redis.get(f"workflow:{workflow_id}:status")

    if not status_data:
        raise HTTPException(status_code=404, detail="Workflow not found")

    return WorkflowStatus(
        workflow_id=status_data.get("workflow_id", workflow_id),
        status=status_data.get("status", "UNKNOWN"),
        current_stage=status_data.get("current_stage"),
        progress=status_data.get("progress", {}),
        agent_states=status_data.get("agent_states", []),
    )
