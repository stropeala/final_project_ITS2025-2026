import {
  ApiError,
  adminCreateUser,
  adminDeleteUser,
  adminDeleteUserChat,
  adminGetUserChat,
  adminListUserChats,
  adminListUsers,
} from "../lib/api.ts";
import { el, mount, clear, toast } from "../lib/dom.ts";
import type { AdminChatSummary, Role, User } from "../lib/types.ts";
import { appBar } from "./shell.ts";

export function renderAdmin(root: HTMLElement, me: User): void {
  let users: User[] = [];
  let selectedUserId: number | null = null;
  let chats: AdminChatSummary[] = [];

  const usersListEl = el("div", { class: "panel-body" });
  const rightColEl = el("div", { class: "admin-col" });

  // --- Create-user form --------------------------------------------------
  const uName = el("input", { class: "input", placeholder: "username" }) as HTMLInputElement;
  const uPass = el("input", {
    class: "input",
    type: "password",
    placeholder: "password",
  }) as HTMLInputElement;
  const uRole = el("select", { class: "input" }) as HTMLSelectElement;
  uRole.appendChild(el("option", { value: "User" }, "User"));
  uRole.appendChild(el("option", { value: "Admin" }, "Admin"));

  const createBtn = el(
    "button",
    { class: "btn btn--primary", onClick: () => void doCreate() },
    "Create",
  ) as HTMLButtonElement;

  const createForm = el(
    "div",
    { class: "create-user" },
    el("div", { class: "field" }, el("label", {}, "Username"), uName),
    el("div", { class: "field" }, el("label", {}, "Password"), uPass),
    el("div", { class: "field" }, el("label", {}, "Role"), uRole),
    createBtn,
  );

  // --- Left column: users ------------------------------------------------
  const leftCol = el(
    "div",
    { class: "admin-col" },
    el(
      "div",
      { class: "panel-head" },
      el("h2", {}, "Users"),
      el("p", {}, "Create accounts and manage who can access the chatbot."),
    ),
    createForm,
    usersListEl,
  );

  const layout = el("div", { class: "admin-layout" }, leftCol, rightColEl);
  mount(root, el("div", { class: "app" }, appBar(me, "admin"), layout));

  renderRightEmpty();
  void loadUsers();

  // --- Users -------------------------------------------------------------
  async function loadUsers(): Promise<void> {
    clear(usersListEl);
    usersListEl.appendChild(el("div", { class: "empty-hint" }, "Loading users…"));
    try {
      users = await adminListUsers();
    } catch (err) {
      users = [];
      toast(err instanceof ApiError ? err.message : "Couldn't load users.", "error");
    }
    renderUsers();
  }

  function renderUsers(): void {
    clear(usersListEl);
    if (users.length === 0) {
      usersListEl.appendChild(el("div", { class: "empty-hint" }, "No users yet."));
      return;
    }
    for (const u of users) {
      const isMe = u.id === me.id;
      const row = el(
        "div",
        {
          class: `user-row${u.id === selectedUserId ? " active" : ""}`,
          onClick: () => void selectUser(u.id),
        },
        el("span", { class: "user-row__id" }, `#${u.id}`),
        el("span", { class: "user-row__name" }, u.username + (isMe ? " (you)" : "")),
        el("span", { class: `role-badge role-badge--${u.role}` }, u.role),
        el(
          "button",
          {
            class: "btn btn--danger btn--mini",
            title: isMe ? "You can't delete your own account" : "Delete user",
            disabled: isMe,
            onClick: (e: Event) => {
              e.stopPropagation();
              void doDeleteUser(u);
            },
          },
          "Delete",
        ),
      );
      usersListEl.appendChild(row);
    }
  }

  async function doCreate(): Promise<void> {
    const username = uName.value.trim();
    const password = uPass.value;
    const role = uRole.value as Role;
    if (!username || !password) {
      toast("Username and password are required.", "error");
      return;
    }
    createBtn.disabled = true;
    createBtn.textContent = "Creating…";
    try {
      const created = await adminCreateUser({ username, password, role });
      users = [...users, created].sort((a, b) => a.id - b.id);
      uName.value = "";
      uPass.value = "";
      uRole.value = "User";
      renderUsers();
      toast(`Created ${created.username} (${created.role}).`, "info");
    } catch (err) {
      toast(err instanceof ApiError ? err.message : "Create failed.", "error");
    } finally {
      createBtn.disabled = false;
      createBtn.textContent = "Create";
    }
  }

  async function doDeleteUser(u: User): Promise<void> {
    if (!confirm(`Delete user "${u.username}" (#${u.id})? Their account will be removed.`)) {
      return;
    }
    try {
      await adminDeleteUser(u.id);
      users = users.filter((x) => x.id !== u.id);
      if (selectedUserId === u.id) {
        selectedUserId = null;
        chats = [];
        renderRightEmpty();
      }
      renderUsers();
      toast(`Deleted ${u.username}.`, "info");
    } catch (err) {
      toast(err instanceof ApiError ? err.message : "Delete failed.", "error");
    }
  }

  // --- Right column: a user's chats --------------------------------------
  function renderRightEmpty(): void {
    mount(
      rightColEl,
      el(
        "div",
        { class: "panel-head" },
        el("h2", {}, "Chats"),
        el("p", {}, "Select a user to inspect and moderate their conversations."),
      ),
      el("div", { class: "empty-hint" }, "No user selected."),
    );
  }

  async function selectUser(userId: number): Promise<void> {
    selectedUserId = userId;
    renderUsers();
    await loadUserChats();
  }

  async function loadUserChats(): Promise<void> {
    if (selectedUserId === null) return;
    try {
      chats = await adminListUserChats(selectedUserId);
    } catch (err) {
      chats = [];
      toast(err instanceof ApiError ? err.message : "Couldn't load chats.", "error");
    }
    renderRight();
  }

  function renderRight(): void {
    const target = users.find((u) => u.id === selectedUserId);
    const body = el("div", { class: "panel-body" });

    if (chats.length === 0) {
      body.appendChild(el("div", { class: "empty-hint" }, "This user has no chats."));
    } else {
      for (const c of chats) {
        body.appendChild(
          el(
            "div",
            { class: "admin-chat-row" },
            el("span", { class: "admin-chat-row__name" }, c.chat_id),
            el(
              "div",
              { class: "admin-chat-row__actions" },
              el(
                "button",
                { class: "btn btn--ghost btn--mini", onClick: () => void viewChat(c) },
                "View",
              ),
              el(
                "button",
                {
                  class: "btn btn--danger btn--mini",
                  onClick: () => void deleteOneChat(c),
                },
                "Delete",
              ),
            ),
          ),
        );
      }
    }

    mount(
      rightColEl,
      el(
        "div",
        { class: "panel-head" },
        el("h2", {}, target ? `${target.username}'s chats` : "Chats"),
        el(
          "p",
          {},
          target ? `User #${target.id} · ${chats.length} chat(s)` : "",
        ),
      ),
      body,
    );
  }

  async function viewChat(c: AdminChatSummary): Promise<void> {
    if (selectedUserId === null) return;
    try {
      const detail = await adminGetUserChat(selectedUserId, c.chat_id);
      renderRight();
      const viewer = el(
        "div",
        { class: "admin-msg-viewer" },
        el(
          "div",
          { class: "side-section-label", style: "padding:0 0 4px" },
          `Transcript · ${c.chat_id}`,
        ),
      );
      if (detail.messages.length === 0) {
        viewer.appendChild(el("div", { class: "empty-hint", style: "padding:0" }, "Empty chat."));
      }
      for (const m of detail.messages) {
        viewer.appendChild(
          el(
            "div",
            { class: `admin-msg admin-msg--${m.role}` },
            el("div", { class: "admin-msg__role" }, m.role),
            m.content,
          ),
        );
      }
      const panelBody = rightColEl.querySelector(".panel-body");
      panelBody?.appendChild(viewer);
      viewer.scrollIntoView({ behavior: "smooth", block: "nearest" });
    } catch (err) {
      toast(err instanceof ApiError ? err.message : "Couldn't open chat.", "error");
    }
  }

  async function deleteOneChat(c: AdminChatSummary): Promise<void> {
    if (selectedUserId === null) return;
    if (!confirm(`Delete chat "${c.chat_id}"?`)) return;
    try {
      await adminDeleteUserChat(selectedUserId, c.chat_id);
      chats = chats.filter((x) => x.chat_id !== c.chat_id);
      renderRight();
      toast(`Deleted "${c.chat_id}".`, "info");
    } catch (err) {
      toast(err instanceof ApiError ? err.message : "Delete failed.", "error");
    }
  }
}
