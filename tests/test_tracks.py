from datetime import datetime, timezone


def make_observation(
    source_track_id: str,
    sensor_id: str = "RADAR-TEST",
    latitude: float = 34.9200,
    longitude: float = -80.9300,
    altitude: float = 12000,
    heading: float = 90,
    speed: float = 180,
):
    return {
        "sensor_id": sensor_id,
        "source_track_id": source_track_id,
        "latitude": latitude,
        "longitude": longitude,
        "altitude": altitude,
        "heading": heading,
        "speed": speed,
        "timestamp": datetime.now(
            timezone.utc
        ).isoformat(),
    }


def test_get_all_tracks(client):
    first_response = client.post(
        "/observations",
        json=make_observation(
            "TRK-READ-001",
            latitude=34.90,
            altitude=8000,
        )
    )

    second_response = client.post(
        "/observations",
        json=make_observation(
            "TRK-READ-002",
            latitude=35.10,
            altitude=16000,
        )
    )

    assert first_response.status_code == 200
    assert second_response.status_code == 200

    first_system_id = (
        first_response.json()["track_id"]
    )

    second_system_id = (
        second_response.json()["track_id"]
    )

    assert (
        first_system_id
        != second_system_id
    )

    response = client.get(
        "/tracks"
    )

    assert response.status_code == 200

    data = response.json()

    assert len(data) == 2

    track_ids = {
        track["track_id"]
        for track in data
    }

    assert first_system_id in track_ids
    assert second_system_id in track_ids


def test_get_specific_track(client):
    create_response = client.post(
        "/observations",
        json=make_observation(
            "TRK-READ-003"
        )
    )

    assert create_response.status_code == 200

    system_track_id = (
        create_response.json()["track_id"]
    )

    response = client.get(
        f"/tracks/{system_track_id}"
    )

    assert response.status_code == 200

    data = response.json()

    assert (
        data["track_id"]
        == system_track_id
    )

    assert (
        data["sensor_id"]
        == "RADAR-TEST"
    )

    assert data["altitude"] == 12000


def test_missing_track_returns_404(
    client
):
    response = client.get(
        "/tracks/SYS-DOES-NOT-EXIST"
    )

    assert response.status_code == 404

    assert (
        response.json()["detail"]
        == "Track: SYS-DOES-NOT-EXIST "
        "does not exist"
    )


def test_get_track_statuses(client):
    create_response = client.post(
        "/observations",
        json=make_observation(
            "TRK-STATUS-001"
        )
    )

    assert create_response.status_code == 200

    system_track_id = (
        create_response.json()["track_id"]
    )

    response = client.get(
        "/tracks/status"
    )

    assert response.status_code == 200

    data = response.json()

    assert len(data) == 1

    track = data[0]

    assert (
        track["track_id"]
        == system_track_id
    )

    assert track["status"] == "ACTIVE"
    assert "age" in track