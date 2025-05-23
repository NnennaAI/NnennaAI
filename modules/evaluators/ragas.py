# modules/evaluators/ragas.py
"""RAGAS evaluation module implementation."""

from typing import Dict, List, Optional, Any
import logging
from datasets import Dataset
import pandas as pd
import logging

logger = logging.getLogger(__name__)

try:
    from ragas import evaluate
    from ragas.metrics import (
        faithfulness,
        answer_relevancy,
        context_precision,
        context_recall,
        context_relevancy,
        answer_similarity,
        answer_correctness
    )
    RAGAS_AVAILABLE = True
except ImportError:
    RAGAS_AVAILABLE = False
    logger.warning("RAGAS not installed. Install with: pip install ragas")

from modules.base import EvaluatorModule



class RAGASEvaluator(EvaluatorModule):
    """
    RAGAS evaluation framework integration.
    
    Uses the official RAGAS library for comprehensive RAG evaluation.
    """
    
    implements = "nai.module.evaluator.ragas@1.0.0"
    
    def setup(self) -> None:
        """Initialize RAGAS evaluator."""
        super().setup()
        
        if not RAGAS_AVAILABLE:
            raise ImportError(
                "RAGAS is not installed. Install it with:\n"
                "pip install ragas"
            )
        
        # Configure which metrics to use
        metric_names = self.config.get(
            "ragas_metrics", 
            ["faithfulness", "answer_relevancy", "context_precision"]
        )
        
        # Map string names to RAGAS metric objects
        metric_map = {
            "faithfulness": faithfulness,
            "answer_relevancy": answer_relevancy,
            "context_precision": context_precision,
            "context_recall": context_recall,
            "context_relevancy": context_relevancy,
            "answer_similarity": answer_similarity,
            "answer_correctness": answer_correctness
        }
        
        self.metrics = []
        for metric_name in metric_names:
            if metric_name in metric_map:
                self.metrics.append(metric_map[metric_name])
            else:
                logger.warning(f"Unknown metric: {metric_name}")
        
        if not self.metrics:
            # Default to core metrics
            self.metrics = [faithfulness, answer_relevancy, context_precision]
        
        logger.info(f"Initialized RAGAS evaluator with metrics: {[m.name for m in self.metrics]}")
    
    def evaluate(self, 
                 query: str,
                 prediction: str, 
                 contexts: List[str],
                 ground_truth: Optional[str] = None) -> Dict[str, float]:
        """
        Evaluate generated output using RAGAS.
        
        Args:
            query: Original query
            prediction: Generated answer
            contexts: Retrieved contexts used
            ground_truth: Optional ground truth answer
            
        Returns:
            Dictionary of metric scores
        """
        if not self._setup_complete:
            self.setup()
        
        @self._track_metrics
        def _evaluate():
            # Prepare data in RAGAS format
            eval_data = {
                "question": [query],
                "answer": [prediction],
                "contexts": [contexts],
            }
            
            # Add ground truth if available
            if ground_truth:
                eval_data["ground_truth"] = [ground_truth]
            
            # Create dataset
            dataset = Dataset.from_dict(eval_data)
            
            # Run evaluation
            try:
                results = evaluate(
                    dataset=dataset,
                    metrics=self.metrics,
                    raise_exceptions=False
                )
                
                # Extract scores
                scores = {}
                for metric in self.metrics:
                    metric_name = metric.name
                    if metric_name in results:
                        scores[metric_name] = float(results[metric_name])
                
                # Calculate overall score
                if scores:
                    scores["overall_score"] = round(sum(scores.values()) / len(scores), 3)
                else:
                    scores["overall_score"] = 0.0
                
                # Add threshold check
                threshold = self.config.get("threshold", 0.7)
                scores["passed"] = scores["overall_score"] >= threshold
                
                logger.info(f"RAGAS evaluation complete. Score: {scores['overall_score']}")
                return scores
                
            except Exception as e:
                logger.error(f"RAGAS evaluation failed: {e}")
                # Return zero scores on failure
                return {
                    metric.name: 0.0 for metric in self.metrics
                } | {"overall_score": 0.0, "passed": False, "error": str(e)}
        
        return _evaluate()
    
    def batch_evaluate(self, 
                      queries: List[str],
                      predictions: List[str],
                      contexts_list: List[List[str]],
                      ground_truths: Optional[List[str]] = None) -> Dict[str, Any]:
        """
        Evaluate multiple examples using RAGAS.
        
        Args:
            queries: List of queries
            predictions: List of generated answers
            contexts_list: List of context lists
            ground_truths: Optional list of ground truth answers
            
        Returns:
            Dictionary with individual and aggregated metrics
        """
        if not self._setup_complete:
            self.setup()
        
        # Prepare batch data
        eval_data = {
            "question": queries,
            "answer": predictions,
            "contexts": contexts_list,
        }
        
        if ground_truths:
            eval_data["ground_truth"] = ground_truths
        
        # Create dataset
        dataset = Dataset.from_dict(eval_data)
        
        try:
            # Run batch evaluation
            results = evaluate(
                dataset=dataset,
                metrics=self.metrics,
                raise_exceptions=False
            )
            
            # Convert to pandas for easier manipulation
            df = results.to_pandas()
            
            # Calculate aggregated metrics
            aggregated = {}
            for metric in self.metrics:
                metric_name = metric.name
                if metric_name in df.columns:
                    aggregated[f"{metric_name}_mean"] = float(df[metric_name].mean())
                    aggregated[f"{metric_name}_std"] = float(df[metric_name].std())
                    aggregated[f"{metric_name}_min"] = float(df[metric_name].min())
                    aggregated[f"{metric_name}_max"] = float(df[metric_name].max())
            
            # Calculate pass rate
            threshold = self.config.get("threshold", 0.7)
            overall_scores = []
            for idx in range(len(queries)):
                row_scores = [df.iloc[idx][m.name] for m in self.metrics if m.name in df.columns]
                overall = sum(row_scores) / len(row_scores) if row_scores else 0.0
                overall_scores.append(overall)
            
            aggregated["overall_score_mean"] = sum(overall_scores) / len(overall_scores)
            aggregated["pass_rate"] = sum(1 for s in overall_scores if s >= threshold) / len(overall_scores)
            
            # Get individual results
            individual_results = []
            for idx in range(len(queries)):
                result = {
                    m.name: float(df.iloc[idx][m.name]) 
                    for m in self.metrics 
                    if m.name in df.columns
                }
                result["overall_score"] = overall_scores[idx]
                result["passed"] = overall_scores[idx] >= threshold
                individual_results.append(result)
            
            return {
                "individual_results": individual_results,
                "aggregated_metrics": aggregated,
                "num_examples": len(queries),
                "ragas_dataframe": df  # Include raw results
            }
            
        except Exception as e:
            logger.error(f"Batch RAGAS evaluation failed: {e}")
            return {
                "error": str(e),
                "individual_results": [],
                "aggregated_metrics": {},
                "num_examples": 0
            }
    
    def get_stats(self) -> Dict[str, Any]:
        """Get evaluation statistics."""
        return {
            "metrics_computed": [m.name for m in self.metrics],
            "threshold": self.config.get("threshold", 0.7),
            "evaluations_run": self._metrics["calls"],
            "ragas_version": "latest",  # Could get actual version
            **self.metrics
        }


class SimpleEvaluator(EvaluatorModule):
    """
    Fallback evaluator when RAGAS is not available.
    
    Provides basic exact match and similarity scoring.
    """
    
    implements = "nai.module.evaluator.simple@1.0.0"
    
    def evaluate(self, 
                 query: str,
                 prediction: str, 
                 contexts: List[str],
                 ground_truth: Optional[str] = None) -> Dict[str, float]:
        """
        Simple evaluation using string matching.
        
        Args:
            query: Original query
            prediction: Generated answer  
            contexts: Retrieved contexts
            ground_truth: Optional ground truth answer
            
        Returns:
            Dictionary with basic metrics
        """
        results = {}
        
        # Check if answer is non-empty
        results["has_answer"] = 1.0 if prediction and len(prediction.strip()) > 0 else 0.0
        
        # Check if answer references context
        if contexts and prediction:
            context_text = " ".join(contexts).lower()
            answer_words = set(prediction.lower().split())
            context_words = set(context_text.split())
            overlap = len(answer_words.intersection(context_words)) / len(answer_words)
            results["uses_context"] = min(1.0, overlap)
        else:
            results["uses_context"] = 0.0
        
        # Exact match if ground truth provided
        if ground_truth:
            results["exact_match"] = 1.0 if prediction.strip().lower() == ground_truth.strip().lower() else 0.0
        
        # Overall score
        results["overall_score"] = sum(results.values()) / len(results)
        results["passed"] = results["overall_score"] >= self.config.get("threshold", 0.5)
        
        return results