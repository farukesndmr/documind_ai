from datetime import datetime, timezone
from app.auth.google import verify_google_credential
from fastapi import APIRouter, Depends, HTTPException, Query, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session

from app.auth.dependencies import get_current_user
from app.auth.email_verification import (
    build_email_verification_url,
    create_email_verification_token,
    get_email_verification_expires_at,
    hash_email_verification_token,
)
from app.auth.schemas import GoogleLoginRequest, TokenResponse, VerifyEmailResponse
from app.auth.security import create_access_token
from app.core.email import send_verification_email
from app.database.connection import get_db
from app.users.schemas import UserCreate, UserResponse
from app.users.service import (
    authenticate_user,
    create_user,
    get_or_create_google_user,
    get_user_by_email,
    get_user_by_email_verification_token_hash,
    mark_user_email_verified,
)


router = APIRouter(
    prefix="/auth",
    tags=["Auth"]
)


@router.get("/test")
def auth_test():
    return {"message": "Auth router is working"}


@router.post(
    "/register",
    response_model=UserResponse,
    status_code=status.HTTP_201_CREATED
)
def register(user_data: UserCreate, db: Session = Depends(get_db)):
    existing_user = get_user_by_email(db, str(user_data.email))

    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email already registered"
        )

    verification_token = create_email_verification_token()
    verification_token_hash = hash_email_verification_token(verification_token)
    verification_expires_at = get_email_verification_expires_at()

    new_user = create_user(
        db=db,
        user_data=user_data,
        email_verification_token_hash=verification_token_hash,
        email_verification_expires_at=verification_expires_at,
    )

    verification_url = build_email_verification_url(verification_token)

    try:
        email_sent = send_verification_email(
        to_email=new_user.email,
        verification_url=verification_url,
    )

        if not email_sent:
            print(
            "Verification email could not be sent. "
            "Email provider is probably not configured yet."
        )

    except Exception as exc:
        print(f"Verification email could not be sent: {exc}")

    return new_user


@router.get(
    "/verify-email",
    response_model=VerifyEmailResponse
)
def verify_email(
    token: str = Query(..., min_length=10),
    db: Session = Depends(get_db)
):
    token_hash = hash_email_verification_token(token)
    user = get_user_by_email_verification_token_hash(db, token_hash)

    if not user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid or expired verification token"
        )

    if user.email_verified:
        return {
            "message": "Email is already verified.",
            "email_verified": True,
            "approval_status": user.approval_status,
        }

    expires_at = user.email_verification_expires_at

    if expires_at is None:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Verification token has expired"
        )

    if expires_at.tzinfo is None:
        expires_at = expires_at.replace(tzinfo=timezone.utc)

    if expires_at < datetime.now(timezone.utc):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Verification token has expired"
        )

    mark_user_email_verified(db, user)

    return {
        "message": "Email verified successfully. Your account is waiting for admin approval.",
        "email_verified": True,
        "approval_status": user.approval_status,
    }


@router.post(
    "/login",
    response_model=TokenResponse
)
def login(
    form_data: OAuth2PasswordRequestForm = Depends(),
    db: Session = Depends(get_db)
):
    user = authenticate_user(
        db=db,
        email=form_data.username,
        password=form_data.password
    )

    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password"
        )

    access_token = create_access_token(
        data={"sub": user.email}
    )

    return {
        "access_token": access_token,
        "token_type": "bearer"
    }


@router.get(
    "/me",
    response_model=UserResponse
)
def get_me(current_user=Depends(get_current_user)):
    return current_user

@router.post(
    "/google-login",
    response_model=TokenResponse,
)
def google_login(
    request_data: GoogleLoginRequest,
    db: Session = Depends(get_db),
):
    try:
        google_user_info = verify_google_credential(
            request_data.credential
        )
    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=str(exc),
        ) from exc

    user = get_or_create_google_user(
        db=db,
        email=google_user_info["email"],
    )

    access_token = create_access_token(
        data={"sub": user.email}
    )

    return {
        "access_token": access_token,
        "token_type": "bearer",
    }