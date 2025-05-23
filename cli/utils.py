"""CLI utility functions."""

import logging
import sys
import typer
from pathlib import Path
from typing import Optional, Dict, Any
import json
import yaml
from rich.console import Console
from rich.logging import RichHandler
from rich.table import Table
from rich.progress import Progress, SpinnerColumn, TextColumn

console = Console()

# Version info
VERSION = "0.1.0"
AUTHOR = "Nnenna Ndukwe"
GITHUB_URL = "https://github.com/NnennaAI/NnennaAI"


def setup_logging(level: str = "INFO") -> None:
    """Configure logging with Rich handler."""
    # Map string levels to logging constants
    level_map = {
        "TRACE": logging.DEBUG - 5,  # Custom trace level
        "DEBUG": logging.DEBUG,
        "INFO": logging.INFO,
        "WARNING": logging.WARNING,
        "ERROR": logging.ERROR
    }
    
    # Add custom TRACE level if it doesn't exist
    if not hasattr(logging, 'TRACE'):
        logging.addLevelName(level_map["TRACE"], "TRACE")
    
    # Configure root logger
    logging.basicConfig(
        level=level_map.get(level, logging.INFO),
        format="%(message)s",
        datefmt="[%X]",
        handlers=[
            RichHandler(
                console=console,
                rich_tracebacks=True,
                markup=True,
                show_path=level == "TRACE"
            )
        ]
    )


def print_version() -> None:
    """Print version information."""
    console.print(f"[bold cyan]NnennaAI[/bold cyan] v{VERSION}")
    console.print(f"Created by {AUTHOR}")
    console.print(f"🔗 {GITHUB_URL}")


def load_config(path: Optional[Path] = None) -> Dict[str, Any]:
    """Load configuration from YAML file."""
    # Default search paths
    search_paths = [
        Path.cwd() / "config.yaml",
        Path.cwd() / ".nai.yaml",
        Path.home() / ".nai.yaml"
    ]
    
    if path:
        search_paths.insert(0, path)
    
    for config_path in search_paths:
        if config_path.exists():
            with open(config_path) as f:
                return yaml.safe_load(f) or {}
    
    return {}


def save_config(config: Dict[str, Any], path: Path) -> None:
    """Save configuration to YAML file."""
    path.parent.mkdir(parents=True, exist_ok=True)
    
    with open(path, 'w') as f:
        yaml.dump(config, f, default_flow_style=False, sort_keys=False)


def print_success(message: str) -> None:
    """Print success message."""
    console.print(f"[bold green]✅ {message}[/bold green]")


def print_error(message: str) -> None:
    """Print error message."""
    console.print(f"[bold red]❌ {message}[/bold red]")


def print_warning(message: str) -> None:
    """Print warning message."""
    console.print(f"[bold yellow]⚠️  {message}[/bold yellow]")


def print_info(message: str) -> None:
    """Print info message."""
    console.print(f"[bold blue]ℹ️  {message}[/bold blue]")


def confirm(message: str, default: bool = False) -> bool:
    """Ask for user confirmation."""
    return typer.confirm(message, default=default)


def create_table(title: str, columns: list) -> Table:
    """Create a Rich table with consistent styling."""
    table = Table(title=title, show_header=True, header_style="bold cyan")
    
    for col in columns:
        table.add_column(col)
    
    return table


def format_duration(seconds: float) -> str:
    """Format duration in human-readable format."""
    if seconds < 1:
        return f"{seconds*1000:.0f}ms"
    elif seconds < 60:
        return f"{seconds:.1f}s"
    else:
        minutes = int(seconds // 60)
        remaining = seconds % 60
        return f"{minutes}m {remaining:.0f}s"


def format_cost(cost: float) -> str:
    """Format cost in USD."""
    if cost < 0.01:
        return f"${cost:.4f}"
    else:
        return f"${cost:.2f}"


def read_run_result(run_id: str, run_dir: Path = Path(".nai/runs")) -> Optional[Dict[str, Any]]:
    """Read a saved run result."""
    run_file = run_dir / f"run_{run_id}.json"
    
    if not run_file.exists():
        # Try to find by partial match
        matches = list(run_dir.glob(f"run_{run_id}*.json"))
        if matches:
            run_file = matches[0]
        else:
            return None
    
    with open(run_file) as f:
        return json.load(f)


def list_runs(run_dir: Path = Path(".nai/runs")) -> list:
    """List all saved runs."""
    if not run_dir.exists():
        return []
    
    runs = []
    for run_file in sorted(run_dir.glob("run_*.json"), key=lambda p: p.stat().st_mtime, reverse=True):
        with open(run_file) as f:
            data = json.load(f)
            runs.append({
                "run_id": data["run_id"],
                "query": data["query"],
                "timestamp": data["timestamp"],
                "duration": data.get("duration_seconds", 0)
            })
    
    return runs


class Spinner:
    """Context manager for showing a spinner during long operations."""
    
    def __init__(self, message: str):
        self.message = message
        self.progress = Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            console=console
        )
        self.task = None
    
    def __enter__(self):
        self.progress.__enter__()
        self.task = self.progress.add_task(self.message, total=None)
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        if self.task is not None:
            self.progress.remove_task(self.task)
        self.progress.__exit__(exc_type, exc_val, exc_tb)
    
    def update(self, message: str):
        """Update spinner message."""
        if self.task is not None:
            self.progress.update(self.task, description=message)


# Export commonly used items
__all__ = [
    "console",
    "setup_logging",
    "print_version",
    "load_config",
    "save_config",
    "print_success",
    "print_error",
    "print_warning",
    "print_info",
    "confirm",
    "create_table",
    "format_duration",
    "format_cost",
    "read_run_result",
    "list_runs",
    "Spinner",
    "VERSION"
]