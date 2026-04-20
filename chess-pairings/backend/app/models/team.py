from sqlalchemy import Boolean, ForeignKey, Integer, String, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base, TimestampMixin


class Team(Base, TimestampMixin):
    __tablename__ = "team"
    __table_args__ = (UniqueConstraint("tournament_id", "name", name="uq_team_name_per_tournament"),)

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    tournament_id: Mapped[int] = mapped_column(ForeignKey("tournament.id", ondelete="CASCADE"), nullable=False)
    name: Mapped[str] = mapped_column(String(120), nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)

    tournament = relationship("Tournament", back_populates="teams")
    members = relationship("TournamentPlayer", back_populates="team")
    availabilities = relationship("TeamAvailability", back_populates="team", cascade="all, delete-orphan")
    lineups = relationship("TeamLineup", back_populates="team", cascade="all, delete-orphan")


class TeamAvailability(Base, TimestampMixin):
    __tablename__ = "team_availability"
    __table_args__ = (UniqueConstraint("team_id", "round_number", name="uq_team_availability_round"),)

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    team_id: Mapped[int] = mapped_column(ForeignKey("team.id", ondelete="CASCADE"), nullable=False)
    round_number: Mapped[int] = mapped_column(Integer, nullable=False)
    is_available: Mapped[bool] = mapped_column(Boolean, default=True)

    team = relationship("Team", back_populates="availabilities")


class TeamLineup(Base, TimestampMixin):
    __tablename__ = "team_lineup"
    __table_args__ = (UniqueConstraint("team_id", "tournament_player_id", "round_number", name="uq_team_lineup_player_round"),)

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    team_id: Mapped[int] = mapped_column(ForeignKey("team.id", ondelete="CASCADE"), nullable=False)
    tournament_player_id: Mapped[int] = mapped_column(ForeignKey("tournament_player.id", ondelete="CASCADE"), nullable=False)
    round_number: Mapped[int] = mapped_column(Integer, nullable=False)
    is_selected: Mapped[bool] = mapped_column(Boolean, default=False)

    team = relationship("Team", back_populates="lineups")
    tournament_player = relationship("TournamentPlayer")
