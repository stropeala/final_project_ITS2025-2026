import {
  clearSession,
  getToken,
} from "./session.ts";
import type {
  AdminChatDetail,
  AdminChatSummary,
  ChatDetail,
  ChatSummary,
  LoginRequest,
  OllamaModel,
  Query,
  TokenOut,
  User,
  UserCreate,
} from "./types.ts";

// ---------------------------------------------------------------------------
// The path strings below are IDENTICAL to your FastAPI routes — "/auth/login",
// "/chat/chats", "/admin/users/3", etc. Put this file next to your routers and
// they read the same.
//
// In dev, vite.config.ts proxies the /auth, /chat, and /admin prefixes to the
// backend on :8000, so there's no CORS and no path rewriting. In production,
// serve the built frontend behind the same origin as the API (or a gateway
// that routes those prefixes to it) and everything keeps working unchanged.
// If the API ever lives on a separate origin, set API_BASE to that origin
// (e.g. "https://api.example.com") — the route strings stay the same.
// ---------------------------------------------------------------------------

const API_BASE = "";

export class ApiError extends Error {
  status: number;

  constructor(status: number, message: string) {
    super(message);
    this.name = "ApiError";
    this.status = status;
  }
}

type Method = "GET" | "POST" | "DELETE";

async function request<T>(
  method: Method,
  path: string,
  body?: unknown,
): Promise<T> {
  const headers: Record<string, string> = {};
  const token = getToken();
  if (token) headers["Authorization"] = `Bearer ${token}`;
  if (body !== undefined) headers["Content-Type"] = "application/json";

  const response = await fetch(API_BASE + path, {
    method,
    headers,
    body: body !== undefined ? JSON.stringify(body) : undefined,
  });

  // Expired / missing token: drop the session so the router bounces to login.
  if (response.status === 401) {
    clearSession();
    if (!location.hash.startsWith("#/login")) {
      location.hash = "#/login";
    }
    throw new ApiError(401, await readError(response));
  }

  if (!response.ok) {
    throw new ApiError(response.status, await readError(response));
  }

  // 204 No Content (e.g. delete user) — nothing to parse.
  if (response.status === 204) return undefined as T;

  const text = await response.text();
  return (text ? JSON.parse(text) : undefined) as T;
}

/** Pull FastAPI's {"detail": "..."} out, falling back to a generic message. */
async function readError(response: Response): Promise<string> {
  try {
    const data = await response.json();
    if (typeof data?.detail === "string") return data.detail;
    if (Array.isArray(data?.detail) && data.detail[0]?.msg) {
      return String(data.detail[0].msg);
    }
    return `Request failed (${response.status})`;
  } catch {
    return `Request failed (${response.status})`;
  }
}

const enc = encodeURIComponent;

// --- Auth -----------------------------------------------------------------

export function login(payload: LoginRequest): Promise<TokenOut> {
  return request<TokenOut>("POST", "/auth/login", payload);
}

export function fetchProfile(): Promise<User> {
  return request<User>("GET", "/auth/profile");
}

// --- Chat -----------------------------------------------------------------

export async function listModels(): Promise<OllamaModel[]> {
  const data = await request<{ models: OllamaModel[] }>("GET", "/chat/models");
  return data.models ?? [];
}

export function createChat(chatId: string): Promise<{ message: string }> {
  return request<{ message: string }>("POST", `/chat/${enc(chatId)}`, {});
}

export function sendMessage(
  chatId: string,
  query: Query,
): Promise<{ generated_text: string }> {
  return request<{ generated_text: string }>(
    "POST",
    `/chat/${enc(chatId)}/message`,
    query,
  );
}

export function getChat(chatId: string): Promise<ChatDetail> {
  return request<ChatDetail>("GET", `/chat/${enc(chatId)}`);
}

export function listChats(): Promise<ChatSummary[]> {
  return request<ChatSummary[]>("GET", "/chat/chats");
}

export function deleteChat(chatId: string): Promise<{ message: string }> {
  return request<{ message: string }>("DELETE", `/chat/${enc(chatId)}`);
}

// --- Admin ----------------------------------------------------------------

export function adminCreateUser(payload: UserCreate): Promise<User> {
  return request<User>("POST", "/admin/users", payload);
}

export function adminListUsers(): Promise<User[]> {
  return request<User[]>("GET", "/admin/users");
}

export function adminDeleteUser(userId: number): Promise<void> {
  return request<void>("DELETE", `/admin/users/${userId}`);
}

export function adminListUserChats(
  userId: number,
): Promise<AdminChatSummary[]> {
  return request<AdminChatSummary[]>("GET", `/admin/users/${userId}/chats`);
}

export function adminGetUserChat(
  userId: number,
  chatId: string,
): Promise<AdminChatDetail> {
  return request<AdminChatDetail>(
    "GET",
    `/admin/users/${userId}/chats/${enc(chatId)}`,
  );
}

export function adminDeleteUserChat(
  userId: number,
  chatId: string,
): Promise<{ message: string }> {
  return request<{ message: string }>(
    "DELETE",
    `/admin/users/${userId}/chats/${enc(chatId)}`,
  );
}
