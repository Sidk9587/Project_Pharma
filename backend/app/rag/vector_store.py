from langchain_chroma import Chroma
from langchain_core.documents import Document
from pathlib import Path
from chromadb import PersistentClient
import hashlib
import re

from app.rag.embeddings import get_embedding_model
from app.config.settings import settings


CHROMA_PATH = "./chroma_db"
COLLECTION_NAME = "pharma_documents"


def get_vector_store() -> Chroma:

    embeddings = get_embedding_model()
    return Chroma(
        collection_name=get_collection_name(),
        embedding_function=embeddings,
        persist_directory=CHROMA_PATH,
    )


def get_collection_name() -> str:

    # Keep the existing default collection intact; any changed embedding space
    # gets its own collection and requires a controlled reindex.
    provider = settings.embedding_provider
    model = settings.ollama_embedding_model if provider == "ollama" else settings.openai_embedding_model
    if provider == "ollama" and model == "nomic-embed-text:latest":
        collection_name = COLLECTION_NAME
    else:
        suffix = re.sub(r"[^a-z0-9]+", "-", f"{provider}-{model}".lower()).strip("-")[:32]
        digest = hashlib.sha256(f"{provider}:{model}".encode()).hexdigest()[:8]
        collection_name = f"{COLLECTION_NAME}_{suffix}_{digest}"
    return collection_name


def add_documents(documents: list[Document], *, ids: list[str] | None = None) -> None:

    vector_store = get_vector_store()

    vector_store.add_documents(documents, ids=ids)


def delete_document_vectors(
    content_hash: str | None = None,
    *,
    document_id: str | None = None,
) -> None:

    if document_id is None and content_hash is None:
        raise ValueError("A document_id or content_hash is required.")

    path = Path(CHROMA_PATH)
    if not path.exists():
        return
    # Remove only vectors owned by this app from every embedding-space
    # collection, including inactive collections retained for rollback.
    client = PersistentClient(path=str(path))
    where = {"document_id": document_id} if document_id is not None else {"content_hash": content_hash}
    for collection in client.list_collections():
        if collection.name == COLLECTION_NAME or collection.name.startswith(f"{COLLECTION_NAME}_"):
            collection.delete(where=where)
