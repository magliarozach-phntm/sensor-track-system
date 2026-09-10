from datetime import datetime, timedelta, timezone

from app.services.time_utils import ensure_utc


STALE_THRESHOLD = timedelta(seconds=10)
DROP_THRESHOLD = timedelta(seconds=30)


def get_track_status(
    last_seen: datetime,
    now: datetime | None = None
) -> str:

    if now is None:
        now = datetime.now(timezone.utc)

    last_seen = ensure_utc(last_seen)
    now = ensure_utc(now)

    age = now - last_seen

    if age >= DROP_THRESHOLD:
        return "DROPPED"

    if age >= STALE_THRESHOLD:
        return "STALE"

    return "ACTIVE"