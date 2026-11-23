import logging

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.core.config import settings
from app.database.connection import Base, engine
from app.database.schema_upgrades import run_schema_upgrades
from app.admin.routes import router as admin_router

from app.users import models as user_models  # noqa: F401 (tabloları kaydeder)
from app.documents import models as document_models  # noqa: F401
from app.usage import models as usage_models  # noqa: F401

from app.auth.routes import router as auth_router
from app.documents.routes import router as documents_router
from app.chat.routes import router as chat_router


logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s %(name)s: %(message)s",
)

Base.metadata.create_all(bind=engine)
run_schema_upgrades(engine)

app = FastAPI(
    title=settings.PROJECT_NAME,
    description="AI-powered document analysis platform",
    version=settings.API_VERSION
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth_router)
app.include_router(documents_router)
app.include_router(chat_router)
app.include_router(admin_router)

@app.get("/")
def root():
    return {"message": "Welcome to DocuMind AI"}


@app.get("/health")
def health_check():
    return {"status": "ok"}


