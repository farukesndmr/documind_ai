from fastapi import FastAPI

app = FastAPI(
    title="DocuMind AI API",
    description="AI-powered document analysis platform",
    version="0.1.0"
)

@app.get("/")
def root():
    return {"message": "DocuMind AI backend is running"}

@app.get("/health")
def health_check():
    return {"status": "ok"}