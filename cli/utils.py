"""Shared utilities for CLI commands."""

import json
from typing import Optional

import click
from rich.console import Console
from rich.panel import Panel

from core.exceptions import WorkflowException

console = Console()


class JSONParamType(click.ParamType):
    """Custom parameter type for JSON input."""

    name = "json"

    def convert(self, value: str, param: Optional[click.Parameter], ctx: Optional[click.Context]) -> dict:
        """Convert JSON string to dictionary.

        Args:
            value: JSON string value
            param: Click parameter
            ctx: Click context

        Returns:
            Parsed JSON dictionary

        Raises:
            click.BadParameter: If JSON is invalid
        """
        try:
            return json.loads(value)
        except json.JSONDecodeError as e:
            self.fail(f"Invalid JSON: {str(e)}", param, ctx)


JSON = JSONParamType()


def handle_error(error: Exception, message: str = "An error occurred") -> None:
    """Handle CLI errors with appropriate output formatting.

    Args:
        error: The exception that occurred
        message: Error message to display
    """
    if isinstance(error, WorkflowException):
        error_msg = f"Workflow Error: {str(error)}"
    elif isinstance(error, click.ClickException):
        error_msg = f"CLI Error: {str(error)}"
    else:
        error_msg = f"{message}: {str(error)}"

    console.print(Panel(error_msg, title="[red]Error[/red]", border_style="red"))
