"""Configuration management commands."""

import typer
from pathlib import Path
from typing import Optional
import json
import yaml
from rich.syntax import Syntax
from rich.tree import Tree

from cli.utils import (
    console, print_success, print_error, print_info,
    load_config, save_config, create_table
)
from modules.config import Settings


app = typer.Typer(help="Manage NnennaAI configuration")


def config_command(
    action: str = typer.Argument(
        "show",
        help="Action to perform: show, get, set, list"
    ),
    key: Optional[str] = typer.Argument(
        None,
        help="Configuration key (e.g., 'generator.model')"
    ),
    value: Optional[str] = typer.Argument(
        None,
        help="Value to set"
    ),
    config_path: Optional[Path] = typer.Option(
        None,
        "--config", "-c",
        help="Path to config file"
    ),
    json_output: bool = typer.Option(
        False,
        "--json",
        help="Output in JSON format"
    )
):
    """
    View and modify configuration.
    
    Examples:
        nai config show
        nai config get generator.model
        nai config set generator.model gpt-4
        nai config list retriever
    """
    
    # Load current config
    config_dict = load_config(config_path)
    
    if action == "show":
        # Show full configuration
        if not config_dict:
            print_error("No configuration found. Run 'nai init' first.")
            raise typer.Exit(1)
        
        if json_output:
            console.print_json(data=config_dict)
        else:
            # Pretty print YAML
            yaml_str = yaml.dump(config_dict, default_flow_style=False, sort_keys=False)
            syntax = Syntax(yaml_str, "yaml", theme="monokai", line_numbers=True)
            console.print(syntax)
    
    elif action == "get":
        # Get specific value
        if not key:
            print_error("Specify a key to get (e.g., 'generator.model')")
            raise typer.Exit(1)
        
        # Navigate nested config
        value = config_dict
        for part in key.split('.'):
            if isinstance(value, dict) and part in value:
                value = value[part]
            else:
                print_error(f"Key '{key}' not found")
                raise typer.Exit(1)
        
        if json_output:
            console.print_json(data={key: value})
        else:
            console.print(f"[bold]{key}:[/bold] {value}")
    
    elif action == "set":
        # Set configuration value
        if not key or value is None:
            print_error("Specify both key and value (e.g., 'nai config set generator.model gpt-4')")
            raise typer.Exit(1)
        
        # Parse value
        # Try to parse as JSON first (for lists, dicts, bools, numbers)
        try:
            parsed_value = json.loads(value)
        except:
            # Keep as string
            parsed_value = value
        
        # Navigate and set nested value
        parts = key.split('.')
        current = config_dict
        
        # Create nested structure if needed
        for i, part in enumerate(parts[:-1]):
            if part not in current:
                current[part] = {}
            elif not isinstance(current[part], dict):
                print_error(f"Cannot set '{key}' - '{'.'.join(parts[:i+1])}' is not a dict")
                raise typer.Exit(1)
            current = current[part]
        
        # Set the value
        old_value = current.get(parts[-1])
        current[parts[-1]] = parsed_value
        
        # Save config
        config_file = config_path or Path("config.yaml")
        save_config(config_dict, config_file)
        
        print_success(f"Set {key} = {parsed_value}")
        if old_value is not None and old_value != parsed_value:
            print_info(f"Previous value: {old_value}")
    
    elif action == "list":
        # List configuration section
        if not config_dict:
            print_error("No configuration found")
            raise typer.Exit(1)
        
        # If key provided, show that section
        if key:
            section = config_dict
            for part in key.split('.'):
                if isinstance(section, dict) and part in section:
                    section = section[part]
                else:
                    print_error(f"Section '{key}' not found")
                    raise typer.Exit(1)
            
            if isinstance(section, dict):
                # Create tree view
                tree = Tree(f"[bold]{key}[/bold]")
                _add_to_tree(tree, section)
                console.print(tree)
            else:
                console.print(f"[bold]{key}:[/bold] {section}")
        else:
            # Show top-level sections
            console.print("[bold]Configuration sections:[/bold]")
            for section in config_dict:
                if isinstance(config_dict[section], dict):
                    console.print(f"  • {section} ({len(config_dict[section])} settings)")
                else:
                    console.print(f"  • {section}: {config_dict[section]}")
    
    elif action == "validate":
        # Validate configuration
        try:
            settings = Settings(**config_dict)
            print_success("Configuration is valid")
            
            # Show summary
            table = create_table("Configuration Summary", ["Component", "Provider/Model", "Status"])
            
            table.add_row(
                "Embeddings",
                f"{settings.embeddings.provider} / {settings.embeddings.model}",
                "✅"
            )
            table.add_row(
                "Retriever", 
                settings.retriever.provider,
                "✅"
            )
            table.add_row(
                "Generator",
                f"{settings.generator.provider} / {settings.generator.model}",
                "✅"
            )
            table.add_row(
                "Evaluator",
                settings.eval.metric,
                "✅"
            )
            
            console.print(table)
            
        except Exception as e:
            print_error(f"Configuration invalid: {e}")
            raise typer.Exit(1)
    
    elif action == "reset":
        # Reset to defaults
        if not typer.confirm("Reset configuration to defaults?"):
            print_info("Cancelled")
            return
        
        # Create default settings
        default_settings = Settings()
        config_dict = default_settings.model_dump(exclude_none=True)
        
        # Save
        config_file = config_path or Path("config.yaml")
        save_config(config_dict, config_file)
        
        print_success("Configuration reset to defaults")
    
    else:
        print_error(f"Unknown action: {action}")
        console.print("Available actions: show, get, set, list, validate, reset")
        raise typer.Exit(1)


def _add_to_tree(tree: Tree, data: dict, prefix: str = "") -> None:
    """Recursively add dict to tree."""
    for key, value in data.items():
        if isinstance(value, dict):
            branch = tree.add(f"[bold cyan]{key}[/bold cyan]")
            _add_to_tree(branch, value, f"{prefix}{key}.")
        else:
            tree.add(f"[green]{key}[/green]: {value}")

# Export for CLI registration
__all__ = ["config_command"]