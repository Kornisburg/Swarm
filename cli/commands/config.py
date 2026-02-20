"""Configuration management commands for The Hive CLI."""

import json
from pathlib import Path
from typing import Optional

import click
from dotenv import load_dotenv, set_key, dotenv_values
from rich.console import Console
from rich.panel import Panel
from rich.table import Table

from cli.utils import handle_error

console = Console()


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


def get_config_file_path() -> Path:
    """Get the path to the configuration file.

    Returns:
        Path to config file
    """
    # Check common locations
    home = Path.home()
    config_dir = home / ".config" / "hive"

    # Try to find existing config
    for path in [config_dir / "config.json", Path(".hive.config.json"), Path(".env")]:
        if path.exists():
            return path

    # Return default config location
    config_dir.mkdir(parents=True, exist_ok=True)
    return config_dir / "config.json"


def show_current_settings() -> dict:
    """Show current configuration settings.

    Returns:
        Dictionary of current settings
    """
    from core.config import get_settings

    settings = get_settings()

    return {
        "api_url": settings.api_url,
        "llm_provider": settings.llm_provider,
        "llm_model": settings.llm_model,
        "llm_api_key": "***" if settings.llm_api_key else "Not set",
        "redis_url": settings.redis_url,
        "postgres_url": settings.postgres_url.replace(settings.postgres_url.split(":")[2] if len(settings.postgres_url.split(":")) > 2 else "", "***") if settings.postgres_url else "Not set",
        "chroma_path": settings.chroma_path,
    }


def format_config_table(settings: dict) -> Table:
    """Format configuration as Rich table.

    Args:
        settings: Configuration dictionary

    Returns:
        Formatted table
    """
    table = Table(title="The Hive Configuration")
    table.add_column("Setting", style="cyan", width=20)
    table.add_column("Value", style="green")

    for key, value in settings.items():
        table.add_row(key.replace("_", " ").title(), str(value))

    return table


@click.command()
@click.option("--json", "json_output", is_flag=True, help="Output as JSON")
@click.pass_context
def show_config_cmd(ctx: click.Context, json_output: bool) -> None:
    """Show current configuration.

    Display all current configuration settings.

    Examples:
        hive config show
        hive config show --json
    """
    try:
        settings = show_current_settings()

        if json_output or ctx.obj.get("json_output"):
            console.print_json(json.dumps(settings, indent=2))
        else:
            table = format_config_table(settings)
            console.print(table)

            # Show config file location
            config_file = get_config_file_path()
            console.print(f"\n[dim]Config file: {config_file}[/dim]")

    except Exception as e:
        handle_error(e, "Failed to show configuration")
        raise click.ClickException(str(e))


@click.command()
@click.argument("key")
@click.argument("value")
@click.option("--env-file", "-e", type=click.Path(), help="Path to .env file")
@click.pass_context
def set_config_cmd(
    ctx: click.Context,
    key: str,
    value: str,
    env_file: Optional[str],
) -> None:
    """Set a configuration value.

    Update a configuration setting. Values are stored in the .env file.

    Examples:
        hive config set llm_provider anthropic
        hive config set llm_api_key sk-ant-xxx
        hive config set llm_model claude-3-opus-20240229

    Available keys:
        - api_url: Base URL for The Hive API
        - llm_provider: LLM provider (openai, anthropic)
        - llm_model: Model name to use
        - llm_api_key: API key for LLM provider
        - redis_url: Redis connection URL
        - postgres_url: PostgreSQL connection URL
        - chroma_path: Path to ChromaDB storage
    """
    try:
        # Determine which .env file to use
        if env_file:
            env_path = Path(env_file)
        else:
            # Use .env in current directory or default to creating one
            env_path = Path(".env")

        # Ensure .env file exists
        if not env_path.exists():
            env_path.touch()
            console.print(f"[yellow]Created new .env file at {env_path}[/yellow]")

        # Set the value
        set_key(env_path, key.upper(), value)

        console.print(f"[green]✓[/green] Set {key}={value}")
        console.print(f"[dim]Updated: {env_path}[/dim]")

        # Reload and show updated settings
        load_dotenv(env_path)

        settings = show_current_settings()
        if key in settings or key.upper() in settings:
            console.print(f"\n[dim]New value: {settings.get(key.lower(), settings.get(key.upper(), 'N/A'))}[/dim]")

    except Exception as e:
        handle_error(e, f"Failed to set configuration {key}")
        raise click.ClickException(str(e))


@click.command(name="init")
@click.option("--api-url", help="Base URL for The Hive API")
@click.option("--llm-provider", type=click.Choice(["openai", "anthropic"]), help="LLM provider")
@click.option("--llm-model", help="LLM model to use")
@click.option("--llm-api-key", help="API key for LLM provider")
@click.option("--env-file", type=click.Path(), help="Path to .env file")
def init_config(
    api_url: Optional[str],
    llm_provider: Optional[str],
    llm_model: Optional[str],
    llm_api_key: Optional[str],
    env_file: Optional[str],
) -> None:
    """Initialize configuration.

    Create or update the configuration with interactive prompts.

    Examples:
        hive config init
        hive config init --api-url http://localhost:8000
        hive config init --llm-provider anthropic --llm-api-key sk-ant-xxx
    """
    try:
        print_banner()

        # Determine .env file path
        if env_file:
            env_path = Path(env_file)
        else:
            env_path = Path(".env")

        # Ensure .env file exists
        if not env_path.exists():
            env_path.touch()

        console.print("\n[cyan]Setting up The Hive configuration...[/cyan]\n")

        # Prompt for values if not provided
        if not api_url:
            api_url = click.prompt("API URL", default="http://localhost:8000")

        if not llm_provider:
            llm_provider = click.prompt(
                "LLM Provider",
                type=click.Choice(["openai", "anthropic"]),
                default="anthropic",
            )

        if not llm_model:
            default_model = "claude-3-opus-20240229" if llm_provider == "anthropic" else "gpt-4-turbo-preview"
            llm_model = click.prompt("LLM Model", default=default_model)

        if not llm_api_key:
            llm_api_key = click.prompt("LLM API Key", hide_input=True)

        # Set values
        set_key(env_path, "API_URL", api_url)
        set_key(env_path, "LLM_PROVIDER", llm_provider)
        set_key(env_path, "LLM_MODEL", llm_model)
        set_key(env_path, "LLM_API_KEY", llm_api_key)

        console.print("\n[green]✓ Configuration saved successfully![/green]\n")

        # Show configuration
        settings = show_current_settings()
        table = format_config_table(settings)
        console.print(table)

        console.print(f"\n[dim]Configuration file: {env_path}[/dim]")
        console.print("[dim]You can now run: hive workflow run \"your feature request\"[/dim]\n")

    except Exception as e:
        handle_error(e, "Failed to initialize configuration")
        raise click.ClickException(str(e))


# Note: init_config command is registered in cli/main.py
