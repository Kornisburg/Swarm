"""Workflow submission endpoints for The Hive API."""

import uuid
from datetime import datetime
from typing import Any

from fastapi import APIRouter, HTTPException, BackgroundTasks

from infra.fastapi_gateway.models.schemas import WorkflowSubmission, WorkflowSubmissionResponse
from core.orchestrator.state import WorkflowState
from core.orchestrator.graph import WorkflowOrchestrator
from memory.postgres.client import get_postgres_client
from memory.redis.client import get_redis_client
from observability.exporters.prometheus import PrometheusExporter

router = APIRouter(tags=["Workflows"])

# Global orchestrator instance
orchestrator = WorkflowOrchestrator()
metrics = PrometheusExporter()


@router.post("/workflows", response_model=WorkflowSubmissionResponse)
async def submit_workflow(
    submission: WorkflowSubmission,
    background_tasks: BackgroundTasks,
) -> WorkflowSubmissionResponse:
    """Submit a new workflow for execution.

    Args:
        submission: Workflow submission data
        background_tasks: FastAPI background tasks

    Returns:
        Workflow submission response
    """
    workflow_id = str(uuid.uuid4())

    # Record metrics
    metrics.record_workflow_start()

    # Store in Redis for session tracking
    redis = get_redis_client()
    redis.set(
        f"workflow:{workflow_id}:request",
        submission.dict(),
        ttl=86400,  # 24 hours
    )

    # Execute workflow in background
    background_tasks.add_task(execute_workflow, workflow_id, submission.input_request)

    return WorkflowSubmissionResponse(
        workflow_id=workflow_id,
        status="PENDING",
        created_at=datetime.utcnow(),
        estimated_completion=None,
    )


async def execute_workflow(workflow_id: str, input_request: str) -> None:
    """Execute workflow asynchronously.

    Args:
        workflow_id: Workflow ID
        input_request: Feature request
    """
    try:
        # Execute workflow
        final_state = await orchestrator.execute(input_request)

        # Update status in Redis
        redis = get_redis_client()
        redis.set(
            f"workflow:{workflow_id}:status",
            {
                "workflow_id": workflow_id,
                "status": final_state.status,
                "current_stage": final_state.current_stage,
                "artifacts": final_state.artifacts,
            },
            ttl=86400,
        )

        # Record completion metrics
        duration = (final_state.updated_at - final_state.created_at).total_seconds()
        metrics.record_workflow_complete(final_state.status, duration)

        # Persist to PostgreSQL
        postgres = get_postgres_client()
        with postgres.get_session() as session:
            from memory.postgres.models import WorkflowSession

            workflow_session = WorkflowSession(
                id=workflow_id,
                input_request={"request": input_request},
                status=final_state.status,
                current_stage=final_state.current_stage,
                artifacts_summary=final_state.artifacts,
            )
            session.add(workflow_session)

    except Exception as e:
        # Record error
        redis = get_redis_client()
        redis.set(
            f"workflow:{workflow_id}:status",
            {"workflow_id": workflow_id, "status": "FAILED", "error": str(e)},
            ttl=86400,
        )


@router.delete("/workflows/{workflow_id}")
async def cancel_workflow(workflow_id: str) -> dict[str, str]:
    """Cancel a running workflow.

    Args:
        workflow_id: Workflow ID

    Returns:
        Cancellation response
    """
    redis = get_redis_client()

    # Update status
    redis.set(
        f"workflow:{workflow_id}:status",
        {"workflow_id": workflow_id, "status": "CANCELLED"},
        ttl=86400,
    )

    return {
        "workflow_id": workflow_id,
        "status": "CANCELLED",
        "message": "Workflow cancelled successfully",
    }
