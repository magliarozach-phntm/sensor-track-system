from datetime import datetime, timezone


def ensure_utc(dt: datetime) -> datetime:
    """
    Ensure a datetime is timezone-aware and normalized to UTC.

    Naive datetimes are assumed to already represent UTC.
    """
    if dt.tzinfo is None:
        return dt.replace(tzinfo=timezone.utc)

    return dt.astimezone(timezone.utc)

def age_seconds(
    timestamp: datetime,
    now: datetime | None = None
) -> float:

    timestamp = ensure_utc(timestamp)

    if now is None:
        now = datetime.now(timezone.utc)

    now = ensure_utc(now)

    return (now - timestamp).total_seconds()