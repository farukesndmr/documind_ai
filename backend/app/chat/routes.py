import json
import logging
from collections.abc import Iterator

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session

from app.auth.access_control import (
    ensure_can_ask_question,
    increment_question_count,
)
from app.auth.dependencies import get_current_user
from app.chat.schemas import (
    AskQuestionRequest,
    AskQuestionResponse,
    ChatMessageResponse,
    SourceChunk,
)
from app.chat.service import (
    build_search_query,
    clear_history,
    get_history_messages,
    get_recent_turns,
    save_exchange,
)
from app.database.connection import SessionLocal, get_db
from app.rag.llm import LLMBudgetError, LLMError, start_llm_stream
from app.rag.service import (
    answer_question_with_rag,
    get_user_document,
    prepare_rag_prompt,
)
from app.users.models import User


logger = logging.getLogger(__name__)

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


def build_sources(chunks) -> list[SourceChunk]:
    return [
        SourceChunk(
            id=chunk.id,
            document_id=chunk.document_id,
            chunk_index=chunk.chunk_index,
            page_number=chunk.page_number,
            content=chunk.content,
        )
        for chunk in chunks
    ]


def sse_event(payload: dict) -> str:
    """Server-Sent Events formatında tek bir olay."""
    return f"data: {json.dumps(payload, ensure_ascii=False)}\n\n"


def finish_exchange(
    db: Session,
    user: User,
    document_id: int,
    question: str,
    answer: str,
    sources: list[dict],
) -> None:
    """Başarılı bir cevaptan sonra: soru-cevabı geçmişe kaydet, soru hakkını düş."""
    save_exchange(
        db=db,
        user_id=user.id,
        document_id=document_id,
        question=question,
        answer=answer,
        sources=sources,
    )
    increment_question_count(db=db, user=user)


@router.get(
    "/history/{document_id}",
    response_model=list[ChatMessageResponse],
)
def get_history(
    document_id: int,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    get_user_document(db=db, document_id=document_id, owner_id=current_user.id)
    return get_history_messages(
        db=db,
        user_id=current_user.id,
        document_id=document_id,
    )


@router.delete(
    "/history/{document_id}",
    status_code=status.HTTP_204_NO_CONTENT,
)
def delete_history(
    document_id: int,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    get_user_document(db=db, document_id=document_id, owner_id=current_user.id)
    clear_history(db=db, user_id=current_user.id, document_id=document_id)


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

    history = get_recent_turns(
        db=db,
        user_id=current_user.id,
        document_id=request_data.document_id,
    )

    answer, chunks = answer_question_with_rag(
        db=db,
        document_id=request_data.document_id,
        question=request_data.question,
        owner_id=current_user.id,
        limit=get_effective_retrieval_limit(request_data.limit),
        answer_language=request_data.answer_language,
        history=history,
        search_query=build_search_query(request_data.question, history),
    )

    sources = build_sources(chunks)

    finish_exchange(
        db=db,
        user=current_user,
        document_id=request_data.document_id,
        question=request_data.question,
        answer=answer,
        sources=[source.model_dump() for source in sources],
    )

    return AskQuestionResponse(
        answer=answer,
        sources=sources,
    )


@router.post("/ask/stream")
def ask_stream(
    request_data: AskQuestionRequest,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    """Cevabı üretildikçe Server-Sent Events (SSE) olarak gönderir.

    Olay sırası: {"type": "sources"} → {"type": "delta"}... → {"type": "done"}
    Akış sırasında hata olursa {"type": "error", "message": ...} gönderilir.
    Limit, yetki ve bütçe hataları akış başlamadan normal HTTP hatası olarak döner.
    """
    ensure_can_ask_question(current_user)

    history = get_recent_turns(
        db=db,
        user_id=current_user.id,
        document_id=request_data.document_id,
    )

    prompt, mode, chunks = prepare_rag_prompt(
        db=db,
        document_id=request_data.document_id,
        question=request_data.question,
        owner_id=current_user.id,
        limit=get_effective_retrieval_limit(request_data.limit),
        answer_language=request_data.answer_language,
        history=history,
        search_query=build_search_query(request_data.question, history),
    )

    try:
        deltas = start_llm_stream(prompt=prompt, mode=mode)
    except LLMBudgetError as exc:
        raise HTTPException(status_code=429, detail=str(exc)) from exc
    except LLMError as exc:
        raise HTTPException(status_code=503, detail=str(exc)) from exc

    sources = [source.model_dump() for source in build_sources(chunks)]
    user_id = current_user.id
    document_id = request_data.document_id
    question = request_data.question

    def event_stream() -> Iterator[str]:
        yield sse_event({"type": "sources", "sources": sources})

        parts: list[str] = []
        try:
            for text in deltas:
                parts.append(text)
                yield sse_event({"type": "delta", "text": text})
        except LLMError as exc:
            yield sse_event({"type": "error", "message": str(exc)})
            return

        answer = "".join(parts).strip()
        if not answer:
            yield sse_event({
                "type": "error",
                "message": "The model returned an empty answer. Please try again.",
            })
            return

        # Geçmişe kayıt ve soru hakkı yalnızca cevap başarıyla tamamlanınca.
        # İstek kapsamındaki oturum akış sırasında kapanmış olabileceği için
        # burada ayrı bir veritabanı oturumu kullanılır.
        try:
            with SessionLocal() as session:
                user = session.get(User, user_id)
                if user is not None:
                    finish_exchange(
                        db=session,
                        user=user,
                        document_id=document_id,
                        question=question,
                        answer=answer,
                        sources=sources,
                    )
        except Exception:
            logger.exception("Sohbet kaydı / soru sayacı güncellenemedi (kullanıcı %s).", user_id)

        yield sse_event({"type": "done"})

    return StreamingResponse(
        event_stream(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "X-Accel-Buffering": "no",  # proxy'lerin akışı tamponlamasını engeller
        },
    )
