from datetime import datetime, timedelta, timezone


def test_recent_same_source_uses_source_continuity(client):
    start = datetime(
        2026, 9, 14, 12, 0, 0,
        tzinfo=timezone.utc,
    )

    first = {
        "sensor_id": "RADAR-01",
        "source_track_id": "RDR-100",
        "latitude": 34.0,
        "longitude": -81.0,
        "altitude": 10000,
        "heading": 90,
        "speed": 200,
        "timestamp": start.isoformat(),
    }

    first_response = client.post(
        "/observations",
        json=first,
    )

    assert first_response.status_code == 200

    system_track_id = first_response.json()["track_id"]

    second = {
        **first,
        "longitude": -80.999,
        "timestamp": (
            start + timedelta(seconds=10)
        ).isoformat(),
    }

    second_response = client.post(
        "/observations",
        json=second,
    )

    assert second_response.status_code == 200
    assert second_response.json()["track_id"] == system_track_id
    assert (
        second_response.json()["association_method"]
        == "SOURCE_CONTINUITY"
    )


def test_expired_source_continuity_creates_new_track(client):
    start = datetime(
        2026, 9, 14, 12, 0, 0,
        tzinfo=timezone.utc,
    )

    first = {
        "sensor_id": "RADAR-01",
        "source_track_id": "RDR-100",
        "latitude": 34.0,
        "longitude": -81.0,
        "altitude": 10000,
        "heading": 90,
        "speed": 200,
        "timestamp": start.isoformat(),
    }

    first_response = client.post(
        "/observations",
        json=first,
    )

    old_system_track_id = first_response.json()["track_id"]

    second = {
        **first,
        "latitude": 36.0,
        "longitude": -79.0,
        "timestamp": (
            start + timedelta(seconds=61)
        ).isoformat(),
    }

    second_response = client.post(
        "/observations",
        json=second,
    )

    assert second_response.status_code == 200

    new_system_track_id = second_response.json()["track_id"]

    assert new_system_track_id != old_system_track_id
    assert (
        second_response.json()["association_method"]
        == "NEW_TRACK"
    )


def test_expired_source_can_recover_by_correlation(client):
    start = datetime(
        2026, 9, 14, 12, 0, 0,
        tzinfo=timezone.utc,
    )

    # RADAR establishes the original system track.
    radar = {
        "sensor_id": "RADAR-01",
        "source_track_id": "RDR-100",
        "latitude": 34.0,
        "longitude": -81.0,
        "altitude": 10000,
        "heading": 90,
        "speed": 0,
        "timestamp": start.isoformat(),
    }

    radar_response = client.post(
        "/observations",
        json=radar,
    )

    assert radar_response.status_code == 200

    system_track_id = radar_response.json()["track_id"]

    # EO joins while the original track is still
    # inside the 20-second correlation window.
    eo_first = {
        "sensor_id": "EO-02",
        "source_track_id": "EO-200",
        "latitude": 34.0,
        "longitude": -81.0,
        "altitude": 10000,
        "heading": 90,
        "speed": 0,
        "timestamp": (
            start + timedelta(seconds=10)
        ).isoformat(),
    }

    eo_first_response = client.post(
        "/observations",
        json=eo_first,
    )

    assert eo_first_response.status_code == 200
    assert (
        eo_first_response.json()["track_id"]
        == system_track_id
    )
    assert (
        eo_first_response.json()["association_method"]
        == "CORRELATION"
    )

    # EO continues reporting and therefore keeps
    # the system track current.
    eo_refresh = {
        **eo_first,
        "timestamp": (
            start + timedelta(seconds=55)
        ).isoformat(),
    }

    eo_refresh_response = client.post(
        "/observations",
        json=eo_refresh,
    )

    assert eo_refresh_response.status_code == 200
    assert (
        eo_refresh_response.json()["track_id"]
        == system_track_id
    )
    assert (
        eo_refresh_response.json()["association_method"]
        == "SOURCE_CONTINUITY"
    )

    # RADAR returns after 65 seconds.
    #
    # Its own source continuity has expired:
    # 65 > 60 seconds.
    #
    # But the SYS track was refreshed by EO only
    # 10 seconds ago, so physical correlation can
    # recover RADAR onto the existing system track.
    radar_returns = {
        **radar,
        "timestamp": (
            start + timedelta(seconds=65)
        ).isoformat(),
    }

    return_response = client.post(
        "/observations",
        json=radar_returns,
    )

    assert return_response.status_code == 200
    assert (
        return_response.json()["track_id"]
        == system_track_id
    )
    assert (
        return_response.json()["association_method"]
        == "CORRELATION"
    )