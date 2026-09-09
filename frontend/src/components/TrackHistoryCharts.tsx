import {
  LineChart,
  Line,
  XAxis,
  YAxis,
  Tooltip,
  ResponsiveContainer,
} from "recharts";

import type { Observation } from "../types/observation";


interface TrackHistoryChartsProps {
  history: Observation[];
}


function TrackHistoryCharts({
  history,
}: TrackHistoryChartsProps) {

  const chartData = history.map((observation) => ({
    time: new Date(
      observation.timestamp
    ).toLocaleTimeString(),

    altitude: observation.altitude,
    speed: observation.speed,
  }));


  if (history.length === 0) {
    return null;
  }


  return (
    <div className="history-charts">

      <div className="chart-section">

        <span className="section-title">
          ALTITUDE HISTORY
        </span>

        <div className="chart-container">
          <ResponsiveContainer
            width="100%"
            height="100%"
          >
            <LineChart data={chartData}>

              <XAxis
                dataKey="time"
                hide
              />

              <YAxis
                width={55}
                tick={{
                  fontSize: 10,
                }}
              />

              <Tooltip />

              <Line
                type="monotone"
                dataKey="altitude"
                dot={false}
                isAnimationActive={false}
              />

            </LineChart>
          </ResponsiveContainer>
        </div>

      </div>


      <div className="chart-section">

        <span className="section-title">
          SPEED HISTORY
        </span>

        <div className="chart-container">
          <ResponsiveContainer
            width="100%"
            height="100%"
          >
            <LineChart data={chartData}>

              <XAxis
                dataKey="time"
                hide
              />

              <YAxis
                width={55}
                tick={{
                  fontSize: 10,
                }}
              />

              <Tooltip />

              <Line
                type="monotone"
                dataKey="speed"
                dot={false}
                isAnimationActive={false}
              />

            </LineChart>
          </ResponsiveContainer>
        </div>

      </div>

    </div>
  );
}


export default TrackHistoryCharts;