from pydantic import BaseModel, Field


class AskQuestionRequest(BaseModel):
    document_id: int
    question: str = Field(min_length=1, max_length=2000)
    limit: int = Field(default=8, ge=1, le=20)


class SourceChunk(BaseModel):
    id: int
    document_id: int
    chunk_index: int
    page_number: int | None = None
    content: str


class AskQuestionResponse(BaseModel):
    answer: str
    sources: list[SourceChunk]
