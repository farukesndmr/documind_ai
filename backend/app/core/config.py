from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict


BACKEND_DIR = Path(__file__).resolve().parents[2]


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=BACKEND_DIR / ".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    PROJECT_NAME: str = "DocuMind AI"
    API_VERSION: str = "0.1.0"

    DATABASE_URL: str

    SECRET_KEY: str
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30

    OPENAI_API_KEY: str | None = None
    OPENAI_MODEL: str = "gpt-4o-mini"

    OPENAI_HARD_LIMIT_USD: float = 1.70

    OPENAI_MAX_OUTPUT_TOKENS: int = 2600
    OPENAI_QA_MAX_OUTPUT_TOKENS: int = 2600
    OPENAI_SUMMARY_MAX_OUTPUT_TOKENS: int = 2600

    OPENAI_TEMPERATURE: float = 0.2
    OPENAI_QA_TEMPERATURE: float = 0.2
    OPENAI_SUMMARY_TEMPERATURE: float = 0.2

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

    @property
    def JWT_SECRET_KEY(self) -> str:
        return self.SECRET_KEY

    @property
    def JWT_ALGORITHM(self) -> str:
        return self.ALGORITHM

    @property
    def JWT_ACCESS_TOKEN_EXPIRE_MINUTES(self) -> int:
        return self.ACCESS_TOKEN_EXPIRE_MINUTES


settings = Settings()