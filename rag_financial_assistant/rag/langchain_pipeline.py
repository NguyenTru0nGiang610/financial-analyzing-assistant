import json
import os
import time

import mlflow
import yaml
from langchain_core.documents import Document
from langchain_core.prompts import PromptTemplate
from langchain_core.runnables import RunnableLambda, RunnableParallel, RunnablePassthrough

from retrieval.embedding_model import EmbeddingModel
from retrieval.retriever import Retriever
from rag.generator import LocalLLMGenerator


LANGCHAIN_RAG_TEMPLATE = """
You are a financial analysis assistant.

Use the provided context to answer the question.

Context:
{context}

Question:
{query}

Instructions:
- Answer based only on the provided context
- If the answer cannot be found, say "The information is not available in the documents."

Answer:
"""


class LangChainRAGPipeline:
    """LangChain LCEL version of the existing custom RAG pipeline."""

    def __init__(self, config_path="config_langchain.yaml", vector_store=None, generator=None):
        self.config = yaml.safe_load(open(config_path))
        self.vector_store = vector_store
        retrieval_config = self.config.get("retrieval", {})
        self.top_k = self.config.get("top_k", retrieval_config.get("top_k", 5))
        self.vector_weight = retrieval_config.get("vector_weight", 0.6)
        self.bm25_weight = retrieval_config.get("bm25_weight", 0.4)
        self.generator = generator or LocalLLMGenerator()

        if self.vector_store is None:
            retriever_config = dict(self.config)
            retriever_config["top_k"] = self.top_k
            self.embedding_model = None
            self.retriever = Retriever(retriever_config)
        else:
            self.retriever = None
            self.embedding_model = EmbeddingModel(self.config["embedding_model"])

        self.prompt = PromptTemplate.from_template(LANGCHAIN_RAG_TEMPLATE)
        self.chain = self._build_chain()

    def _build_chain(self):
        retrieval = RunnableLambda(self._retrieve_documents)
        answer = RunnableLambda(self._generate_answer)

        return (
            RunnableParallel(
                {
                    "query": RunnablePassthrough(),
                    "documents": retrieval,
                }
            )
            | answer
        )

    def _retrieve_documents(self, query):
        start = time.time()

        if self.vector_store is None:
            contexts = self.retriever.retrieve(query)
        else:
            query_embedding = self.embedding_model.embed_query(query)
            contexts = self.vector_store.search(
                query_embedding=query_embedding,
                query_text=query,
                top_k=self.top_k,
                vector_weight=self.vector_weight,
                bm25_weight=self.bm25_weight,
            )

        mlflow.log_metric("langchain_latency_retrieval", time.time() - start)
        return [self._context_to_document(context) for context in contexts]

    @staticmethod
    def _context_to_document(context):
        return Document(
            page_content=context["text"],
            metadata={
                "source": context.get("source"),
                "page": context.get("page"),
                "score": context.get("score"),
                "chunk_id": context.get("chunk_id"),
            },
        )

    @staticmethod
    def _document_to_context(document):
        return {
            "text": document.page_content,
            "source": document.metadata.get("source"),
            "page": document.metadata.get("page"),
            "score": document.metadata.get("score"),
            "chunk_id": document.metadata.get("chunk_id"),
        }

    @staticmethod
    def _format_documents(documents):
        return "\n\n".join(
            f"Context {i + 1}: {document.page_content}"
            for i, document in enumerate(documents)
        )

    def _generate_answer(self, inputs):
        prompt = self.prompt.format(
            query=inputs["query"],
            context=self._format_documents(inputs["documents"]),
        )
        answer = self.generator.generate(prompt)
        contexts = [
            self._document_to_context(document)
            for document in inputs["documents"]
        ]
        return {
            "answer": answer,
            "contexts": contexts,
        }

    def run(self, query):
        result = self.chain.invoke(query)
        return result["answer"], result["contexts"]
