from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Response, status
from sqlalchemy.orm import Session

from app.database.database import get_db
from app.ingestion.crawler import crawl_source
from app.schemas.source import CrawlResponse, SourceCreate, SourcePatch, SourceResponse
from app.services.source_service import (
    create_source,
    delete_source,
    get_source,
    list_sources,
    source_status,
    update_source,
)


router = APIRouter(prefix="/sources", tags=["Sources"])


@router.post("", response_model=SourceResponse, status_code=status.HTTP_201_CREATED)
def create_source_endpoint(request: SourceCreate, db: Session = Depends(get_db)):
    try:
        return create_source(db, name=request.name, base_url=request.base_url)
    except ValueError as exc:
        raise HTTPException(status_code=409 if "already configured" in str(exc) else 422, detail=str(exc)) from exc


@router.get("", response_model=list[SourceResponse])
def list_sources_endpoint(db: Session = Depends(get_db)):
    return list_sources(db)


@router.get("/{source_id}/status")
def source_status_endpoint(source_id: UUID, db: Session = Depends(get_db)):
    source = get_source(db, source_id)
    if source is None:
        raise HTTPException(status_code=404, detail="Source not found.")
    return source_status(db, source)


@router.post("/{source_id}/crawl", response_model=CrawlResponse)
def crawl_source_endpoint(source_id: UUID, db: Session = Depends(get_db)):
    try:
        return crawl_source(db, source_id)
    except LookupError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    except PermissionError as exc:
        raise HTTPException(status_code=409, detail=str(exc)) from exc
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc


@router.get("/{source_id}", response_model=SourceResponse)
def get_source_endpoint(source_id: UUID, db: Session = Depends(get_db)):
    source = get_source(db, source_id)
    if source is None:
        raise HTTPException(status_code=404, detail="Source not found.")
    return source


@router.patch("/{source_id}", response_model=SourceResponse)
def update_source_endpoint(
    source_id: UUID,
    request: SourcePatch,
    db: Session = Depends(get_db),
):
    source = get_source(db, source_id)
    if source is None:
        raise HTTPException(status_code=404, detail="Source not found.")
    try:
        changes = {
            key: value
            for key, value in request.model_dump(exclude_unset=True).items()
            if value is not None
        }
        return update_source(db, source, changes)
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc


@router.delete("/{source_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_source_endpoint(source_id: UUID, db: Session = Depends(get_db)):
    source = get_source(db, source_id)
    if source is None:
        raise HTTPException(status_code=404, detail="Source not found.")
    try:
        delete_source(db, source)
    except Exception as exc:
        raise HTTPException(status_code=500, detail="Source cleanup failed; source remains inactive.") from exc
    return Response(status_code=status.HTTP_204_NO_CONTENT)
