def build_prompt(query, contexts):

    context_block = "\n\n".join(
        [f"Context {i+1}: {c['text']}" for i, c in enumerate(contexts)]
    )

    prompt = f"""
You are a financial analysis assistant.

Use the provided context to answer the question.

Context:
{context_block}

Question:
{query}

Instructions:
- Answer based only on the provided context


Answer:
"""

    return prompt


def build_dynamic_prompt(query, contexts, confidence_level="medium"):
    """
    Build a prompt dynamically based on retrieval confidence level.
    
    Args:
        query: The user's question
        contexts: List of retrieved context documents with scores
        confidence_level: "high", "medium", or "low"
    
    Returns:
        Dynamically formatted prompt string
    """
    context_block = "\n\n".join(
        [f"Context {i+1} (Source: {c.get('source', 'local')}): {c['text']}" 
         for i, c in enumerate(contexts)]
    )
    
    if confidence_level == "high":
        # High confidence: direct and confident tone
        prompt = f"""
You are a financial analysis assistant with access to reliable financial data.

Use the provided context to answer the question directly and confidently.

Context:
{context_block}

Question:
{query}

Instructions:
- Answer based on the provided context with confidence
- Provide specific numbers and references from the context
- Be concise and direct
- Cite sources when available

Answer:
"""
    
    elif confidence_level == "low":
        # Low confidence: cautious tone with caveats
        prompt = f"""
You are a financial analysis assistant.

The following context is available but may be only partially relevant to your question.
Use it carefully and acknowledge any limitations.

Context:
{context_block}

Question:
{query}

Instructions:
- Use the context only as a starting point for your answer
- Clearly indicate any assumptions or limitations in your answer
- Note which parts of your answer are based on the provided context
- If context is insufficient, provide general financial principles
- Suggest what additional information would be helpful
- Include confidence indicators (high/medium/low confidence)

Answer:
"""
    
    else:  # medium confidence
        # Medium confidence: balanced tone with context notes
        prompt = f"""
You are a financial analysis assistant.

Use the provided context to answer the question. Note that the context may be partially relevant.

Context:
{context_block}

Question:
{query}

Instructions:
- Answer based primarily on the provided context
- If the context doesn't fully address the question, acknowledge the limitation
- Provide a confidence level for your answer (high/medium/low)
- Suggest what additional information would be helpful
- Include specific references to source documents when relevant

Answer:
"""
    
    return prompt

# - If the answer cannot be found, say "The information is not available in the documents."