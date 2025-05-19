# cli/commands/scan.py
import typer
from context.context_docs import show_scan_output

app = typer.Typer(help="🔐 Scan files or directories for PII and redact if needed")

@app.command()
def pii(
    path: str = typer.Argument(..., help="Path to file or directory to scan for PII"),
    mode: str = typer.Option("report", help="Mode to use: report or redact"),
    output: str = typer.Option("./cleaned", help="Directory to save redacted files (if in redact mode)"),
    format: str = typer.Option("md", help="Output report format: md or json")
):
    """
    Scan a directory or file for PII and optionally redact.
    """
    typer.echo(f"🔍 Scanning path: {path}")
    typer.echo(f"🔧 Mode: {mode} | Output: {output} | Format: {format}\n")

    # Simulated scan logic
    typer.echo("⏳ Running PII scan...\n")

    # Show contextual documentation
    show_scan_output()
