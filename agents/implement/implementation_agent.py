"""Code generation agent for The Hive."""

import json
from typing import Any

from ..base import BaseAgent
from ...orchestrator.state import WorkflowState


class ImplementationAgent(BaseAgent):
    """Generate implementation code from designs."""

    async def execute(self, state: WorkflowState) -> dict[str, Any]:
        """Generate code implementation.

        Args:
            state: Current workflow state

        Returns:
            Updated state fragment with code_artifact
        """
        if not state.design_artifact:
            return {"error_message": "Design artifact required for implementation"}

        prompt = self._build_code_prompt(state.design_artifact)

        # Call LLM
        response = await self.llm.complete(prompt)

        # Parse response
        code_artifact = self._parse_code_response(response)

        return {
            "code_artifact": code_artifact,
            "artifacts": {**state.artifacts, "code": code_artifact},
        }

    def _build_code_prompt(self, design: dict) -> str:
        """Build prompt for code generation.

        Args:
            design: Design artifact

        Returns:
            Formatted prompt
        """
        return f"""You are a senior software engineer. Generate production-ready code based on the following technical design.

Design:
{json.dumps(design, indent=2)}

Generate a JSON output with the following structure:

{{
    "files": [
        {{
            "path": "path/to/file.py",
            "language": "python",
            "content": "Complete file content",
            "description": "What this file does"
        }}
    ],
    "dependencies": [
        {{"name": "package-name", "version": "version specifier"}}
    ],
    "setup_instructions": ["Step 1", "Step 2"]
}}

Generate ONLY the JSON, no additional text."""

    def _parse_code_response(self, response: str) -> dict[str, Any]:
        """Parse LLM response into code artifact.

        Args:
            response: LLM response text

        Returns:
            Parsed code artifact
        """
        try:
            start = response.find("{")
            end = response.rfind("}") + 1
            json_str = response[start:end]
            return json.loads(json_str)
        except Exception as e:
            return {
                "error": f"Failed to parse code: {str(e)}",
                "raw_response": response,
            }
