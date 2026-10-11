from langchain_chroma import Chroma
from langchain_core.documents import Document

from app.rag.embeddings import get_embedding_model


CHROMA_PATH = "./chroma_db"
COLLECTION_NAME = "pharma_documents"


def get_vector_store() -> Chroma:

    embeddings = get_embedding_model()

    return Chroma(
        collection_name=COLLECTION_NAME,
        embedding_function=embeddings,
        persist_directory=CHROMA_PATH,
    )


def add_documents(documents: list[Document]) -> None:

    vector_store = get_vector_store()

    vector_store.add_documents(documents)


def delete_document_vectors(
    content_hash: str | None = None,
    *,
    document_id: str | None = None,
) -> None:

    if document_id is None and content_hash is None:
        raise ValueError("A document_id or content_hash is required.")

    vector_store = get_vector_store()

    vector_store.delete(
        where={
            "document_id": document_id,
        }
        if document_id is not None
        else {"content_hash": content_hash}
    )
