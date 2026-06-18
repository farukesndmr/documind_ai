from sqlalchemy.orm import Session

from app.documents.models import Document


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