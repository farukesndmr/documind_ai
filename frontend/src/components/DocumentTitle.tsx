import { useState, type FormEvent, type KeyboardEvent } from "react";

import { displayTitle } from "../documentTitle";
import { Icon } from "./Icon";

type DocumentTitleProps = {
  title: string;
  disabled?: boolean;
  onRename: (title: string) => Promise<void>;
};

export function DocumentTitle({ title, disabled, onRename }: DocumentTitleProps) {
  const [editing, setEditing] = useState(false);
  const [draft, setDraft] = useState(title);
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState("");

  function startEditing() {
    setDraft(displayTitle(title));
    setError("");
    setEditing(true);
  }

  function cancel() {
    setEditing(false);
    setError("");
  }

  async function save(event?: FormEvent) {
    event?.preventDefault();
    const cleaned = draft.trim().replace(/\s+/g, " ");

    if (!cleaned) {
      setError("The name cannot be empty.");
      return;
    }

    if (cleaned === displayTitle(title)) {
      setEditing(false);
      return;
    }

    try {
      setSaving(true);
      setError("");
      await onRename(cleaned);
      setEditing(false);
    } catch (renameError) {
      setError(
        renameError instanceof Error
          ? renameError.message
          : "The document could not be renamed.",
      );
    } finally {
      setSaving(false);
    }
  }

  function handleKeyDown(event: KeyboardEvent<HTMLInputElement>) {
    if (event.key === "Escape") {
      event.preventDefault();
      cancel();
    }
  }

  if (editing) {
    return (
      <form className="title-editor" onSubmit={(event) => void save(event)}>
        <input
          autoFocus
          value={draft}
          maxLength={200}
          disabled={saving}
          aria-label="Document name"
          onChange={(event) => setDraft(event.target.value)}
          onKeyDown={handleKeyDown}
        />
        <div className="title-editor-actions">
          <button type="submit" className="title-save" disabled={saving}>
            <Icon name="check" size={14} />
            {saving ? "Saving…" : "Save"}
          </button>
          <button type="button" className="title-cancel" onClick={cancel} disabled={saving}>
            Cancel
          </button>
        </div>
        {error && (
          <p className="error-message" role="alert">
            {error}
          </p>
        )}
      </form>
    );
  }

  return (
    <div className="title-row">
      <h1 title={title}>{displayTitle(title)}</h1>
      <button
        type="button"
        className="title-edit-button"
        onClick={startEditing}
        disabled={disabled}
        aria-label="Rename document"
        title="Rename document"
      >
        <Icon name="edit" size={15} />
      </button>
    </div>
  );
}
