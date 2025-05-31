"""NnennaAI modules package.

Core components for building GenAI pipelines.
"""

from modules.base import (
    BaseModule,
    EmbedderModule,
    RetrieverModule,
    GeneratorModule,
    EvaluatorModule
)
from modules.config import Settings, get_settings, set_settings
from modules.run_engine import RunEngine, RunResult, RunContext

__version__ = "0.1.0"

__all__ = [
    # Base classes
    "BaseModule",
    "EmbedderModule",
    "RetrieverModule", 
    "GeneratorModule",
    "EvaluatorModule",
    
    # Configuration
    "Settings",
    "get_settings",
    "set_settings",
    
    # Engine
    "RunEngine",
    "RunResult",
    "RunContext",
]