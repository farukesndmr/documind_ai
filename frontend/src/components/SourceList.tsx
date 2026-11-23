import { useState } from "react";

import type { SourceChunk } from "../api";
import { Icon } from "./Icon";

const PREVIEW_LENGTH = 220;

function SourceCard({
  source,
  number,
}: {
  source: SourceChunk;
  number: number;
}) {
  const [expanded, setExpanded] = useState(false);
  const content = source.content.trim();
  const isLong = content.length > PREVIEW_LENGTH;
  const visibleText =
    expanded || !isLong
      ? content
      : `${content.slice(0, PREVIEW_LENGTH).trimEnd()}…`;

  return (
    <li className="source-card">
      <div className="source-card-header">
        <span className="source-number">{number}</span>
        <strong>Source {number}</strong>
        {source.page_number ? (
          <span className="source-page">Page {source.page_number}</span>
        ) : null}
      </div>

      <p className="source-text">{visibleText}</p>

      {isLong && (
        <button
          type="button"
          className="source-toggle"
          aria-expanded={expanded}
          onClick={() => setExpanded((value) => !value)}
        >
          {expanded ? "Show less" : "Show full passage"}
          <span className={expanded ? "chevron up" : "chevron"}>
            <Icon name="chevron" size={13} />
          </span>
        </button>
      )}
    </li>
  );
}

export function SourceList({
  sources,
  collapsible = false,
}: {
  sources: SourceChunk[];
  collapsible?: boolean;
}) {
  if (sources.length === 0) {
    return null;
  }

  const grid = (
    <ol className="source-grid">
      {sources.map((source, index) => (
        <SourceCard key={source.id} source={source} number={index + 1} />
      ))}
    </ol>
  );

  if (collapsible) {
    return (
      <details className="sources collapsible">
        <summary className="sources-header">
          <span>
            Sources <span className="source-count">{sources.length}</span>
          </span>
          <span className="sources-summary-hint">
            [1], [2]… in the answer refer to these passages
            <span className="chevron">
              <Icon name="chevron" size={13} />
            </span>
          </span>
        </summary>
        {grid}
      </details>
    );
  }

  return (
    <section className="sources" aria-label="Sources used for this answer">
      <header className="sources-header">
        <span>Sources</span>
        <span className="source-count">{sources.length}</span>
      </header>

      <p className="sources-hint">
        Numbers like [1] in the answer refer to these passages from your PDF.
      </p>

      {grid}
    </section>
  );
}
