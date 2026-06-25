import re
from typing import Sequence

from sqlalchemy.orm import Session

from app.documents.models import DocumentChunk


SUMMARY_KEYWORDS = [
    "özet",
    "özetle",
    "özetini",
    "summary",
    "summarize",
    "ders notu",
    "sınav",
    "exam",
    "çalışma notu",
    "konu anlatımı",
    "detaylı anlat",
    "detaylı özet",
]


STOP_WORDS = {
    "bana",
    "şunu",
    "bunu",
    "için",
    "olan",
    "nedir",
    "midir",
    "pdf",
    "doküman",
    "döküman",
    "belge",
    "çıkar",
    "çıkarır",
    "misin",
    "musun",
    "kısa",
    "detaylı",
    "türkçe",
    "ingilizce",
    "cümle",
    "kullanma",
}


def is_summary_request(question: str) -> bool:
    question_lower = question.lower()
    return any(keyword in question_lower for keyword in SUMMARY_KEYWORDS)


def tokenize(text: str) -> list[str]:
    cleaned_text = re.sub(
        r"[^a-zA-Z0-9ğüşöçıİĞÜŞÖÇ]+",
        " ",
        text.lower(),
    )

    return [
        word
        for word in cleaned_text.split()
        if len(word) > 2 and word not in STOP_WORDS
    ]


def score_chunk(content: str, question_tokens: list[str]) -> int:
    content_lower = content.lower()
    score = 0

    for token in question_tokens:
        score += content_lower.count(token)

    return score


def get_document_chunks(
    db: Session,
    document_id: int,
) -> list[DocumentChunk]:
    return (
        db.query(DocumentChunk)
        .filter(DocumentChunk.document_id == document_id)
        .order_by(DocumentChunk.chunk_index.asc())
        .all()
    )


def limit_by_char_count(
    chunks: Sequence[DocumentChunk],
    max_chars: int,
) -> list[DocumentChunk]:
    selected_chunks: list[DocumentChunk] = []
    total_chars = 0

    for chunk in chunks:
        content = chunk.content or ""
        content_length = len(content)

        if selected_chunks and total_chars + content_length > max_chars:
            break

        selected_chunks.append(chunk)
        total_chars += content_length

    return selected_chunks


def select_summary_chunks(
    chunks: Sequence[DocumentChunk],
    limit: int = 12,
) -> list[DocumentChunk]:
    if not chunks:
        return []

    total_chunks = len(chunks)

    if total_chunks <= limit:
        return limit_by_char_count(chunks, max_chars=14000)

    selected_indexes = set()

    # Başlangıç kısmı genelde konu başlığı ve giriş içerir.
    selected_indexes.add(0)

    # PDF'in geneline yayılmış chunk seç.
    step = max(total_chunks // limit, 1)

    for index in range(0, total_chunks, step):
        selected_indexes.add(index)

        if len(selected_indexes) >= limit:
            break

    selected_chunks = [
        chunks[index]
        for index in sorted(selected_indexes)
        if index < total_chunks
    ]

    return limit_by_char_count(selected_chunks, max_chars=14000)


def select_question_chunks(
    chunks: Sequence[DocumentChunk],
    question: str,
    limit: int = 8,
) -> list[DocumentChunk]:
    if not chunks:
        return []

    if len(chunks) <= limit:
        return limit_by_char_count(chunks, max_chars=10000)

    question_tokens = tokenize(question)

    scored_chunks = [
        (
            score_chunk(chunk.content or "", question_tokens),
            chunk.chunk_index,
            chunk,
        )
        for chunk in chunks
    ]

    scored_chunks.sort(
        key=lambda item: (item[0], -item[1]),
        reverse=True,
    )

    selected_chunks = [
        chunk
        for score, _, chunk in scored_chunks[:limit]
    ]

    selected_chunks.sort(key=lambda chunk: chunk.chunk_index)

    return limit_by_char_count(selected_chunks, max_chars=10000)


def retrieve_context_chunks(
    db: Session,
    document_id: int,
    question: str,
    limit: int = 8,
) -> tuple[list[DocumentChunk], str]:
    chunks = get_document_chunks(
        db=db,
        document_id=document_id,
    )

    if is_summary_request(question):
        selected_chunks = select_summary_chunks(
            chunks=chunks,
            limit=max(limit, 12),
        )
        return selected_chunks, "summary"

    selected_chunks = select_question_chunks(
        chunks=chunks,
        question=question,
        limit=min(limit, 8),
    )

    return selected_chunks, "qa"