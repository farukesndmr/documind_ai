from fastapi import HTTPException
from sqlalchemy.orm import Session

from app.documents.models import Document
from app.rag.llm import generate_with_llm
from app.rag.prompt_builder import build_prompt
from app.rag.retriever import retrieve_context_chunks


def get_document_owner_id(document: Document) -> int | None:
    owner_id = getattr(document, "owner_id", None)

    if owner_id is not None:
        return owner_id

    user_id = getattr(document, "user_id", None)

    if user_id is not None:
        return user_id

    return None


def get_user_document(
    db: Session,
    document_id: int,
    owner_id: int,
) -> Document:
    document = (
        db.query(Document)
        .filter(Document.id == document_id)
        .first()
    )

    if document is None:
        raise HTTPException(
            status_code=404,
            detail="Document not found.",
        )

    document_owner_id = get_document_owner_id(document)

    if document_owner_id is None or int(document_owner_id) != int(owner_id):
        raise HTTPException(
            status_code=404,
            detail="Document not found.",
        )

    return document


def answer_question_with_rag(
    db: Session,
    document_id: int,
    question: str,
    owner_id: int,
    limit: int = 8,
):
    get_user_document(
        db=db,
        document_id=document_id,
        owner_id=owner_id,
    )

    chunks, mode = retrieve_context_chunks(
        db=db,
        document_id=document_id,
        question=question,
        limit=limit,
    )

    if not chunks:
        raise HTTPException(
            status_code=404,
            detail="No chunks found for this document.",
        )

    prompt = build_prompt(
        question=question,
        chunks=chunks,
        mode=mode,
    )

    answer = generate_with_llm(
        prompt=prompt,
        mode=mode,
    )

    return answer, chunks