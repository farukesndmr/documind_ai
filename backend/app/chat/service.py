from sqlalchemy.orm import Session

from app.chat.llm_service import generate_answer_with_llm
from app.documents.service import search_similar_chunks


def ask_question(
    db: Session,
    question: str,
    owner_id: int,
    limit: int = 5
):
    chunks = search_similar_chunks(
        db=db,
        query=question,
        owner_id=owner_id,
        limit=limit
    )

    answer = generate_answer_with_llm(
        question=question,
        chunks=chunks
    )

    return answer, chunks