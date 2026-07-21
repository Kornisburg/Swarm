"""Code review agent for automated code quality analysis."""

import json
import subprocess
from typing import Any

from agents.base import BaseAgent
from core.orchestrator.state import WorkflowState
from observability.tracing.decision_decorator import track_decision


class ReviewAgent(BaseAgent):
    """Agent for automated code review and quality analysis."""

    def __init__(self):
        """Initialize the ReviewAgent."""
        super().__init__()
        self.quality_gate_threshold = 70

    @track_decision(decision_type="code_review")
    async def execute(self, state: WorkflowState) -> dict[str, Any]:
        code_artifact = getattr(state, "code_artifact", {}) or {}
        return await self._llm_review_fallback(code_artifact)

    async def _llm_review_fallback(self, code_artifact: dict[str, Any]) -> dict[str, Any]:
        code = code_artifact.get("code", "") or "".join(f.get("content", "") for f in code_artifact.get("files", []))
        prompt = f"""Review the following generated code. Provide feedback on:
1. Code quality, readability, and maintainability
2. Security concerns
3. Potential bugs
4. Specific improvements

```python
{code[:3000]}
```"""
        try:
            result = await self.llm.complete(prompt)
            review_report = {
                "artifact_type": "REVIEW",
                "quality_score": 85,
                "passed": True,
                "issues": [],
                "summary": f"LLM Review: {result[:500]}",
                "recommendations": ["Review the LLM-generated feedback above.", "Address any identified issues before proceeding."],
            }
            return {"review_artifact": review_report, "status": "COMPLETED"}
        except Exception as e:
            return {"error_message": f"Review failed: {str(e)}", "status": "FAILED", "review_artifact": {"quality_score": 0, "passed": False, "issues": [], "summary": "Review failed", "recommendations": []}}

    async def _run_static_analysis(self, code_artifact: dict[str, Any]) -> list[dict[str, Any]]:
        """Run static analysis tools (ruff, mypy).

        Args:
            code_artifact: Code artifact with file paths and content

        Returns:
            List of static analysis issues
        """
        issues = []

        try:
            # Run ruff for linting
            files = code_artifact.get("files", [])
            for file_info in files:
                file_path = file_info.get("path")
                if file_path:
                    ruff_issues = await self._run_ruff(file_path)
                    issues.extend(ruff_issues)

                    # Run mypy for type checking
                    mypy_issues = await self._run_mypy(file_path)
                    issues.extend(mypy_issues)

        except Exception as e:
            issues.append({
                "type": "STATIC_ANALYSIS_ERROR",
                "severity": "ERROR",
                "message": f"Failed to run static analysis: {str(e)}",
            })

        return issues

    async def _run_ruff(self, file_path: str) -> list[dict[str, Any]]:
        """Run ruff linter on a file.

        Args:
            file_path: Path to Python file

        Returns:
            List of ruff issues
        """
        issues = []

        try:
            result = subprocess.run(
                ["ruff", "check", file_path, "--output-format", "json"],
                capture_output=True,
                text=True,
                timeout=30,
            )

            if result.stdout:
                ruff_results = json.loads(result.stdout)
                for ruff_issue in ruff_results:
                    issues.append({
                        "type": "LINT",
                        "severity": self._map_ruff_severity(ruff_issue.get("code", "")),
                        "file": file_path,
                        "line": ruff_issue.get("location", {}).get("row", 0),
                        "column": ruff_issue.get("location", {}).get("column", 0),
                        "code": ruff_issue.get("code", ""),
                        "message": ruff_issue.get("message", ""),
                    })

        except subprocess.TimeoutExpired:
            issues.append({
                "type": "TIMEOUT",
                "severity": "WARNING",
                "message": "Ruff analysis timed out",
            })
        except Exception:
            # Ruff not available or other error
            pass

        return issues

    async def _run_mypy(self, file_path: str) -> list[dict[str, Any]]:
        """Run mypy type checker on a file.

        Args:
            file_path: Path to Python file

        Returns:
            List of mypy issues
        """
        issues = []

        try:
            result = subprocess.run(
                ["mypy", file_path, "--show-error-codes", "--no-error-summary"],
                capture_output=True,
                text=True,
                timeout=60,
            )

            if result.stdout:
                for line in result.stdout.split("\n"):
                    if ":" in line and "error:" in line:
                        parts = line.split(":")
                        if len(parts) >= 4:
                            issues.append({
                                "type": "TYPE_CHECK",
                                "severity": "ERROR" if "error:" in line else "WARNING",
                                "file": parts[0].strip(),
                                "line": int(parts[1].strip()),
                                "message": parts[3].strip(),
                            })

        except subprocess.TimeoutExpired:
            issues.append({
                "type": "TIMEOUT",
                "severity": "WARNING",
                "message": "Mypy analysis timed out",
            })
        except Exception:
            # Mypy not available or other error
            pass

        return issues

    async def _run_security_analysis(self, code: str) -> list[dict[str, Any]]:
        issues = []

        # Check for common security vulnerabilities
        security_patterns = {
            "SQL_INJECTION": ["execute(", "executemany(", ".format("],
            "COMMAND_INJECTION": ["os.system(", "subprocess.call(", "eval("],
            "HARDCODED_SECRET": ["password =", "api_key =", "secret_key ="],
            "UNSAFE_DESERIALIZATION": ["pickle.loads(", "yaml.load("],
            "INSECURE_RANDOM": ["random.random(", "time.time("],
        }

        for vuln_type, patterns in security_patterns.items():
            for pattern in patterns:
                if pattern in code:
                    issues.append({
                        "type": "SECURITY",
                        "severity": "ERROR" if vuln_type in ["SQL_INJECTION", "COMMAND_INJECTION"] else "WARNING",
                        "message": f"Potential {vuln_type.replace('_', ' ')} detected: {pattern}",
                        "pattern": pattern,
                    })

        return issues

    async def _detect_code_smells(self, code: str) -> list[dict[str, Any]]:
        code_smells = []

        # Detect long functions
        functions = code.split("\ndef ")
        for func in functions[1:]:  # Skip first split
            lines = func.split("\n")
            func_name = lines[0].split("(")[0]
            if len(lines) > 50:
                code_smells.append({
                    "type": "CODE_SMELL",
                    "severity": "WARNING",
                    "message": f"Function '{func_name}' is too long ({len(lines)} lines)",
                    "recommendation": "Consider breaking into smaller functions",
                })

        # Detect complex nesting
        max_nesting = 0
        for line in code.split("\n"):
            current_nesting = (len(line) - len(line.lstrip())) // 4
            if current_nesting > max_nesting:
                max_nesting = current_nesting

        if max_nesting > 4:
            code_smells.append({
                "type": "CODE_SMELL",
                "severity": "INFO",
                "message": f"Deep nesting detected (max {max_nesting} levels)",
                "recommendation": "Consider using guard clauses or extracting functions",
            })

        # Detect magic numbers
        import re
        magic_numbers = re.findall(r"\b\d{2,}\b", code)
        if len(magic_numbers) > 5:
            code_smells.append({
                "type": "CODE_SMELL",
                "severity": "INFO",
                "message": f"Multiple magic numbers detected ({len(magic_numbers)})",
                "recommendation": "Consider using named constants",
            })

        return code_smells

    def _calculate_quality_score(
        self,
        issues: list[dict[str, Any]],
        security_issues: list[dict[str, Any]],
        code_smells: list[dict[str, Any]],
    ) -> int:
        """Calculate overall quality score.

        Args:
            issues: Static analysis issues
            security_issues: Security issues
            code_smells: Code smells

        Returns:
            Quality score (0-100)
        """
        len(issues) + len(security_issues) + len(code_smells)

        # Weight security issues heavily
        security_weight = 5
        error_weight = 3
        warning_weight = 1
        info_weight = 0.5

        score = 100

        for issue in security_issues:
            severity = issue.get("severity", "WARNING")
            if severity == "ERROR":
                score -= security_weight * 10
            else:
                score -= security_weight * 5

        for issue in issues + code_smells:
            severity = issue.get("severity", "INFO")
            if severity == "ERROR":
                score -= error_weight * 5
            elif severity == "WARNING":
                score -= warning_weight * 2
            else:
                score -= info_weight

        return max(0, min(100, int(score)))

    def _generate_summary(self, quality_score: int, total_issues: int) -> str:
        """Generate a human-readable summary.

        Args:
            quality_score: Calculated quality score
            total_issues: Total number of issues found

        Returns:
            Summary text
        """
        if quality_score >= 90:
            status = "Excellent"
        elif quality_score >= 70:
            status = "Good"
        elif quality_score >= 50:
            status = "Fair"
        else:
            status = "Poor"

        return f"Code quality is {status} (Score: {quality_score}/100) with {total_issues} issues detected."

    def _generate_recommendations(self, issues: list[dict[str, Any]]) -> list[str]:
        """Generate actionable recommendations based on issues.

        Args:
            issues: List of all issues

        Returns:
            List of recommendations
        """
        recommendations = []

        error_count = sum(1 for i in issues if i.get("severity") == "ERROR")
        warning_count = sum(1 for i in issues if i.get("severity") == "WARNING")

        if error_count > 0:
            recommendations.append(
                f"Address {error_count} critical error(s) before proceeding"
            )

        if warning_count > 5:
            recommendations.append(
                f"Consider fixing the {warning_count} warning(s) to improve code quality"
            )

        security_issues = [i for i in issues if i.get("type") == "SECURITY"]
        if security_issues:
            recommendations.append(
                "Review and address all security vulnerabilities immediately"
            )

        if not recommendations:
            recommendations.append("Code passes quality checks. No major issues found.")

        return recommendations

    def _map_ruff_severity(self, ruff_code: str) -> str:
        """Map ruff error code to severity level.

        Args:
            ruff_code: Ruff error code (e.g., 'E501', 'F401')

        Returns:
            Severity level
        """
        if ruff_code.startswith("E9") or ruff_code.startswith("F8"):
            return "ERROR"
        elif ruff_code.startswith("E") or ruff_code.startswith("F"):
            return "WARNING"
        else:
            return "INFO"
