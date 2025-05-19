# cli/commands/init.py
import typer
import os
from pathlib import Path
from context.context_docs import show_init_output

app = typer.Typer(help="📦 Scaffold a GenAI pipeline")

@app.command()
def rag(
    template: str = typer.Option("starter-rag", help="Which template to use"),
    llm: str = typer.Option("gpt-4", help="LLM provider (gpt-4, mistral, claude, etc.)"),
    db: str = typer.Option("qdrant", help="Vector DB (qdrant, chroma, weaviate)"),
    path: str = typer.Option("./my-rag-pipeline", help="Project output directory")
):
    """
    Initialize a new RAG project with default configurations.
    """
    project_path = Path(path)
    os.makedirs(project_path, exist_ok=True)

    # Simulate file creation (replace with real file copying logic later)
    (project_path / "config.yaml").touch()
    (project_path / ".env.example").touch()
    (project_path / "run_rag_pipeline.py").touch()

    # Show contextual output
    show_init_output()
