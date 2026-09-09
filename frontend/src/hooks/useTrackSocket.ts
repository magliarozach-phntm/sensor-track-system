import { useEffect } from "react";

import type { TrackUpdate } from "../types/trackUpdate";


export function useTrackSocket(
  onTrackUpdate: (track: TrackUpdate) => void
) {

  useEffect(() => {

    const ws = new WebSocket(
      "ws://127.0.0.1:8000/ws/tracks"
    );


    ws.onmessage = (event) => {

      const data: TrackUpdate =
        JSON.parse(event.data);


      if (data.event === "track_updated") {
        onTrackUpdate(data);
      }

    };


    return () => {
      ws.close();
    };

  }, [onTrackUpdate]);

}