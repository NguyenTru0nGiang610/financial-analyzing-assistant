#!/usr/bin/env python3
"""
Evaluation runner for the Financial RAG Assistant.

Runs the RAG pipeline against a set of test queries and evaluates performance
using proxy metrics (answer length, context utilization, context hit rate, latency).

Usage:
    python3 run_evaluation.py
"""

import sys
import json
from datetime import datetime
from pathlib import Path

from rag.rag_pipeline import RAGPipeline
from evaluation.rag_eval import RAGEvaluator
from data.apple_testing import apple_test_set


def main():
    """Run evaluation and save results."""
    
    print("=" * 80)
    print("Financial RAG Assistant - Evaluation Runner")
    print("=" * 80)
    print()
    
    # Initialize pipeline and evaluator
    print("[*] Initializing RAG Pipeline...")
    pipeline = RAGPipeline()
    
    print("[*] Initializing Evaluator...")
    evaluator = RAGEvaluator(pipeline)
    print()
    
    # Extract queries from test set
    queries = [item["question"] for item in apple_test_set]
    print(f"[*] Loaded {len(queries)} test queries")
    print()
    
    # Run evaluation
    print("[*] Starting evaluation...")
    print("-" * 80)
    results = evaluator.evaluate(queries, run_name="apple_financial_eval")
    print("-" * 80)
    print()
    
    # Save detailed results to file
    output_dir = Path("evaluation/results")
    output_dir.mkdir(parents=True, exist_ok=True)
    
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    results_file = output_dir / f"eval_results_{timestamp}.json"
    
    # Prepare full results with expected answers
    full_results = []
    for i, result in enumerate(results):
        if i < len(apple_test_set):
            full_results.append({
                **result,
                "expected_answer": apple_test_set[i]["answer"]
            })
        else:
            full_results.append(result)
    
    with open(results_file, "w") as f:
        json.dump(full_results, f, indent=2)
    
    print(f"[✓] Detailed results saved to: {results_file}")
    print()
    
    # Print summary
    print("=" * 80)
    print("Evaluation Summary")
    print("=" * 80)
    print()
    
    print(f"Total Queries: {len(results)}")
    print()
    
    print("Per-Query Metrics (Average):")
    print("-" * 80)
    
    avg_latency = sum(r["latency_sec"] for r in results) / len(results)
    avg_answer_length = sum(r["answer_length"] for r in results) / len(results)
    avg_context_util = sum(r["context_utilisation"] for r in results) / len(results)
    avg_context_hit = sum(r["context_hit_rate"] for r in results) / len(results)
    avg_contexts = sum(r["num_contexts_retrieved"] for r in results) / len(results)
    
    print(f"  Average Latency:              {avg_latency:.4f} sec")
    print(f"  Average Answer Length:        {avg_answer_length:.0f} tokens")
    print(f"  Average Context Utilization:  {avg_context_util:.2%}")
    print(f"  Average Context Hit Rate:     {avg_context_hit:.2%}")
    print(f"  Average Contexts Retrieved:   {avg_contexts:.1f}")
    print()
    
    print("Performance Percentiles:")
    print("-" * 80)
    
    latencies = sorted([r["latency_sec"] for r in results])
    p50_idx = len(latencies) // 2
    p95_idx = int(len(latencies) * 0.95)
    
    print(f"  Latency (p50):                {latencies[p50_idx]:.4f} sec")
    print(f"  Latency (p95):                {latencies[p95_idx]:.4f} sec")
    print(f"  Latency (max):                {latencies[-1]:.4f} sec")
    print()
    
    # Show sample results
    print("Sample Results (First 3 Queries):")
    print("-" * 80)
    for i in range(min(3, len(results))):
        result = results[i]
        expected = apple_test_set[i]["answer"] if i < len(apple_test_set) else "N/A"
        print()
        print(f"Query {i+1}: {result['query'][:70]}...")
        print(f"  Expected: {expected}")
        print(f"  Generated: {result['answer'][:70]}...")
        print(f"  Latency: {result['latency_sec']:.4f} sec | "
              f"Answer Length: {result['answer_length']} tokens | "
              f"Context Hit Rate: {result['context_hit_rate']:.2%}")
    print()
    
    print("=" * 80)
    print(f"[✓] Evaluation Complete! Results saved to: {results_file}")
    print("=" * 80)
    
    return 0


if __name__ == "__main__":
    sys.exit(main())
