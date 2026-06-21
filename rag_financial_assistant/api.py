import os
import uuid
import time
from flask import Flask, request, jsonify
from flask_cors import CORS

# Your existing imports
from rag.rag_pipeline import RAGPipeline
from ingestion.chunking import chunk_documents
from ingestion.pdf_extractor import extract_documents
from retrieval.embedding_model import EmbeddingModel
from retrieval.vector_store import VectorStore

app = Flask(__name__)
CORS(app)
embedding_model = EmbeddingModel("all-MiniLM-L6-v2")

# session_id -> {vector_store, created_at}
SESSION_STORE = {}

SESSION_TTL = 3600  # 1 hour

# SESSION CLEANUP

def cleanup_sessions():
    now = time.time()
    expired = []

    for sid, data in SESSION_STORE.items():
        if now - data["created_at"] > SESSION_TTL:
            expired.append(sid)

    for sid in expired:
        del SESSION_STORE[sid]
# CREATE SESSION
@app.route("/session", methods=["GET"])
def create_session():
    session_id = str(uuid.uuid4())

    SESSION_STORE[session_id] = {
        "vector_store": None,
        "created_at": time.time()
    }

    return jsonify({"session_id": session_id})


# UPLOAD DOCUMENT
@app.route("/upload", methods=["POST"])
def upload():

    session_id = request.args.get("session_id")

    if session_id not in SESSION_STORE:
        return jsonify({"error": "Invalid session"}), 400

    file = request.files.get("file")

    if not file:
        return jsonify({"error": "No file uploaded"}), 400

    # Save file to a temporary location
    file_path = f"/tmp/{file.filename}"
    file.save(file_path)

    # Extract
    documents = extract_documents(file_path)
    os.remove(file_path)  
    # Chunk
    chunks = chunk_documents(documents, 400, 50)

    texts = [c["text"] for c in chunks]

    # Embed
    embeddings = embedding_model.embed(texts)

    dim = embeddings.shape[1]

    # Create vector store
    store = VectorStore.create(dim)
    store.add(embeddings, chunks)

    # Save to session
    SESSION_STORE[session_id]["vector_store"] = store
    SESSION_STORE[session_id]["created_at"] = time.time()

    return jsonify({"status": "indexed"})


# QUERY
@app.route("/query", methods=["POST"])
def query():

    data = request.get_json()

    session_id = data.get("session_id")
    user_query = data.get("query")

    if session_id not in SESSION_STORE:
        return jsonify({"error": "Invalid session"}), 400

    store = SESSION_STORE[session_id]["vector_store"]

    if store is None:
        return jsonify({"error": "No documents uploaded"}), 400

    # Retrieve
    query_embedding = embedding_model.embed_query(user_query)
    contexts = store.search(query_embedding=query_embedding, query_text=user_query, top_k=5)

    pipeline = data.get("pipeline", "langchain")

    if pipeline == "langchain":
        from rag.langchain_pipeline import LangChainRAGPipeline

        rag = LangChainRAGPipeline(vector_store=store)
        answer, contexts = rag.run(user_query)
    elif pipeline == "custom":
        rag = RAGPipeline()
        answer, contexts = rag.run_with_contexts(user_query, contexts)
    else:
        return jsonify({"error": "pipeline must be 'custom' or 'langchain'"}), 400

    return jsonify({
        "answer": answer,
        "sources": contexts,
        "pipeline": pipeline
    })


@app.route("/query/compare", methods=["POST"])
def query_compare():

    data = request.get_json()

    session_id = data.get("session_id")
    user_query = data.get("query")

    if session_id not in SESSION_STORE:
        return jsonify({"error": "Invalid session"}), 400

    store = SESSION_STORE[session_id]["vector_store"]

    if store is None:
        return jsonify({"error": "No documents uploaded"}), 400

    query_embedding = embedding_model.embed_query(user_query)
    custom_contexts = store.search(query_embedding=query_embedding, query_text=user_query, top_k=5)

    custom_rag = RAGPipeline()
    custom_answer, custom_contexts = custom_rag.run_with_contexts(user_query, custom_contexts)

    from rag.langchain_pipeline import LangChainRAGPipeline

    langchain_rag = LangChainRAGPipeline(
        vector_store=store,
        generator=custom_rag.generator,
    )
    langchain_answer, langchain_contexts = langchain_rag.run(user_query)

    return jsonify({
        "custom": {
            "answer": custom_answer,
            "sources": custom_contexts,
        },
        "langchain": {
            "answer": langchain_answer,
            "sources": langchain_contexts,
        }
    })

# HEALTH CHECK
@app.route("/")
def home():
    return jsonify({"status": "RAG API running"})


# =========================
# RUN SERVER
# =========================
if __name__ == "__main__":
    app.run(debug=True, port=8000)
