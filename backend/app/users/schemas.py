from pydantic import BaseModel, EmailStr


class UserCreate(BaseModel):
    email: EmailStr
    password: str


class UserResponse(BaseModel):
    id: int
    email: EmailStr

    role: str
    email_verified: bool
    is_approved: bool
    approval_status: str

    pdf_upload_count: int
    question_count: int

    can_use_app: bool
    is_active: bool

    class Config:
        from_attributes = True