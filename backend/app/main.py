from fastapi import FastAPI

from app.auth.routes import router as auth_router
from app.core.config import settings
from app.database.connection import Base, engine
from app.users import models

Base.metadata.create_all(bind=engine)

app = FastAPI(
    title=settings.PROJECT_NAME,
    description="AI-powered document analysis platform",
    version=settings.API_VERSION
)

app.include_router(auth_router)


@app.get("/")
def root():
    return {"message": "DocuMind AI backend is running"}


@app.get("/health")
def health_check():
    return {"status": "ok"}