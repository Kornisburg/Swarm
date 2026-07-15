"""Specification generation agent for The Hive."""

from typing import Any

from ..base import BaseAgent
from core.orchestrator.state import WorkflowState


class SpecAgent(BaseAgent):
    """Generate structured specifications from feature requests."""

    async def execute(self, state: WorkflowState) -> dict[str, Any]:
        """Generate specification document.

        Args:
            state: Current workflow state

        Returns:
            Updated state fragment with spec_artifact
        """
        prompt = self._build_spec_prompt(state.input_request)

        # Call LLM
        response = await self.llm.complete(prompt)

        # Parse and structure the response
        spec_artifact = self._parse_spec_response(response)

        return {
            "spec_artifact": spec_artifact,
            "artifacts": {**state.artifacts, "spec": spec_artifact},
        }

    def _build_spec_prompt(self, feature_request: str) -> str:
        """Build prompt for spec generation.

        Args:
            feature_request: User's feature request

        Returns:
            Formatted prompt
        """
        return f"""You are a product specification expert. Generate a comprehensive, structured specification for the following feature request.

Feature Request: {feature_request}

Your output must be a JSON object with the following structure:

{{
    "title": "Feature title",
    "description": "Brief description",
    "user_stories": [
        {{
            "title": "Story title",
            "priority": "P1/P2/P3",
            "description": "User story description",
            "acceptance_criteria": ["Given...When...Then..."]
        }}
    ],
    "functional_requirements": [
        {{"id": "FR-001", "description": "Requirement description"}}
    ],
    "success_criteria": [
        {{"id": "SC-001", "metric": "Measurable metric"}}
    ],
    "assumptions": ["List of assumptions"],
    "edge_cases": ["List of edge cases to consider"]
}}

Generate ONLY the JSON, no additional text."""

    def _parse_spec_response(self, response: str) -> dict[str, Any]:
        """Parse LLM response into spec artifact.

        Args:
            response: LLM response text

        Returns:
            Parsed spec artifact
        """
        import json

        try:
            # Try to extract JSON from response
            start = response.find("{")
            end = response.rfind("}") + 1
            json_str = response[start:end]
            return json.loads(json_str)
        except Exception as e:
            return {
                "error": f"Failed to parse spec: {str(e)}",
                "raw_response": response,
            }
