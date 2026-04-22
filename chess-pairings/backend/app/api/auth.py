from datetime import datetime, timezone
import hashlib
import logging

from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_user
from app.core.database import get_db
from app.core.rate_limit import RateLimitRule, enforce_rate_limit
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
logger = logging.getLogger(__name__)

LOGIN_RATE_LIMIT = RateLimitRule(5, 60, "Troppi tentativi di accesso. Riprova tra un minuto.")
REGISTER_RATE_LIMIT = RateLimitRule(3, 300, "Troppe registrazioni da questa postazione. Riprova piu tardi.")
RESEND_RATE_LIMIT = RateLimitRule(3, 300, "Hai richiesto troppe email di conferma. Riprova piu tardi.")
CONFIRM_RATE_LIMIT = RateLimitRule(10, 300, "Troppi tentativi di conferma email. Riprova piu tardi.")


@router.post("/api/v1/auth/login", response_model=AuthToken)
async def login(data: LoginRequest, request: Request, db: AsyncSession = Depends(get_db)):
    normalized_username = user_service.normalize_username(data.username)
    client_ip = request.client.host if request.client else "unknown"
    enforce_rate_limit("login", f"{client_ip}:{normalized_username}", LOGIN_RATE_LIMIT)
    user = await user_service.authenticate_user(db, data.username, data.password)
    if user is None:
        logger.info("Failed login attempt for username %s from %s", normalized_username, client_ip)
        raise HTTPException(status_code=401, detail="Credenziali non valide")
    if not user.is_active:
        logger.info("Blocked login for inactive account %s from %s", user.username, client_ip)
        raise HTTPException(status_code=403, detail="Questo account e disattivato. Contatta lo sviluppatore.")
    if not user.email_confirmed:
        logger.info("Blocked login for unconfirmed account %s from %s", user.username, client_ip)
        raise HTTPException(status_code=403, detail="Devi confermare il tuo indirizzo email prima di accedere")
    return AuthToken(access_token=auth_service.create_access_token(user.id), user=UserRead.model_validate(user))


@router.post("/api/v1/auth/register", response_model=MessageResponse, status_code=201)
async def register(data: PublicRegistrationRequest, request: Request, db: AsyncSession = Depends(get_db)):
    client_ip = request.client.host if request.client else "unknown"
    enforce_rate_limit("register", f"{client_ip}:{data.email.lower().strip()}", REGISTER_RATE_LIMIT)
    existing = await user_service.get_user_by_email(db, data.email)
    if existing is not None:
        raise HTTPException(status_code=409, detail="Esiste gia un account con questa email")
    existing_username = await user_service.get_user_by_username(db, data.username)
    if existing_username is not None:
        raise HTTPException(status_code=409, detail="Esiste gia un account con questo username")

    try:
        sent_at = datetime.now(timezone.utc)
        user = await user_service.create_user(
            db,
            email=data.email,
            username=data.username,
            password=data.password,
            email_confirmed=False,
            email_confirmation_sent_at=sent_at,
        )
        token = auth_service.create_email_confirmation_token(user.id, user.email, issued_at=sent_at)
        MailService().send_registration_confirmation(recipient_email=user.email, username=user.username, token=token)
        logger.info("Registered user %s from %s", user.email, client_ip)
    except IntegrityError:
        raise HTTPException(status_code=409, detail="Esiste gia un account con questo username")
    except HTTPException:
        if "user" in locals():
            await user_service.delete_user_without_reassignment(db, user)
        raise
    return MessageResponse(message="Ti abbiamo inviato una email di conferma. Controlla la tua casella per attivare l'account.")


@router.post("/api/v1/auth/confirm-email", response_model=MessageResponse)
async def confirm_email(data: EmailConfirmationRequest, request: Request, db: AsyncSession = Depends(get_db)):
    client_ip = request.client.host if request.client else "unknown"
    token_hash = hashlib.sha256(data.token.encode("utf-8")).hexdigest()[:12]
    enforce_rate_limit("confirm-email", f"{client_ip}:{token_hash}", CONFIRM_RATE_LIMIT)
    user_id, email, issued_at = auth_service.decode_email_confirmation_token(data.token)
    user = await user_service.get_user_by_id(db, user_id)
    if user is None or user.email != email.lower().strip():
        raise HTTPException(status_code=404, detail="Utente non trovato")
    confirmation_sent_at = user.email_confirmation_sent_at
    if confirmation_sent_at and confirmation_sent_at.tzinfo is None:
        confirmation_sent_at = confirmation_sent_at.replace(tzinfo=timezone.utc)
    if confirmation_sent_at and issued_at < confirmation_sent_at:
        raise HTTPException(status_code=400, detail="Questo link di conferma non e piu valido. Richiedine uno nuovo.")
    if not user.email_confirmed:
        await user_service.confirm_user_email(db, user)
        logger.info("Confirmed email for user %s from %s", user.email, client_ip)
    return MessageResponse(message="Email confermata con successo. Ora puoi accedere.")


@router.post("/api/v1/auth/resend-confirmation", response_model=MessageResponse)
async def resend_confirmation_email(data: EmailConfirmationResendRequest, request: Request, db: AsyncSession = Depends(get_db)):
    client_ip = request.client.host if request.client else "unknown"
    enforce_rate_limit("resend-confirmation", f"{client_ip}:{data.email.lower().strip()}", RESEND_RATE_LIMIT)
    user = await user_service.get_user_by_email(db, data.email)
    if user is None:
        raise HTTPException(status_code=404, detail="Nessun account trovato con questa email")
    if user.email_confirmed:
        return MessageResponse(message="Questo account e gia confermato. Puoi accedere.")

    sent_at = datetime.now(timezone.utc)
    token = auth_service.create_email_confirmation_token(user.id, user.email, issued_at=sent_at)
    MailService().send_registration_confirmation(recipient_email=user.email, username=user.username, token=token)
    await user_service.mark_confirmation_sent(db, user, sent_at=sent_at)
    logger.info("Resent confirmation email for user %s from %s", user.email, client_ip)
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
        raise HTTPException(status_code=400, detail="La password attuale non e corretta")
    return UserRead.model_validate(updated_user)
