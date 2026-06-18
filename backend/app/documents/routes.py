import os
from uuid import uuid4

from fastapi import APIRouter, Depends, File, HTTPException, UploadFile, status
from sqlalchemy.orm import Session

from app.auth.dependencies import get_current_user
from app.database.connection import get_db
from app.documents.pdf_utils import extract_text_from_pdf
from app.documents.schemas import DocumentChunkResponse, DocumentResponse
from app.documents.service import (
    create_document,
    create_document_chunks,
    get_chunks_by_document,
    get_documents_by_user,
)
from app.documents.text_utils import split_text_into_chunks


router = APIRouter(
    prefix="/documents",
    tags=["Documents"]
)


UPLOAD_DIR = "uploads"


@router.post(
    "/upload",
    response_model=DocumentResponse,
    status_code=status.HTTP_201_CREATED
)
def upload_document(
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user)
):
    if file.content_type != "application/pdf":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Only PDF files are allowed"
        )

    os.makedirs(UPLOAD_DIR, exist_ok=True)

    unique_filename = f"{uuid4()}_{file.filename}"
    file_path = os.path.join(UPLOAD_DIR, unique_filename)

    with open(file_path, "wb") as buffer:
        buffer.write(file.file.read())

    extracted_text = extract_text_from_pdf(file_path)

    new_document = create_document(
        db=db,
        title=file.filename,
        file_path=file_path,
        owner_id=current_user.id,
        extracted_text=extracted_text
    )

    chunks = split_text_into_chunks(extracted_text)
    create_document_chunks(
        db=db,
        document_id=new_document.id,
        chunks=chunks
    )

    return new_document


@router.get(
    "",
    response_model=list[DocumentResponse]
)
def list_documents(
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user)
):
    documents = get_documents_by_user(
        db=db,
        owner_id=current_user.id
    )

    return documents


@router.get(
    "/{document_id}/chunks",
    response_model=list[DocumentChunkResponse]
)
def list_document_chunks(
    document_id: int,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user)
):
    documents = get_documents_by_user(
        db=db,
        owner_id=current_user.id
    )

    document_ids = [document.id for document in documents]

    if document_id not in document_ids:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Document not found"
        )

    chunks = get_chunks_by_document(
        db=db,
        document_id=document_id
    )

    return chunks