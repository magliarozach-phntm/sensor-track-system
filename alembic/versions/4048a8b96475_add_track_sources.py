"""add track sources

Revision ID: 4048a8b96475
Revises: 9a4729a1683f
Create Date: 2026-09-11 14:57:13.162593

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '4048a8b96475'
down_revision: Union[str, Sequence[str], None] = '9a4729a1683f'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "track_sources",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("track_id", sa.String(length=50), nullable=False),
        sa.Column("sensor_id", sa.String(length=50), nullable=False),
        sa.Column("source_track_id", sa.String(length=50), nullable=False),
        sa.Column("first_seen", sa.DateTime(timezone=True), nullable=False),
        sa.Column("last_seen", sa.DateTime(timezone=True), nullable=False),
        sa.Column(
            "observation_count",
            sa.Integer(),
            server_default="1",
            nullable=False,
        ),
        sa.ForeignKeyConstraint(
            ["track_id"],
            ["tracks.track_id"],
        ),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint(
            "track_id",
            "sensor_id",
            "source_track_id",
            name="uq_track_source_identity",
        ),
    )

    op.create_index(
        op.f("ix_track_sources_track_id"),
        "track_sources",
        ["track_id"],
        unique=False,
    )

def downgrade() -> None:
    op.drop_index(
        op.f("ix_track_sources_track_id"),
        table_name="track_sources",
    )

    op.drop_table("track_sources")
    # ### end Alembic commands ###
