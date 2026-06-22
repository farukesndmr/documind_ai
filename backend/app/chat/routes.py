from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.auth.dependencies import get_current_user
from app.chat.schemas import AskQuestionRequest, AskQuestionResponse, SourceChunk
from app.chat.service import ask_question
from app.database.connection import get_db


router = APIRouter(
    prefix="/chat",
    tags=["Chat"]
)


@router.post(
    "/ask",
    response_model=AskQuestionResponse
)
def ask(
    request_data: AskQuestionRequest,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user)
):
    answer, chunks = ask_question(
        db=db,
        question=request_data.question,
        owner_id=current_user.id,
        limit=request_data.limit
    )

    sources = [
        SourceChunk(
            id=chunk.id,
            document_id=chunk.document_id,
            chunk_index=chunk.chunk_index,
            content=chunk.content
        )
        for chunk in chunks
    ]

    return AskQuestionResponse(
        answer=answer,
        sources=sources
    )