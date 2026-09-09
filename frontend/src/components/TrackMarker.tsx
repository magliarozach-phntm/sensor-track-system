import L from "leaflet";
import { Marker, Popup } from "react-leaflet";

import type { Track } from "../types/track";
import "./TrackMarker.css";


interface TrackMarkerProps {
  track: Track;
  onSelect: (track: Track) => void;
}


function TrackMarker({
  track,
  onSelect,
}: TrackMarkerProps) {

  const statusClass = track.status.toLowerCase();

  const icon = L.divIcon({
    className: "",
    html: `
      <div class="track-marker ${statusClass}">
        <div
          class="track-arrow"
          style="transform: rotate(${track.heading}deg)"
        ></div>

        <div class="track-label">
          ${track.track_id}
        </div>
      </div>
    `,
    iconSize: [90, 50],
    iconAnchor: [45, 20],
  });


  return (
    <Marker
      position={[
        track.latitude,
        track.longitude,
      ]}
      icon={icon}
      eventHandlers={{
        click: () => onSelect(track),
      }}
    >
      <Popup>
        <strong>{track.track_id}</strong>

        <br />
        Sensor: {track.sensor_id}

        <br />
        Status: {track.status}

        <br />
        Altitude: {track.altitude.toFixed(0)} ft

        <br />
        Speed: {track.speed.toFixed(1)} kt

        <br />
        Heading: {track.heading.toFixed(1)}°
      </Popup>
    </Marker>
  );
}


export default TrackMarker;