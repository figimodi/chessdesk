from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI
from fastapi import HTTPException, Request
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from fastapi.responses import FileResponse
from fastapi.routing import APIRoute

from app import models  # noqa: F401
from app.api import auth, health, pairings, players, teams, tournaments, users
from app.core.config import settings
from app.core.exceptions import ApiErrorPayload
from app.core.migrations import run_migrations
from app.services import user as user_service


def generate_operation_id(route: APIRoute) -> str:
    return route.name


async def bootstrap_admin_user() -> None:
    if not (settings.ADMIN_EMAIL and settings.ADMIN_PASSWORD and settings.ADMIN_USERNAME):
        return

    from app.core.database import AsyncSessionLocal

    async with AsyncSessionLocal() as session:
        await user_service.ensure_admin_user(
            session,
            email=settings.ADMIN_EMAIL,
            username=settings.ADMIN_USERNAME,
            password=settings.ADMIN_PASSWORD,
        )


@asynccontextmanager
async def lifespan(_: FastAPI):
    Path(settings.DOCUMENTS_DIR).mkdir(parents=True, exist_ok=True)
    Path(settings.PAIRINGS_WORK_DIR).mkdir(parents=True, exist_ok=True)
    await run_migrations()
    await bootstrap_admin_user()

    yield


app = FastAPI(
    title=settings.APP_NAME,
    version="0.1.0",
    description="API for chess tournament management with FIDE import and bbpPairings integration.",
    generate_unique_id_function=generate_operation_id,
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.exception_handler(HTTPException)
async def http_exception_handler(_: Request, exc: HTTPException):
    message = exc.detail if isinstance(exc.detail, str) else "Si e verificato un errore inatteso."
    return JSONResponse(
        status_code=exc.status_code,
        content=ApiErrorPayload(code=_http_status_to_code(exc.status_code), message=message).__dict__,
    )


@app.exception_handler(RequestValidationError)
async def validation_exception_handler(_: Request, exc: RequestValidationError):
    first_error = exc.errors()[0] if exc.errors() else None
    message = _validation_message(first_error)
    return JSONResponse(
        status_code=422,
        content=ApiErrorPayload(code="validation_error", message=message).__dict__,
    )


@app.exception_handler(Exception)
async def unhandled_exception_handler(_: Request, __: Exception):
    return JSONResponse(
        status_code=500,
        content=ApiErrorPayload(code="internal_error", message="Si e verificato un errore inatteso.").__dict__,
    )


@app.get("/files/documents/{file_name}")
async def get_document(file_name: str):
    return FileResponse(Path(settings.DOCUMENTS_DIR) / file_name)


app.include_router(health.router)
app.include_router(auth.router)
app.include_router(users.router)
app.include_router(tournaments.router)
app.include_router(players.router)
app.include_router(teams.router)
app.include_router(pairings.router)


def _http_status_to_code(status_code: int) -> str:
    mapping = {
        400: "bad_request",
        401: "unauthorized",
        403: "forbidden",
        404: "not_found",
        409: "conflict",
        429: "rate_limited",
        500: "internal_error",
    }
    return mapping.get(status_code, "http_error")


def _validation_message(error: dict | None) -> str:
    if error is None:
        return "Dati non validi."
    field = error.get("loc", [None])[-1]
    message = str(error.get("msg", "Dati non validi."))
    if field == "password" and "at least 8 characters" in message:
        return "La password deve contenere almeno 8 caratteri."
    if field == "username" and "at least 2 characters" in message:
        return "Lo username deve contenere almeno 2 caratteri."
    if field == "email":
        return "Inserisci un indirizzo email valido."
    return message
