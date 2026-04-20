from typing import Optional

from sqlalchemy import Integer, String
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base, TimestampMixin


class CatalogPlayer(Base, TimestampMixin):
    __tablename__ = "catalog_player"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    fide_id: Mapped[str] = mapped_column(String(20), unique=True, index=True)
    full_name: Mapped[str] = mapped_column(String(120), nullable=False, index=True)
    federation: Mapped[Optional[str]] = mapped_column(String(3))
    rating: Mapped[Optional[int]] = mapped_column(Integer)
    standard_rating: Mapped[Optional[int]] = mapped_column(Integer)
    standard_k: Mapped[Optional[int]] = mapped_column(Integer)
    rapid_rating: Mapped[Optional[int]] = mapped_column(Integer)
    rapid_k: Mapped[Optional[int]] = mapped_column(Integer)
    blitz_rating: Mapped[Optional[int]] = mapped_column(Integer)
    blitz_k: Mapped[Optional[int]] = mapped_column(Integer)
    birth_year: Mapped[Optional[int]] = mapped_column(Integer)
    fide_title: Mapped[Optional[str]] = mapped_column(String(20))
