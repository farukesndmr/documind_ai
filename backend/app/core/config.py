from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    PROJECT_NAME: str = "DocuMind AI"
    API_VERSION: str = "0.1.0"

    DATABASE_URL: str = "postgresql://documind_user:documind_password@localhost:5432/documind_db"

    JWT_SECRET_KEY: str = "temporary-secret-key-change-later"
    JWT_ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30

    class Config:
        env_file = ".env"


settings = Settings()