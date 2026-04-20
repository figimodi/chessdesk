from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_pairing_or_404, get_tournament_or_404
from app.core.database import get_db
from app.schemas.pairing import PairingCreateResponse, PairingResultUpdate
from app.services import pairing as pairing_service

router = APIRouter(tags=["pairings"])


@router.post(
    "/api/v1/admin/tournaments/{tournament_id}/pairings/generate",
    response_model=PairingCreateResponse,
)
async def generate_pairings(
    tournament=Depends(get_tournament_or_404), db: AsyncSession = Depends(get_db)
):
    return await pairing_service.generate_pairings(db, tournament)


@router.patch("/api/v1/admin/tournaments/{tournament_id}/pairings/results/{pairing_id}")
async def update_pairing_result(
    data: PairingResultUpdate,
    pairing=Depends(get_pairing_or_404),
    db: AsyncSession = Depends(get_db),
):
    return await pairing_service.update_pairing_result(db, pairing, data)


@router.delete("/api/v1/admin/tournaments/{tournament_id}/pairings/latest-round")
async def delete_latest_round(
    tournament=Depends(get_tournament_or_404), db: AsyncSession = Depends(get_db)
):
    return await pairing_service.delete_latest_round(db, tournament)
