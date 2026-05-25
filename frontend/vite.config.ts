import { defineConfig } from "vite";

// The frontend calls the SAME paths your FastAPI app serves: /auth/*, /chat/*,
// /admin/*. In dev, Vite forwards those three prefixes to the backend on
// :8000 untouched (no rewrite), so the URL in the browser's Network tab is
// byte-for-byte what your routers define.
//
// We proxy the specific router prefixes rather than everything, so Vite can
// still serve the app itself and its own dev assets (/src, /@vite, ...).
const BACKEND = "http://127.0.0.1:8000";

export default defineConfig({
  server: {
    proxy: {
      "/auth": { target: BACKEND, changeOrigin: true },
      "/chat": { target: BACKEND, changeOrigin: true },
      "/admin": { target: BACKEND, changeOrigin: true },
    },
  },
});
