from fastapi import Depends, HTTPException
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.models.user import UserRole
from app.services import auth as auth_service
from app.services import pairing as pairing_service
from app.services import tournament as tournament_service
from app.services import user as user_service

security = HTTPBearer(auto_error=False)


async def get_current_user(
    credentials: HTTPAuthorizationCredentials | None = Depends(security),
    db: AsyncSession = Depends(get_db),
):
    if credentials is None:
        raise HTTPException(status_code=401, detail="Autenticazione richiesta")
    user_id = auth_service.decode_access_token(credentials.credentials)
    user = await user_service.get_user_by_id(db, user_id)
    if user is None or not user.is_active:
        raise HTTPException(status_code=401, detail="Token di autenticazione non valido")
    return user


async def get_optional_current_user(
    credentials: HTTPAuthorizationCredentials | None = Depends(security),
    db: AsyncSession = Depends(get_db),
):
    if credentials is None:
        return None
    user_id = auth_service.decode_access_token(credentials.credentials)
    user = await user_service.get_user_by_id(db, user_id)
    if user is None or not user.is_active:
        raise HTTPException(status_code=401, detail="Token di autenticazione non valido")
    return user


async def get_admin_user(current_user=Depends(get_current_user)):
    if current_user.role != UserRole.admin:
        raise HTTPException(status_code=403, detail="Permessi amministratore richiesti")
    return current_user


async def get_tournament_or_404(
    tournament_id: int,
    db: AsyncSession = Depends(get_db),
    current_user=Depends(get_current_user),
):
    tournament = await tournament_service.get_tournament(db, tournament_id, current_user)
    if tournament is None:
        raise HTTPException(status_code=404, detail="Torneo non trovato")
    return tournament


async def get_pairing_or_404(
    pairing_id: int,
    db: AsyncSession = Depends(get_db),
    current_user=Depends(get_current_user),
):
    pairing = await pairing_service.get_pairing(db, pairing_id, current_user)
    if pairing is None:
        raise HTTPException(status_code=404, detail="Abbinamento non trovato")
    return pairing
