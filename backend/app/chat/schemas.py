from datetime import datetime
from typing import Literal

from pydantic import BaseModel, Field, field_validator


AnswerLanguage = Literal["auto", "en", "tr", "de", "es", "fr"]


class AskQuestionRequest(BaseModel):
    document_id: int
    question: str = Field(min_length=1, max_length=2000)
    limit: int = Field(default=8, ge=1, le=20)
    answer_language: AnswerLanguage = "auto"


class SourceChunk(BaseModel):
    id: int
    document_id: int
    chunk_index: int
    page_number: int | None = None
    content: str


class AskQuestionResponse(BaseModel):
    answer: str
    sources: list[SourceChunk]


class ChatMessageResponse(BaseModel):
    id: int
    role: Literal["user", "assistant"]
    content: str
    sources: list[SourceChunk] = []
    created_at: datetime | None = None

    @field_validator("sources", mode="before")
    @classmethod
    def none_to_empty(cls, value):
        return value or []

    class Config:
        from_attributes = True
