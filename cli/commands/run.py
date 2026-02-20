"""Workflow run command for The Hive CLI."""

import asyncio
import json
from pathlib import Path
from typing import Optional

import click
import httpx
from rich.console import Console
from rich.live import Live
from rich.panel import Panel
from rich.progress import (
    BarColumn,
    Progress,
    SpinnerColumn,
    TextColumn,
    TimeRemainingColumn,
)
from rich.table import Table

from cli.utils import JSON, handle_error

console = Console()


async def submit_workflow(
    api_url: str,
    request: str,
    project_id: Optional[str] = None,
    context: Optional[dict] = None,
) -> dict:
    """Submit a workflow to the API.

    Args:
        api_url: Base API URL
        request: Feature request description
        project_id: Optional project ID for context
        context: Additional context parameters

    Returns:
        Workflow submission response

    Raises:
        httpx.HTTPError: If API request fails
    """
    async with httpx.AsyncClient(timeout=60.0) as client:
        payload = {"input_request": request}
        if project_id:
            payload["project_id"] = project_id
        if context:
            payload["context"] = context

        response = await client.post(
            f"{api_url}/api/workflows/submit",
            json=payload,
        )
        response.raise_for_status()
        return response.json()


async def poll_workflow_status(api_url: str, workflow_id: str) -> dict:
    """Poll workflow status from API.

    Args:
        api_url: Base API URL
        workflow_id: Workflow ID

    Returns:
        Workflow status response

    Raises:
        httpx.HTTPError: If API request fails
    """
    async with httpx.AsyncClient(timeout=30.0) as client:
        response = await client.get(
            f"{api_url}/api/workflows/{workflow_id}/status",
        )
        response.raise_for_status()
        return response.json()


async def run_workflow_async(
    request: str,
    api_url: str,
    project_id: Optional[str] = None,
    context: Optional[dict] = None,
    follow: bool = True,
    json_output: bool = False,
) -> None:
    """Run workflow and optionally follow progress.

    Args:
        request: Feature request description
        api_url: Base API URL
        project_id: Optional project ID
        context: Additional context
        follow: Whether to follow progress
        json_output: Whether to output JSON
    """
    try:
        # Submit workflow
        console.print(f"[cyan]Submitting workflow...[/cyan]")
        result = await submit_workflow(api_url, request, project_id, context)

        if json_output:
            console.print_json(json.dumps(result))
            return

        workflow_id = result["workflow_id"]
        console.print(f"[green]✓[/green] Workflow submitted: {workflow_id}")

        if not follow:
            console.print(f"\n[yellow]Use 'hive workflow status {workflow_id}' to check progress[/yellow]")
            return

        # Follow workflow progress
        with Live(console=console, refresh_per_second=2) as live:
            while True:
                status_data = await poll_workflow_status(api_url, workflow_id)
                status = status_data.get("status", "UNKNOWN")
                current_stage = status_data.get("current_stage", "None")
                stage_history = status_data.get("stage_history", [])
                error_message = status_data.get("error_message")

                # Build progress display
                if status == "FAILED" and error_message:
                    panel = Panel(
                        f"[red]Error:[/red] {error_message}",
                        title="[red]Workflow Failed[/red]",
                        border_style="red",
                    )
                    live.update(panel)
                    break

                progress = Progress(
                    SpinnerColumn(),
                    TextColumn("[progress.description]{task.description}"),
                    BarColumn(),
                    TextColumn("[progress.percentage]{task.percentage:>3.0f}%"),
                    TimeRemainingColumn(),
                )

                task = progress.add_task(
                    f"Workflow Progress - {status}", total=100, completed=get_stage_progress(status)
                )

                # Create status table
                table = Table(show_header=True, header_style="bold magenta")
                table.add_column("Property", style="cyan")
                table.add_column("Value", style="green")

                table.add_row("Workflow ID", workflow_id)
                table.add_row("Status", status)
                table.add_row("Current Stage", current_stage)

                if stage_history:
                    table.add_row(
                        "Stage Progress",
                        " → ".join(stage_history),
                    )

                # Combine progress and table
                panel = Panel(
                    progress,
                    title=f"[bold blue]The Hive - Workflow Progress[/bold blue]",
                    border_style="blue",
                )

                live.update(Panel(Group(table, panel)))

                if status in ("COMPLETED", "FAILED", "CANCELLED"):
                    break

                await asyncio.sleep(2)

        console.print(f"\n[green]✓[/green] Workflow {status.lower()}")

        if status == "COMPLETED":
            console.print(f"\n[yellow]Use 'hive workflow artifacts {workflow_id}' to view results[/yellow]")

    except Exception as e:
        handle_error(e, "Failed to run workflow")


def get_stage_progress(status: str) -> int:
    """Get progress percentage based on workflow status.

    Args:
        status: Workflow status

    Returns:
        Progress percentage
    """
    progress_map = {
        "PENDING": 0,
        "RUNNING": 50,
        "COMPLETED": 100,
        "FAILED": 100,
        "CANCELLED": 100,
    }
    return progress_map.get(status, 0)


@click.command()
@click.argument("request")
@click.option("--project", "-p", help="Project ID for context")
@click.option("--context", "-c", type=JSON, help="Additional context as JSON")
@click.option("--api-url", help="Override API URL")
@click.option("--no-follow", is_flag=True, help="Don't follow progress")
@click.option("--file", "-f", type=click.Path(exists=True), help="Read request from file")
@click.pass_context
def run_cmd(
    ctx: click.Context,
    request: str,
    project: Optional[str],
    context: Optional[dict],
    api_url: Optional[str],
    no_follow: bool,
    file: Optional[str],
) -> None:
    """Run a new workflow.

    Submit a feature request and optionally follow its progress through the multi-agent system.

    Examples:
        hive workflow run "Create a user authentication system"
        hive workflow run -p my-project "Add search functionality"
        hive workflow run -f feature_request.md
        hive workflow run --context '{"language":"python"}' "Create REST API"
    """
    from core.config import get_settings

    try:
        # Read request from file if specified
        if file:
            request = Path(file).read_text().strip()

        # Get API URL
        settings = get_settings()
        base_url = api_url or settings.api_url

        # Run workflow
        asyncio.run(
            run_workflow_async(
                request=request,
                api_url=base_url,
                project_id=project,
                context=context,
                follow=not no_follow,
                json_output=ctx.obj.get("json_output", False),
            )
        )

    except Exception as e:
        handle_error(e, "Failed to run workflow")
        raise click.ClickException(str(e))
