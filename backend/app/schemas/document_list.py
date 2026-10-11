from datetime import datetime

from pydantic import BaseModel


class DocumentListItem(BaseModel):
    id: str
    file_name: str | None
    title: str | None
    document_type: str
    status: str
    created_at: datetime


class DocumentDetail(DocumentListItem):
    source_id: str | None = None
    user_id: str | None = None
    url: str | None = None
    content_hash: str | None = None
    updated_at: datetime
