# modules/embedders/openai.py
"""OpenAI embedding module implementation."""

from typing import List, Dict, Any
import openai
from tenacity import retry, stop_after_attempt, wait_exponential
import logging

from modules.base import EmbedderModule

logger = logging.getLogger(__name__)
# TODO: Add import for Langfuse & refactor to be Pythonic

class OpenAIEmbedder(EmbedderModule):
    """
    OpenAI embeddings using text-embedding-3-small.
    
    Fast, affordable, and high-quality embeddings.
    """
    
    implements = "nai.module.embedder.openai@1.0.0"
    
    def setup(self) -> None:
        """Initialize OpenAI client."""
        super().setup()
        
        if not self.config.get("api_key"):
            raise ValueError("OpenAI API key not found. Set OPENAI_API_KEY env var.")
        
        self.client = openai.OpenAI(api_key=self.config["api_key"])
        self.model = self.config.get("model", "text-embedding-3-small")
        self.batch_size = self.config.get("batch_size", 100)
        
        logger.info(f"Initialized OpenAI embedder with model: {self.model}")
    
    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(min=1, max=10),
        reraise=True
    )
    def _embed_batch(self, texts: List[str]) -> List[List[float]]:
        """Embed a batch of texts with retry logic."""
        response = self.client.embeddings.create(
            model=self.model,
            input=texts
        )
        
        return [item.embedding for item in response.data]
    
    def __call__(self, texts: List[str]) -> List[List[float]]:
        """
        Embed texts into vectors.
        
        Args:
            texts: List of strings to embed
            
        Returns:
            List of embedding vectors
        """
        if not self._setup_complete:
            self.setup()
        
        if not texts:
            return []
        
        # Track metrics
        @self._track_metrics
        def _embed_all():
            embeddings = []
            
            # Process in batches
            for i in range(0, len(texts), self.batch_size):
                batch = texts[i:i + self.batch_size]
                logger.debug(f"Embedding batch {i//self.batch_size + 1} of {len(texts)//self.batch_size + 1}")
                
                batch_embeddings = self._embed_batch(batch)
                embeddings.extend(batch_embeddings)
            
            logger.info(f"Embedded {len(texts)} texts using {self.model}")
            
            # Track token usage for cost estimation
            # Rough estimate: ~4 tokens per word, ~75 words per chunk
            estimated_tokens = sum(len(text.split()) * 4 for text in texts)
            self._metrics["total_tokens"] = self._metrics.get("total_tokens", 0) + estimated_tokens
            
            return embeddings
        
        return _embed_all()
    
    @property
    def embedding_dim(self) -> int:
        """Return embedding dimension for this model."""
        model_dims = {
            "text-embedding-3-small": 1536,
            "text-embedding-3-large": 3072,
            "text-embedding-ada-002": 1536
        }
        return model_dims.get(self.model, 1536)
    
    @property
    def estimated_cost(self) -> float:
        """Estimate total cost based on token usage."""
        # Pricing as of 2024
        cost_per_1k_tokens = {
            "text-embedding-3-small": 0.00002,
            "text-embedding-3-large": 0.00013,
            "text-embedding-ada-002": 0.0001
        }
        
        tokens = self._metrics.get("total_tokens", 0)
        rate = cost_per_1k_tokens.get(self.model, 0.00002)
        
        return (tokens / 1000) * rate