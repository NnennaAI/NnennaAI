"""Dashboard for viewing runs and metrics."""

import typer
from pathlib import Path
from typing import Optional
import json
from datetime import datetime
import webbrowser
from collections import defaultdict

from cli.utils import (
    console, print_success, print_error, print_info,
    list_runs, read_run_result, format_duration, format_cost,
    create_table
)


def dashboard_command(
    port: int = typer.Option(
        8080,
        "--port", "-p",
        help="Port to run dashboard on"
    ),
    export: Optional[Path] = typer.Option(
        None,
        "--export", "-e", 
        help="Export dashboard as static HTML"
    ),
    last_n: int = typer.Option(
        50,
        "--last", "-n",
        help="Show last N runs"
    ),
    run_dir: Path = typer.Option(
        Path(".nai/runs"),
        "--run-dir",
        help="Directory containing run results"
    )
):
    """
    Launch dashboard to view runs and metrics.
    
    Examples:
        nai dashboard                    # Launch interactive dashboard
        nai dashboard --export report.html  # Export static report
        nai dashboard --last 100         # Show last 100 runs
    """
    
    # Load runs
    runs = list_runs(run_dir)
    
    if not runs:
        print_error("No runs found. Run some queries first with 'nai run'")
        raise typer.Exit(1)
    
    # Limit to last N runs
    runs = runs[:last_n]
    
    # Load full run data
    full_runs = []
    for run_summary in runs:
        run_data = read_run_result(run_summary["run_id"], run_dir)
        if run_data:
            full_runs.append(run_data)
    
    if export:
        # Generate static HTML report
        print_info(f"Generating dashboard for {len(full_runs)} runs...")
        
        html_content = _generate_html_dashboard(full_runs)
        
        with open(export, 'w') as f:
            f.write(html_content)
        
        print_success(f"Dashboard exported to {export}")
        
        # Optionally open in browser
        if typer.confirm("Open in browser?", default=True):
            webbrowser.open(f"file://{export.absolute()}")
    
    else:
        # Show summary in terminal (simple version for v0.1.0)
        console.print(f"\n[bold]Pipeline Dashboard[/bold] - Last {len(full_runs)} runs\n")
        
        # Summary statistics
        total_cost = sum(r.get("metrics", {}).get("estimated_cost", 0) or 0 for r in full_runs)
        total_tokens = sum(
            r.get("metrics", {}).get("generator", {}).get("total_tokens", 0) 
            for r in full_runs
        )
        avg_latency = sum(r.get("duration_seconds", 0) for r in full_runs) / len(full_runs)
        
        # Create summary table
        summary_table = create_table("Summary Statistics", ["Metric", "Value"])
        summary_table.add_row("Total runs", str(len(full_runs)))
        summary_table.add_row("Total cost", format_cost(total_cost))
        summary_table.add_row("Total tokens", f"{total_tokens:,}")
        summary_table.add_row("Average latency", format_duration(avg_latency))
        
        console.print(summary_table)
        
        # Recent runs table
        console.print("\n[bold]Recent Runs:[/bold]")
        
        runs_table = create_table(
            "Pipeline Runs",
            ["Time", "Query", "Latency", "Tokens", "Cost", "Score"]
        )
        
        for run in full_runs[:10]:
            timestamp = datetime.fromisoformat(run["timestamp"])
            query_preview = run["query"][:40] + "..." if len(run["query"]) > 40 else run["query"]
            
            # Get metrics
            latency = run.get("duration_seconds", 0)
            tokens = run.get("metrics", {}).get("generator", {}).get("total_tokens", 0)
            cost = run.get("metrics", {}).get("estimated_cost", 0)
            
            # Check if evaluation exists
            if "evaluation" in run:
                score = run["evaluation"].get("overall_score", "N/A")
                if isinstance(score, float):
                    score = f"{score:.2f}"
            else:
                score = "―"
            
            runs_table.add_row(
                timestamp.strftime("%H:%M:%S"),
                query_preview,
                format_duration(latency),
                str(tokens) if tokens else "―",
                format_cost(cost) if cost else "―",
                score
            )
        
        console.print(runs_table)
        
        # Model usage breakdown
        model_usage = defaultdict(lambda: {"count": 0, "tokens": 0, "cost": 0})
        
        for run in full_runs:
            model = run.get("config", {}).get("generator", {}).get("model", "unknown")
            model_usage[model]["count"] += 1
            model_usage[model]["tokens"] += run.get("metrics", {}).get("generator", {}).get("total_tokens", 0)
            model_usage[model]["cost"] += run.get("metrics", {}).get("estimated_cost", 0) or 0
        
        console.print("\n[bold]Model Usage:[/bold]")
        
        model_table = create_table("Model Statistics", ["Model", "Runs", "Tokens", "Cost"])
        
        for model, stats in sorted(model_usage.items(), key=lambda x: x[1]["count"], reverse=True):
            model_table.add_row(
                model,
                str(stats["count"]),
                f"{stats['tokens']:,}",
                format_cost(stats["cost"])
            )
        
        console.print(model_table)
        
        print_info(f"\nExport full dashboard: nai dashboard --export report.html")
        
        # Note about Langfuse
        if any(r.get("metrics", {}).get("langfuse_enabled") for r in full_runs):
            print_info("💡 View detailed cost analytics in your Langfuse dashboard")


def _generate_html_dashboard(runs: list) -> str:
    """Generate static HTML dashboard."""
    
    # Calculate statistics
    total_runs = len(runs)
    total_cost = sum(r.get("metrics", {}).get("estimated_cost", 0) or 0 for r in runs)
    total_tokens = sum(
        r.get("metrics", {}).get("generator", {}).get("total_tokens", 0) 
        for r in runs
    )
    
    # Group by date
    runs_by_date = defaultdict(list)
    for run in runs:
        date = datetime.fromisoformat(run["timestamp"]).date()
        runs_by_date[date].append(run)
    
    # Generate charts data
    dates = sorted(runs_by_date.keys())
    daily_counts = [len(runs_by_date[d]) for d in dates]
    daily_costs = [
        sum(r.get("metrics", {}).get("estimated_cost", 0) or 0 for r in runs_by_date[d])
        for d in dates
    ]
    
    # Create HTML
    html = f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>NnennaAI Dashboard</title>
    <script src="https://cdn.jsdelivr.net/npm/chart.js@4.4.0/dist/chart.umd.min.js"></script>
    <style>
        body {{
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
            margin: 0;
            padding: 0;
            background: #f5f5f5;
            color: #333;
        }}
        .container {{
            max-width: 1200px;
            margin: 0 auto;
            padding: 20px;
        }}
        h1 {{
            color: #2563eb;
            margin-bottom: 30px;
        }}
        .stats-grid {{
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(250px, 1fr));
            gap: 20px;
            margin-bottom: 40px;
        }}
        .stat-card {{
            background: white;
            padding: 20px;
            border-radius: 8px;
            box-shadow: 0 1px 3px rgba(0,0,0,0.1);
        }}
        .stat-value {{
            font-size: 2em;
            font-weight: bold;
            color: #1e40af;
        }}
        .stat-label {{
            color: #6b7280;
            margin-top: 5px;
        }}
        .chart-container {{
            background: white;
            padding: 20px;
            border-radius: 8px;
            box-shadow: 0 1px 3px rgba(0,0,0,0.1);
            margin-bottom: 40px;
            height: 400px;
        }}
        table {{
            width: 100%;
            background: white;
            border-radius: 8px;
            overflow: hidden;
            box-shadow: 0 1px 3px rgba(0,0,0,0.1);
        }}
        th {{
            background: #f9fafb;
            padding: 12px;
            text-align: left;
            font-weight: 600;
            color: #374151;
        }}
        td {{
            padding: 12px;
            border-top: 1px solid #e5e7eb;
        }}
        .footer {{
            text-align: center;
            color: #6b7280;
            margin-top: 40px;
            padding: 20px;
        }}
    </style>
</head>
<body>
    <div class="container">
        <h1>🧠 NnennaAI Pipeline Dashboard</h1>
        
        <div class="stats-grid">
            <div class="stat-card">
                <div class="stat-value">{total_runs}</div>
                <div class="stat-label">Total Runs</div>
            </div>
            <div class="stat-card">
                <div class="stat-value">${total_cost:.4f}</div>
                <div class="stat-label">Total Cost</div>
            </div>
            <div class="stat-card">
                <div class="stat-value">{total_tokens:,}</div>
                <div class="stat-label">Total Tokens</div>
            </div>
            <div class="stat-card">
                <div class="stat-value">{len(dates)}</div>
                <div class="stat-label">Active Days</div>
            </div>
        </div>
        
        <div class="chart-container">
            <canvas id="runsChart"></canvas>
        </div>
        
        <h2>Recent Runs</h2>
        <table>
            <thead>
                <tr>
                    <th>Timestamp</th>
                    <th>Query</th>
                    <th>Duration</th>
                    <th>Tokens</th>
                    <th>Cost</th>
                    <th>Score</th>
                </tr>
            </thead>
            <tbody>
    """
    
    # Add run rows
    for run in runs[:50]:  # Show last 50
        timestamp = datetime.fromisoformat(run["timestamp"]).strftime("%Y-%m-%d %H:%M:%S")
        query = run["query"][:60] + "..." if len(run["query"]) > 60 else run["query"]
        duration = format_duration(run.get("duration_seconds", 0))
        tokens = run.get("metrics", {}).get("generator", {}).get("total_tokens", 0)
        cost = run.get("metrics", {}).get("estimated_cost", 0)
        
        if "evaluation" in run:
            score = run["evaluation"].get("overall_score", "N/A")
            if isinstance(score, float):
                score = f"{score:.2f}"
        else:
            score = "―"
        
        html += f"""
                <tr>
                    <td>{timestamp}</td>
                    <td>{query}</td>
                    <td>{duration}</td>
                    <td>{tokens:,}</td>
                    <td>${cost:.4f}</td>
                    <td>{score}</td>
                </tr>
        """
    
    html += f"""
            </tbody>
        </table>
        
        <div class="footer">
            Generated by NnennaAI on {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}
        </div>
    </div>
    
    <script>
        // Create chart
        const ctx = document.getElementById('runsChart').getContext('2d');
        new Chart(ctx, {{
            type: 'line',
            data: {{
                labels: {json.dumps([d.isoformat() for d in dates])},
                datasets: [{{
                    label: 'Runs per Day',
                    data: {json.dumps(daily_counts)},
                    borderColor: '#2563eb',
                    backgroundColor: '#dbeafe',
                    tension: 0.1
                }}, {{
                    label: 'Cost per Day ($)',
                    data: {json.dumps(daily_costs)},
                    borderColor: '#dc2626',
                    backgroundColor: '#fee2e2',
                    tension: 0.1,
                    yAxisID: 'y1'
                }}]
            }},
            options: {{
                responsive: true,
                maintainAspectRatio: false,
                plugins: {{
                    title: {{
                        display: true,
                        text: 'Pipeline Usage Over Time'
                    }}
                }},
                scales: {{
                    y: {{
                        type: 'linear',
                        display: true,
                        position: 'left',
                        title: {{
                            display: true,
                            text: 'Number of Runs'
                        }}
                    }},
                    y1: {{
                        type: 'linear',
                        display: true,
                        position: 'right',
                        title: {{
                            display: true,
                            text: 'Cost ($)'
                        }},
                        grid: {{
                            drawOnChartArea: false
                        }}
                    }}
                }}
            }}
        }});
    </script>
</body>
</html>
    """
    
    return html


# Export for CLI registration
__all__ = ["dashboard_command"]