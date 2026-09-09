from datetime import datetime

from sqlalchemy import DateTime, Float, String
from sqlalchemy.orm import Mapped, mapped_column

from app.database.database import Base

class Track(Base):
    __tablename__ = "tracks"
    
    id: Mapped[int] = mapped_column(primary_key=True)
    
    track_id: Mapped[str] = mapped_column(
        String(50),
        unique=True,
        nullable=False,
        index=True
    )
    
    sensor_id: Mapped[str] = mapped_column(
        String(50), 
        nullable=False
    )
    
    latitude: Mapped[float] = mapped_column(
        Float, 
        nullable=False
    )
    
    longitude: Mapped[float] = mapped_column(
        Float, 
        nullable=False
    )
    
    altitude: Mapped[float] = mapped_column(
        Float, 
        nullable=False
    )
    
    heading: Mapped[float] = mapped_column(
        Float, 
        nullable=False
    )
    
    speed: Mapped[float] = mapped_column(
        Float, 
        nullable=False
    )
    
    last_seen: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False)