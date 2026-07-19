"""LangGraph workflow orchestration for The Hive."""

import time
import uuid
from collections.abc import Callable
from typing import Any

from langgraph.graph import StateGraph

from observability.exporters.jaeger import get_logger
from observability.exporters.prometheus import get_prometheus_exporter
from observability.tracing.decision_decorator import get_decision_tracker

from ..exceptions import WorkflowException
from ..workflow_definitions.stages import StageOrder, WorkflowStage
from .state import WorkflowState

logger = get_logger("hive.orchestrator")


class WorkflowOrchestrator:
    """LangGraph-based workflow orchestrator."""

    def __init__(self):
        """Initialize the workflow orchestrator."""
        self.graph: StateGraph | None = None
        self.agents: dict[str, Callable] = {}
        self._metrics = get_prometheus_exporter()
        self._decision_tracker = get_decision_tracker()
        self._build_graph()

    def _build_graph(self) -> None:
        """Build the LangGraph workflow graph."""
        self.graph = StateGraph(WorkflowState)

        for stage in WorkflowStage:
            agent_func = self._create_agent_node(stage)
            self.graph.add_node(stage.value, agent_func)

        order = StageOrder.ORDER
        for i in range(len(order) - 1):
            self.graph.add_edge(order[i].value, order[i + 1].value)

        self.graph.set_entry_point(StageOrder.get_first_stage().value)
        self.compiled_graph = self.graph.compile()
        logger.info("Workflow graph compiled", stages=[s.value for s in WorkflowStage])

    def _create_agent_node(self, stage: WorkflowStage) -> Callable:
        """Create a LangGraph node for an agent.

        Args:
            stage: Workflow stage

        Returns:
            Node function
        """
        async def node_func(state: WorkflowState) -> dict[str, Any]:
            agent = self.agents.get(stage.value)
            if agent is None:
                raise WorkflowException(f"No agent registered for stage: {stage.value}")

            start = time.monotonic()
            logger.info(
                "Agent stage started",
                workflow_id=state.workflow_id,
                stage=stage.value,
                agent_type=stage.value,
            )

            try:
                result = await agent(state)

                duration = time.monotonic() - start
                self._metrics.record_agent_invocation(stage.value, duration)
                logger.info(
                    "Agent stage completed",
                    workflow_id=state.workflow_id,
                    stage=stage.value,
                    duration_seconds=round(duration, 3),
                )
            except Exception as e:
                duration = time.monotonic() - start
                logger.error(
                    "Agent stage failed",
                    workflow_id=state.workflow_id,
                    stage=stage.value,
                    error=str(e),
                    duration_seconds=round(duration, 3),
                )
                raise WorkflowException(
                    f"Agent {stage.value} failed after {duration:.1f}s: {e}"
                ) from e

            from datetime import datetime
            return {
                **state.model_dump(),
                "current_stage": stage.value,
                "stage_history": state.stage_history + [stage.value],
                "updated_at": datetime.utcnow(),
                **result,
            }

        return node_func

    def register_agent(self, stage: WorkflowStage, agent_func: Callable) -> None:
        """Register an agent function for a stage.

        Args:
            stage: Workflow stage
            agent_func: Agent execution function
        """
        self.agents[stage.value] = agent_func
        logger.info("Agent registered", stage=stage.value, agent=str(agent_func))

    async def execute(self, input_request: str, workflow_id: str | None = None) -> WorkflowState:
        """Execute the workflow.

        Args:
            input_request: User's feature request
            workflow_id: Optional workflow ID (generated if not provided)

        Returns:
            Final workflow state
        """
        workflow_id = workflow_id or str(uuid.uuid4())
        logger.info(
            "Workflow execution started",
            workflow_id=workflow_id,
        )

        initial_state = WorkflowState(
            workflow_id=workflow_id,
            input_request=input_request,
            status="RUNNING",
        )

        self._metrics.record_workflow_start()
        start = time.monotonic()

        current_state = initial_state
        try:
            for stage in StageOrder.ORDER:
                agent_func = self.agents.get(stage.value)
                if agent_func is None:
                    raise WorkflowException(f"No agent registered for stage: {stage.value}")

                start_time = time.monotonic()
                logger.info(
                    "Agent stage started",
                    workflow_id=workflow_id,
                    stage=stage.value,
                    agent_type=stage.value,
                )

                try:
                    result = await agent_func(current_state)
                    duration = time.monotonic() - start_time
                    self._metrics.record_agent_invocation(stage.value, duration)
                    agent_status = result.get("status", "COMPLETED")
                    if agent_status in ("FAILED",):
                        logger.warning(
                            "Agent stage returned failure",
                            workflow_id=workflow_id,
                            stage=stage.value,
                            error=result.get("error_message", ""),
                            duration_seconds=round(duration, 3),
                        )
                    else:
                        logger.info(
                            "Agent stage completed",
                            workflow_id=workflow_id,
                            stage=stage.value,
                            duration_seconds=round(duration, 3),
                        )
                except Exception as exc:
                    duration = time.monotonic() - start_time
                    logger.error(
                        "Agent stage failed",
                        workflow_id=workflow_id,
                        stage=stage.value,
                        error=str(exc),
                        duration_seconds=round(duration, 3),
                    )
                    raise WorkflowException(f"Agent {stage.value} failed: {exc}") from exc

                from datetime import datetime
                state_before = current_state.model_dump()
                update = {
                    **state_before,
                    "current_stage": stage.value,
                    "stage_history": current_state.stage_history + [stage.value],
                    "updated_at": datetime.utcnow(),
                    **result,
                }
                current_state = WorkflowState(**update)
                logger.info(
                    "State after stage",
                    stage=stage.value,
                    spec_val="present" if current_state.spec_artifact else "missing",
                    design_val="present" if current_state.design_artifact else "missing",
                    artifact_keys=list((current_state.artifacts or {}).keys()),
                    result_has_artifact="artifacts" in result,
                )

            duration = time.monotonic() - start
            status = current_state.status
            self._metrics.record_workflow_complete(status, duration)
            logger.info(
                "Workflow execution completed",
                workflow_id=workflow_id,
                status=status,
                duration_seconds=round(duration, 3),
            )
        except Exception as e:
            duration = time.monotonic() - start
            self._metrics.record_workflow_complete("FAILED", duration)
            logger.error(
                "Workflow execution failed",
                workflow_id=workflow_id,
                error=str(e),
                duration_seconds=round(duration, 3),
            )
            raise

        return current_state
