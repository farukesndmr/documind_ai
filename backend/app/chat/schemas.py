from pydantic import BaseModel, Field


class AskQuestionRequest(BaseModel):
    question: str
    limit: int = Field(default=5, ge=1, le=10)


class SourceChunk(BaseModel):
    id: int
    document_id: int
    chunk_index: int
    content: str


class AskQuestionResponse(BaseModel):
    answer: str
    sources: list[SourceChunk]