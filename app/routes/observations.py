from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.database.database import get_db
from app.models.observation import Observation
from app.models.track import Track
from app.schemas.sensor import SensorObservation
from app.services.track_status import get_track_status
from app.services.web_socket_manager import manager

router = APIRouter(
    prefix="/observations",
    tags=["observations"],
)

@router.post("")
async def create_observation(
    observation: SensorObservation,
    db: Session = Depends(get_db)
):
    db_observation = Observation(
        sensor_id=observation.sensor_id,
        track_id=observation.track_id,
        latitude=observation.latitude,
        longitude=observation.longitude,
        altitude=observation.altitude,
        heading=observation.heading,
        speed=observation.speed,
        timestamp=observation.timestamp,
    )

    db.add(db_observation)

    stmt = (
        select(Track)
        .where(Track.track_id == observation.track_id)
    )

    existing_track = db.scalar(stmt)

    if existing_track:
        existing_track.sensor_id = observation.sensor_id
        existing_track.latitude = observation.latitude
        existing_track.longitude = observation.longitude
        existing_track.altitude = observation.altitude
        existing_track.heading = observation.heading
        existing_track.speed = observation.speed
        existing_track.last_seen = observation.timestamp

        track = existing_track

    else:
        new_track = Track(
            track_id=observation.track_id,
            sensor_id=observation.sensor_id,
            latitude=observation.latitude,
            longitude=observation.longitude,
            altitude=observation.altitude,
            heading=observation.heading,
            speed=observation.speed,
            last_seen=observation.timestamp,
        )

        db.add(new_track)

        track = new_track

    db.commit()

    db.refresh(db_observation)
    db.refresh(track)

    status = get_track_status(track.last_seen)

    await manager.broadcast({
    "event": "track_updated",

    "observation_id": db_observation.id,

    "track_id": track.track_id,
    "sensor_id": track.sensor_id,
    "latitude": track.latitude,
    "longitude": track.longitude,
    "altitude": track.altitude,
    "heading": track.heading,
    "speed": track.speed,
    "status": status,
    "last_seen": track.last_seen.isoformat()
})

    return {
        "message": "Observation stored and track state updated",
        "id": db_observation.id,
        "track_id": db_observation.track_id,
    }


@router.get('/{track_id}')
def get_observations(
    track_id: str,
    limit: int = 100, 
    db: Session = Depends(get_db)
):
    stmt = (
        select(Observation)
        .where(Observation.track_id == track_id)
        .order_by(Observation.timestamp.desc())
        .limit(limit)
    )
    
    observations = db.scalars(stmt).all()
    
    if not observations:
        raise HTTPException(status_code=404, 
                            detail=f"No observations found for track_id: {track_id}")
    
    return list(reversed(observations))

@router.get('')
def get_all_observations(db: Session = Depends(get_db)):
    stmt = select(Observation).order_by(Observation.timestamp)
    observations = db.scalars(stmt).all()
    
    return observations

@router.get('/{track_id}/latest')
def get_latest_observation(
    track_id: str, 
    db: Session = Depends(get_db)
):
    stmt = (
    select(Observation)
    .where(Observation.track_id == track_id)
    .order_by(
        Observation.timestamp.desc(),
        Observation.id.desc()
    )
    .limit(1)
)
    
    latest_observation = db.scalars(stmt).first()
    
    if not latest_observation:
        raise HTTPException(status_code=404, 
                            detail=f"No observations found for track_id: {track_id}")
    
    return latest_observation