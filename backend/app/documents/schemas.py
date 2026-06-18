from datetime import datetime

from pydantic import BaseModel


class DocumentResponse(BaseModel):
    id: int
    title: str
    file_path: str
    extracted_text: str | None
    owner_id: int
    created_at: datetime

    class Config:
        from_attributes = True


class DocumentChunkResponse(BaseModel):
    id: int
    document_id: int
    content: str
    chunk_index: int
    created_at: datetime

    class Config:
        from_attributes = True