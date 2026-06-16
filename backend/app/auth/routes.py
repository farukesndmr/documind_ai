from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.database.connection import get_db
from app.users.schemas import UserCreate, UserResponse
from app.users.service import create_user, get_user_by_email


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
    existing_user = get_user_by_email(db, user_data.email)

    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email already registered"
        )

    new_user = create_user(db, user_data)

    return new_user