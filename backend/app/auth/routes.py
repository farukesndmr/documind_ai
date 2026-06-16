from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from fastapi.security import OAuth2PasswordRequestForm
from app.auth.dependencies import get_current_user
from app.auth.schemas import LoginRequest, TokenResponse
from app.auth.security import create_access_token
from app.database.connection import get_db
from app.users.schemas import UserCreate, UserResponse
from app.users.service import (
    authenticate_user,
    create_user,
    get_user_by_email,
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
    existing_user = get_user_by_email(db, user_data.email)

    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email already registered"
        )

    new_user = create_user(db, user_data)

    return new_user


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