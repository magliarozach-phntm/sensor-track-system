from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.source import TrackSource

def record_track_source(
    db: Session,
    track_id: str,
    sensor_id: str,
    source_track_id: str,
    timestamp,
) -> TrackSource:
    
    stmt = select(TrackSource).where(
        TrackSource.track_id == track_id,
        TrackSource.sensor_id == sensor_id,
        TrackSource.source_track_id == source_track_id,
    )

    source = db.scalar(stmt)
    
    if source is not None:
        source.last_seen = timestamp
        source.observation_count += 1

    else:
        source = TrackSource(
            track_id=track_id,
            sensor_id=sensor_id,
            source_track_id=source_track_id,
            first_seen=timestamp,
            last_seen=timestamp,
            observation_count=1,
        )

        db.add(source)
        
    return source