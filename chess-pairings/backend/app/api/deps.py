from fastapi import Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.services import pairing as pairing_service
from app.services import tournament as tournament_service


async def get_tournament_or_404(
    tournament_id: int, db: AsyncSession = Depends(get_db)
):
    tournament = await tournament_service.get_tournament(db, tournament_id)
    if tournament is None:
        raise HTTPException(status_code=404, detail="Tournament not found")
    return tournament


async def get_pairing_or_404(pairing_id: int, db: AsyncSession = Depends(get_db)):
    pairing = await pairing_service.get_pairing(db, pairing_id)
    if pairing is None:
        raise HTTPException(status_code=404, detail="Pairing not found")
    return pairing
