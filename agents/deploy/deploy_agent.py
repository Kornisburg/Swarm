from typing import Any

from core.orchestrator.state import WorkflowState
from observability.tracing.decision_decorator import track_decision

from ..base import BaseAgent


class DeployAgent(BaseAgent):
    """Stub deploy agent — deployment handled externally via CI/CD."""

    @track_decision(decision_type="deploy", track_input=False, track_output=True)
    async def execute(self, state: WorkflowState) -> dict[str, Any]:
        return {
            "status": "DEPLOYED",
            "artifacts": {
                **(state.artifacts or {}),
                "deploy": {
                    "status": "deployed",
                    "message": "Deployment handled via Cloud Build + GKE Autopilot",
                },
            },
        }
