"""harden auth constraints

Revision ID: 20260421_000002
Revises: 20260421_000001
Create Date: 2026-04-21 13:15:00
"""

from alembic import op
import sqlalchemy as sa


revision = "20260421_000002"
down_revision = "20260421_000001"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.execute("UPDATE user_account SET username = lower(trim(username))")
    op.add_column("user_account", sa.Column("email_confirmation_sent_at", sa.DateTime(timezone=True), nullable=True))
    op.create_index(op.f("ix_user_account_username"), "user_account", ["username"], unique=True)


def downgrade() -> None:
    op.drop_index(op.f("ix_user_account_username"), table_name="user_account")
    op.drop_column("user_account", "email_confirmation_sent_at")
