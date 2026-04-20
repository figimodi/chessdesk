from datetime import datetime

from app.models.pairing import PairingResult
from app.models.tournament import RoundStatus
from app.schemas.common import ORMModel


class PairingRead(ORMModel):
    id: int
    match_number: int | None = None
    board_number: int
    white_player_id: int
    black_player_id: int | None = None
    white_player_name: str
    black_player_name: str | None = None
    white_team_id: int | None = None
    black_team_id: int | None = None
    white_team_name: str | None = None
    black_team_name: str | None = None
    result: PairingResult
    white_points: float
    black_points: float
    is_bye: bool


class RoundRead(ORMModel):
    id: int
    number: int
    scheduled_at: datetime | None = None
    status: RoundStatus
    pairings: list[PairingRead]


class PairingResultUpdate(ORMModel):
    result: PairingResult


class PairingCreateResponse(ORMModel):
    round: RoundRead
    standings: list["StandingEntry"]


class StandingEntry(ORMModel):
    player_id: int
    full_name: str
    federation: str | None = None
    team_board_order: int | None = None
    seed_number: int | None = None
    rating: int | None = None
    rapid_rating: int | None = None
    blitz_rating: int | None = None
    team_id: int | None = None
    team_name: str | None = None
    points: float
    buchholz: float
    buchholz_cut1: float
    sonneborn_berger: float
    average_opponent_rating: int | None = None
    performance_rating: int | None = None
    elo_change: float | None = None
    played_games: int
    wins: int
    black_wins: int


PairingCreateResponse.model_rebuild()
