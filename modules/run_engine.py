"""Pipeline orchestration engine for NnennaAI."""

import json
import time
from pathlib import Path
from typing import List, Dict, Any, Optional, Union
from datetime import datetime
import logging
from dataclasses import dataclass, asdict
import hashlib

try:
    from langfuse import Langfuse
    from langfuse.decorators import observe, langfuse_context
    LANGFUSE_AVAILABLE = True
except ImportError:
    LANGFUSE_AVAILABLE = False
    logger.info("Langfuse not installed. Cost tracking will use fallback estimation.")

from modules.config import Settings
from modules.base import (
    EmbedderModule, 
    RetrieverModule, 
    GeneratorModule, 
    EvaluatorModule
)

# Module imports
from modules.embedders.openai import OpenAIEmbedder
from modules.retrievers.chroma import ChromaRetriever
from modules.generators.openai import GPT4Generator
from modules.evaluators.ragas import RAGASEvaluator, SimpleEvaluator

logger = logging.getLogger(__name__)


@dataclass
class RunContext:
    """Context for a single pipeline run."""
    run_id: str
    query: str
    timestamp: datetime
    config: Dict[str, Any]
    trace_enabled: bool = False
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization."""
        return {
            **asdict(self),
            "timestamp": self.timestamp.isoformat()
        }


@dataclass
class RunResult:
    """Result from a pipeline run."""
    run_id: str
    query: str
    answer: str
    contexts: List[Dict[str, Any]]
    metrics: Dict[str, Any]
    trace: List[Dict[str, Any]]
    duration_seconds: float
    timestamp: datetime
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization."""
        return {
            **asdict(self),
            "timestamp": self.timestamp.isoformat()
        }


class RunEngine:
    """Main pipeline orchestration engine.
    
    Coordinates the flow: query → embed → retrieve → generate → evaluate
    """
    
    # Module registry - maps provider names to classes
    EMBEDDER_REGISTRY = {
        "openai": OpenAIEmbedder
    }
    
    RETRIEVER_REGISTRY = {
        "chroma": ChromaRetriever
    }
    
    GENERATOR_REGISTRY = {
        "openai": GPT4Generator
    }
    
    EVALUATOR_REGISTRY = {
        "ragas": RAGASEvaluator,
        "simple": SimpleEvaluator,
        "exact_match": SimpleEvaluator
    }
    
    def __init__(self, settings: Optional[Settings] = None):
        """Initialize the pipeline engine.
        
        Args:
            settings: Configuration settings. If None, loads from default.
        """
        self.settings = settings or Settings()
        self.modules = {}
        self._setup_complete = False
        self._run_history = []
        
        # Create run directory
        self.run_dir = Path(self.settings.pipeline.run_dir)
        self.run_dir.mkdir(parents=True, exist_ok=True)
        
        # Initialize Langfuse if available and enabled
        self.langfuse = None
        self.langfuse_enabled = self.settings.pipeline.get("langfuse_enabled", True) and LANGFUSE_AVAILABLE
        
        if self.langfuse_enabled:
            try:
                self.langfuse = Langfuse()
                logger.info("Langfuse initialized for cost tracking")
            except Exception as e:
                logger.warning(f"Failed to initialize Langfuse: {e}")
                self.langfuse_enabled = False
        
        logger.info("Initialized RunEngine")
    
    def setup(self) -> None:
        """Initialize all pipeline modules."""
        if self._setup_complete:
            return
        
        logger.info("Setting up pipeline modules...")
        
        # Initialize embedder
        embedder_class = self.EMBEDDER_REGISTRY.get(self.settings.embeddings.provider)
        if not embedder_class:
            raise ValueError(f"Unknown embedder: {self.settings.embeddings.provider}")
        
        self.embedder = embedder_class(self.settings.embeddings.model_dump())
        self.embedder.setup()
        
        # Initialize retriever
        retriever_class = self.RETRIEVER_REGISTRY.get(self.settings.retriever.provider)
        if not retriever_class:
            raise ValueError(f"Unknown retriever: {self.settings.retriever.provider}")
        
        self.retriever = retriever_class(self.settings.retriever.model_dump())
        self.retriever.setup()
        
        # Initialize generator
        generator_class = self.GENERATOR_REGISTRY.get(self.settings.generator.provider)
        if not generator_class:
            raise ValueError(f"Unknown generator: {self.settings.generator.provider}")
        
        self.generator = generator_class(self.settings.generator.model_dump())
        self.generator.setup()
        
        # Initialize evaluator
        evaluator_class = self.EVALUATOR_REGISTRY.get(self.settings.eval.metric)
        if not evaluator_class:
            raise ValueError(f"Unknown evaluator: {self.settings.eval.metric}")
        
        self.evaluator = evaluator_class(self.settings.eval.model_dump())
        self.evaluator.setup()
        
        self._setup_complete = True
        logger.info("Pipeline setup complete")
    
    def _generate_run_id(self, query: str) -> str:
        """Generate unique run ID."""
        timestamp = datetime.now().isoformat()
        content = f"{query}{timestamp}"
        return hashlib.md5(content.encode()).hexdigest()[:12]
    
    def _trace(self, 
               run_context: RunContext, 
               step: str, 
               data: Dict[str, Any],
               duration: Optional[float] = None) -> Dict[str, Any]:
        """Create trace entry for a step."""
        trace_entry = {
            "step": step,
            "timestamp": datetime.now().isoformat(),
            "data": data
        }
        
        if duration is not None:
            trace_entry["duration_seconds"] = duration
        
        if run_context.trace_enabled:
            logger.info(f"[TRACE] {step}: {json.dumps(data, indent=2)}")
        
        return trace_entry
    
    def ingest(self, 
               documents: List[Union[str, Dict[str, Any]]],
               batch_size: int = 10) -> Dict[str, Any]:
        """Ingest documents into the vector store.
        
        Args:
            documents: List of documents (strings or dicts with 'text' and 'metadata')
            batch_size: Number of documents to process at once
            
        Returns:
            Ingestion statistics
        """
        if not self._setup_complete:
            self.setup()
        
        start_time = time.time()
        total_chunks = 0
        
        logger.info(f"Starting ingestion of {len(documents)} documents")
        
        # Process documents in batches
        for i in range(0, len(documents), batch_size):
            batch = documents[i:i + batch_size]
            
            # Extract texts and metadata
            texts = []
            metadata_list = []
            
            for doc in batch:
                if isinstance(doc, str):
                    texts.append(doc)
                    metadata_list.append({"source": "manual", "index": i + len(texts) - 1})
                elif isinstance(doc, dict):
                    texts.append(doc["text"])
                    metadata_list.append(doc.get("metadata", {"source": "manual"}))
                else:
                    logger.warning(f"Skipping invalid document type: {type(doc)}")
                    continue
            
            # Chunk texts if needed
            chunked_texts = []
            chunked_metadata = []
            
            chunk_size = self.settings.pipeline.chunk_size
            chunk_overlap = self.settings.pipeline.chunk_overlap
            
            for text, meta in zip(texts, metadata_list):
                # Simple chunking - in production, use langchain or similar
                chunks = self._simple_chunk_text(text, chunk_size, chunk_overlap)
                for j, chunk in enumerate(chunks):
                    chunked_texts.append(chunk)
                    chunked_metadata.append({
                        **meta,
                        "chunk_index": j,
                        "total_chunks": len(chunks)
                    })
            
            # Embed chunks
            logger.debug(f"Embedding {len(chunked_texts)} chunks")
            embeddings = self.embedder(chunked_texts)
            
            # Add to retriever
            self.retriever.add(chunked_texts, embeddings, chunked_metadata)
            total_chunks += len(chunked_texts)
            
            logger.info(f"Ingested batch {i//batch_size + 1}: {len(chunked_texts)} chunks")
        
        duration = time.time() - start_time
        
        stats = {
            "documents_processed": len(documents),
            "chunks_created": total_chunks,
            "duration_seconds": round(duration, 2),
            "chunks_per_second": round(total_chunks / duration, 2) if duration > 0 else 0,
            "retriever_count": self.retriever.count
        }
        
        logger.info(f"Ingestion complete: {stats}")
        return stats
    
    def _simple_chunk_text(self, 
                          text: str, 
                          chunk_size: int, 
                          overlap: int) -> List[str]:
        """Simple text chunking implementation."""
        if len(text) <= chunk_size:
            return [text]
        
        chunks = []
        start = 0
        
        while start < len(text):
            end = start + chunk_size
            chunk = text[start:end]
            chunks.append(chunk)
            start = end - overlap
        
        return chunks
    
    def run(self, 
            query: str,
            k: int = None,
            trace: bool = None) -> RunResult:
        """Execute the RAG pipeline.
        
        Args:
            query: User query
            k: Number of contexts to retrieve
            trace: Enable step-by-step tracing
            
        Returns:
            RunResult with answer and metadata
        """
        if not self._setup_complete:
            self.setup()
        
        # Create run context
        run_context = RunContext(
            run_id=self._generate_run_id(query),
            query=query,
            timestamp=datetime.now(),
            config=self.settings.model_dump(),
            trace_enabled=trace if trace is not None else self.settings.pipeline.trace
        )
        
        start_time = time.time()
        trace_log = []
        
        logger.info(f"Starting run {run_context.run_id} for query: {query}")
        
        # Start Langfuse trace if enabled
        langfuse_trace = None
        if self.langfuse_enabled and self.langfuse:
            langfuse_trace = self.langfuse.trace(
                name="rag_pipeline",
                user_id=run_context.run_id,
                metadata={
                    "pipeline_version": "0.1.0",
                    "config": run_context.config
                }
            )
        
        try:
            # Step 1: Embed query
            step_start = time.time()
            
            if langfuse_trace:
                embed_span = langfuse_trace.span(
                    name="embed_query",
                    input=query,
                    metadata={"model": self.settings.embeddings.model}
                )
            
            query_embedding = self.embedder([query])[0]
            embed_duration = time.time() - step_start
            
            if langfuse_trace:
                embed_span.end(
                    output={"embedding_dim": len(query_embedding)},
                    usage={"unit": "TOKENS", "input": len(query.split()) * 4}  # Rough estimate
                )
            
            trace_log.append(self._trace(
                run_context, 
                "embed_query",
                {"query": query, "embedding_dim": len(query_embedding)},
                embed_duration
            ))
            
            # Step 2: Retrieve contexts
            step_start = time.time()
            k = k or self.settings.pipeline.top_k
            
            if langfuse_trace:
                retrieve_span = langfuse_trace.span(
                    name="retrieve",
                    input={"k": k},
                    metadata={"retriever": self.settings.retriever.provider}
                )
            
            retrieved_docs = self.retriever(query_embedding, k=k)
            retrieve_duration = time.time() - step_start
            
            if langfuse_trace:
                retrieve_span.end(
                    output={
                        "num_retrieved": len(retrieved_docs),
                        "avg_score": sum(d["score"] for d in retrieved_docs) / len(retrieved_docs) if retrieved_docs else 0
                    }
                )
            
            trace_log.append(self._trace(
                run_context,
                "retrieve",
                {"k": k, "num_retrieved": len(retrieved_docs)},
                retrieve_duration
            ))
            
            # Step 3: Generate answer
            step_start = time.time()
            
            if langfuse_trace:
                generate_span = langfuse_trace.generation(
                    name="generate",
                    model=self.settings.generator.model,
                    input=[
                        {"role": "system", "content": self.settings.generator.system_prompt},
                        {"role": "user", "content": query}
                    ],
                    metadata={
                        "temperature": self.settings.generator.temperature,
                        "max_tokens": self.settings.generator.max_tokens,
                        "num_contexts": len(retrieved_docs)
                    }
                )
            
            answer = self.generator(
                query,
                context=retrieved_docs,
                use_rag_template=True,
                run_id=run_context.run_id  # Pass for tracking
            )
            generate_duration = time.time() - step_start
            
            # Get token usage from generator if available
            generator_stats = self.generator.get_stats()
            
            if langfuse_trace:
                generate_span.end(
                    output=answer,
                    usage={
                        "input": generator_stats.get("prompt_tokens", 0),
                        "output": generator_stats.get("completion_tokens", 0),
                        "total": generator_stats.get("prompt_tokens", 0) + generator_stats.get("completion_tokens", 0),
                        "unit": "TOKENS"
                    }
                )
            
            trace_log.append(self._trace(
                run_context,
                "generate",
                {"answer_length": len(answer), "model": self.settings.generator.model},
                generate_duration
            ))
            
            # Step 4: Create result
            total_duration = time.time() - start_time
            
            # Get cost from Langfuse or estimate
            if self.langfuse_enabled and langfuse_trace:
                langfuse_trace.update(
                    output=answer,
                    metadata={
                        "total_duration_seconds": total_duration,
                        "pipeline_successful": True
                    }
                )
                # Langfuse will calculate costs based on model pricing
                estimated_cost = None  # Will be available in Langfuse dashboard
            else:
                estimated_cost = self._estimate_cost()
            
            result = RunResult(
                run_id=run_context.run_id,
                query=query,
                answer=answer,
                contexts=retrieved_docs,
                metrics={
                    "latency": {
                        "total_seconds": round(total_duration, 3),
                        "embed_seconds": round(embed_duration, 3),
                        "retrieve_seconds": round(retrieve_duration, 3),
                        "generate_seconds": round(generate_duration, 3)
                    },
                    "retrieval": {
                        "num_contexts": len(retrieved_docs),
                        "avg_score": sum(d["score"] for d in retrieved_docs) / len(retrieved_docs) if retrieved_docs else 0
                    },
                    "generator": generator_stats,
                    "estimated_cost": estimated_cost,
                    "langfuse_enabled": self.langfuse_enabled
                },
                trace=trace_log,
                duration_seconds=total_duration,
                timestamp=run_context.timestamp
            )
            
            # Save run if configured
            if self.settings.pipeline.save_runs:
                self._save_run(result)
            
            self._run_history.append(result)
            logger.info(f"Run {run_context.run_id} complete in {total_duration:.2f}s")
            
            return result
            
        except Exception as e:
            logger.error(f"Pipeline run failed: {e}")
            
            if langfuse_trace:
                langfuse_trace.update(
                    metadata={
                        "pipeline_successful": False,
                        "error": str(e)
                    }
                )
            
            raise
    
    def score(self,
              query: str,
              ground_truth: Optional[str] = None,
              k: int = None) -> Dict[str, Any]:
        """Run pipeline and evaluate the output.
        
        Args:
            query: User query
            ground_truth: Expected answer for evaluation
            k: Number of contexts to retrieve
            
        Returns:
            Dictionary with run result and evaluation scores
        """
        # Run pipeline
        result = self.run(query, k=k)
        
        # Start Langfuse score if enabled
        if self.langfuse_enabled and self.langfuse:
            score_trace = self.langfuse.trace(
                name="rag_evaluation",
                user_id=result.run_id,
                metadata={
                    "evaluator": self.settings.eval.metric,
                    "has_ground_truth": ground_truth is not None
                }
            )
        else:
            score_trace = None
        
        # Evaluate
        eval_scores = self.evaluator.evaluate(
            query=query,
            prediction=result.answer,
            contexts=[doc["text"] for doc in result.contexts],
            ground_truth=ground_truth
        )
        
        # Log evaluation to Langfuse
        if score_trace:
            score_trace.score(
                name="overall_score",
                value=eval_scores.get("overall_score", 0),
                comment=f"Evaluated with {self.settings.eval.metric}"
            )
            
            # Log individual metrics as scores
            for metric, value in eval_scores.items():
                if metric not in ["overall_score", "passed", "error"]:
                    score_trace.score(
                        name=metric,
                        value=value
                    )
        
        # Combine results
        return {
            "run_id": result.run_id,
            "query": query,
            "answer": result.answer,
            "evaluation": eval_scores,
            "metrics": result.metrics,
            "timestamp": result.timestamp.isoformat()
        }
    
    def _estimate_cost(self) -> float:
        """Estimate total cost of the run."""
        embed_cost = self.embedder.estimated_cost if hasattr(self.embedder, "estimated_cost") else 0
        generate_cost = self.generator.estimated_cost if hasattr(self.generator, "estimated_cost") else 0
        return round(embed_cost + generate_cost, 5)
    
    def _save_run(self, result: RunResult) -> None:
        """Save run result to disk."""
        run_file = self.run_dir / f"run_{result.run_id}.json"
        
        with open(run_file, "w") as f:
            json.dump(result.to_dict(), f, indent=2)
        
        logger.debug(f"Saved run to {run_file}")
    
    def get_run_history(self) -> List[RunResult]:
        """Get history of runs from this session."""
        return self._run_history
    
    def teardown(self) -> None:
        """Clean up pipeline resources."""
        logger.info("Tearing down pipeline modules...")
        
        for module_name, module in [
            ("embedder", self.embedder),
            ("retriever", self.retriever),
            ("generator", self.generator),
            ("evaluator", self.evaluator)
        ]:
            if hasattr(self, module_name):
                module.teardown()
        
        self._setup_complete = False
        logger.info("Pipeline teardown complete")