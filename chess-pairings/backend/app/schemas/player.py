from app.schemas.common import ORMModel
from pydantic import Field


class PlayerBase(ORMModel):
    full_name: str = Field(min_length=2, max_length=120)
    fide_id: str | None = None
    federation: str | None = Field(default=None, min_length=3, max_length=3)
    rating: int | None = Field(default=None, ge=0, le=4000)
    standard_k: int | None = Field(default=None, ge=0, le=100)
    rapid_rating: int | None = Field(default=None, ge=0, le=4000)
    rapid_k: int | None = Field(default=None, ge=0, le=100)
    blitz_rating: int | None = Field(default=None, ge=0, le=4000)
    blitz_k: int | None = Field(default=None, ge=0, le=100)
    birth_year: int | None = Field(default=None, ge=0, le=3000)
    fide_title: str | None = None


class PlayerCreate(PlayerBase):
    pass


class PlayerRead(PlayerBase):
    id: int


class FidePlayerSearchResult(ORMModel):
    fide_id: str
    full_name: str
    federation: str | None = None
    rating: int | None = None
    standard_rating: int | None = None
    standard_k: int | None = None
    rapid_rating: int | None = None
    rapid_k: int | None = None
    blitz_rating: int | None = None
    blitz_k: int | None = None
    birth_year: int | None = None
    fide_title: str | None = None
