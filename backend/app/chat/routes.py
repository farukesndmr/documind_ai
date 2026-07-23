from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.auth.access_control import (
    ensure_can_ask_question,
    increment_question_count,
)
from app.auth.dependencies import get_current_user
from app.chat.schemas import AskQuestionRequest, AskQuestionResponse, SourceChunk
from app.database.connection import get_db
from app.rag.service import answer_question_with_rag


router = APIRouter(
    prefix="/chat",
    tags=["Chat"],
)


def get_effective_retrieval_limit(requested_limit: int | None) -> int:
    """
    RAG teknik olarak kaç chunk kullanacağını bilmek zorunda.
    Ama demo limiti olarak chunk sayısını düşük tutmuyoruz.

    Frontend 2 gibi düşük bir değer gönderirse cevap kalitesi düşmesin diye
    minimum 6 chunk kullanıyoruz.
    """
    if requested_limit is None:
        return 6

    return max(requested_limit, 6)


@router.post(
    "/ask",
    response_model=AskQuestionResponse,
)
def ask(
    request_data: AskQuestionRequest,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    ensure_can_ask_question(current_user)

    retrieval_limit = get_effective_retrieval_limit(
        request_data.limit
    )

    answer, chunks = answer_question_with_rag(
        db=db,
        document_id=request_data.document_id,
        question=request_data.question,
        owner_id=current_user.id,
        limit=retrieval_limit,
    )

    increment_question_count(
        db=db,
        user=current_user,
    )

    sources = [
        SourceChunk(
            id=chunk.id,
            document_id=chunk.document_id,
            chunk_index=chunk.chunk_index,
            content=chunk.content,
        )
        for chunk in chunks
    ]

    return AskQuestionResponse(
        answer=answer,
        sources=sources,
    )