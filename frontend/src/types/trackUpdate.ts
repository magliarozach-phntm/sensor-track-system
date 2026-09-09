import type { Track } from "./track";


export interface TrackUpdate extends Track {
  observation_id: number;
  event: "track_updated";
}