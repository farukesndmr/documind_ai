# DocuMind AI

DocuMind AI is a full-stack AI document assistant that allows users to upload PDF files and ask questions about their contents using a Retrieval-Augmented Generation (RAG) pipeline.

Live Demo: https://documind-ai-g0wj.onrender.com/

Backend API: https://documind-api-5w97.onrender.com/

---

## Features

- Google sign-in authentication
- JWT-based backend authentication
- PDF upload and document management
- PDF text extraction
- Text chunking for retrieval
- OpenAI embeddings
- PostgreSQL + pgvector vector search
- RAG-based question answering
- Source chunks shown with answers
- Demo usage limits
  - 1 PDF upload per normal user
  - 2 questions per normal user
  - 4 MB PDF upload limit
- Admin users are exempt from demo limits
- Production deployment with Render
- Supabase PostgreSQL database

---

## Tech Stack

### Frontend

- React
- TypeScript
- Vite
- Google OAuth
- React Markdown

### Backend

- Python
- FastAPI
- SQLAlchemy
- PostgreSQL
- pgvector
- OpenAI API
- JWT authentication

### Deployment

- Frontend: Render Static Site
- Backend: Render Web Service
- Database: Supabase PostgreSQL

---

## How It Works

1. The user signs in with Google.
2. The frontend sends the Google credential to the FastAPI backend.
3. The backend verifies the Google token.
4. The backend creates or logs in the user.
5. The user uploads a PDF document.
6. The backend extracts text from the PDF.
7. The extracted text is split into chunks.
8. OpenAI embeddings are generated for each chunk.
9. Chunks and vectors are stored in PostgreSQL using pgvector.
10. When the user asks a question, the backend performs vector search.
11. The most relevant chunks are sent to the language model.
12. The answer is returned with source chunks.

---

## Demo Limitations

This public demo has usage limits to control API costs:

- Normal users can upload 1 PDF.
- Normal users can ask 2 questions.
- Maximum PDF size is 4 MB.
- Admin users are exempt from these limits.

---

## Security Notes

- API keys are stored only in environment variables.
- Secret files such as `.env` are ignored by Git.
- Google tokens are verified on the backend.
- JWT tokens are used for protected API routes.
- Database access is handled through backend services, not directly from the frontend.

---

## Project Status

The project is deployed and working in production.

Current completed milestones:

- Full-stack app setup
- User authentication
- Google login
- PDF upload
- Text extraction
- Chunking
- Embeddings
- Vector search
- RAG question answering
- Production deployment
- Demo limits

---

## Future Improvements

- Improve response speed
- Add background processing for PDF embeddings
- Add better document summaries
- Improve UI design
- Add user dashboard analytics
- Add document classification
- Add evaluation metrics for retrieval quality
- Add ONNX or model optimization experiments