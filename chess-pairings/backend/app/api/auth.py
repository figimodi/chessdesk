from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_user
from app.core.database import get_db
from app.schemas.user import (
    AuthToken,
    EmailConfirmationRequest,
    EmailConfirmationResendRequest,
    LoginRequest,
    MessageResponse,
    PasswordChangeRequest,
    PublicRegistrationRequest,
    UserRead,
)
from app.services import auth as auth_service
from app.services.mail import MailService
from app.services import user as user_service

router = APIRouter(tags=["auth"])


@router.post("/api/v1/auth/login", response_model=AuthToken)
async def login(data: LoginRequest, db: AsyncSession = Depends(get_db)):
    user = await user_service.authenticate_user(db, data.username, data.password)
    if user is None:
        raise HTTPException(status_code=401, detail="Invalid username or password")
    if not user.email_confirmed:
        raise HTTPException(status_code=403, detail="Devi confermare il tuo indirizzo email prima di accedere")
    return AuthToken(access_token=auth_service.create_access_token(user.id), user=UserRead.model_validate(user))


@router.post("/api/v1/auth/register", response_model=MessageResponse, status_code=201)
async def register(data: PublicRegistrationRequest, db: AsyncSession = Depends(get_db)):
    existing = await user_service.get_user_by_email(db, data.email)
    if existing is not None:
        raise HTTPException(status_code=409, detail="Esiste gia un account con questa email")
    existing_username = await user_service.get_user_by_username(db, data.username)
    if existing_username is not None:
        raise HTTPException(status_code=409, detail="Esiste gia un account con questo username")

    user = await user_service.create_user(
        db,
        email=data.email,
        username=data.username,
        password=data.password,
        email_confirmed=False,
    )
    try:
        token = auth_service.create_email_confirmation_token(user.id, user.email)
        MailService().send_registration_confirmation(recipient_email=user.email, username=user.username, token=token)
    except HTTPException:
        await user_service.delete_user_without_reassignment(db, user)
        raise
    return MessageResponse(message="Ti abbiamo inviato una email di conferma. Controlla la tua casella per attivare l'account.")


@router.post("/api/v1/auth/confirm-email", response_model=MessageResponse)
async def confirm_email(data: EmailConfirmationRequest, db: AsyncSession = Depends(get_db)):
    user_id, email = auth_service.decode_email_confirmation_token(data.token)
    user = await user_service.get_user_by_id(db, user_id)
    if user is None or user.email != email.lower().strip():
        raise HTTPException(status_code=404, detail="Utente non trovato")
    if not user.email_confirmed:
        await user_service.confirm_user_email(db, user)
    return MessageResponse(message="Email confermata con successo. Ora puoi accedere.")


@router.post("/api/v1/auth/resend-confirmation", response_model=MessageResponse)
async def resend_confirmation_email(data: EmailConfirmationResendRequest, db: AsyncSession = Depends(get_db)):
    user = await user_service.get_user_by_email(db, data.email)
    if user is None:
        raise HTTPException(status_code=404, detail="Nessun account trovato con questa email")
    if user.email_confirmed:
        return MessageResponse(message="Questo account e gia confermato. Puoi accedere.")

    token = auth_service.create_email_confirmation_token(user.id, user.email)
    MailService().send_registration_confirmation(recipient_email=user.email, username=user.username, token=token)
    return MessageResponse(message="Ti abbiamo inviato una nuova email di conferma.")


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
