from datetime import datetime, timedelta, timezone

from sqlalchemy import select

from app.models.observation import Observation
from app.models.track import Track


def test_create_observation(
    client,
    db_session
):
    payload = {
        "sensor_id": "RADAR-TEST",
        "source_track_id": "TRK-TEST-001",
        "latitude": 34.9200,
        "longitude": -80.9300,
        "altitude": 12000,
        "heading": 90,
        "speed": 180,
        "timestamp": "2026-09-10T12:00:00Z",
    }

    response = client.post(
        "/observations",
        json=payload
    )

    assert response.status_code == 200

    data = response.json()

    assert (
        data["source_track_id"]
        == "TRK-TEST-001"
    )

    assert data["track_id"].startswith(
        "SYS-"
    )

    system_track_id = data["track_id"]

    observation = db_session.scalar(
        select(Observation)
        .where(
            Observation.source_track_id
            == "TRK-TEST-001"
        )
    )

    assert observation is not None
    assert (
        observation.track_id
        == system_track_id
    )
    assert (
        observation.sensor_id
        == "RADAR-TEST"
    )

    track = db_session.scalar(
        select(Track)
        .where(
            Track.track_id
            == system_track_id
        )
    )

    assert track is not None
    assert track.speed == 180
    assert track.heading == 90


def test_reject_invalid_observation(
    client
):
    payload = {
        "sensor_id": "RADAR-TEST",
        "source_track_id": "TRK-TEST-002",
        "latitude": 120,
        "longitude": -80.9300,
        "altitude": 12000,
        "heading": 400,
        "speed": -50,
        "timestamp": "2026-09-10T12:00:00Z",
    }

    response = client.post(
        "/observations",
        json=payload
    )

    assert response.status_code == 422


def test_second_observation_updates_track(
    client,
    db_session
):
    first = {
        "sensor_id": "RADAR-TEST",
        "source_track_id": "TRK-TEST-003",
        "latitude": 34.9200,
        "longitude": -80.9300,
        "altitude": 12000,
        "heading": 90,
        "speed": 180,
        "timestamp": "2026-09-10T12:00:00Z",
    }

    second = {
        "sensor_id": "RADAR-TEST",
        "source_track_id": "TRK-TEST-003",
        "latitude": 34.9300,
        "longitude": -80.9400,
        "altitude": 12500,
        "heading": 110,
        "speed": 200,
        "timestamp": "2026-09-10T12:00:02Z",
    }

    first_response = client.post(
        "/observations",
        json=first
    )

    assert first_response.status_code == 200

    system_track_id = (
        first_response.json()["track_id"]
    )

    second_response = client.post(
        "/observations",
        json=second
    )

    assert second_response.status_code == 200

    assert (
        second_response.json()["track_id"]
        == system_track_id
    )
    
    assert (
        second_response.json()["association_method"]
        == "SOURCE_CONTINUITY"
    )

    assert (
        second_response.json()["association_score"]
        is None
    )

    track = db_session.scalar(
        select(Track)
        .where(
            Track.track_id
            == system_track_id
        )
    )

    assert track is not None
    assert track.latitude == 34.9300
    assert track.longitude == -80.9400
    assert track.altitude == 12500
    assert track.heading == 110
    assert track.speed == 200

    observations = db_session.scalars(
        select(Observation)
        .where(
            Observation.track_id
            == system_track_id
        )
    ).all()

    assert len(observations) == 2


def test_get_track_observation_history(
    client,
    db_session
):
    base_time = datetime.now(
        timezone.utc
    )

    first = {
        "sensor_id": "RADAR-TEST",
        "source_track_id": "TRK-HISTORY-001",
        "latitude": 34.9200,
        "longitude": -80.9300,
        "altitude": 10000,
        "heading": 90,
        "speed": 180,
        "timestamp": base_time.isoformat(),
    }

    second = {
        "sensor_id": "RADAR-TEST",
        "source_track_id": "TRK-HISTORY-001",
        "latitude": 34.9300,
        "longitude": -80.9400,
        "altitude": 11000,
        "heading": 95,
        "speed": 190,
        "timestamp": (
            base_time
            + timedelta(seconds=2)
        ).isoformat(),
    }

    first_response = client.post(
        "/observations",
        json=first
    )

    assert first_response.status_code == 200

    system_track_id = (
        first_response.json()["track_id"]
    )

    second_response = client.post(
        "/observations",
        json=second
    )

    assert second_response.status_code == 200

    assert (
        second_response.json()["track_id"]
        == system_track_id
    )

    print(
        "\nFIRST:",
        first_response.json()
    )

    print(
        "SECOND:",
        second_response.json()
    )

    stored_observations = db_session.scalars(
        select(Observation)
        .where(
            Observation.track_id
            == system_track_id
        )
        .order_by(Observation.timestamp)
    ).all()

    print(
        "STORED:",
        [
            (
                obs.id,
                obs.source_track_id,
                obs.track_id,
                obs.altitude,
            )
            for obs in stored_observations
        ]
    )

    assert len(stored_observations) == 2

    response = client.get(
        f"/observations/{system_track_id}"
    )

    print(
        "GET RESPONSE:",
        response.json()
    )

    assert response.status_code == 200

    data = response.json()

    assert len(data) == 2
    assert data[0]["altitude"] == 10000
    assert data[1]["altitude"] == 11000


def test_observation_history_limit(
    client
):
    base_time = datetime.now(
        timezone.utc
    )

    system_track_id = None

    for i in range(5):
        payload = {
            "sensor_id": "RADAR-TEST",
            "source_track_id": "TRK-LIMIT-001",
            "latitude": 34.92 + (
                i * 0.001
            ),
            "longitude": -80.93,
            "altitude": 10000 + (
                i * 100
            ),
            "heading": 90,
            "speed": 180,
            "timestamp": (
                base_time
                + timedelta(seconds=i)
            ).isoformat(),
        }

        response = client.post(
            "/observations",
            json=payload
        )

        assert response.status_code == 200

        current_system_id = (
            response.json()["track_id"]
        )

        if system_track_id is None:
            system_track_id = (
                current_system_id
            )
        else:
            assert (
                current_system_id
                == system_track_id
            )

    response = client.get(
        f"/observations/"
        f"{system_track_id}?limit=3"
    )

    assert response.status_code == 200

    data = response.json()

    assert len(data) == 3
    assert data[0]["altitude"] == 10200
    assert data[1]["altitude"] == 10300
    assert data[2]["altitude"] == 10400


def test_missing_observation_history_returns_404(
    client
):
    response = client.get(
        "/observations/SYS-NOT-REAL"
    )

    assert response.status_code == 404

    assert (
        response.json()["detail"]
        == "No observations found for "
        "track_id: SYS-NOT-REAL"
    )
    

    