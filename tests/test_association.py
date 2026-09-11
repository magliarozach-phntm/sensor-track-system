from datetime import datetime, timedelta, timezone

import pytest

from app.models.track import Track
from app.schemas.sensor import SensorObservation
from app.services.association import (
    association_confidence,
    find_correlated_track,
    haversine_distance_m,
    heading_difference,
)
from app.services.prediction import predict_position


@pytest.mark.parametrize(
    "score, expected",
    [
        (0.0, "HIGH CONFIDENCE"),
        (0.5, "HIGH CONFIDENCE"),
        (0.51, "MEDIUM CONFIDENCE"),
        (0.99, "MEDIUM CONFIDENCE"),
        (1.0, "LOW CONFIDENCE"),
        (2.0, "LOW CONFIDENCE"),
    ]
)
def test_association_confidence(
    score,
    expected
):
    result = association_confidence(
        score
    )

    assert result == expected

def test_prediction_selects_correct_moving_track(
    db_session
):
    now = datetime.now(timezone.utc)

    track_time = (
        now - timedelta(seconds=10)
    )

    # Candidate A:
    # moving east at 200 knots.
    # We will place the new observation exactly
    # where this track should be after 10 seconds.
    track_a_lat = 34.92
    track_a_lon = -80.93

    predicted_lat, predicted_lon = (
        predict_position(
            latitude=track_a_lat,
            longitude=track_a_lon,
            heading=90,
            speed=200,
            seconds=10,
        )
    )

    track_a = Track(
        track_id="SYS-CORRECT",
        sensor_id="RADAR-01",
        latitude=track_a_lat,
        longitude=track_a_lon,
        altitude=12000,
        heading=90,
        speed=200,
        last_seen=track_time,
        classification="UNKNOWN",
    )

    # Candidate B:
    # its OLD position is closer to the incoming
    # observation, but if projected forward using
    # its motion, it should move past it.
    track_b = Track(
        track_id="SYS-WRONG",
        sensor_id="RADAR-02",
        latitude=predicted_lat,
        longitude=predicted_lon - 0.002,
        altitude=12000,
        heading=90,
        speed=200,
        last_seen=track_time,
        classification="UNKNOWN",
    )

    db_session.add_all([
        track_a,
        track_b,
    ])

    db_session.commit()

    observation = SensorObservation(
        sensor_id="EO-99",
        source_track_id="EO-NEW-001",
        latitude=predicted_lat,
        longitude=predicted_lon,
        altitude=12000,
        heading=90,
        speed=200,
        timestamp=now,
    )

    matched_track = find_correlated_track(
        observation,
        db_session,
    )

    assert matched_track is not None

    assert (
        matched_track.track.track_id
        == "SYS-CORRECT"
    )
    assert matched_track.method == "CORRELATION"
    assert matched_track.score is not None
    assert matched_track.distance_m is not None

def test_heading_difference_wraparound():
    difference = heading_difference(
        359,
        1
    )

    assert difference == 2


def test_heading_difference_normal():
    difference = heading_difference(
        90,
        120
    )

    assert difference == 30


def test_haversine_same_position():
    distance = haversine_distance_m(
        34.92,
        -80.93,
        34.92,
        -80.93,
    )

    assert distance == 0
    
def test_two_sensors_correlate_to_same_system_track(
    client
):
    base_time = datetime.now(
        timezone.utc
    )

    radar = {
        "sensor_id": "RADAR-01",
        "source_track_id": "RDR-441",
        "latitude": 34.9200,
        "longitude": -80.9300,
        "altitude": 12000,
        "heading": 90,
        "speed": 180,
        "timestamp": base_time.isoformat(),
    }

    eo = {
        "sensor_id": "EO-02",
        "source_track_id": "EO-827",
        "latitude": 34.9205,
        "longitude": -80.9295,
        "altitude": 12100,
        "heading": 92,
        "speed": 182,
        "timestamp": (
            base_time
            + timedelta(seconds=2)
        ).isoformat(),
    }

    radar_response = client.post(
        "/observations",
        json=radar
    )

    eo_response = client.post(
        "/observations",
        json=eo
    )

    assert radar_response.status_code == 200
    assert eo_response.status_code == 200

    assert (
        radar_response.json()["track_id"]
        == eo_response.json()["track_id"]
    )

    assert (
        eo_response.json()["association_method"]
        == "CORRELATION"
    )

    assert (
        eo_response.json()["association_confidence"]
        == "HIGH CONFIDENCE"
    )

    assert (
        eo_response.json()["association_score"]
        is not None
    )
    
def test_distant_observations_create_separate_tracks(
    client
):
    now = datetime.now(
        timezone.utc
    )

    first = {
        "sensor_id": "RADAR-01",
        "source_track_id": "RDR-A",
        "latitude": 34.90,
        "longitude": -80.90,
        "altitude": 8000,
        "heading": 90,
        "speed": 180,
        "timestamp": now.isoformat(),
    }

    second = {
        "sensor_id": "EO-02",
        "source_track_id": "EO-B",
        "latitude": 35.20,
        "longitude": -81.20,
        "altitude": 16000,
        "heading": 270,
        "speed": 300,
        "timestamp": now.isoformat(),
    }

    first_response = client.post(
        "/observations",
        json=first
    )

    second_response = client.post(
        "/observations",
        json=second
    )

    assert (
        first_response.json()["track_id"]
        != second_response.json()["track_id"]
    )
    
def test_old_track_is_not_correlated(
    client
):
    now = datetime.now(
        timezone.utc
    )

    old_observation = {
        "sensor_id": "RADAR-01",
        "source_track_id": "RDR-OLD",
        "latitude": 34.9200,
        "longitude": -80.9300,
        "altitude": 12000,
        "heading": 90,
        "speed": 180,
        "timestamp": (
            now
            - timedelta(seconds=60)
        ).isoformat(),
    }

    new_observation = {
        "sensor_id": "EO-02",
        "source_track_id": "EO-NEW",
        "latitude": 34.9201,
        "longitude": -80.9301,
        "altitude": 12050,
        "heading": 91,
        "speed": 181,
        "timestamp": now.isoformat(),
    }

    old_response = client.post(
        "/observations",
        json=old_observation
    )

    new_response = client.post(
        "/observations",
        json=new_observation
    )

    assert (
        old_response.json()["track_id"]
        != new_response.json()["track_id"]
    )
    
def test_ambiguous_candidates_choose_best_overall_match(
    db_session
):
    now = datetime.now(timezone.utc)

    # Candidate A is spatially perfect,
    # but its kinematics are a poor match.
    candidate_a = Track(
        track_id="SYS-CLOSE-BUT-WRONG",
        sensor_id="RADAR-01",
        latitude=34.9200,
        longitude=-80.9300,
        altitude=13500,
        heading=140,
        speed=260,
        last_seen=now,
        classification="UNKNOWN",
    )

    # Candidate B is slightly farther away,
    # but altitude, heading, and speed
    # match the incoming observation closely.
    candidate_b = Track(
        track_id="SYS-BEST-MATCH",
        sensor_id="RADAR-02",
        latitude=34.9208,
        longitude=-80.9308,
        altitude=12100,
        heading=92,
        speed=185,
        last_seen=now,
        classification="UNKNOWN",
    )

    db_session.add_all([
        candidate_a,
        candidate_b,
    ])

    db_session.commit()

    observation = SensorObservation(
        sensor_id="EO-99",
        source_track_id="EO-AMBIGUOUS-001",
        latitude=34.9200,
        longitude=-80.9300,
        altitude=12000,
        heading=90,
        speed=180,
        timestamp=now,
    )

    result = find_correlated_track(
        observation,
        db_session,
    )

    assert result is not None

    assert (
        result.track.track_id
        == "SYS-BEST-MATCH"
    )

    assert result.method == "CORRELATION"

    assert result.score is not None

    assert result.confidence == \
        "HIGH CONFIDENCE"