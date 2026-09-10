from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.database.database import get_db
from app.models.track import Track
from app.services.time_utils import age_seconds, ensure_utc
from app.services.track_status import get_track_status

router = APIRouter(
    prefix="/tracks",
    tags=["tracks"],
)
@router.get('')
def get_all_tracks(db: Session = Depends(get_db)):
    stmt = select(Track).order_by(Track.last_seen.desc())
    tracks = db.scalars(stmt).all()

    return tracks

@router.get('/search')
def search_tracks(
    sensor_id: str | None = None,
    min_altitude: float | None = None,
    max_altitude: float | None = None,
    min_speed: float | None = None,
    max_speed: float | None = None,
    db: Session = Depends(get_db)
):
    
    if (
        min_altitude is not None
        and max_altitude is not None
        and min_altitude > max_altitude
    ):
        raise HTTPException(
            status_code=400,
            detail="min_altitude cannot be greater than max_altitude"
        )
        
    if (
        min_speed is not None
        and max_speed is not None
        and min_speed > max_speed
    ):
        raise HTTPException(
            status_code=400,
            detail="min_speed cannot be greater than max_speed"
        )
    
    
    
    stmt = select(Track)
    
    # filters
    
    if sensor_id is not None:
        stmt = stmt.where(Track.sensor_id == sensor_id)
    if min_altitude is not None:
        stmt = stmt.where(Track.altitude >= min_altitude)
    if max_altitude is not None:
        stmt = stmt.where(Track.altitude <= max_altitude)
    if min_speed is not None:
        stmt = stmt.where(Track.speed >= min_speed)
    if max_speed is not None:
        stmt = stmt.where(Track.speed <= max_speed)
    
    stmt = stmt.order_by(Track.last_seen.desc())
    
    tracks = db.scalars(stmt).all()
    
    return tracks

@router.get("/status")
def get_all_track_statuses(
    db: Session = Depends(get_db)
):
    stmt = (
        select(Track)
        .order_by(Track.last_seen.desc())
    )

    tracks = db.scalars(stmt).all()

    results = []

    for track in tracks:
        
        last_seen = ensure_utc(track.last_seen)
            
        status = get_track_status(last_seen)

        results.append({
            "track_id": track.track_id,
            "sensor_id": track.sensor_id,
            "latitude": track.latitude,
            "longitude": track.longitude,
            "altitude": track.altitude,
            "heading": track.heading,
            "speed": track.speed,
            "status": status,
            "last_seen": last_seen,
            "age": age_seconds(last_seen)
        })

    return results 

@router.get('/{track_id}')
def get_track(
    track_id: str,
    db: Session = Depends(get_db)
):
    stmt = (
        select(Track)
        .where(Track.track_id == track_id)
    )
    
    track = db.scalar(stmt)
    
    if not track:
        raise HTTPException(
            status_code=404,
            detail=f"Track: {track_id} does not exist"
        )
    
    return track

@router.get("/{track_id}/status")
def track_status(
    track_id: str,
    db: Session = Depends(get_db)
):
    stmt = (
        select(Track)
        .where(Track.track_id == track_id)
    )

    track = db.scalar(stmt)

    if not track:
        raise HTTPException(
            status_code=404,
            detail=f"Track: {track_id} does not exist"
        )

    last_seen = ensure_utc(track.last_seen)

    return {
        "track_id": track.track_id,
        "status": get_track_status(last_seen),
        "last_seen": last_seen
    }