import math
from datetime import timedelta

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.observation import Observation
from app.models.track import Track
from app.schemas.sensor import SensorObservation
from app.services.prediction import predict_position
from app.services.time_utils import ensure_utc

ASSOCIATION_WINDOW = timedelta(seconds=20)

MAX_ALTITUDE_DIFFERENCE = 2000
MAX_SPEED_DIFFERENCE = 100
MAX_HEADING_DIFFERENCE = 60

BASE_DISTANCE_GATE_M = 1000


def haversine_distance_m(
    lat1: float,
    lon1: float,
    lat2: float,
    lon2: float,
) -> float:
    earth_radius_m = 6_371_000

    lat1_rad = math.radians(lat1)
    lat2_rad = math.radians(lat2)

    delta_lat = math.radians(
        lat2 - lat1
    )

    delta_lon = math.radians(
        lon2 - lon1
    )

    a = (
        math.sin(delta_lat / 2) ** 2
        + math.cos(lat1_rad)
        * math.cos(lat2_rad)
        * math.sin(delta_lon / 2) ** 2
    )

    c = 2 * math.atan2(
        math.sqrt(a),
        math.sqrt(1 - a)
    )

    return earth_radius_m * c


def heading_difference(
    heading_a: float,
    heading_b: float,
) -> float:
    difference = abs(
        heading_a - heading_b
    ) % 360

    return min(
        difference,
        360 - difference
    )


def find_source_track(
    observation: SensorObservation,
    db: Session,
) -> Track | None:
    stmt = (
        select(Observation)
        .where(
            Observation.sensor_id
            == observation.sensor_id,
            Observation.source_track_id
            == observation.source_track_id,
        )
        .order_by(
            Observation.timestamp.desc(),
            Observation.id.desc(),
        )
        .limit(1)
    )

    previous_observation = db.scalar(
        stmt
    )

    if previous_observation is None:
        return None

    return db.scalar(
        select(Track)
        .where(
            Track.track_id
            == previous_observation.track_id
        )
    )


def find_correlated_track(
    observation: SensorObservation,
    db: Session,
) -> Track | None:

    # First preserve continuity from the
    # same sensor/source-track pair.
    source_track = find_source_track(
        observation,
        db
    )

    if source_track is not None:
        return source_track

    candidates = db.scalars(
        select(Track)
    ).all()

    best_track = None
    best_score = float("inf")

    observation_time = ensure_utc(
        observation.timestamp
    )

    for track in candidates:

        track_time = ensure_utc(
            track.last_seen
        )

        time_difference = (
            observation_time
            - track_time
        ).total_seconds()

        if time_difference < 0:
            continue
        
        if (
            time_difference
            > ASSOCIATION_WINDOW.total_seconds()
        ):
            continue
        
        predicted_latitude, predicted_longitude = (
            predict_position(
                latitude=track.latitude,
                longitude=track.longitude,
                heading=track.heading,
                speed=track.speed,
                seconds=time_difference,
            )
        )

        altitude_difference = abs(
            observation.altitude
            - track.altitude
        )

        if (
            altitude_difference
            > MAX_ALTITUDE_DIFFERENCE
        ):
            continue

        speed_difference = abs(
            observation.speed
            - track.speed
        )

        if (
            speed_difference
            > MAX_SPEED_DIFFERENCE
        ):
            continue

        heading_delta = heading_difference(
            observation.heading,
            track.heading
        )

        if (
            heading_delta
            > MAX_HEADING_DIFFERENCE
        ):
            continue

        distance = haversine_distance_m(
            observation.latitude,
            observation.longitude,
            predicted_latitude,
            predicted_longitude,
        )

        # Allow the distance gate to expand
        # based on target speed and time.
        max_speed_knots = max(
            observation.speed,
            track.speed
        )

        max_speed_mps = (
            max_speed_knots * 0.514444
        )

        expected_travel = (
            max_speed_mps
            * time_difference
        )

        distance_gate = (
            BASE_DISTANCE_GATE_M
            + expected_travel * 1.5
        )

        if distance > distance_gate:
            continue

        score = (
            distance / distance_gate
            + altitude_difference
            / MAX_ALTITUDE_DIFFERENCE
            + speed_difference
            / MAX_SPEED_DIFFERENCE
            + heading_delta
            / MAX_HEADING_DIFFERENCE
        )

        if score < best_score:
            best_score = score
            best_track = track

    return best_track