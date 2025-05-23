"""Initialize a new NnennaAI project."""

import typer
from pathlib import Path
import shutil
from typing import Optional

from cli.utils import (
    console, print_success, print_error, print_warning, print_info,
    save_config, Spinner
)

GITHUB_URL = "https://github.com/NnennaAI/NnennaAI"

# Template configurations
TEMPLATES = {
    "rag-starter": {
        "description": "Basic RAG pipeline with evaluation",
        "config": {
            "embeddings": {
                "provider": "openai",
                "model": "text-embedding-3-small"
            },
            "retriever": {
                "provider": "chroma",
                "persist_dir": ".nai/chroma",
                "collection": "documents"
            },
            "generator": {
                "provider": "openai",
                "model": "gpt-4o-mini",
                "temperature": 0.7,
                "max_tokens": 1000
            },
            "eval": {
                "metric": "ragas",
                "ragas_metrics": ["faithfulness", "answer_relevancy", "context_precision"],
                "threshold": 0.7
            },
            "pipeline": {
                "chunk_size": 400,
                "chunk_overlap": 50,
                "top_k": 5,
                "langfuse_enabled": True
            }
        }
    },
    "minimal": {
        "description": "Minimal setup for quick testing",
        "config": {
            "embeddings": {"provider": "openai"},
            "retriever": {"provider": "chroma"},
            "generator": {"provider": "openai"},
            "eval": {"metric": "simple"}
        }
    }
}


def init_command(
    path: Path = typer.Argument(Path("."), help="Project directory path"),
    template: str = typer.Option(
        "rag-starter",
        "--template", "-t",
        help="Template to use",
        show_choices=True,
        case_sensitive=False,
        callback=lambda x: x.lower()
    ),
    name: Optional[str] = typer.Option(None, "--name", "-n", help="Project name"),
    force: bool = typer.Option(False, "--force", "-f", help="Overwrite existing files")
):
    """Initialize a new NnennaAI project with starter templates."""
    
    # Validate template
    if template not in TEMPLATES:
        print_error(f"Unknown template: {template}")
        console.print(f"Available templates: {', '.join(TEMPLATES.keys())}")
        raise typer.Exit(1)
    
    # Create project directory
    project_path = Path(path).resolve()
    project_name = name or project_path.name
    
    if project_path.exists() and any(project_path.iterdir()) and not force:
        print_error(f"Directory {project_path} is not empty. Use --force to overwrite.")
        raise typer.Exit(1)
    
    with Spinner(f"Creating project '{project_name}'..."):
        # Create directory structure
        project_path.mkdir(parents=True, exist_ok=True)
        (project_path / "data").mkdir(exist_ok=True)
        (project_path / "docs").mkdir(exist_ok=True)
        (project_path / ".nai").mkdir(exist_ok=True)
        (project_path / ".nai" / "runs").mkdir(exist_ok=True)
    
    # Create config.yaml
    config_path = project_path / "config.yaml"
    template_config = TEMPLATES[template]["config"].copy()
    
    # Add project metadata
    template_config["project"] = {
        "name": project_name,
        "version": "0.1.0",
        "template": template
    }
    
    save_config(template_config, config_path)
    print_success(f"Created config.yaml")
    
    # Create .env.example
    env_example = """# NnennaAI Environment Variables
OPENAI_API_KEY=your-openai-api-key-here

# Optional: Langfuse observability
# LANGFUSE_PUBLIC_KEY=your-public-key
# LANGFUSE_SECRET_KEY=your-secret-key
# LANGFUSE_HOST=https://cloud.langfuse.com  # or your self-hosted URL

# Optional: Override models
# EMBEDDING_MODEL=text-embedding-3-small
# GENERATOR_MODEL=gpt-4o-mini
"""
    
    env_path = project_path / ".env.example"
    env_path.write_text(env_example)
    print_success(f"Created .env.example")
    
    # Create .gitignore
    gitignore = """.env
.nai/
__pycache__/
*.pyc
.DS_Store
.vscode/
.idea/
"""
    
    gitignore_path = project_path / ".gitignore"
    gitignore_path.write_text(gitignore)
    print_success(f"Created .gitignore")
    
    # Create README.md
    readme = f"""# {project_name}

Built with [NnennaAI](https://github.com/NnennaAI/NnennaAI) - the developer-first GenAI framework.

## Quick Start

1. Set up your environment:
   ```bash
   cp .env.example .env
   # Add your OPENAI_API_KEY to .env
   ```

2. Install dependencies:
   ```bash
   pip install nai
   ```

3. Ingest your documents:
   ```bash
   nai ingest ./docs
   ```

4. Run a query:
   ```bash
   nai run "What is the main topic of the documents?"
   ```

5. Evaluate quality:
   ```bash
   nai score --baseline latest
   ```

## Project Structure

```
{project_name}/
├── config.yaml      # Pipeline configuration
├── data/           # Raw data files
├── docs/           # Documents to ingest
├── .nai/           # NnennaAI metadata
│   ├── chroma/     # Vector store
│   └── runs/       # Run history
└── .env           # Environment variables (create from .env.example)
```

## Configuration

Edit `config.yaml` to customize:
- Embedding model
- Retriever settings
- Generator parameters
- Evaluation metrics

## Learn More

- [NnennaAI Documentation](https://github.com/NnennaAI/NnennaAI/docs)
- [Template: {template}]({GITHUB_URL}/templates/{template})
"""
    
    readme_path = project_path / "README.md"
    readme_path.write_text(readme)
    print_success(f"Created README.md")
    
    # Create sample documents
    if template == "rag-starter":
        sample_doc = """# Welcome to NnennaAI

NnennaAI is a developer-first framework for building GenAI applications with built-in evaluation and observability.

## Key Features

- **Modular Architecture**: Swap embedders, retrievers, and generators with a single config change
- **Evaluation First**: Every run is automatically evaluated for quality
- **Cost Tracking**: Know exactly how much each query costs
- **Developer Friendly**: CLI-first design for rapid iteration

## Philosophy

We believe that you can't own your AI if you don't own your evaluations. That's why evaluation is built into every step of the NnennaAI pipeline.

## Getting Started

The quickest way to get started is with the CLI:

```bash
nai init my-project
nai ingest ./docs
nai run "What is NnennaAI?"
nai score
```

Build with intention. Evaluate with confidence. Scale with clarity.
"""
        
        docs_path = project_path / "docs" / "welcome.md"
        docs_path.write_text(sample_doc)
        print_success(f"Created sample document")
    
    # Create a simple Python script for programmatic usage
    script = """#!/usr/bin/env python3
\"\"\"Example script for using NnennaAI programmatically.\"\"\"

from modules.config import Settings
from modules.engine import RunEngine

def main():
    # Load configuration
    settings = Settings.from_yaml("config.yaml")
    
    # Initialize pipeline
    engine = RunEngine(settings)
    
    # Example: Run a query
    result = engine.run("What is NnennaAI?")
    
    print(f"Answer: {result.answer}")
    print(f"Cost: ${result.metrics.get('estimated_cost', 0):.4f}")
    print(f"Latency: {result.duration_seconds:.2f}s")

if __name__ == "__main__":
    main()
"""
    
    script_path = project_path / "run_pipeline.py"
    script_path.write_text(script)
    script_path.chmod(0o755)  # Make executable
    print_success(f"Created run_pipeline.py")
    
    # Print summary
    console.print("\n[bold green]✨ Project initialized successfully![/bold green]\n")
    
    # Print tree structure
    console.print("[bold]Project structure:[/bold]")
    console.print(f"""
{project_name}/
├── 📄 config.yaml      [dim]# Pipeline configuration[/dim]
├── 📄 .env.example    [dim]# Environment template[/dim]
├── 📄 .gitignore      [dim]# Git ignore rules[/dim]
├── 📄 README.md       [dim]# Project documentation[/dim]
├── 🐍 run_pipeline.py [dim]# Example Python script[/dim]
├── 📁 data/           [dim]# Your data files[/dim]
├── 📁 docs/           [dim]# Documents to ingest[/dim]
│   └── 📄 welcome.md  [dim]# Sample document[/dim]
└── 📁 .nai/           [dim]# NnennaAI metadata[/dim]
    """)
    
    # Print next steps
    console.print("\n[bold]Next steps:[/bold]")
    console.print("1. cd " + str(project_path))
    console.print("2. cp .env.example .env")
    console.print("3. Add your OPENAI_API_KEY to .env")
    console.print("4. nai ingest ./docs")
    console.print("5. nai run \"What is NnennaAI?\"")
    
    print_info(f"\nUsing template: {template} - {TEMPLATES[template]['description']}")


# Export for CLI registration
__all__ = ["init_command"]