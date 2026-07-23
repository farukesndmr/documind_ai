import logging
import shutil
from pathlib import Path
from uuid import uuid4

from fastapi import (
    APIRouter,
    Depends,
    File,
    HTTPException,
    UploadFile,
    status,
)
from sqlalchemy.orm import Session

from app.auth.access_control import (
    ensure_can_upload_pdf,
    ensure_pdf_size_allowed,
    ensure_user_can_use_app,
    increment_pdf_upload_count,
)
from app.auth.dependencies import get_current_user
from app.database.connection import get_db
from app.documents.pdf_utils import extract_text_from_pdf
from app.documents.schemas import (
    ChunkSearchRequest,
    DocumentChunkResponse,
    DocumentResponse,
)
from app.documents.service import (
    create_document,
    create_document_chunks,
    delete_document_by_owner,
    get_chunks_by_document,
    get_documents_by_user,
    search_similar_chunks,
)
from app.documents.text_utils import split_text_into_chunks


router = APIRouter(
    prefix="/documents",
    tags=["Documents"],
)

logger = logging.getLogger(__name__)

BACKEND_DIR = Path(__file__).resolve().parents[2]
UPLOAD_DIR = BACKEND_DIR / "uploads"


def get_upload_file_size_bytes(file: UploadFile) -> int:
    file.file.seek(0, 2)
    file_size = file.file.tell()
    file.file.seek(0)
    return file_size


@router.post(
    "/upload",
    response_model=DocumentResponse,
    status_code=status.HTTP_201_CREATED,
)
def upload_document(
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    ensure_can_upload_pdf(current_user)

    if file.content_type != "application/pdf":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Only PDF files are allowed",
        )

    file_size_bytes = get_upload_file_size_bytes(file)
    ensure_pdf_size_allowed(file_size_bytes)

    UPLOAD_DIR.mkdir(
        parents=True,
        exist_ok=True,
    )

    original_filename = Path(
        file.filename or "document.pdf"
    ).name

    unique_filename = (
        f"{uuid4()}_{original_filename}"
    )

    file_path = UPLOAD_DIR / unique_filename

    try:
        with file_path.open("wb") as buffer:
            shutil.copyfileobj(
                file.file,
                buffer,
            )

        extracted_text = extract_text_from_pdf(
            str(file_path)
        )

        new_document = create_document(
            db=db,
            title=original_filename,
            file_path=str(file_path),
            owner_id=current_user.id,
            extracted_text=extracted_text,
        )

        chunks = split_text_into_chunks(
            extracted_text
        )

        create_document_chunks(
            db=db,
            document_id=new_document.id,
            chunks=chunks,
        )

        increment_pdf_upload_count(
            db=db,
            user=current_user,
        )

        return new_document

    except Exception:
        if file_path.exists():
            try:
                file_path.unlink()
            except OSError:
                logger.exception(
                    "Failed to remove incomplete PDF upload."
                )

        raise

    finally:
        file.file.close()


@router.get(
    "",
    response_model=list[DocumentResponse],
)
def list_documents(
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    ensure_user_can_use_app(current_user)

    return get_documents_by_user(
        db=db,
        owner_id=current_user.id,
    )


@router.post(
    "/search",
    response_model=list[DocumentChunkResponse],
)
def search_documents(
    search_data: ChunkSearchRequest,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    ensure_user_can_use_app(current_user)

    return search_similar_chunks(
        db=db,
        query=search_data.query,
        owner_id=current_user.id,
        limit=search_data.limit,
    )


@router.delete(
    "/{document_id}",
    status_code=status.HTTP_200_OK,
)
def delete_document(
    document_id: int,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    ensure_user_can_use_app(current_user)

    stored_file_path = delete_document_by_owner(
        db=db,
        document_id=document_id,
        owner_id=current_user.id,
    )

    if stored_file_path is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Document not found",
        )

    file_deleted = True

    try:
        pdf_path = Path(stored_file_path)

        if not pdf_path.is_absolute():
            pdf_path = BACKEND_DIR / pdf_path

        resolved_pdf_path = pdf_path.resolve()
        resolved_upload_dir = UPLOAD_DIR.resolve()

        is_inside_upload_directory = (
            resolved_upload_dir
            in resolved_pdf_path.parents
        )

        if not is_inside_upload_directory:
            file_deleted = False

            logger.warning(
                "Blocked deletion outside upload directory: %s",
                resolved_pdf_path,
            )

        elif resolved_pdf_path.exists():
            resolved_pdf_path.unlink()

    except OSError:
        file_deleted = False

        logger.exception(
            "Database record was deleted, but PDF file "
            "could not be removed: %s",
            stored_file_path,
        )

    return {
        "message": "Document deleted successfully",
        "document_id": document_id,
        "file_deleted": file_deleted,
    }


@router.get(
    "/{document_id}/chunks",
    response_model=list[DocumentChunkResponse],
)
def list_document_chunks(
    document_id: int,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    ensure_user_can_use_app(current_user)

    documents = get_documents_by_user(
        db=db,
        owner_id=current_user.id,
    )

    document_ids = [
        document.id
        for document in documents
    ]

    if document_id not in document_ids:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Document not found",
        )

    return get_chunks_by_document(
        db=db,
        document_id=document_id,
    )