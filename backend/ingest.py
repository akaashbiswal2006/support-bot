import glob
import os

import chromadb

from .config import DOCS_DIR, COLLECTION_NAME, CHUNK_SIZE


def load_documents(folder=DOCS_DIR):
    """Read every .txt file in the folder. Returns a list of dictionaries."""
    documents = []
    for path in sorted(glob.glob(os.path.join(folder, "*.txt"))):
        with open(path, "r", encoding="utf-8") as f:
            documents.append({"source": os.path.basename(path), "text": f.read()})
    return documents


def split_into_chunks(text, size=CHUNK_SIZE):
    """Group whole lines into small chunks so each fact is easy to match."""
    lines = [line.strip() for line in text.splitlines() if line.strip()]
    chunks, current = [], ""
    for line in lines:
        if current and len(current) + len(line) + 1 > size:
            chunks.append(current)
            current = ""
        current = (current + " " + line).strip()
    if current:
        chunks.append(current)
    return chunks


def build_index():
    """Load documents, chunk them, and store them in an in-memory ChromaDB."""
    client = chromadb.EphemeralClient()
    collection = client.get_or_create_collection(name=COLLECTION_NAME)

    ids, texts, metadatas = [], [], []
    for doc in load_documents():
        if not doc["text"].strip():
            continue
        title = doc["text"].strip().splitlines()[0].strip()
        for i, chunk in enumerate(split_into_chunks(doc["text"])):
            if not chunk.startswith(title):
                chunk = f"{title}: {chunk}"      # keep the topic in every chunk
            ids.append(f"{doc['source']}-{i}")
            texts.append(chunk)
            metadatas.append({"source": doc["source"], "chunk": i})

    if texts:
        collection.upsert(ids=ids, documents=texts, metadatas=metadatas)
    return collection