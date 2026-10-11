from pydantic import BaseModel, Field, field_validator


class ChatRequest(BaseModel):
    question: str = Field(
        ...,
        min_length=1,
        max_length=2000,
    )

    @field_validator("question")
    @classmethod
    def question_must_not_be_blank(cls, value: str) -> str:
        value = value.strip()
        if not value:
            raise ValueError("Question must not be empty.")
        return value


class SourceInfo(BaseModel):
    source: str
    page_number: int | None = None
    chunk_index: int
    document_id: str | None = None
    content_hash: str | None = None
    url: str | None = None
    domain: str | None = None


class ChatResponse(BaseModel):
    answer: str
    sources: list[SourceInfo]
