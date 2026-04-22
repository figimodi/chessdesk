from email.message import EmailMessage
import logging
import smtplib

from fastapi import HTTPException

from app.core.config import settings


logger = logging.getLogger(__name__)


class MailService:
    def send_registration_confirmation(self, *, recipient_email: str, username: str, token: str) -> None:
        if not settings.SMTP_HOST or not settings.SMTP_FROM_EMAIL:
            raise HTTPException(
                status_code=500,
                detail="La configurazione email non e completa. Controlla SMTP_HOST e SMTP_FROM_EMAIL.",
            )

        confirmation_url = f"{settings.FRONTEND_BASE_URL.rstrip('/')}/confirm-email?token={token}"
        message = EmailMessage()
        message["Subject"] = "Conferma il tuo account Chess Pairings"
        message["From"] = self._format_sender()
        message["To"] = recipient_email
        message.set_content(
            "\n".join(
                [
                    f"Ciao {username},",
                    "",
                    "conferma il tuo account Chess Pairings aprendo questo link:",
                    confirmation_url,
                    "",
                    "Se non hai richiesto questa registrazione puoi ignorare questa email.",
                ]
            )
        )

        try:
            with smtplib.SMTP(settings.SMTP_HOST, settings.SMTP_PORT, timeout=20) as smtp:
                if settings.SMTP_USE_TLS:
                    smtp.starttls()
                if settings.SMTP_USERNAME and settings.SMTP_PASSWORD:
                    smtp.login(settings.SMTP_USERNAME, settings.SMTP_PASSWORD)
                smtp.send_message(message)
        except Exception as exc:  # pragma: no cover
            logger.exception("Failed to send registration confirmation email")
            raise HTTPException(
                status_code=500,
                detail="Non sono riuscito a inviare l'email di conferma. Contatta lo sviluppatore.",
            ) from exc

    def _format_sender(self) -> str:
        return f"{settings.SMTP_FROM_NAME} <{settings.SMTP_FROM_EMAIL}>"
