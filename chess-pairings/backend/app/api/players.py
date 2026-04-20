from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.schemas.player import FidePlayerSearchResult, PlayerCreate, PlayerRead
from app.services import player as player_service

router = APIRouter(tags=["players"])


@router.get("/api/v1/players/", response_model=list[PlayerRead])
async def get_players(db: AsyncSession = Depends(get_db)):
    return await player_service.get_players(db)


@router.post("/api/v1/admin/players/", response_model=PlayerRead, status_code=201)
async def create_player(data: PlayerCreate, db: AsyncSession = Depends(get_db)):
    return await player_service.create_player(db, data)


@router.get("/api/v1/players/fide/search", response_model=list[FidePlayerSearchResult])
async def search_fide_players(
    query: str = Query(min_length=2, max_length=60),
    category: str | None = Query(default=None),
    db: AsyncSession = Depends(get_db),
):
    return await player_service.search_fide_players(db, query, category)


@router.post("/api/v1/admin/players/import-from-fide", response_model=PlayerRead)
async def import_player_from_fide(
    fide_id: str = Query(min_length=4), db: AsyncSession = Depends(get_db)
):
    return await player_service.import_player_from_fide(db, fide_id)
