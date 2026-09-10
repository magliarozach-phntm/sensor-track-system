import type { Track } from "../types/track";
import type { Observation } from "../types/observation";

import { API_BASE_URL } from "../config";


export async function getTracks(): Promise<Track[]> {
  const response = await fetch(
    `${API_BASE_URL}/tracks/status`
  );

  if (!response.ok) {
    throw new Error(
      `Failed to fetch tracks: ${response.status}`
    );
  }

  return response.json();
}


export async function getTrackHistory(
  trackId: string,
  limit = 100
): Promise<Observation[]> {
  const response = await fetch(
    `${API_BASE_URL}/observations/${trackId}?limit=${limit}`
  );

  if (!response.ok) {
    throw new Error(
      `Failed to fetch track history: ${response.status}`
    );
  }

  return response.json();
}