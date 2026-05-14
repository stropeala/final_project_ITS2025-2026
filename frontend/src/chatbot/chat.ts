import "./style.css";

// ─── Types ────────────────────────────────────────────────────────────────────

interface Message {
  role: "user" | "assistant";
  content: string;
  timestamp: number;
}

interface ChatSession {
  id: string;
  messages: Message[];
  createdAt: number;
}

interface OllamaModel {
  name: string;
  model: string;
  [key: string]: unknown;
}

// ─── State ────────────────────────────────────────────────────────────────────

const sessions = new Map<string, ChatSession>();
let activeChatId: string | null = null;
let selectedModel = "gemma3:4b";
let isSending = false;

// ─── DOM refs ─────────────────────────────────────────────────────────────────

const statusIndicator =
  document.querySelector<HTMLSpanElement>("#status-indicator")!;
const statusText = document.querySelector<HTMLSpanElement>("#status-text")!;
const modelSelect = document.querySelector<HTMLSelectElement>("#model-select")!;
const newChatBtn = document.querySelector<HTMLButtonElement>("#new-chat-btn")!;
const sessionList = document.querySelector<HTMLUListElement>("#session-list")!;
const emptyState = document.querySelector<HTMLDivElement>("#empty-state")!;
const messagesEl = document.querySelector<HTMLDivElement>("#messages")!;
const thinkingEl = document.querySelector<HTMLDivElement>("#thinking")!;
const inputEl = document.querySelector<HTMLTextAreaElement>("#input")!;
const sendBtn = document.querySelector<HTMLButtonElement>("#send-btn")!;

// ─── API helpers ──────────────────────────────────────────────────────────────

async function apiFetch<T>(path: string, init?: RequestInit): Promise<T> {
  const res = await fetch(`/api${path}`, {
    headers: { "Content-Type": "application/json" },
    ...init,
  });
  if (!res.ok) {
    const detail = await res.json().catch(() => ({}));
    throw new Error(detail?.detail ?? `HTTP ${res.status}`);
  }
  return res.json() as Promise<T>;
}

// ─── Connection check ─────────────────────────────────────────────────────────

async function checkConnection(): Promise<boolean> {
  try {
    await apiFetch<{ message: string }>("/");
    setStatus("ok", "connected");
    return true;
  } catch {
    setStatus("err", "disconnected");
    return false;
  }
}

function setStatus(state: "connecting" | "ok" | "err", label: string) {
  statusIndicator.className = `status-indicator ${state}`;
  statusText.textContent = label;
}

// ─── Models ───────────────────────────────────────────────────────────────────

async function loadModels() {
  try {
    const { models } = await apiFetch<{ models: OllamaModel[] }>("/models");
    modelSelect.innerHTML = "";
    for (const m of models) {
      const opt = document.createElement("option");
      opt.value = m.name ?? m.model;
      opt.textContent = m.name ?? m.model;
      modelSelect.appendChild(opt);
    }
    selectedModel = modelSelect.value;
    modelSelect.disabled = false;
  } catch {
    modelSelect.innerHTML = `<option value="${selectedModel}">${selectedModel}</option>`;
    modelSelect.disabled = false;
    selectedModel = modelSelect.value;
  }
}

modelSelect.addEventListener("change", () => {
  selectedModel = modelSelect.value;
});

// ─── Session management ───────────────────────────────────────────────────────

function generateId(): string {
  return `chat_${Date.now().toString(36)}_${Math.random().toString(36).slice(2, 6)}`;
}

async function createSession(): Promise<string> {
  const id = generateId();
  await apiFetch<{ message: string }>(
    `/chat/start?chat_id=${encodeURIComponent(id)}`,
    {
      method: "POST",
    },
  );
  const session: ChatSession = { id, messages: [], createdAt: Date.now() };
  sessions.set(id, session);
  renderSidebar();
  return id;
}

function selectSession(id: string) {
  activeChatId = id;
  renderSidebar();
  renderMessages();
  enableInput();
  scrollToBottom();
}

function renderSidebar() {
  sessionList.innerHTML = "";
  const sorted = [...sessions.values()].sort(
    (a, b) => b.createdAt - a.createdAt,
  );

  for (const session of sorted) {
    const li = document.createElement("li");
    li.className = `session-item${session.id === activeChatId ? " active" : ""}`;
    li.dataset["id"] = session.id;

    const preview =
      session.messages[0]?.content.slice(0, 32) ?? "empty session";
    const time = formatTime(session.createdAt);

    li.innerHTML = `
      <span class="session-id">${session.id}</span>
      <span class="session-preview">${escapeHtml(preview)}${preview.length >= 32 ? "…" : ""}</span>
      <span class="session-time">${time}</span>
    `;

    li.addEventListener("click", () => selectSession(session.id));
    sessionList.appendChild(li);
  }
}

// ─── Messaging ────────────────────────────────────────────────────────────────

async function sendMessage() {
  if (isSending || !activeChatId) return;

  const text = inputEl.value.trim();
  if (!text) return;

  const session = sessions.get(activeChatId);
  if (!session) return;

  isSending = true;
  inputEl.value = "";
  autoResizeInput();
  disableInput();

  // Optimistically add user message
  const userMsg: Message = {
    role: "user",
    content: text,
    timestamp: Date.now(),
  };
  session.messages.push(userMsg);
  renderMessages();
  showThinking(true);
  scrollToBottom();

  try {
    const { generated_text } = await apiFetch<{ generated_text: string }>(
      `/chat/${encodeURIComponent(activeChatId)}/message`,
      {
        method: "POST",
        body: JSON.stringify({
          prompt: text,
          model: selectedModel,
          stream: false,
        }),
      },
    );

    const assistantMsg: Message = {
      role: "assistant",
      content: generated_text,
      timestamp: Date.now(),
    };
    session.messages.push(assistantMsg);
  } catch (err) {
    const errMsg: Message = {
      role: "assistant",
      content: `[error] ${err instanceof Error ? err.message : String(err)}`,
      timestamp: Date.now(),
    };
    session.messages.push(errMsg);
  } finally {
    isSending = false;
    showThinking(false);
    renderMessages();
    renderSidebar();
    enableInput();
    inputEl.focus();
    scrollToBottom();
  }
}

// ─── Render ───────────────────────────────────────────────────────────────────

function renderMessages() {
  const session = activeChatId ? sessions.get(activeChatId) : null;

  if (!session) {
    emptyState.classList.remove("hidden");
    messagesEl.classList.add("hidden");
    return;
  }

  emptyState.classList.add("hidden");
  messagesEl.classList.remove("hidden");
  messagesEl.innerHTML = "";

  for (const msg of session.messages) {
    const div = document.createElement("div");
    div.className = `message ${msg.role}`;
    div.innerHTML = `
      <span class="message-prefix">${msg.role === "user" ? ">" : "<"}</span>
      <div class="message-body">
        <p class="message-text">${escapeHtml(msg.content)}</p>
        <span class="message-meta">${formatTime(msg.timestamp)}</span>
      </div>
    `;
    messagesEl.appendChild(div);
  }
}

function showThinking(show: boolean) {
  thinkingEl.classList.toggle("hidden", !show);
}

function scrollToBottom() {
  const area = document.querySelector<HTMLDivElement>("#chat-area")!;
  requestAnimationFrame(() => {
    area.scrollTop = area.scrollHeight;
  });
}

// ─── Input handling ───────────────────────────────────────────────────────────

function enableInput() {
  inputEl.disabled = false;
  sendBtn.disabled = false;
}

function disableInput() {
  sendBtn.disabled = true;
}

function autoResizeInput() {
  inputEl.style.height = "auto";
  inputEl.style.height = `${Math.min(inputEl.scrollHeight, 180)}px`;
}

inputEl.addEventListener("input", autoResizeInput);

inputEl.addEventListener("keydown", (e) => {
  if (e.key === "Enter" && !e.shiftKey) {
    e.preventDefault();
    sendMessage();
  }
});

sendBtn.addEventListener("click", () => sendMessage());

newChatBtn.addEventListener("click", async () => {
  newChatBtn.disabled = true;
  try {
    const id = await createSession();
    selectSession(id);
    inputEl.focus();
  } catch (err) {
    console.error("Failed to start chat:", err);
  } finally {
    newChatBtn.disabled = false;
  }
});

// ─── Utils ────────────────────────────────────────────────────────────────────

function escapeHtml(str: string): string {
  return str
    .replace(/&/g, "&amp;")
    .replace(/</g, "&lt;")
    .replace(/>/g, "&gt;")
    .replace(/"/g, "&quot;");
}

function formatTime(ts: number): string {
  return new Date(ts).toLocaleTimeString([], {
    hour: "2-digit",
    minute: "2-digit",
    second: "2-digit",
  });
}

// ─── Boot ─────────────────────────────────────────────────────────────────────

async function init() {
  setStatus("connecting", "connecting");
  const connected = await checkConnection();
  if (connected) {
    await loadModels();
    newChatBtn.disabled = false;
  }
}

init();
