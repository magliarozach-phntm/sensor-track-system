import {
  useEffect,
  useRef,
} from "react";

import { useMap } from "react-leaflet";
import L from "leaflet";

import type { Track } from "../types/track";


interface MapControllerProps {
  track: Track | null;
  tracks: Track[];
  resetViewTrigger: number;
}


function MapController({
  track,
  tracks,
  resetViewTrigger,
}: MapControllerProps) {

  const map = useMap();

  /*
    Always keep the newest track list available,
    without making the RESET effect rerun
    every time a track moves.
  */
  const tracksRef = useRef<Track[]>(tracks);


  useEffect(() => {
    tracksRef.current = tracks;
  }, [tracks]);


  // Focus a newly selected track.
  useEffect(() => {

    if (!track) {
      return;
    }


    map.flyTo(
      [
        track.latitude,
        track.longitude,
      ],
      15,
      {
        duration: 0.8,
      }
    );

  }, [
    track?.track_id,
    map,
  ]);


  // RESET VIEW only runs when button is clicked.
  useEffect(() => {

    if (resetViewTrigger === 0) {
      return;
    }


    const currentTracks =
      tracksRef.current;


    if (currentTracks.length === 0) {
      return;
    }


    if (currentTracks.length === 1) {

      map.flyTo(
        [
          currentTracks[0].latitude,
          currentTracks[0].longitude,
        ],
        13
      );

      return;
    }


    const bounds = L.latLngBounds(
      currentTracks.map((track) => [
        track.latitude,
        track.longitude,
      ])
    );


    map.fitBounds(
      bounds,
      {
        padding: [50, 50],
      }
    );

  }, [
    resetViewTrigger,
    map,
  ]);


  return null;
}


export default MapController;