from pydantic_settings import BaseSettings, SettingsConfigDict
from pathlib import Path


BACKEND_ROOT = Path(__file__).resolve().parents[2]


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    DATABASE_URL: str = "postgresql+asyncpg://chess:chess@localhost:5432/chess_pairings"
    ALLOWED_ORIGINS: list[str] = ["http://localhost:5173"]

    APP_NAME: str = "Chess Pairings API"
    FILES_BASE_URL: str = "http://localhost:8010"
    DOCUMENTS_DIR: str = "storage/documents"
    PAIRINGS_WORK_DIR: str = "storage/pairings"

    BBP_PAIRINGS_BIN: str = "/usr/local/bin/bbpPairings"
    BBP_PAIRINGS_SYSTEM: str = "dutch"

    PLAYER_LIST_FILE: str = str(BACKEND_ROOT / "data" / "players_list_foa.txt")
    AUTH_SECRET_KEY: str = "change-me"
    AUTH_TOKEN_TTL_HOURS: int = 12
    ADMIN_EMAIL: str | None = None
    ADMIN_PASSWORD: str | None = None
    ADMIN_USERNAME: str | None = None


settings = Settings()
