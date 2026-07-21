"""Architecture design agent for The Hive."""

import json
from typing import Any

from core.orchestrator.state import WorkflowState
from observability.tracing.decision_decorator import track_decision

from ..base import BaseAgent


class DesignAgent(BaseAgent):
    """Generate architecture design from specifications."""

    @track_decision(decision_type="design_generation", track_input=True, track_output=True)
    async def execute(self, state: WorkflowState) -> dict[str, Any]:
        """Generate design document.

        Args:
            state: Current workflow state

        Returns:
            Updated state fragment with design_artifact
        """
        if not state.spec_artifact:
            return {"error_message": "Spec artifact required for design"}

        prompt = self._build_design_prompt(state.spec_artifact)

        # Call LLM
        response = await self.llm.complete(prompt)

        # Parse response
        design_artifact = self._parse_design_response(response)

        return {
            "design_artifact": design_artifact,
            "artifacts": {**state.artifacts, "design": design_artifact},
        }

    def _build_design_prompt(self, spec: dict) -> str:
        """Build prompt for design generation.

        Args:
            spec: Specification artifact

        Returns:
            Formatted prompt
        """
        return f"""You are a software architect. Generate a comprehensive technical design document based on the following specification.

Specification:
{json.dumps(spec, indent=2)}

Your output must be a JSON object with the following structure:

{{
    "architecture": "High-level architecture description",
    "modules": [
        {{"name": "Module name", "responsibility": "What it does", "dependencies": ["Other modules"]}}
    ],
    "data_model": [
        {{"name": "Entity", "fields": ["field1", "field2"], "relationships": "Other entities"}}
    ],
    "api_contracts": [
        {{"endpoint": "POST /api/resource", "description": "What it does", "inputs": [], "outputs": []}}
    ],
    "technology_choices": [
        {{"component": "Component name", "choice": "Technology choice", "rationale": "Why this choice"}}
    ]
}}

Generate ONLY the JSON, no additional text."""

    def _parse_design_response(self, response: str) -> dict[str, Any]:
        """Parse LLM response into design artifact.

        Args:
            response: LLM response text

        Returns:
            Parsed design artifact
        """
        try:
            start = response.find("{")
            end = response.rfind("}") + 1
            json_str = response[start:end]
            return json.loads(json_str)
        except Exception as e:
            return {
                "error": f"Failed to parse design: {str(e)}",
                "raw_response": response,
            }
