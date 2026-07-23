from google.auth.transport import requests
from google.oauth2 import id_token

from app.core.config import settings


def verify_google_credential(credential: str) -> dict:
    """
    Google Identity Services tarafından frontend'e verilen ID token'ı doğrular.
    Başarılıysa Google user bilgilerini döndürür.
    """
    idinfo = id_token.verify_oauth2_token(
        credential,
        requests.Request(),
        settings.GOOGLE_CLIENT_ID,
    )

    if not idinfo.get("email"):
        raise ValueError("Google account does not include an email address.")

    if not idinfo.get("email_verified"):
        raise ValueError("Google email is not verified.")

    return idinfo