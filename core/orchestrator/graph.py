"""LangGraph workflow orchestration for The Hive."""

import uuid
from typing import Any, Callable, Optional

from langchain.graphs import StateGraph
from langchain_core.messages import BaseMessage

from .state import WorkflowState
from ..workflow_definitions.stages import WorkflowStage, StageOrder
from ...exceptions import WorkflowException


class WorkflowOrchestrator:
    """LangGraph-based workflow orchestrator."""

    def __init__(self):
        """Initialize the workflow orchestrator."""
        self.graph: Optional[StateGraph] = None
        self.agents: dict[str, Callable] = {}
        self._build_graph()

    def _build_graph(self) -> None:
        """Build the LangGraph workflow graph."""
        # Create StateGraph with WorkflowState
        self.graph = StateGraph(WorkflowState)

        # Add agent nodes
        for stage in WorkflowStage:
            agent_func = self._create_agent_node(stage)
            self.graph.add_node(stage.value, agent_func)

        # Define edges between stages
        order = StageOrder.ORDER
        for i in range(len(order) - 1):
            self.graph.add_edge(order[i].value, order[i + 1].value)

        # Set entry point
        self.graph.set_entry_point(StageOrder.get_first_stage().value)

        # Compile the graph
        self.compiled_graph = self.graph.compile()

    def _create_agent_node(self, stage: WorkflowStage) -> Callable:
        """Create a LangGraph node for an agent.

        Args:
            stage: Workflow stage

        Returns:
            Node function
        """
        async def node_func(state: WorkflowState) -> dict[str, Any]:
            """Execute agent node.

            Args:
                state: Current workflow state

            Returns:
                Updated state fragment
            """
            agent = self.agents.get(stage.value)
            if agent is None:
                raise WorkflowException(f"No agent registered for stage: {stage.value}")

            # Execute the agent
            result = await agent(state)

            # Update state
            return {
                "current_stage": stage.value,
                "stage_history": state.stage_history + [stage.value],
                "updated_at": None,  # Will be set by graph
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

    async def execute(self, input_request: str) -> WorkflowState:
        """Execute the workflow.

        Args:
            input_request: User's feature request

        Returns:
            Final workflow state
        """
        # Initialize state
        initial_state = WorkflowState(
            workflow_id=str(uuid.uuid4()),
            input_request=input_request,
            status="RUNNING",
        )

        # Execute graph
        final_state = None
        async for state_snapshot in self.compiled_graph.astream(initial_state):
            final_state = state_snapshot

        return final_state or initial_state
