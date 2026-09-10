"""add source track id to observations

Revision ID: db2ba2ab88ef
Revises: 8d2437af9b80
Create Date: 2026-09-10 10:36:33.854381

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'db2ba2ab88ef'
down_revision: Union[str, Sequence[str], None] = '8d2437af9b80'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column(
        "observations",
        sa.Column(
            "source_track_id",
            sa.String(length=50),
            nullable=True
        )
    )

    op.execute(
        """
        UPDATE observations
        SET source_track_id = track_id
        """
    )

    op.alter_column(
        "observations",
        "source_track_id",
        existing_type=sa.String(length=50),
        nullable=False
    )


def downgrade() -> None:
    op.drop_column(
        "observations",
        "source_track_id"
    )
