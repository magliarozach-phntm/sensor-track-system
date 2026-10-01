import { useEffect, useState } from "react";
import { API_BASE_URL } from "../config";

type DemoStatus = {
  running: boolean;
  ends_at: string | null;
  next_allowed_at: string | null;
  runs_remaining: number;
  error: string | null;
  server_time: string;
};

export default function DemoControl() {
  const [status, setStatus] = useState<DemoStatus | null>(null);
  const [pending, setPending] = useState(false);
  const [error, setError] = useState("");
  const [clock, setClock] = useState(Date.now());
  const [offset, setOffset] = useState(0);

  function accept(next: DemoStatus) {
    setStatus(next);
    setOffset(Date.parse(next.server_time) - Date.now());
  }

  async function refresh() {
    try {
      const response = await fetch(`${API_BASE_URL}/demo`);
      if (!response.ok) throw new Error("Demo status is unavailable. Try again shortly.");
      accept(await response.json());
    } catch (e) {
      setError(e instanceof Error ? e.message : "Demo unavailable.");
    }
  }

  useEffect(() => { void refresh(); }, []);
  useEffect(() => {
    const timer = window.setInterval(() => setClock(Date.now()), 1000);
    return () => window.clearInterval(timer);
  }, []);
  useEffect(() => {
    if (!status?.running) return;
    const timer = window.setInterval(() => { void refresh(); }, 5000);
    return () => window.clearInterval(timer);
  }, [status?.running]);

  async function start() {
    setPending(true);
    setError("");
    try {
      const response = await fetch(`${API_BASE_URL}/demo`, { method: "POST" });
      const data = await response.json();
      if (response.status === 429) {
        accept(data.detail);
      } else if (!response.ok) {
        throw new Error(typeof data.detail === "string" ? data.detail : "Demo could not start.");
      } else {
        accept(data);
      }
    } catch (e) {
      setError(e instanceof Error ? e.message : "Demo could not start.");
    } finally {
      setPending(false);
    }
  }

  const now = clock + offset;
  const remaining = Math.max(0, Math.ceil(((status?.ends_at ? Date.parse(status.ends_at) : now) - now) / 1000));
  const cooldown = Math.max(0, Math.ceil(((status?.next_allowed_at ? Date.parse(status.next_allowed_at) : now) - now) / 1000));
  const running = Boolean(status?.running && remaining > 0);

  return <section className="demo-controls" aria-label="Interactive demo">
    <button onClick={start} disabled={pending || running || cooldown > 0}>
      {pending ? "Starting demo…" : running ? `Demo running · ${remaining}s` : "Run 60-second demo"}
    </button>
    <span role="status" aria-live="polite">
      {error || status?.error || (running
        ? "Watch three simulated tracks move on the map."
        : cooldown > 0
          ? `Next demo available in ${Math.floor(cooldown / 60)}m ${cooldown % 60}s.`
          : "Start a shared live demo. It stops automatically after one minute.")}
    </span>
    <small>Shared demo · 5-minute cooldown · up to 12 runs per day</small>
  </section>;
}
