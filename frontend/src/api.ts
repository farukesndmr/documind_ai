const API_BASE_URL =
  import.meta.env.VITE_API_BASE_URL || "http://127.0.0.1:8000";

const ENDPOINTS = {
  register: "/auth/register",
  login: "/auth/login",
  me: "/auth/me",
  verifyEmail: "/auth/verify-email",
  documents: "/documents",
  documentsWithSlash: "/documents/",
  upload: "/documents/upload",
  chatAsk: "/chat/ask",
  adminUsers: "/admin/users",
  adminPendingUsers: "/admin/users/pending",
};

export type UserProfile = {
  id: number;
  email: string;
  role: string;
  email_verified: boolean;
  is_approved: boolean;
  approval_status: string;
  pdf_upload_count: number;
  question_count: number;
  can_use_app: boolean;
  is_active: boolean;
};

export type DocumentItem = {
  id: number;
  filename: string;
  created_at?: string;
};

export type ChatAnswer = {
  answer: string;
  sources?: unknown[];
  raw?: unknown;
};

export type VerifyEmailResult = {
  message: string;
  email_verified: boolean;
  approval_status?: string | null;
};

export function getToken(): string | null {
  return (
    localStorage.getItem("access_token") ||
    localStorage.getItem("token")
  );
}

export function setToken(token: string): void {
  localStorage.setItem("access_token", token);
}

export function clearToken(): void {
  localStorage.removeItem("access_token");
  localStorage.removeItem("token");
}

function getAuthHeaders(): Record<string, string> {
  const token = getToken();

  if (!token) {
    return {};
  }

  return {
    Authorization: `Bearer ${token}`,
  };
}

async function readErrorMessage(
  response: Response,
): Promise<string> {
  try {
    const data = await response.json();

    if (typeof data.detail === "string") {
      return data.detail;
    }

    if (Array.isArray(data.detail)) {
      return data.detail
        .map((item: unknown) => {
          if (
            typeof item === "object" &&
            item !== null &&
            "msg" in item
          ) {
            const message = (
              item as { msg?: unknown }
            ).msg;

            if (typeof message === "string") {
              return message;
            }
          }

          if (typeof item === "string") {
            return item;
          }

          return JSON.stringify(item) ?? String(item);
        })
        .join(", ");
    }

    return JSON.stringify(data);
  } catch {
    return response.statusText || "Unknown error";
  }
}

async function fetchFirstAvailable(
  paths: string[],
  initFactory: () => RequestInit,
): Promise<Response> {
  let lastResponse: Response | null = null;

  for (const path of paths) {
    const response = await fetch(
      `${API_BASE_URL}${path}`,
      initFactory(),
    );

    if (
      response.status !== 404 &&
      response.status !== 405
    ) {
      return response;
    }

    lastResponse = response;
  }

  if (lastResponse) {
    throw new Error(
      `Endpoint not found. Last status: ${lastResponse.status}`,
    );
  }

  throw new Error("Endpoint not found.");
}

function normalizeUserProfile(data: any): UserProfile {
  return {
    id: Number(data.id),
    email: String(data.email),
    role: String(data.role ?? "user"),
    email_verified: Boolean(data.email_verified),
    is_approved: Boolean(data.is_approved),
    approval_status: String(data.approval_status ?? "pending"),
    pdf_upload_count: Number(data.pdf_upload_count ?? 0),
    question_count: Number(data.question_count ?? 0),
    can_use_app: Boolean(data.can_use_app),
    is_active: Boolean(data.is_active),
  };
}

function normalizeDocument(document: any): DocumentItem {
  return {
    id: Number(
      document.id ??
        document.document_id,
    ),
    filename:
      document.filename ??
      document.file_name ??
      document.name ??
      document.title ??
      `Document ${
        document.id ??
        document.document_id
      }`,
    created_at: document.created_at,
  };
}

function normalizeDocumentsResponse(
  data: any,
): DocumentItem[] {
  if (Array.isArray(data)) {
    return data.map(normalizeDocument);
  }

  if (Array.isArray(data.documents)) {
    return data.documents.map(normalizeDocument);
  }

  if (Array.isArray(data.items)) {
    return data.items.map(normalizeDocument);
  }

  return [];
}

function normalizeChatResponse(
  data: any,
): ChatAnswer {
  const answer =
    data.answer ??
    data.response ??
    data.message ??
    data.result ??
    data.text ??
    JSON.stringify(data, null, 2);

  return {
    answer,
    sources:
      data.sources ??
      data.chunks ??
      data.context ??
      [],
    raw: data,
  };
}

async function parseAuthResponse(
  response: Response,
): Promise<string> {
  const data = await response.json();

  const token =
    data.access_token ??
    data.token;

  if (!token) {
    throw new Error(
      "Login response did not include access_token.",
    );
  }

  return token;
}

export async function registerUser(
  email: string,
  password: string,
): Promise<UserProfile> {
  const response = await fetchFirstAvailable(
    [ENDPOINTS.register, "/register"],
    () => ({
      method: "POST",
      headers: {
        "Content-Type": "application/json",
      },
      body: JSON.stringify({
        email,
        username: email,
        password,
      }),
    }),
  );

  if (!response.ok) {
    throw new Error(
      await readErrorMessage(response),
    );
  }

  const data = await response.json();
  return normalizeUserProfile(data);
}

export async function loginUser(
  email: string,
  password: string,
): Promise<string> {
  try {
    const jsonResponse =
      await fetchFirstAvailable(
        [ENDPOINTS.login, "/login"],
        () => ({
          method: "POST",
          headers: {
            "Content-Type": "application/json",
          },
          body: JSON.stringify({
            email,
            username: email,
            password,
          }),
        }),
      );

    if (jsonResponse.ok) {
      return parseAuthResponse(jsonResponse);
    }
  } catch {
    // JSON login çalışmazsa form login denenir.
  }

  const formData = new URLSearchParams();
  formData.append("username", email);
  formData.append("password", password);

  const formResponse =
    await fetchFirstAvailable(
      [ENDPOINTS.login, "/login"],
      () => ({
        method: "POST",
        headers: {
          "Content-Type":
            "application/x-www-form-urlencoded",
        },
        body: formData,
      }),
    );

  if (!formResponse.ok) {
    throw new Error(
      await readErrorMessage(formResponse),
    );
  }

  return parseAuthResponse(formResponse);
}

export async function getMe(): Promise<UserProfile> {
  const response = await fetch(
    `${API_BASE_URL}${ENDPOINTS.me}`,
    {
      method: "GET",
      headers: {
        ...getAuthHeaders(),
      },
    },
  );

  if (!response.ok) {
    throw new Error(
      await readErrorMessage(response),
    );
  }

  const data = await response.json();
  return normalizeUserProfile(data);
}

export async function verifyEmail(
  token: string,
): Promise<VerifyEmailResult> {
  const response = await fetch(
    `${API_BASE_URL}${ENDPOINTS.verifyEmail}?token=${encodeURIComponent(
      token,
    )}`,
    {
      method: "GET",
    },
  );

  if (!response.ok) {
    throw new Error(
      await readErrorMessage(response),
    );
  }

  return response.json();
}

export async function getDocuments(): Promise<
  DocumentItem[]
> {
  const response = await fetchFirstAvailable(
    [
      ENDPOINTS.documents,
      ENDPOINTS.documentsWithSlash,
    ],
    () => ({
      method: "GET",
      headers: {
        ...getAuthHeaders(),
      },
    }),
  );

  if (!response.ok) {
    throw new Error(
      await readErrorMessage(response),
    );
  }

  const data = await response.json();
  return normalizeDocumentsResponse(data);
}

export async function uploadDocument(
  file: File,
): Promise<unknown> {
  const formData = new FormData();
  formData.append("file", file);

  const response = await fetchFirstAvailable(
    [
      ENDPOINTS.upload,
      ENDPOINTS.documentsWithSlash,
      ENDPOINTS.documents,
    ],
    () => ({
      method: "POST",
      headers: {
        ...getAuthHeaders(),
      },
      body: formData,
    }),
  );

  if (!response.ok) {
    throw new Error(
      await readErrorMessage(response),
    );
  }

  return response.json();
}

export async function deleteDocument(
  documentId: number,
): Promise<void> {
  const response = await fetch(
    `${API_BASE_URL}${ENDPOINTS.documents}/${documentId}`,
    {
      method: "DELETE",
      headers: {
        ...getAuthHeaders(),
      },
    },
  );

  if (!response.ok) {
    throw new Error(
      await readErrorMessage(response),
    );
  }
}

export async function askQuestion(
  documentId: number,
  question: string,
): Promise<ChatAnswer> {
  const response = await fetch(
    `${API_BASE_URL}${ENDPOINTS.chatAsk}`,
    {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
        ...getAuthHeaders(),
      },
      body: JSON.stringify({
        document_id: documentId,
        question,
        message: question,
        limit: 6,
      }),
    },
  );

  if (!response.ok) {
    throw new Error(
      await readErrorMessage(response),
    );
  }

  const data = await response.json();
  return normalizeChatResponse(data);
}

export async function getAdminUsers(): Promise<UserProfile[]> {
  const response = await fetch(
    `${API_BASE_URL}${ENDPOINTS.adminUsers}`,
    {
      method: "GET",
      headers: {
        ...getAuthHeaders(),
      },
    },
  );

  if (!response.ok) {
    throw new Error(
      await readErrorMessage(response),
    );
  }

  const data = await response.json();
  return Array.isArray(data)
    ? data.map(normalizeUserProfile)
    : [];
}

export async function getPendingUsers(): Promise<UserProfile[]> {
  const response = await fetch(
    `${API_BASE_URL}${ENDPOINTS.adminPendingUsers}`,
    {
      method: "GET",
      headers: {
        ...getAuthHeaders(),
      },
    },
  );

  if (!response.ok) {
    throw new Error(
      await readErrorMessage(response),
    );
  }

  const data = await response.json();
  return Array.isArray(data)
    ? data.map(normalizeUserProfile)
    : [];
}

export async function approveUser(
  userId: number,
): Promise<UserProfile> {
  const response = await fetch(
    `${API_BASE_URL}${ENDPOINTS.adminUsers}/${userId}/approve`,
    {
      method: "PATCH",
      headers: {
        ...getAuthHeaders(),
      },
    },
  );

  if (!response.ok) {
    throw new Error(
      await readErrorMessage(response),
    );
  }

  const data = await response.json();
  return normalizeUserProfile(data);
}

export async function rejectUser(
  userId: number,
): Promise<UserProfile> {
  const response = await fetch(
    `${API_BASE_URL}${ENDPOINTS.adminUsers}/${userId}/reject`,
    {
      method: "PATCH",
      headers: {
        ...getAuthHeaders(),
      },
    },
  );

  if (!response.ok) {
    throw new Error(
      await readErrorMessage(response),
    );
  }

  const data = await response.json();
  return normalizeUserProfile(data);
}