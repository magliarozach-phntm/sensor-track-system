import pytest

from app.services.track_quality import calculate_track_quality


def test_source_continuity_increases_quality():
    quality = calculate_track_quality(
        current_quality=0.50,
        association_method="SOURCE_CONTINUITY",
        association_score=None,
    )

    assert quality == pytest.approx(0.55)


def test_strong_correlation_increases_quality():
    quality = calculate_track_quality(
        current_quality=0.50,
        association_method="CORRELATION",
        association_score=0.30,
    )

    assert quality == pytest.approx(0.58)


def test_medium_correlation_increases_quality():
    quality = calculate_track_quality(
        current_quality=0.50,
        association_method="CORRELATION",
        association_score=0.75,
    )

    assert quality == pytest.approx(0.53)


def test_weak_correlation_decreases_quality():
    quality = calculate_track_quality(
        current_quality=0.50,
        association_method="CORRELATION",
        association_score=1.20,
    )

    assert quality == pytest.approx(0.45)


def test_quality_cannot_exceed_one():
    quality = calculate_track_quality(
        current_quality=0.98,
        association_method="SOURCE_CONTINUITY",
        association_score=None,
    )

    assert quality == 1.0


def test_quality_cannot_drop_below_zero():
    quality = calculate_track_quality(
        current_quality=0.02,
        association_method="CORRELATION",
        association_score=1.20,
    )

    assert quality == 0.0


def test_correlation_requires_score():
    with pytest.raises(ValueError):
        calculate_track_quality(
            current_quality=0.50,
            association_method="CORRELATION",
            association_score=None,
        )


def test_quality_above_one_is_invalid():
    with pytest.raises(ValueError):
        calculate_track_quality(
            current_quality=1.50,
            association_method="SOURCE_CONTINUITY",
            association_score=None,
        )


def test_quality_below_zero_is_invalid():
    with pytest.raises(ValueError):
        calculate_track_quality(
            current_quality=-0.20,
            association_method="SOURCE_CONTINUITY",
            association_score=None,
        )


def test_invalid_association_method():
    with pytest.raises(ValueError):
        calculate_track_quality(
            current_quality=0.50,
            association_method="INVALID",
            association_score=0.30,
        )
        
def test_track_quality_persists_and_increases(client):
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
    assert second_response.json()["quality"] == pytest.approx(0.55)

    track_response = client.get(
        f"/tracks/{system_track_id}"
    )

    assert track_response.status_code == 200
    assert track_response.json()["quality"] == pytest.approx(0.55)