from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.auth.dependencies import get_current_user
from app.database.connection import get_db
from app.users.models import User
from app.users.schemas import UserResponse
from app.users.service import (
    approve_user,
    get_all_users,
    get_pending_users,
    get_user_by_id,
    reject_user,
)


router = APIRouter(
    prefix="/admin",
    tags=["Admin"],
)


def require_admin(current_user: User = Depends(get_current_user)) -> User:
    if current_user.role != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin access required",
        )

    return current_user


@router.get(
    "/users",
    response_model=list[UserResponse],
)
def list_users(
    db: Session = Depends(get_db),
    admin_user: User = Depends(require_admin),
):
    return get_all_users(db)


@router.get(
    "/users/pending",
    response_model=list[UserResponse],
)
def list_pending_users(
    db: Session = Depends(get_db),
    admin_user: User = Depends(require_admin),
):
    return get_pending_users(db)


@router.patch(
    "/users/{user_id}/approve",
    response_model=UserResponse,
)
def approve_user_access(
    user_id: int,
    db: Session = Depends(get_db),
    admin_user: User = Depends(require_admin),
):
    user = get_user_by_id(db, user_id)

    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found",
        )

    if user.role == "admin":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Admin users do not need approval",
        )

    return approve_user(db, user, admin_user)


@router.patch(
    "/users/{user_id}/reject",
    response_model=UserResponse,
)
def reject_user_access(
    user_id: int,
    db: Session = Depends(get_db),
    admin_user: User = Depends(require_admin),
):
    user = get_user_by_id(db, user_id)

    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found",
        )

    if user.role == "admin":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Admin users cannot be rejected",
        )

    return reject_user(db, user, admin_user)