"""Artifacts command for The Hive CLI."""

import asyncio
import json
from pathlib import Path
from typing import Optional

import click
import httpx
from rich.console import Console
from rich.panel import Panel
from rich.syntax import Syntax
from rich.table import Table
from rich.tree import Tree

from cli.utils import handle_error

console = Console()


async def get_artifacts(
    api_url: str,
    workflow_id: str,
    artifact_type: Optional[str] = None,
) -> list[dict]:
    """Get artifacts from API.

    Args:
        api_url: Base API URL
        workflow_id: Workflow ID
        artifact_type: Filter by artifact type

    Returns:
        List of artifacts

    Raises:
        httpx.HTTPError: If API request fails
    """
    async with httpx.AsyncClient(timeout=30.0) as client:
        params = {}
        if artifact_type:
            params["type"] = artifact_type

        response = await client.get(
            f"{api_url}/api/workflows/{workflow_id}/artifacts",
            params=params,
        )
        response.raise_for_status()
        return response.json().get("artifacts", [])


async def get_artifact_content(
    api_url: str,
    workflow_id: str,
    artifact_id: str,
) -> dict:
    """Get artifact content from API.

    Args:
        api_url: Base API URL
        workflow_id: Workflow ID
        artifact_id: Artifact ID

    Returns:
        Artifact content

    Raises:
        httpx.HTTPError: If API request fails
    """
    async with httpx.AsyncClient(timeout=60.0) as client:
        response = await client.get(
            f"{api_url}/api/workflows/{workflow_id}/artifacts/{artifact_id}",
        )
        response.raise_for_status()
        return response.json()


def get_artifact_color(artifact_type: str) -> str:
    """Get color for artifact type.

    Args:
        artifact_type: Artifact type

    Returns:
        Color name for Rich
    """
    colors = {
        "SPEC": "cyan",
        "DESIGN": "yellow",
        "CODE": "green",
        "TEST": "magenta",
        "REVIEW": "blue",
    }
    return colors.get(artifact_type, "white")


def format_artifacts_table(artifacts: list[dict]) -> Table:
    """Format artifacts as Rich table.

    Args:
        artifacts: List of artifact data

    Returns:
        Formatted table
    """
    table = Table(title="Workflow Artifacts")
    table.add_column("ID", style="cyan", width=10)
    table.add_column("Type", style="yellow", width=10)
    table.add_column("Version", style="magenta", width=8)
    table.add_column("Created", style="dim", width=20)

    for artifact in artifacts:
        table.add_row(
            artifact.get("id", "N/A")[:10],
            f"[{get_artifact_color(artifact.get('artifact_type', ''))}]{artifact.get('artifact_type', 'N/A')}[/]",
            str(artifact.get("version", "1")),
            artifact.get("created_at", "N/A"),
        )

    return table


def format_artifact_tree(artifacts: list[dict]) -> Tree:
    """Format artifacts as Rich tree grouped by type.

    Args:
        artifacts: List of artifact data

    Returns:
        Formatted tree
    """
    tree = Tree("[bold blue]Artifacts[/bold blue]")

    # Group by type
    by_type: dict[str, list[dict]] = {}
    for artifact in artifacts:
        artifact_type = artifact.get("artifact_type", "UNKNOWN")
        if artifact_type not in by_type:
            by_type[artifact_type] = []
        by_type[artifact_type].append(artifact)

    # Build tree
    for artifact_type, items in sorted(by_type.items()):
        type_branch = tree.add(f"[{get_artifact_color(artifact_type)}]{artifact_type}[/]")
        for item in items:
            type_branch.add(
                f"[dim]{item.get('id', 'N/A')[:10]}[/dim] "
                f"v{item.get('version', '1')} - {item.get('created_at', 'N/A')}"
            )

    return tree


def display_artifact_content(artifact: dict, output_format: str = "pretty") -> None:
    """Display artifact content in various formats.

    Args:
        artifact: Artifact data with content
        output_format: Output format (pretty, json, raw)
    """
    content = artifact.get("content", {})
    artifact_type = artifact.get("artifact_type", "UNKNOWN")

    if output_format == "json":
        console.print_json(json.dumps(content))
    elif output_format == "raw":
        console.print(json.dumps(content, indent=2))
    else:
        # Pretty format
        panel_title = f"[bold blue]{artifact_type} - v{artifact.get('version', '1')}[/bold blue]"

        if artifact_type == "CODE":
            # Display as code with syntax highlighting
            code = content.get("code", "")
            language = content.get("language", "python")
            syntax = Syntax(code, language, theme="monokai", line_numbers=True)
            panel = Panel(syntax, title=panel_title, border_style="green")
            console.print(panel)

            # Display other metadata
            if "files" in content:
                files_table = Table(title="Generated Files")
                files_table.add_column("File Path", style="cyan")
                files_table.add_column("Size", style="green")
                for file_info in content["files"]:
                    files_table.add_row(
                        file_info.get("path", "N/A"),
                        str(file_info.get("size", 0)),
                    )
                console.print(files_table)

        elif artifact_type == "SPEC":
            # Display specification
            spec_panel = Panel(
                f"[bold]Title:[/bold] {content.get('title', 'N/A')}\n\n"
                f"[bold]Description:[/bold]\n{content.get('description', 'N/A')}\n\n"
                f"[bold]Requirements:[/bold]\n{json.dumps(content.get('requirements', []), indent=2)}\n\n"
                f"[bold]Acceptance Criteria:[/bold]\n{json.dumps(content.get('acceptance_criteria', []), indent=2)}",
                title=panel_title,
                border_style="cyan",
            )
            console.print(spec_panel)

        elif artifact_type == "DESIGN":
            # Display design
            design_text = f"[bold]Architecture:[/bold]\n{json.dumps(content.get('architecture', {}), indent=2)}\n\n"

            if "modules" in content:
                design_text += f"[bold]Modules:[/bold]\n"
                for module in content["modules"]:
                    design_text += f"  - {module.get('name', 'N/A')}: {module.get('purpose', 'N/A')}\n"

            if "data_flow" in content:
                design_text += f"\n[bold]Data Flow:[/bold]\n{json.dumps(content['data_flow'], indent=2)}\n"

            panel = Panel(design_text, title=panel_title, border_style="yellow")
            console.print(panel)

        elif artifact_type == "TEST":
            # Display test suite
            test_text = f"[bold]Test Cases:[/bold] {len(content.get('test_cases', []))}\n\n"

            for i, test_case in enumerate(content.get("test_cases", []), 1):
                test_text += f"[cyan]Test {i}:[/cyan] {test_case.get('name', 'N/A')}\n"
                test_text += f"  [dim]{test_case.get('description', 'N/A')}[/dim]\n"

            panel = Panel(test_text, title=panel_title, border_style="magenta")
            console.print(panel)

        elif artifact_type == "REVIEW":
            # Display review report
            review_text = f"[bold]Quality Score:[/bold] {content.get('quality_score', 'N/A')}/100\n\n"
            review_text += f"[bold]Issues Found:[/bold] {len(content.get('issues', []))}\n\n"

            for issue in content.get("issues", [])[:5]:
                severity = issue.get("severity", "INFO")
                color = {"ERROR": "red", "WARNING": "yellow", "INFO": "blue"}.get(severity, "white")
                review_text += f"[{color}]{severity}:[/{color}] {issue.get('message', 'N/A')}\n"

            panel = Panel(review_text, title=panel_title, border_style="blue")
            console.print(panel)

        else:
            # Generic display
            panel = Panel(
                json.dumps(content, indent=2),
                title=panel_title,
                border_style="white",
            )
            console.print(panel)


@click.command()
@click.argument("workflow_id")
@click.option("--type", "-t", help="Filter by artifact type")
@click.option("--artifact-id", "-a", help="Get specific artifact content")
@click.option("--output", "-o", type=click.Choice(["pretty", "json", "raw"]), default="pretty", help="Output format")
@click.option("--save", "-s", type=click.Path(), help="Save artifact to file")
@click.option("--api-url", help="Override API URL")
@click.pass_context
def artifacts_cmd(
    ctx: click.Context,
    workflow_id: str,
    type: Optional[str],
    artifact_id: Optional[str],
    output: str,
    save: Optional[str],
    api_url: Optional[str],
) -> None:
    """Get workflow artifacts.

    Retrieve and display artifacts from a workflow.

    Examples:
        hive workflow artifacts abc123
        hive workflow artifacts abc123 --type CODE
        hive workflow artifacts abc123 -a def456 --output json
        hive workflow artifacts abc123 -t SPEC --save spec.json
    """
    from core.config import get_settings

    try:
        settings = get_settings()
        base_url = api_url or settings.api_url

        if artifact_id:
            # Get specific artifact content
            artifact = asyncio.run(get_artifact_content(base_url, workflow_id, artifact_id))

            if ctx.obj.get("json_output") or output == "json":
                console.print_json(json.dumps(artifact))

            if save:
                with open(save, "w") as f:
                    json.dump(artifact, f, indent=2)
                console.print(f"[green]✓[/green] Artifact saved to {save}")
            else:
                display_artifact_content(artifact, output)
        else:
            # List all artifacts
            artifacts = asyncio.run(get_artifacts(base_url, workflow_id, type))

            if ctx.obj.get("json_output"):
                console.print_json(json.dumps(artifacts))
                return

            if not artifacts:
                console.print("[yellow]No artifacts found[/yellow]")
                return

            tree = format_artifact_tree(artifacts)
            console.print(tree)
            console.print(f"\n[dim]Use --artifact-id to view specific artifact content[/dim]")

            # Also show table
            table = format_artifacts_table(artifacts)
            console.print(table)

            if save:
                with open(save, "w") as f:
                    json.dump(artifacts, f, indent=2)
                console.print(f"\n[green]✓[/green] Artifacts saved to {save}")

    except Exception as e:
        handle_error(e, f"Failed to get artifacts for workflow {workflow_id}")
        raise click.ClickException(str(e))
