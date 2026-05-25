import {
  ApiError,
  createChat,
  deleteChat,
  getChat,
  listChats,
  listModels,
  sendMessage,
} from "../lib/api.ts";
import { el, mount, clear, toast } from "../lib/dom.ts";
import { renderMarkdown } from "../lib/markdown.ts";
import { randomChatName } from "../lib/names.ts";
import type { ChatMessage, ChatSummary, OllamaModel, User } from "../lib/types.ts";
import { appBar } from "./shell.ts";

const DEFAULT_MODEL = "gemma3:4b";
// Names that would collide with the literal chat routes:
// POST /chat/generate, GET /chat/models, GET /chat/chats.
const RESERVED_NAMES = ["models", "generate", "chats"];

export function renderChat(root: HTMLElement, user: User): void {
  // --- State -------------------------------------------------------------
  let chats: ChatSummary[] = [];
  let models: OllamaModel[] = [];
  let selectedModel = DEFAULT_MODEL;
  let activeId: string | null = null;
  let messages: ChatMessage[] = [];
  let pending = false;

  // --- Element refs ------------------------------------------------------
  const listEl = el("div", { class: "chat-list" });
  const mainEl = el("section", { class: "chat-main" });
  const modelSelect = el("select", { class: "input" }) as HTMLSelectElement;
  modelSelect.addEventListener("change", () => (selectedModel = modelSelect.value));

  const newBtn = el(
    "button",
    { class: "btn btn--primary btn--block", onClick: () => openNewChatModal() },
    "+ New chat",
  );

  const side = el(
    "aside",
    { class: "chat-side" },
    el("div", { class: "side-head" }, newBtn),
    el("div", { class: "side-section-label" }, "Your chats"),
    listEl,
    el(
      "div",
      { class: "side-foot" },
      el("label", { class: "field" }, el("label", {}, "Model"), modelSelect),
    ),
  );

  const layout = el("div", { class: "chat-layout" }, side, mainEl);
  mount(root, el("div", { class: "app" }, appBar(user, "chat"), layout));

  renderEmptyMain();
  void bootstrap();

  // --- Bootstrap ---------------------------------------------------------
  async function bootstrap(): Promise<void> {
    await Promise.all([loadModels(), loadChats()]);
  }

  async function loadModels(): Promise<void> {
    clear(modelSelect);
    try {
      models = await listModels();
    } catch {
      models = [];
    }
    if (models.length === 0) {
      modelSelect.appendChild(el("option", { value: DEFAULT_MODEL }, DEFAULT_MODEL));
      selectedModel = DEFAULT_MODEL;
      return;
    }
    const names = models.map((m) => m.name);
    selectedModel = names.includes(DEFAULT_MODEL) ? DEFAULT_MODEL : names[0];
    for (const name of names) {
      modelSelect.appendChild(el("option", { value: name }, name));
    }
    modelSelect.value = selectedModel;
  }

  async function loadChats(): Promise<void> {
    try {
      chats = await listChats();
    } catch (err) {
      chats = [];
      toast(err instanceof ApiError ? err.message : "Couldn't load chats.", "error");
    }
    renderList();
  }

  // --- Sidebar list ------------------------------------------------------
  function renderList(): void {
    clear(listEl);
    if (chats.length === 0) {
      listEl.appendChild(el("div", { class: "side-empty" }, "No chats yet. Start one above."));
      return;
    }
    for (const chat of chats) {
      const item = el(
        "div",
        {
          class: `chat-item${chat.chat_id === activeId ? " active" : ""}`,
          onClick: () => void selectChat(chat.chat_id),
        },
        el("span", { class: "chat-item__name" }, chat.chat_id),
        el(
          "button",
          {
            class: "chat-item__del",
            title: "Delete chat",
            onClick: (e: Event) => {
              e.stopPropagation();
              void removeChat(chat.chat_id);
            },
          },
          "×",
        ),
      );
      listEl.appendChild(item);
    }
  }

  // --- Main panel --------------------------------------------------------
  function renderEmptyMain(): void {
    mount(
      mainEl,
      el(
        "div",
        { class: "chat-empty" },
        el(
          "div",
          { class: "chat-empty__inner" },
          el("h2", {}, "Pick a chat, or start a new one"),
          el(
            "p",
            {},
            "Every conversation is saved under a unique name so you can come " +
              "back to it later.",
          ),
          el(
            "button",
            { class: "btn btn--primary", onClick: () => openNewChatModal() },
            "+ New chat",
          ),
        ),
      ),
    );
  }

  let msgListEl: HTMLElement | null = null;
  let composerInput: HTMLTextAreaElement | null = null;

  function renderActiveMain(): void {
    if (!activeId) {
      renderEmptyMain();
      return;
    }

    msgListEl = el("div", { class: "msg-list" });

    const textarea = el("textarea", {
      class: "input",
      placeholder: "Send a message…  (Enter to send, Shift+Enter for newline)",
      rows: 1,
    }) as HTMLTextAreaElement;
    composerInput = textarea;

    autoGrow(textarea);
    textarea.addEventListener("input", () => autoGrow(textarea));
    textarea.addEventListener("keydown", (e: KeyboardEvent) => {
      if (e.key === "Enter" && !e.shiftKey) {
        e.preventDefault();
        void handleSend();
      }
    });

    const sendBtn = el(
      "button",
      { class: "btn btn--primary", onClick: () => void handleSend() },
      "Send",
    );

    const composer = el(
      "div",
      { class: "composer" },
      el("div", { class: "composer__row" }, textarea, sendBtn),
      el("div", { class: "composer__hint" }, `chat: ${activeId}  ·  model: ${selectedModel}`),
    );

    mount(
      mainEl,
      el(
        "div",
        { class: "chat-main__head" },
        el("span", { class: "chat-main__title" }, activeId),
        el("span", { class: "chat-main__model" }, selectedModel),
      ),
      msgListEl,
      composer,
    );

    renderMessages();
    textarea.focus();
  }

  function renderMessages(): void {
    if (!msgListEl) return;
    clear(msgListEl);

    if (messages.length === 0 && !pending) {
      msgListEl.appendChild(
        el("div", { class: "msg msg--assistant" }, "New chat — say hello to get started."),
      );
    }

    for (const m of messages) {
      const bubble = el(
        "div",
        { class: `msg msg--${m.role}` },
        el("div", { class: "msg__role" }, m.role),
      );
      if (m.role === "assistant") {
        // Assistant output is Markdown — render it (safely) to HTML.
        bubble.appendChild(
          el("div", { class: "md", html: renderMarkdown(m.content) }),
        );
      } else {
        // User text is shown verbatim (el() text nodes are auto-escaped).
        bubble.appendChild(el("div", {}, m.content));
      }
      msgListEl.appendChild(bubble);
    }

    if (pending) {
      msgListEl.appendChild(
        el(
          "div",
          { class: "msg msg--assistant msg--pending" },
          el("div", { class: "msg__role" }, "assistant"),
          el("span", { class: "dots" }, "thinking"),
        ),
      );
    }

    msgListEl.scrollTop = msgListEl.scrollHeight;
  }

  // --- Actions -----------------------------------------------------------
  async function selectChat(id: string): Promise<void> {
    try {
      const detail = await getChat(id);
      activeId = id;
      messages = detail.messages ?? [];
      pending = false;
      renderList();
      renderActiveMain();
    } catch (err) {
      toast(err instanceof ApiError ? err.message : "Couldn't open chat.", "error");
    }
  }

  async function handleSend(): Promise<void> {
    if (!activeId || pending || !composerInput) return;
    const prompt = composerInput.value.trim();
    if (!prompt) return;

    composerInput.value = "";
    autoGrow(composerInput);

    messages = [...messages, { role: "user", content: prompt }];
    pending = true;
    renderMessages();

    try {
      const { generated_text } = await sendMessage(activeId, {
        prompt,
        model: selectedModel,
        stream: false,
      });
      pending = false;
      messages = [...messages, { role: "assistant", content: generated_text }];
      renderMessages();
    } catch (err) {
      // Backend rolls the turn back on failure, so we do too.
      pending = false;
      messages = messages.slice(0, -1);
      renderMessages();
      if (composerInput) composerInput.value = prompt;
      toast(err instanceof ApiError ? err.message : "Send failed.", "error");
    }
  }

  async function removeChat(id: string): Promise<void> {
    if (!confirm(`Delete chat "${id}"? This can't be undone.`)) return;
    try {
      await deleteChat(id);
      chats = chats.filter((c) => c.chat_id !== id);
      if (activeId === id) {
        activeId = null;
        messages = [];
        renderEmptyMain();
      }
      renderList();
      toast(`Deleted "${id}".`, "info");
    } catch (err) {
      toast(err instanceof ApiError ? err.message : "Delete failed.", "error");
    }
  }

  // --- New chat modal ----------------------------------------------------
  function openNewChatModal(): void {
    const nameInput = el("input", {
      class: "input",
      placeholder: "e.g. trip-planning",
      maxlength: 80,
    }) as HTMLInputElement;

    const errEl = el("div", { class: "modal__err" });

    const createBtn = el(
      "button",
      { class: "btn btn--primary", onClick: () => attemptCreate() },
      "Start chat",
    ) as HTMLButtonElement;

    const backdrop = el("div", { class: "modal-backdrop" });
    function close(): void {
      backdrop.remove();
    }
    backdrop.addEventListener("click", (e) => {
      if (e.target === backdrop) close();
    });

    async function attemptCreate(): Promise<void> {
      const name = nameInput.value.trim();
      errEl.textContent = "";

      if (!name) {
        errEl.textContent = "Give the chat a name.";
        return;
      }
      if (RESERVED_NAMES.includes(name.toLowerCase())) {
        errEl.textContent = `"${name}" is reserved — pick another name.`;
        return;
      }
      if (chats.some((c) => c.chat_id === name)) {
        errEl.textContent = "You already have a chat with that name.";
        return;
      }

      createBtn.disabled = true;
      createBtn.textContent = "Creating…";
      try {
        await createChat(name);
        chats = [{ chat_id: name }, ...chats];
        activeId = name;
        messages = [];
        pending = false;
        close();
        renderList();
        renderActiveMain();
      } catch (err) {
        errEl.textContent =
          err instanceof ApiError ? err.message : "Could not create chat.";
        createBtn.disabled = false;
        createBtn.textContent = "Start chat";
      }
    }

    nameInput.addEventListener("keydown", (e) => {
      if (e.key === "Enter") void attemptCreate();
    });

    const surprise = el(
      "button",
      {
        class: "btn btn--ghost",
        title: "Random name",
        onClick: () => {
          nameInput.value = randomChatName();
          errEl.textContent = "";
          nameInput.focus();
        },
      },
      "🎲 Surprise me",
    );

    const modal = el(
      "div",
      { class: "modal" },
      el("h3", {}, "Name your chat"),
      el(
        "p",
        {},
        "Each chat needs a unique name so you can find it again. Type one, or " +
          "let me roll a random name for you.",
      ),
      el("div", { class: "modal__name-row" }, nameInput, surprise),
      errEl,
      el(
        "div",
        { class: "modal__actions" },
        el("button", { class: "btn btn--ghost", onClick: () => close() }, "Cancel"),
        createBtn,
      ),
    );

    backdrop.appendChild(modal);
    document.body.appendChild(backdrop);
    nameInput.focus();
  }
}

function autoGrow(el: HTMLTextAreaElement): void {
  el.style.height = "auto";
  el.style.height = `${Math.min(el.scrollHeight, 200)}px`;
}
