import enum
from datetime import date, datetime
from typing import Optional

from sqlalchemy import Boolean, Date, DateTime, Enum, ForeignKey, Integer, String, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base, TimestampMixin


class TournamentType(str, enum.Enum):
    individual = "individual"
    team = "team"


class TournamentFormat(str, enum.Enum):
    swiss = "swiss"


class RoundStatus(str, enum.Enum):
    pending = "pending"
    published = "published"
    completed = "completed"


class Tournament(Base, TimestampMixin):
    __tablename__ = "tournament"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    name: Mapped[str] = mapped_column(String(120), nullable=False, index=True)
    type: Mapped[TournamentType] = mapped_column(Enum(TournamentType), nullable=False)
    format: Mapped[TournamentFormat] = mapped_column(Enum(TournamentFormat), default=TournamentFormat.swiss)
    time_control: Mapped[str] = mapped_column(String(20), nullable=False)
    start_date: Mapped[date] = mapped_column(Date, nullable=False)
    end_date: Mapped[date] = mapped_column(Date, nullable=False)
    rounds_count: Mapped[int] = mapped_column(Integer, nullable=False)
    pairings_system: Mapped[str] = mapped_column(String(20), default="dutch")
    tie_breaks: Mapped[str] = mapped_column(String(120), default="buchholz,sonneborn_berger,rating")
    is_elo_rated: Mapped[bool] = mapped_column(Boolean, default=False)
    max_players_per_team: Mapped[Optional[int]] = mapped_column(Integer)
    boards_per_match: Mapped[Optional[int]] = mapped_column(Integer)
    enforce_board_order: Mapped[bool] = mapped_column(Boolean, default=False)
    match_points_win: Mapped[Optional[int]] = mapped_column(Integer)
    match_points_draw: Mapped[Optional[int]] = mapped_column(Integer)
    match_points_loss: Mapped[Optional[int]] = mapped_column(Integer)
    venue: Mapped[Optional[str]] = mapped_column(String(120))
    description: Mapped[Optional[str]] = mapped_column(String(1000))
    bulletin_path: Mapped[Optional[str]] = mapped_column(String(255))
    is_published: Mapped[bool] = mapped_column(Boolean, default=False)
    is_private: Mapped[bool] = mapped_column(Boolean, default=False)
    is_registration_closed: Mapped[bool] = mapped_column(Boolean, default=False)
    owner_id: Mapped[Optional[int]] = mapped_column(ForeignKey("user_account.id", ondelete="SET NULL"))

    rounds = relationship("Round", back_populates="tournament", cascade="all, delete-orphan")
    players = relationship("TournamentPlayer", back_populates="tournament", cascade="all, delete-orphan")
    teams = relationship("Team", back_populates="tournament", cascade="all, delete-orphan")
    owner = relationship("User", back_populates="tournaments")


class TournamentPlayer(Base, TimestampMixin):
    __tablename__ = "tournament_player"
    __table_args__ = (UniqueConstraint("tournament_id", "player_id", name="uq_tournament_player"),)

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    tournament_id: Mapped[int] = mapped_column(ForeignKey("tournament.id", ondelete="CASCADE"), nullable=False)
    player_id: Mapped[int] = mapped_column(ForeignKey("player.id", ondelete="CASCADE"), nullable=False)
    team_id: Mapped[Optional[int]] = mapped_column(ForeignKey("team.id", ondelete="SET NULL"))
    team_board_order: Mapped[Optional[int]] = mapped_column(Integer)
    seed_number: Mapped[Optional[int]] = mapped_column(Integer)
    initial_rating: Mapped[Optional[int]] = mapped_column(Integer)
    start_round_number: Mapped[int] = mapped_column(Integer, default=1)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    joined_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=datetime.utcnow)

    tournament = relationship("Tournament", back_populates="players")
    player = relationship("Player", back_populates="tournaments")
    team = relationship("Team", back_populates="members")
    availabilities = relationship(
        "TournamentPlayerAvailability",
        back_populates="tournament_player",
        cascade="all, delete-orphan",
    )


class TournamentPlayerAvailability(Base, TimestampMixin):
    __tablename__ = "tournament_player_availability"
    __table_args__ = (
        UniqueConstraint(
            "tournament_player_id",
            "round_number",
            name="uq_tournament_player_availability_round",
        ),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    tournament_player_id: Mapped[int] = mapped_column(
        ForeignKey("tournament_player.id", ondelete="CASCADE"), nullable=False
    )
    round_number: Mapped[int] = mapped_column(Integer, nullable=False)
    is_available: Mapped[bool] = mapped_column(Boolean, default=True)

    tournament_player = relationship("TournamentPlayer", back_populates="availabilities")
