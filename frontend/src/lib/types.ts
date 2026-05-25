// ---------------------------------------------------------------------------
// Types mirroring the backend Pydantic schemas (auth_schema.py, query.py)
// and the JSON shapes returned by the chatbot/admin routers.
// ---------------------------------------------------------------------------

export type Role = "Admin" | "User";

/** UserOut — public, response-safe view of a user. */
export interface User {
  id: number;
  username: string;
  role: Role;
}

/** TokenOut — returned by POST /auth/login. */
export interface TokenOut {
  access_token: string;
  token_type: string;
}

/** LoginRequest — body for POST /auth/login. */
export interface LoginRequest {
  username: string;
  password: string;
}

/** UserCreate — body for POST /admin/users. */
export interface UserCreate {
  username: string;
  password: string;
  role: Role;
}

/** Query — body for the Ollama generate/chat endpoints. */
export interface Query {
  prompt: string;
  model: string;
  stream: boolean;
}

/** A single turn in a stored conversation. */
export interface ChatMessage {
  role: "user" | "assistant";
  content: string;
}

/** Full chat as returned by GET /chat/{chat_id}. */
export interface ChatDetail {
  chat_id: string;
  messages: ChatMessage[];
}

/** One entry in the user's chat list (GET /chat/{user_id}/chats). */
export interface ChatSummary {
  chat_id: string;
}

/** An Ollama model tag (subset of GET /chat/models we care about). */
export interface OllamaModel {
  name: string;
  size?: number;
}

/** Admin view of a chat row (GET /admin/users/{id}/chats). */
export interface AdminChatSummary {
  chat_id: string;
  user_id: number;
}

/** Admin view of a single chat (GET /admin/users/{id}/chats/{chat_id}). */
export interface AdminChatDetail {
  chat_id: string;
  user_id: number;
  messages: ChatMessage[];
}
