import "./style.css";

const statusEl = document.querySelector<HTMLParagraphElement>("#status")!;
const messageEl = document.querySelector<HTMLParagraphElement>("#message")!;

async function fetchIndex() {
  try {
    const res = await fetch("/api/");
    if (!res.ok) throw new Error(`HTTP ${res.status}`);
    const data: { message: string } = await res.json();

    statusEl.textContent = "● connected";
    statusEl.className = "status ok";
    messageEl.textContent = `"${data.message}"`;
  } catch (err) {
    statusEl.textContent = "● disconnected";
    statusEl.className = "status err";
    messageEl.textContent = String(err);
  }
}

fetchIndex();
