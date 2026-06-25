from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.core.config import settings
from app.database.connection import Base, engine

from app.users import models as user_models
from app.documents import models as document_models

from app.auth.routes import router as auth_router
from app.documents.routes import router as documents_router
from app.chat.routes import router as chat_router


Base.metadata.create_all(bind=engine)

app = FastAPI(
    title=settings.PROJECT_NAME,
    description="AI-powered document analysis platform",
    version=settings.API_VERSION
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",
        "http://127.0.0.1:5173",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth_router)
app.include_router(documents_router)
app.include_router(chat_router)


@app.get("/")
def root():
    return {"message": "Welcome to DocuMind AI"}


@app.get("/health")
def health_check():
    return {"status": "ok"}


