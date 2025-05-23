# modules/base.py
"""Base module interface for all NnennaAI components."""

from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional
import time
import logging
# TODO: Add import for Langfuse and refactor to be Pythonic

logger = logging.getLogger(__name__)


class BaseModule(ABC):
    """
    Base class for all NnennaAI modules.
    
    Every module must implement:
    - setup(): Initialize resources
    - __call__(): Main execution
    - teardown(): Cleanup resources
    """
    
    # Version tag for compatibility checking
    implements: str = "nai.module.base@1.0.0"
    
    def __init__(self, config: Dict[str, Any]):
        """Initialize module with configuration."""
        self.config = config
        self._setup_complete = False
        self._metrics = {
            "calls": 0,
            "total_time": 0.0,
            "errors": 0
        }
        # Optional Langfuse integration
        self.langfuse_enabled = config.get("langfuse_enabled", False)
        if self.langfuse_enabled:
            from langfuse import Langfuse
            self.langfuse = Langfuse()
    
    def setup(self) -> None:
        """
        Initialize module resources.
        Called once before first use.
        """
        logger.info(f"Setting up {self.__class__.__name__}")
        self._setup_complete = True
    
    @abstractmethod
    def __call__(self, *args, **kwargs) -> Any:
        """
        Main execution method.
        Must be implemented by all modules.
        """
        pass
    
    def teardown(self) -> None:
        """
        Clean up module resources.
        Called on shutdown.
        """
        logger.info(f"Tearing down {self.__class__.__name__}")
        self._setup_complete = False
    
    def _track_metrics(self, func):
        """Decorator to track module metrics."""
        def wrapper(*args, **kwargs):
            start_time = time.time()
            try:
                result = func(*args, **kwargs)
                self._metrics["calls"] += 1
                self._metrics["total_time"] += time.time() - start_time
                return result
            except Exception as e:
                self._metrics["errors"] += 1
                raise e
        return wrapper
    
    @property
    def metrics(self) -> Dict[str, Any]:
        """Return module performance metrics."""
        return {
            **self._metrics,
            "avg_time": self._metrics["total_time"] / max(1, self._metrics["calls"])
        }


class EmbedderModule(BaseModule):
    """Base class for embedding modules."""
    
    implements = "nai.module.embedder@1.0.0"
    
    @abstractmethod
    def __call__(self, texts: List[str]) -> List[List[float]]:
        """
        Convert texts to embeddings.
        
        Args:
            texts: List of strings to embed
            
        Returns:
            List of embedding vectors
        """
        pass


class RetrieverModule(BaseModule):
    """Base class for retriever modules."""
    
    implements = "nai.module.retriever@1.0.0"
    
    @abstractmethod
    def add(self, texts: List[str], embeddings: List[List[float]], 
            metadata: Optional[List[Dict]] = None) -> None:
        """Add documents to the retriever."""
        pass
    
    @abstractmethod
    def __call__(self, query_embedding: List[float], k: int = 5) -> List[Dict[str, Any]]:
        """
        Retrieve relevant documents.
        
        Args:
            query_embedding: Query vector
            k: Number of results to return
            
        Returns:
            List of documents with text, score, and metadata
        """
        pass


class GeneratorModule(BaseModule):
    """Base class for LLM/generator modules."""
    
    implements = "nai.module.generator@1.0.0"
    
    @abstractmethod
    def __call__(self, prompt: str, **kwargs) -> str:
        """
        Generate text from prompt.
        
        Args:
            prompt: Input prompt
            **kwargs: Additional generation parameters
            
        Returns:
            Generated text
        """
        pass


class EvaluatorModule(BaseModule):
    """Base class for evaluation modules."""
    
    implements = "nai.module.evaluator@1.0.0"
    
    @abstractmethod
    def evaluate(self, 
                 query: str,
                 prediction: str, 
                 contexts: List[str],
                 ground_truth: Optional[str] = None) -> Dict[str, float]:
        """
        Evaluate generated output.
        
        Args:
            query: Original query
            prediction: Generated answer
            contexts: Retrieved contexts used
            ground_truth: Optional ground truth answer
            
        Returns:
            Dictionary of metric scores
        """
        pass
    
    def __call__(self, *args, **kwargs):
        """Alias for evaluate method."""
        return self.evaluate(*args, **kwargs)