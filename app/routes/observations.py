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
from app.services.state_estimation import EstimatedState, estimate_track_state
from app.services.track_quality import calculate_track_quality
from app.services.track_sources import record_track_source
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
    association = find_correlated_track(
        observation,
        db
    )

    if association is not None:
        track = association.track
        system_track_id = track.track_id
        track.quality = calculate_track_quality(
            current_quality=track.quality,
            association_method=association.method,
            association_score=association.score
        )
        
        previous_state = EstimatedState(
            latitude=track.latitude,
            longitude=track.longitude,
            altitude=track.altitude,
            heading=track.heading,
            speed=track.speed,
        )
        
        measurement = EstimatedState(
            latitude=observation.latitude,
            longitude=observation.longitude,
            altitude=observation.altitude,
            heading=observation.heading,
            speed=observation.speed
        )
        
        estimated_state = estimate_track_state(
            previous_state=previous_state,
            measurement=measurement
        )
        
        track.sensor_id = observation.sensor_id
        track.latitude = observation.latitude
        track.longitude = observation.longitude
        track.altitude = observation.altitude
        track.heading = observation.heading
        track.speed = observation.speed
        track.last_seen = observation.timestamp

    else:
        system_track_id = generate_track_id()

        track = Track(
            track_id=system_track_id,
            quality=0.50,
            sensor_id=observation.sensor_id,
            latitude=observation.latitude,
            longitude=observation.longitude,
            altitude=observation.altitude,
            heading=observation.heading,
            speed=observation.speed,
            last_seen=observation.timestamp,
        )

        db.add(track)
        db.flush()


    # Association metadata
    if association is not None:
        association_method = association.method
        association_score = association.score
        confidence = association.confidence
    else:
        association_method = "NEW_TRACK"
        association_score = None
        confidence = None

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

    record_track_source(
        db=db,
        track_id=system_track_id,
        sensor_id=observation.sensor_id,
        source_track_id=observation.source_track_id,
        timestamp=observation.timestamp,
    )
    
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
        "quality": track.quality,
        "latitude": track.latitude,
        "longitude": track.longitude,
        "altitude": track.altitude,
        "heading": track.heading,
        "speed": track.speed,

        "status": status,
        "last_seen": track.last_seen.isoformat(),

        "association_method": association_method,
        "association_score": association_score,
        "association_confidence": confidence
    })
    
    return {
        "message": (
            "Observation stored and "
            "track state updated"
        ),
        "id": db_observation.id,
        "track_id": track.track_id,
        "quality": track.quality,
        "source_track_id": observation.source_track_id,
        "association_method": association_method,
        "association_score": association_score,
        "association_confidence": confidence
    }


@router.get('/{track_id}')
def get_observations(
    track_id: str,
    limit: int = 100,
    db: Session = Depends(get_db)
):
    stmt = (
        select(Observation)
        .where(
            Observation.track_id == track_id
        )
        .order_by(
            Observation.timestamp.desc()
        )
        .limit(limit)
    )

    observations = db.scalars(
        stmt
    ).all()

    if not observations:
        raise HTTPException(
            status_code=404,
            detail=(
                "No observations found for "
                f"track_id: {track_id}"
            )
        )

    return list(
        reversed(observations)
    )

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