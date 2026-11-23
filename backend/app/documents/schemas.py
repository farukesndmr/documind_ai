from datetime import datetime

from pydantic import BaseModel, Field, field_validator


class DocumentResponse(BaseModel):
    """Liste ve yükleme cevabı. Tam metin ve sunucu dosya yolu bilerek dönülmez:
    hem cevabı hafifletir hem de sunucu içi bilgileri dışarı sızdırmaz."""

    id: int
    title: str
    created_at: datetime

    class Config:
        from_attributes = True


class DocumentChunkResponse(BaseModel):
    id: int
    document_id: int
    content: str
    chunk_index: int
    page_number: int | None = None
    created_at: datetime

    class Config:
        from_attributes = True


class ChunkSearchRequest(BaseModel):
    query: str = Field(min_length=1, max_length=2000)
    limit: int = Field(default=5, ge=1, le=10)


class DocumentRenameRequest(BaseModel):
    title: str = Field(min_length=1, max_length=200)

    @field_validator("title")
    @classmethod
    def clean_title(cls, value: str) -> str:
        cleaned = " ".join(value.split())
        if not cleaned:
            raise ValueError("Title cannot be empty.")
        return cleaned

