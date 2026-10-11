from pathlib import Path
from tempfile import NamedTemporaryFile
from uuid import UUID

from fastapi import APIRouter, Depends, File, HTTPException, UploadFile
from sqlalchemy.orm import Session

from app.database.database import get_db
from app.database.document_repository import (
    delete_document,
    get_document_by_id,
    get_documents,
)
from app.ingestion.pdf_ingestion import ingest_pdf
from app.rag.pdf_processor import validate_pdf_file
from app.rag.vector_store import delete_document_vectors
from app.schemas.document import DocumentUploadResponse
from app.schemas.document_list import DocumentDetail, DocumentListItem


router = APIRouter(prefix="/documents", tags=["Documents"])
MAX_UPLOAD_BYTES = 50 * 1024 * 1024


def _document_detail(document) -> DocumentDetail:
    return DocumentDetail(
        id=str(document.id),
        file_name=document.file_name,
        title=document.title,
        document_type=document.document_type,
        status=document.status,
        created_at=document.created_at,
        updated_at=document.updated_at,
        source_id=str(document.source_id) if document.source_id else None,
        user_id=str(document.user_id) if document.user_id else None,
        url=document.url,
        content_hash=document.content_hash,
    )


@router.post("/upload", response_model=DocumentUploadResponse)
async def upload_document(
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
):
    if not file.filename:
        raise HTTPException(status_code=400, detail="File name is required.")
    safe_name = Path(file.filename).name
    if not safe_name.lower().endswith(".pdf"):
        raise HTTPException(status_code=400, detail="Only PDF files are supported.")

    temp_path: str | None = None
    try:
        size = 0
        with NamedTemporaryFile(prefix="pharma_upload_", suffix=".pdf", delete=False) as temp_file:
            temp_path = temp_file.name
            while chunk := await file.read(1024 * 1024):
                size += len(chunk)
                if size > MAX_UPLOAD_BYTES:
                    raise HTTPException(status_code=413, detail="PDF exceeds the 50 MB upload limit.")
                temp_file.write(chunk)
        if size == 0:
            raise HTTPException(status_code=400, detail="Uploaded file is empty.")

        validate_pdf_file(temp_path)
        result = ingest_pdf(db=db, file_path=temp_path, file_name=safe_name)
        return DocumentUploadResponse(
            document_id=result["document_id"],
            file_name=result["file_name"],
            pages=result["pages"],
            chunks_created=result["chunks"],
            content_hash=result["content_hash"],
            status=result["status"],
            duplicate=result["status"] == "duplicate",
        )
    except HTTPException:
        raise
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    except Exception as exc:
        raise HTTPException(status_code=500, detail="Document processing failed.") from exc
    finally:
        await file.close()
        if temp_path:
            Path(temp_path).unlink(missing_ok=True)


@router.get("", response_model=list[DocumentListItem])
def list_documents(db: Session = Depends(get_db)):
    return [
        DocumentListItem(
            id=str(document.id),
            file_name=document.file_name,
            title=document.title,
            document_type=document.document_type,
            status=document.status,
            created_at=document.created_at,
        )
        for document in get_documents(db)
    ]


@router.get("/{document_id}/status")
def get_document_status(document_id: UUID, db: Session = Depends(get_db)):
    document = get_document_by_id(db, document_id)
    if document is None:
        raise HTTPException(status_code=404, detail="Document not found.")
    return {"document_id": str(document.id), "status": document.status}


@router.get("/{document_id}", response_model=DocumentDetail)
def get_document(document_id: UUID, db: Session = Depends(get_db)):
    document = get_document_by_id(db, document_id)
    if document is None:
        raise HTTPException(status_code=404, detail="Document not found.")
    return _document_detail(document)


@router.delete("/{document_id}", status_code=204)
def remove_document(document_id: UUID, db: Session = Depends(get_db)):
    document = get_document_by_id(db, document_id)
    if document is None:
        raise HTTPException(status_code=404, detail="Document not found.")
    try:
        delete_document_vectors(document_id=str(document.id))
        delete_document(db, document)
    except Exception as exc:
        db.rollback()
        raise HTTPException(status_code=500, detail="Document cleanup failed.") from exc
    return None
