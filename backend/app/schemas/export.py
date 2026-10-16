"""Export request and response schemas."""

from datetime import datetime
from typing import Any, Literal

from pydantic import BaseModel, Field


class ExportMessage(BaseModel):
    role: Literal["user", "assistant"]
    content: str = Field(min_length=1, max_length=100_000)
    created_at: datetime | None = None
    sources: list[dict[str, Any]] = Field(default_factory=list)


class ExportRequest(BaseModel):
    title: str = Field(default="Pharma AI conversation", max_length=255)
    messages: list[ExportMessage] = Field(min_length=1, max_length=500)
