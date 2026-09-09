import type { Track } from "../types/track";

const STALE_THRESHOLD_MS = 10_000;
const DROP_THRESHOLD_MS = 30_000;


export function getTrackStatus(
  lastSeen: string
): Track["status"] {

  const now = Date.now();
  const lastSeenTime = new Date(lastSeen).getTime();

  const age = now - lastSeenTime;

  if (age > DROP_THRESHOLD_MS) {
    return "DROPPED";
  }

  if (age > STALE_THRESHOLD_MS) {
    return "STALE";
  }

  return "ACTIVE";
}