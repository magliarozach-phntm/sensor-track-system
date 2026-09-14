import logging
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

logger = logging.getLogger(__name__)

def generate_track_id() -> str:
    return (
        f"SYS-{uuid4().hex[:12].upper()}"
    )

@router.post("")
async def create_observation(
    observation: SensorObservation,
    db: Session = Depends(get_db),
):
    # --------------------------------------------------
    # 1. ASSOCIATION
    # --------------------------------------------------

    association = find_correlated_track(
        observation,
        db,
    )

    # --------------------------------------------------
    # 2. EXISTING SYSTEM TRACK
    # --------------------------------------------------

    if association is not None:
        track = association.track
        system_track_id = track.track_id

        # Update accumulated track quality.
        track.quality = calculate_track_quality(
            current_quality=track.quality,
            association_method=association.method,
            association_score=association.score,
        )

        # Current system belief before applying
        # the newest sensor measurement.
        previous_state = EstimatedState(
            latitude=track.latitude,
            longitude=track.longitude,
            altitude=track.altitude,
            heading=track.heading,
            speed=track.speed,
        )

        # Raw incoming sensor measurement.
        measurement = EstimatedState(
            latitude=observation.latitude,
            longitude=observation.longitude,
            altitude=observation.altitude,
            heading=observation.heading,
            speed=observation.speed,
        )

        # Blend the existing system state with
        # the incoming sensor measurement.
        estimated_state = estimate_track_state(
            previous_state=previous_state,
            measurement=measurement,
        )

        # Latest contributing sensor.
        track.sensor_id = observation.sensor_id

        # Estimated system state.
        track.latitude = estimated_state.latitude
        track.longitude = estimated_state.longitude
        track.altitude = estimated_state.altitude
        track.heading = estimated_state.heading
        track.speed = estimated_state.speed

        track.last_seen = observation.timestamp

    # --------------------------------------------------
    # 3. NEW SYSTEM TRACK
    # --------------------------------------------------

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

        # IMPORTANT:
        # TrackSource has a foreign key to tracks.track_id.
        # Flush ensures PostgreSQL receives the parent Track
        # INSERT before we create its TrackSource row.
        #
        # This is NOT a commit.
        db.flush()

    # --------------------------------------------------
    # 4. ASSOCIATION METADATA
    # --------------------------------------------------

    if association is not None:
        association_method = association.method
        association_score = association.score
        confidence = association.confidence

    else:
        association_method = "NEW_TRACK"
        association_score = None
        confidence = None

    # --------------------------------------------------
    # 5. PRESERVE RAW SENSOR OBSERVATION
    # --------------------------------------------------

    db_observation = Observation(
        sensor_id=observation.sensor_id,

        # Identity assigned by the sensor.
        source_track_id=observation.source_track_id,

        # Identity owned by this tracking system.
        track_id=system_track_id,

        # Preserve RAW measurement values here.
        latitude=observation.latitude,
        longitude=observation.longitude,
        altitude=observation.altitude,
        heading=observation.heading,
        speed=observation.speed,
        timestamp=observation.timestamp,
    )

    db.add(db_observation)

    # --------------------------------------------------
    # 6. RECORD SENSOR/SOURCE PROVENANCE
    # --------------------------------------------------

    record_track_source(
        db=db,
        track_id=system_track_id,
        sensor_id=observation.sensor_id,
        source_track_id=observation.source_track_id,
        timestamp=observation.timestamp,
    )

    # --------------------------------------------------
    # 7. COMMIT TRANSACTION
    # --------------------------------------------------

    try:
        db.commit()

    except Exception:
        db.rollback()

        logger.exception(
            "event=OBSERVATION_COMMIT_FAILED "
            "track_id=%s "
            "sensor_id=%s "
            "source_track_id=%s",
            system_track_id,
            observation.sensor_id,
            observation.source_track_id,
        )

        raise

    db.refresh(db_observation)
    db.refresh(track)

    # --------------------------------------------------
    # 8. STRUCTURED APPLICATION LOGGING
    # --------------------------------------------------

    if association_method == "NEW_TRACK":
        logger.info(
            "event=TRACK_CREATED "
            "track_id=%s "
            "sensor_id=%s "
            "source_track_id=%s "
            "quality=%.2f",
            track.track_id,
            observation.sensor_id,
            observation.source_track_id,
            track.quality,
        )

    elif association_method == "SOURCE_CONTINUITY":
        logger.info(
            "event=SOURCE_CONTINUITY "
            "track_id=%s "
            "sensor_id=%s "
            "source_track_id=%s "
            "quality=%.2f",
            track.track_id,
            observation.sensor_id,
            observation.source_track_id,
            track.quality,
        )

    elif association_method == "CORRELATION":
        logger.info(
            "event=TRACK_CORRELATED "
            "track_id=%s "
            "sensor_id=%s "
            "source_track_id=%s "
            "score=%.3f "
            "confidence=%s "
            "quality=%.2f",
            track.track_id,
            observation.sensor_id,
            observation.source_track_id,
            association_score,
            confidence,
            track.quality,
        )

    # --------------------------------------------------
    # 9. TRACK STATUS
    # --------------------------------------------------

    status = get_track_status(
        track.last_seen,
    )

    # --------------------------------------------------
    # 10. REAL-TIME WEBSOCKET UPDATE
    # --------------------------------------------------

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
        "association_confidence": confidence,
    })

    # --------------------------------------------------
    # 11. API RESPONSE
    # --------------------------------------------------

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
        "association_confidence": confidence,
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