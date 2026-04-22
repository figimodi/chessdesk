"""add quadriglia tournament type

Revision ID: 20260421_000004
Revises: 20260421_000003
Create Date: 2026-04-21 16:20:00
"""

from alembic import op


revision = "20260421_000004"
down_revision = "20260421_000003"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.execute("ALTER TYPE tournamenttype ADD VALUE IF NOT EXISTS 'quadriglia'")


def downgrade() -> None:
    # PostgreSQL enum value removal is not safely reversible.
    pass
