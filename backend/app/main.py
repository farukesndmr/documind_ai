from fastapi import FastAPI

from app.chat.routes import router as chat_router
from app.auth.routes import router as auth_router
from app.core.config import settings
from app.database.connection import Base, engine
from app.documents import models as document_models
from app.documents.routes import router as documents_router
from app.users import models as user_models

Base.metadata.create_all(bind=engine)

app = FastAPI(
    title=settings.PROJECT_NAME,
    description="AI-powered document analysis platform",
    version=settings.API_VERSION
)

app.include_router(chat_router)
app.include_router(auth_router)
app.include_router(documents_router)


@app.get("/")
def root():
    return {"message": "DocuMind AI backend is running"}


@app.get("/health")
def health_check():
    return {"status": "ok"}