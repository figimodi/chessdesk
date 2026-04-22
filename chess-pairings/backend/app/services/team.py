import secrets

from fastapi import HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models.team import Team, TeamAvailability, TeamLineup
from app.models.tournament import Tournament, TournamentPlayer
from app.schemas.team import TeamAvailabilityUpdate, TeamCreate, TeamLineupUpdate, TeamMemberRead, TeamMemberAssign, TeamMemberOrderUpdate, TeamRead, TeamStatusUpdate, TeamUpdate
from app.services.seeding import get_player_seed_numbers


async def get_teams(db: AsyncSession, tournament_id: int) -> list[Team]:
    result = await db.execute(
        select(Team)
        .where(Team.tournament_id == tournament_id)
        .options(
            selectinload(Team.tournament),
            selectinload(Team.members).selectinload(TournamentPlayer.player),
            selectinload(Team.members).selectinload(TournamentPlayer.availabilities),
            selectinload(Team.availabilities),
            selectinload(Team.lineups),
        )
        .order_by(Team.name.asc())
    )
    return list(result.scalars().all())


async def create_team(db: AsyncSession, tournament_id: int, data: TeamCreate) -> Team:
    existing_teams = await get_teams(db, tournament_id)
    team = Team(tournament_id=tournament_id, join_pin=_generate_join_pin(existing_teams), **data.model_dump())
    db.add(team)
    await db.commit()
    return await _reload_team(db, team.id)


async def update_team(db: AsyncSession, team: Team, data: TeamUpdate) -> Team:
    team.name = data.name
    await db.commit()
    return await _reload_team(db, team.id)


async def update_team_availability(db: AsyncSession, team: Team, data: TeamAvailabilityUpdate) -> Team:
    availability = next((item for item in team.availabilities if item.round_number == data.round_number), None)
    if availability is None:
        availability = TeamAvailability(team_id=team.id, round_number=data.round_number, is_available=data.is_available)
        db.add(availability)
    else:
        availability.is_available = data.is_available

    if data.is_available:
        team.is_active = True

    await db.commit()
    return await _reload_team(db, team.id)


async def update_team_status(db: AsyncSession, team: Team, data: TeamStatusUpdate) -> Team:
    team.is_active = data.is_active
    if not data.is_active:
        for round_number in range(1, team.tournament.rounds_count + 1):
            availability = next((item for item in team.availabilities if item.round_number == round_number), None)
            if availability is None:
                db.add(TeamAvailability(team_id=team.id, round_number=round_number, is_available=False))
            else:
                availability.is_available = False
    await db.commit()
    return await _reload_team(db, team.id)


async def update_team_lineup(db: AsyncSession, team: Team, data: TeamLineupUpdate) -> Team:
    member = next((item for item in team.members if item.player_id == data.player_id), None)
    if member is None:
        raise HTTPException(status_code=404, detail="Giocatore non trovato nella squadra")

    boards = team.tournament.boards_per_match or 0
    selected_count = 0
    for existing_member in team.members:
        existing_lineup = next(
            (item for item in team.lineups if item.tournament_player_id == existing_member.id and item.round_number == data.round_number),
            None,
        )
        default_selected = existing_member.is_active and data.round_number >= existing_member.start_round_number and (existing_member.team_board_order or 10**9) <= boards
        is_selected = existing_lineup.is_selected if existing_lineup is not None else default_selected
        if existing_member.player_id == data.player_id:
            is_selected = data.is_selected
        if is_selected:
            selected_count += 1

    if data.is_selected and selected_count > boards:
        raise HTTPException(status_code=409, detail=f"Puoi schierare al massimo {boards} giocatori per turno.")

    lineup = next(
        (item for item in team.lineups if item.tournament_player_id == member.id and item.round_number == data.round_number),
        None,
    )
    if lineup is None:
        lineup = TeamLineup(team_id=team.id, tournament_player_id=member.id, round_number=data.round_number, is_selected=data.is_selected)
        db.add(lineup)
    else:
        lineup.is_selected = data.is_selected

    await db.commit()
    return await _reload_team(db, team.id)


async def delete_team(db: AsyncSession, team: Team) -> None:
    for member in team.members:
        member.team_id = None
        member.team_board_order = None
    await db.delete(team)
    await db.commit()


async def assign_member(db: AsyncSession, tournament: Tournament, team: Team, data: TeamMemberAssign) -> Team:
    member = next((item for item in tournament.players if item.player_id == data.player_id), None)
    if member is None:
        raise HTTPException(status_code=404, detail="Giocatore non trovato nel torneo")
    if member.team_id == team.id:
        return team
    if team.tournament_id != tournament.id:
        raise HTTPException(status_code=409, detail="La squadra non appartiene al torneo")

    if tournament.max_players_per_team is not None:
        current_members = [item for item in tournament.players if item.team_id == team.id and item.player_id != member.player_id]
        if len(current_members) >= tournament.max_players_per_team:
            raise HTTPException(status_code=409, detail="La squadra ha raggiunto il numero massimo di giocatori.")

    previous_team_id = member.team_id
    member.team_id = team.id
    member.team_board_order = _next_board_order([item for item in tournament.players if item.team_id == team.id and item.player_id != member.player_id])
    await db.commit()
    if previous_team_id and previous_team_id != team.id:
        previous_team = await _reload_team(db, previous_team_id)
        if previous_team is not None:
            await _normalize_board_order(db, previous_team)
    refreshed = await _reload_team(db, team.id)
    if refreshed is not None:
        await _normalize_board_order(db, refreshed)
    return await _reload_team(db, team.id)


async def remove_member(db: AsyncSession, team: Team, player_id: int) -> Team:
    member = next((item for item in team.members if item.player_id == player_id), None)
    if member is None:
        raise HTTPException(status_code=404, detail="Giocatore non trovato nella squadra")

    member.team_id = None
    member.team_board_order = None
    await db.commit()

    refreshed = await _reload_team(db, team.id)
    await _normalize_board_order(db, refreshed)
    return await _reload_team(db, team.id)


async def reorder_members(db: AsyncSession, team: Team, data: TeamMemberOrderUpdate) -> Team:
    members_by_id = {member.player_id: member for member in team.members}
    if set(data.player_ids) != set(members_by_id):
        raise HTTPException(status_code=409, detail="La lista dei giocatori della squadra non e valida.")

    for index, player_id in enumerate(data.player_ids, start=1):
        members_by_id[player_id].team_board_order = index

    await db.commit()
    return await _reload_team(db, team.id)


async def get_team(db: AsyncSession, team_id: int) -> Team | None:
    return await _reload_team(db, team_id)


def serialize_team(team: Team) -> TeamRead:
    members = sorted(team.__dict__.get("members", []), key=lambda item: (item.team_board_order or 10**9, item.player.full_name))
    seed_numbers = get_player_seed_numbers(team.tournament)
    availability_map = {item.round_number: item.is_available for item in team.availabilities}
    availability_by_round = []
    for round_number in range(1, team.tournament.rounds_count + 1):
        availability_by_round.append(availability_map.get(round_number, team.is_active))
    return TeamRead(
        id=team.id,
        tournament_id=team.tournament_id,
        name=team.name,
        is_active=team.is_active,
        availability_by_round=availability_by_round,
        points=0,
        members_count=len(members),
        members=[serialize_team_member(member, seed_numbers) for member in members],
    )


def serialize_team_member(member: TournamentPlayer, seed_numbers: dict[int, int]) -> TeamMemberRead:
    ordered_members = sorted(member.team.members, key=lambda item: (item.team_board_order or 10**9, item.player.full_name))
    lineup_map = {
        item.round_number: item.is_selected
        for item in member.team.lineups
        if item.tournament_player_id == member.id
    }
    selected_by_round = []
    boards = member.tournament.boards_per_match or 0
    for round_number in range(1, member.tournament.rounds_count + 1):
        default_selected = member.is_active and round_number >= member.start_round_number and (
            len(ordered_members) <= boards or (member.team_board_order or 10**9) <= boards
        )
        selected_by_round.append(lineup_map.get(round_number, default_selected))

    return TeamMemberRead(
        player_id=member.player_id,
        full_name=member.player.full_name,
        federation=member.player.federation,
        seed_number=seed_numbers.get(member.player_id),
        rating=member.player.rating,
        rapid_rating=member.player.rapid_rating,
        blitz_rating=member.player.blitz_rating,
        birth_year=member.player.birth_year,
        team_board_order=member.team_board_order,
        selected_by_round=selected_by_round,
    )


async def _reload_team(db: AsyncSession, team_id: int) -> Team | None:
    result = await db.execute(
        select(Team)
        .where(Team.id == team_id)
        .execution_options(populate_existing=True)
        .options(
            selectinload(Team.tournament).selectinload(Tournament.players).selectinload(TournamentPlayer.player),
            selectinload(Team.members).selectinload(TournamentPlayer.player),
            selectinload(Team.members).selectinload(TournamentPlayer.availabilities),
            selectinload(Team.availabilities),
            selectinload(Team.lineups),
        )
    )
    return result.scalar_one_or_none()


async def _normalize_board_order(db: AsyncSession, team: Team) -> None:
    for index, member in enumerate(sorted(team.members, key=lambda item: (item.team_board_order or 10**9, item.player.full_name)), start=1):
        member.team_board_order = index
    await db.commit()


def _next_board_order(members: list[TournamentPlayer]) -> int:
    return max((member.team_board_order or 0 for member in members), default=0) + 1


def _generate_join_pin(teams: list[Team]) -> str:
    used_pins = {team.join_pin for team in teams}
    for _ in range(1000):
        candidate = f"{secrets.randbelow(10000):04d}"
        if candidate not in used_pins:
            return candidate
    raise HTTPException(status_code=500, detail="Non sono riuscito a generare un PIN squadra")
