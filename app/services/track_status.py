from datetime import datetime, timedelta, timezone

STALE_THRESHOLD = timedelta(seconds=10)
DROP_THRESHOLD = timedelta(seconds=30)


def get_track_status(last_seen: datetime) -> str:
    now = datetime.now(timezone.utc)

    age = now - last_seen

    if age > DROP_THRESHOLD:
        return "DROPPED"
    elif age > STALE_THRESHOLD:
        return "STALE"
    else:
        return "ACTIVE"