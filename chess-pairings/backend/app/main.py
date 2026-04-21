from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from fastapi.routing import APIRoute

from app import models  # noqa: F401
from app.api import auth, health, pairings, players, teams, tournaments, users
from app.core.config import settings
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
