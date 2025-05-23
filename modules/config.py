# modules/config.py
"""Configuration management for NnennaAI."""

from pydantic import BaseModel, Field
from pathlib import Path
from typing import Literal, Optional, Dict, Any
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()


class EmbeddingSettings(BaseModel):
    """Embedding module configuration."""
    provider: Literal["openai"] = "openai"
    model: str = "text-embedding-3-small"
    api_key: Optional[str] = Field(default_factory=lambda: os.getenv("OPENAI_API_KEY"))
    batch_size: int = 100


class RetrieverSettings(BaseModel):
    """Retriever module configuration."""
    provider: Literal["chroma"] = "chroma"
    persist_dir: Path = Path(".nai/chroma")
    collection: str = "nai_docs"
    distance_metric: Literal["cosine", "l2", "ip"] = "cosine"


class GeneratorSettings(BaseModel):
    """Generator/LLM module configuration."""
    provider: Literal["openai"] = "openai"
    model: str = "gpt-4o-mini"
    api_key: Optional[str] = Field(default_factory=lambda: os.getenv("OPENAI_API_KEY"))
    temperature: float = 0.7
    max_tokens: int = 1000
    system_prompt: str = "You are a helpful AI assistant."


class EvalSettings(BaseModel):
    """Evaluation module configuration."""
    metric: Literal["ragas", "exact_match"] = "ragas"
    ragas_metrics: list[str] = ["faithfulness", "answer_relevancy", "context_precision"]
    threshold: float = 0.7


class PipelineSettings(BaseModel):
    """Pipeline execution settings."""
    chunk_size: int = 400
    chunk_overlap: int = 50
    top_k: int = 5
    trace: bool = False
    save_runs: bool = True
    run_dir: Path = Path(".nai/runs")


class Settings(BaseModel):
    """Main configuration container."""
    embeddings: EmbeddingSettings = Field(default_factory=EmbeddingSettings)
    retriever: RetrieverSettings = Field(default_factory=RetrieverSettings)
    generator: GeneratorSettings = Field(default_factory=GeneratorSettings)
    eval: EvalSettings = Field(default_factory=EvalSettings)
    pipeline: PipelineSettings = Field(default_factory=PipelineSettings)
    
    @classmethod
    def from_yaml(cls, path: Path) -> "Settings":
        """Load settings from YAML file."""
        import yaml
        
        if not path.exists():
            return cls()
        
        with open(path) as f:
            data = yaml.safe_load(f)
        
        return cls(**data) if data else cls()
    
    def to_yaml(self, path: Path) -> None:
        """Save settings to YAML file."""
        import yaml
        
        path.parent.mkdir(parents=True, exist_ok=True)
        
        with open(path, 'w') as f:
            yaml.dump(self.model_dump(exclude_none=True), f, default_flow_style=False)
    
    def merge_with_cli(self, **cli_args) -> "Settings":
        """Merge CLI arguments with current settings."""
        # Remove None values
        cli_args = {k: v for k, v in cli_args.items() if v is not None}
        
        # Update nested settings
        current = self.model_dump()
        for key, value in cli_args.items():
            if '.' in key:
                # Handle nested keys like "generator.model"
                parts = key.split('.')
                target = current
                for part in parts[:-1]:
                    target = target.setdefault(part, {})
                target[parts[-1]] = value
            else:
                current[key] = value
        
        return Settings(**current)


# Global settings instance
_settings: Optional[Settings] = None


def get_settings() -> Settings:
    """Get or create global settings instance."""
    global _settings
    
    if _settings is None:
        # Load from default locations
        config_paths = [
            Path(".nai.yaml"),
            Path.home() / ".nai.yaml",
            Path(".") / "config.yaml"
        ]
        
        for path in config_paths:
            if path.exists():
                _settings = Settings.from_yaml(path)
                break
        else:
            _settings = Settings()
    
    return _settings


def set_settings(settings: Settings) -> None:
    """Update global settings instance."""
    global _settings
    _settings = settings