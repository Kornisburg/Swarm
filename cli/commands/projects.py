"""Project context management commands for The Hive CLI."""

import asyncio
import json
from typing import Optional

import click
import httpx
from rich.console import Console
from rich.panel import Panel
from rich.table import Table
from rich.tree import Tree

from cli.utils import JSON, handle_error

console = Console()


async def create_project(
    api_url: str,
    name: str,
    description: Optional[str] = None,
    metadata: Optional[dict] = None,
) -> dict:
    """Create a new project.

    Args:
        api_url: Base API URL
        name: Project name
        description: Project description
        metadata: Additional metadata

    Returns:
        Created project data

    Raises:
        httpx.HTTPError: If API request fails
    """
    async with httpx.AsyncClient(timeout=30.0) as client:
        payload = {"name": name}
        if description:
            payload["description"] = description
        if metadata:
            payload["metadata"] = metadata

        response = await client.post(
            f"{api_url}/api/projects",
            json=payload,
        )
        response.raise_for_status()
        return response.json()


async def list_projects(
    api_url: str,
    limit: int = 50,
    offset: int = 0,
) -> list[dict]:
    """List all projects.

    Args:
        api_url: Base API URL
        limit: Max results
        offset: Pagination offset

    Returns:
        List of projects

    Raises:
        httpx.HTTPError: If API request fails
    """
    async with httpx.AsyncClient(timeout=30.0) as client:
        params = {"limit": limit, "offset": offset}

        response = await client.get(
            f"{api_url}/api/projects",
            params=params,
        )
        response.raise_for_status()
        return response.json().get("projects", [])


async def get_project(api_url: str, project_id: str) -> dict:
    """Get project details.

    Args:
        api_url: Base API URL
        project_id: Project ID

    Returns:
        Project data

    Raises:
        httpx.HTTPError: If API request fails
    """
    async with httpx.AsyncClient(timeout=30.0) as client:
        response = await client.get(
            f"{api_url}/api/projects/{project_id}",
        )
        response.raise_for_status()
        return response.json()


async def get_project_timeline(
    api_url: str,
    project_id: str,
    limit: int = 20,
) -> list[dict]:
    """Get project timeline/workflow history.

    Args:
        api_url: Base API URL
        project_id: Project ID
        limit: Max results

    Returns:
        List of workflow history

    Raises:
        httpx.HTTPError: If API request fails
    """
    async with httpx.AsyncClient(timeout=30.0) as client:
        params = {"limit": limit}

        response = await client.get(
            f"{api_url}/api/projects/{project_id}/timeline",
            params=params,
        )
        response.raise_for_status()
        return response.json().get("workflows", [])


def format_project_table(project: dict) -> Table:
    """Format project details as Rich table.

    Args:
        project: Project data

    Returns:
        Formatted table
    """
    table = Table(show_header=False)
    table.add_column("Property", style="cyan", width=20)
    table.add_column("Value", style="green")

    table.add_row("Project ID", project.get("id", "N/A"))
    table.add_row("Name", project.get("name", "N/A"))
    table.add_row("Description", project.get("description", "N/A")[:50] + "...")

    if "metadata" in project:
        table.add_row("Metadata", json.dumps(project["metadata"], indent=2))

    table.add_row("Created", project.get("created_at", "N/A"))
    table.add_row("Updated", project.get("updated_at", "N/A"))

    return table


def format_projects_table(projects: list[dict]) -> Table:
    """Format projects list as Rich table.

    Args:
        projects: List of project data

    Returns:
        Formatted table
    """
    table = Table(title="Projects")
    table.add_column("ID", style="cyan", width=10)
    table.add_column("Name", style="green", width=30)
    table.add_column("Workflows", style="yellow", width=10)
    table.add_column("Created", style="dim", width=20)

    for project in projects:
        table.add_row(
            project.get("id", "N/A")[:10],
            project.get("name", "N/A"),
            str(project.get("workflow_count", 0)),
            project.get("created_at", "N/A"),
        )

    return table


def format_timeline_tree(workflows: list[dict]) -> Tree:
    """Format project timeline as Rich tree.

    Args:
        workflows: List of workflow history

    Returns:
        Formatted tree
    """
    tree = Tree("[bold blue]Project Timeline[/bold blue]")

    for workflow in workflows:
        status = workflow.get("status", "UNKNOWN")
        status_color = {
            "COMPLETED": "green",
            "RUNNING": "blue",
            "FAILED": "red",
            "PENDING": "yellow",
        }.get(status, "white")

        branch = tree.add(
            f"[{status_color}]{status}[/] "
            f"{workflow.get('created_at', 'N/A')[:19]} "
            f"- {workflow.get('workflow_id', 'N/A')[:10]}"
        )

        branch.add(f"[dim]{workflow.get('input_request', 'N/A')[:60]}...[/dim]")

    return tree


@click.command()
@click.argument("name")
@click.option("--description", "-d", help="Project description")
@click.option("--metadata", "-m", type=JSON, help="Project metadata as JSON")
@click.option("--api-url", help="Override API URL")
@click.pass_context
def create_project_cmd(
    ctx: click.Context,
    name: str,
    description: Optional[str],
    metadata: Optional[dict],
    api_url: Optional[str],
) -> None:
    """Create a new project.

    Create a new project context for grouping related workflows.

    Examples:
        hive project create "My Web App"
        hive project create "API Service" -d "REST API for user management"
        hive project create "Mobile App" -m '{"platform":"iOS","language":"Swift"}'
    """
    from core.config import get_settings

    try:
        settings = get_settings()
        base_url = api_url or settings.api_url

        project = asyncio.run(
            create_project(base_url, name, description, metadata)
        )

        if ctx.obj.get("json_output"):
            console.print_json(json.dumps(project))
            return

        console.print(f"[green]✓[/green] Project created: {project['id']}")
        table = format_project_table(project)
        console.print(table)

    except Exception as e:
        handle_error(e, "Failed to create project")
        raise click.ClickException(str(e))


@click.command(name="list")
@click.option("--limit", "-l", default=50, help="Maximum results")
@click.option("--offset", "-o", default=0, help="Pagination offset")
@click.option("--api-url", help="Override API URL")
@click.pass_context
def list_projects_cmd(
    ctx: click.Context,
    limit: int,
    offset: int,
    api_url: Optional[str],
) -> None:
    """List all projects.

    Display all available projects.

    Examples:
        hive project list
        hive project list -l 10
        hive project list --offset 20
    """
    from core.config import get_settings

    try:
        settings = get_settings()
        base_url = api_url or settings.api_url

        projects = asyncio.run(
            list_projects(base_url, limit, offset)
        )

        if ctx.obj.get("json_output"):
            console.print_json(json.dumps(projects))
            return

        if not projects:
            console.print("[yellow]No projects found[/yellow]")
            return

        table = format_projects_table(projects)
        console.print(table)
        console.print(f"\n[dim]Showing {len(projects)} project(s)[/dim]")

    except Exception as e:
        handle_error(e, "Failed to list projects")
        raise click.ClickException(str(e))


@click.command(name="show")
@click.argument("project_id")
@click.option("--api-url", help="Override API URL")
@click.pass_context
def show_project_cmd(
    ctx: click.Context,
    project_id: str,
    api_url: Optional[str],
) -> None:
    """Show project details.

    Display detailed information about a specific project.

    Examples:
        hive project show abc123
        hive project show my-project-id
    """
    from core.config import get_settings

    try:
        settings = get_settings()
        base_url = api_url or settings.api_url

        project = asyncio.run(get_project(base_url, project_id))

        if ctx.obj.get("json_output"):
            console.print_json(json.dumps(project))
            return

        table = format_project_table(project)
        console.print(table)

    except Exception as e:
        handle_error(e, f"Failed to get project {project_id}")
        raise click.ClickException(str(e))


@click.command(name="timeline")
@click.argument("project_id")
@click.option("--limit", "-l", default=20, help="Maximum workflows to show")
@click.option("--api-url", help="Override API URL")
@click.pass_context
def project_timeline_cmd(
    ctx: click.Context,
    project_id: str,
    limit: int,
    api_url: Optional[str],
) -> None:
    """Show project timeline.

    Display the workflow history for a project.

    Examples:
        hive project timeline abc123
        hive project timeline abc123 -l 50
    """
    from core.config import get_settings

    try:
        settings = get_settings()
        base_url = api_url or settings.api_url

        workflows = asyncio.run(
            get_project_timeline(base_url, project_id, limit)
        )

        if ctx.obj.get("json_output"):
            console.print_json(json.dumps(workflows))
            return

        if not workflows:
            console.print(f"[yellow]No workflow history found for project {project_id}[/yellow]")
            return

        tree = format_timeline_tree(workflows)
        console.print(tree)
        console.print(f"\n[dim]Showing {len(workflows)} workflow(s)[/dim]")

    except Exception as e:
        handle_error(e, f"Failed to get timeline for project {project_id}")
        raise click.ClickException(str(e))
