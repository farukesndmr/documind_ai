from pydantic import BaseModel, Field


class AskQuestionRequest(BaseModel):
    document_id: int
    question: str
    limit: int = Field(default=8, ge=1, le=20)


class SourceChunk(BaseModel):
    id: int
    document_id: int
    chunk_index: int
    content: str


class AskQuestionResponse(BaseModel):
    answer: str
    sources: list[SourceChunk]