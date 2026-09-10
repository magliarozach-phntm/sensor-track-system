from datetime import datetime

from sqlalchemy import DateTime, Float, String
from sqlalchemy.orm import Mapped, mapped_column

from app.database.database import Base


class Observation(Base):
    __tablename__ = "observations"
    
    id: Mapped[int] = mapped_column(primary_key=True)
    
    sensor_id: Mapped[str] = mapped_column(String(50), nullable=False)
    track_id: Mapped[str] = mapped_column(String(50), nullable=False)
    source_track_id: Mapped[str] = mapped_column(
        String(50),
        nullable=False
    )
    
    latitude: Mapped[float] = mapped_column(Float, nullable=False)
    longitude: Mapped[float] = mapped_column(Float, nullable=False)
    
    altitude: Mapped[float] = mapped_column(Float, nullable=False)
    heading: Mapped[float] = mapped_column(Float, nullable=False)
    speed: Mapped[float] = mapped_column(Float, nullable=False)
    timestamp: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False)
    