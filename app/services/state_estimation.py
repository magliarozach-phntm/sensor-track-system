from dataclasses import dataclass


@dataclass
class EstimatedState:
    latitude: float
    longitude: float
    altitude: float
    heading: float
    speed: float
    
def estimate_track_state(
    previous_state: EstimatedState,
    measurement: EstimatedState,
    alpha: float = 0.65,
) -> EstimatedState:
    
    if not 0.0 <= alpha <= 1.0:
        raise ValueError(
            "Alpha must be between 0.0 and 1.0"
        )
    
    return EstimatedState(
        latitude=(
            alpha * measurement.latitude 
            + (1 - alpha) * previous_state.latitude
        ),
        longitude=(
            alpha * measurement.longitude
            + (1 - alpha) * previous_state.longitude
        ),
        altitude=(
            alpha * measurement.altitude
            + (1 - alpha) * previous_state.altitude
        ),
        heading=measurement.heading,
        speed=(
            alpha * measurement.speed
            + (1 - alpha) * previous_state.speed
        )
    )