from langchain_core.documents import Document
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.database.chunk_repository import (
    create_chunks,
    delete_chunks_for_document,
)
from app.database.document_repository import (
    create_document,
    get_document_by_hash,
    mark_document_failed,
    mark_document_processed,
)
from app.ingestion.file_utils import calculate_file_hash
from app.rag.chunker import split_text
from app.rag.pdf_processor import extract_pages_from_pdf, validate_pdf_file
from app.rag.vector_store import add_documents, delete_document_vectors


def ingest_pdf(
    db: Session,
    file_path: str,
    file_name: str,
) -> dict:

    validate_pdf_file(file_path)

    # ---------------------------------------------
    # 1. Calculate SHA-256
    # ---------------------------------------------

    content_hash = calculate_file_hash(
        file_path
    )

    # ---------------------------------------------
    # 2. Check duplicate
    # ---------------------------------------------

    existing_document = get_document_by_hash(
        db,
        content_hash,
    )

    if existing_document:

        return {
            "status": "duplicate",
            "document_id": str(
                existing_document.id
            ),
            "file_name": existing_document.file_name,
            "pages": 0,
            "chunks": 0,
            "content_hash": content_hash,
        }

    # ---------------------------------------------
    # 3. Create PostgreSQL document
    # ---------------------------------------------

    try:
        document = create_document(
            db,
            file_name=file_name,
            content_hash=content_hash,
        )
    except IntegrityError:
        # The unique database index is the final protection against two
        # concurrent uploads racing past the initial duplicate lookup.
        db.rollback()
        existing_document = get_document_by_hash(db, content_hash)
        if existing_document:
            return {
                "status": "duplicate",
                "document_id": str(existing_document.id),
                "file_name": existing_document.file_name,
                "pages": 0,
                "chunks": 0,
                "content_hash": content_hash,
            }
        raise

    try:

        # -----------------------------------------
        # 4. Extract pages
        # -----------------------------------------

        pages = extract_pages_from_pdf(
            file_path
        )

        if not pages:
            raise ValueError(
                "No readable text found in PDF."
            )

        # -----------------------------------------
        # 5. Create chunks
        # -----------------------------------------

        documents = []
        database_chunks = []

        chunk_index = 0

        for page in pages:

            chunks = split_text(
                page["text"]
            )

            for chunk in chunks:

                metadata = {
                    "source": file_name,
                    "document_id": str(
                        document.id
                    ),
                    "content_hash": content_hash,
                    "page_number": page[
                        "page_number"
                    ],
                    "chunk_index": chunk_index,
                }

                documents.append(
                    Document(
                        page_content=chunk,
                        metadata=metadata,
                    )
                )

                database_chunks.append(
                    {
                        "chunk_index": chunk_index,
                        "content": chunk,
                        "page_number": page[
                            "page_number"
                        ],
                        "metadata": metadata,
                    }
                )

                chunk_index += 1

        # -----------------------------------------
        if not documents:
            raise ValueError("No text chunks could be created from the PDF.")

        # 6. Save chunks to PostgreSQL
        # -----------------------------------------

        create_chunks(
            db,
            document_id=document.id,
            chunks=database_chunks,
        )

        # -----------------------------------------
        # 7. Generate embeddings + Chroma
        # -----------------------------------------

        add_documents(
            documents
        )

        # -----------------------------------------
        # 8. Mark complete
        # -----------------------------------------

        mark_document_processed(
            db,
            document,
        )

        return {
            "status": "processed",
            "document_id": str(
                document.id
            ),
            "file_name": file_name,
            "pages": len(pages),
            "chunks": len(documents),
            "content_hash": content_hash,
        }

    except Exception as ingestion_error:
        # Roll back any pending relational writes, then remove partial chunks
        # and vectors scoped to this document. Retain the failed document row.
        db.rollback()
        cleanup_error = None
        try:
            delete_document_vectors(document_id=str(document.id))
        except Exception as exc:
            cleanup_error = exc
        try:
            delete_chunks_for_document(db, document.id)
        except Exception as exc:
            cleanup_error = cleanup_error or exc
        try:
            mark_document_failed(db, document)
        except Exception as exc:
            cleanup_error = cleanup_error or exc
        if cleanup_error is not None:
            raise RuntimeError(
                "PDF ingestion failed and one or more cleanup operations "
                "also failed; document remains marked failed where possible."
            ) from ingestion_error
        raise
