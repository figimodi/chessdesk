from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from fastapi.routing import APIRoute

from app import models  # noqa: F401
from app.api import health, pairings, players, teams, tournaments
from app.core.config import settings
from app.core.database import engine
from app.models.base import Base
from sqlalchemy import text


def generate_operation_id(route: APIRoute) -> str:
    return route.name


@asynccontextmanager
async def lifespan(_: FastAPI):
    Path(settings.DOCUMENTS_DIR).mkdir(parents=True, exist_ok=True)
    Path(settings.PAIRINGS_WORK_DIR).mkdir(parents=True, exist_ok=True)
    async with engine.begin() as connection:
        await connection.run_sync(Base.metadata.create_all)
        await connection.execute(
            text("ALTER TABLE player ADD COLUMN IF NOT EXISTS rapid_rating INTEGER")
        )
        await connection.execute(
            text("ALTER TABLE player ADD COLUMN IF NOT EXISTS standard_k INTEGER")
        )
        await connection.execute(
            text("ALTER TABLE player ADD COLUMN IF NOT EXISTS rapid_k INTEGER")
        )
        await connection.execute(
            text("ALTER TABLE player ADD COLUMN IF NOT EXISTS blitz_rating INTEGER")
        )
        await connection.execute(
            text("ALTER TABLE player ADD COLUMN IF NOT EXISTS blitz_k INTEGER")
        )
        await connection.execute(
            text("ALTER TABLE player ADD COLUMN IF NOT EXISTS birth_year INTEGER")
        )
        await connection.execute(
            text("ALTER TABLE catalog_player ADD COLUMN IF NOT EXISTS birth_year INTEGER")
        )
        await connection.execute(
            text("ALTER TABLE catalog_player ADD COLUMN IF NOT EXISTS standard_k INTEGER")
        )
        await connection.execute(
            text("ALTER TABLE catalog_player ADD COLUMN IF NOT EXISTS rapid_k INTEGER")
        )
        await connection.execute(
            text("ALTER TABLE catalog_player ADD COLUMN IF NOT EXISTS blitz_k INTEGER")
        )
        await connection.execute(
            text("ALTER TABLE tournament ADD COLUMN IF NOT EXISTS is_registration_closed BOOLEAN DEFAULT FALSE")
        )
        await connection.execute(
            text("ALTER TABLE tournament ADD COLUMN IF NOT EXISTS tie_breaks VARCHAR(120) DEFAULT 'buchholz,sonneborn_berger,rating'")
        )
        await connection.execute(
            text("ALTER TABLE tournament ADD COLUMN IF NOT EXISTS is_elo_rated BOOLEAN DEFAULT FALSE")
        )
        await connection.execute(
            text("ALTER TABLE tournament ADD COLUMN IF NOT EXISTS max_players_per_team INTEGER")
        )
        await connection.execute(
            text("ALTER TABLE tournament ADD COLUMN IF NOT EXISTS boards_per_match INTEGER")
        )
        await connection.execute(
            text("ALTER TABLE tournament ADD COLUMN IF NOT EXISTS enforce_board_order BOOLEAN DEFAULT FALSE")
        )
        await connection.execute(
            text("ALTER TABLE tournament ADD COLUMN IF NOT EXISTS match_points_win INTEGER")
        )
        await connection.execute(
            text("ALTER TABLE tournament ADD COLUMN IF NOT EXISTS match_points_draw INTEGER")
        )
        await connection.execute(
            text("ALTER TABLE tournament ADD COLUMN IF NOT EXISTS match_points_loss INTEGER")
        )
        await connection.execute(
            text("ALTER TABLE tournament_player ADD COLUMN IF NOT EXISTS start_round_number INTEGER DEFAULT 1")
        )
        await connection.execute(
            text("ALTER TABLE tournament_player ADD COLUMN IF NOT EXISTS team_board_order INTEGER")
        )
        await connection.execute(
            text("ALTER TABLE pairing ADD COLUMN IF NOT EXISTS match_number INTEGER")
        )
        await connection.execute(
            text("ALTER TYPE pairingresult ADD VALUE IF NOT EXISTS 'white_forfeit_win'")
        )
        await connection.execute(
            text("ALTER TYPE pairingresult ADD VALUE IF NOT EXISTS 'black_forfeit_win'")
        )
        await connection.execute(
            text("ALTER TYPE pairingresult ADD VALUE IF NOT EXISTS 'double_forfeit_loss'")
        )
        await connection.execute(
            text("ALTER TYPE pairingresult ADD VALUE IF NOT EXISTS 'double_forfeit_win'")
        )
        await connection.execute(
            text("ALTER TABLE team ADD COLUMN IF NOT EXISTS is_active BOOLEAN DEFAULT TRUE")
        )
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
app.include_router(tournaments.router)
app.include_router(players.router)
app.include_router(teams.router)
app.include_router(pairings.router)
