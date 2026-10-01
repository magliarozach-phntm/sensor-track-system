import secrets

from fastapi import Header, HTTPException

from app.config import settings


def require_sensor_key(x_sensor_key: str = Header(default="")) -> None:
    """Keep public demo reads open while restricting database writes."""
    if settings.app_env == "production" and not settings.sensor_api_key:
        raise HTTPException(status_code=503, detail="Observation ingestion is not configured")
    if settings.sensor_api_key and not secrets.compare_digest(
        x_sensor_key.encode(), settings.sensor_api_key.encode()
    ):
        raise HTTPException(status_code=401, detail="Invalid sensor key")
