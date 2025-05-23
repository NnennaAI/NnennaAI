"""Ingest documents into the vector store."""

import typer
from pathlib import Path
from typing import List, Optional
import time

from cli.utils import (
    console, print_success, print_error, print_warning, print_info,
    load_config, format_duration, Spinner, create_table
)
from modules.config import Settings
from modules.run_engine import RunEngine


def ingest_command(
    paths: List[Path] = typer.Argument(
        ...,
        help="Paths to files or directories to ingest",
        exists=True
    ),
    pattern: Optional[str] = typer.Option(
        "*.md",
        "--pattern", "-p",
        help="File pattern to match (e.g., '*.txt', '*.md')"
    ),
    chunk_size: Optional[int] = typer.Option(
        None,
        "--chunk-size", "-c",
        help="Override chunk size"
    ),
    chunk_overlap: Optional[int] = typer.Option(
        None,
        "--chunk-overlap", "-o",
        help="Override chunk overlap"
    ),
    metadata: Optional[List[str]] = typer.Option(
        None,
        "--metadata", "-m",
        help="Add metadata as key=value pairs"
    ),
    batch_size: int = typer.Option(
        10,
        "--batch-size", "-b",
        help="Number of documents to process at once"
    ),
    reset: bool = typer.Option(
        False,
        "--reset", "-r",
        help="Clear existing documents before ingesting"
    ),
    config_path: Optional[Path] = typer.Option(
        None,
        "--config",
        help="Path to config file"
    ),
    dry_run: bool = typer.Option(
        False,
        "--dry-run",
        help="Show what would be ingested without actually doing it"
    )
):
    """
    Ingest documents into the vector store.
    
    Examples:
        nai ingest ./docs
        nai ingest ./data --pattern "*.txt"
        nai ingest file1.md file2.md --metadata project=rag tier=docs
    """
    
    # Load configuration
    config_dict = load_config(config_path)
    if not config_dict:
        print_error("No configuration found. Run 'nai init' first.")
        raise typer.Exit(1)
    
    # Override config with CLI options
    if chunk_size:
        config_dict.setdefault("pipeline", {})["chunk_size"] = chunk_size
    if chunk_overlap:
        config_dict.setdefault("pipeline", {})["chunk_overlap"] = chunk_overlap
    
    settings = Settings(**config_dict)
    
    # Parse metadata
    metadata_dict = {}
    if metadata:
        for item in metadata:
            if "=" not in item:
                print_error(f"Invalid metadata format: {item}. Use key=value")
                raise typer.Exit(1)
            key, value = item.split("=", 1)
            metadata_dict[key] = value
    
    # Collect files to ingest
    files_to_ingest = []
    
    for path in paths:
        if path.is_file():
            files_to_ingest.append(path)
        elif path.is_dir():
            # Find matching files in directory
            if pattern.startswith("*"):
                matching_files = list(path.rglob(pattern))
            else:
                matching_files = list(path.glob(pattern))
            
            if not matching_files:
                print_warning(f"No files matching '{pattern}' found in {path}")
            else:
                files_to_ingest.extend(matching_files)
        else:
            print_warning(f"Skipping {path} - not a file or directory")
    
    if not files_to_ingest:
        print_error("No files found to ingest")
        raise typer.Exit(1)
    
    # Remove duplicates and sort
    files_to_ingest = sorted(set(files_to_ingest))
    
    # Show what will be ingested
    console.print(f"\n[bold]Found {len(files_to_ingest)} files to ingest:[/bold]")
    
    table = create_table("Files to Ingest", ["File", "Size", "Type"])
    total_size = 0
    
    for f in files_to_ingest[:10]:  # Show first 10
        size = f.stat().st_size
        total_size += size
        table.add_row(
            str(f.relative_to(Path.cwd())),
            f"{size:,} bytes",
            f.suffix or "no extension"
        )
    
    if len(files_to_ingest) > 10:
        table.add_row("...", f"({len(files_to_ingest) - 10} more files)", "...")
    
    console.print(table)
    
    # Show metadata if provided
    if metadata_dict:
        console.print(f"\n[bold]Metadata:[/bold] {metadata_dict}")
    
    # Show chunk settings
    console.print(f"\n[bold]Chunk settings:[/bold]")
    console.print(f"  Size: {settings.pipeline.chunk_size} chars")
    console.print(f"  Overlap: {settings.pipeline.chunk_overlap} chars")
    
    if dry_run:
        print_info("Dry run - no files were actually ingested")
        return
    
    # Initialize engine
    engine = RunEngine(settings)
    
    # Reset if requested
    if reset:
        with Spinner("Clearing existing documents..."):
            engine.retriever.reset()
        print_success("Cleared existing documents")
    
    # Load and process documents
    documents = []
    
    with Spinner(f"Reading {len(files_to_ingest)} files...") as spinner:
        for i, file_path in enumerate(files_to_ingest):
            try:
                # Read file content
                content = file_path.read_text(encoding='utf-8')
                
                # Create document with metadata
                doc_metadata = {
                    "source": str(file_path.relative_to(Path.cwd())),
                    "filename": file_path.name,
                    "file_type": file_path.suffix,
                    **metadata_dict
                }
                
                documents.append({
                    "text": content,
                    "metadata": doc_metadata
                })
                
                # Update spinner
                spinner.update(f"Reading files... [{i+1}/{len(files_to_ingest)}]")
                
            except Exception as e:
                print_warning(f"Failed to read {file_path}: {e}")
    
    if not documents:
        print_error("No documents could be read")
        raise typer.Exit(1)
    
    print_success(f"Read {len(documents)} documents")
    
    # Ingest documents
    console.print("\n[bold]Starting ingestion...[/bold]")
    
    start_time = time.time()
    
    try:
        with Spinner("Ingesting documents...") as spinner:
            # Update spinner during ingestion
            def update_callback(current, total):
                spinner.update(f"Ingesting... [{current}/{total} documents]")
            
            # Ingest with progress callback
            stats = engine.ingest(documents, batch_size=batch_size)
        
        duration = time.time() - start_time
        
        # Show results
        console.print("\n[bold green]✅ Ingestion complete![/bold green]")
        
        results_table = create_table("Ingestion Results", ["Metric", "Value"])
        results_table.add_row("Documents processed", str(stats["documents_processed"]))
        results_table.add_row("Chunks created", str(stats["chunks_created"]))
        results_table.add_row("Total documents in store", str(stats["retriever_count"]))
        results_table.add_row("Duration", format_duration(duration))
        results_table.add_row("Chunks per second", f"{stats['chunks_per_second']:.1f}")
        
        if engine.langfuse_enabled:
            results_table.add_row("Cost tracking", "✅ Enabled (view in Langfuse)")
        
        console.print(results_table)
        
        # Estimate embedding costs
        if hasattr(engine.embedder, 'estimated_cost'):
            cost = engine.embedder.estimated_cost
            if cost > 0:
                print_info(f"Estimated embedding cost: ${cost:.4f}")
        
        # Next steps
        console.print("\n[bold]Next steps:[/bold]")
        console.print("1. Run a query: [bold green]nai run \"Your question here\"[/bold green]")
        console.print("2. List documents: [bold yellow]nai config show retriever.stats[/bold yellow]")
        
    except Exception as e:
        print_error(f"Ingestion failed: {e}")
        raise typer.Exit(1)


# Export for CLI registration
__all__ = ["ingest_command"]