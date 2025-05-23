"""Evaluate pipeline outputs."""

import typer
from pathlib import Path
from typing import Optional, List
import json
from datetime import datetime
from rich.panel import Panel

from cli.utils import (
    console, print_success, print_error, print_info, print_warning,
    load_config, format_duration, format_cost, Spinner, create_table,
    read_run_result, list_runs
)
from modules.config import Settings
from modules.run_engine import RunEngine


def score_command(
    query: Optional[str] = typer.Argument(
        None,
        help="Query to evaluate (if not using --run-id)"
    ),
    ground_truth: Optional[str] = typer.Option(
        None,
        "--ground-truth", "-g",
        help="Expected answer for evaluation"
    ),
    run_id: Optional[str] = typer.Option(
        None,
        "--run-id", "-r",
        help="Evaluate a previous run by ID"
    ),
    baseline: Optional[str] = typer.Option(
        None,
        "--baseline", "-b",
        help="Compare against baseline run ID"
    ),
    k: Optional[int] = typer.Option(
        None,
        "--k",
        help="Number of documents to retrieve"
    ),
    config_path: Optional[Path] = typer.Option(
        None,
        "--config",
        help="Path to config file"
    ),
    output: Optional[Path] = typer.Option(
        None,
        "--output", "-o",
        help="Save evaluation results to file"
    ),
    json_output: bool = typer.Option(
        False,
        "--json",
        help="Output raw JSON"
    ),
    list_runs_flag: bool = typer.Option(
        False,
        "--list",
        help="List available runs"
    )
):
    """
    Evaluate pipeline outputs using configured metrics.
    
    Examples:
        nai score "What is NnennaAI?" --ground-truth "A modular GenAI framework"
        nai score --run-id abc123
        nai score --list
        nai score "Question here" --baseline latest
    """
    
    # Handle list runs
    if list_runs_flag:
        runs = list_runs()
        if not runs:
            print_info("No saved runs found")
            return
        
        table = create_table("Available Runs", ["Run ID", "Query", "Timestamp", "Duration"])
        for run in runs[:20]:  # Show last 20
            timestamp = datetime.fromisoformat(run["timestamp"])
            table.add_row(
                run["run_id"][:12],
                run["query"][:50] + "..." if len(run["query"]) > 50 else run["query"],
                timestamp.strftime("%Y-%m-%d %H:%M:%S"),
                format_duration(run["duration"])
            )
        
        console.print(table)
        if len(runs) > 20:
            print_info(f"Showing 20 of {len(runs)} runs")
        return
    
    # Load configuration
    config_dict = load_config(config_path)
    if not config_dict:
        print_error("No configuration found. Run 'nai init' first.")
        raise typer.Exit(1)
    
    settings = Settings(**config_dict)
    
    # Determine what to evaluate
    if run_id:
        # Evaluate existing run
        if run_id == "latest":
            runs = list_runs()
            if not runs:
                print_error("No saved runs found")
                raise typer.Exit(1)
            run_id = runs[0]["run_id"]
        
        run_data = read_run_result(run_id)
        if not run_data:
            print_error(f"Run {run_id} not found")
            raise typer.Exit(1)
        
        query = run_data["query"]
        answer = run_data["answer"]
        contexts = [doc["text"] for doc in run_data["contexts"]]
        
        console.print(f"\n[bold]Evaluating run:[/bold] {run_id[:12]}")
        console.print(f"[bold]Query:[/bold] {query}\n")
        
    elif query:
        # Run pipeline and evaluate
        console.print(f"\n[bold]Running and evaluating:[/bold] {query}\n")
        
        try:
            engine = RunEngine(settings)
            
            with Spinner("Running pipeline..."):
                result = engine.run(query, k=k)
            
            answer = result.answer
            contexts = [doc["text"] for doc in result.contexts]
            run_id = result.run_id
            
            # Show answer
            answer_panel = Panel(
                answer,
                title="[bold green]Generated Answer[/bold green]",
                border_style="green",
                padding=(1, 2)
            )
            console.print(answer_panel)
            
        except Exception as e:
            print_error(f"Pipeline failed: {e}")
            raise typer.Exit(1)
    
    else:
        print_error("Provide either a query or --run-id")
        raise typer.Exit(1)
    
    # Load baseline if specified
    baseline_data = None
    if baseline:
        if baseline == "latest":
            runs = list_runs()
            if len(runs) > 1:
                baseline = runs[1]["run_id"]  # Second latest
            else:
                print_warning("No baseline run available")
                baseline = None
        
        if baseline:
            baseline_data = read_run_result(baseline)
            if not baseline_data:
                print_warning(f"Baseline run {baseline} not found")
                baseline_data = None
    
    # Initialize evaluator
    try:
        engine = RunEngine(settings)
        evaluator = engine.evaluator
    except Exception as e:
        print_error(f"Failed to initialize evaluator: {e}")
        raise typer.Exit(1)
    
    # Run evaluation
    console.print("\n[bold]Running evaluation...[/bold]")
    
    try:
        with Spinner(f"Evaluating with {settings.eval.metric}..."):
            scores = evaluator.evaluate(
                query=query,
                prediction=answer,
                contexts=contexts,
                ground_truth=ground_truth
            )
        
        # Handle JSON output
        if json_output:
            output_data = {
                "run_id": run_id,
                "query": query,
                "answer": answer,
                "ground_truth": ground_truth,
                "evaluation": scores,
                "evaluator": settings.eval.metric,
                "timestamp": datetime.now().isoformat()
            }
            
            if baseline_data:
                output_data["baseline"] = {
                    "run_id": baseline,
                    "scores": baseline_data.get("evaluation", {})
                }
            
            if output:
                with open(output, 'w') as f:
                    json.dump(output_data, f, indent=2)
                print_success(f"Saved JSON output to {output}")
            else:
                console.print_json(data=output_data)
            return
        
        # Display evaluation results
        console.print("\n[bold]Evaluation Results:[/bold]")
        
        # Create results table
        results_table = create_table(
            f"{settings.eval.metric.upper()} Evaluation",
            ["Metric", "Score", "Status"]
        )
        
        # Show individual metrics
        for metric, value in scores.items():
            if metric in ["passed", "error"]:
                continue
            
            # Format score
            if isinstance(value, float):
                score_str = f"{value:.3f}"
            else:
                score_str = str(value)
            
            # Determine status
            if metric == "overall_score":
                threshold = settings.eval.threshold
                if value >= threshold:
                    status = f"[green]✅ Pass (≥{threshold})[/green]"
                else:
                    status = f"[red]❌ Fail (<{threshold})[/red]"
            else:
                status = "―"
            
            results_table.add_row(metric, score_str, status)
        
        console.print(results_table)
        
        # Show baseline comparison if available
        if baseline_data and "evaluation" in baseline_data:
            console.print("\n[bold]Baseline Comparison:[/bold]")
            
            baseline_scores = baseline_data["evaluation"]
            comparison_table = create_table(
                "Current vs Baseline",
                ["Metric", "Current", "Baseline", "Change"]
            )
            
            for metric in scores:
                if metric in ["passed", "error"] or metric not in baseline_scores:
                    continue
                
                current = scores[metric]
                baseline_val = baseline_scores[metric]
                
                if isinstance(current, float) and isinstance(baseline_val, float):
                    change = current - baseline_val
                    if change > 0:
                        change_str = f"[green]+{change:.3f}[/green]"
                    elif change < 0:
                        change_str = f"[red]{change:.3f}[/red]"
                    else:
                        change_str = "―"
                    
                    comparison_table.add_row(
                        metric,
                        f"{current:.3f}",
                        f"{baseline_val:.3f}",
                        change_str
                    )
            
            console.print(comparison_table)
        
        # Show ground truth if provided
        if ground_truth:
            gt_panel = Panel(
                ground_truth,
                title="[bold yellow]Ground Truth[/bold yellow]",
                border_style="yellow",
                padding=(1, 2)
            )
            console.print("\n")
            console.print(gt_panel)
        
        # Save evaluation results
        if output:
            output_content = f"""# Evaluation Results

**Run ID:** {run_id}  
**Timestamp:** {datetime.now().isoformat()}  
**Evaluator:** {settings.eval.metric}

## Query
{query}

## Generated Answer
{answer}

## Evaluation Scores
"""
            for metric, value in scores.items():
                if metric not in ["passed", "error"]:
                    output_content += f"- **{metric}:** {value}\n"
            
            if ground_truth:
                output_content += f"\n## Ground Truth\n{ground_truth}\n"
            
            with open(output, 'w') as f:
                f.write(output_content)
            
            print_success(f"Saved evaluation to {output}")
        
        # Show overall result
        if scores.get("passed"):
            print_success(f"Evaluation PASSED (score: {scores.get('overall_score', 0):.3f})")
        else:
            print_error(f"Evaluation FAILED (score: {scores.get('overall_score', 0):.3f})")
        
        # Langfuse tracking note
        if hasattr(engine, 'langfuse_enabled') and engine.langfuse_enabled:
            print_info("Evaluation scores tracked in Langfuse dashboard")
        
    except Exception as e:
        print_error(f"Evaluation failed: {e}")
        console.print_exception()
        raise typer.Exit(1)

# Export for CLI registration
__all__ = ["score_command"]