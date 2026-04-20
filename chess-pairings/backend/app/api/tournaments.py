from fastapi import APIRouter, Depends, File, UploadFile
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_tournament_or_404
from app.core.database import get_db
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
from app.services import tournament as tournament_service

router = APIRouter(tags=["tournaments"])


@router.get("/api/v1/tournaments/", response_model=list[TournamentListItem])
async def get_tournaments(db: AsyncSession = Depends(get_db)):
    tournaments = await tournament_service.get_tournaments(db)
    return [tournament_service.serialize_tournament_list_item(item) for item in tournaments]


@router.get("/api/v1/tournaments/{tournament_id}", response_model=TournamentDetail)
async def get_tournament(
    tournament=Depends(get_tournament_or_404), db: AsyncSession = Depends(get_db)
):
    return await tournament_service.serialize_tournament_detail(db, tournament)


@router.post("/api/v1/admin/tournaments/", response_model=TournamentListItem, status_code=201)
async def create_tournament(
    data: TournamentCreate, db: AsyncSession = Depends(get_db)
):
    tournament = await tournament_service.create_tournament(db, data)
    return tournament_service.serialize_tournament_list_item(tournament)


@router.put("/api/v1/admin/tournaments/{tournament_id}", response_model=TournamentListItem)
async def update_tournament(
    data: TournamentUpdate,
    tournament=Depends(get_tournament_or_404),
    db: AsyncSession = Depends(get_db),
):
    updated = await tournament_service.update_tournament(db, tournament, data)
    return tournament_service.serialize_tournament_list_item(updated)


@router.delete("/api/v1/admin/tournaments/{tournament_id}")
async def delete_tournament(
    tournament=Depends(get_tournament_or_404), db: AsyncSession = Depends(get_db)
):
    await tournament_service.delete_tournament(db, tournament)
    return {"ok": True}


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
    return tournament_service.serialize_tournament_list_item(updated)


@router.post(
    "/api/v1/admin/tournaments/{tournament_id}/reopen-registration",
    response_model=TournamentListItem,
)
async def reopen_registration(
    tournament=Depends(get_tournament_or_404),
    db: AsyncSession = Depends(get_db),
):
    updated = await tournament_service.reopen_registration(db, tournament)
    return tournament_service.serialize_tournament_list_item(updated)


@router.post("/api/v1/admin/tournaments/{tournament_id}/bulletin")
async def upload_bulletin(
    upload: UploadFile = File(...),
    tournament=Depends(get_tournament_or_404),
    db: AsyncSession = Depends(get_db),
):
    return await tournament_service.upload_bulletin(db, tournament, upload)
