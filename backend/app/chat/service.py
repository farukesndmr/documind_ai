import re
from typing import Sequence

from fastapi import HTTPException
from sqlalchemy.orm import Session

from app.chat.llm_service import generate_answer_with_llm
from app.documents.models import Document, DocumentChunk


def _tokenize(text: str) -> list[str]:
    cleaned_text = re.sub(
        r"[^a-zA-Z0-9ğüşöçıİĞÜŞÖÇ]+",
        " ",
        text.lower()
    )

    return [
        word
        for word in cleaned_text.split()
        if len(word) > 2
    ]


def _score_chunk(content: str, question_tokens: list[str]) -> int:
    content_lower = content.lower()
    score = 0

    for token in question_tokens:
        score += content_lower.count(token)

    return score


def _select_relevant_chunks(
    chunks: Sequence[DocumentChunk],
    question: str,
    limit: int
) -> list[DocumentChunk]:
    if len(chunks) <= limit:
        return list(chunks)

    question_tokens = _tokenize(question)

    # Genel konu sorularında ilk chunk genelde çok değerlidir.
    selected_chunks: list[DocumentChunk] = [chunks[0]]

    remaining_chunks = list(chunks[1:])

    scored_chunks = [
        (
            _score_chunk(chunk.content, question_tokens),
            chunk.chunk_index,
            chunk
        )
        for chunk in remaining_chunks
    ]

    scored_chunks.sort(key=lambda item: (item[0], -item[1]), reverse=True)

    for score, _, chunk in scored_chunks:
        if len(selected_chunks) >= limit:
            break

        selected_chunks.append(chunk)

    selected_chunks.sort(key=lambda chunk: chunk.chunk_index)

    return selected_chunks


def _get_document_owner_id(document: Document) -> int | None:
    owner_id = getattr(document, "owner_id", None)

    if owner_id is not None:
        return owner_id

    user_id = getattr(document, "user_id", None)

    if user_id is not None:
        return user_id

    return None


def ask_question(
    db: Session,
    document_id: int,
    question: str,
    owner_id: int,
    limit: int = 5
):
    document = (
        db.query(Document)
        .filter(Document.id == document_id)
        .first()
    )

    if document is None:
        raise HTTPException(
            status_code=404,
            detail="Document not found."
        )

    document_owner_id = _get_document_owner_id(document)

    if document_owner_id is None or int(document_owner_id) != int(owner_id):
        raise HTTPException(
            status_code=404,
            detail="Document not found."
        )

    chunks = (
        db.query(DocumentChunk)
        .filter(DocumentChunk.document_id == document_id)
        .order_by(DocumentChunk.chunk_index.asc())
        .all()
    )

    if not chunks:
        raise HTTPException(
            status_code=404,
            detail="No text chunks found for this document."
        )

    selected_chunks = _select_relevant_chunks(
        chunks=chunks,
        question=question,
        limit=limit
    )

    answer = generate_answer_with_llm(
        question=question,
        chunks=selected_chunks
    )

    return answer, selected_chunks