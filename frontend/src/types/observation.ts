export interface Observation {
  id: number;
  sensor_id: string;
  track_id: string;
  latitude: number;
  longitude: number;
  altitude: number;
  heading: number;
  speed: number;
  timestamp: string;
}