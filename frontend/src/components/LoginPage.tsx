import {
  GoogleLogin,
  GoogleOAuthProvider,
} from "@react-oauth/google";

import { Icon } from "./Icon";
import { ServerStatus } from "./ServerStatus";

const GOOGLE_CLIENT_ID = import.meta.env.VITE_GOOGLE_CLIENT_ID as string;

type LoginPageProps = {
  authError: string;
  onCredential: (credential?: string) => Promise<void>;
  onGoogleError: () => void;
};

export function LoginPage({
  authError,
  onCredential,
  onGoogleError,
}: LoginPageProps) {
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
                  <Icon name="sparkles" size={19} />
                </div>

                <div>
                  <strong>Semantic search</strong>
                  <span>Finds passages by meaning, not just keywords.</span>
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

            <ServerStatus />

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
                <GoogleOAuthProvider clientId={GOOGLE_CLIENT_ID} locale="en">
                  <GoogleLogin
                    text="signin_with"
                    shape="pill"
                    size="large"
                    width="320"
                    useOneTap={false}
                    auto_select={false}
                    onSuccess={(credentialResponse) => {
                      void onCredential(credentialResponse.credential);
                    }}
                    onError={onGoogleError}
                  />
                </GoogleOAuthProvider>
              ) : (
                <p className="error-message">
                  Google sign-in is not configured.
                </p>
              )}
            </div>

            {authError && (
              <p className="error-message" role="alert">{authError}</p>
            )}

            <ol className="auth-steps">
              <li>
                <span>1</span>
                <div>
                  <strong>Upload a PDF</strong>
                  <p>Lecture notes, papers, reports — any text-based PDF.</p>
                </div>
              </li>
              <li>
                <span>2</span>
                <div>
                  <strong>Ask anything</strong>
                  <p>Or start with a summary, flashcards or a quiz.</p>
                </div>
              </li>
              <li>
                <span>3</span>
                <div>
                  <strong>Check the sources</strong>
                  <p>Every answer shows the passages and pages it used.</p>
                </div>
              </li>
            </ol>

            <div className="security-note">
              <Icon name="shield" size={15} />
              Google sign-in, protected API routes and demo limits
            </div>
          </div>
        </section>
      </main>
  );
}
