from fastapi import APIRouter, Depends
from fastapi import HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_tournament_or_404
from app.core.database import get_db
from app.schemas.team import TeamAvailabilityUpdate, TeamCreate, TeamLineupUpdate, TeamMemberAssign, TeamMemberOrderUpdate, TeamRead, TeamStatusUpdate, TeamUpdate
from app.services import team as team_service

router = APIRouter(tags=["teams"])


@router.get("/api/v1/admin/tournaments/{tournament_id}/teams/", response_model=list[TeamRead])
async def get_teams(
    tournament=Depends(get_tournament_or_404), db: AsyncSession = Depends(get_db)
):
    teams = await team_service.get_teams(db, tournament.id)
    return [team_service.serialize_team(team) for team in teams]


@router.post("/api/v1/admin/tournaments/{tournament_id}/teams/", response_model=TeamRead, status_code=201)
async def create_team(
    data: TeamCreate,
    tournament=Depends(get_tournament_or_404),
    db: AsyncSession = Depends(get_db),
):
    team = await team_service.create_team(db, tournament.id, data)
    return team_service.serialize_team(team)


@router.put("/api/v1/admin/tournaments/{tournament_id}/teams/{team_id}", response_model=TeamRead)
async def update_team(
    team_id: int,
    data: TeamUpdate,
    tournament=Depends(get_tournament_or_404),
    db: AsyncSession = Depends(get_db),
):
    team = await team_service.get_team(db, team_id)
    if team is None or team.tournament_id != tournament.id:
        raise HTTPException(status_code=404, detail="Squadra non trovata")
    team = await team_service.update_team(db, team, data)
    return team_service.serialize_team(team)


@router.delete("/api/v1/admin/tournaments/{tournament_id}/teams/{team_id}")
async def delete_team(
    team_id: int,
    tournament=Depends(get_tournament_or_404),
    db: AsyncSession = Depends(get_db),
):
    team = await team_service.get_team(db, team_id)
    if team is None or team.tournament_id != tournament.id:
        raise HTTPException(status_code=404, detail="Squadra non trovata")
    await team_service.delete_team(db, team)
    return {"ok": True}


@router.post("/api/v1/admin/tournaments/{tournament_id}/teams/{team_id}/members", response_model=TeamRead)
async def assign_team_member(
    team_id: int,
    data: TeamMemberAssign,
    tournament=Depends(get_tournament_or_404),
    db: AsyncSession = Depends(get_db),
):
    team = await team_service.get_team(db, team_id)
    if team is None or team.tournament_id != tournament.id:
        raise HTTPException(status_code=404, detail="Squadra non trovata")
    updated = await team_service.assign_member(db, tournament, team, data)
    return team_service.serialize_team(updated)


@router.delete("/api/v1/admin/tournaments/{tournament_id}/teams/{team_id}/members/{player_id}", response_model=TeamRead)
async def remove_team_member(
    team_id: int,
    player_id: int,
    tournament=Depends(get_tournament_or_404),
    db: AsyncSession = Depends(get_db),
):
    team = await team_service.get_team(db, team_id)
    if team is None or team.tournament_id != tournament.id:
        raise HTTPException(status_code=404, detail="Squadra non trovata")
    updated = await team_service.remove_member(db, team, player_id)
    return team_service.serialize_team(updated)


@router.patch("/api/v1/admin/tournaments/{tournament_id}/teams/{team_id}/members/order", response_model=TeamRead)
async def reorder_team_members(
    team_id: int,
    data: TeamMemberOrderUpdate,
    tournament=Depends(get_tournament_or_404),
    db: AsyncSession = Depends(get_db),
):
    team = await team_service.get_team(db, team_id)
    if team is None or team.tournament_id != tournament.id:
        raise HTTPException(status_code=404, detail="Squadra non trovata")
    updated = await team_service.reorder_members(db, team, data)
    return team_service.serialize_team(updated)


@router.patch("/api/v1/admin/tournaments/{tournament_id}/teams/{team_id}/availability", response_model=TeamRead)
async def update_team_availability(
    team_id: int,
    data: TeamAvailabilityUpdate,
    tournament=Depends(get_tournament_or_404),
    db: AsyncSession = Depends(get_db),
):
    team = await team_service.get_team(db, team_id)
    if team is None or team.tournament_id != tournament.id:
        raise HTTPException(status_code=404, detail="Squadra non trovata")
    updated = await team_service.update_team_availability(db, team, data)
    return team_service.serialize_team(updated)


@router.patch("/api/v1/admin/tournaments/{tournament_id}/teams/{team_id}/status", response_model=TeamRead)
async def update_team_status(
    team_id: int,
    data: TeamStatusUpdate,
    tournament=Depends(get_tournament_or_404),
    db: AsyncSession = Depends(get_db),
):
    team = await team_service.get_team(db, team_id)
    if team is None or team.tournament_id != tournament.id:
        raise HTTPException(status_code=404, detail="Squadra non trovata")
    updated = await team_service.update_team_status(db, team, data)
    return team_service.serialize_team(updated)


@router.patch("/api/v1/admin/tournaments/{tournament_id}/teams/{team_id}/lineup", response_model=TeamRead)
async def update_team_lineup(
    team_id: int,
    data: TeamLineupUpdate,
    tournament=Depends(get_tournament_or_404),
    db: AsyncSession = Depends(get_db),
):
    team = await team_service.get_team(db, team_id)
    if team is None or team.tournament_id != tournament.id:
        raise HTTPException(status_code=404, detail="Squadra non trovata")
    updated = await team_service.update_team_lineup(db, team, data)
    return team_service.serialize_team(updated)
