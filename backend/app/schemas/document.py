from pydantic import BaseModel


class DocumentUploadResponse(BaseModel):
    document_id: str
    file_name: str
    pages: int
    chunks_created: int
    content_hash: str
    status: str
    duplicate: bool = False
