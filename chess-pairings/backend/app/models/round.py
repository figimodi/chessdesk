from datetime import datetime
from typing import Optional

from sqlalchemy import DateTime, Enum, ForeignKey, Integer
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base, TimestampMixin
from app.models.tournament import RoundStatus


class Round(Base, TimestampMixin):
    __tablename__ = "round"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    tournament_id: Mapped[int] = mapped_column(ForeignKey("tournament.id", ondelete="CASCADE"), nullable=False)
    number: Mapped[int] = mapped_column(Integer, nullable=False)
    scheduled_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True))
    status: Mapped[RoundStatus] = mapped_column(Enum(RoundStatus), default=RoundStatus.pending)

    tournament = relationship("Tournament", back_populates="rounds")
    pairings = relationship("Pairing", back_populates="round", cascade="all, delete-orphan")
