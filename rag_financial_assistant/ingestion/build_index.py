import yaml
from ingestion.loader import load_documents
from ingestion.chunking import chunk_documents
from retrieval.embedding_model import EmbeddingModel
from retrieval.vector_store import VectorStore
from mlops.tracking import start_experiment, log_config


class IndexBuilder:
    def __init__(self):
        pass
    def run(self):
        config = yaml.safe_load(open("config.yaml"))

        # with start_experiment():

        #     log_config(config)

        docs = load_documents("data/raw")

        chunks = chunk_documents(
            docs,
            config["chunk_size"],
            config["chunk_overlap"]
        )

        texts = [c["text"] for c in chunks]

        model = EmbeddingModel(config["embedding_model"])

        embeddings = model.embed(texts)

        dim = embeddings.shape[1]

        store = VectorStore.create(dim)

        store.add(embeddings, chunks)

        store.save("data/processed")

        print("Index built")