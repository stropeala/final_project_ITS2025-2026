import { el } from "../lib/dom.ts";
import { clearSession } from "../lib/session.ts";
import type { User } from "../lib/types.ts";

function logout(): void {
  clearSession();
  location.hash = "#/login";
}

/**
 * The persistent top bar across chat/admin. `active` highlights the current
 * tab; the Admin link only renders for Admin accounts.
 */
export function appBar(
  user: User,
  active: "chat" | "admin",
  leading?: HTMLElement,
): HTMLElement {
  const nav = el("nav", { class: "app-nav" });

  nav.appendChild(
    el("a", { href: "#/chat", class: active === "chat" ? "active" : "" }, "Chat"),
  );
  if (user.role === "Admin") {
    nav.appendChild(
      el("a", { href: "#/admin", class: active === "admin" ? "active" : "" }, "Admin"),
    );
  }
  nav.appendChild(el("a", { href: "#/" }, "Portfolio"));

  const pill = el(
    "div",
    { class: "app-userpill" },
    el("span", {}, user.username),
    el("span", { class: `role-badge role-badge--${user.role}` }, user.role),
    el(
      "button",
      { class: "btn btn--ghost btn--mini", onClick: () => logout() },
      "Log out",
    ),
  );

  const left = el("div", { style: "display:flex;align-items:center;gap:12px" });
  if (leading) left.appendChild(leading);
  left.appendChild(
    el(
      "div",
      { class: "app-brand" },
      el("span", { class: "blip" }),
      "ITS",
      el("small", {}, "// private"),
    ),
  );

  return el(
    "header",
    { class: "app-bar" },
    left,
    el("div", { style: "display:flex;align-items:center;gap:14px" }, nav, pill),
  );
}
