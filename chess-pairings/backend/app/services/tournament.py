from pathlib import Path

from fastapi import HTTPException, UploadFile
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models.pairing import Pairing
from app.models.round import Round
from app.models.team import Team
from app.models.tournament import Tournament, TournamentPlayer, TournamentPlayerAvailability
from app.schemas.team import TeamRead
from app.schemas.tournament import (
    TournamentCreate,
    TournamentDetail,
    TournamentListItem,
    TournamentPlayerAssign,
    TournamentPlayerAvailabilityUpdate,
    TournamentPlayerRead,
    TournamentPlayerStatusUpdate,
    TournamentUpdate,
)
from app.services.files import FileStorageService
from app.services.seeding import get_player_seed_numbers
from app.services.standings import StandingsService
from app.services.team_standings import TeamStandingsService
from app.services import team as team_service
from app.services.time_control import get_time_control_category


def _serialize_tie_breaks(value: list[str]) -> str:
    return ",".join(value)


def _deserialize_tie_breaks(value: str | None) -> list[str]:
    if not value:
        return ["buchholz_cut1", "buchholz", "sonneborn_berger"]
    return [item for item in value.split(",") if item]


def _detail_options():
    return [
        selectinload(Tournament.players).selectinload(TournamentPlayer.player),
        selectinload(Tournament.players).selectinload(TournamentPlayer.team),
        selectinload(Tournament.players).selectinload(TournamentPlayer.availabilities),
        selectinload(Tournament.rounds)
        .selectinload(Round.pairings)
        .selectinload(Pairing.white_player),
        selectinload(Tournament.rounds)
        .selectinload(Round.pairings)
        .selectinload(Pairing.black_player),
        selectinload(Tournament.teams).selectinload(Team.members).selectinload(TournamentPlayer.player),
        selectinload(Tournament.teams).selectinload(Team.members).selectinload(TournamentPlayer.availabilities),
        selectinload(Tournament.teams).selectinload(Team.availabilities),
        selectinload(Tournament.teams).selectinload(Team.lineups),
    ]


async def get_tournaments(db: AsyncSession) -> list[Tournament]:
    result = await db.execute(
        select(Tournament)
        .options(
            selectinload(Tournament.players),
            selectinload(Tournament.teams),
        )
        .order_by(Tournament.start_date.desc())
    )
    return list(result.scalars().all())


async def get_tournament(db: AsyncSession, tournament_id: int) -> Tournament | None:
    result = await db.execute(
        select(Tournament).where(Tournament.id == tournament_id).options(*_detail_options())
    )
    return result.scalar_one_or_none()


async def create_tournament(db: AsyncSession, data: TournamentCreate) -> Tournament:
    payload = data.model_dump(exclude={"round_schedule", "tie_breaks"})
    if data.type == "team":
        if payload.get("match_points_win") is None:
            payload["match_points_win"] = 2
        if payload.get("match_points_draw") is None:
            payload["match_points_draw"] = 1
        if payload.get("match_points_loss") is None:
            payload["match_points_loss"] = 0
    tournament = Tournament(**payload, tie_breaks=_serialize_tie_breaks(data.tie_breaks))
    db.add(tournament)
    await db.flush()

    for index in range(data.rounds_count):
        scheduled_at = data.round_schedule[index] if index < len(data.round_schedule) else None
        db.add(Round(tournament_id=tournament.id, number=index + 1, scheduled_at=scheduled_at))

    await db.commit()
    return await get_tournament(db, tournament.id)


async def update_tournament(
    db: AsyncSession, tournament: Tournament, data: TournamentUpdate
) -> Tournament:
    generated_rounds_count = sum(1 for round_model in tournament.rounds if round_model.pairings)
    if data.rounds_count is not None and data.rounds_count < generated_rounds_count:
        raise HTTPException(
            status_code=409,
            detail=f"Non puoi impostare meno di {generated_rounds_count} turni: sono gia stati generati/disputati {generated_rounds_count} turni.",
        )

    payload = data.model_dump(exclude_unset=True, exclude={"round_schedule", "tie_breaks"})
    for key, value in payload.items():
        setattr(tournament, key, value)

    if data.tie_breaks is not None:
        tournament.tie_breaks = _serialize_tie_breaks(data.tie_breaks)

    if data.round_schedule is not None:
        for round_model in tournament.rounds:
            round_index = round_model.number - 1
            round_model.scheduled_at = (
                data.round_schedule[round_index]
                if round_index < len(data.round_schedule)
                else None
            )

    await db.commit()
    return await get_tournament(db, tournament.id)


async def delete_tournament(db: AsyncSession, tournament: Tournament) -> None:
    await db.delete(tournament)
    await db.commit()


async def assign_player(
    db: AsyncSession, tournament: Tournament, data: TournamentPlayerAssign
) -> TournamentPlayer:
    if tournament.is_registration_closed:
        if not data.allow_late_join:
            next_round_number = next(
                (round_model.number for round_model in sorted(tournament.rounds, key=lambda item: item.number) if not round_model.pairings),
                tournament.rounds_count + 1,
            )
            raise HTTPException(
                status_code=409,
                detail=f"Le iscrizioni del torneo sono chiuse. Puoi aggiungere questo giocatore solo dal turno {next_round_number}.",
            )

    existing = next(
        (item for item in tournament.players if item.player_id == data.player_id),
        None,
    )
    if existing is not None:
        return existing

    next_round_number = next(
        (round_model.number for round_model in sorted(tournament.rounds, key=lambda item: item.number) if not round_model.pairings),
        tournament.rounds_count + 1,
    )

    entry = TournamentPlayer(
        tournament_id=tournament.id,
        player_id=data.player_id,
        team_id=data.team_id,
        team_board_order=data.team_board_order,
        seed_number=data.seed_number,
        initial_rating=data.initial_rating,
        start_round_number=next_round_number if tournament.is_registration_closed and data.allow_late_join else 1,
    )
    db.add(entry)
    await db.commit()
    refreshed = await get_tournament(db, tournament.id)
    matched = next(
        (item for item in refreshed.players if item.player_id == data.player_id),
        None,
    )
    if matched is None:
        result = await db.execute(
            select(TournamentPlayer)
            .where(
                TournamentPlayer.tournament_id == tournament.id,
                TournamentPlayer.player_id == data.player_id,
            )
            .options(
                selectinload(TournamentPlayer.player),
                selectinload(TournamentPlayer.team),
            )
        )
        matched = result.scalar_one()
    return matched


async def upload_bulletin(
    db: AsyncSession, tournament: Tournament, upload: UploadFile
) -> dict:
    storage = FileStorageService()
    tournament.bulletin_path = await storage.save_bulletin(upload)
    await db.commit()
    return {"bulletinUrl": storage.public_url(tournament.bulletin_path)}


async def close_registration(db: AsyncSession, tournament: Tournament) -> Tournament:
    if tournament.is_registration_closed:
        return tournament

    participants_count = len(tournament.teams) if tournament.type == "team" else len(tournament.players)
    if participants_count < 2:
        raise HTTPException(
            status_code=409,
            detail="Servono almeno 2 partecipanti per chiudere le iscrizioni.",
        )

    max_supported_rounds = max(participants_count - 1, 0)
    if tournament.rounds_count > max_supported_rounds:
        label = "squadre" if tournament.type == "team" else "giocatori"
        raise HTTPException(
            status_code=409,
            detail=(
                f"Con {participants_count} {label} puoi disputare al massimo {max_supported_rounds} turni. "
                f"Riduci il numero di turni oppure aggiungi altri partecipanti prima di chiudere le iscrizioni."
            ),
        )

    tournament.is_registration_closed = True
    await db.commit()
    return await get_tournament(db, tournament.id)


async def reopen_registration(db: AsyncSession, tournament: Tournament) -> Tournament:
    if not tournament.is_registration_closed:
        return tournament

    generated_rounds = [round_model for round_model in tournament.rounds if round_model.pairings]
    if generated_rounds:
        raise HTTPException(
            status_code=409,
            detail="Non puoi riaprire le iscrizioni dopo che è già stato generato almeno un turno.",
        )

    tournament.is_registration_closed = False
    await db.commit()
    return await get_tournament(db, tournament.id)


def serialize_tournament_player(entry: TournamentPlayer) -> TournamentPlayerRead:
    seed_numbers = get_player_seed_numbers(entry.tournament)
    availability_by_round = []
    availability_map = {item.round_number: item.is_available for item in entry.availabilities}
    for round_number in range(1, entry.tournament.rounds_count + 1):
        default_available = round_number >= entry.start_round_number and entry.is_active
        availability_by_round.append(availability_map.get(round_number, default_available))

    return TournamentPlayerRead(
        player_id=entry.player_id,
        tournament_id=entry.tournament_id,
        team_id=entry.team_id,
        team_board_order=entry.team_board_order,
        seed_number=seed_numbers.get(entry.player_id),
        initial_rating=entry.initial_rating,
        start_round_number=entry.start_round_number,
        is_active=entry.is_active,
        full_name=entry.player.full_name,
        fide_id=entry.player.fide_id,
        federation=entry.player.federation,
        rating=entry.player.rating,
        rapid_rating=entry.player.rapid_rating,
        blitz_rating=entry.player.blitz_rating,
        birth_year=entry.player.birth_year,
        availability_by_round=availability_by_round,
        team_name=entry.team.name if entry.team else None,
    )


async def update_player_availability(
    db: AsyncSession,
    tournament: Tournament,
    player_id: int,
    data: TournamentPlayerAvailabilityUpdate,
) -> TournamentPlayer:
    entry = next((item for item in tournament.players if item.player_id == player_id), None)
    if entry is None:
        raise HTTPException(status_code=404, detail="Player not found in tournament")

    availability = next(
        (item for item in entry.availabilities if item.round_number == data.round_number),
        None,
    )

    if availability is None:
        availability = TournamentPlayerAvailability(
            tournament_player_id=entry.id,
            round_number=data.round_number,
            is_available=data.is_available,
        )
        db.add(availability)
    else:
        availability.is_available = data.is_available

    if data.is_available:
        entry.is_active = True

    await db.commit()
    refreshed = await get_tournament(db, tournament.id)
    return next(item for item in refreshed.players if item.player_id == player_id)


async def update_player_status(
    db: AsyncSession,
    tournament: Tournament,
    player_id: int,
    data: TournamentPlayerStatusUpdate,
) -> TournamentPlayer:
    entry = next((item for item in tournament.players if item.player_id == player_id), None)
    if entry is None:
        raise HTTPException(status_code=404, detail="Player not found in tournament")

    entry.is_active = data.is_active
    if not data.is_active:
        for round_number in range(1, tournament.rounds_count + 1):
            availability = next((item for item in entry.availabilities if item.round_number == round_number), None)
            if availability is None:
                db.add(
                    TournamentPlayerAvailability(
                        tournament_player_id=entry.id,
                        round_number=round_number,
                        is_available=False,
                    )
                )
            else:
                availability.is_available = False
    await db.commit()
    refreshed = await get_tournament(db, tournament.id)
    return next(item for item in refreshed.players if item.player_id == player_id)


def serialize_round(round_model: Round) -> dict:
    return {
        "id": round_model.id,
        "number": round_model.number,
        "scheduled_at": round_model.scheduled_at,
        "status": round_model.status,
        "pairings": [
            {
                "id": pairing.id,
                "match_number": pairing.match_number,
                "board_number": pairing.board_number,
                "white_player_id": pairing.white_player_id,
                "black_player_id": pairing.black_player_id,
                "white_player_name": pairing.white_player.full_name,
                "black_player_name": pairing.black_player.full_name if pairing.black_player else None,
                "white_team_id": next((entry.team_id for entry in round_model.tournament.players if entry.player_id == pairing.white_player_id), None),
                "black_team_id": next((entry.team_id for entry in round_model.tournament.players if entry.player_id == pairing.black_player_id), None) if pairing.black_player_id else None,
                "white_team_name": next((entry.team.name for entry in round_model.tournament.players if entry.player_id == pairing.white_player_id and entry.team), None),
                "black_team_name": next((entry.team.name for entry in round_model.tournament.players if entry.player_id == pairing.black_player_id and entry.team), None) if pairing.black_player_id else None,
                "result": pairing.result,
                "white_points": float(pairing.white_points),
                "black_points": float(pairing.black_points),
                "is_bye": pairing.is_bye,
            }
            for pairing in sorted(round_model.pairings, key=lambda item: (item.match_number or 10**9, item.board_number, item.id))
        ],
    }


def serialize_tournament_list_item(tournament: Tournament) -> TournamentListItem:
    is_team_tournament = tournament.type == "team"
    return TournamentListItem(
        id=tournament.id,
        name=tournament.name,
        type=tournament.type,
        format=tournament.format,
        time_control=tournament.time_control,
        start_date=tournament.start_date,
        end_date=tournament.end_date,
        rounds_count=tournament.rounds_count,
        pairings_system=tournament.pairings_system,
        tie_breaks=_deserialize_tie_breaks(tournament.tie_breaks),
        is_elo_rated=tournament.is_elo_rated,
        max_players_per_team=(tournament.max_players_per_team if tournament.max_players_per_team is not None else 6) if is_team_tournament else None,
        boards_per_match=(tournament.boards_per_match if tournament.boards_per_match is not None else 4) if is_team_tournament else None,
        enforce_board_order=tournament.enforce_board_order,
        match_points_win=(tournament.match_points_win if tournament.match_points_win is not None else 2) if is_team_tournament else None,
        match_points_draw=(tournament.match_points_draw if tournament.match_points_draw is not None else 1) if is_team_tournament else None,
        match_points_loss=(tournament.match_points_loss if tournament.match_points_loss is not None else 0) if is_team_tournament else None,
        time_control_category=get_time_control_category(tournament.time_control),
        venue=tournament.venue,
        description=tournament.description,
        is_published=tournament.is_published,
        is_registration_closed=tournament.is_registration_closed,
        bulletin_url=FileStorageService().public_url(tournament.bulletin_path),
        players_count=len(tournament.players),
        teams_count=len(tournament.teams),
    )


async def serialize_tournament_detail(
    db: AsyncSession, tournament: Tournament
) -> TournamentDetail:
    standings = StandingsService().build_standings(tournament)
    team_standings = TeamStandingsService().build_standings(tournament) if tournament.type == "team" else []
    teams = await team_service.get_teams(db, tournament.id)

    return TournamentDetail(
        **serialize_tournament_list_item(tournament).model_dump(),
        rounds=[serialize_round(item) for item in sorted(tournament.rounds, key=lambda item: item.number)],
        standings=standings,
        team_standings=team_standings,
        players=[serialize_tournament_player(entry) for entry in tournament.players],
        teams=[team_service.serialize_team(team) for team in teams],
    )
