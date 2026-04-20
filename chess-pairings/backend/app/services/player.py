from fastapi import HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.schemas.player import PlayerCreate
from app.models.player import Player
from app.services.fide import FideService


async def get_players(db: AsyncSession) -> list[Player]:
    result = await db.execute(select(Player).order_by(Player.full_name.asc()))
    return list(result.scalars().all())


async def get_player(db: AsyncSession, player_id: int) -> Player | None:
    result = await db.execute(select(Player).where(Player.id == player_id))
    return result.scalar_one_or_none()


async def get_player_by_fide_id(db: AsyncSession, fide_id: str) -> Player | None:
    result = await db.execute(select(Player).where(Player.fide_id == fide_id))
    return result.scalar_one_or_none()


async def create_player(db: AsyncSession, data: PlayerCreate) -> Player:
    player = Player(**data.model_dump())
    db.add(player)
    await db.commit()
    await db.refresh(player)
    return player


async def search_fide_players(
    db: AsyncSession, query: str, category: str | None = None
):
    return await FideService().search_players(db, query, category)


async def import_player_from_fide(db: AsyncSession, fide_id: str) -> Player:
    try:
        profile = await FideService().fetch_profile(db, fide_id)
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc

    existing = await get_player_by_fide_id(db, profile.fide_id)

    payload = PlayerCreate(
        full_name=profile.full_name,
        fide_id=profile.fide_id,
        federation=profile.federation,
        rating=profile.rating,
        standard_k=profile.standard_k,
        rapid_rating=profile.rapid_rating,
        rapid_k=profile.rapid_k,
        blitz_rating=profile.blitz_rating,
        blitz_k=profile.blitz_k,
        birth_year=profile.birth_year,
        fide_title=profile.fide_title,
    )

    if existing:
        for key, value in payload.model_dump().items():
            setattr(existing, key, value)
        await db.commit()
        await db.refresh(existing)
        return existing

    return await create_player(db, payload)
