import { login } from "../lib/api.ts";
import { ApiError } from "../lib/api.ts";
import { setToken, setCachedUser } from "../lib/session.ts";
import { el, mount, toast } from "../lib/dom.ts";

export function renderLogin(root: HTMLElement): void {
  const username = el("input", {
    class: "input",
    type: "text",
    autocomplete: "username",
    placeholder: "username",
  }) as HTMLInputElement;

  const password = el("input", {
    class: "input",
    type: "password",
    autocomplete: "current-password",
    placeholder: "••••••••",
  }) as HTMLInputElement;

  const submit = el(
    "button",
    { class: "btn btn--primary btn--block", type: "button" },
    "Sign in",
  ) as HTMLButtonElement;

  let busy = false;

  async function doLogin(): Promise<void> {
    if (busy) return;
    const u = username.value.trim();
    const p = password.value;
    if (!u || !p) {
      toast("Enter your username and password.", "error");
      return;
    }

    busy = true;
    submit.disabled = true;
    submit.textContent = "Signing in…";

    try {
      const { access_token } = await login({ username: u, password: p });
      setToken(access_token);
      setCachedUser(null); // force a fresh profile fetch on the next route
      location.hash = "#/chat";
    } catch (err) {
      const msg =
        err instanceof ApiError ? err.message : "Could not reach the server.";
      toast(msg, "error");
      password.value = "";
      busy = false;
      submit.disabled = false;
      submit.textContent = "Sign in";
    }
  }

  const onEnter = (e: KeyboardEvent) => {
    if (e.key === "Enter") void doLogin();
  };
  username.addEventListener("keydown", onEnter);
  password.addEventListener("keydown", onEnter);
  submit.addEventListener("click", () => void doLogin());

  const card = el(
    "div",
    { class: "login-card" },
    el("div", { class: "login-badge" }, el("span", { class: "lock" }), "Private access"),
    el("h1", { class: "login-title" }, "Sign in"),
    el(
      "p",
      { class: "login-note" },
      "This chatbot is private. Accounts are created by the owner for family, " +
        "friends, and colleagues — there's no public sign-up. If you need " +
        "access, ask the owner to add you.",
    ),
    el(
      "div",
      { class: "login-form" },
      el("div", { class: "field" }, el("label", {}, "Username"), username),
      el("div", { class: "field" }, el("label", {}, "Password"), password),
      submit,
    ),
    el("a", { class: "login-back", href: "#/" }, "← Back to portfolio"),
  );

  mount(root, el("div", { class: "login-wrap" }, card));
  username.focus();
}
