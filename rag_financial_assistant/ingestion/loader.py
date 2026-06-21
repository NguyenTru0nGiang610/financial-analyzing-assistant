import os

from ingestion.pdf_extractor import extract_documents


def load_documents(folder):
    documents = []

    for file in os.listdir(folder):
        path = os.path.join(folder, file)
        print(f"Processing file: {path}")
        documents.extend(extract_documents(path))
    return documents
