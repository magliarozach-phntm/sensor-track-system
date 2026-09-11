from sqlalchemy import select

from app.models.source import TrackSource


def test_first_source_creates_track_source(client, db_session):
    payload = {
        "sensor_id": "RADAR-01",
        "source_track_id": "RDR-100",
        "latitude": 34.0,
        "longitude": -81.0,
        "altitude": 10000,
        "heading": 90,
        "speed": 200,
        "timestamp": "2026-09-11T16:00:00Z",
    }

    response = client.post(
        "/observations",
        json=payload,
    )

    assert response.status_code == 200

    system_track_id = response.json()["track_id"]

    stmt = select(TrackSource).where(
        TrackSource.track_id == system_track_id,
        TrackSource.sensor_id == "RADAR-01",
        TrackSource.source_track_id == "RDR-100",
    )

    source = db_session.scalar(stmt)

    assert source is not None
    assert source.observation_count == 1
    assert source.first_seen == source.last_seen


def test_same_source_increments_observation_count(
    client,
    db_session,
):
    first = {
        "sensor_id": "RADAR-01",
        "source_track_id": "RDR-100",
        "latitude": 34.0,
        "longitude": -81.0,
        "altitude": 10000,
        "heading": 90,
        "speed": 200,
        "timestamp": "2026-09-11T16:00:00Z",
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
        "timestamp": "2026-09-11T16:00:02Z",
    }

    second_response = client.post(
        "/observations",
        json=second,
    )

    assert second_response.status_code == 200
    assert second_response.json()["track_id"] == system_track_id

    stmt = select(TrackSource).where(
        TrackSource.track_id == system_track_id,
        TrackSource.sensor_id == "RADAR-01",
        TrackSource.source_track_id == "RDR-100",
    )

    sources = db_session.scalars(stmt).all()

    assert len(sources) == 1
    assert sources[0].observation_count == 2
    assert sources[0].last_seen > sources[0].first_seen


def test_second_sensor_creates_second_track_source(
    client,
    db_session,
):
    radar = {
        "sensor_id": "RADAR-01",
        "source_track_id": "RDR-100",
        "latitude": 34.0,
        "longitude": -81.0,
        "altitude": 10000,
        "heading": 90,
        "speed": 200,
        "timestamp": "2026-09-11T16:00:00Z",
    }

    radar_response = client.post(
        "/observations",
        json=radar,
    )

    assert radar_response.status_code == 200

    system_track_id = radar_response.json()["track_id"]

    eo = {
        "sensor_id": "EO-02",
        "source_track_id": "EO-200",
        "latitude": 34.0002,
        "longitude": -80.9997,
        "altitude": 10050,
        "heading": 92,
        "speed": 198,
        "timestamp": "2026-09-11T16:00:02Z",
    }

    eo_response = client.post(
        "/observations",
        json=eo,
    )

    assert eo_response.status_code == 200
    assert eo_response.json()["track_id"] == system_track_id

    stmt = (
        select(TrackSource)
        .where(
            TrackSource.track_id == system_track_id
        )
        .order_by(TrackSource.sensor_id)
    )

    sources = db_session.scalars(stmt).all()

    assert len(sources) == 2

    source_identities = {
        (
            source.sensor_id,
            source.source_track_id,
        )
        for source in sources
    }

    assert (
        "RADAR-01",
        "RDR-100",
    ) in source_identities

    assert (
        "EO-02",
        "EO-200",
    ) in source_identities