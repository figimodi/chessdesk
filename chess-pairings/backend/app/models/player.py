from typing import Optional

from sqlalchemy import Integer, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base, TimestampMixin


class Player(Base, TimestampMixin):
    __tablename__ = "player"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    full_name: Mapped[str] = mapped_column(String(120), nullable=False, index=True)
    fide_id: Mapped[Optional[str]] = mapped_column(String(20), unique=True, index=True)
    federation: Mapped[Optional[str]] = mapped_column(String(3))
    rating: Mapped[Optional[int]] = mapped_column(Integer)
    standard_k: Mapped[Optional[int]] = mapped_column(Integer)
    rapid_rating: Mapped[Optional[int]] = mapped_column(Integer)
    rapid_k: Mapped[Optional[int]] = mapped_column(Integer)
    blitz_rating: Mapped[Optional[int]] = mapped_column(Integer)
    blitz_k: Mapped[Optional[int]] = mapped_column(Integer)
    birth_year: Mapped[Optional[int]] = mapped_column(Integer)
    fide_title: Mapped[Optional[str]] = mapped_column(String(20))

    tournaments = relationship("TournamentPlayer", back_populates="player")
    white_pairings = relationship(
        "Pairing",
        foreign_keys="Pairing.white_player_id",
        overlaps="white_player",
    )
    black_pairings = relationship(
        "Pairing",
        foreign_keys="Pairing.black_player_id",
        overlaps="black_player",
    )
