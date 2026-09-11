from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, Integer, String, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column

from app.database.database import Base


class TrackSource(Base):
    __tablename__ = "track_sources"

    id: Mapped[int] = mapped_column(
        Integer,
        primary_key=True,
    )

    track_id: Mapped[str] = mapped_column(
        String(50),
        ForeignKey("tracks.track_id"),
        nullable=False,
        index=True,
    )

    sensor_id: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
    )

    source_track_id: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
    )

    first_seen: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
    )

    last_seen: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
    )

    observation_count: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        default=1,
        server_default="1",
    )

    __table_args__ = (
        UniqueConstraint(
            "track_id",
            "sensor_id",
            "source_track_id",
            name="uq_track_source_identity",
        ),
    )