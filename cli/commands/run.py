"""Run the GenAI pipeline."""

import typer
from pathlib import Path
from typing import Optional
import json
from rich.panel import Panel
from rich.syntax import Syntax

from cli.utils import (
    console, print_success, print_error, print_info,
    load_config, format_duration, format_cost, Spinner, create_table
)
from modules.config import Settings
from modules.run_engine import RunEngine


def run_command(
    query: str = typer.Argument(..., help="Query to run through the pipeline"),
    k: Optional[int] = typer.Option(
        None,
        "--k", "-k",
        help="Number of documents to retrieve"
    ),
    temperature: Optional[float] = typer.Option(
        None,
        "--temperature", "-t",
        help="Override generation temperature"
    ),
    max_tokens: Optional[int] = typer.Option(
        None,
        "--max-tokens",
        help="Override max tokens"
    ),
    config_path: Optional[Path] = typer.Option(
        None,
        "--config",
        help="Path to config file"
    ),
    output: Optional[Path] = typer.Option(
        None,
        "--output", "-o",
        help="Save output to file"
    ),
    json_output: bool = typer.Option(
        False,
        "--json",
        help="Output raw JSON"
    ),
    show_contexts: bool = typer.Option(
        False,
        "--show-contexts", "-c",
        help="Show retrieved contexts"
    ),
    trace: bool = typer.Option(
        False,
        "--trace",
        help="Enable step-by-step tracing"
    ),
    no_save: bool = typer.Option(
        False,
        "--no-save",
        help="Don't save run results"
    )
):
    """
    Run a query through the RAG pipeline.
    
    Examples:
        nai run "What is NnennaAI?"
        nai run "Explain the architecture" --k 10 --trace
        nai run "How does evaluation work?" --output answer.md
    """
    
    # Load configuration
    config_dict = load_config(config_path)
    if not config_dict:
        print_error("No configuration found. Run 'nai init' first.")
        raise typer.Exit(1)
    
    # Override config with CLI options
    if temperature is not None:
        config_dict.setdefault("generator", {})["temperature"] = temperature
    if max_tokens is not None:
        config_dict.setdefault("generator", {})["max_tokens"] = max_tokens
    if no_save:
        config_dict.setdefault("pipeline", {})["save_runs"] = False
    
    settings = Settings(**config_dict)
    
    # Initialize engine
    try:
        engine = RunEngine(settings)
    except Exception as e:
        print_error(f"Failed to initialize pipeline: {e}")
        raise typer.Exit(1)
    
    # Check if retriever has documents
    if hasattr(engine.retriever, 'count') and engine.retriever.count == 0:
        print_error("No documents in vector store. Run 'nai ingest' first.")
        raise typer.Exit(1)
    
    # Run the pipeline
    console.print(f"\n[bold]Running query:[/bold] {query}\n")
    
    try:
        with Spinner("Processing query...") as spinner:
            # Run pipeline
            result = engine.run(query, k=k, trace=trace)
            spinner.update("Generating response...")
        
        # Handle JSON output
        if json_output:
            output_data = result.to_dict()
            if output:
                with open(output, 'w') as f:
                    json.dump(output_data, f, indent=2)
                print_success(f"Saved JSON output to {output}")
            else:
                console.print_json(data=output_data)
            return
        
        # Display answer
        answer_panel = Panel(
            result.answer,
            title="[bold green]Answer[/bold green]",
            border_style="green",
            padding=(1, 2)
        )
        console.print(answer_panel)
        
        # Show contexts if requested
        if show_contexts:
            console.print("\n[bold]Retrieved Contexts:[/bold]")
            for i, ctx in enumerate(result.contexts, 1):
                context_panel = Panel(
                    ctx["text"],
                    title=f"[bold cyan]Context {i}[/bold cyan] (score: {ctx['score']:.3f})",
                    border_style="cyan",
                    padding=(0, 1)
                )
                console.print(context_panel)
                if ctx.get("metadata"):
                    console.print(f"  [dim]Source: {ctx['metadata'].get('source', 'unknown')}[/dim]")
                console.print()
        
        # Show metrics
        console.print("\n[bold]Pipeline Metrics:[/bold]")
        
        metrics_table = create_table("Performance", ["Metric", "Value"])
        
        # Latency metrics
        latency = result.metrics["latency"]
        metrics_table.add_row(
            "Total time",
            format_duration(latency["total_seconds"])
        )
        metrics_table.add_row(
            "├─ Embedding",
            format_duration(latency["embed_seconds"])
        )
        metrics_table.add_row(
            "├─ Retrieval",
            format_duration(latency["retrieve_seconds"])
        )
        metrics_table.add_row(
            "└─ Generation",
            format_duration(latency["generate_seconds"])
        )
        
        # Retrieval metrics
        metrics_table.add_row("", "")  # Empty row
        metrics_table.add_row(
            "Documents retrieved",
            str(result.metrics["retrieval"]["num_contexts"])
        )
        metrics_table.add_row(
            "Average relevance",
            f"{result.metrics['retrieval']['avg_score']:.3f}"
        )
        
        # Token usage
        if "generator" in result.metrics:
            gen_stats = result.metrics["generator"]
            if "total_tokens" in gen_stats:
                metrics_table.add_row("", "")  # Empty row
                metrics_table.add_row(
                    "Total tokens",
                    f"{gen_stats['total_tokens']:,}"
                )
                if "prompt_tokens" in gen_stats:
                    metrics_table.add_row(
                        "├─ Prompt",
                        f"{gen_stats['prompt_tokens']:,}"
                    )
                    metrics_table.add_row(
                        "└─ Completion",
                        f"{gen_stats['completion_tokens']:,}"
                    )
        
        # Cost
        if "estimated_cost" in result.metrics and result.metrics["estimated_cost"]:
            metrics_table.add_row("", "")  # Empty row
            metrics_table.add_row(
                "Estimated cost",
                format_cost(result.metrics["estimated_cost"])
            )
        
        # Langfuse tracking
        if result.metrics.get("langfuse_enabled"):
            metrics_table.add_row(
                "Cost tracking",
                "✅ View in Langfuse dashboard"
            )
        
        console.print(metrics_table)
        
        # Save output if requested
        if output:
            output_content = f"""# Query: {query}

## Answer

{result.answer}

## Metadata

- Run ID: {result.run_id}
- Timestamp: {result.timestamp}
- Duration: {format_duration(result.duration_seconds)}
- Model: {settings.generator.model}
- Retrieved contexts: {len(result.contexts)}
"""
            
            if show_contexts:
                output_content += "\n## Retrieved Contexts\n\n"
                for i, ctx in enumerate(result.contexts, 1):
                    output_content += f"### Context {i} (score: {ctx['score']:.3f})\n\n"
                    output_content += ctx["text"] + "\n\n"
                    if ctx.get("metadata", {}).get("source"):
                        output_content += f"*Source: {ctx['metadata']['source']}*\n\n"
            
            with open(output, 'w') as f:
                f.write(output_content)
            
            print_success(f"Saved output to {output}")
        
        # Show run info
        if not no_save:
            print_info(f"Run ID: {result.run_id}")
            console.print("[dim]View run details: nai score --run-id " + result.run_id[:8] + "[/dim]")
        
        # Show trace if enabled
        if trace and result.trace:
            console.print("\n[bold]Execution Trace:[/bold]")
            for step in result.trace:
                console.print(f"\n[bold cyan]{step['step']}[/bold cyan] ({step['duration_seconds']:.3f}s)")
                # Pretty print the data
                data_str = json.dumps(step['data'], indent=2)
                syntax = Syntax(data_str, "json", theme="monokai", line_numbers=False)
                console.print(syntax)
        
    except KeyboardInterrupt:
        print_error("\nQuery cancelled by user")
        raise typer.Exit(1)
    except Exception as e:
        print_error(f"Pipeline failed: {e}")
        if trace:
            console.print_exception()
        raise typer.Exit(1)

# Export for CLI registration
__all__ = ["run_command"]