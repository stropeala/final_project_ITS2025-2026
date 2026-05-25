import { el, mount } from "../lib/dom.ts";

// ===========================================================================
//  EDIT ME — everything you'd want to change for your own portfolio lives in
//  this one block. The rest of the file just lays it out.
// ===========================================================================

const PROFILE = {
  name: "Your Name",
  monogram: "YN",
  role: "Backend & Full-Stack Developer",
  location: "Bucharest, Romania",
  available: true, // toggles the green "available for work" pill
  // The big hero line. Wrap a word in *asterisks* to render it in rust italic.
  headline: "I build *dependable* backends and the interfaces that sit on top.",
  lead:
    "I'm a developer focused on clean, well-documented APIs and pragmatic " +
    "full-stack work. I care about correctness, security, and code that the " +
    "next person can actually read.",
  email: "you@example.com",
  github: "https://github.com/your-username",
  linkedin: "https://www.linkedin.com/in/your-username",
};

interface Project {
  featured?: boolean;
  tag: string;
  title: string;
  description: string;
  tags: string[];
  github?: string;
  liveLabel?: string;
  liveHref?: string;
  // featured-only: lines for the spec aside, "label: value"
  spec?: [string, string][];
}

const PROJECTS: Project[] = [
  {
    featured: true,
    tag: "Featured · 2026",
    title: "Project ITS — Private AI Chatbot",
    description:
      "A self-hosted, invite-only chatbot platform. A FastAPI backend issues " +
      "JWT sessions, enforces role-based access (Admin / User), and proxies a " +
      "local Ollama model. User accounts live in PostgreSQL; conversations are " +
      "persisted per-user in SQLite. Admins get a full moderation surface over " +
      "every account and chat. This very site is the frontend.",
    tags: [
      "FastAPI",
      "JWT + bcrypt",
      "PostgreSQL",
      "SQLite",
      "Ollama",
      "RBAC",
      "TypeScript",
      "Vite",
    ],
    github: "https://github.com/your-username/project-its",
    liveLabel: "Try the private chat",
    liveHref: "#/login",
    spec: [
      ["auth", "JWT (HS256) + bcrypt"],
      ["roles", "Admin · User"],
      ["users", "PostgreSQL / SQLAlchemy"],
      ["chats", "SQLite, JSON history"],
      ["model", "Ollama (gemma3:4b)"],
      ["client", "Vanilla TS + Vite"],
    ],
  },
  // Add more projects here as you build them — they'll render as cards below.
];

const STACK: { group: string; items: string[] }[] = [
  { group: "Backend", items: ["Python", "FastAPI", "SQLAlchemy", "Pydantic", "REST"] },
  { group: "Frontend", items: ["TypeScript", "Vite", "HTML/CSS", "DOM APIs"] },
  { group: "Data", items: ["PostgreSQL", "SQLite", "JWT", "bcrypt"] },
  { group: "Tooling", items: ["Git", "Docker", "Ollama", "Linux"] },
];

const ABOUT: string[] = [
  "I gravitate toward the parts of a system most people would rather not " +
    "touch — auth, data modelling, the boring-but-load-bearing middle. " +
    "Project ITS started as a way to give friends and family a private LLM " +
    "without handing their conversations to a third party.",
  "Outside of shipping features I spend time reading other people's code, " +
    "tightening documentation, and trying to make the next deploy less " +
    "exciting than the last one.",
];

// ===========================================================================
//  Layout
// ===========================================================================

/** Render a headline string, turning *word* into rust italic emphasis. */
function emphasized(text: string): (Node | string)[] {
  return text.split(/(\*[^*]+\*)/).map((part) =>
    part.startsWith("*") && part.endsWith("*")
      ? el("em", {}, part.slice(1, -1))
      : part,
  );
}

function scrollTo(id: string): (e: Event) => void {
  return (e: Event) => {
    e.preventDefault();
    document.getElementById(id)?.scrollIntoView({ behavior: "smooth", block: "start" });
  };
}

function navLink(label: string, targetId: string): HTMLElement {
  return el("a", { href: `#${targetId}`, onClick: scrollTo(targetId) }, label);
}

function arrow(): HTMLElement {
  return el("span", { class: "arrow", "aria-hidden": "true" }, "→");
}

function renderProjectCard(p: Project): HTMLElement {
  const links = el("div", { class: "pf-project__links" });
  if (p.liveHref) {
    links.appendChild(
      el("a", { class: "pf-link", href: p.liveHref }, p.liveLabel ?? "Visit", arrow()),
    );
  }
  if (p.github) {
    links.appendChild(
      el(
        "a",
        { class: "pf-link", href: p.github, target: "_blank", rel: "noreferrer" },
        "Source on GitHub",
        arrow(),
      ),
    );
  }

  const main = el(
    "div",
    { class: "pf-project__main" },
    el("span", { class: "pf-project__tag" }, p.tag),
    el("h3", {}, p.title),
    el("p", {}, p.description),
    el(
      "div",
      { class: "pf-tags" },
      ...p.tags.map((t) => el("span", {}, t)),
    ),
    links,
  );

  const cardClass = p.featured
    ? "pf-project pf-project--featured reveal"
    : "pf-project reveal";

  if (p.featured && p.spec) {
    const aside = el(
      "div",
      { class: "pf-project__aside" },
      el(
        "div",
        { class: "pf-arch" },
        ...p.spec.flatMap(([k, v], i) => [
          i > 0 ? el("br") : "",
          `${k.padEnd(7, " ")} `,
          el("b", {}, v),
        ]),
      ),
    );
    return el("article", { class: cardClass }, main, aside);
  }

  return el("article", { class: cardClass }, main);
}

export function renderPortfolio(root: HTMLElement): void {
  const year = new Date().getFullYear();

  // --- Nav ---
  const nav = el(
    "header",
    { class: "pf-nav" },
    el(
      "div",
      { class: "pf-nav__inner" },
      el(
        "a",
        { class: "pf-monogram", href: "#/", onClick: scrollTo("top") },
        el("span", { class: "dot" }),
        PROFILE.monogram,
      ),
      el(
        "nav",
        { class: "pf-nav__links" },
        navLink("Work", "work"),
        navLink("About", "about"),
        navLink("Stack", "stack"),
        navLink("Contact", "contact"),
        el("a", { class: "pf-cta", href: "#/login" }, "Private chat →"),
      ),
    ),
  );

  // --- Hero ---
  const hero = el(
    "section",
    { class: "pf-hero", id: "top" },
    el(
      "div",
      { class: "pf__inner" },
      el("div", { class: "pf-eyebrow reveal", style: "--i:0" }, `${PROFILE.role} · ${PROFILE.location}`),
      el("h1", { class: "reveal", style: "--i:1" }, ...emphasized(PROFILE.headline)),
      el("p", { class: "pf-hero__lead reveal", style: "--i:2" }, PROFILE.lead),
      el(
        "div",
        { class: "pf-hero__actions reveal", style: "--i:3" },
        el("a", { class: "pf-btn pf-btn--primary", href: "#work", onClick: scrollTo("work") }, "View work", arrow()),
        el("a", { class: "pf-btn pf-btn--ghost", href: "#/login" }, "Private chatbot login"),
      ),
      PROFILE.available
        ? el(
            "div",
            { class: "pf-availability reveal", style: "--i:4" },
            el("span", { class: "pulse" }),
            "Open to new opportunities",
          )
        : "",
    ),
  );

  // --- Work ---
  const work = el(
    "section",
    { class: "pf-section", id: "work" },
    el(
      "div",
      { class: "pf__inner" },
      el(
        "div",
        { class: "pf-section__head reveal" },
        el("span", { class: "pf-section__num" }, "01"),
        el("h2", { class: "pf-section__title" }, "Selected work"),
      ),
      el(
        "div",
        { class: "pf-projects" },
        ...PROJECTS.map(renderProjectCard),
        el(
          "div",
          { class: "pf-soon reveal" },
          "More projects landing here soon — this list grows as I ship.",
        ),
      ),
    ),
  );

  // --- About ---
  const about = el(
    "section",
    { class: "pf-section", id: "about" },
    el(
      "div",
      { class: "pf__inner" },
      el(
        "div",
        { class: "pf-section__head reveal" },
        el("span", { class: "pf-section__num" }, "02"),
        el("h2", { class: "pf-section__title" }, "About"),
      ),
      el(
        "div",
        { class: "pf-about reveal" },
        el("div", { class: "pf-about__body" }, ...ABOUT.map((para) => el("p", {}, para))),
        el(
          "div",
          { class: "pf-about__side" },
          el("div", { class: "pf-stack" }, el("h4", {}, "Currently"), el("p", {}, "Building & maintaining Project ITS.")),
        ),
      ),
    ),
  );

  // --- Stack ---
  const stack = el(
    "section",
    { class: "pf-section", id: "stack" },
    el(
      "div",
      { class: "pf__inner" },
      el(
        "div",
        { class: "pf-section__head reveal" },
        el("span", { class: "pf-section__num" }, "03"),
        el("h2", { class: "pf-section__title" }, "Stack & tools"),
      ),
      el(
        "div",
        { class: "pf-about reveal" },
        el(
          "div",
          {},
          ...STACK.map((s) =>
            el(
              "div",
              { class: "pf-stack" },
              el("h4", {}, s.group),
              el("ul", {}, ...s.items.map((i) => el("li", {}, i))),
            ),
          ),
        ),
      ),
    ),
  );

  // --- Contact ---
  const contact = el(
    "section",
    { class: "pf-section", id: "contact" },
    el(
      "div",
      { class: "pf__inner pf-contact reveal" },
      el(
        "div",
        { class: "pf-section__head", style: "justify-content:center" },
        el("span", { class: "pf-section__num" }, "04"),
        el("h2", { class: "pf-section__title" }, "Contact"),
      ),
      el("h2", {}, ...emphasized("Let's build something *worth* maintaining.")),
      el(
        "div",
        { class: "pf-contact__links" },
        el("a", { class: "pf-btn pf-btn--primary", href: `mailto:${PROFILE.email}` }, "Email me", arrow()),
        el("a", { class: "pf-btn pf-btn--ghost", href: PROFILE.github, target: "_blank", rel: "noreferrer" }, "GitHub"),
        el("a", { class: "pf-btn pf-btn--ghost", href: PROFILE.linkedin, target: "_blank", rel: "noreferrer" }, "LinkedIn"),
      ),
    ),
  );

  const footer = el(
    "footer",
    { class: "pf-section", style: "border-bottom:none;padding-bottom:0" },
    el(
      "div",
      { class: "pf__inner pf-footer" },
      el("span", {}, `© ${year} ${PROFILE.name}`),
      el("span", {}, "Built with vanilla TypeScript + Vite"),
    ),
  );

  const page = el("div", { class: "pf" }, nav, hero, work, about, stack, contact, footer);
  mount(root, page);

  setupReveals();
}

/** Fade sections in as they scroll into view. */
function setupReveals(): void {
  const items = Array.from(document.querySelectorAll<HTMLElement>(".reveal"));
  if (!("IntersectionObserver" in window)) {
    items.forEach((n) => n.classList.add("in"));
    return;
  }

  // Hero items animate in immediately on load.
  document.querySelectorAll<HTMLElement>(".pf-hero .reveal").forEach((n) => {
    requestAnimationFrame(() => n.classList.add("in"));
  });

  const observer = new IntersectionObserver(
    (entries) => {
      for (const entry of entries) {
        if (entry.isIntersecting) {
          entry.target.classList.add("in");
          observer.unobserve(entry.target);
        }
      }
    },
    { threshold: 0.12 },
  );

  items
    .filter((n) => !n.closest(".pf-hero"))
    .forEach((n) => observer.observe(n));
}
