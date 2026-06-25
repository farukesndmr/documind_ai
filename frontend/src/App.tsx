import { FormEvent, useEffect, useMemo, useState } from "react";
import "./App.css";
import {
  askQuestion,
  clearToken,
  getDocuments,
  getToken,
  loginUser,
  registerUser,
  setToken,
  uploadDocument,
  type ChatAnswer,
  type DocumentItem,
} from "./api";

function App() {
  const [isAuthenticated, setIsAuthenticated] = useState(Boolean(getToken()));

  const [authMode, setAuthMode] = useState<"login" | "register">("login");
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");

  const [authLoading, setAuthLoading] = useState(false);
  const [authError, setAuthError] = useState("");

  const [documents, setDocuments] = useState<DocumentItem[]>([]);
  const [selectedDocumentId, setSelectedDocumentId] = useState<number | null>(
    null
  );

  const [documentsLoading, setDocumentsLoading] = useState(false);
  const [documentsError, setDocumentsError] = useState("");

  const [uploadLoading, setUploadLoading] = useState(false);
  const [uploadMessage, setUploadMessage] = useState("");

  const [question, setQuestion] = useState("");
  const [chatAnswer, setChatAnswer] = useState<ChatAnswer | null>(null);
  const [chatLoading, setChatLoading] = useState(false);
  const [chatError, setChatError] = useState("");

  const selectedDocument = useMemo(() => {
    return documents.find((document) => document.id === selectedDocumentId);
  }, [documents, selectedDocumentId]);

  useEffect(() => {
    if (isAuthenticated) {
      loadDocuments();
    }
  }, [isAuthenticated]);

  async function loadDocuments() {
    try {
      setDocumentsLoading(true);
      setDocumentsError("");

      const data = await getDocuments();
      setDocuments(data);

      if (data.length > 0 && selectedDocumentId === null) {
        setSelectedDocumentId(data[0].id);
      }

      if (data.length === 0) {
        setSelectedDocumentId(null);
      }
    } catch (error) {
      setDocumentsError(
        error instanceof Error
          ? error.message
          : "Documents could not be loaded."
      );
    } finally {
      setDocumentsLoading(false);
    }
  }

  async function handleAuthSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();

    if (!email.trim() || !password.trim()) {
      setAuthError("Email and password are required.");
      return;
    }

    try {
      setAuthLoading(true);
      setAuthError("");

      if (authMode === "register") {
        await registerUser(email.trim(), password);
      }

      const token = await loginUser(email.trim(), password);
      setToken(token);

      setIsAuthenticated(true);
      setPassword("");
    } catch (error) {
      setAuthError(
        error instanceof Error ? error.message : "Authentication failed."
      );
    } finally {
      setAuthLoading(false);
    }
  }

  function handleLogout() {
    clearToken();
    setIsAuthenticated(false);
    setDocuments([]);
    setSelectedDocumentId(null);
    setChatAnswer(null);
    setQuestion("");
    setUploadMessage("");
  }

  async function handleFileUpload(event: React.ChangeEvent<HTMLInputElement>) {
    const file = event.target.files?.[0];

    if (!file) {
      return;
    }

    try {
      setUploadLoading(true);
      setUploadMessage("");
      setDocumentsError("");

      await uploadDocument(file);
      setUploadMessage(`${file.name} uploaded successfully.`);

      await loadDocuments();

      event.target.value = "";
    } catch (error) {
      setUploadMessage(
        error instanceof Error ? error.message : "File upload failed."
      );
    } finally {
      setUploadLoading(false);
    }
  }

  async function handleAskQuestion(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();

    if (!selectedDocumentId) {
      setChatError("Please select a document first.");
      return;
    }

    if (!question.trim()) {
      setChatError("Please write a question.");
      return;
    }

    try {
      setChatLoading(true);
      setChatError("");
      setChatAnswer(null);

      const answer = await askQuestion(selectedDocumentId, question.trim());
      setChatAnswer(answer);
    } catch (error) {
      setChatError(
        error instanceof Error ? error.message : "Question could not be answered."
      );
    } finally {
      setChatLoading(false);
    }
  }

  if (!isAuthenticated) {
    return (
      <main className="page">
        <section className="auth-card">
          <div className="brand">
            <div className="brand-icon">D</div>
            <div>
              <h1>DocuMind AI</h1>
              <p>Upload documents and chat with them using AI.</p>
            </div>
          </div>

          <div className="auth-tabs">
            <button
              className={authMode === "login" ? "tab active" : "tab"}
              onClick={() => {
                setAuthMode("login");
                setAuthError("");
              }}
              type="button"
            >
              Login
            </button>

            <button
              className={authMode === "register" ? "tab active" : "tab"}
              onClick={() => {
                setAuthMode("register");
                setAuthError("");
              }}
              type="button"
            >
              Register
            </button>
          </div>

          <form className="auth-form" onSubmit={handleAuthSubmit}>
            <label>
              Email
              <input
                type="email"
                placeholder="you@example.com"
                value={email}
                onChange={(event) => setEmail(event.target.value)}
              />
            </label>

            <label>
              Password
              <input
                type="password"
                placeholder="Your password"
                value={password}
                onChange={(event) => setPassword(event.target.value)}
              />
            </label>

            {authError && <p className="error-text">{authError}</p>}

            <button className="primary-button" type="submit" disabled={authLoading}>
              {authLoading
                ? "Please wait..."
                : authMode === "login"
                ? "Login"
                : "Create account"}
            </button>
          </form>
        </section>
      </main>
    );
  }

  return (
    <main className="dashboard">
      <aside className="sidebar">
        <div className="brand small">
          <div className="brand-icon">D</div>
          <div>
            <h1>DocuMind AI</h1>
            <p>Document Chat Dashboard</p>
          </div>
        </div>

        <section className="panel">
          <div className="panel-header">
            <h2>Upload PDF</h2>
          </div>

          <label className="upload-box">
            <input
              type="file"
              accept="application/pdf"
              onChange={handleFileUpload}
              disabled={uploadLoading}
            />
            <span>{uploadLoading ? "Uploading..." : "Choose PDF file"}</span>
          </label>

          {uploadMessage && <p className="info-text">{uploadMessage}</p>}
        </section>

        <section className="panel documents-panel">
          <div className="panel-header">
            <h2>Your Documents</h2>
            <button className="ghost-button" onClick={loadDocuments} type="button">
              Refresh
            </button>
          </div>

          {documentsLoading && <p className="muted-text">Loading documents...</p>}

          {documentsError && <p className="error-text">{documentsError}</p>}

          {!documentsLoading && documents.length === 0 && (
            <p className="muted-text">No documents uploaded yet.</p>
          )}

          <div className="documents-list">
            {documents.map((document) => (
              <button
                key={document.id}
                type="button"
                className={
                  selectedDocumentId === document.id
                    ? "document-item active"
                    : "document-item"
                }
                onClick={() => {
                  setSelectedDocumentId(document.id);
                  setChatAnswer(null);
                  setChatError("");
                }}
              >
                <span>{document.filename}</span>
                {document.created_at && (
                  <small>{new Date(document.created_at).toLocaleDateString()}</small>
                )}
              </button>
            ))}
          </div>
        </section>

        <button className="logout-button" onClick={handleLogout} type="button">
          Logout
        </button>
      </aside>

      <section className="chat-area">
        <div className="chat-card">
          <div className="chat-header">
            <div>
              <p className="eyebrow">Selected document</p>
              <h2>{selectedDocument ? selectedDocument.filename : "No document selected"}</h2>
            </div>
          </div>

          <form className="question-form" onSubmit={handleAskQuestion}>
            <textarea
              placeholder="Ask a question about the selected document..."
              value={question}
              onChange={(event) => setQuestion(event.target.value)}
              rows={4}
            />

            {chatError && <p className="error-text">{chatError}</p>}

            <button
              className="primary-button"
              type="submit"
              disabled={chatLoading || !selectedDocumentId}
            >
              {chatLoading ? "Thinking..." : "Ask DocuMind"}
            </button>
          </form>

          <div className="answer-box">
            {!chatAnswer && !chatLoading && (
              <p className="muted-text">
                Select a document and ask a question to start chatting.
              </p>
            )}

            {chatLoading && <p className="muted-text">Generating answer...</p>}

            {chatAnswer && (
              <>
                <h3>Answer</h3>
                <p>{chatAnswer.answer}</p>

                {chatAnswer.sources && chatAnswer.sources.length > 0 && (
                  <details>
                    <summary>Sources / chunks</summary>
                    <pre>{JSON.stringify(chatAnswer.sources, null, 2)}</pre>
                  </details>
                )}
              </>
            )}
          </div>
        </div>
      </section>
    </main>
  );
}

export default App;