from pathlib import Path

from pydantic import SecretStr
from pydantic_settings import BaseSettings, SettingsConfigDict


BACKEND_DIR = Path(__file__).resolve().parents[2]


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=BACKEND_DIR / ".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    # App
    PROJECT_NAME: str = "DocuMind AI"
    API_VERSION: str = "0.1.0"

    # Database
    DATABASE_URL: str

    # Auth / JWT
    SECRET_KEY: str
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30

    # Old auth compatibility
    @property
    def JWT_SECRET_KEY(self) -> str:
        return self.SECRET_KEY

    @property
    def JWT_ALGORITHM(self) -> str:
        return self.ALGORITHM

    @property
    def JWT_ACCESS_TOKEN_EXPIRE_MINUTES(self) -> int:
        return self.ACCESS_TOKEN_EXPIRE_MINUTES

    # LLM provider compatibility
    LOCAL_LLM_PROVIDER: str = "openai"

    # Ollama compatibility
    OLLAMA_BASE_URL: str = "http://localhost:11434"
    OLLAMA_MODEL: str = "llama3.2:3b"

    # OpenAI core
    OPENAI_API_KEY: SecretStr | None = None

    OPENAI_MODEL: str = "gpt-4o-mini"
    OPENAI_QA_MODEL: str = "gpt-4o-mini"
    OPENAI_SUMMARY_MODEL: str = "gpt-4o-mini"

    # OpenAI embeddings
    OPENAI_EMBEDDING_MODEL: str = "text-embedding-3-small"
    EMBEDDING_MODEL: str = "text-embedding-3-small"

    # OpenAI usage limit
    OPENAI_HARD_LIMIT_USD: float = 1.70

    # OpenAI estimated pricing values
    OPENAI_INPUT_PRICE_PER_1M: float = 0.15
    OPENAI_OUTPUT_PRICE_PER_1M: float = 0.60

    # OpenAI generation settings
    OPENAI_MAX_OUTPUT_TOKENS: int = 2600
    OPENAI_QA_MAX_OUTPUT_TOKENS: int = 2600
    OPENAI_SUMMARY_MAX_OUTPUT_TOKENS: int = 2600

    OPENAI_TEMPERATURE: float = 0.2
    OPENAI_QA_TEMPERATURE: float = 0.2
    OPENAI_SUMMARY_TEMPERATURE: float = 0.2

    @property
    def openai_api_key_value(self) -> str | None:
        if self.OPENAI_API_KEY is None:
            return None
        return self.OPENAI_API_KEY.get_secret_value()

    # Frontend / CORS
    FRONTEND_URL: str = "http://127.0.0.1:5173"

    BACKEND_CORS_ORIGINS: str = (
        "http://127.0.0.1:5173,"
        "http://localhost:5173,"
        "http://127.0.0.1:5174,"
        "http://localhost:5174"
    )

    @property
    def cors_origins(self) -> list[str]:
        origins = [
            origin.strip()
            for origin in self.BACKEND_CORS_ORIGINS.split(",")
            if origin.strip()
        ]

        if self.FRONTEND_URL and self.FRONTEND_URL not in origins:
            origins.append(self.FRONTEND_URL)

        return origins


settings = Settings()