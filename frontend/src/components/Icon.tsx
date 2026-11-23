export type IconName =
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
  | "trash"
  | "copy"
  | "chevron"
  | "server";

export function Icon({
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

    case "copy":
      return (
        <svg {...iconProps}>
          <rect x="9" y="9" width="12" height="12" rx="2" />
          <path d="M5 15H4a1 1 0 0 1-1-1V4a1 1 0 0 1 1-1h10a1 1 0 0 1 1 1v1" />
        </svg>
      );

    case "chevron":
      return (
        <svg {...iconProps}>
          <path d="m6 9 6 6 6-6" />
        </svg>
      );

    case "server":
      return (
        <svg {...iconProps}>
          <rect x="3" y="4" width="18" height="7" rx="2" />
          <rect x="3" y="13" width="18" height="7" rx="2" />
          <path d="M7 7.5h.01" />
          <path d="M7 16.5h.01" />
        </svg>
      );

    default:
      return null;
  }
}
