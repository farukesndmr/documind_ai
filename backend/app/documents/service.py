import logging

from sqlalchemy import or_
from sqlalchemy.orm import Session

from app.documents.embedding_utils import (
    EmbeddingError,
    current_embedding_model,
    embed_query,
    embed_texts,
)
from app.documents.models import Document, DocumentChunk
from app.documents.text_utils import TextChunk


logger = logging.getLogger(__name__)


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
    chunks: list[TextChunk],
):
    """Parçaları kaydeder ve embedding'lerini tek seferde (batch) üretir.

    Embedding servisine ulaşılamazsa parçalar yine de kaydedilir; anahtar
    kelime araması çalışmaya devam eder ve embedding'ler ilk soruda tekrar denenir.
    """
    embeddings: list[list[float]] | None = None
    model_name: str | None = None

    try:
        embeddings = embed_texts([chunk.content for chunk in chunks])
        model_name = current_embedding_model()
    except EmbeddingError:
        logger.warning(
            "Belge %s için embedding üretilemedi; parçalar embedding'siz kaydediliyor.",
            document_id,
        )

    chunk_objects = [
        DocumentChunk(
            document_id=document_id,
            content=chunk.content,
            chunk_index=index,
            page_number=chunk.page_number,
            embedding=embeddings[index] if embeddings else None,
            embedding_model=model_name,
        )
        for index, chunk in enumerate(chunks)
    ]

    db.add_all(chunk_objects)
    db.commit()

    return chunk_objects


def ensure_document_embeddings(db: Session, document_id: int) -> bool:
    """Belgenin eksik ya da eski modelle üretilmiş embedding'lerini tamamlar.

    Eski sürümde yüklenen belgeler anlamsız (hash tabanlı) vektörlere sahipti;
    bu fonksiyon onları ilk soruda bir kez gerçek embedding'lerle değiştirir.
    True dönerse belgenin tüm parçaları vektör aramaya hazırdır.
    """
    model_name = current_embedding_model()

    stale_chunks = (
        db.query(DocumentChunk)
        .filter(DocumentChunk.document_id == document_id)
        .filter(
            or_(
                DocumentChunk.embedding_model.is_(None),
                DocumentChunk.embedding_model != model_name,
                DocumentChunk.embedding.is_(None),
            )
        )
        .order_by(DocumentChunk.chunk_index)
        .all()
    )

    if not stale_chunks:
        return True

    try:
        vectors = embed_texts([chunk.content for chunk in stale_chunks])
    except EmbeddingError:
        return False

    for chunk, vector in zip(stale_chunks, vectors, strict=True):
        chunk.embedding = vector
        chunk.embedding_model = model_name

    db.commit()
    logger.info(
        "Belge %s: %d parça yeniden embed edildi.", document_id, len(stale_chunks)
    )
    return True


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
    try:
        query_embedding = embed_query(query)
    except EmbeddingError:
        return []

    return (
        db.query(DocumentChunk)
        .join(
            Document,
            DocumentChunk.document_id == Document.id,
        )
        .filter(Document.owner_id == owner_id)
        .filter(DocumentChunk.embedding.isnot(None))
        .filter(DocumentChunk.embedding_model == current_embedding_model())
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