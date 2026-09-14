import pytest

from app.services.state_estimation import (
    EstimatedState,
    estimate_track_state,
)


def test_alpha_one_returns_measurement():
    previous = EstimatedState(
        latitude=34.0,
        longitude=-81.0,
        altitude=10000,
        heading=90,
        speed=200,
    )

    measurement = EstimatedState(
        latitude=35.0,
        longitude=-80.0,
        altitude=11000,
        heading=120,
        speed=250,
    )

    result = estimate_track_state(
        previous_state=previous,
        measurement=measurement,
        alpha=1.0,
    )

    assert result.latitude == pytest.approx(35.0)
    assert result.longitude == pytest.approx(-80.0)
    assert result.altitude == pytest.approx(11000)
    assert result.speed == pytest.approx(250)
    assert result.heading == 120


def test_alpha_zero_keeps_previous_state():
    previous = EstimatedState(
        latitude=34.0,
        longitude=-81.0,
        altitude=10000,
        heading=90,
        speed=200,
    )

    measurement = EstimatedState(
        latitude=35.0,
        longitude=-80.0,
        altitude=11000,
        heading=120,
        speed=250,
    )

    result = estimate_track_state(
        previous_state=previous,
        measurement=measurement,
        alpha=0.0,
    )

    assert result.latitude == pytest.approx(34.0)
    assert result.longitude == pytest.approx(-81.0)
    assert result.altitude == pytest.approx(10000)
    assert result.speed == pytest.approx(200)

    # Heading currently always trusts newest measurement.
    assert result.heading == 120


def test_default_alpha_blends_state():
    previous = EstimatedState(
        latitude=34.0,
        longitude=-81.0,
        altitude=10000,
        heading=90,
        speed=200,
    )

    measurement = EstimatedState(
        latitude=35.0,
        longitude=-80.0,
        altitude=10100,
        heading=95,
        speed=220,
    )

    result = estimate_track_state(
        previous_state=previous,
        measurement=measurement,
    )

    assert result.latitude == pytest.approx(34.65)
    assert result.longitude == pytest.approx(-80.35)
    assert result.altitude == pytest.approx(10065)
    assert result.speed == pytest.approx(213)
    assert result.heading == 95


def test_alpha_below_zero_is_invalid():
    previous = EstimatedState(
        latitude=34.0,
        longitude=-81.0,
        altitude=10000,
        heading=90,
        speed=200,
    )

    measurement = previous

    with pytest.raises(ValueError):
        estimate_track_state(
            previous_state=previous,
            measurement=measurement,
            alpha=-0.1,
        )


def test_alpha_above_one_is_invalid():
    previous = EstimatedState(
        latitude=34.0,
        longitude=-81.0,
        altitude=10000,
        heading=90,
        speed=200,
    )

    measurement = previous

    with pytest.raises(ValueError):
        estimate_track_state(
            previous_state=previous,
            measurement=measurement,
            alpha=1.1,
        )