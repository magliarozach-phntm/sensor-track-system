"""Persist shared public demo limits across restarts."""
from alembic import op
import sqlalchemy as sa

revision = "e49268d61a01"
down_revision = "4048a8b96475"
branch_labels = None
depends_on = None


def upgrade():
    state = op.create_table(
        "demo_state",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("run_day", sa.Date(), nullable=True),
        sa.Column("runs", sa.Integer(), nullable=False),
        sa.Column("running_until", sa.DateTime(timezone=True), nullable=True),
        sa.Column("next_allowed_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("error", sa.String(200), nullable=True),
    )
    op.bulk_insert(state, [{"id": 1, "runs": 0}])


def downgrade():
    op.drop_table("demo_state")
