from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_admin_user
from app.core.database import get_db
from app.models.user import UserRole
from app.schemas.user import UserCreate, UserRead, UserUpdate
from app.services import user as user_service

router = APIRouter(tags=["users"])


@router.get("/api/v1/admin/users/", response_model=list[UserRead])
async def get_users(_: object = Depends(get_admin_user), db: AsyncSession = Depends(get_db)):
    users = await user_service.list_users(db)
    return [UserRead.model_validate(user) for user in users]


@router.post("/api/v1/admin/users/", response_model=UserRead, status_code=201)
async def create_user(
    data: UserCreate,
    _: object = Depends(get_admin_user),
    db: AsyncSession = Depends(get_db),
):
    existing = await user_service.get_user_by_email(db, data.email)
    if existing is not None:
        raise HTTPException(status_code=409, detail="Esiste gia un utente con questa email")
    existing_username = await user_service.get_user_by_username(db, data.username)
    if existing_username is not None:
        raise HTTPException(status_code=409, detail="Esiste gia un utente con questo username")
    user = await user_service.create_user(
        db,
        email=data.email,
        username=data.username,
        password=data.password,
        role=UserRole.user,
        email_confirmed=True,
        must_change_password=True,
    )
    return UserRead.model_validate(user)


@router.patch("/api/v1/admin/users/{user_id}", response_model=UserRead)
async def update_user(
    user_id: int,
    data: UserUpdate,
    current_admin=Depends(get_admin_user),
    db: AsyncSession = Depends(get_db),
):
    user = await user_service.get_user_by_id(db, user_id)
    if user is None:
        raise HTTPException(status_code=404, detail="Utente non trovato")
    if data.username is not None:
        existing_username = await user_service.get_user_by_username(db, data.username)
        if existing_username is not None and existing_username.id != user.id:
            raise HTTPException(status_code=409, detail="Esiste gia un utente con questo username")
    if user.role == UserRole.admin and data.is_active is False:
        raise HTTPException(status_code=409, detail="L'account admin non puo essere disattivato")
    updated = await user_service.update_user(
        db,
        user,
        username=data.username,
        password=data.password,
        is_active=data.is_active,
        must_change_password=(True if data.password is not None and user.id != current_admin.id else None),
    )
    return UserRead.model_validate(updated)


@router.delete("/api/v1/admin/users/{user_id}")
async def delete_user(
    user_id: int,
    current_admin=Depends(get_admin_user),
    db: AsyncSession = Depends(get_db),
):
    user = await user_service.get_user_by_id(db, user_id)
    if user is None:
        raise HTTPException(status_code=404, detail="Utente non trovato")
    if user.id == current_admin.id:
        raise HTTPException(status_code=409, detail="Non puoi eliminare l'account attualmente in uso")
    await user_service.delete_user(db, user, reassigned_owner_id=current_admin.id)
    return {"ok": True}
