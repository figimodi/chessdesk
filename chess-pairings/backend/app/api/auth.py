from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_user
from app.core.database import get_db
from app.schemas.user import AuthToken, LoginRequest, PasswordChangeRequest, UserRead
from app.services import auth as auth_service
from app.services import user as user_service

router = APIRouter(tags=["auth"])


@router.post("/api/v1/auth/login", response_model=AuthToken)
async def login(data: LoginRequest, db: AsyncSession = Depends(get_db)):
    user = await user_service.authenticate_user(db, data.username, data.password)
    if user is None:
        raise HTTPException(status_code=401, detail="Invalid username or password")
    return AuthToken(access_token=auth_service.create_access_token(user.id), user=UserRead.model_validate(user))


@router.get("/api/v1/auth/me", response_model=UserRead)
async def get_me(current_user=Depends(get_current_user)):
    return UserRead.model_validate(current_user)


@router.post("/api/v1/auth/change-password", response_model=UserRead)
async def change_password(
    data: PasswordChangeRequest,
    current_user=Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    updated_user = await user_service.change_password(
        db,
        current_user,
        current_password=data.current_password,
        new_password=data.new_password,
    )
    if updated_user is None:
        raise HTTPException(status_code=400, detail="Current password is incorrect")
    return UserRead.model_validate(updated_user)
