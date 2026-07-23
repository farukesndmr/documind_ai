from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from app.core.config import settings
from app.users.models import User


def ensure_user_can_use_app(user: User) -> None:
    if user.is_admin:
        return

    if not user.email_verified:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Please verify your email before using DocuMind AI.",
        )

    if not user.is_approved or user.approval_status != "approved":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Your account is waiting for admin approval.",
        )


def ensure_can_upload_pdf(user: User) -> None:
    ensure_user_can_use_app(user)

    if user.is_admin:
        return

    if user.pdf_upload_count >= settings.DEMO_PDF_UPLOAD_LIMIT:
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail=(
                f"PDF upload limit reached. "
                f"You can upload {settings.DEMO_PDF_UPLOAD_LIMIT} PDF file."
            ),
        )


def ensure_can_ask_question(user: User) -> None:
    ensure_user_can_use_app(user)

    if user.is_admin:
        return

    if user.question_count >= settings.DEMO_QUESTION_LIMIT:
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail=(
                f"Question limit reached. "
                f"You can ask {settings.DEMO_QUESTION_LIMIT} questions in this demo."
            ),
        )


def ensure_pdf_size_allowed(file_size_bytes: int) -> None:
    if file_size_bytes > settings.demo_max_pdf_size_bytes:
        raise HTTPException(
            status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
            detail=(
                f"PDF file is too large. "
                f"Maximum allowed size is {settings.DEMO_MAX_PDF_SIZE_MB} MB."
            ),
        )


def increment_pdf_upload_count(db: Session, user: User) -> User:
    if user.is_admin:
        return user

    user.pdf_upload_count += 1
    db.commit()
    db.refresh(user)
    return user


def increment_question_count(db: Session, user: User) -> User:
    if user.is_admin:
        return user

    user.question_count += 1
    db.commit()
    db.refresh(user)
    return user