import logging
import shutil
import tempfile
from pathlib import Path

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
from app.documents.pdf_utils import extract_pages_from_pdf
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
from app.documents.text_utils import split_pages_into_chunks


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
            detail="Yalnızca PDF dosyaları yüklenebilir.",
        )

    file_size_bytes = get_upload_file_size_bytes(file)
    ensure_pdf_size_allowed(file_size_bytes)

    # Dosyanın gerçekten PDF olduğunu içeriğinden doğrula (uzantıya/başlığa güvenme).
    if file.file.read(5) != b"%PDF-":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Dosya geçerli bir PDF değil.",
        )
    file.file.seek(0)

    original_filename = Path(file.filename or "document.pdf").name

    # PDF yalnızca metni çıkarmak için geçici bir dosyaya yazılır ve hemen silinir.
    # Render gibi platformlarda disk kalıcı olmadığından dosyayı saklamak anlamsızdı;
    # gereken her şey (metin, parçalar, embedding'ler) veritabanında tutuluyor.
    with tempfile.NamedTemporaryFile(suffix=".pdf", delete=False) as tmp:
        shutil.copyfileobj(file.file, tmp)
        temp_path = Path(tmp.name)

    try:
        try:
            pages = extract_pages_from_pdf(str(temp_path))
        except Exception as exc:
            logger.warning("PDF okunamadı: %s", exc)
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="PDF okunamadı. Dosya bozuk veya şifreli olabilir.",
            ) from exc
    finally:
        temp_path.unlink(missing_ok=True)

    if not pages:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=(
                "Bu PDF'ten metin çıkarılamadı. Taranmış (resim) bir belge olabilir; "
                "metin içeren bir PDF yükleyin."
            ),
        )

    chunks = split_pages_into_chunks(pages)

    new_document = create_document(
        db=db,
        title=original_filename,
        file_path="",
        owner_id=current_user.id,
        extracted_text="\n\n".join(text for _, text in pages),
    )

    try:
        create_document_chunks(
            db=db,
            document_id=new_document.id,
            chunks=chunks,
        )
    except Exception:
        # Parçalar kaydedilemediyse yarım kalmış belgeyi geri al.
        db.rollback()
        delete_document_by_owner(
            db=db,
            document_id=new_document.id,
            owner_id=current_user.id,
        )
        raise

    increment_pdf_upload_count(
        db=db,
        user=current_user,
    )

    logger.info(
        "Belge yüklendi: id=%s, %d sayfa, %d parça",
        new_document.id, len(pages), len(chunks),
    )

    return new_document


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

    file_deleted = False

    # Yeni yüklenen belgeler diskte saklanmıyor (file_path boş).
    # Eski belgelerin dosyası hâlâ duruyorsa silinir.
    if not stored_file_path:
        return {
            "message": "Document deleted successfully",
            "document_id": document_id,
            "file_deleted": file_deleted,
        }

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