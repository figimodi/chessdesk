import enum
from typing import Optional

from sqlalchemy import Boolean, Enum, ForeignKey, Integer, Numeric, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base, TimestampMixin


class PairingResult(str, enum.Enum):
    white_win = "1-0"
    black_win = "0-1"
    draw = "1/2-1/2"
    white_forfeit_win = "1-0F"
    black_forfeit_win = "0-1F"
    double_forfeit_loss = "0F-0F"
    double_forfeit_win = "1F-1F"
    bye = "1-bye"
    unplayed = "unplayed"


class Pairing(Base, TimestampMixin):
    __tablename__ = "pairing"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    round_id: Mapped[int] = mapped_column(ForeignKey("round.id", ondelete="CASCADE"), nullable=False)
    match_number: Mapped[Optional[int]] = mapped_column(Integer)
    board_number: Mapped[int] = mapped_column(Integer, nullable=False)
    white_player_id: Mapped[int] = mapped_column(ForeignKey("player.id", ondelete="RESTRICT"), nullable=False)
    black_player_id: Mapped[Optional[int]] = mapped_column(ForeignKey("player.id", ondelete="RESTRICT"))
    result: Mapped[PairingResult] = mapped_column(
        Enum(PairingResult, values_callable=lambda enum_items: [item.value for item in enum_items]),
        default=PairingResult.unplayed,
    )
    white_points: Mapped[float] = mapped_column(Numeric(4, 1), default=0)
    black_points: Mapped[float] = mapped_column(Numeric(4, 1), default=0)
    result_note: Mapped[Optional[str]] = mapped_column(String(120))
    is_bye: Mapped[bool] = mapped_column(Boolean, default=False)

    round = relationship("Round", back_populates="pairings")
    white_player = relationship(
        "Player", foreign_keys=[white_player_id], overlaps="white_pairings"
    )
    black_player = relationship(
        "Player", foreign_keys=[black_player_id], overlaps="black_pairings"
    )
