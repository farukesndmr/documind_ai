from pydantic import BaseModel, EmailStr


class LoginRequest(BaseModel):
    email: EmailStr
    password: str


class TokenResponse(BaseModel):
    access_token: str
    token_type: str


class VerifyEmailResponse(BaseModel):
    message: str
    email_verified: bool
    approval_status: str | None = None

class GoogleLoginRequest(BaseModel):
    credential: str