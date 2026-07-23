import { useCallback, useEffect, useMemo, useState } from "react";
import type {
  ChangeEvent,
  FormEvent,
  KeyboardEvent,
} from "react";

import ReactMarkdown from "react-markdown";
import remarkGfm from "remark-gfm";

import "./App.css";
import "./delete.css";

import {
  GoogleLogin,
  GoogleOAuthProvider,
} from "@react-oauth/google";

import {
  askQuestion,
  deleteDocument,
  getDocuments,
  getMe,
  getToken,
  loginWithGoogle,
  setToken,
  uploadDocument,
  type ChatAnswer,
  type DocumentItem,
  type UserProfile,
} from "./api";


type IconName =
  | "logo"
  | "upload"
  | "document"
  | "refresh"
  | "logout"
  | "sparkles"
  | "send"
  | "summary"
  | "flashcards"
  | "quiz"
  | "concepts"
  | "shield"
  | "arrow"
  | "check"
  | "trash";

type QuickAction = {
  title: string;
  description: string;
  prompt: string;
  icon: IconName;
};

const QUICK_ACTIONS: QuickAction[] = [
  {
    title: "Exam summary",
    description: "Create a structured study guide",
    prompt:
      "Bu belgenin sınav odaklı, detaylı ve başlıklandırılmış bir özetini çıkar.",
    icon: "summary",
  },
  {
    title: "Flashcards",
    description: "Turn key ideas into study cards",
    prompt:
      "Bu belgedeki önemli kavramlardan soru-cevap formatında flashcardlar oluştur.",
    icon: "flashcards",
  },
  {
    title: "Generate quiz",
    description: "Test your document knowledge",
    prompt:
      "Bu belgeye dayanarak cevapları en sonda bulunan 10 soruluk bir quiz hazırla.",
    icon: "quiz",
  },
  {
    title: "Key concepts",
    description: "Extract the essential ideas",
    prompt:
      "Bu belgedeki en önemli kavramları kısa ve anlaşılır açıklamalarıyla listele.",
    icon: "concepts",
  },
];

function Icon({
  name,
  size = 18,
}: {
  name: IconName;
  size?: number;
}) {
  const iconProps = {
    width: size,
    height: size,
    viewBox: "0 0 24 24",
    fill: "none",
    stroke: "currentColor",
    strokeWidth: 1.8,
    strokeLinecap: "round" as const,
    strokeLinejoin: "round" as const,
    "aria-hidden": true,
  };

  switch (name) {
    case "logo":
      return (
        <svg {...iconProps}>
          <path d="M7 3.5h7.5L19 8v8.5A4.5 4.5 0 0 1 14.5 21H7a2 2 0 0 1-2-2V5.5a2 2 0 0 1 2-2Z" />
          <path d="M14 3.5V9h5" />
          <path d="m8.5 15 2 2 5-5" />
        </svg>
      );

    case "upload":
      return (
        <svg {...iconProps}>
          <path d="M12 16V4" />
          <path d="m7 9 5-5 5 5" />
          <path d="M5 20h14" />
        </svg>
      );

    case "document":
      return (
        <svg {...iconProps}>
          <path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8Z" />
          <path d="M14 2v6h6" />
          <path d="M8 13h8" />
          <path d="M8 17h5" />
        </svg>
      );

    case "refresh":
      return (
        <svg {...iconProps}>
          <path d="M20 7v5h-5" />
          <path d="M4 17v-5h5" />
          <path d="M18.4 9A7 7 0 0 0 6.7 6.4L4 9" />
          <path d="M5.6 15a7 7 0 0 0 11.7 2.6L20 15" />
        </svg>
      );

    case "logout":
      return (
        <svg {...iconProps}>
          <path d="M10 17l5-5-5-5" />
          <path d="M15 12H3" />
          <path d="M14 3h5a2 2 0 0 1 2 2v14a2 2 0 0 1-2 2h-5" />
        </svg>
      );

    case "sparkles":
      return (
        <svg {...iconProps}>
          <path d="m12 3-1.2 3.2L7.5 7.5l3.3 1.3L12 12l1.2-3.2 3.3-1.3-3.3-1.3Z" />
          <path d="m18 13-.8 2.2L15 16l2.2.8L18 19l.8-2.2L21 16l-2.2-.8Z" />
          <path d="m5 14-.6 1.6-1.4.6 1.4.6L5 18.4l.6-1.6 1.4-.6-1.4-.6Z" />
        </svg>
      );

    case "send":
      return (
        <svg {...iconProps}>
          <path d="m22 2-7 20-4-9-9-4Z" />
          <path d="M22 2 11 13" />
        </svg>
      );

    case "summary":
      return (
        <svg {...iconProps}>
          <path d="M5 5h14" />
          <path d="M5 10h14" />
          <path d="M5 15h9" />
          <path d="M5 20h6" />
        </svg>
      );

    case "flashcards":
      return (
        <svg {...iconProps}>
          <rect x="3" y="5" width="14" height="16" rx="2" />
          <path d="M7 9h6" />
          <path d="M7 13h4" />
          <path d="M7 3h12a2 2 0 0 1 2 2v14" />
        </svg>
      );

    case "quiz":
      return (
        <svg {...iconProps}>
          <circle cx="12" cy="12" r="9" />
          <path d="M9.7 9a2.5 2.5 0 1 1 4.1 1.9C12.9 11.6 12 12 12 13.2" />
          <path d="M12 17h.01" />
        </svg>
      );

    case "concepts":
      return (
        <svg {...iconProps}>
          <path d="M9 18h6" />
          <path d="M10 22h4" />
          <path d="M8.5 14.5A6 6 0 1 1 15.5 14.5C14.6 15.3 14 16.2 14 17h-4c0-.8-.6-1.7-1.5-2.5Z" />
        </svg>
      );

    case "shield":
      return (
        <svg {...iconProps}>
          <path d="M12 22s8-3.5 8-10V5l-8-3-8 3v7c0 6.5 8 10 8 10Z" />
          <path d="m9 12 2 2 4-4" />
        </svg>
      );

    case "arrow":
      return (
        <svg {...iconProps}>
          <path d="M5 12h14" />
          <path d="m14 7 5 5-5 5" />
        </svg>
      );

    case "check":
      return (
        <svg {...iconProps}>
          <path d="m5 12 4 4L19 6" />
        </svg>
      );

    case "trash":
      return (
        <svg {...iconProps}>
          <path d="M3 6h18" />
          <path d="M8 6V4h8v2" />
          <path d="M19 6l-1 15H6L5 6" />
          <path d="M10 11v6" />
          <path d="M14 11v6" />
        </svg>
      );

    default:
      return null;
  }
}

function formatDate(value?: string) {
  if (!value) {
    return "PDF document";
  }

  const date = new Date(value);

  if (Number.isNaN(date.getTime())) {
    return "PDF document";
  }

  return new Intl.DateTimeFormat(undefined, {
    day: "numeric",
    month: "short",
    year: "numeric",
  }).format(date);
}
const GOOGLE_CLIENT_ID = import.meta.env.VITE_GOOGLE_CLIENT_ID as string;
function App() {
  const [isAuthenticated, setIsAuthenticated] = useState(
    Boolean(getToken()),
  );
  const [authError, setAuthError] = useState("");

  const [currentUser, setCurrentUser] =
    useState<UserProfile | null>(null);
  const [profileLoading, setProfileLoading] = useState(false);
  const [profileError, setProfileError] = useState("");

  const [documents, setDocuments] = useState<DocumentItem[]>([]);
  const [selectedDocumentId, setSelectedDocumentId] = useState<
    number | null
  >(null);
  const [documentsLoading, setDocumentsLoading] = useState(false);
  const [documentsError, setDocumentsError] = useState("");

  const [uploadLoading, setUploadLoading] = useState(false);
  const [uploadMessage, setUploadMessage] = useState("");
  const [uploadError, setUploadError] = useState("");

  const [deletingDocumentId, setDeletingDocumentId] = useState<
    number | null
  >(null);

  const [question, setQuestion] = useState("");
  const [chatAnswer, setChatAnswer] =
    useState<ChatAnswer | null>(null);
  const [chatLoading, setChatLoading] = useState(false);
  const [chatError, setChatError] = useState("");

  const selectedDocument = useMemo(() => {
    return documents.find(
      (document) => document.id === selectedDocumentId,
    );
  }, [documents, selectedDocumentId]);

  const isAdmin = currentUser?.role === "admin";

  const canUseWorkspace = Boolean(
    currentUser &&
      (isAdmin ||
        currentUser.email_verified ||
        currentUser.can_use_app ||
        currentUser.is_active),
  );

  const pdfUsageText = currentUser
    ? `${currentUser.pdf_upload_count}/1 PDF used`
    : "PDF usage";

  const questionUsageText = currentUser
    ? `${currentUser.question_count}/2 questions used`
    : "Question usage";

  const loadCurrentUser = useCallback(async () => {
    try {
      setProfileLoading(true);
      setProfileError("");

      const data = await getMe();
      setCurrentUser(data);

      return data;
    } catch (error) {
      const message =
        error instanceof Error
          ? error.message
          : "User profile could not be loaded.";

      setProfileError(message);
      throw error;
    } finally {
      setProfileLoading(false);
    }
  }, []);

  const loadDocuments = useCallback(async () => {
    try {
      setDocumentsLoading(true);
      setDocumentsError("");

      const data = await getDocuments();
      setDocuments(data);

      setSelectedDocumentId((currentId) => {
        if (data.length === 0) {
          return null;
        }

        const currentDocumentExists = data.some(
          (document) => document.id === currentId,
        );

        return currentDocumentExists ? currentId : data[0].id;
      });
    } catch (error) {
      setDocumentsError(
        error instanceof Error
          ? error.message
          : "Documents could not be loaded.",
      );
    } finally {
      setDocumentsLoading(false);
    }
  }, []);

  useEffect(() => {
    if (!isAuthenticated) {
      return;
    }

    void (async () => {
      try {
        const profile = await loadCurrentUser();
        const profileCanUseWorkspace =
          profile.role === "admin" ||
          profile.can_use_app ||
          profile.is_active;

        if (profileCanUseWorkspace) {
          await loadDocuments();
        } else {
          setDocuments([]);
          setSelectedDocumentId(null);
        }

      } catch {
        // Error message is already stored in state.
      }
    })();
  }, [
    isAuthenticated,
    loadCurrentUser,
    loadDocuments,
  ]);

  async function handleGoogleLoginSuccess(credential?: string) {
    if (!credential) {
      setAuthError("Google login did not return a credential.");
      return;
    }

    try {
      setAuthError("");

      const token = await loginWithGoogle(credential);

      setToken(token);
      setIsAuthenticated(true);
    } catch (error) {
      setAuthError(
        error instanceof Error ? error.message : "Google login failed.",
      );
    }
  }


  function handleLogout() {
    localStorage.removeItem("access_token");
    localStorage.removeItem("token");

    setIsAuthenticated(false);
    setCurrentUser(null);
    setProfileError("");
    setDocuments([]);
    setSelectedDocumentId(null);
    setChatAnswer(null);
    setQuestion("");
    setChatError("");
    setDocumentsError("");
    setUploadMessage("");
    setUploadError("");
    setDeletingDocumentId(null);
  }

  async function handleFileUpload(
    event: ChangeEvent<HTMLInputElement>,
  ) {
    const file = event.target.files?.[0];

    if (!file) {
      return;
    }

    if (file.type !== "application/pdf") {
      setUploadError("Only PDF files are supported.");
      event.target.value = "";
      return;
    }

    try {
      setUploadLoading(true);
      setUploadMessage("");
      setUploadError("");

      await uploadDocument(file);
      setUploadMessage(`${file.name} uploaded successfully.`);
      await loadDocuments();
      await loadCurrentUser();
      event.target.value = "";
    } catch (error) {
      setUploadError(
        error instanceof Error
          ? error.message
          : "Document upload failed.",
      );
    } finally {
      setUploadLoading(false);
    }
  }

  async function handleDeleteDocument(document: DocumentItem) {
    if (deletingDocumentId !== null) {
      return;
    }

    const confirmed = window.confirm(
      `"${document.filename}" kalıcı olarak silinsin mi?`,
    );

    if (!confirmed) {
      return;
    }

    try {
      setDeletingDocumentId(document.id);

      await deleteDocument(document.id);

      const remainingDocuments = documents.filter(
        (item) => item.id !== document.id,
      );

      setDocuments(remainingDocuments);

      if (selectedDocumentId === document.id) {
        setSelectedDocumentId(
          remainingDocuments[0]?.id ?? null,
        );
        setChatAnswer(null);
        setQuestion("");
        setChatError("");
      }
    } catch (error) {
      const message =
        error instanceof Error
          ? error.message
          : "Document could not be deleted.";

      window.alert(`Silme hatası: ${message}`);
    } finally {
      setDeletingDocumentId(null);
    }
  }

  async function runQuestion(promptText: string) {
    if (selectedDocumentId === null) {
      setChatError("Please select a document first.");
      return;
    }

    const cleanPrompt = promptText.trim();

    if (!cleanPrompt) {
      setChatError("Please write a question.");
      return;
    }

    try {
      setQuestion(cleanPrompt);
      setChatLoading(true);
      setChatError("");
      setChatAnswer(null);

      const answer = await askQuestion(
        selectedDocumentId,
        cleanPrompt,
      );

      setChatAnswer(answer);
      await loadCurrentUser();
    } catch (error) {
      setChatError(
        error instanceof Error
          ? error.message
          : "Question could not be answered.",
      );
    } finally {
      setChatLoading(false);
    }
  }

  async function handleAskQuestion(
    event: FormEvent<HTMLFormElement>,
  ) {
    event.preventDefault();
    await runQuestion(question);
  }

  function handleQuestionKeyDown(
    event: KeyboardEvent<HTMLTextAreaElement>,
  ) {
    if (
      event.key === "Enter" &&
      (event.ctrlKey || event.metaKey)
    ) {
      event.preventDefault();
      void runQuestion(question);
    }
  }

  if (!isAuthenticated) {
    return (
      <main className="auth-layout">
        <section className="auth-showcase">
          <div className="auth-brand">
            <div className="logo-box">
              <Icon name="logo" size={22} />
            </div>

            <div>
              <strong>DocuMind</strong>
              <span>AI document workspace</span>
            </div>
          </div>

          <div className="showcase-content">
            <div className="showcase-badge">
              <Icon name="sparkles" size={15} />
              Production RAG document assistant
            </div>

            <h1>
              Ask better questions from
              <span> your PDFs.</span>
            </h1>

            <p>
              Upload a PDF, retrieve relevant passages and get
              source-grounded answers with an AI workflow.
            </p>

            <div className="showcase-features">
              <article>
                <div className="feature-icon">
                  <Icon name="document" size={19} />
                </div>

                <div>
                  <strong>Grounded answers</strong>
                  <span>Responses generated from your documents.</span>
                </div>
              </article>

              <article>
                <div className="feature-icon">
                  <Icon name="shield" size={19} />
                </div>

                <div>
                  <strong>Private workspace</strong>
                  <span>Your documents remain inside your account.</span>
                </div>
              </article>
            </div>

            <div className="showcase-preview">
              <div className="preview-header">
                <div>
                  <Icon name="document" size={16} />
                  Lecture_9.pdf
                </div>

                <span>PDF</span>
              </div>

              <div className="preview-question">
                What are the differences between Traditional and
                Agile V&amp;V?
              </div>

              <div className="preview-response">
                <div className="preview-ai-icon">
                  <Icon name="sparkles" size={15} />
                </div>

                <div className="preview-lines">
                  <span />
                  <span />
                  <span />
                </div>
              </div>
            </div>
          </div>

          <footer className="showcase-footer">
            <span>Built as a full-stack AI portfolio project.</span>
            <span>DocuMind AI</span>
          </footer>
        </section>

        <section className="auth-form-side">
          <div className="auth-card">
            <div className="mobile-auth-brand">
              <div className="logo-box">
                <Icon name="logo" size={21} />
              </div>

              <strong>DocuMind</strong>
            </div>

            <div className="auth-card-heading">
              <span>
                Continue with Google
              </span>

              <h2>
                Enter your workspace
              </h2>

              <p>
                Sign in or create an account with your Google account.
              </p>
            </div>
            <div className="google-login-box">
              {GOOGLE_CLIENT_ID ? (
                <GoogleOAuthProvider clientId={GOOGLE_CLIENT_ID}>
                  <GoogleLogin
                    text="continue_with"
                    shape="pill"
                    size="large"
                    width="320"
                    onSuccess={(credentialResponse) => {
                      void handleGoogleLoginSuccess(
                        credentialResponse.credential,
                      );
                    }}
                    onError={() => {
                      setAuthError("Google login failed.");
                    }}
                  />
                </GoogleOAuthProvider>
              ) : (
                <p className="error-message">
                  Google sign-in is not configured.
                </p>
              )}
            </div>
              {authError && (
                <p className="error-message">{authError}</p>
              )}
            <div className="security-note">
              <Icon name="shield" size={15} />
              Google sign-in, protected API routes and demo limits
            </div>
          </div>
        </section>
      </main>
    );
  }

  if (profileLoading && !currentUser) {
    return (
      <main className="auth-layout">
        <section className="auth-form-side">
          <div className="auth-card">
            <div className="auth-card-heading">
              <span>Loading account</span>
              <h2>Preparing your workspace</h2>
              <p>Please wait while we check your account status.</p>
            </div>
          </div>
        </section>
      </main>
    );
  }

  if (isAuthenticated && !currentUser && profileError) {
    return (
      <main className="auth-layout">
        <section className="auth-form-side">
          <div className="auth-card">
            <div className="auth-card-heading">
              <span>Account error</span>
              <h2>We could not load your workspace</h2>
              <p>{profileError}</p>
            </div>

            <button
              className="auth-submit"
              type="button"
              disabled={profileLoading}
              onClick={() => void loadCurrentUser()}
            >
              <span>{profileLoading ? "Checking..." : "Try again"}</span>
              {!profileLoading && <Icon name="refresh" size={17} />}
            </button>

            <button
              type="button"
              className="logout-button"
              onClick={handleLogout}
            >
              <Icon name="logout" size={17} />
              Log out
            </button>
          </div>
        </section>
      </main>
    );
  }

  return (
    <main className="app-shell">
      <aside className="sidebar">
        <div className="sidebar-brand">
          <div className="logo-box">
            <Icon name="logo" size={21} />
          </div>

          <div>
            <strong>DocuMind</strong>
            <span>Document AI</span>
          </div>
        </div>

        <section className="upload-area">
          <span className="section-caption">Add document</span>

          <label className="upload-button">
            <input
              type="file"
              accept="application/pdf"
              disabled={uploadLoading || !canUseWorkspace}
              onChange={handleFileUpload}
            />

            <div className="upload-button-icon">
              <Icon name="upload" size={18} />
            </div>

            <div>
              <strong>
                {uploadLoading
                  ? "Uploading..."
                  : "Upload PDF"}
              </strong>

              <span>
                {uploadLoading
                  ? "Please wait"
                  : "Choose a file"}
              </span>
            </div>
          </label>

          {uploadMessage && (
            <p className="success-message">
              <Icon name="check" size={14} />
              {uploadMessage}
            </p>
          )}

          {uploadError && (
            <p className="error-message">{uploadError}</p>
          )}
        </section>

        {currentUser && !isAdmin && (
          <section className="upload-area">
            <span className="section-caption">Public demo usage</span>

            <div className="private-status">
              <Icon name="document" size={16} />

              <div>
                <strong>{pdfUsageText}</strong>
                <span>Demo limit</span>
              </div>
            </div>

            <div className="private-status">
              <Icon name="send" size={16} />

              <div>
                <strong>{questionUsageText}</strong>
                <span>Demo limit</span>
              </div>
            </div>
          </section>
        )}

        <section className="library">
          <div className="library-header">
            <div>
              <span className="section-caption">Library</span>
              <strong>{documents.length} documents</strong>
            </div>

            <button
              type="button"
              className="icon-button"
              aria-label="Refresh documents"
              title="Refresh documents"
              disabled={documentsLoading}
              onClick={() => void loadDocuments()}
            >
              <Icon name="refresh" size={17} />
            </button>
          </div>

          {documentsError && (
            <p className="error-message">{documentsError}</p>
          )}

          {documentsLoading && (
            <p className="sidebar-message">
              Loading documents...
            </p>
          )}

          {!documentsLoading && documents.length === 0 && (
            <div className="empty-library">
              <Icon name="document" size={24} />
              <strong>No documents yet</strong>
              <span>Upload your first PDF to begin.</span>
            </div>
          )}

          <div className="document-list">
            {documents.map((document) => {
              const isSelected =
                selectedDocumentId === document.id;
              const isDeleting =
                deletingDocumentId === document.id;

              return (
                <div
                  className="document-row"
                  key={document.id}
                >
                  <button
                    type="button"
                    className={
                      isSelected
                        ? "document-item selected"
                        : "document-item"
                    }
                    onClick={() => {
                      setSelectedDocumentId(document.id);
                      setChatAnswer(null);
                      setChatError("");
                      setQuestion("");
                    }}
                  >
                    <div className="document-item-icon">
                      <Icon name="document" size={17} />
                    </div>

                    <div className="document-item-text">
                      <strong>{document.filename}</strong>
                      <span>
                        {formatDate(document.created_at)}
                      </span>
                    </div>

                    <span className="selected-dot" />
                  </button>

                  <button
                    type="button"
                    className="document-delete-button"
                    title="Delete document"
                    aria-label={`Delete ${document.filename}`}
                    disabled={deletingDocumentId !== null}
                    onClick={(event) => {
                      event.preventDefault();
                      event.stopPropagation();
                      void handleDeleteDocument(document);
                    }}
                  >
                    {isDeleting ? (
                      <span className="delete-spinner" />
                    ) : (
                      <Icon name="trash" size={15} />
                    )}
                  </button>
                </div>
              );
            })}
          </div>
        </section>

        <div className="sidebar-bottom">
          <div className="private-status">
            <Icon name="shield" size={16} />

            <div>
              <strong>
                {isAdmin ? "Admin workspace" : "Private workspace"}
              </strong>
              <span>
                {currentUser?.email ?? "Protected account access"}
              </span>
            </div>
          </div>

          <button
            type="button"
            className="logout-button"
            onClick={handleLogout}
          >
            <Icon name="logout" size={17} />
            Log out
          </button>
        </div>
      </aside>

      <section className="main-workspace">
        <header className="topbar">
          <div className="breadcrumb">
            <span>Workspace</span>
            <span>/</span>

            <strong>
              {selectedDocument
                ? selectedDocument.filename
                : "No document selected"}
            </strong>
          </div>

          <div className="online-badge">
            <span />
            {isAdmin ? "Admin ready" : "Ready"}
          </div>
        </header>

        <div className="workspace-content">
          <section className="document-heading">
            <div>
              <div className="heading-label">
                <Icon name="sparkles" size={15} />
                Active document
              </div>

              <h1>
                {selectedDocument
                  ? selectedDocument.filename
                  : "Choose a document"}
              </h1>

              <p>
                {selectedDocument
                  ? "Ask questions, generate study notes and review answers grounded in the selected PDF."
                  : "Upload or select a PDF from your document library."}
              </p>
            </div>

            {selectedDocument && (
              <div className="pdf-badge">
                <Icon name="document" size={16} />
                PDF
              </div>
            )}
          </section>

          <section className="quick-actions">
            <div className="content-title">
              <span className="section-caption">
                Suggested actions
              </span>

              <h2>Start with a document task</h2>
            </div>

            <div className="quick-action-grid">
              {QUICK_ACTIONS.map((action) => (
                <button
                  type="button"
                  key={action.title}
                  className="quick-action"
                  disabled={
                    selectedDocumentId === null ||
                    chatLoading ||
                    !canUseWorkspace
                  }
                  onClick={() =>
                    void runQuestion(action.prompt)
                  }
                >
                  <div className="quick-action-icon">
                    <Icon name={action.icon} size={18} />
                  </div>

                  <div>
                    <strong>{action.title}</strong>
                    <span>{action.description}</span>
                  </div>

                  <Icon name="arrow" size={16} />
                </button>
              ))}
            </div>
          </section>

          <form
            className="question-box"
            onSubmit={handleAskQuestion}
          >
            <div className="question-icon">
              <Icon name="sparkles" size={19} />
            </div>

            <div className="question-content">
              <textarea
                rows={3}
                value={question}
                placeholder="Ask a question about the selected PDF..."
                onKeyDown={handleQuestionKeyDown}
                onChange={(event) =>
                  setQuestion(event.target.value)
                }
              />

              <div className="question-footer">
                <span>
                  Press <kbd>Ctrl</kbd> + <kbd>Enter</kbd> to
                  send
                </span>

                <button
                  type="submit"
                  className="ask-button"
                  disabled={
                    chatLoading ||
                    selectedDocumentId === null ||
                    !canUseWorkspace ||
                    !question.trim()
                  }
                >
                  <span>
                    {chatLoading
                      ? "Thinking..."
                      : "Ask"}
                  </span>

                  <Icon name="send" size={16} />
                </button>
              </div>
            </div>
          </form>

          {chatError && (
            <p className="workspace-error">{chatError}</p>
          )}

          <section className="answer-container">
            {!chatAnswer && !chatLoading && (
              <div className="answer-placeholder">
                <div className="placeholder-visual">
                  <div className="placeholder-ring outer" />
                  <div className="placeholder-ring inner" />

                  <div className="placeholder-core">
                    <Icon name="sparkles" size={24} />
                  </div>
                </div>

                <h2>Your grounded answer will appear here</h2>

                <p>
                  Ask a question or select one of the suggested
                  actions.
                </p>
              </div>
            )}

            {chatLoading && (
              <div className="answer-loading">
                <div className="loading-heading">
                  <div className="loading-icon">
                    <Icon name="sparkles" size={18} />
                  </div>

                  <div>
                    <strong>Searching relevant passages</strong>
                    <span>
                      Preparing a source-grounded response...
                    </span>
                  </div>
                </div>

                <div className="loading-lines">
                  <span className="long" />
                  <span className="medium" />
                  <span className="long" />
                  <span className="short" />
                </div>
              </div>
            )}

            {chatAnswer && (
              <div className="answer-content">
                <header className="answer-header">
                  <div className="answer-header-icon">
                    <Icon name="sparkles" size={16} />
                  </div>

                  <div>
                    <span>AI response</span>
                    <strong>Grounded in your PDF</strong>
                  </div>
                </header>

                <article className="markdown-answer">
                  <ReactMarkdown
                    remarkPlugins={[remarkGfm]}
                  >
                    {chatAnswer.answer}
                  </ReactMarkdown>
                </article>

                {chatAnswer.sources &&
                  chatAnswer.sources.length > 0 && (
                    <details className="source-details">
                      <summary>
                        <span>Retrieved source chunks</span>

                        <span className="source-count">
                          {chatAnswer.sources.length}
                        </span>
                      </summary>

                      <pre>
                        {JSON.stringify(
                          chatAnswer.sources,
                          null,
                          2,
                        )}
                      </pre>
                    </details>
                  )}
              </div>
            )}
          </section>
        </div>
      </section>
    </main>
  );
}

export default App;