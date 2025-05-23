# modules/generators/openai.py
"""OpenAI LLM generator module implementation."""

from typing import Dict, Any, Optional, List
import openai
from tenacity import retry, stop_after_attempt, wait_exponential
import logging
import json
# TODO: Refactor to be Pythonic if needed
try:
    from langfuse import Langfuse
    LANGFUSE_AVAILABLE = True
except ImportError:
    LANGFUSE_AVAILABLE = False

from modules.base import GeneratorModule

logger = logging.getLogger(__name__)


class GPT4Generator(GeneratorModule):
    """
    OpenAI GPT-4 generator for high-quality responses.
    
    Supports both standard and RAG-specific prompting.
    """
    
    implements = "nai.module.generator.openai@1.0.0"
    
    # Default RAG prompt template
    DEFAULT_RAG_TEMPLATE = """You are a helpful AI assistant. Answer the user's question based on the provided context.

Context:
{context}

Question: {query}

Instructions:
- Use only information from the context to answer
- If the context doesn't contain enough information, say so
- Be concise but complete
- Cite which part of the context supports your answer when relevant

Answer:"""
    
    def setup(self) -> None:
        """Initialize OpenAI client."""
        super().setup()
        
        if not self.config.get("api_key"):
            raise ValueError("OpenAI API key not found. Set OPENAI_API_KEY env var.")
        
        self.client = openai.OpenAI(api_key=self.config["api_key"])
        self.model = self.config.get("model", "gpt-4o-mini")
        self.temperature = self.config.get("temperature", 0.7)
        self.max_tokens = self.config.get("max_tokens", 1000)
        self.system_prompt = self.config.get("system_prompt", "You are a helpful AI assistant.")
        
        # Initialize Langfuse if available and enabled
        self.langfuse = None
        self.langfuse_enabled = self.config.get("langfuse_enabled", True) and LANGFUSE_AVAILABLE
        
        if self.langfuse_enabled:
            try:
                self.langfuse = Langfuse()
                logger.info(f"Langfuse enabled for {self.model} generator")
            except Exception as e:
                logger.warning(f"Failed to initialize Langfuse: {e}")
                self.langfuse_enabled = False
        
        logger.info(f"Initialized OpenAI generator with model: {self.model}")
    
    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(min=1, max=10),
        reraise=True
    )
    def _generate(self, messages: List[Dict[str, str]], **kwargs) -> str:
        """Generate response with retry logic."""
        response = self.client.chat.completions.create(
            model=self.model,
            messages=messages,
            temperature=kwargs.get("temperature", self.temperature),
            max_tokens=kwargs.get("max_tokens", self.max_tokens),
            n=1
        )
        
        # Store response for Langfuse usage tracking
        self._last_response = response
        
        # Track token usage
        if response.usage:
            self._metrics["prompt_tokens"] = self._metrics.get("prompt_tokens", 0) + response.usage.prompt_tokens
            self._metrics["completion_tokens"] = self._metrics.get("completion_tokens", 0) + response.usage.completion_tokens
        
        return response.choices[0].message.content
    
    def __call__(self, prompt: str, **kwargs) -> str:
        """
        Generate text from prompt.
        
        Args:
            prompt: Input prompt or query
            context: Optional context for RAG (list of retrieved docs)
            use_rag_template: Whether to use RAG-specific formatting
            run_id: Optional run ID for tracking
            **kwargs: Additional generation parameters
            
        Returns:
            Generated text
        """
        if not self._setup_complete:
            self.setup()
        
        @self._track_metrics
        def _generate_response():
            # Extract run_id if provided
            run_id = kwargs.pop("run_id", None)
            
            # Handle RAG-specific formatting
            if kwargs.get("use_rag_template", False) and "context" in kwargs:
                # Format context from retrieved documents
                context_texts = []
                for i, doc in enumerate(kwargs["context"]):
                    text = doc.get("text", "") if isinstance(doc, dict) else str(doc)
                    context_texts.append(f"[{i+1}] {text}")
                
                context_str = "\n\n".join(context_texts)
                
                # Use RAG template
                template = kwargs.get("rag_template", self.DEFAULT_RAG_TEMPLATE)
                formatted_prompt = template.format(
                    context=context_str,
                    query=prompt
                )
                
                messages = [
                    {"role": "system", "content": self.system_prompt},
                    {"role": "user", "content": formatted_prompt}
                ]
            else:
                # Standard generation
                messages = [
                    {"role": "system", "content": self.system_prompt},
                    {"role": "user", "content": prompt}
                ]
            
            # Start Langfuse generation tracking if enabled
            langfuse_generation = None
            if self.langfuse_enabled and self.langfuse:
                try:
                    langfuse_generation = self.langfuse.generation(
                        name="openai_generation",
                        model=self.model,
                        input=messages,
                        metadata={
                            "temperature": kwargs.get("temperature", self.temperature),
                            "max_tokens": kwargs.get("max_tokens", self.max_tokens),
                            "run_id": run_id,
                            "use_rag_template": kwargs.get("use_rag_template", False)
                        }
                    )
                except Exception as e:
                    logger.warning(f"Failed to start Langfuse generation: {e}")
            
            # Generate response
            try:
                response = self._generate(messages, **kwargs)
                
                # Update Langfuse with response and usage
                if langfuse_generation and hasattr(self, '_last_response'):
                    try:
                        usage_data = None
                        if self._last_response.usage:
                            usage_data = {
                                "input": self._last_response.usage.prompt_tokens,
                                "output": self._last_response.usage.completion_tokens,
                                "total": self._last_response.usage.total_tokens,
                                "unit": "TOKENS"
                            }
                        
                        langfuse_generation.end(
                            output=response,
                            usage=usage_data,
                            level="DEFAULT",
                            status_message="Success"
                        )
                    except Exception as e:
                        logger.warning(f"Failed to update Langfuse generation: {e}")
                
                logger.debug(f"Generated response of length: {len(response)}")
                return response
                
            except Exception as e:
                # Log error to Langfuse
                if langfuse_generation:
                    try:
                        langfuse_generation.end(
                            level="ERROR",
                            status_message=str(e)
                        )
                    except:
                        pass
                raise
        
        return _generate_response()
    
    @property
    def estimated_cost(self) -> float:
        """Estimate total cost based on token usage."""
        # Pricing as of 2024 (per 1K tokens)
        pricing = {
            "gpt-4o": {"prompt": 0.005, "completion": 0.015},
            "gpt-4o-mini": {"prompt": 0.00015, "completion": 0.0006},
            "gpt-4-turbo": {"prompt": 0.01, "completion": 0.03},
            "gpt-3.5-turbo": {"prompt": 0.0005, "completion": 0.0015}
        }
        
        model_pricing = pricing.get(self.model, pricing["gpt-4o-mini"])
        
        prompt_cost = (self._metrics.get("prompt_tokens", 0) / 1000) * model_pricing["prompt"]
        completion_cost = (self._metrics.get("completion_tokens", 0) / 1000) * model_pricing["completion"]
        
        return prompt_cost + completion_cost
    
    def get_stats(self) -> Dict[str, Any]:
        """Get generation statistics."""
        stats = {
            "model": self.model,
            "total_tokens": self._metrics.get("prompt_tokens", 0) + self._metrics.get("completion_tokens", 0),
            "prompt_tokens": self._metrics.get("prompt_tokens", 0),
            "completion_tokens": self._metrics.get("completion_tokens", 0),
            "estimated_cost": f"${self.estimated_cost:.4f}",
            "langfuse_enabled": self.langfuse_enabled,
            **self.metrics
        }
        
        # If Langfuse is enabled, note that precise costs are in Langfuse dashboard
        if self.langfuse_enabled:
            stats["cost_tracking"] = "Precise costs available in Langfuse dashboard"
        
        return stats