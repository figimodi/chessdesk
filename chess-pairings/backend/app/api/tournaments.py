from fastapi import APIRouter, Depends, File, HTTPException, UploadFile
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_user, get_optional_current_user, get_tournament_or_404
from app.core.database import get_db
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
from app.services import tournament as tournament_service

router = APIRouter(tags=["tournaments"])


@router.get("/api/v1/tournaments/", response_model=list[TournamentListItem])
async def get_tournaments(
    db: AsyncSession = Depends(get_db), current_user=Depends(get_optional_current_user)
):
    tournaments = await tournament_service._get_tournament_unscoped_list(db)
    return [tournament_service.serialize_tournament_list_item(item, current_user) for item in tournaments]


@router.get("/api/v1/tournaments/{tournament_id}", response_model=TournamentDetail)
async def get_tournament(
    tournament_id: int,
    db: AsyncSession = Depends(get_db),
    current_user=Depends(get_optional_current_user),
):
    tournament = await tournament_service._get_tournament_unscoped(db, tournament_id)
    if tournament is None:
        raise HTTPException(status_code=404, detail="Tournament not found")
    return await tournament_service.serialize_tournament_detail(db, tournament, current_user)


@router.post("/api/v1/admin/tournaments/", response_model=TournamentListItem, status_code=201)
async def create_tournament(
    data: TournamentCreate, db: AsyncSession = Depends(get_db), current_user=Depends(get_current_user)
):
    tournament = await tournament_service.create_tournament(db, data, current_user)
    return tournament_service.serialize_tournament_list_item(tournament, current_user)


@router.put("/api/v1/admin/tournaments/{tournament_id}", response_model=TournamentListItem)
async def update_tournament(
    data: TournamentUpdate,
    tournament=Depends(get_tournament_or_404),
    db: AsyncSession = Depends(get_db),
):
    updated = await tournament_service.update_tournament(db, tournament, data)
    return tournament_service.serialize_tournament_list_item(updated, tournament.owner)


@router.delete("/api/v1/admin/tournaments/{tournament_id}")
async def delete_tournament(
    tournament=Depends(get_tournament_or_404), db: AsyncSession = Depends(get_db)
):
    await tournament_service.delete_tournament(db, tournament)
    return {"ok": True}


@router.post(
    "/api/v1/tournaments/{tournament_id}/register",
    response_model=TournamentPlayerRead,
)
async def register_to_tournament(
    tournament_id: int,
    data: TournamentPublicRegistration,
    db: AsyncSession = Depends(get_db),
):
    tournament = await tournament_service._get_tournament_unscoped(db, tournament_id)
    if tournament is None:
        raise HTTPException(status_code=404, detail="Tournament not found")
    entry = await tournament_service.register_public_player(db, tournament, data)
    return tournament_service.serialize_tournament_player(entry)


@router.post(
    "/api/v1/admin/tournaments/{tournament_id}/players",
    response_model=TournamentPlayerRead,
)
async def assign_player(
    data: TournamentPlayerAssign,
    tournament=Depends(get_tournament_or_404),
    db: AsyncSession = Depends(get_db),
):
    entry = await tournament_service.assign_player(db, tournament, data)
    return tournament_service.serialize_tournament_player(entry)


@router.delete("/api/v1/admin/tournaments/{tournament_id}/players/{player_id}")
async def remove_player(
    player_id: int,
    tournament=Depends(get_tournament_or_404),
    db: AsyncSession = Depends(get_db),
):
    await tournament_service.remove_player(db, tournament, player_id)
    return {"ok": True}


@router.patch(
    "/api/v1/admin/tournaments/{tournament_id}/players/{player_id}/availability",
    response_model=TournamentPlayerRead,
)
async def update_player_availability(
    player_id: int,
    data: TournamentPlayerAvailabilityUpdate,
    tournament=Depends(get_tournament_or_404),
    db: AsyncSession = Depends(get_db),
):
    entry = await tournament_service.update_player_availability(db, tournament, player_id, data)
    return tournament_service.serialize_tournament_player(entry)


@router.patch(
    "/api/v1/admin/tournaments/{tournament_id}/players/{player_id}/status",
    response_model=TournamentPlayerRead,
)
async def update_player_status(
    player_id: int,
    data: TournamentPlayerStatusUpdate,
    tournament=Depends(get_tournament_or_404),
    db: AsyncSession = Depends(get_db),
):
    entry = await tournament_service.update_player_status(db, tournament, player_id, data)
    return tournament_service.serialize_tournament_player(entry)


@router.post(
    "/api/v1/admin/tournaments/{tournament_id}/close-registration",
    response_model=TournamentListItem,
)
async def close_registration(
    tournament=Depends(get_tournament_or_404),
    db: AsyncSession = Depends(get_db),
):
    updated = await tournament_service.close_registration(db, tournament)
    return tournament_service.serialize_tournament_list_item(updated, tournament.owner)


@router.post(
    "/api/v1/admin/tournaments/{tournament_id}/reopen-registration",
    response_model=TournamentListItem,
)
async def reopen_registration(
    tournament=Depends(get_tournament_or_404),
    db: AsyncSession = Depends(get_db),
):
    updated = await tournament_service.reopen_registration(db, tournament)
    return tournament_service.serialize_tournament_list_item(updated, tournament.owner)


@router.post("/api/v1/admin/tournaments/{tournament_id}/bulletin")
async def upload_bulletin(
    upload: UploadFile = File(...),
    tournament=Depends(get_tournament_or_404),
    db: AsyncSession = Depends(get_db),
):
    return await tournament_service.upload_bulletin(db, tournament, upload)
