from datetime import datetime, timezone


def make_observation(
    track_id: str,
    sensor_id: str = "RADAR-TEST",
    altitude: float = 12000,
):
    return {
        "sensor_id": sensor_id,
        "track_id": track_id,
        "latitude": 34.9200,
        "longitude": -80.9300,
        "altitude": altitude,
        "heading": 90,
        "speed": 180,
        "timestamp": datetime.now(
            timezone.utc
        ).isoformat(),
    }


def test_get_all_tracks(client):
    client.post(
        "/observations",
        json=make_observation(
            "TRK-READ-001"
        )
    )

    client.post(
        "/observations",
        json=make_observation(
            "TRK-READ-002"
        )
    )

    response = client.get("/tracks")

    assert response.status_code == 200

    data = response.json()

    assert len(data) == 2

    track_ids = {
        track["track_id"]
        for track in data
    }

    assert "TRK-READ-001" in track_ids
    assert "TRK-READ-002" in track_ids


def test_get_specific_track(client):
    client.post(
        "/observations",
        json=make_observation(
            "TRK-READ-003"
        )
    )

    response = client.get(
        "/tracks/TRK-READ-003"
    )

    assert response.status_code == 200

    data = response.json()

    assert data["track_id"] == \
        "TRK-READ-003"

    assert data["sensor_id"] == \
        "RADAR-TEST"

    assert data["altitude"] == 12000


def test_missing_track_returns_404(
    client
):
    response = client.get(
        "/tracks/TRK-DOES-NOT-EXIST"
    )

    assert response.status_code == 404


def test_get_track_statuses(client):
    client.post(
        "/observations",
        json=make_observation(
            "TRK-STATUS-001"
        )
    )

    response = client.get(
        "/tracks/status"
    )

    assert response.status_code == 200

    data = response.json()

    assert len(data) == 1

    track = data[0]

    assert track["track_id"] == \
        "TRK-STATUS-001"

    assert track["status"] == "ACTIVE"

    assert "age" in track