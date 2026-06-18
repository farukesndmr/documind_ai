from sqlalchemy.orm import Session

from app.documents.models import Document, DocumentChunk


def create_document(
    db: Session,
    title: str,
    file_path: str,
    owner_id: int,
    extracted_text: str | None = None
):
    new_document = Document(
        title=title,
        file_path=file_path,
        owner_id=owner_id,
        extracted_text=extracted_text
    )

    db.add(new_document)
    db.commit()
    db.refresh(new_document)

    return new_document


def get_documents_by_user(db: Session, owner_id: int):
    return db.query(Document).filter(Document.owner_id == owner_id).all()


def create_document_chunks(
    db: Session,
    document_id: int,
    chunks: list[str]
):
    chunk_objects = []

    for index, chunk_text in enumerate(chunks):
        chunk = DocumentChunk(
            document_id=document_id,
            content=chunk_text,
            chunk_index=index
        )

        db.add(chunk)
        chunk_objects.append(chunk)

    db.commit()

    for chunk in chunk_objects:
        db.refresh(chunk)

    return chunk_objects


def get_chunks_by_document(db: Session, document_id: int):
    return (
        db.query(DocumentChunk)
        .filter(DocumentChunk.document_id == document_id)
        .order_by(DocumentChunk.chunk_index)
        .all()
    )