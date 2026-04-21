from pathlib import Path
import asyncio

from alembic import command
from alembic.config import Config

from app.core.config import settings


async def run_migrations() -> None:
    config = _build_alembic_config()
    await asyncio.to_thread(command.upgrade, config, "head")


def _build_alembic_config() -> Config:
    config = Config(str(Path(__file__).resolve().parents[2] / "alembic.ini"))
    config.set_main_option("sqlalchemy.url", settings.DATABASE_URL)
    return config
