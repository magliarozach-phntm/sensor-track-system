from datetime import datetime, timedelta, timezone

from app.services.track_status import get_track_status

NOW = datetime(
    2026,
    9,
    10,
    12,
    0,
    0,
    tzinfo=timezone.utc
)


def test_active_track():
    last_seen = NOW - timedelta(seconds=5)

    status = get_track_status(
        last_seen,
        now=NOW
    )

    assert status == "ACTIVE"


def test_track_becomes_stale():
    last_seen = NOW - timedelta(seconds=10)

    status = get_track_status(
        last_seen,
        now=NOW
    )

    assert status == "STALE"


def test_stale_track():
    last_seen = NOW - timedelta(seconds=20)

    status = get_track_status(
        last_seen,
        now=NOW
    )

    assert status == "STALE"


def test_track_becomes_dropped():
    last_seen = NOW - timedelta(seconds=30)

    status = get_track_status(
        last_seen,
        now=NOW
    )

    assert status == "DROPPED"


def test_dropped_track():
    last_seen = NOW - timedelta(seconds=60)

    status = get_track_status(
        last_seen,
        now=NOW
    )

    assert status == "DROPPED"