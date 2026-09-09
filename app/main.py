from datetime import datetime, timezone

from fastapi import Depends, FastAPI, HTTPException, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.database.database import Base, engine, get_db
from app.models.observation import Observation
from app.models.track import Track
from app.schemas.sensor import SensorObservation
from app.services.track_status import get_track_status
from app.services.web_socket_manager import manager

Base.metadata.create_all(bind=engine)
app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",
        "http://127.0.0.1:5173",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.websocket("/ws/tracks")
async def websocket_tracks(websocket: WebSocket):
    await manager.connect(websocket)

    try:
        while True:
            await websocket.receive_text()

    except WebSocketDisconnect:
        manager.disconnect(websocket)
        


@app.get("/")
def root():
    return {"message": 'Sensor Track System Online'}

@app.post("/observations")
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


@app.get('/observations/{track_id}')
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

@app.get('/observations')
def get_all_observations(db: Session = Depends(get_db)):
    stmt = select(Observation).order_by(Observation.timestamp)
    observations = db.scalars(stmt).all()
    
    return observations

@app.get('/observations/{track_id}/latest')
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

@app.get('/tracks')
def get_all_tracks(db: Session = Depends(get_db)):
    stmt = select(Track).order_by(Track.last_seen.desc())
    tracks = db.scalars(stmt).all()

    return tracks

@app.get('/tracks/search')
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

@app.get("/tracks/status")
def get_all_track_statuses(
    db: Session = Depends(get_db)
):
    stmt = (
        select(Track)
        .order_by(Track.last_seen.desc())
    )

    tracks = db.scalars(stmt).all()

    results = []

    now = datetime.now(timezone.utc)

    for track in tracks:
        status = get_track_status(track.last_seen)
        age = now - track.last_seen

        results.append({
            "track_id": track.track_id,
            "sensor_id": track.sensor_id,
            "latitude": track.latitude,
            "longitude": track.longitude,
            "altitude": track.altitude,
            "heading": track.heading,
            "speed": track.speed,
            "status": status,
            "last_seen": track.last_seen,
            "age": age.total_seconds()
        })

    return results 

@app.get('/tracks/{track_id}')
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

@app.get("/tracks/{track_id}/status")
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

    status = get_track_status(track.last_seen)

    return {
        "track_id": track.track_id,
        "status": status,
        "last_seen": track.last_seen
    }
    
  
    
