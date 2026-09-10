from uuid import uuid4

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.database.database import get_db
from app.models.observation import Observation
from app.models.track import Track
from app.schemas.sensor import SensorObservation
from app.services.association import (
    find_correlated_track,
)
from app.services.track_status import get_track_status
from app.services.web_socket_manager import manager

router = APIRouter(
    prefix="/observations",
    tags=["observations"],
)

def generate_track_id() -> str:
    return (
        f"SYS-{uuid4().hex[:12].upper()}"
    )

@router.post("")
async def create_observation(
    observation: SensorObservation,
    db: Session = Depends(get_db)
):
    # Try to associate the incoming sensor report
    # with an existing system-owned track.
    associated_track = find_correlated_track(
        observation,
        db
    )

    if associated_track is not None:
        track = associated_track
        system_track_id = track.track_id

        # Update current system track state
        # with the latest observation.
        track.sensor_id = observation.sensor_id
        track.latitude = observation.latitude
        track.longitude = observation.longitude
        track.altitude = observation.altitude
        track.heading = observation.heading
        track.speed = observation.speed
        track.last_seen = observation.timestamp

    else:
        # No plausible existing track was found,
        # so create a new system-owned identity.
        system_track_id = generate_track_id()

        track = Track(
            track_id=system_track_id,
            sensor_id=observation.sensor_id,
            latitude=observation.latitude,
            longitude=observation.longitude,
            altitude=observation.altitude,
            heading=observation.heading,
            speed=observation.speed,
            last_seen=observation.timestamp,
        )

        db.add(track)

    # Preserve both identities:
    # source_track_id = sensor identity
    # track_id        = system identity
    db_observation = Observation(
        sensor_id=observation.sensor_id,
        source_track_id=observation.source_track_id,
        track_id=system_track_id,
        latitude=observation.latitude,
        longitude=observation.longitude,
        altitude=observation.altitude,
        heading=observation.heading,
        speed=observation.speed,
        timestamp=observation.timestamp,
    )

    db.add(db_observation)

    db.commit()

    db.refresh(db_observation)
    db.refresh(track)

    status = get_track_status(
        track.last_seen
    )

    await manager.broadcast({
        "event": "track_updated",
        "observation_id": db_observation.id,
        "track_id": track.track_id,
        "source_track_id": observation.source_track_id,
        "sensor_id": track.sensor_id,
        "latitude": track.latitude,
        "longitude": track.longitude,
        "altitude": track.altitude,
        "heading": track.heading,
        "speed": track.speed,
        "status": status,
        "last_seen": track.last_seen.isoformat(),
    })

    return {
        "message": (
            "Observation stored and "
            "track state updated"
        ),
        "id": db_observation.id,
        "track_id": track.track_id,
        "source_track_id": observation.source_track_id,
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