


type StatusFilter =
  | "ALL"
  | "ACTIVE"
  | "STALE"
  | "DROPPED";


interface TrackControlsProps {
  trailLimit: number;
  onTrailLimitChange: (limit: number) => void;

  statusFilter: StatusFilter;
  onStatusFilterChange: (status: StatusFilter) => void;

  sensorFilter: string;
  onSensorFilterChange: (sensor: string) => void;

  sensors: string[];
}


function TrackControls({
  trailLimit,
  onTrailLimitChange,

  statusFilter,
  onStatusFilterChange,

  sensorFilter,
  onSensorFilterChange,

  sensors,
}: TrackControlsProps) {

  const statuses: StatusFilter[] = [
    "ALL",
    "ACTIVE",
    "STALE",
    "DROPPED",
  ];


  return (
    <div className="track-controls">

      <div className="control-group">

        <span className="control-label">
          STATUS
        </span>

        {statuses.map((status) => (
          <button
            key={status}
            className={
              statusFilter === status
                ? "control-button active"
                : "control-button"
            }
            onClick={() =>
              onStatusFilterChange(status)
            }
          >
            {status}
          </button>
        ))}

      </div>


      <div className="control-divider" />


      <div className="control-group">

        <span className="control-label">
          SENSOR
        </span>

        <select
          className="sensor-select"
          value={sensorFilter}
          onChange={(event) =>
            onSensorFilterChange(
              event.target.value
            )
          }
        >
          <option value="ALL">
            ALL
          </option>

          {sensors.map((sensor) => (
            <option
              key={sensor}
              value={sensor}
            >
              {sensor}
            </option>
          ))}

        </select>

      </div>


      <div className="control-divider" />


      <div className="control-group">

        <span className="control-label">
          TRAIL
        </span>

        {[50, 100, 250].map((limit) => (
          <button
            key={limit}
            className={
              trailLimit === limit
                ? "control-button active"
                : "control-button"
            }
            onClick={() =>
              onTrailLimitChange(limit)
            }
          >
            {limit}
          </button>
        ))}

      </div>

    </div>
  );
}


export default TrackControls;

export type { StatusFilter };