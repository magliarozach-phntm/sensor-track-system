import { useEffect } from "react";

import type { TrackUpdate } from "../types/trackUpdate";

import { WS_BASE_URL } from "../config";

export function useTrackSocket(
  onTrackUpdate: (track: TrackUpdate) => void
) {

  useEffect(() => {

    const ws = new WebSocket(
      `${WS_BASE_URL}/ws/tracks`
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