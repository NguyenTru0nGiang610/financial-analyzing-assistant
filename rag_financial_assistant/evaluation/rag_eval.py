"""
RAG Evaluation module for the Financial RAG Assistant.

Provides RAGAS-inspired proxy metrics that do not require ground-truth labels:
  - answer_length        : token-level proxy for verbosity
  - context_utilisation  : fraction of retrieved context tokens that appear in the answer
  - context_hit_rate     : fraction of retrieved chunks referenced in the answer (keyword overlap)
  - latency_sec          : wall-clock inference time

All per-query metrics and aggregate statistics are logged to the active MLflow run.

Usage:
    from evaluation.rag_eval import RAGEvaluator
    from rag.rag_pipeline import RAGPipeline

    pipeline = RAGPipeline()
    evaluator = RAGEvaluator(pipeline)
    results = evaluator.evaluate(queries)
"""

from __future__ import annotations

import re
import time
import statistics
from typing import Any

import mlflow
import yaml


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _tokenize(text: str) -> list[str]:
    """Minimal whitespace tokenizer used for overlap metrics."""
    return re.findall(r"\b\w+\b", text.lower())


def _context_utilisation(answer: str, contexts: list[dict]) -> float:
    """
    Fraction of unique context tokens that appear at least once in the answer.
    Measures how much of the retrieved context the model actually used.
    """
    context_text = " ".join(c.get("text", "") for c in contexts)
    ctx_tokens = set(_tokenize(context_text))
    if not ctx_tokens:
        return 0.0
    ans_tokens = set(_tokenize(answer))
    return len(ctx_tokens & ans_tokens) / len(ctx_tokens)


def _context_hit_rate(answer: str, contexts: list[dict]) -> float:
    """
    Fraction of retrieved chunks that have at least one keyword overlap with
    the answer.  A chunk is "hit" if 3+ of its tokens appear in the answer.
    """
    if not contexts:
        return 0.0
    ans_tokens = set(_tokenize(answer))
    hits = sum(
        1
        for c in contexts
        if len(set(_tokenize(c.get("text", ""))) & ans_tokens) >= 3
    )
    return hits / len(contexts)


# ---------------------------------------------------------------------------
# Evaluator
# ---------------------------------------------------------------------------

class RAGEvaluator:
    """
    Runs a list of queries through a RAGPipeline and records quality metrics.
    """

    def __init__(self, pipeline, config_path: str = "config.yaml") -> None:
        self.pipeline = pipeline
        config = yaml.safe_load(open(config_path))
        # mlflow_cfg = config.get("mlflow", {})
        # mlflow.set_tracking_uri(mlflow_cfg.get("tracking_uri", "sqlite:///mlflow.db"))
        # mlflow.set_experiment(mlflow_cfg.get("experiment_name", "financial_finetuning"))

    def _evaluate_single(self, query: str) -> dict[str, Any]:
        """Run one query and return its per-query metric dict."""
        t0 = time.perf_counter()
        answer, contexts = self.pipeline.run(query)
        latency = time.perf_counter() - t0

        ans_tokens = _tokenize(answer)
        return {
            "query": query,
            "answer": answer,
            "latency_sec": round(latency, 4),
            "answer_length": len(ans_tokens),
            "context_utilisation": round(_context_utilisation(answer, contexts), 4),
            "context_hit_rate": round(_context_hit_rate(answer, contexts), 4),
            "num_contexts_retrieved": len(contexts),
        }

    def evaluate(
        self,
        queries: list[str],
        run_name: str = "rag_evaluation",
    ) -> list[dict[str, Any]]:
        """
        Evaluate all queries and log per-query and aggregate metrics to MLflow.

        Returns a list of per-query result dicts.
        """
        results: list[dict[str, Any]] = []

        # with mlflow.start_run(run_name=run_name):
        #     mlflow.log_param("num_queries", len(queries))

        for i, query in enumerate(queries):
            print(f"[Eval] ({i + 1}/{len(queries)}) {query[:80]}")
            result = self._evaluate_single(query)
            results.append(result)

            # Log per-query metrics at step = query index
            # mlflow.log_metrics(
            #     {
            #         "query/latency_sec": result["latency_sec"],
            #         "query/answer_length": result["answer_length"],
            #         "query/context_utilisation": result["context_utilisation"],
            #         "query/context_hit_rate": result["context_hit_rate"],
            #     },
            #     step=i,
            # )

        # Aggregate metrics
        def _mean(key: str) -> float:
            return round(statistics.mean(r[key] for r in results), 4)

        agg = {
            "agg/mean_latency_sec": _mean("latency_sec"),
            "agg/mean_answer_length": _mean("answer_length"),
            "agg/mean_context_utilisation": _mean("context_utilisation"),
            "agg/mean_context_hit_rate": _mean("context_hit_rate"),
            "agg/p95_latency_sec": round(
                sorted(r["latency_sec"] for r in results)[int(0.95 * len(results)) - 1], 4
            ),
        }
        # mlflow.log_metrics(agg)

        print("\n[Eval] Aggregate results:")
        for k, v in agg.items():
            print(f"  {k}: {v}")

        return results