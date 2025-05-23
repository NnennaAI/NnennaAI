"""CLI commands package."""

from cli.commands.init import init_command
from cli.commands.ingest import ingest_command
from cli.commands.run import run_command
from cli.commands.score import score_command
from cli.commands.config import config_command
from cli.commands.dashboard import dashboard_command

__all__ = [
    "init_command",
    "ingest_command", 
    "run_command",
    "score_command",
    "config_command",
    "dashboard_command"
]