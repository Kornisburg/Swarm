"""Workflow submission endpoints for The Hive API."""

import uuid
from datetime import datetime

from fastapi import APIRouter, BackgroundTasks

from core.orchestrator.graph import WorkflowOrchestrator
from core.workflow_definitions.stages import WorkflowStage
from memory.postgres.client import get_postgres_client
from memory.redis.client import get_redis_client
from observability.exporters.jaeger import get_logger

from ..models.schemas import WorkflowSubmission, WorkflowSubmissionResponse

logger = get_logger("hive.api.workflows")
router = APIRouter(tags=["Workflows"])

# Global orchestrator instance
orchestrator = WorkflowOrchestrator()


def _register_all_agents() -> None:
    """Register all available agents with the global orchestrator."""
    from agents.base import BaseAgent

    agent_sources: dict[WorkflowStage, type[BaseAgent]] = {}

    try:
        from agents.spec.spec_agent import SpecAgent
        agent_sources[WorkflowStage.SPEC] = SpecAgent
    except ImportError as e:
        logger.warning("SpecAgent import failed", error=str(e))

    try:
        from agents.design.design_agent import DesignAgent
        agent_sources[WorkflowStage.DESIGN] = DesignAgent
    except ImportError as e:
        logger.warning("DesignAgent import failed", error=str(e))

    try:
        from agents.implement.implementation_agent import ImplementationAgent
        agent_sources[WorkflowStage.IMPLEMENT] = ImplementationAgent
    except ImportError as e:
        logger.warning("ImplementationAgent import failed", error=str(e))

    try:
        from agents.review.review_agent import ReviewAgent
        agent_sources[WorkflowStage.REVIEW] = ReviewAgent
    except ImportError as e:
        logger.warning("ReviewAgent import failed", error=str(e))

    try:
        from agents.test.test_agent import TestAgent
        agent_sources[WorkflowStage.TEST] = TestAgent
    except ImportError as e:
        logger.warning("TestAgent import failed", error=str(e))

    try:
        from agents.deploy.deploy_agent import DeployAgent
        agent_sources[WorkflowStage.DEPLOY] = DeployAgent
    except ImportError as e:
        logger.warning("DeployAgent import failed", error=str(e))

    for stage, agent_class in agent_sources.items():
        try:
            agent_instance = agent_class()
            orchestrator.register_agent(stage, agent_instance.invoke)
            logger.info("Agent registered", stage=stage.value, agent=agent_class.__name__)
        except Exception as e:
            logger.warning("Agent registration failed", stage=stage.value, error=str(e))


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
    logger.info(
        "Workflow submitted",
        workflow_id=workflow_id,
        input_request_preview=submission.input_request[:100],
    )

    redis = get_redis_client()
    redis.set(
        f"workflow:{workflow_id}:request",
        submission.dict(),
        ttl=86400,
    )

    background_tasks.add_task(execute_workflow, workflow_id, submission.input_request)

    return WorkflowSubmissionResponse(
        workflow_id=workflow_id,
        status="PENDING",
        created_at=datetime.utcnow(),
        estimated_completion=None,
    )


async def execute_workflow(workflow_id: str, input_request: str) -> None:
    """Execute workflow asynchronously."""
    try:
        final_state = await orchestrator.execute(input_request, workflow_id)

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

        logger.info(
            "Workflow result persisted",
            workflow_id=workflow_id,
            status=final_state.status,
            stage_count=len(final_state.stage_history),
        )

    except Exception as e:
        logger.error("Workflow background execution failed", workflow_id=workflow_id, error=str(e))
        redis = get_redis_client()
        redis.set(
            f"workflow:{workflow_id}:status",
            {"workflow_id": workflow_id, "status": "FAILED", "error": str(e)},
            ttl=86400,
        )


@router.delete("/workflows/{workflow_id}")
async def cancel_workflow(workflow_id: str) -> dict[str, str]:
    """Cancel a running workflow."""
    redis = get_redis_client()

    redis.set(
        f"workflow:{workflow_id}:status",
        {"workflow_id": workflow_id, "status": "CANCELLED"},
        ttl=86400,
    )

    logger.info("Workflow cancelled", workflow_id=workflow_id)

    return {
        "workflow_id": workflow_id,
        "status": "CANCELLED",
        "message": "Workflow cancelled successfully",
    }
