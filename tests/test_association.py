from datetime import datetime, timedelta, timezone

from app.services.association import (
    haversine_distance_m,
    heading_difference,
)


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