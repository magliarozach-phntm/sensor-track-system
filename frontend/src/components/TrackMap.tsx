import {
  CircleMarker,
  MapContainer,
  Polyline,
  TileLayer,
} from "react-leaflet";

import TrackMarker from "./TrackMarker";
import MapController from "./MapController";

import type { Track } from "../types/track";
import type { Observation } from "../types/observation";


interface TrackMapProps {
  tracks: Track[];
  trackHistory: Observation[];
  selectedTrackId: string | null;
  resetViewTrigger: number;
  onTrackSelect: (track: Track) => void;
}


function TrackMap({
  tracks,
  trackHistory,
  selectedTrackId,
  resetViewTrigger,
  onTrackSelect,
}: TrackMapProps) {

  const selectedTrack =
    tracks.find(
      (track) =>
        track.track_id === selectedTrackId
    ) ?? null;


  const trailPositions: [number, number][] =
    trackHistory.map((observation) => [
      observation.latitude,
      observation.longitude,
    ]);


  // Connect trail to current live position.
  if (selectedTrack) {
    trailPositions.push([
      selectedTrack.latitude,
      selectedTrack.longitude,
    ]);
  }


  return (
    <MapContainer
      center={[34.92, -80.93]}
      zoom={12}
      className="track-map"
    >

      <MapController
        track={selectedTrack}
        tracks={tracks}
        resetViewTrigger={resetViewTrigger}
      />


      <TileLayer
        attribution="&copy; OpenStreetMap contributors"
        url="https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png"
      />


      {trailPositions.length > 1 && (
        <Polyline
          positions={trailPositions}
          pathOptions={{
            weight: 3,
            opacity: 0.8,
          }}
        />
      )}


      {trackHistory.map((observation) => (
        <CircleMarker
          key={observation.id}
          center={[
            observation.latitude,
            observation.longitude,
          ]}
          radius={2}
          pathOptions={{
            opacity: 0.6,
            fillOpacity: 0.6,
          }}
        />
      ))}


      {tracks.map((track) => (
        <TrackMarker
          key={track.track_id}
          track={track}
          onSelect={onTrackSelect}
        />
      ))}

    </MapContainer>
  );
}


export default TrackMap;