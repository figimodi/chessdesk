from datetime import date, datetime

from app.models.tournament import TournamentFormat, TournamentType
from app.schemas.common import ORMModel
from app.schemas.pairing import RoundRead, StandingEntry
from app.schemas.team import TeamRead, TeamStandingEntry
from pydantic import Field, field_validator, model_validator


ALLOWED_TIE_BREAKS = {
    "buchholz",
    "buchholz_cut1",
    "sonneborn_berger",
    "rating",
    "played_games",
    "direct_encounter",
    "wins_black",
    "individual_points",
    "head_to_head",
    "weighted_sonneborn",
}

INDIVIDUAL_DEFAULT_TIE_BREAKS = ["buchholz_cut1", "buchholz", "sonneborn_berger"]
TEAM_DEFAULT_TIE_BREAKS = ["individual_points", "head_to_head", "weighted_sonneborn"]


class TournamentBase(ORMModel):
    name: str = Field(min_length=2, max_length=120)
    type: TournamentType
    format: TournamentFormat = TournamentFormat.swiss
    time_control: str = Field(min_length=3, max_length=20)
    start_date: date
    end_date: date
    rounds_count: int = Field(ge=1, le=30)
    pairings_system: str = Field(default="swiss", min_length=3, max_length=20)
    tie_breaks: list[str] = Field(default_factory=lambda: INDIVIDUAL_DEFAULT_TIE_BREAKS.copy())
    is_elo_rated: bool = False
    max_players_per_team: int | None = Field(default=None, ge=1, le=100)
    boards_per_match: int | None = Field(default=None, ge=1, le=100)
    enforce_board_order: bool = False
    match_points_win: int | None = Field(default=None, ge=0, le=100)
    match_points_draw: int | None = Field(default=None, ge=0, le=100)
    match_points_loss: int | None = Field(default=None, ge=0, le=100)
    venue: str | None = Field(default=None, max_length=120)
    description: str | None = Field(default=None, max_length=1000)
    is_published: bool = False
    is_registration_closed: bool = False

    @field_validator("end_date")
    @classmethod
    def validate_dates(cls, value: date, info):
        start_date = info.data.get("start_date")
        if start_date and value < start_date:
            raise ValueError("La data di fine non puo essere precedente alla data di inizio.")
        return value

    @field_validator("tie_breaks")
    @classmethod
    def validate_tie_breaks(cls, value: list[str]):
        if not value:
            raise ValueError("At least one tie-break must be selected")
        normalized = [item.strip() for item in value if item.strip()]
        if len(normalized) != len(set(normalized)):
            raise ValueError("Tie-breaks must be unique")
        invalid = [item for item in normalized if item not in ALLOWED_TIE_BREAKS]
        if invalid:
            raise ValueError(f"Unsupported tie-breaks: {', '.join(invalid)}")
        return normalized

    @field_validator("match_points_draw")
    @classmethod
    def validate_draw_points(cls, value: int | None, info):
        win_points = info.data.get("match_points_win")
        if value is not None and win_points is not None and value > win_points:
            raise ValueError("draw points cannot exceed win points")
        return value

    @field_validator("match_points_loss")
    @classmethod
    def validate_loss_points(cls, value: int | None, info):
        draw_points = info.data.get("match_points_draw")
        if value is not None and draw_points is not None and value > draw_points:
            raise ValueError("loss points cannot exceed draw points")
        return value

    @model_validator(mode="after")
    def validate_team_settings(self):
        if self.type != TournamentType.team:
            return self

        required_values = {
            "max_players_per_team": self.max_players_per_team,
            "boards_per_match": self.boards_per_match,
            "match_points_win": self.match_points_win,
            "match_points_draw": self.match_points_draw,
            "match_points_loss": self.match_points_loss,
        }
        missing = [key for key, value in required_values.items() if value is None]
        if missing:
            raise ValueError(f"Missing team tournament settings: {', '.join(missing)}")
        if self.max_players_per_team < self.boards_per_match:
            raise ValueError("max_players_per_team must be greater than or equal to boards_per_match")
        return self


class TournamentCreate(TournamentBase):
    round_schedule: list[datetime] = Field(default_factory=list)

    @field_validator("round_schedule")
    @classmethod
    def validate_round_schedule(cls, value: list[datetime], info):
        if any(left > right for left, right in zip(value, value[1:])):
            raise ValueError("Le date dei turni devono essere in ordine cronologico.")
        start_date = info.data.get("start_date")
        end_date = info.data.get("end_date")
        if start_date and end_date:
          for scheduled_at in value:
              scheduled_date = scheduled_at.date()
              if scheduled_date < start_date or scheduled_date > end_date:
                  raise ValueError("Le date dei turni devono essere comprese tra la data di inizio e la data di fine del torneo.")
        return value


class TournamentUpdate(ORMModel):
    name: str | None = None
    type: TournamentType | None = None
    format: TournamentFormat | None = None
    time_control: str | None = None
    start_date: date | None = None
    end_date: date | None = None
    rounds_count: int | None = Field(default=None, ge=1, le=30)
    pairings_system: str | None = None
    tie_breaks: list[str] | None = None
    is_elo_rated: bool | None = None
    max_players_per_team: int | None = Field(default=None, ge=1, le=100)
    boards_per_match: int | None = Field(default=None, ge=1, le=100)
    enforce_board_order: bool | None = None
    match_points_win: int | None = Field(default=None, ge=0, le=100)
    match_points_draw: int | None = Field(default=None, ge=0, le=100)
    match_points_loss: int | None = Field(default=None, ge=0, le=100)
    venue: str | None = None
    description: str | None = None
    is_published: bool | None = None
    is_registration_closed: bool | None = None
    round_schedule: list[datetime] | None = None

    @model_validator(mode="after")
    def validate_update_dates(self):
        if self.start_date and self.end_date and self.end_date < self.start_date:
            raise ValueError("La data di fine non puo essere precedente alla data di inizio.")
        if self.round_schedule and any(left > right for left, right in zip(self.round_schedule, self.round_schedule[1:])):
            raise ValueError("Le date dei turni devono essere in ordine cronologico.")
        if self.round_schedule and self.start_date and self.end_date:
            for scheduled_at in self.round_schedule:
                scheduled_date = scheduled_at.date()
                if scheduled_date < self.start_date or scheduled_date > self.end_date:
                    raise ValueError("Le date dei turni devono essere comprese tra la data di inizio e la data di fine del torneo.")
        return self


class TournamentListItem(TournamentBase):
    id: int
    time_control_category: str
    bulletin_url: str | None = None
    players_count: int = 0
    teams_count: int = 0


class TournamentPlayerAssign(ORMModel):
    player_id: int
    team_id: int | None = None
    team_board_order: int | None = None
    seed_number: int | None = None
    initial_rating: int | None = None
    allow_late_join: bool = False


class TournamentPlayerAvailabilityUpdate(ORMModel):
    round_number: int
    is_available: bool


class TournamentPlayerStatusUpdate(ORMModel):
    is_active: bool


class TournamentPlayerRead(ORMModel):
    player_id: int
    tournament_id: int
    team_id: int | None = None
    team_board_order: int | None = None
    seed_number: int | None = None
    initial_rating: int | None = None
    start_round_number: int = 1
    is_active: bool = True
    full_name: str
    fide_id: str | None = None
    federation: str | None = None
    rating: int | None = None
    rapid_rating: int | None = None
    blitz_rating: int | None = None
    birth_year: int | None = None
    availability_by_round: list[bool] = []
    team_name: str | None = None


class TournamentDetail(TournamentListItem):
    rounds: list[RoundRead]
    standings: list[StandingEntry]
    team_standings: list[TeamStandingEntry] = []
    players: list[TournamentPlayerRead]
    teams: list[TeamRead]
