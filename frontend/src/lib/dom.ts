// ---------------------------------------------------------------------------
// Tiny DOM utilities. Just enough to build pages declaratively without a
// framework. el("div", { class: "x", onClick: fn }, child1, child2).
// ---------------------------------------------------------------------------

type Attrs = Record<
  string,
  string | number | boolean | EventListenerOrEventListenerObject | null | undefined
>;

type Child = Node | string | number | null | undefined | false;

export function el<K extends keyof HTMLElementTagNameMap>(
  tag: K,
  attrs: Attrs = {},
  ...children: Child[]
): HTMLElementTagNameMap[K] {
  const node = document.createElement(tag);

  for (const [key, value] of Object.entries(attrs)) {
    if (value === null || value === undefined || value === false) continue;

    if (key === "class") {
      node.className = String(value);
    } else if (key === "html") {
      node.innerHTML = String(value);
    } else if (key.startsWith("on") && typeof value === "function") {
      node.addEventListener(key.slice(2).toLowerCase(), value as EventListener);
    } else if (value === true) {
      node.setAttribute(key, "");
    } else {
      node.setAttribute(key, String(value));
    }
  }

  for (const child of children) append(node, child);
  return node;
}

function append(parent: Node, child: Child): void {
  if (child === null || child === undefined || child === false) return;
  if (child instanceof Node) {
    parent.appendChild(child);
  } else {
    parent.appendChild(document.createTextNode(String(child)));
  }
}

export function clear(node: Node): void {
  while (node.firstChild) node.removeChild(node.firstChild);
}

export function mount(root: HTMLElement, ...nodes: Child[]): void {
  clear(root);
  for (const n of nodes) append(root, n);
}

/** Transient corner notification. kind tints the accent border. */
export function toast(message: string, kind: "info" | "error" = "info"): void {
  let host = document.getElementById("toast-host");
  if (!host) {
    host = el("div", { id: "toast-host" });
    document.body.appendChild(host);
  }
  const item = el("div", { class: `toast toast--${kind}` }, message);
  host.appendChild(item);
  requestAnimationFrame(() => item.classList.add("toast--in"));
  window.setTimeout(() => {
    item.classList.remove("toast--in");
    window.setTimeout(() => item.remove(), 250);
  }, 3600);
}
