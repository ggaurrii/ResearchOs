import { clearTokens, getAccessToken, getRefreshToken, setTokens } from "./token-store";

const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000/api/v1";

// ---------------------------------------------------------------- types

export type Role = "student" | "researcher" | "mentor" | "admin";
export type Visibility = "private" | "team" | "public";
export type PaperSource = "openalex" | "arxiv" | "semantic_scholar" | "pubmed" | "crossref" | "upload";

export interface User {
  id: string;
  email: string;
  full_name: string;
  role: Role;
  institution: string | null;
  status: string;
  email_verified_at: string | null;
  created_at: string;
}

export interface TokenResponse {
  access_token: string;
  refresh_token: string;
  token_type: string;
  expires_in: number;
}

export interface Workspace {
  id: string;
  owner_id: string;
  title: string;
  domain: string | null;
  description: string | null;
  visibility: Visibility;
  status: string;
  created_at: string;
  updated_at: string;
}

export interface ActivityEntry {
  id: string;
  actor_id: string;
  event_type: string;
  event_data: Record<string, unknown> | null;
  created_at: string;
}

export interface Paper {
  id: string;
  workspace_id: string;
  title: string;
  authors: string[] | null;
  doi: string | null;
  source: PaperSource;
  publication_year: number | null;
  storage_path: string | null;
  abstract: string | null;
  analysis_status: string;
  added_by: string;
  created_at: string;
}

export interface LiteratureSearchResult {
  title: string;
  authors: string[];
  year: number | null;
  venue: string | null;
  doi: string | null;
  source: PaperSource;
  abstract_snippet: string | null;
}

export interface LiteratureSearchResponse {
  results: LiteratureSearchResult[];
  sources_queried: string[];
  sources_failed: string[];
  total_results: number;
}

export interface Page<T> {
  results: T[];
  page: number;
  page_size: number;
  total_results: number;
}

export class ApiError extends Error {
  code: string;
  status: number;
  details: Record<string, unknown>;

  constructor(status: number, code: string, message: string, details: Record<string, unknown> = {}) {
    super(message);
    this.status = status;
    this.code = code;
    this.details = details;
  }
}

// ------------------------------------------------------------- core fetch

interface RequestOptions {
  method?: string;
  body?: unknown;
  isForm?: boolean;
  skipAuth?: boolean;
}

let refreshInFlight: Promise<void> | null = null;

async function doRefresh(): Promise<void> {
  const refreshToken = getRefreshToken();
  if (!refreshToken) throw new ApiError(401, "UNAUTHORIZED", "Not signed in.");

  const resp = await fetch(`${API_BASE_URL}/auth/refresh`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ refresh_token: refreshToken }),
  });

  if (!resp.ok) {
    clearTokens();
    throw new ApiError(401, "UNAUTHORIZED", "Session expired. Please sign in again.");
  }

  const tokens: TokenResponse = await resp.json();
  setTokens(tokens);
}

async function request<T>(path: string, options: RequestOptions = {}, isRetry = false): Promise<T> {
  const { method = "GET", body, isForm = false, skipAuth = false } = options;

  const headers: Record<string, string> = {};
  if (!isForm) headers["Content-Type"] = "application/json";

  if (!skipAuth) {
    const token = getAccessToken();
    if (token) headers["Authorization"] = `Bearer ${token}`;
  }

  const resp = await fetch(`${API_BASE_URL}${path}`, {
    method,
    headers,
    body: body === undefined ? undefined : isForm ? (body as FormData) : JSON.stringify(body),
  });

  if (resp.status === 204) {
    return undefined as T;
  }

  const isJson = resp.headers.get("content-type")?.includes("application/json");
  const payload = isJson ? await resp.json() : undefined;

  if (!resp.ok) {
    // Access token expired mid-session: refresh once and retry the original
    // request, rather than bouncing the user straight to the login screen.
    if (resp.status === 401 && !skipAuth && !isRetry && getRefreshToken()) {
      refreshInFlight ??= doRefresh().finally(() => {
        refreshInFlight = null;
      });
      try {
        await refreshInFlight;
        return request<T>(path, options, true);
      } catch {
        // fall through to throwing the original error below
      }
    }

    const err = payload?.error;
    throw new ApiError(
      resp.status,
      err?.code ?? "UNKNOWN_ERROR",
      err?.message ?? `Request failed with status ${resp.status}`,
      err?.details ?? {}
    );
  }

  return payload as T;
}

// ------------------------------------------------------------------ auth

export const api = {
  register: (data: { email: string; password: string; full_name: string; role: Role; institution?: string }) =>
    request<User>("/auth/register", { method: "POST", body: data, skipAuth: true }),

  login: async (email: string, password: string) => {
    const tokens = await request<TokenResponse>("/auth/login", {
      method: "POST",
      body: { email, password },
      skipAuth: true,
    });
    setTokens(tokens);
    return tokens;
  },

  logout: async () => {
    const refreshToken = getRefreshToken();
    clearTokens();
    if (refreshToken) {
      await request("/auth/logout", { method: "POST", body: { refresh_token: refreshToken } }).catch(() => {
        // Best-effort revoke; the client-side token is already cleared either way.
      });
    }
  },

  getMe: () => request<User>("/users/me"),

  updateMe: (data: { full_name?: string; institution?: string }) =>
    request<User>("/users/me", { method: "PATCH", body: data }),

  // ------------------------------------------------------------ workspaces

  createWorkspace: (data: { title: string; domain?: string; description?: string; visibility?: Visibility }) =>
    request<Workspace>("/workspaces", { method: "POST", body: data }),

  listWorkspaces: (page = 1, pageSize = 20) =>
    request<Page<Workspace>>(`/workspaces?page=${page}&page_size=${pageSize}`),

  getWorkspace: (id: string) => request<Workspace>(`/workspaces/${id}`),

  updateWorkspace: (
    id: string,
    data: { title?: string; domain?: string; description?: string; visibility?: Visibility }
  ) => request<Workspace>(`/workspaces/${id}`, { method: "PATCH", body: data }),

  archiveWorkspace: (id: string) => request<void>(`/workspaces/${id}`, { method: "DELETE" }),

  getActivity: (id: string, page = 1, pageSize = 20) =>
    request<Page<ActivityEntry>>(`/workspaces/${id}/activity?page=${page}&page_size=${pageSize}`),

  // ------------------------------------------------------------ literature

  searchLiterature: (workspaceId: string, keywords: string[], domain?: string) =>
    request<LiteratureSearchResponse>(`/workspaces/${workspaceId}/literature/search`, {
      method: "POST",
      body: { keywords, domain },
    }),

  addPaper: (
    workspaceId: string,
    data: {
      title: string;
      authors?: string[];
      doi?: string;
      source: PaperSource;
      publication_year?: number;
      abstract?: string;
    }
  ) => request<Paper>(`/workspaces/${workspaceId}/papers`, { method: "POST", body: data }),

  uploadPaper: (workspaceId: string, file: File) => {
    const form = new FormData();
    form.append("file", file);
    return request<Paper>(`/workspaces/${workspaceId}/papers/upload`, {
      method: "POST",
      body: form,
      isForm: true,
    });
  },

  listPapers: (workspaceId: string, page = 1, pageSize = 20) =>
    request<Page<Paper>>(`/workspaces/${workspaceId}/papers?page=${page}&page_size=${pageSize}`),

  getPaper: (workspaceId: string, paperId: string) =>
    request<Paper>(`/workspaces/${workspaceId}/papers/${paperId}`),
};
