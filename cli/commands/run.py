# cli/commands/run.py
import typer
from context.context_docs import show_run_output

app = typer.Typer(help="⚙️ Run the pipeline from config or direct query")

@app.command()
def query(
    query: str = typer.Argument(..., help="User query to run through the pipeline"),
    config: str = typer.Option("config.yaml", help="Path to pipeline configuration file")
):
    """
    Run a GenAI pipeline using the specified query and config file.
    """
    # TODO: Load config and run RAG logic here
    # This is just scaffolding for now

    typer.echo(f"📥 Loading config: {config}")
    typer.echo(f"🔍 Query: {query}")

    # Simulated run steps
    typer.echo("🔗 Using vector DB: Qdrant | Embeddings: text-embedding-3-small")
    typer.echo("📚 Retrieved 5 relevant chunks (top-k=5)")
    typer.echo("🤖 Generating response using GPT-4...\n")

    # Save output simulation
    typer.echo("✅ Output saved to: outputs/response.json\n")

    # Show contextual UX output
    show_run_output()