from sqlalchemy.orm import Session

from app.documents.service import search_similar_chunks


def build_basic_answer(question: str, chunks) -> str:
    if not chunks:
        return "Bu soruyla ilgili dokümanlarda uygun bir bilgi bulunamadı."

    context_preview = "\n\n".join(
        chunk.content for chunk in chunks[:3]
    )

    answer = (
        "Bu soruya göre dokümanlarda bulunan en alakalı bilgiler aşağıdadır. "
        "Şu an cevap, bulunan kaynak parçalardan oluşturulmuş basit bir özet formatındadır.\n\n"
        f"Soru: {question}\n\n"
        f"İlgili içerik:\n{context_preview}"
    )

    return answer


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

    answer = build_basic_answer(
        question=question,
        chunks=chunks
    )

    return answer, chunks