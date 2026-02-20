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
        "api_host": settings.api_host,
        "api_port": settings.api_port,
        "llm_provider": settings.llm_provider,
        "openai_api_key": "***" if settings.openai_api_key else "Not set",
        "anthropic_api_key": "***" if settings.anthropic_api_key else "Not set",
        "postgres_host": settings.postgres_host,
        "postgres_port": settings.postgres_port,
        "postgres_db": settings.postgres_db,
        "redis_host": settings.redis_host,
        "redis_port": settings.redis_port,
        "chroma_host": settings.chroma_host,
        "chroma_port": settings.chroma_port,
        "chroma_persist_dir": settings.chroma_persist_dir,
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
        hive config set openai_api_key sk-xxx
        hive config set anthropic_api_key sk-ant-xxx
        hive config set api_host localhost
        hive config set api_port 8000

    Available keys:
        - llm_provider: LLM provider (openai, anthropic)
        - openai_api_key: API key for OpenAI
        - anthropic_api_key: API key for Anthropic
        - api_host: API host address
        - api_port: API port number
        - postgres_host: PostgreSQL host
        - postgres_port: PostgreSQL port
        - redis_host: Redis host
        - redis_port: Redis port
        - chroma_host: ChromaDB host
        - chroma_port: ChromaDB port
        - chroma_persist_dir: ChromaDB storage path
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
@click.option("--api-host", help="API host address")
@click.option("--api-port", type=int, help="API port number")
@click.option("--llm-provider", type=click.Choice(["openai", "anthropic"]), help="LLM provider")
@click.option("--openai-api-key", help="OpenAI API key")
@click.option("--anthropic-api-key", help="Anthropic API key")
@click.option("--env-file", type=click.Path(), help="Path to .env file")
def init_config(
    api_host: Optional[str],
    api_port: Optional[int],
    llm_provider: Optional[str],
    openai_api_key: Optional[str],
    anthropic_api_key: Optional[str],
    env_file: Optional[str],
) -> None:
    """Initialize configuration.

    Create or update the configuration with interactive prompts.

    Examples:
        hive config init
        hive config init --api-host localhost --api-port 8000
        hive config init --llm-provider anthropic --anthropic-api-key sk-ant-xxx
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
        if not api_host:
            api_host = click.prompt("API Host", default="0.0.0.0")

        if not api_port:
            api_port = click.prompt("API Port", default=8000, type=int)

        if not llm_provider:
            llm_provider = click.prompt(
                "LLM Provider",
                type=click.Choice(["openai", "anthropic"]),
                default="anthropic",
            )

        if llm_provider == "openai" and not openai_api_key:
            openai_api_key = click.prompt("OpenAI API Key", hide_input=True)
        elif llm_provider == "anthropic" and not anthropic_api_key:
            anthropic_api_key = click.prompt("Anthropic API Key", hide_input=True)

        # Set values
        set_key(env_path, "API_HOST", api_host)
        set_key(env_path, "API_PORT", str(api_port))
        set_key(env_path, "LLM_PROVIDER", llm_provider)
        if openai_api_key:
            set_key(env_path, "OPENAI_API_KEY", openai_api_key)
        if anthropic_api_key:
            set_key(env_path, "ANTHROPIC_API_KEY", anthropic_api_key)

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
