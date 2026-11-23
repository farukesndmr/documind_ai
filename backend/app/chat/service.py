"""Sohbet geçmişinin okunması, kaydedilmesi ve silinmesi."""

from sqlalchemy.orm import Session

from app.chat.models import ChatMessage
from app.rag.prompt_builder import HistoryTurn


# Modele bağlam olarak verilecek en fazla önceki soru-cevap sayısı.
HISTORY_TURNS_FOR_PROMPT = 3
# Arayüze döndürülecek en fazla mesaj sayısı (en yeniler).
HISTORY_MESSAGES_FOR_UI = 100
# Bu kadar kelimeden kısa sorular "takip sorusu" olabilir; arama sorgusuna
# önceki soru da eklenir ("peki ikincisi?" tek başına aranamaz).
FOLLOW_UP_MAX_WORDS = 12


def get_history_messages(
    db: Session,
    user_id: int,
    document_id: int,
    limit: int = HISTORY_MESSAGES_FOR_UI,
) -> list[ChatMessage]:
    newest_first = (
        db.query(ChatMessage)
        .filter(ChatMessage.user_id == user_id)
        .filter(ChatMessage.document_id == document_id)
        .order_by(ChatMessage.id.desc())
        .limit(limit)
        .all()
    )
    return list(reversed(newest_first))


def get_recent_turns(
    db: Session,
    user_id: int,
    document_id: int,
    turns: int = HISTORY_TURNS_FOR_PROMPT,
) -> list[HistoryTurn]:
    """Son birkaç tamamlanmış soru-cevap çiftini eskiden yeniye döndürür."""
    messages = get_history_messages(db, user_id, document_id, limit=turns * 2 + 1)

    result: list[HistoryTurn] = []
    pending_question: str | None = None
    for message in messages:
        if message.role == "user":
            pending_question = message.content
        elif message.role == "assistant" and pending_question is not None:
            result.append(HistoryTurn(question=pending_question, answer=message.content))
            pending_question = None

    return result[-turns:]


def build_search_query(question: str, history: list[HistoryTurn]) -> str:
    """Takip sorularında aramayı önceki soruyla zenginleştirir."""
    if not history or len(question.split()) > FOLLOW_UP_MAX_WORDS:
        return question
    return f"{history[-1].question}\n{question}"


def save_exchange(
    db: Session,
    user_id: int,
    document_id: int,
    question: str,
    answer: str,
    sources: list[dict],
) -> None:
    db.add_all([
        ChatMessage(
            document_id=document_id,
            user_id=user_id,
            role="user",
            content=question,
        ),
        ChatMessage(
            document_id=document_id,
            user_id=user_id,
            role="assistant",
            content=answer,
            sources=sources,
        ),
    ])
    db.commit()


def clear_history(db: Session, user_id: int, document_id: int) -> int:
    deleted = (
        db.query(ChatMessage)
        .filter(ChatMessage.user_id == user_id)
        .filter(ChatMessage.document_id == document_id)
        .delete(synchronize_session=False)
    )
    db.commit()
    return deleted
