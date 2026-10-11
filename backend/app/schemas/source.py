from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field


class SourceCreate(BaseModel):
    name: str = Field(min_length=1, max_length=255)
    base_url: str = Field(min_length=8, max_length=2048)


class SourcePatch(BaseModel):
    name: str | None = Field(default=None, min_length=1, max_length=255)
    base_url: str | None = Field(default=None, min_length=8, max_length=2048)
    is_active: bool | None = None
    crawl_enabled: bool | None = None


class SourceResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    name: str
    base_url: str
    domain: str
    is_active: bool
    crawl_enabled: bool
    last_crawled_at: datetime | None
    created_at: datetime
    updated_at: datetime


class CrawlResponse(BaseModel):
    source_id: UUID
    pages_seen: int
    pages_indexed: int
    pages_skipped: int
    pages_failed: int
    pages_blocked: int = 0
    status: str
