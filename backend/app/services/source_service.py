from uuid import UUID

from sqlalchemy.orm import Session

from app.ingestion.url_validator import normalize_source_url
from app.models.crawl_log import CrawlLog
from app.models.document import Document
from app.models.source import Source
from app.rag.vector_store import delete_document_vectors


def create_source(db: Session, *, name: str, base_url: str) -> Source:
    normalized_url, domain = normalize_source_url(base_url)
    name = name.strip()
    if not name:
        raise ValueError("Source name must not be empty.")
    existing = (
        db.query(Source)
        .filter(Source.domain == domain, Source.base_url == normalized_url)
        .first()
    )
    if existing:
        raise ValueError("This source URL is already configured.")
    source = Source(
        name=name,
        base_url=normalized_url,
        domain=domain,
        is_active=True,
        crawl_enabled=True,
    )
    db.add(source)
    db.commit()
    db.refresh(source)
    return source


def list_sources(db: Session) -> list[Source]:
    return db.query(Source).order_by(Source.created_at.desc()).all()


def get_source(db: Session, source_id: UUID) -> Source | None:
    return db.get(Source, source_id)


def update_source(db: Session, source: Source, changes: dict) -> Source:
    if "name" in changes:
        source.name = changes["name"].strip()
        if not source.name:
            raise ValueError("Source name must not be empty.")
    if "base_url" in changes:
        normalized_url, domain = normalize_source_url(changes["base_url"])
        duplicate = (
            db.query(Source)
            .filter(Source.domain == domain, Source.base_url == normalized_url, Source.id != source.id)
            .first()
        )
        if duplicate:
            raise ValueError("This source URL is already configured.")
        source.base_url = normalized_url
        source.domain = domain
    for field in ("is_active", "crawl_enabled"):
        if field in changes:
            setattr(source, field, changes[field])
    db.commit()
    db.refresh(source)
    return source


def delete_source(db: Session, source: Source) -> None:
    # Turn off retrieval before any external vector cleanup, so partial cleanup
    # can never leave the source available as evidence.
    source.is_active = False
    source.crawl_enabled = False
    db.commit()
    documents = db.query(Document).filter(Document.source_id == source.id).all()
    for document in documents:
        delete_document_vectors(document_id=str(document.id))
    try:
        for document in documents:
            db.delete(document)
        db.delete(source)
        db.commit()
    except Exception:
        db.rollback()
        raise


def source_status(db: Session, source: Source) -> dict:
    docs = db.query(Document).filter(Document.source_id == source.id)
    logs = db.query(CrawlLog).filter(CrawlLog.source_id == source.id)
    latest = logs.order_by(CrawlLog.crawled_at.desc()).first()
    return {
        "source_id": source.id,
        "is_active": source.is_active,
        "crawl_enabled": source.crawl_enabled,
        "last_crawled_at": source.last_crawled_at,
        "documents": docs.count(),
        "latest_crawl": ({
                "id": log.id,
                "url": log.url,
                "status": log.status,
                "http_status": log.http_status,
                "error_message": log.error_message,
                "crawled_at": log.crawled_at,
            } if latest else None),
    }
