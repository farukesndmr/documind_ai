import { useEffect, useState } from "react";

import { Icon } from "./Icon";

export function CopyButton({ text }: { text: string }) {
  const [copied, setCopied] = useState(false);

  useEffect(() => {
    if (!copied) {
      return;
    }
    const timer = window.setTimeout(() => setCopied(false), 1800);
    return () => window.clearTimeout(timer);
  }, [copied]);

  async function handleCopy() {
    try {
      await navigator.clipboard.writeText(text);
      setCopied(true);
    } catch {
      setCopied(false);
    }
  }

  return (
    <button
      type="button"
      className="copy-button"
      onClick={() => void handleCopy()}
      aria-live="polite"
    >
      <Icon name={copied ? "check" : "copy"} size={14} />
      {copied ? "Copied" : "Copy"}
    </button>
  );
}
