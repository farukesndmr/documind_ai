import hashlib
import secrets
from datetime import datetime, timedelta, timezone
from urllib.parse import urlencode

from app.core.config import settings


def create_email_verification_token() -> str:
    return secrets.token_urlsafe(32)


def hash_email_verification_token(token: str) -> str:
    return hashlib.sha256(token.encode("utf-8")).hexdigest()


def get_email_verification_expires_at() -> datetime:
    return datetime.now(timezone.utc) + timedelta(
        hours=settings.EMAIL_VERIFICATION_TOKEN_EXPIRE_HOURS
    )


def build_email_verification_url(token: str) -> str:
    query = urlencode({"token": token})
    frontend_url = settings.FRONTEND_URL.rstrip("/")
    return f"{frontend_url}/verify-email?{query}"