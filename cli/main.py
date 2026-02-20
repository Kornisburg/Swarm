"""The Hive CLI - Command-line interface for The Hive Multi-Agent Engineering System."""

import json
from pathlib import Path
from typing import Optional

import click
from dotenv import load_dotenv
from rich.console import Console
from rich.panel import Panel
from rich.table import Table

from core.config import get_settings

console = Console()


def load_environment(env_file: Optional[str] = None) -> None:
    """Load environment variables from .env file.

    Args:
        env_file: Path to .env file
    """
    if env_file:
        load_dotenv(env_file)
    else:
        # Try default locations
        for path in [".env", ".env.local", "~/.config/hive/.env"]:
            env_path = Path(path).expanduser()
            if env_path.exists():
                load_dotenv(env_path)
                break


def print_banner() -> None:
    """Print The Hive CLI banner."""
    banner = """
    ================================================================
                    The Hive CLI v0.1.0
            Multi-Agent Engineering System
        AI-powered coding workflows with LangGraph
    ================================================================
    """
    console.print(banner, style="bold cyan")


@click.group()
@click.option("--env", type=click.Path(exists=True), help="Path to .env file")
@click.option("--json", is_flag=True, help="Output results as JSON")
@click.pass_context
def cli(ctx: click.Context, env: Optional[str], json: bool) -> None:
    """The Hive CLI - Multi-Agent Engineering System.

    Submit workflows, query status, and retrieve artifacts from The Hive.
    """
    # Load environment variables
    load_environment(env)

    # Store JSON flag in context for subcommands
    ctx.ensure_object(dict)
    ctx.obj["json_output"] = json

    # Print banner unless --json flag
    if not json:
        print_banner()


@cli.command()
@click.pass_context
def version(ctx: click.Context) -> None:
    """Show CLI version and configuration."""
    settings = get_settings()

    if ctx.obj.get("json_output"):
        data = {
            "version": "0.1.0",
            "api_host": settings.api_host,
            "api_port": settings.api_port,
            "llm_provider": settings.llm_provider,
        }
        console.print_json(json.dumps(data))
    else:
        table = Table(title="The Hive Configuration")
        table.add_column("Setting", style="cyan")
        table.add_column("Value", style="green")

        table.add_row("Version", "0.1.0")
        table.add_row("API Host", settings.api_host)
        table.add_row("API Port", str(settings.api_port))
        table.add_row("LLM Provider", settings.llm_provider)

        console.print(table)


@cli.group()
def workflow() -> None:
    """Workflow management commands."""
    pass


@cli.group()
def project() -> None:
    """Project context management commands."""
    pass


@cli.group()
def config() -> None:
    """Configuration management commands."""
    pass


# Import command groups
try:
    from cli.commands.run import run_cmd
    from cli.commands.status import status_cmd, list_cmd
    from cli.commands.artifacts import artifacts_cmd
    from cli.commands.projects import (
        create_project_cmd,
        list_projects_cmd,
        show_project_cmd,
        project_timeline_cmd,
    )
    from cli.commands.config import show_config_cmd, set_config_cmd, init_config

    # Register workflow commands
    workflow.add_command(run_cmd, name="run")
    workflow.add_command(status_cmd, name="status")
    workflow.add_command(list_cmd, name="list")

    # Register artifact commands
    workflow.add_command(artifacts_cmd, name="artifacts")

    # Register project commands
    project.add_command(create_project_cmd, name="create")
    project.add_command(list_projects_cmd, name="list")
    project.add_command(show_project_cmd, name="show")
    project.add_command(project_timeline_cmd, name="timeline")

    # Register config commands
    config.add_command(show_config_cmd, name="show")
    config.add_command(set_config_cmd, name="set")
    config.add_command(init_config, name="init")

except ImportError:
    # Commands not yet implemented
    pass


if __name__ == "__main__":
    cli()
