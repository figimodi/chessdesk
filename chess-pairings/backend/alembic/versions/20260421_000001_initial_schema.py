"""initial schema

Revision ID: 20260421_000001
Revises:
Create Date: 2026-04-21 00:00:01
"""

from alembic import op
import sqlalchemy as sa


revision = "20260421_000001"
down_revision = None
branch_labels = None
depends_on = None


pairingresult = sa.Enum(
    "1-0",
    "0-1",
    "1/2-1/2",
    "1-0F",
    "0-1F",
    "0F-0F",
    "1F-1F",
    "1-bye",
    "unplayed",
    name="pairingresult",
)
tournamentformat = sa.Enum("swiss", name="tournamentformat")
tournamenttype = sa.Enum("individual", "team", name="tournamenttype")
roundstatus = sa.Enum("pending", "published", "completed", name="roundstatus")
userrole = sa.Enum("admin", "user", name="userrole")


def upgrade() -> None:
    op.create_table(
        "catalog_player",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("fide_id", sa.String(length=20), nullable=False),
        sa.Column("full_name", sa.String(length=120), nullable=False),
        sa.Column("federation", sa.String(length=3), nullable=True),
        sa.Column("rating", sa.Integer(), nullable=True),
        sa.Column("standard_rating", sa.Integer(), nullable=True),
        sa.Column("standard_k", sa.Integer(), nullable=True),
        sa.Column("rapid_rating", sa.Integer(), nullable=True),
        sa.Column("rapid_k", sa.Integer(), nullable=True),
        sa.Column("blitz_rating", sa.Integer(), nullable=True),
        sa.Column("blitz_k", sa.Integer(), nullable=True),
        sa.Column("birth_year", sa.Integer(), nullable=True),
        sa.Column("fide_title", sa.String(length=20), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_catalog_player_fide_id"), "catalog_player", ["fide_id"], unique=True)
    op.create_index(op.f("ix_catalog_player_full_name"), "catalog_player", ["full_name"], unique=False)

    op.create_table(
        "player",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("full_name", sa.String(length=120), nullable=False),
        sa.Column("fide_id", sa.String(length=20), nullable=True),
        sa.Column("federation", sa.String(length=3), nullable=True),
        sa.Column("rating", sa.Integer(), nullable=True),
        sa.Column("standard_k", sa.Integer(), nullable=True),
        sa.Column("rapid_rating", sa.Integer(), nullable=True),
        sa.Column("rapid_k", sa.Integer(), nullable=True),
        sa.Column("blitz_rating", sa.Integer(), nullable=True),
        sa.Column("blitz_k", sa.Integer(), nullable=True),
        sa.Column("birth_year", sa.Integer(), nullable=True),
        sa.Column("fide_title", sa.String(length=20), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_player_fide_id"), "player", ["fide_id"], unique=True)
    op.create_index(op.f("ix_player_full_name"), "player", ["full_name"], unique=False)

    op.create_table(
        "user_account",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("email", sa.String(length=255), nullable=False),
        sa.Column("username", sa.String(length=120), nullable=False),
        sa.Column("password_hash", sa.String(length=255), nullable=False),
        sa.Column("role", userrole, nullable=False),
        sa.Column("is_active", sa.Boolean(), nullable=False),
        sa.Column("email_confirmed", sa.Boolean(), nullable=False),
        sa.Column("must_change_password", sa.Boolean(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_user_account_email"), "user_account", ["email"], unique=True)

    op.create_table(
        "tournament",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("name", sa.String(length=120), nullable=False),
        sa.Column("type", tournamenttype, nullable=False),
        sa.Column("format", tournamentformat, nullable=False),
        sa.Column("time_control", sa.String(length=20), nullable=False),
        sa.Column("start_date", sa.Date(), nullable=False),
        sa.Column("end_date", sa.Date(), nullable=False),
        sa.Column("rounds_count", sa.Integer(), nullable=False),
        sa.Column("pairings_system", sa.String(length=20), nullable=False),
        sa.Column("tie_breaks", sa.String(length=120), nullable=False),
        sa.Column("is_elo_rated", sa.Boolean(), nullable=False),
        sa.Column("max_players_per_team", sa.Integer(), nullable=True),
        sa.Column("boards_per_match", sa.Integer(), nullable=True),
        sa.Column("enforce_board_order", sa.Boolean(), nullable=False),
        sa.Column("match_points_win", sa.Integer(), nullable=True),
        sa.Column("match_points_draw", sa.Integer(), nullable=True),
        sa.Column("match_points_loss", sa.Integer(), nullable=True),
        sa.Column("venue", sa.String(length=120), nullable=True),
        sa.Column("description", sa.String(length=1000), nullable=True),
        sa.Column("bulletin_path", sa.String(length=255), nullable=True),
        sa.Column("is_published", sa.Boolean(), nullable=False),
        sa.Column("is_private", sa.Boolean(), nullable=False),
        sa.Column("is_registration_closed", sa.Boolean(), nullable=False),
        sa.Column("owner_id", sa.Integer(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.ForeignKeyConstraint(["owner_id"], ["user_account.id"], ondelete="SET NULL"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_tournament_name"), "tournament", ["name"], unique=False)

    op.create_table(
        "round",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("tournament_id", sa.Integer(), nullable=False),
        sa.Column("number", sa.Integer(), nullable=False),
        sa.Column("scheduled_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("status", roundstatus, nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.ForeignKeyConstraint(["tournament_id"], ["tournament.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )

    op.create_table(
        "team",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("tournament_id", sa.Integer(), nullable=False),
        sa.Column("name", sa.String(length=120), nullable=False),
        sa.Column("is_active", sa.Boolean(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.ForeignKeyConstraint(["tournament_id"], ["tournament.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("tournament_id", "name", name="uq_team_name_per_tournament"),
    )

    op.create_table(
        "pairing",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("round_id", sa.Integer(), nullable=False),
        sa.Column("match_number", sa.Integer(), nullable=True),
        sa.Column("board_number", sa.Integer(), nullable=False),
        sa.Column("white_player_id", sa.Integer(), nullable=False),
        sa.Column("black_player_id", sa.Integer(), nullable=True),
        sa.Column("result", pairingresult, nullable=False),
        sa.Column("white_points", sa.Numeric(4, 1), nullable=False),
        sa.Column("black_points", sa.Numeric(4, 1), nullable=False),
        sa.Column("result_note", sa.String(length=120), nullable=True),
        sa.Column("is_bye", sa.Boolean(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.ForeignKeyConstraint(["black_player_id"], ["player.id"], ondelete="RESTRICT"),
        sa.ForeignKeyConstraint(["round_id"], ["round.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["white_player_id"], ["player.id"], ondelete="RESTRICT"),
        sa.PrimaryKeyConstraint("id"),
    )

    op.create_table(
        "tournament_player",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("tournament_id", sa.Integer(), nullable=False),
        sa.Column("player_id", sa.Integer(), nullable=False),
        sa.Column("team_id", sa.Integer(), nullable=True),
        sa.Column("team_board_order", sa.Integer(), nullable=True),
        sa.Column("seed_number", sa.Integer(), nullable=True),
        sa.Column("initial_rating", sa.Integer(), nullable=True),
        sa.Column("start_round_number", sa.Integer(), nullable=False),
        sa.Column("is_active", sa.Boolean(), nullable=False),
        sa.Column("joined_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.ForeignKeyConstraint(["player_id"], ["player.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["team_id"], ["team.id"], ondelete="SET NULL"),
        sa.ForeignKeyConstraint(["tournament_id"], ["tournament.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("tournament_id", "player_id", name="uq_tournament_player"),
    )

    op.create_table(
        "team_availability",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("team_id", sa.Integer(), nullable=False),
        sa.Column("round_number", sa.Integer(), nullable=False),
        sa.Column("is_available", sa.Boolean(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.ForeignKeyConstraint(["team_id"], ["team.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("team_id", "round_number", name="uq_team_availability_round"),
    )

    op.create_table(
        "team_lineup",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("team_id", sa.Integer(), nullable=False),
        sa.Column("tournament_player_id", sa.Integer(), nullable=False),
        sa.Column("round_number", sa.Integer(), nullable=False),
        sa.Column("is_selected", sa.Boolean(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.ForeignKeyConstraint(["team_id"], ["team.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["tournament_player_id"], ["tournament_player.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("team_id", "tournament_player_id", "round_number", name="uq_team_lineup_player_round"),
    )

    op.create_table(
        "tournament_player_availability",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("tournament_player_id", sa.Integer(), nullable=False),
        sa.Column("round_number", sa.Integer(), nullable=False),
        sa.Column("is_available", sa.Boolean(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.ForeignKeyConstraint(["tournament_player_id"], ["tournament_player.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("tournament_player_id", "round_number", name="uq_tournament_player_availability_round"),
    )


def downgrade() -> None:
    op.drop_table("tournament_player_availability")
    op.drop_table("team_lineup")
    op.drop_table("team_availability")
    op.drop_table("tournament_player")
    op.drop_table("pairing")
    op.drop_table("team")
    op.drop_table("round")
    op.drop_index(op.f("ix_tournament_name"), table_name="tournament")
    op.drop_table("tournament")
    op.drop_index(op.f("ix_user_account_email"), table_name="user_account")
    op.drop_table("user_account")
    op.drop_index(op.f("ix_player_full_name"), table_name="player")
    op.drop_index(op.f("ix_player_fide_id"), table_name="player")
    op.drop_table("player")
    op.drop_index(op.f("ix_catalog_player_full_name"), table_name="catalog_player")
    op.drop_index(op.f("ix_catalog_player_fide_id"), table_name="catalog_player")
    op.drop_table("catalog_player")

    bind = op.get_bind()
    roundstatus.drop(bind, checkfirst=True)
    tournamenttype.drop(bind, checkfirst=True)
    tournamentformat.drop(bind, checkfirst=True)
    userrole.drop(bind, checkfirst=True)
    pairingresult.drop(bind, checkfirst=True)
