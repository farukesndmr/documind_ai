from pathlib import Path

from pydantic import SecretStr
from pydantic_settings import BaseSettings, SettingsConfigDict


BACKEND_DIR = Path(__file__).resolve().parents[2]


class Settings(BaseSettings):
    PROJECT_NAME: str = "DocuMind AI"
    API_VERSION: str = "0.1.0"

    DATABASE_URL: str = (
        "postgresql://documind_user:"
        "documind_password@localhost:5432/documind_db"
    )

    JWT_SECRET_KEY: str = "temporary-secret-key-change-later"
    JWT_ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30

    # Mevcut Ollama ayarlarını uyumluluk için tutuyoruz.
    LOCAL_LLM_PROVIDER: str = "openai"
    OLLAMA_MODEL: str = "qwen3:8b"

    # OpenAI
    OPENAI_API_KEY: SecretStr | None = None
    OPENAI_MODEL: str = "gpt-5.6-luna"

    # OpenAI projesinde limitin 2 dolar.
    # Uygulama tarafında güvenlik payıyla 1.70 dolarda durduruyoruz.
    OPENAI_HARD_LIMIT_USD: float = 1.70

    OPENAI_INPUT_PRICE_PER_1M: float = 1.00
    OPENAI_OUTPUT_PRICE_PER_1M: float = 6.00

    OPENAI_QA_MAX_OUTPUT_TOKENS: int = 1000
    OPENAI_SUMMARY_MAX_OUTPUT_TOKENS: int = 1800

    model_config = SettingsConfigDict(
        env_file=BACKEND_DIR / ".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )


settings = Settings()