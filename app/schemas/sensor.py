from datetime import datetime, timezone

from pydantic import BaseModel, Field, field_validator


class SensorObservation(BaseModel):
    sensor_id: str
    track_id: str
    
    latitude: float = Field(ge=-90, le=90)
    longitude: float = Field(ge=-180, le=180)
    
    altitude: float = Field(ge=0)
    heading: float = Field(ge=0, lt=360)
    speed: float = Field(ge=0)
    
    timestamp: datetime
    
    @field_validator('timestamp')
    @classmethod
    def normalize_timestamp(cls, value: datetime) -> datetime:
        if value.tzinfo is None or value.utcoffset() is None:
            raise ValueError('timestamp must include timezone information')
        
        return value.astimezone(timezone.utc)
    