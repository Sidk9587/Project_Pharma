from uuid import UUID

from sqlalchemy.orm import Session

from app.models.document_chunk import DocumentChunk


def create_chunk(
    db: Session,
    *,
    document_id: UUID,
    chunk: dict,
) -> DocumentChunk:
    record = DocumentChunk(
        document_id=document_id,
        chunk_index=chunk["chunk_index"],
        content=chunk["content"],
        token_count=chunk.get("token_count"),
        page_number=chunk.get("page_number"),
        metadata_json=chunk.get("metadata", {}),
    )
    db.add(record)
    db.commit()
    db.refresh(record)
    return record


def create_chunks(
    db: Session,
    *,
    document_id,
    chunks: list[dict],
) -> None:

    records = []

    for chunk in chunks:

        records.append(
            DocumentChunk(
                document_id=document_id,
                chunk_index=chunk["chunk_index"],
                content=chunk["content"],
                token_count=chunk.get("token_count"),
                page_number=chunk.get("page_number"),
                metadata_json=chunk.get("metadata", {}),
            )
        )

    db.add_all(records)
    db.commit()
    return records


def get_chunks_for_document(
    db: Session,
    document_id: UUID,
) -> list[DocumentChunk]:
    return (
        db.query(DocumentChunk)
        .filter(DocumentChunk.document_id == document_id)
        .order_by(DocumentChunk.chunk_index.asc())
        .all()
    )


def delete_chunks_for_document(
    db: Session,
    document_id: UUID,
) -> None:
    db.query(DocumentChunk).filter(
        DocumentChunk.document_id == document_id
    ).delete(synchronize_session=False)
    db.commit()
