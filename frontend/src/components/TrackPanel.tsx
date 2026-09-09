import type { Observation } from "../types/observation";
import type { Track } from "../types/track";

import TrackHistoryCharts from "./TrackHistoryCharts";


interface TrackPanelProps {
  track: Track | null;
  history: Observation[];
}


function TrackPanel({
  track,
  history,
}: TrackPanelProps) {

  if (!track) {
    return (
      <aside className="track-panel empty-panel">

        <div className="panel-header">
          TRACK DETAILS
        </div>

        <div className="empty-message">
          <h2>NO TRACK SELECTED</h2>

          <p>
            Select a track symbol on the map
            to inspect its current state.
          </p>
        </div>

      </aside>
    );
  }


  const statusClass =
    track.status.toLowerCase();


  return (
    <aside className="track-panel">

      <div className="panel-header">
        TRACK DETAILS
      </div>


      <div className="track-title">

        <div>
          <span className="small-label">
            TRACK ID
          </span>

          <h2>{track.track_id}</h2>
        </div>


        <span
          className={`status-badge ${statusClass}`}
        >
          {track.status}
        </span>

      </div>


      <div className="data-section">

        <span className="section-title">
          SOURCE
        </span>

        <div className="data-row">
          <span>Sensor</span>
          <strong>{track.sensor_id}</strong>
        </div>

      </div>


      <div className="data-section">

        <span className="section-title">
          POSITION
        </span>

        <div className="data-row">
          <span>Latitude</span>

          <strong>
            {track.latitude.toFixed(5)}
          </strong>
        </div>

        <div className="data-row">
          <span>Longitude</span>

          <strong>
            {track.longitude.toFixed(5)}
          </strong>
        </div>

        <div className="data-row">
          <span>Altitude</span>

          <strong>
            {track.altitude.toFixed(0)} ft
          </strong>
        </div>

      </div>


      <div className="data-section">

        <span className="section-title">
          KINEMATICS
        </span>

        <div className="data-row">
          <span>Speed</span>

          <strong>
            {track.speed.toFixed(1)} kt
          </strong>
        </div>

        <div className="data-row">
          <span>Heading</span>

          <strong>
            {track.heading.toFixed(1)}°
          </strong>
        </div>

      </div>


      <div className="data-section">

        <span className="section-title">
          TIMING
        </span>

        <div className="data-row">
          <span>Last Seen</span>

          <strong>
            {new Date(
              track.last_seen
            ).toLocaleTimeString()}
          </strong>
        </div>

      </div>


      <TrackHistoryCharts
        history={history}
      />

    </aside>
  );
}


export default TrackPanel;