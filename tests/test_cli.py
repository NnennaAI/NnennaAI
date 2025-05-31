"""Basic tests for NnennaAI CLI."""

import pytest
from typer.testing import CliRunner
from pathlib import Path
import tempfile
import shutil

from cli.main import app

runner = CliRunner()


def test_cli_version():
    """Test version command."""
    result = runner.invoke(app, ["version"])
    assert result.exit_code == 0
    assert "NnennaAI v0.1.0" in result.stdout


def test_cli_help():
    """Test help command."""
    result = runner.invoke(app, ["--help"])
    assert result.exit_code == 0
    assert "NnennaAI" in result.stdout
    assert "init" in result.stdout
    assert "ingest" in result.stdout
    assert "run" in result.stdout


def test_init_command():
    """Test init command creates project structure."""
    with tempfile.TemporaryDirectory() as tmpdir:
        project_path = Path(tmpdir) / "test-project"
        
        result = runner.invoke(app, ["init", str(project_path)])
        
        assert result.exit_code == 0
        assert "Project initialized successfully" in result.stdout
        
        # Check created files
        assert (project_path / "config.yaml").exists()
        assert (project_path / ".env.example").exists()
        assert (project_path / "README.md").exists()
        assert (project_path / ".gitignore").exists()
        assert (project_path / "run_pipeline.py").exists()
        
        # Check directories
        assert (project_path / "data").is_dir()
        assert (project_path / "docs").is_dir()
        assert (project_path / ".nai").is_dir()


def test_init_with_template():
    """Test init with minimal template."""
    with tempfile.TemporaryDirectory() as tmpdir:
        project_path = Path(tmpdir) / "test-minimal"
        
        result = runner.invoke(app, ["init", str(project_path), "--template", "minimal"])
        
        assert result.exit_code == 0
        assert (project_path / "config.yaml").exists()


def test_config_show():
    """Test config show command."""
    with tempfile.TemporaryDirectory() as tmpdir:
        # Create a test config
        config_path = Path(tmpdir) / "config.yaml"
        config_path.write_text("""
embeddings:
  provider: openai
  model: text-embedding-3-small
""")
        
        result = runner.invoke(app, ["config", "show", "--config", str(config_path)])
        
        assert result.exit_code == 0
        assert "embeddings:" in result.stdout
        assert "openai" in result.stdout


def test_config_get():
    """Test config get command."""
    with tempfile.TemporaryDirectory() as tmpdir:
        config_path = Path(tmpdir) / "config.yaml"
        config_path.write_text("""
generator:
  model: gpt-4o-mini
  temperature: 0.7
""")
        
        result = runner.invoke(app, ["config", "get", "generator.model", "--config", str(config_path)])
        
        assert result.exit_code == 0
        assert "gpt-4o-mini" in result.stdout


def test_config_set():
    """Test config set command."""
    with tempfile.TemporaryDirectory() as tmpdir:
        config_path = Path(tmpdir) / "config.yaml"
        config_path.write_text("""
generator:
  model: gpt-3.5-turbo
""")
        
        result = runner.invoke(
            app, 
            ["config", "set", "generator.model", "gpt-4", "--config", str(config_path)]
        )
        
        assert result.exit_code == 0
        assert "Set generator.model = gpt-4" in result.stdout
        
        # Verify the change
        import yaml
        with open(config_path) as f:
            config = yaml.safe_load(f)
        assert config["generator"]["model"] == "gpt-4"


@pytest.mark.skip(reason="Requires API keys")
def test_full_pipeline():
    """Test full pipeline flow (requires API keys)."""
    with tempfile.TemporaryDirectory() as tmpdir:
        project_path = Path(tmpdir) / "test-pipeline"
        
        # Init project
        result = runner.invoke(app, ["init", str(project_path)])
        assert result.exit_code == 0
        
        # Change to project directory
        import os
        original_cwd = os.getcwd()
        try:
            os.chdir(project_path)
            
            # Ingest documents
            result = runner.invoke(app, ["ingest", "./docs"])
            assert result.exit_code == 0
            
            # Run query
            result = runner.invoke(app, ["run", "What is NnennaAI?"])
            assert result.exit_code == 0
            assert "Answer" in result.stdout
            
        finally:
            os.chdir(original_cwd)