export const API_BASE_URL =
  import.meta.env.VITE_API_URL ??
  (import.meta.env.DEV ? "http://127.0.0.1:8000" : window.location.origin);

export const WS_BASE_URL =
  import.meta.env.VITE_WS_URL ??
  (import.meta.env.DEV
    ? "ws://127.0.0.1:8000"
    : `${window.location.protocol === "https:" ? "wss:" : "ws:"}//${window.location.host}`);
