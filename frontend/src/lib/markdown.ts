// ---------------------------------------------------------------------------
// A tiny, dependency-free Markdown -> HTML renderer for chat messages.
// It handles what an LLM typically emits: fenced + inline code, headings,
// bold/italic/strikethrough, links, ordered/unordered lists, blockquotes,
// and horizontal rules.
//
// SAFETY: every piece of model/user text is HTML-escaped before any tags are
// added, and link URLs are sanitised, so the output is safe to assign to
// innerHTML. If you ever want full CommonMark, swap this for `marked`.
// ---------------------------------------------------------------------------

function escapeHtml(text: string): string {
  return text
    .replace(/&/g, "&amp;")
    .replace(/</g, "&lt;")
    .replace(/>/g, "&gt;")
    .replace(/"/g, "&quot;")
    .replace(/'/g, "&#39;");
}

function sanitizeUrl(url: string): string | null {
  const trimmed = url.trim();
  if (/^(https?:|mailto:|#|\/)/i.test(trimmed)) return escapeHtml(trimmed);
  return null; // reject javascript:, data:, etc.
}

/** Inline formatting on a single (raw) string. */
function inline(raw: string): string {
  // Pull inline code out first so its contents aren't touched by other rules.
  const codes: string[] = [];
  let text = raw.replace(/`([^`]+)`/g, (_m, code: string) => {
    codes.push(`<code>${escapeHtml(code)}</code>`);
    return `\u0000${codes.length - 1}\u0000`;
  });

  text = escapeHtml(text);

  text = text.replace(
    /\[([^\]]+)\]\(([^)\s]+)\)/g,
    (_m, label: string, url: string) => {
      const href = sanitizeUrl(url);
      return href
        ? `<a href="${href}" target="_blank" rel="noreferrer">${label}</a>`
        : label;
    },
  );

  text = text
    .replace(/\*\*([^*]+)\*\*/g, "<strong>$1</strong>")
    .replace(/__([^_]+)__/g, "<strong>$1</strong>")
    .replace(/\*([^*\n]+)\*/g, "<em>$1</em>")
    .replace(/~~([^~]+)~~/g, "<del>$1</del>");

  // Restore the inline code spans.
  text = text.replace(/\u0000(\d+)\u0000/g, (_m, n: string) => codes[Number(n)]);
  return text;
}

const HR = /^\s*([-*_])(?:\s*\1){2,}\s*$/;
const UL = /^\s*[-*+]\s+(.*)$/;
const OL = /^\s*\d+\.\s+(.*)$/;

export function renderMarkdown(src: string): string {
  const lines = src.replace(/\r\n?/g, "\n").split("\n");
  const out: string[] = [];
  let i = 0;

  while (i < lines.length) {
    const line = lines[i];

    // Fenced code block
    const fence = line.match(/^```(\w*)\s*$/);
    if (fence) {
      const buf: string[] = [];
      i++;
      while (i < lines.length && !/^```\s*$/.test(lines[i])) {
        buf.push(lines[i]);
        i++;
      }
      i++; // consume closing ```
      out.push(`<pre><code>${escapeHtml(buf.join("\n"))}</code></pre>`);
      continue;
    }

    if (line.trim() === "") {
      i++;
      continue;
    }

    // Horizontal rule
    if (HR.test(line)) {
      out.push("<hr />");
      i++;
      continue;
    }

    // Heading
    const heading = line.match(/^(#{1,6})\s+(.*)$/);
    if (heading) {
      const level = heading[1].length;
      out.push(`<h${level}>${inline(heading[2])}</h${level}>`);
      i++;
      continue;
    }

    // Blockquote
    if (/^\s*>/.test(line)) {
      const buf: string[] = [];
      while (i < lines.length && /^\s*>/.test(lines[i])) {
        buf.push(lines[i].replace(/^\s*>\s?/, ""));
        i++;
      }
      out.push(`<blockquote>${inline(buf.join("\n")).replace(/\n/g, "<br />")}</blockquote>`);
      continue;
    }

    // Unordered list
    if (UL.test(line)) {
      const items: string[] = [];
      while (i < lines.length && UL.test(lines[i])) {
        items.push(`<li>${inline(lines[i].replace(UL, "$1"))}</li>`);
        i++;
      }
      out.push(`<ul>${items.join("")}</ul>`);
      continue;
    }

    // Ordered list
    if (OL.test(line)) {
      const items: string[] = [];
      while (i < lines.length && OL.test(lines[i])) {
        items.push(`<li>${inline(lines[i].replace(OL, "$1"))}</li>`);
        i++;
      }
      out.push(`<ol>${items.join("")}</ol>`);
      continue;
    }

    // Paragraph: gather until a blank line or the start of another block.
    const para: string[] = [];
    while (
      i < lines.length &&
      lines[i].trim() !== "" &&
      !/^```/.test(lines[i]) &&
      !HR.test(lines[i]) &&
      !/^(#{1,6})\s+/.test(lines[i]) &&
      !/^\s*>/.test(lines[i]) &&
      !UL.test(lines[i]) &&
      !OL.test(lines[i])
    ) {
      para.push(lines[i]);
      i++;
    }
    out.push(`<p>${inline(para.join("\n")).replace(/\n/g, "<br />")}</p>`);
  }

  return out.join("");
}
