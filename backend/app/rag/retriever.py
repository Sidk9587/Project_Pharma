"""Retrieve semantically relevant chunks and authorize them through PostgreSQL."""

from uuid import UUID

from langchain_core.documents import Document as LangChainDocument
from sqlalchemy.orm import Session

from app.config.settings import settings
from app.database.database import SessionLocal
from app.guardrails.source_checker import is_approved_evidence
from app.models.document import Document
from app.models.source import Source
from app.rag.vector_store import get_vector_store


def retrieve_documents(
    query: str,
    k: int = 4,
    *,
    db: Session | None = None,
) -> list[LangChainDocument]:
    vector_store = get_vector_store()
    matches = vector_store.similarity_search_with_relevance_scores(
        query,
        k=max(k * 3, k),
    )
    owns_session = db is None
    session = db or SessionLocal()
    accepted: list[LangChainDocument] = []
    try:
        for document, score in matches:
            if score < settings.rag_min_relevance_score:
                continue
            metadata = document.metadata or {}
            try:
                document_id = UUID(str(metadata["document_id"]))
            except (KeyError, TypeError, ValueError):
                continue
            record = session.get(Document, document_id)
            if record is None:
                continue
            source = session.get(Source, record.source_id) if record.source_id else None
            if not is_approved_evidence(metadata, record, source):
                continue

            clean_metadata = dict(metadata)
            clean_metadata["source"] = record.title or record.file_name or clean_metadata.get("source", "unknown")
            clean_metadata["document_id"] = str(record.id)
            if source:
                clean_metadata["url"] = record.url
                clean_metadata["domain"] = source.domain
            accepted.append(LangChainDocument(
                page_content=document.page_content,
                metadata=clean_metadata,
            ))
            if len(accepted) >= k:
                break
    finally:
        if owns_session:
            session.close()
    return accepted
