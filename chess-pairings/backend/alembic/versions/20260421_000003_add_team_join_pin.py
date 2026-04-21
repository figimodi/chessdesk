"""add team join pin

Revision ID: 20260421_000003
Revises: 20260421_000002
Create Date: 2026-04-21 13:40:00
"""

from alembic import op
import sqlalchemy as sa


revision = "20260421_000003"
down_revision = "20260421_000002"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column("team", sa.Column("join_pin", sa.String(length=4), nullable=True))
    op.execute("UPDATE team SET join_pin = lpad((1000 + id % 9000)::text, 4, '0') WHERE join_pin IS NULL")
    op.alter_column("team", "join_pin", nullable=False)
    op.create_unique_constraint("uq_team_join_pin_per_tournament", "team", ["tournament_id", "join_pin"])


def downgrade() -> None:
    op.drop_constraint("uq_team_join_pin_per_tournament", "team", type_="unique")
    op.drop_column("team", "join_pin")
