from app.schemas.common import ORMModel
from pydantic import Field, model_validator


class TeamCreate(ORMModel):
    name: str = Field(min_length=2, max_length=120)


class TeamUpdate(ORMModel):
    name: str = Field(min_length=2, max_length=120)


class TeamMemberAssign(ORMModel):
    player_id: int


class TeamMemberOrderUpdate(ORMModel):
    player_ids: list[int]


class TeamAvailabilityUpdate(ORMModel):
    round_number: int
    is_available: bool


class TeamStatusUpdate(ORMModel):
    is_active: bool


class TeamLineupUpdate(ORMModel):
    player_id: int
    round_number: int
    is_selected: bool


class TeamMemberRead(ORMModel):
    player_id: int
    full_name: str
    federation: str | None = None
    seed_number: int | None = None
    rating: int | None = None
    rapid_rating: int | None = None
    blitz_rating: int | None = None
    birth_year: int | None = None
    team_board_order: int | None = None
    selected_by_round: list[bool] = []


class TeamRead(TeamCreate):
    id: int
    tournament_id: int
    is_active: bool = True
    availability_by_round: list[bool] = []
    points: float = 0
    members_count: int = 0
    members: list[TeamMemberRead] = []


class TeamStandingEntry(ORMModel):
    team_id: int
    name: str
    match_points: float
    individual_points: float
    head_to_head_applies: bool = False
    head_to_head_match_points: float = 0
    head_to_head_individual_points: float = 0
    weighted_sonneborn: float = 0


class PublicRegistrantIdentity(ORMModel):
    fide_id: str | None = Field(default=None, min_length=4, max_length=20)
    first_name: str | None = Field(default=None, min_length=2, max_length=60)
    last_name: str | None = Field(default=None, min_length=2, max_length=60)

    @model_validator(mode="after")
    def validate_registration_payload(self):
        has_fide = bool(self.fide_id)
        has_manual_identity = bool(self.first_name and self.last_name)
        if has_fide == has_manual_identity:
            raise ValueError("Provide either a fide_id or first_name and last_name")
        return self


class PublicTeamRegistrationCreate(ORMModel):
    team_name: str = Field(min_length=2, max_length=120)
    captain: PublicRegistrantIdentity
    teammate_player_ids: list[int] = []
    teammate_fide_ids: list[str] = []
    teammate_manual_entries: list[PublicRegistrantIdentity] = []


class PublicTeamRegistrationJoin(ORMModel):
    team_id: int
    pin: str = Field(min_length=4, max_length=4)
    registrant: PublicRegistrantIdentity


class PublicTeamRegistrationCreateResponse(ORMModel):
    team_id: int
    team_name: str
    pin: str
    members_count: int
