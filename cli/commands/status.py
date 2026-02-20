"""Workflow status command for The Hive CLI."""

import asyncio
import json
from typing import Optional

import click
import httpx
from rich.console import Console
from rich.panel import Panel
from rich.table import Table

from cli.utils import handle_error

console = Console()


async def get_workflow_status(api_url: str, workflow_id: str) -> dict:
    """Get workflow status from API.

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


async def list_workflows(
    api_url: str,
    status_filter: Optional[str] = None,
    project_id: Optional[str] = None,
    limit: int = 20,
    offset: int = 0,
) -> list:
    """List workflows from API.

    Args:
        api_url: Base API URL
        status_filter: Filter by status
        project_id: Filter by project
        limit: Max results
        offset: Pagination offset

    Returns:
        List of workflows

    Raises:
        httpx.HTTPError: If API request fails
    """
    async with httpx.AsyncClient(timeout=30.0) as client:
        params = {"limit": limit, "offset": offset}
        if status_filter:
            params["status"] = status_filter
        if project_id:
            params["project_id"] = project_id

        response = await client.get(
            f"{api_url}/api/workflows",
            params=params,
        )
        response.raise_for_status()
        return response.json().get("workflows", [])


def get_status_color(status: str) -> str:
    """Get color for workflow status.

    Args:
        status: Workflow status

    Returns:
        Color name for Rich
    """
    colors = {
        "PENDING": "yellow",
        "RUNNING": "blue",
        "COMPLETED": "green",
        "FAILED": "red",
        "CANCELLED": "magenta",
    }
    return colors.get(status, "white")


def format_status_table(workflow: dict) -> Table:
    """Format workflow status as Rich table.

    Args:
        workflow: Workflow data

    Returns:
        Formatted table
    """
    table = Table(show_header=True, header_style="bold magenta")
    table.add_column("Property", style="cyan", width=20)
    table.add_column("Value", style="green")

    # Basic info
    table.add_row("Workflow ID", workflow.get("workflow_id", "N/A"))
    table.add_row("Status", f"[{get_status_color(workflow.get('status', ''))}]{workflow.get('status', 'N/A')}[/]")
    table.add_row("Input Request", workflow.get("input_request", "N/A")[:50] + "...")

    # Stage information
    table.add_row("Current Stage", workflow.get("current_stage", "N/A"))
    stage_history = workflow.get("stage_history", [])
    if stage_history:
        table.add_row("Stage Progress", " → ".join(stage_history))

    # Timestamps
    if "created_at" in workflow:
        table.add_row("Created", workflow["created_at"])
    if "updated_at" in workflow:
        table.add_row("Updated", workflow["updated_at"])

    # Error if present
    error_message = workflow.get("error_message")
    if error_message:
        table.add_row("Error", f"[red]{error_message}[/red]")

    # Project if present
    if "project_id" in workflow:
        table.add_row("Project", workflow["project_id"])

    return table


def format_workflows_table(workflows: list[dict]) -> Table:
    """Format workflows list as Rich table.

    Args:
        workflows: List of workflow data

    Returns:
        Formatted table
    """
    table = Table(title="Workflows")
    table.add_column("ID", style="cyan", width=10)
    table.add_column("Status", style="green", width=12)
    table.add_column("Current Stage", style="yellow", width=20)
    table.add_column("Request", style="white", width=30)
    table.add_column("Created", style="dim", width=20)

    for workflow in workflows:
        status = workflow.get("status", "N/A")
        request = workflow.get("input_request", "N/A")[:28]

        table.add_row(
            workflow.get("workflow_id", "N/A")[:10],
            f"[{get_status_color(status)}]{status}[/]",
            workflow.get("current_stage", "N/A"),
            request + "...",
            workflow.get("created_at", "N/A"),
        )

    return table


@click.command()
@click.argument("workflow_id")
@click.option("--api-url", help="Override API URL")
@click.option("--watch", "-w", is_flag=True, help="Watch status updates")
@click.option("--interval", default=2, help="Watch interval in seconds")
@click.pass_context
def status_cmd(
    ctx: click.Context,
    workflow_id: str,
    api_url: Optional[str],
    watch: bool,
    interval: int,
) -> None:
    """Show workflow status.

    Display detailed status for a specific workflow.

    Examples:
        hive workflow status abc123
        hive workflow status abc123 --watch
        hive workflow status abc123 -w --interval 5
    """
    from core.config import get_settings

    try:
        settings = get_settings()
        base_url = api_url or settings.api_url

        if ctx.obj.get("json_output"):
            status_data = asyncio.run(get_workflow_status(base_url, workflow_id))
            console.print_json(json.dumps(status_data))
            return

        if watch:
            from rich.live import Live

            async def watch_workflow():
                with Live(console=console, refresh_per_second=1) as live:
                    while True:
                        status_data = await get_workflow_status(base_url, workflow_id)
                        table = format_status_table(status_data)
                        panel = Panel(table, title="[bold blue]Workflow Status[/bold blue]")
                        live.update(panel)

                        if status_data.get("status") in ("COMPLETED", "FAILED", "CANCELLED"):
                            break

                        await asyncio.sleep(interval)

            asyncio.run(watch_workflow())
        else:
            status_data = asyncio.run(get_workflow_status(base_url, workflow_id))
            table = format_status_table(status_data)
            console.print(table)

    except Exception as e:
        handle_error(e, f"Failed to get status for workflow {workflow_id}")
        raise click.ClickException(str(e))


@click.command(name="list")
@click.option("--status", "-s", help="Filter by status")
@click.option("--project", "-p", help="Filter by project")
@click.option("--limit", "-l", default=20, help="Maximum results")
@click.option("--offset", "-o", default=0, help="Pagination offset")
@click.option("--api-url", help="Override API URL")
@click.pass_context
def list_cmd(
    ctx: click.Context,
    status: Optional[str],
    project: Optional[str],
    limit: int,
    offset: int,
    api_url: Optional[str],
) -> None:
    """List workflows.

    List all workflows with optional filtering.

    Examples:
        hive workflow list
        hive workflow list --status RUNNING
        hive workflow list -p my-project -l 10
        hive workflow list -s COMPLETED --offset 20
    """
    from core.config import get_settings

    try:
        settings = get_settings()
        base_url = api_url or settings.api_url

        workflows = asyncio.run(
            list_workflows(
                api_url=base_url,
                status_filter=status,
                project_id=project,
                limit=limit,
                offset=offset,
            )
        )

        if ctx.obj.get("json_output"):
            console.print_json(json.dumps(workflows))
            return

        if not workflows:
            console.print("[yellow]No workflows found[/yellow]")
            return

        table = format_workflows_table(workflows)
        console.print(table)
        console.print(f"\n[dim]Showing {len(workflows)} workflow(s)[/dim]")

    except Exception as e:
        handle_error(e, "Failed to list workflows")
        raise click.ClickException(str(e))
