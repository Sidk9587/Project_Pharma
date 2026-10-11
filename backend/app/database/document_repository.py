from uuid import UUID

from sqlalchemy.orm import Session

from app.models.document import Document


def get_document_by_hash(
    db: Session,
    content_hash: str,
) -> Document | None:

    return (
        db.query(Document)
        .filter(
            Document.content_hash == content_hash
        )
        .first()
    )


def get_document_by_id(
    db: Session,
    document_id: UUID,
) -> Document | None:
    return db.get(Document, document_id)


def create_document(
    db: Session,
    *,
    file_name: str,
    content_hash: str,
    document_type: str = "pdf",
    user_id: UUID | None = None,
) -> Document:

    document = Document(
        title=file_name,
        file_name=file_name,
        document_type=document_type,
        content_hash=content_hash,
        status="processing",
        user_id=user_id,
    )

    db.add(document)
    db.commit()
    db.refresh(document)

    return document


def update_document_status(
    db: Session,
    document: Document,
    status: str,
) -> Document:
    document.status = status
    db.commit()
    db.refresh(document)
    return document


def mark_document_processed(
    db: Session,
    document: Document,
) -> Document:
    return update_document_status(db, document, "processed")


def mark_document_failed(
    db: Session,
    document: Document,
) -> Document:
    return update_document_status(db, document, "failed")


def get_documents(
    db: Session,
) -> list[Document]:

    return (
        db.query(Document)
        .order_by(Document.created_at.desc())
        .all()
    )


def delete_document(
    db: Session,
    document: Document,
) -> None:

    db.delete(document)
    db.commit()
