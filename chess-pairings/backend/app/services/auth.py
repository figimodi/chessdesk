import base64
import hashlib
import hmac
import json
import secrets
from datetime import datetime, timedelta, timezone

from fastapi import HTTPException

from app.core.config import settings


def hash_password(password: str) -> str:
    salt = secrets.token_bytes(16)
    derived = hashlib.pbkdf2_hmac("sha256", password.encode("utf-8"), salt, 600000)
    return f"{base64.urlsafe_b64encode(salt).decode()}${base64.urlsafe_b64encode(derived).decode()}"


def verify_password(password: str, password_hash: str) -> bool:
    try:
        encoded_salt, encoded_hash = password_hash.split("$", maxsplit=1)
    except ValueError:
        return False

    salt = base64.urlsafe_b64decode(encoded_salt.encode())
    expected_hash = base64.urlsafe_b64decode(encoded_hash.encode())
    candidate_hash = hashlib.pbkdf2_hmac("sha256", password.encode("utf-8"), salt, 600000)
    return hmac.compare_digest(candidate_hash, expected_hash)


def _b64encode(raw: bytes) -> str:
    return base64.urlsafe_b64encode(raw).decode().rstrip("=")


def _b64decode(raw: str) -> bytes:
    padding = "=" * (-len(raw) % 4)
    return base64.urlsafe_b64decode(f"{raw}{padding}".encode())


def create_access_token(user_id: int) -> str:
    expires_at = datetime.now(timezone.utc) + timedelta(hours=settings.AUTH_TOKEN_TTL_HOURS)
    payload = {
        "sub": str(user_id),
        "exp": int(expires_at.timestamp()),
    }
    serialized_payload = json.dumps(payload, separators=(",", ":")).encode()
    signature = hmac.new(
        settings.AUTH_SECRET_KEY.encode("utf-8"),
        serialized_payload,
        hashlib.sha256,
    ).digest()
    return f"{_b64encode(serialized_payload)}.{_b64encode(signature)}"


def create_email_confirmation_token(user_id: int, email: str, issued_at: datetime | None = None) -> str:
    issued_at = issued_at or datetime.now(timezone.utc)
    expires_at = issued_at + timedelta(hours=settings.EMAIL_CONFIRMATION_TOKEN_TTL_HOURS)
    payload = {
        "sub": str(user_id),
        "email": email,
        "purpose": "email_confirmation",
        "iat": issued_at.isoformat(),
        "exp": int(expires_at.timestamp()),
    }
    serialized_payload = json.dumps(payload, separators=(",", ":")).encode()
    signature = hmac.new(
        settings.AUTH_SECRET_KEY.encode("utf-8"),
        serialized_payload,
        hashlib.sha256,
    ).digest()
    return f"{_b64encode(serialized_payload)}.{_b64encode(signature)}"


def decode_email_confirmation_token(token: str) -> tuple[int, str, datetime]:
    try:
        payload_part, signature_part = token.split(".", maxsplit=1)
        payload_bytes = _b64decode(payload_part)
        provided_signature = _b64decode(signature_part)
    except (ValueError, json.JSONDecodeError):
        raise HTTPException(status_code=400, detail="Token di conferma non valido")

    expected_signature = hmac.new(
        settings.AUTH_SECRET_KEY.encode("utf-8"),
        payload_bytes,
        hashlib.sha256,
    ).digest()
    if not hmac.compare_digest(provided_signature, expected_signature):
        raise HTTPException(status_code=400, detail="Token di conferma non valido")

    payload = json.loads(payload_bytes.decode())
    if payload.get("purpose") != "email_confirmation":
        raise HTTPException(status_code=400, detail="Token di conferma non valido")
    if payload.get("exp", 0) < int(datetime.now(timezone.utc).timestamp()):
        raise HTTPException(status_code=400, detail="Token di conferma scaduto")

    try:
        issued_at = payload["iat"]
        if isinstance(issued_at, (int, float)):
            issued_at_dt = datetime.fromtimestamp(issued_at, tz=timezone.utc)
        else:
            issued_at_dt = datetime.fromisoformat(str(issued_at))
            if issued_at_dt.tzinfo is None:
                issued_at_dt = issued_at_dt.replace(tzinfo=timezone.utc)
        return int(payload["sub"]), str(payload["email"]), issued_at_dt
    except (KeyError, TypeError, ValueError):
        raise HTTPException(status_code=400, detail="Token di conferma non valido")


def decode_access_token(token: str) -> int:
    try:
        payload_part, signature_part = token.split(".", maxsplit=1)
        payload_bytes = _b64decode(payload_part)
        provided_signature = _b64decode(signature_part)
    except (ValueError, json.JSONDecodeError):
        raise HTTPException(status_code=401, detail="Token di autenticazione non valido")

    expected_signature = hmac.new(
        settings.AUTH_SECRET_KEY.encode("utf-8"),
        payload_bytes,
        hashlib.sha256,
    ).digest()
    if not hmac.compare_digest(provided_signature, expected_signature):
        raise HTTPException(status_code=401, detail="Token di autenticazione non valido")

    payload = json.loads(payload_bytes.decode())
    if payload.get("exp", 0) < int(datetime.now(timezone.utc).timestamp()):
        raise HTTPException(status_code=401, detail="Token di autenticazione scaduto")

    try:
        return int(payload["sub"])
    except (KeyError, TypeError, ValueError):
        raise HTTPException(status_code=401, detail="Token di autenticazione non valido")
