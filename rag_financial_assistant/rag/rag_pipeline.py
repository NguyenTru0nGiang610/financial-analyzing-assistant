import json
import os
import logging

import yaml
import mlflow

from retrieval.retriever import Retriever
from rag.prompt_template import build_prompt, build_dynamic_prompt
from rag.generator import DeepSeekGenerator, LocalLLMGenerator
from tools.searching_tool import SearchTool
from ingestion.build_index import build_index
logger = logging.getLogger(__name__)


class RAGPipeline:

    def __init__(self):

        config = yaml.safe_load(open("config.yaml"))

        self.retriever = Retriever(config)
        # self.generator = LocalLLMGenerator()
        self.generator = DeepSeekGenerator()
        self.search_tool = SearchTool()
        # Score threshold configuration
        self.score_threshold = config.get("rag", {}).get("score_threshold", 0.5)
        self.low_confidence_threshold = config.get("rag", {}).get("low_confidence_threshold", 0.6)
        self.high_confidence_threshold = config.get("rag", {}).get("high_confidence_threshold", 0.8)
        self.max_search_retries = config.get("rag", {}).get("max_search_retries", 2)

    def _calculate_average_score(self, contexts):
        """Calculate average retrieval score from contexts."""
        if not contexts:
            return 0.0
        scores = [c.get("score", 0.0) for c in contexts]
        return sum(scores) / len(scores) if scores else 0.0

    def _get_confidence_level(self, avg_score):
        """Determine confidence level based on average score."""
        if avg_score >= self.high_confidence_threshold:
            return "high"
        elif avg_score >= self.low_confidence_threshold:
            return "medium"
        else:
            return "low"

    def _should_trigger_search(self, avg_score, contexts):
        """Determine if search tool should be triggered."""
        # Trigger if average score is below threshold
        if avg_score < self.score_threshold:
            return True
        
        # Trigger if all contexts have low scores
        if contexts and all(c.get("score", 0.0) < self.low_confidence_threshold for c in contexts):
            return True
        
        return False


    def run(self, query):
        """Run RAG pipeline with score-based threshold checking."""
        contexts = self.retriever.retrieve(query)
        
        # Calculate average score
        avg_score = self._calculate_average_score(contexts)
        confidence_level = self._get_confidence_level(avg_score)
        
        # Log metrics
        # mlflow.log_metric("retrieval_avg_score", avg_score)
        # mlflow.log_param("confidence_level", confidence_level)
        # mlflow.log_param("contexts_count", len(contexts))
        
  
        # if self._should_trigger_search(avg_score, contexts):
            # logger.info(f"Low confidence score ({avg_score:.2f}), triggering search tool")
            # search_results = self.search_tool.run(query)
            # self.index_builder.run()
            # search_contexts = self.retriever.retrieve(query) 
            # contexts.extend(search_contexts)
            # # Recalculate average score after search
            # avg_score = self._calculate_average_score(contexts)
            # confidence_level = self._get_confidence_level(avg_score)
            # mlflow.log_metric("retrieval_avg_score_after_search", avg_score)
            # mlflow.log_param("confidence_level_after_search", confidence_level)
            # mlflow.log_param("search_results_count", len(search_results))
        return self.run_with_contexts(query, contexts, confidence_level)

    def run_with_contexts(self, query, contexts, confidence_level="medium"):
        """Generate answer with dynamic prompt based on confidence level."""
        # Validate and clean contexts
        valid_contexts = []
        for ctx in contexts:
            if isinstance(ctx, dict) and "text" in ctx:
                # Ensure text is not empty and is a string
                text = str(ctx.get("text", "")).strip()
                if text:
                    ctx["text"] = text[:2000]  # Limit context length to prevent token overflow
                    valid_contexts.append(ctx)
        
        if not valid_contexts:
            logger.warning("No valid contexts found, using empty context")
            valid_contexts = [{"text": "No relevant context available.", "score": 0.0}]
        
        prompt = build_dynamic_prompt(query, valid_contexts, confidence_level)
        
        # Validate prompt length (max 3000 tokens approximately)
        if len(prompt) > 12000:  # Rough estimate: 1 token ≈ 4 chars
            logger.warning(f"Prompt too long ({len(prompt)} chars), truncating contexts")
            valid_contexts = valid_contexts[:3]  # Reduce to top 3 contexts
            prompt = build_dynamic_prompt(query, valid_contexts, confidence_level)
        
        answer = self.generator.generate(prompt)
        
        # Log the response
        # mlflow.log_text(f"Query: {query}", "query.txt")
        # mlflow.log_text(f"Answer: {answer}", "answer.txt")

        return answer, valid_contexts

