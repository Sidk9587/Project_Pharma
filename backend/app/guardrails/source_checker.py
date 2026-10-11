"""Validate Chroma evidence against PostgreSQL's approved document/source state."""

from app.models.document import Document
from app.models.source import Source


def is_approved_evidence(metadata: dict, document: Document, source: Source | None) -> bool:
    if document.status != "processed":
        return False
    if not metadata.get("document_id") or str(document.id) != str(metadata["document_id"]):
        return False
    if document.content_hash and metadata.get("content_hash") != document.content_hash:
        return False

    if document.source_id is None:
        return document.document_type == "pdf" and source is None

    if source is None or not source.is_active or not source.crawl_enabled:
        return False
    return (
        str(source.id) == str(document.source_id)
        and str(metadata.get("source_id", "")) == str(source.id)
        and metadata.get("url") == document.url
        and metadata.get("source_domain") == source.domain
    )
