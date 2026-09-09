import {
  useState,
} from "react";

import type { Track } from "../types/track";


interface TrackSearchProps {
  tracks: Track[];
  onTrackSelect: (track: Track) => void;
}


function TrackSearch({
  tracks,
  onTrackSelect,
}: TrackSearchProps) {

  const [query, setQuery] =
    useState("");

  const [message, setMessage] =
    useState("");


  function searchTrack() {

    const normalizedQuery =
      query.trim().toUpperCase();


    if (!normalizedQuery) {
      return;
    }


    const track = tracks.find(
      (track) =>
        track.track_id.toUpperCase() ===
        normalizedQuery
    );


    if (!track) {

      setMessage(
        `Track ${normalizedQuery} not found`
      );

      return;
    }


    setMessage("");

    onTrackSelect(track);
  }


  return (
    <div className="track-search">

      <input
        type="text"
        value={query}
        placeholder="TRK-1001"

        onChange={(event) =>
          setQuery(event.target.value)
        }

        onKeyDown={(event) => {
          if (event.key === "Enter") {
            searchTrack();
          }
        }}
      />


      <button
        onClick={searchTrack}
      >
        FIND TRACK
      </button>


      {message && (
        <span className="search-message">
          {message}
        </span>
      )}

    </div>
  );
}


export default TrackSearch;