export interface Track {
    track_id: string;
    sensor_id: string;
    quality: number;
    latitude: number;
    longitude: number;
    altitude: number;
    heading: number;
    speed: number;
    status: "ACTIVE" | "STALE" | "DROPPED";
    last_seen: string;
    age?: number;
}