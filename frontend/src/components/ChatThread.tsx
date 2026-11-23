import ReactMarkdown from "react-markdown";
import remarkGfm from "remark-gfm";

import type { ChatMessage } from "../api";
import { CopyButton } from "./CopyButton";
import { Icon } from "./Icon";
import { SourceList } from "./SourceList";

function UserMessage({ message }: { message: ChatMessage }) {
  return (
    <li className="chat-message user">
      <div className="user-bubble">{message.content}</div>
    </li>
  );
}

function AssistantMessage({ message }: { message: ChatMessage }) {
  const isStreaming = message.status === "streaming";
  const hasText = message.content.length > 0;

  return (
    <li className="chat-message assistant">
      <div className="assistant-avatar" aria-hidden="true">
        <Icon name="sparkles" size={15} />
      </div>

      <div className="assistant-card">
        {!hasText && isStreaming ? (
          <div className="assistant-thinking" role="status">
            <span>Searching relevant passages…</span>
            <div className="loading-lines">
              <span className="long" />
              <span className="medium" />
              <span className="short" />
            </div>
          </div>
        ) : (
          <article
            className={isStreaming ? "markdown-answer streaming" : "markdown-answer"}
            aria-busy={isStreaming}
          >
            <ReactMarkdown remarkPlugins={[remarkGfm]}>
              {message.content}
            </ReactMarkdown>
          </article>
        )}

        {message.status === "interrupted" && (
          <p className="message-note">
            This answer was interrupted and was not saved.
          </p>
        )}

        {!isStreaming && hasText && (
          <footer className="assistant-footer">
            <CopyButton text={message.content} />
          </footer>
        )}

        {!isStreaming && message.sources.length > 0 && (
          <SourceList sources={message.sources} collapsible />
        )}
      </div>
    </li>
  );
}

type ChatThreadProps = {
  messages: ChatMessage[];
  onClear: () => void;
  clearing: boolean;
  disabled: boolean;
};

export function ChatThread({ messages, onClear, clearing, disabled }: ChatThreadProps) {
  return (
    <section className="chat-thread" aria-label="Conversation">
      <header className="chat-thread-header">
        <div>
          <span className="section-caption">Conversation</span>
          <strong>
            {Math.ceil(messages.length / 2)}{" "}
            {Math.ceil(messages.length / 2) === 1 ? "question" : "questions"}
          </strong>
        </div>

        <button
          type="button"
          className="clear-chat-button"
          onClick={onClear}
          disabled={disabled || clearing}
        >
          <Icon name="trash" size={14} />
          {clearing ? "Clearing…" : "Clear chat"}
        </button>
      </header>

      <ol className="chat-messages">
        {messages.map((message) =>
          message.role === "user" ? (
            <UserMessage key={message.id} message={message} />
          ) : (
            <AssistantMessage key={message.id} message={message} />
          ),
        )}
      </ol>
    </section>
  );
}
