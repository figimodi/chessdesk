import secrets
from pathlib import Path

from fastapi import HTTPException, UploadFile
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models.pairing import Pairing
from app.models.round import Round
from app.models.team import Team
from app.models.user import UserRole
from app.models.tournament import Tournament, TournamentPlayer, TournamentPlayerAvailability
from app.models.user import User
from app.schemas.team import PublicRegistrantIdentity, PublicTeamRegistrationCreate, PublicTeamRegistrationCreateResponse, PublicTeamRegistrationJoin, TeamMemberAssign, TeamRead
from app.schemas.tournament import (
    TournamentCreate,
    TournamentDetail,
    TournamentListItem,
    TournamentPublicRegistration,
    TournamentPlayerAssign,
    TournamentPlayerAvailabilityUpdate,
    TournamentPlayerRead,
    TournamentPlayerStatusUpdate,
    TournamentUpdate,
)
from app.services.files import FileStorageService
from app.services import player as player_service
from app.services import user as user_service
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


def _apply_tournament_scope(statement, user: User):
    if user.role == UserRole.admin:
        return statement
    return statement.where(Tournament.owner_id == user.id)


def can_view_tournament(tournament: Tournament, user: User | None) -> bool:
    if not tournament.is_private:
        return True
    if user is None:
        return False
    if user.role == UserRole.admin:
        return True
    return tournament.owner_id == user.id


def can_manage_tournament(tournament: Tournament, user: User | None) -> bool:
    if user is None:
        return False
    return user.role == UserRole.admin or tournament.owner_id == user.id


async def _get_tournament_unscoped(db: AsyncSession, tournament_id: int) -> Tournament | None:
    result = await db.execute(
        select(Tournament).where(Tournament.id == tournament_id).options(*_detail_options())
    )
    return result.scalar_one_or_none()


async def _get_tournament_unscoped_list(db: AsyncSession) -> list[Tournament]:
    result = await db.execute(
        select(Tournament)
        .options(selectinload(Tournament.players), selectinload(Tournament.teams))
        .order_by(Tournament.start_date.desc())
    )
    return list(result.scalars().all())


async def get_tournaments(db: AsyncSession, user: User) -> list[Tournament]:
    result = await db.execute(
        _apply_tournament_scope(
            select(Tournament)
            .options(
                selectinload(Tournament.players),
                selectinload(Tournament.teams),
            )
            .order_by(Tournament.start_date.desc()),
            user,
        )
    )
    return list(result.scalars().all())


async def get_tournament(db: AsyncSession, tournament_id: int, user: User) -> Tournament | None:
    result = await db.execute(
        _apply_tournament_scope(
            select(Tournament).where(Tournament.id == tournament_id).options(*_detail_options()),
            user,
        )
    )
    return result.scalar_one_or_none()


async def create_tournament(db: AsyncSession, data: TournamentCreate, owner: User) -> Tournament:
    payload = data.model_dump(exclude={"round_schedule", "tie_breaks"})
    if data.type in ("team", "quadriglia"):
        if payload.get("match_points_win") is None:
            payload["match_points_win"] = 2
        if payload.get("match_points_draw") is None:
            payload["match_points_draw"] = 1
        if payload.get("match_points_loss") is None:
            payload["match_points_loss"] = 0
        if data.type == "quadriglia":
            payload["max_players_per_team"] = 2
            payload["boards_per_match"] = 2
        _validate_team_tournament_limits(
            max_players_per_team=data.max_players_per_team,
            boards_per_match=data.boards_per_match,
            existing_team_member_counts=[],
        )
    tournament = Tournament(**payload, tie_breaks=_serialize_tie_breaks(data.tie_breaks), owner_id=owner.id)
    db.add(tournament)
    await db.flush()

    for index in range(data.rounds_count):
        scheduled_at = data.round_schedule[index] if index < len(data.round_schedule) else None
        db.add(Round(tournament_id=tournament.id, number=index + 1, scheduled_at=scheduled_at))

    await db.commit()
    return await get_tournament(db, tournament.id, owner)


async def update_tournament(
    db: AsyncSession, tournament: Tournament, data: TournamentUpdate, current_user: User
) -> Tournament:
    generated_rounds_count = sum(1 for round_model in tournament.rounds if round_model.pairings)
    if data.rounds_count is not None and data.rounds_count < generated_rounds_count:
        raise HTTPException(
            status_code=409,
            detail=f"Non puoi impostare meno di {generated_rounds_count} turni: sono gia stati generati/disputati {generated_rounds_count} turni.",
        )

    payload = data.model_dump(exclude_unset=True, exclude={"round_schedule", "tie_breaks"})
    if "owner_id" in payload:
        if current_user.role != UserRole.admin:
            raise HTTPException(status_code=403, detail="Solo un admin puo riassegnare il proprietario del torneo.")
        new_owner = await user_service.get_user_by_id(db, payload["owner_id"])
        if new_owner is None:
            raise HTTPException(status_code=404, detail="Utente proprietario non trovato")

    next_max_players_per_team = data.max_players_per_team if data.max_players_per_team is not None else tournament.max_players_per_team
    next_boards_per_match = data.boards_per_match if data.boards_per_match is not None else tournament.boards_per_match
    existing_team_member_counts = [len(team.members) for team in tournament.teams]
    if (data.type or tournament.type) in ("team", "quadriglia"):
        if (data.type or tournament.type) == "quadriglia":
            payload["max_players_per_team"] = 2
            payload["boards_per_match"] = 2
            if data.tie_breaks is not None:
                data.tie_breaks = ["head_to_head"]
        _validate_team_tournament_limits(
            max_players_per_team=next_max_players_per_team,
            boards_per_match=next_boards_per_match,
            existing_team_member_counts=existing_team_member_counts,
        )

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
    return await _get_tournament_unscoped(db, tournament.id)


def _validate_team_tournament_limits(
    *,
    max_players_per_team: int | None,
    boards_per_match: int | None,
    existing_team_member_counts: list[int],
) -> None:
    if max_players_per_team is not None and boards_per_match is not None and boards_per_match > max_players_per_team:
        raise HTTPException(
            status_code=409,
            detail="I giocatori schierati per incontro non possono superare il numero massimo di giocatori per squadra.",
        )

    if max_players_per_team is not None:
        current_max_members = max(existing_team_member_counts, default=0)
        if current_max_members > max_players_per_team:
            raise HTTPException(
                status_code=409,
                detail=f"Non puoi impostare meno di {current_max_members} giocatori per squadra: esiste gia una squadra con {current_max_members} giocatori.",
            )


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
    refreshed = await _get_tournament_unscoped(db, tournament.id)
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


async def register_public_player(
    db: AsyncSession, tournament: Tournament, data: TournamentPublicRegistration
) -> TournamentPlayer:
    if tournament.is_registration_closed:
        raise HTTPException(status_code=409, detail="Le iscrizioni del torneo sono chiuse")

    if data.fide_id:
        existing_fide_entry = next(
            (
                entry
                for entry in tournament.players
                if entry.player.fide_id and entry.player.fide_id == data.fide_id.strip()
            ),
            None,
        )
        if existing_fide_entry is not None:
            raise HTTPException(status_code=409, detail="Il giocatore risulta gia iscritto a questo torneo")

        player = await player_service.import_player_from_fide(db, data.fide_id)
    else:
        full_name = f"{(data.last_name or '').strip()}, {(data.first_name or '').strip()}"
        existing_manual_entry = next(
            (
                entry
                for entry in tournament.players
                if entry.player.full_name.strip().lower() == full_name.lower()
            ),
            None,
        )
        if existing_manual_entry is not None:
            raise HTTPException(status_code=409, detail="Esiste gia un giocatore con lo stesso nome in questo torneo")

        player = await player_service.create_public_manual_player(
            db,
            first_name=data.first_name or "",
            last_name=data.last_name or "",
        )

    return await assign_player(
        db,
        tournament,
        TournamentPlayerAssign(player_id=player.id),
    )


async def register_public_team(
    db: AsyncSession, tournament: Tournament, data: PublicTeamRegistrationCreate
) -> PublicTeamRegistrationCreateResponse:
    tournament_id = tournament.id
    _ensure_public_team_registration_allowed(tournament)

    if any(team.name.strip().lower() == data.team_name.strip().lower() for team in tournament.teams):
        raise HTTPException(status_code=409, detail="Esiste gia una squadra con questo nome")

    join_pin = _generate_team_join_pin(tournament)
    team = Team(tournament_id=tournament_id, name=data.team_name.strip(), join_pin=join_pin)
    db.add(team)
    await db.commit()

    db.expire_all()
    refreshed_tournament = await _get_tournament_unscoped(db, tournament_id)
    created_team = await team_service.get_team(db, team.id)
    if created_team is None:
        raise HTTPException(status_code=500, detail="Non sono riuscito a creare la squadra")

    processed_player_ids: set[int] = set()

    for player_id in data.teammate_player_ids:
        if player_id in processed_player_ids:
            continue
        existing_entry = next((entry for entry in refreshed_tournament.players if entry.player_id == player_id), None)
        if existing_entry is None:
            raise HTTPException(status_code=404, detail="Giocatore non trovato nel torneo")
        if existing_entry.team_id is not None:
            raise HTTPException(status_code=409, detail="Uno dei giocatori selezionati appartiene gia a una squadra")
        db.expire_all()
        refreshed_tournament = await _get_tournament_unscoped(db, tournament_id)
        created_team_model = next(team for team in refreshed_tournament.teams if team.id == created_team.id)
        created_team = await team_service.assign_member(
            db,
            refreshed_tournament,
            created_team_model,
            TeamMemberAssign(player_id=player_id),
        )
        processed_player_ids.add(player_id)

    for fide_id in data.teammate_fide_ids:
        db.expire_all()
        refreshed_tournament = await _get_tournament_unscoped(db, tournament_id)
        teammate_entry = await _resolve_public_registration_entry(
            db,
            refreshed_tournament,
            PublicRegistrantIdentity(fide_id=fide_id),
        )
        if teammate_entry.player_id in processed_player_ids:
            continue
        if teammate_entry.team_id is not None:
            raise HTTPException(status_code=409, detail="Uno dei giocatori selezionati appartiene gia a una squadra")
        db.expire_all()
        refreshed_tournament = await _get_tournament_unscoped(db, tournament_id)
        created_team_model = next(team for team in refreshed_tournament.teams if team.id == created_team.id)
        created_team = await team_service.assign_member(
            db,
            refreshed_tournament,
            created_team_model,
            TeamMemberAssign(player_id=teammate_entry.player_id),
        )
        processed_player_ids.add(teammate_entry.player_id)

    for manual_identity in data.teammate_manual_entries:
        refreshed_tournament = await _get_tournament_unscoped(db, tournament_id)
        teammate_entry = await _resolve_public_registration_entry(
            db,
            refreshed_tournament,
            manual_identity,
        )
        if teammate_entry.player_id in processed_player_ids:
            continue
        if teammate_entry.team_id is not None:
            raise HTTPException(status_code=409, detail="Uno dei giocatori selezionati appartiene gia a una squadra")
        db.expire_all()
        refreshed_tournament = await _get_tournament_unscoped(db, tournament_id)
        created_team_model = next(team for team in refreshed_tournament.teams if team.id == created_team.id)
        created_team = await team_service.assign_member(
            db,
            refreshed_tournament,
            created_team_model,
            TeamMemberAssign(player_id=teammate_entry.player_id),
        )
        processed_player_ids.add(teammate_entry.player_id)

    db.expire_all()
    refreshed_tournament = await _get_tournament_unscoped(db, tournament_id)
    members_count = sum(1 for player in refreshed_tournament.players if player.team_id == created_team.id)

    return PublicTeamRegistrationCreateResponse(
        team_id=created_team.id,
        team_name=created_team.name,
        pin=join_pin,
        members_count=members_count,
    )


async def join_public_team(
    db: AsyncSession, tournament: Tournament, data: PublicTeamRegistrationJoin
) -> TournamentPlayer:
    tournament_id = tournament.id
    _ensure_public_team_registration_allowed(tournament)
    team = next((item for item in tournament.teams if item.id == data.team_id), None)
    if team is None:
        raise HTTPException(status_code=404, detail="Squadra non trovata")
    if team.join_pin != data.pin.strip():
        raise HTTPException(status_code=409, detail="PIN squadra non valido")

    entry = await _resolve_public_registration_entry(db, tournament, data.registrant)
    if entry.team_id is not None:
        raise HTTPException(status_code=409, detail="Il giocatore risulta gia assegnato a una squadra")

    db.expire_all()
    refreshed_tournament = await _get_tournament_unscoped(db, tournament_id)
    refreshed_team = next(item for item in refreshed_tournament.teams if item.id == data.team_id)
    await team_service.assign_member(
        db,
        refreshed_tournament,
        refreshed_team,
        TeamMemberAssign(player_id=entry.player_id),
    )
    db.expire_all()
    refreshed_tournament = await _get_tournament_unscoped(db, tournament_id)
    return next(item for item in refreshed_tournament.players if item.player_id == entry.player_id)


def _ensure_public_team_registration_allowed(tournament: Tournament) -> None:
    if tournament.type.value not in ("team", "quadriglia"):
        raise HTTPException(status_code=409, detail="Questa funzionalita e disponibile solo per i tornei a squadre")
    if tournament.is_registration_closed:
        raise HTTPException(status_code=409, detail="Le iscrizioni del torneo sono chiuse")


async def _resolve_public_registration_entry(
    db: AsyncSession,
    tournament: Tournament,
    identity: TournamentPublicRegistration | PublicRegistrantIdentity,
) -> TournamentPlayer:
    if identity.fide_id:
        existing_fide_entry = next(
            (
                entry
                for entry in tournament.players
                if entry.player.fide_id and entry.player.fide_id == identity.fide_id.strip()
            ),
            None,
        )
        if existing_fide_entry is not None:
            return existing_fide_entry
        player = await player_service.import_player_from_fide(db, identity.fide_id)
    else:
        full_name = f"{(identity.last_name or '').strip()}, {(identity.first_name or '').strip()}"
        existing_manual_entry = next(
            (
                entry
                for entry in tournament.players
                if entry.player.full_name.strip().lower() == full_name.lower()
            ),
            None,
        )
        if existing_manual_entry is not None:
            return existing_manual_entry
        player = await player_service.create_public_manual_player(
            db,
            first_name=identity.first_name or "",
            last_name=identity.last_name or "",
        )

    return await assign_player(
        db,
        tournament,
        TournamentPlayerAssign(player_id=player.id),
    )


def _generate_team_join_pin(tournament: Tournament) -> str:
    used_pins = {team.join_pin for team in tournament.teams}
    for _ in range(1000):
        candidate = f"{secrets.randbelow(10000):04d}"
        if candidate not in used_pins:
            return candidate
    raise HTTPException(status_code=500, detail="Non sono riuscito a generare un PIN squadra")


async def remove_player(
    db: AsyncSession, tournament: Tournament, player_id: int
) -> None:
    if any(round_model.pairings for round_model in tournament.rounds):
        raise HTTPException(
            status_code=409,
            detail="Non puoi rimuovere partecipanti dopo che e' stato generato almeno un turno.",
        )

    entry = next((item for item in tournament.players if item.player_id == player_id), None)
    if entry is None:
        raise HTTPException(status_code=404, detail="Giocatore non trovato nel torneo")

    await db.delete(entry)
    await db.commit()


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

    participants_count = len(tournament.teams) if tournament.type in ("team", "quadriglia") else len(tournament.players)
    if participants_count < 2:
        raise HTTPException(
            status_code=409,
            detail="Servono almeno 2 partecipanti per chiudere le iscrizioni.",
        )

    max_supported_rounds = max(participants_count - 1, 0)
    if tournament.rounds_count > max_supported_rounds:
        label = "squadre" if tournament.type in ("team", "quadriglia") else "giocatori"
        raise HTTPException(
            status_code=409,
            detail=(
                f"Con {participants_count} {label} puoi disputare al massimo {max_supported_rounds} turni. "
                f"Riduci il numero di turni oppure aggiungi altri partecipanti prima di chiudere le iscrizioni."
            ),
        )

    tournament.is_registration_closed = True
    await db.commit()
    return await _get_tournament_unscoped(db, tournament.id)


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
    return await _get_tournament_unscoped(db, tournament.id)


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
        raise HTTPException(status_code=404, detail="Giocatore non trovato nel torneo")

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
    refreshed = await _get_tournament_unscoped(db, tournament.id)
    return next(item for item in refreshed.players if item.player_id == player_id)


async def update_player_status(
    db: AsyncSession,
    tournament: Tournament,
    player_id: int,
    data: TournamentPlayerStatusUpdate,
) -> TournamentPlayer:
    entry = next((item for item in tournament.players if item.player_id == player_id), None)
    if entry is None:
        raise HTTPException(status_code=404, detail="Giocatore non trovato nel torneo")

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
    refreshed = await _get_tournament_unscoped(db, tournament.id)
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


def serialize_tournament_list_item(
    tournament: Tournament, user: User | None = None
) -> TournamentListItem:
    is_team_tournament = tournament.type in ("team", "quadriglia")
    raw_max_players_per_team = tournament.max_players_per_team if tournament.max_players_per_team is not None else 6
    raw_boards_per_match = tournament.boards_per_match if tournament.boards_per_match is not None else 4
    safe_max_players_per_team = max(raw_max_players_per_team, raw_boards_per_match) if is_team_tournament else None
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
        max_players_per_team=safe_max_players_per_team,
        boards_per_match=raw_boards_per_match if is_team_tournament else None,
        enforce_board_order=tournament.enforce_board_order,
        match_points_win=(tournament.match_points_win if tournament.match_points_win is not None else 2) if is_team_tournament else None,
        match_points_draw=(tournament.match_points_draw if tournament.match_points_draw is not None else 1) if is_team_tournament else None,
        match_points_loss=(tournament.match_points_loss if tournament.match_points_loss is not None else 0) if is_team_tournament else None,
        time_control_category=get_time_control_category(tournament.time_control),
        venue=tournament.venue,
        description=tournament.description,
        is_published=tournament.is_published,
        is_private=tournament.is_private,
        is_registration_closed=tournament.is_registration_closed,
        bulletin_url=FileStorageService().public_url(tournament.bulletin_path),
        players_count=len(tournament.players),
        teams_count=len(tournament.teams),
        can_manage=can_manage_tournament(tournament, user),
        owner_id=tournament.owner_id,
    )


async def serialize_tournament_detail(
    db: AsyncSession, tournament: Tournament, user: User | None = None
) -> TournamentDetail:
    standings = StandingsService().build_standings(tournament)
    team_standings = TeamStandingsService().build_standings(tournament) if tournament.type in ("team", "quadriglia") else []
    teams = await team_service.get_teams(db, tournament.id)

    return TournamentDetail(
        **serialize_tournament_list_item(tournament, user).model_dump(),
        rounds=[serialize_round(item) for item in sorted(tournament.rounds, key=lambda item: item.number)],
        standings=standings,
        team_standings=team_standings,
        players=[serialize_tournament_player(entry) for entry in tournament.players],
        teams=[team_service.serialize_team(team) for team in teams],
    )
