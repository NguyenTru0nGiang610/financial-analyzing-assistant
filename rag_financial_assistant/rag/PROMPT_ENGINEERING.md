# LLM Answer Prompt Engineering Guide

## Overview

This document outlines the prompt engineering strategies used to optimize LLM answers in the Financial Analyzing Assistant. The system uses a score-based threshold mechanism to determine when additional context retrieval is needed via the search tool.

## Score-Based Context Retrieval

### Retrieval Score Components

The RAG pipeline uses a **hybrid scoring system** combining:

- **Vector Search Score**: Semantic similarity from embedding models (60% weight)
- **BM25 Score**: Keyword-based relevance (40% weight)

### Score Calculation

```
Final Score = (vector_score / (rank + 1)) * 0.6 + (bm25_score / (rank + 1)) * 0.4
```

### Threshold Strategy

#### Score Categories:

| Score Range | Category            | Action                                       |
| ----------- | ------------------- | -------------------------------------------- |
| 0.8 - 1.0   | High Confidence     | Use retrieved context directly               |
| 0.5 - 0.8   | Medium Confidence   | Use retrieved context with caution notes     |
| 0.3 - 0.5   | Low Confidence      | Use retrieved context + trigger search tool  |
| < 0.3       | Very Low Confidence | Skip local context, trigger search tool only |

**Default Threshold**: `0.5` (activate search tool when score < 0.5)

## Prompt Engineering Templates

### 1. High Confidence Prompt (Score ≥ 0.8)

```
You are a financial analysis assistant.

Use the provided context to answer the question directly and confidently.

Context:
[contexts]

Question:
[query]

Instructions:
- Answer based on the provided context with confidence
- Provide specific numbers and references from the context
- Be concise and direct

Answer:
```

### 2. Medium Confidence Prompt (0.5 ≤ Score < 0.8)

```
You are a financial analysis assistant.

Use the provided context to answer the question. Note that the context may be partially relevant.

Context:
[contexts]

Question:
[query]

Instructions:
- Answer based primarily on the provided context
- If the context doesn't fully address the question, acknowledge the limitation
- Provide confidence level for your answer
- Suggest what additional information would be helpful

Answer:
```

### 3. Low Confidence Prompt (0.3 ≤ Score < 0.5)

```
You are a financial analysis assistant.

The following context is loosely related to the question. Use it cautiously.

Context:
[contexts]

Question:
[query]

Instructions:
- Use the context only as a starting point
- Clearly indicate any assumptions or limitations in your answer
- Note that a web search has been triggered to find more relevant information
- Answer based on financial principles if context is insufficient

Answer:
```

### 4. Additional Context Prompt (When Search Tool is Triggered)

```
You are a financial analysis assistant.

Original Context (Local Database):
[original_contexts]

Additional Context (Web Search):
[search_tool_results]

Question:
[query]

Instructions:
- Prioritize the additional web search results for accuracy
- Cross-reference with local database context
- If sources conflict, note both perspectives
- Provide the most accurate and up-to-date answer
- Include sources for web-based information

Answer:
```

## Search Tool Trigger Logic

### When to Trigger Search Tool:

1. **Low Retrieval Score** (< 0.5): Indicates insufficient local knowledge
2. **Multiple Low-Confidence Contexts**: When all retrieved contexts have scores < 0.6
3. **Query Type Detection**: Financial news, real-time data, recent events
4. **User Indication**: Explicit request for web search

### Search Tool Configuration:

- **Max Results**: 3 documents
- **Timeout**: 30 seconds
- **Fallback**: If search fails, continue with local context
- **Deduplication**: Remove redundant results before merging

## Implementation Details

### Score Threshold Configuration

```yaml
# config.yaml
rag:
  score_threshold: 0.5 # Trigger search if below
  low_confidence_threshold: 0.6 # Flag for confidence notes
  high_confidence_threshold: 0.8 # Use directly without caution
  max_search_retries: 2 # Retry search tool on failure
```

### Context Merging Strategy

When both local and web-searched contexts are available:

1. Sort all contexts by relevance score
2. Remove duplicate/redundant information
3. Prioritize more recent web sources for time-sensitive queries
4. Maintain up to 5 most relevant contexts in final prompt

## Dynamic Prompt Adjustment

### Query Analysis:

- **Temporal Keywords** (recent, latest, 2024, 2025): Trigger search
- **Statistical Keywords** (statistics, data, performance): High confidence if available
- **Opinion Keywords** (should, would, predict): Lower confidence threshold
- **Technical Keywords** (quarterly, earnings, P/E ratio): Use specialized context

### Confidence Score Feedback Loop:

```
1. Calculate retrieval score
2. Adjust confidence level in prompt
3. Monitor LLM response quality
4. Update threshold if needed
5. Log metrics for evaluation
```

## Best Practices

### For High-Quality Answers:

- ✅ Always include the confidence level in the response
- ✅ Cite specific sources and documents
- ✅ Use search tool proactively for uncertain queries
- ✅ Combine multiple sources when available
- ✅ Note data freshness/temporal context

### Things to Avoid:

- ❌ Don't present low-confidence answers without caveats
- ❌ Don't ignore web search results when available
- ❌ Don't mix old and new data without clear temporal markers
- ❌ Don't skip the search tool for real-time financial queries

## Metrics & Monitoring

### Track These Metrics:

- Average retrieval score per query
- Search tool activation rate
- User satisfaction with answers (if available)
- Average answer latency with/without search
- Confidence score distribution

### Sample MLflow Logging:

```python
mlflow.log_metric("retrieval_score", avg_score)
mlflow.log_metric("search_triggered", 1 if score < threshold else 0)
mlflow.log_param("confidence_level", "high" / "medium" / "low")
mlflow.log_param("sources_count", len(contexts))
```

## Examples

### Example 1: High Score Query

**Query**: "What was Apple's revenue in Q3 2024?"
**Retrieval Score**: 0.92
**Action**: Use high confidence prompt, provide specific numbers
**Answer**: "Apple's Q3 2024 revenue was [specific amount] according to [source]."

### Example 2: Low Score Query

**Query**: "What are the latest market trends?"
**Retrieval Score**: 0.35
**Action**: Trigger search tool, use merged prompt
**Answer**: "According to recent web sources, ... Additionally, our database shows ..."

### Example 3: Moderate Score Query

**Query**: "Explain P/E ratio for tech stocks"
**Retrieval Score**: 0.68
**Action**: Use medium confidence prompt with context notes
**Answer**: "Based on the available context, ... [note any gaps] Additional information would help provide a more comprehensive answer."
