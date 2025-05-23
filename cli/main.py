#!/usr/bin/env python3
"""NnennaAI CLI - The developer-first GenAI framework."""

import typer
from rich.console import Console
from rich.panel import Panel
from pathlib import Path
import sys

# Import commands
from cli.commands.init import init_command
from cli.commands.ingest import ingest_command
from cli.commands.run import run_command
from cli.commands.score import score_command
from cli.commands.config import config_command
from cli.commands.dashboard import dashboard_command
from cli.utils import setup_logging, print_version

# Initialize Typer app with custom help
app = typer.Typer(
    name="nai",
    help="🧠 NnennaAI - Build GenAI systems with intention, evaluation, and scale.",
    add_completion=False,
    rich_markup_mode="rich",
    pretty_exceptions_show_locals=False,
    context_settings={"help_option_names": ["-h", "--help"]}
)

console = Console()

# Register subcommands
app.command("init")(init_command)
app.command("ingest")(ingest_command)
app.command("run")(run_command)
app.command("score")(score_command)
app.command("config")(config_command)
app.command("dashboard")(dashboard_command)


@app.command("version")
def version_command():
    """Show NnennaAI version."""
    print_version()


@app.callback()
def main(
    ctx: typer.Context,
    verbose: bool = typer.Option(False, "--verbose", "-v", help="Enable verbose logging"),
    trace: bool = typer.Option(False, "--trace", help="Enable trace logging for debugging")
):
    """
    NnennaAI CLI - Build evaluated GenAI pipelines in minutes.
    
    Start with 'nai init' to create a new project.
    """
    # Setup logging based on verbosity
    if trace:
        setup_logging(level="TRACE")
    elif verbose:
        setup_logging(level="DEBUG")
    else:
        setup_logging(level="INFO")
    
    # Show welcome message only for root command
    if ctx.invoked_subcommand is None:
        panel = Panel.fit(
            "[bold cyan]Welcome to NnennaAI![/bold cyan]\n\n"
            "🧠 Build GenAI systems with intention, evaluation, and scale.\n\n"
            "Get started with: [bold green]nai init my-project[/bold green]\n"
            "Need help? Run: [bold yellow]nai --help[/bold yellow]",
            border_style="cyan"
        )
        console.print(panel)


if __name__ == "__main__":
    app()
