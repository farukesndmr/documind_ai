from datetime import datetime, timezone

from sqlalchemy.orm import Session

from app.auth.security import hash_password, verify_password
from app.users.models import User
from app.users.schemas import UserCreate


def get_user_by_id(db: Session, user_id: int):
    return db.query(User).filter(User.id == user_id).first()


def get_user_by_email(db: Session, email: str):
    normalized_email = email.lower().strip()
    return db.query(User).filter(User.email == normalized_email).first()


def get_user_by_email_verification_token_hash(db: Session, token_hash: str):
    return (
        db.query(User)
        .filter(User.email_verification_token_hash == token_hash)
        .first()
    )


def get_pending_users(db: Session):
    return (
        db.query(User)
        .filter(User.role == "user")
        .filter(User.email_verified == True)  # noqa: E712
        .filter(User.approval_status == "pending")
        .order_by(User.created_at.desc())
        .all()
    )


def get_all_users(db: Session):
    return db.query(User).order_by(User.created_at.desc()).all()


def create_user(
    db: Session,
    user_data: UserCreate,
    *,
    email_verification_token_hash: str | None = None,
    email_verification_expires_at=None,
):
    hashed_password = hash_password(user_data.password)
    normalized_email = str(user_data.email).lower().strip()

    new_user = User(
        email=normalized_email,
        hashed_password=hashed_password,
        role="user",
        email_verified=False,
        email_verified_at=None,
        email_verification_token_hash=email_verification_token_hash,
        email_verification_expires_at=email_verification_expires_at,
        last_verification_email_sent_at=datetime.now(timezone.utc),
        is_approved=False,
        approval_status="pending",
        pdf_upload_count=0,
        question_count=0,
    )

    db.add(new_user)
    db.commit()
    db.refresh(new_user)

    return new_user


def mark_user_email_verified(db: Session, user: User):
    user.email_verified = True
    user.email_verified_at = datetime.now(timezone.utc)
    user.email_verification_token_hash = None
    user.email_verification_expires_at = None

    db.commit()
    db.refresh(user)

    return user


def approve_user(db: Session, user: User, admin_user: User):
    user.is_approved = True
    user.approval_status = "approved"
    user.approved_at = datetime.now(timezone.utc)
    user.approved_by = admin_user.id

    user.rejected_at = None
    user.rejected_by = None

    db.commit()
    db.refresh(user)

    return user


def reject_user(db: Session, user: User, admin_user: User):
    user.is_approved = False
    user.approval_status = "rejected"
    user.rejected_at = datetime.now(timezone.utc)
    user.rejected_by = admin_user.id

    db.commit()
    db.refresh(user)

    return user


def authenticate_user(db: Session, email: str, password: str):
    user = get_user_by_email(db, email)

    if not user:
        return None

    if not verify_password(password, user.hashed_password):
        return None

    return user