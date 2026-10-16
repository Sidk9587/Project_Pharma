from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, Field
from typing import Any


class ConversationCreate(BaseModel):
    title: str | None = Field(default=None, max_length=255)


class ConversationMessage(BaseModel):
    id: UUID
    conversation_id: UUID
    role: str
    content: str
    created_at: datetime
    sources: list[dict[str, Any]] = Field(default_factory=list)


class ConversationSummary(BaseModel):
    id: UUID
    title: str | None
    created_at: datetime
    updated_at: datetime


class ConversationDetail(ConversationSummary):
    messages: list[ConversationMessage] = Field(default_factory=list)
