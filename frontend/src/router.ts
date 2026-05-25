import { fetchProfile } from "./lib/api.ts";
import {
  clearSession,
  getCachedUser,
  isAuthenticated,
  setCachedUser,
} from "./lib/session.ts";
import { mount, el } from "./lib/dom.ts";
import type { User } from "./lib/types.ts";

import { renderPortfolio } from "./pages/portfolio.ts";
import { renderLogin } from "./pages/login.ts";
import { renderChat } from "./pages/chat.ts";
import { renderAdmin } from "./pages/admin.ts";

// ---------------------------------------------------------------------------
// Routes: "#/" portfolio (public) · "#/login" · "#/chat" (auth) · "#/admin"
// (auth + Admin). Hash routing means deep links work on any static host
// with zero server rewrite config.
// ---------------------------------------------------------------------------

function currentPath(): string {
  const raw = location.hash.replace(/^#/, "");
  const path = raw.split("?")[0] || "/";
  return path;
}

/** Resolve the logged-in user once, caching for the page lifetime. */
async function resolveUser(): Promise<User | null> {
  if (!isAuthenticated()) return null;
  const cached = getCachedUser();
  if (cached) return cached;
  try {
    const user = await fetchProfile();
    setCachedUser(user);
    return user;
  } catch {
    clearSession();
    return null;
  }
}

function appRoot(): HTMLElement {
  const root = document.getElementById("app");
  if (!root) throw new Error("#app root element is missing");
  return root;
}

function showLoading(): void {
  mount(appRoot(), el("div", { class: "route-loading" }, el("span", { class: "spinner" })));
}

let navToken = 0;

async function navigate(): Promise<void> {
  const token = ++navToken;
  const path = currentPath();
  const root = appRoot();
  window.scrollTo(0, 0);

  // Public routes ---------------------------------------------------------
  if (path === "/" || path === "") {
    document.body.dataset.route = "portfolio";
    renderPortfolio(root);
    return;
  }

  if (path === "/login") {
    document.body.dataset.route = "login";
    // Already signed in? Skip straight to the chat.
    if (isAuthenticated()) {
      const user = await resolveUser();
      if (token !== navToken) return;
      if (user) {
        location.hash = "#/chat";
        return;
      }
    }
    renderLogin(root);
    return;
  }

  // Guarded routes --------------------------------------------------------
  if (path === "/chat" || path === "/admin") {
    document.body.dataset.route = "app";
    showLoading();
    const user = await resolveUser();
    if (token !== navToken) return; // a newer navigation superseded this one

    if (!user) {
      location.hash = "#/login";
      return;
    }

    if (path === "/admin" && user.role !== "Admin") {
      location.hash = "#/chat";
      return;
    }

    if (path === "/chat") renderChat(root, user);
    else renderAdmin(root, user);
    return;
  }

  // Unknown -> portfolio
  location.hash = "#/";
}

export function startRouter(): void {
  window.addEventListener("hashchange", () => void navigate());
  void navigate();
}
