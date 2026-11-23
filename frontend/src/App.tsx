import { useCallback, useEffect, useMemo, useRef, useState } from "react";
import type {
  ChangeEvent,
  FormEvent,
  KeyboardEvent,
} from "react";


import "./App.css";
import "./delete.css";

import { ChatThread } from "./components/ChatThread";
import { Icon, type IconName } from "./components/Icon";
import { LoginPage } from "./components/LoginPage";
import { ServerStatus } from "./components/ServerStatus";
import { LanguageSelect } from "./components/LanguageSelect";
import { loadAnswerLanguage, saveAnswerLanguage } from "./answerLanguage";

import {
  askQuestion,
  askQuestionStream,
  clearChatHistory,
  getChatHistory,
  deleteDocument,
  getDocuments,
  isStreamingUnavailable,
  isUnauthorized,
  getMe,
  getToken,
  loginWithGoogle,
  setToken,
  uploadDocument,
  type AnswerLanguage,
  type ChatMessage,
  type DocumentItem,
  type UserProfile,
} from "./api";


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
      "Create a detailed, exam-focused summary of this document with clear headings.",
    icon: "summary",
  },
  {
    title: "Flashcards",
    description: "Turn key ideas into study cards",
    prompt:
      "Create question-and-answer flashcards from the key concepts in this document.",
    icon: "flashcards",
  },
  {
    title: "Generate quiz",
    description: "Test your document knowledge",
    prompt:
      "Create a 10-question quiz based on this document, with the answer key at the end.",
    icon: "quiz",
  },
  {
    title: "Key concepts",
    description: "Extract the essential ideas",
    prompt:
      "List the key concepts in this document with short, clear explanations.",
    icon: "concepts",
  },
];

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
  const [messages, setMessages] = useState<ChatMessage[]>([]);
  // Hangi belgenin geçmişi "messages" içinde yüklü (belge değişince yeniden yüklenir).
  const [historyDocumentId, setHistoryDocumentId] = useState<number | null>(null);
  const [clearingHistory, setClearingHistory] = useState(false);
  const [answerLanguage, setAnswerLanguage] =
    useState<AnswerLanguage>(loadAnswerLanguage);
  const threadEndRef = useRef<HTMLDivElement | null>(null);
  const [chatLoading, setChatLoading] = useState(false);
  const [chatError, setChatError] = useState("");

  const selectedDocument = useMemo(() => {
    return documents.find(
      (document) => document.id === selectedDocumentId,
    );
  }, [documents, selectedDocumentId]);

  const isAdmin = currentUser?.role === "admin";

  const historyLoading =
    selectedDocumentId !== null && historyDocumentId !== selectedDocumentId;
  const visibleMessages = historyLoading ? [] : messages;
  const hasConversation = visibleMessages.length > 0;
  const currentUserId = currentUser?.id;

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

const clearSession = useCallback(() => {
  localStorage.removeItem("access_token");
  localStorage.removeItem("token");

  setIsAuthenticated(false);
  setCurrentUser(null);
  setDocuments([]);
  setSelectedDocumentId(null);
  setMessages([]);
  setHistoryDocumentId(null);
  setQuestion("");
  setChatError("");
  setDocumentsError("");
  setUploadMessage("");
  setUploadError("");
  setProfileError("");
  setDeletingDocumentId(null);
}, []);

  const handleSessionError = useCallback(
    (error: unknown): boolean => {
      if (!isUnauthorized(error)) {
        return false;
      }
      clearSession();
      setAuthError("Your session has expired. Please sign in again.");
      return true;
    },
    [clearSession],
  );

  const scrollThreadToEnd = useCallback(
    (behavior: ScrollBehavior = "auto") => {
      window.requestAnimationFrame(() => {
        threadEndRef.current?.scrollIntoView({ behavior, block: "end" });
      });
    },
    [],
  );

const loadCurrentUser = useCallback(async () => {
  try {
    setProfileLoading(true);
    setProfileError("");

    const data = await getMe();
    setCurrentUser(data);

    return data;
  } catch (error) {
    clearSession();
    if (isUnauthorized(error)) {
      setAuthError("Your session has expired. Please sign in again.");
    }
    throw error;
  } finally {
    setProfileLoading(false);
  }
}, [clearSession]);

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
      if (handleSessionError(error)) {
        return;
      }
      setDocumentsError(
        error instanceof Error
          ? error.message
          : "Documents could not be loaded.",
      );
    } finally {
      setDocumentsLoading(false);
    }
  }, [handleSessionError]);

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

  // Seçili belgenin sohbet geçmişini yükle.
  useEffect(() => {
    if (selectedDocumentId === null || currentUserId === undefined) {
      return;
    }

    let cancelled = false;
    const documentId = selectedDocumentId;

    getChatHistory(documentId)
      .then((history) => {
        if (cancelled) {
          return;
        }
        setMessages(history);
        setHistoryDocumentId(documentId);
        scrollThreadToEnd();
      })
      .catch((error: unknown) => {
        if (cancelled || handleSessionError(error)) {
          return;
        }
        setMessages([]);
        setHistoryDocumentId(documentId);
        // Eski backend'de geçmiş endpoint'i yoksa sessizce boş sohbetle devam et.
        if (!isStreamingUnavailable(error)) {
          setChatError("Conversation history could not be loaded.");
        }
      });

    return () => {
      cancelled = true;
    };
  }, [selectedDocumentId, currentUserId, handleSessionError, scrollThreadToEnd]);

  // Cevap akarken, kullanıcı en alttaysa sohbeti aşağı kaydır.
  useEffect(() => {
    const lastMessage = messages[messages.length - 1];

    if (lastMessage?.status !== "streaming") {
      return;
    }

    const distanceFromBottom =
      document.documentElement.scrollHeight -
      (window.scrollY + window.innerHeight);

    if (distanceFromBottom < 220) {
      threadEndRef.current?.scrollIntoView({ block: "end" });
    }
  }, [messages]);

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
    clearSession();
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
      if (handleSessionError(error)) {
        return;
      }
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
        setMessages([]);
        setQuestion("");
        setChatError("");
      }
    } catch (error) {
      if (handleSessionError(error)) {
        return;
      }
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

    const documentId = selectedDocumentId;
    const stamp = Date.now();
    const userMessageId = `local-user-${stamp}`;
    const assistantMessageId = `local-assistant-${stamp}`;

    const updateAssistant = (
      update: (message: ChatMessage) => ChatMessage,
    ) => {
      setMessages((current) =>
        current.map((message) =>
          message.id === assistantMessageId ? update(message) : message,
        ),
      );
    };

    setChatLoading(true);
    setChatError("");
    setQuestion("");
    setMessages((current) => [
      ...current,
      { id: userMessageId, role: "user", content: cleanPrompt, sources: [] },
      {
        id: assistantMessageId,
        role: "assistant",
        content: "",
        sources: [],
        status: "streaming",
      },
    ]);
    scrollThreadToEnd("smooth");

    try {
      try {
        await askQuestionStream(
          documentId,
          cleanPrompt,
          {
            onSources: (sources) => {
              updateAssistant((message) => ({ ...message, sources }));
            },
            onDelta: (text) => {
              updateAssistant((message) => ({
                ...message,
                content: message.content + text,
              }));
            },
          },
          answerLanguage,
        );
      } catch (streamError) {
        if (!isStreamingUnavailable(streamError)) {
          throw streamError;
        }
        // Backend henüz streaming desteklemiyorsa normal isteğe dön.
        const answer = await askQuestion(documentId, cleanPrompt, answerLanguage);
        updateAssistant((message) => ({
          ...message,
          content: answer.answer,
          sources: answer.sources,
        }));
      }

      updateAssistant((message) => ({ ...message, status: undefined }));
      await loadCurrentUser();
    } catch (error) {
      if (handleSessionError(error)) {
        return;
      }

      setMessages((current) => {
        const assistant = current.find(
          (message) => message.id === assistantMessageId,
        );

        if (assistant && assistant.content) {
          // Metnin bir kısmı geldiyse göster ama yarım kaldığını belirt.
          return current.map((message) =>
            message.id === assistantMessageId
              ? { ...message, status: "interrupted" }
              : message,
          );
        }

        // Hiç cevap gelmediyse soruyu geri al ki kullanıcı tekrar deneyebilsin.
        return current.filter(
          (message) =>
            message.id !== assistantMessageId && message.id !== userMessageId,
        );
      });
      setQuestion((current) => current || cleanPrompt);
      setChatError(
        error instanceof Error
          ? error.message
          : "Question could not be answered.",
      );
    } finally {
      setChatLoading(false);
    }
  }

  async function handleClearHistory() {
    if (selectedDocumentId === null || clearingHistory) {
      return;
    }

    const confirmed = window.confirm(
      "Clear this conversation? Your document will not be deleted.",
    );

    if (!confirmed) {
      return;
    }

    try {
      setClearingHistory(true);
      await clearChatHistory(selectedDocumentId);
      setMessages([]);
      setChatError("");
    } catch (error) {
      if (handleSessionError(error)) {
        return;
      }
      setChatError(
        error instanceof Error
          ? error.message
          : "Conversation could not be cleared.",
      );
    } finally {
      setClearingHistory(false);
    }
  }

  function handleLanguageChange(value: AnswerLanguage) {
    setAnswerLanguage(value);
    saveAnswerLanguage(value);
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
      <LoginPage
        authError={authError}
        onCredential={handleGoogleLoginSuccess}
        onGoogleError={() => setAuthError("Google sign-in failed. Please try again.")}
      />
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
                    disabled={chatLoading && !isSelected}
                    title={
                      chatLoading && !isSelected
                        ? "Wait for the current answer to finish"
                        : undefined
                    }
                    onClick={() => {
                      if (isSelected) {
                        return;
                      }
                      setSelectedDocumentId(document.id);
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
        <ServerStatus />
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

          {historyLoading && (
            <p className="history-loading" role="status">
              Loading conversation…
            </p>
          )}

          {!historyLoading && !hasConversation && (
            <>
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
                      historyLoading ||
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
            </>
          )}

          {hasConversation && (
            <ChatThread
              messages={visibleMessages}
              onClear={() => void handleClearHistory()}
              clearing={clearingHistory}
              disabled={chatLoading}
            />
          )}

          <div className={hasConversation ? "composer sticky" : "composer"}>
            {hasConversation && (
              <div className="quick-chips" aria-label="Suggested actions">
                {QUICK_ACTIONS.map((action) => (
                  <button
                    type="button"
                    key={action.title}
                    className="quick-chip"
                    disabled={chatLoading || !canUseWorkspace}
                    onClick={() => void runQuestion(action.prompt)}
                  >
                    <Icon name={action.icon} size={14} />
                    {action.title}
                  </button>
                ))}
              </div>
            )}

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
                  placeholder={
                    hasConversation
                      ? "Ask a follow-up question…"
                      : "Ask a question about the selected PDF…"
                  }
                  onKeyDown={handleQuestionKeyDown}
                  onChange={(event) =>
                    setQuestion(event.target.value)
                  }
                />

                <div className="question-footer">
                  <LanguageSelect
                    value={answerLanguage}
                    onChange={handleLanguageChange}
                    disabled={chatLoading}
                  />

                  <span className="send-hint">
                    <kbd>Ctrl</kbd> + <kbd>Enter</kbd> to send
                  </span>

                  <button
                    type="submit"
                    className="ask-button"
                    disabled={
                      chatLoading ||
                      historyLoading ||
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
              <p className="workspace-error" role="alert">{chatError}</p>
            )}
          </div>

          <div ref={threadEndRef} className="thread-end" aria-hidden="true" />

          {!historyLoading && !hasConversation && (
            <section className="answer-container">
              {!chatLoading && (
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
            </section>
          )}
        </div>
      </section>
    </main>
  );
}

export default App;