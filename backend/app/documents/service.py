from sqlalchemy.orm import Session

from app.documents.embedding_utils import generate_embedding
from app.documents.models import Document, DocumentChunk


def create_document(
    db: Session,
    title: str,
    file_path: str,
    owner_id: int,
    extracted_text: str | None = None,
):
    new_document = Document(
        title=title,
        file_path=file_path,
        owner_id=owner_id,
        extracted_text=extracted_text,
    )

    db.add(new_document)
    db.commit()
    db.refresh(new_document)

    return new_document


def get_documents_by_user(
    db: Session,
    owner_id: int,
):
    return (
        db.query(Document)
        .filter(Document.owner_id == owner_id)
        .order_by(Document.created_at.desc())
        .all()
    )


def get_document_by_id_and_owner(
    db: Session,
    document_id: int,
    owner_id: int,
):
    return (
        db.query(Document)
        .filter(
            Document.id == document_id,
            Document.owner_id == owner_id,
        )
        .first()
    )


def create_document_chunks(
    db: Session,
    document_id: int,
    chunks: list[str],
):
    chunk_objects = []

    for index, chunk_text in enumerate(chunks):
        embedding = generate_embedding(chunk_text)

        chunk = DocumentChunk(
            document_id=document_id,
            content=chunk_text,
            chunk_index=index,
            embedding=embedding,
        )

        db.add(chunk)
        chunk_objects.append(chunk)

    db.commit()

    for chunk in chunk_objects:
        db.refresh(chunk)

    return chunk_objects


def get_chunks_by_document(
    db: Session,
    document_id: int,
):
    return (
        db.query(DocumentChunk)
        .filter(DocumentChunk.document_id == document_id)
        .order_by(DocumentChunk.chunk_index)
        .all()
    )


def search_similar_chunks(
    db: Session,
    query: str,
    owner_id: int,
    limit: int = 5,
):
    query_embedding = generate_embedding(query)

    return (
        db.query(DocumentChunk)
        .join(
            Document,
            DocumentChunk.document_id == Document.id,
        )
        .filter(Document.owner_id == owner_id)
        .filter(DocumentChunk.embedding.isnot(None))
        .order_by(
            DocumentChunk.embedding.cosine_distance(
                query_embedding,
            )
        )
        .limit(limit)
        .all()
    )


def delete_document_by_owner(
    db: Session,
    document_id: int,
    owner_id: int,
) -> str | None:
    document = get_document_by_id_and_owner(
        db=db,
        document_id=document_id,
        owner_id=owner_id,
    )

    if document is None:
        return None

    file_path = document.file_path

    try:
        (
            db.query(DocumentChunk)
            .filter(
                DocumentChunk.document_id == document_id
            )
            .delete(synchronize_session=False)
        )

        db.delete(document)
        db.commit()

    except Exception:
        db.rollback()
        raise

    return file_path