# cli/commands/assess.py
import typer
from context.context_docs import show_assess_output

app = typer.Typer(help="🧪 Assess the quality of GenAI output")

@app.command()
def file(
    filepath: str = typer.Argument(..., help="Path to the output JSON file to assess"),
    metrics: list[str] = typer.Option(["faithfulness", "completeness"], help="Metrics to use for assessment"),
    engine: str = typer.Option("ragas", help="Evaluation engine (ragas or galileo)")
):
    """
    Assess the output of a GenAI pipeline.
    """
    typer.echo(f"📂 Loading file: {filepath}")
    typer.echo(f"📊 Metrics: {', '.join(metrics)}")
    typer.echo(f"⚙️ Engine: {engine}")

    # Simulated assessment logic
    typer.echo("⏳ Running assessment...\n")

    # Show contextual output
    show_assess_output()