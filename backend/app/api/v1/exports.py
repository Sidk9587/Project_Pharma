"""Downloadable conversation export endpoints."""

from fastapi import APIRouter
from fastapi.responses import Response

from app.schemas.export import ExportRequest
from app.services.export_service import create_excel_export, create_pdf_export

router = APIRouter(prefix="/exports", tags=["Exports"])


@router.post("/pdf")
def export_pdf(request: ExportRequest):
    return Response(create_pdf_export(request), media_type="application/pdf", headers={"Content-Disposition": 'attachment; filename="pharma-conversation.pdf"'})


@router.post("/excel")
def export_excel(request: ExportRequest):
    return Response(create_excel_export(request), media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet", headers={"Content-Disposition": 'attachment; filename="pharma-conversation.xlsx"'})
