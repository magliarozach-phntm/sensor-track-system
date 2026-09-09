import {
  useCallback,
  useEffect,
  useState,
} from "react";

import "./App.css";

import TrackControls from "./components/TrackControls";
import TrackMap from "./components/TrackMap";
import TrackPanel from "./components/TrackPanel";
import TrackSearch from "./components/TrackSearch";
import type { TrackUpdate } from "./types/trackUpdate";

import { useTrackSocket } from "./hooks/useTrackSocket";

import {
  getTracks,
  getTrackHistory,
} from "./services/api";

import { getTrackStatus } from "./services/trackStatus";

import type { Track } from "./types/track";
import type { Observation } from "./types/observation";

import type {
  StatusFilter,
} from "./components/TrackControls";


function App() {
  const [tracks, setTracks] =
    useState<Track[]>([]);

  const [resetViewTrigger, setResetViewTrigger] =
  useState(0);

  const [trackHistory, setTrackHistory] =
    useState<Observation[]>([]);

  const [selectedTrackId, setSelectedTrackId] =
    useState<string | null>(null);

  const [trailLimit, setTrailLimit] =
    useState(100);

  const [statusFilter, setStatusFilter] =
    useState<StatusFilter>("ALL");

  const [sensorFilter, setSensorFilter] =
    useState("ALL");

  const [error, setError] =
    useState<string | null>(null);

  const [, setClock] =
    useState(0);


  // Recalculate ACTIVE / STALE / DROPPED
  // based on current time.
  const liveTracks = tracks.map((track) => ({
    ...track,
    status: getTrackStatus(track.last_seen),
  }));


  // Build sensor filter options dynamically.
  const sensors = [
    ...new Set(
      liveTracks.map(
        (track) => track.sensor_id
      )
    ),
  ].sort();


  // Apply status + sensor filters to map.
  const filteredTracks = liveTracks.filter(
    (track) => {

      const statusMatches =
        statusFilter === "ALL" ||
        track.status === statusFilter;

      const sensorMatches =
        sensorFilter === "ALL" ||
        track.sensor_id === sensorFilter;

      return (
        statusMatches &&
        sensorMatches
      );
    }
  );


  // Load existing tracks when frontend starts.
  useEffect(() => {

    async function loadTracks() {
      try {
        const data = await getTracks();

        setTracks(data);
      }

      catch (err) {
        if (err instanceof Error) {
          setError(err.message);
        }
      }
    }

    loadTracks();

  }, []);


  // Re-render once per second so track status
  // can age from ACTIVE -> STALE -> DROPPED.
  useEffect(() => {

    const interval = setInterval(() => {

      setClock(
        (clock) => clock + 1
      );

    }, 1000);


    return () => {
      clearInterval(interval);
    };

  }, []);


  // Load history whenever selected track
  // OR trail length changes.
  useEffect(() => {

    if (!selectedTrackId) {
      setTrackHistory([]);
      return;
    }


    async function loadTrackHistory() {

      try {
        const history =
          await getTrackHistory(
            selectedTrackId!,
            trailLimit
          );

        setTrackHistory(history);
      }

      catch (err) {
        if (err instanceof Error) {
          console.error(err.message);
        }
      }
    }


    loadTrackHistory();

  }, [
    selectedTrackId,
    trailLimit,
  ]);


  // Handle live WebSocket updates.
  const handleTrackUpdate = useCallback(
    (updatedTrack: TrackUpdate) => {

      setTracks((currentTracks) => {

        const exists =
          currentTracks.some(
            (track) =>
              track.track_id ===
              updatedTrack.track_id
          );


        if (exists) {
          return currentTracks.map(
            (track) =>
              track.track_id ===
              updatedTrack.track_id
                ? updatedTrack
                : track
          );
        }

        if (
          updatedTrack.track_id === selectedTrackId
        ) {

          const liveObservation: Observation = {
            id: updatedTrack.observation_id,
            sensor_id: updatedTrack.sensor_id,
            track_id: updatedTrack.track_id,
            latitude: updatedTrack.latitude,
            longitude: updatedTrack.longitude,
            altitude: updatedTrack.altitude,
            heading: updatedTrack.heading,
            speed: updatedTrack.speed,
            timestamp: updatedTrack.last_seen,
          };


          setTrackHistory((currentHistory) => {

            const updatedHistory = [
              ...currentHistory,
              liveObservation,
            ];


            return updatedHistory.slice(
              -trailLimit
            );
          });

        }


        return [
          ...currentTracks,
          updatedTrack,
        ];
      });

    },
    []
  );


  useTrackSocket(handleTrackUpdate);

function handleSearchTrackSelect(track: Track) {

  // Clear status filter only if it hides this track.
  if (
    statusFilter !== "ALL" &&
    statusFilter !== track.status
  ) {
    setStatusFilter("ALL");
  }


  // Clear sensor filter only if it hides this track.
  if (
    sensorFilter !== "ALL" &&
    sensorFilter !== track.sensor_id
  ) {
    setSensorFilter("ALL");
  }


  setSelectedTrackId(track.track_id);
}

  // Keep selected track using newest live data.
  const selectedTrack =
    liveTracks.find(
      (track) =>
        track.track_id === selectedTrackId
    ) ?? null;


  // Global counts should NOT be affected
  // by map filters.
  const activeCount =
    liveTracks.filter(
      (track) =>
        track.status === "ACTIVE"
    ).length;

  const staleCount =
    liveTracks.filter(
      (track) =>
        track.status === "STALE"
    ).length;

  const droppedCount =
    liveTracks.filter(
      (track) =>
        track.status === "DROPPED"
    ).length;


  return (
    <div className="app-shell">

      <header className="topbar">

        <div className="brand">

          <h1>
            SENSOR TRACK SYSTEM
          </h1>

          <span>
            LIVE TRACKING CONSOLE
          </span>

        </div>


        <div className="status-summary">

          <div className="status-count active">
            <span>ACTIVE</span>
            <strong>{activeCount}</strong>
          </div>


          <div className="status-count stale">
            <span>STALE</span>
            <strong>{staleCount}</strong>
          </div>


          <div className="status-count dropped">
            <span>DROPPED</span>
            <strong>{droppedCount}</strong>
          </div>


          <div className="status-count total">
            <span>TOTAL</span>
            <strong>{liveTracks.length}</strong>
          </div>

        </div>

      </header>


      {error && (
        <div className="error-banner">
          {error}
        </div>
      )}

      <div className="map-actions">

        <TrackSearch
          tracks={liveTracks}
          onTrackSelect={handleSearchTrackSelect}
        />

        <button
          className="reset-view-button"
          onClick={() =>
            setResetViewTrigger(
              (current) => current + 1
            )
          }
        >
          RESET VIEW
        </button>

      </div>

      <TrackControls
        trailLimit={trailLimit}
        onTrailLimitChange={setTrailLimit}

        statusFilter={statusFilter}
        onStatusFilterChange={setStatusFilter}

        sensorFilter={sensorFilter}
        onSensorFilterChange={setSensorFilter}

        sensors={sensors}
      />


      <div className="dashboard-grid">

        <section className="map-card">

          <TrackMap
            tracks={filteredTracks}
            trackHistory={trackHistory}
            selectedTrackId={selectedTrackId}
            resetViewTrigger={resetViewTrigger}
            onTrackSelect={(track) =>
              setSelectedTrackId(track.track_id)
            }
          />

        </section>


        <TrackPanel
  track={selectedTrack}
  history={trackHistory}
/>

      </div>

    </div>
  );
}


export default App;