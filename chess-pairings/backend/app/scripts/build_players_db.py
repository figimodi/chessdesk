import asyncio

from sqlalchemy import text

from app import models  # noqa: F401
from app.core.database import AsyncSessionLocal, engine
from app.models.base import Base
from app.services.catalog import rebuild_catalog_players


async def main() -> None:
    async with engine.begin() as connection:
        await connection.run_sync(Base.metadata.create_all)
        await connection.execute(
            text("ALTER TABLE catalog_player ADD COLUMN IF NOT EXISTS birth_year INTEGER")
        )
        await connection.execute(text("TRUNCATE TABLE catalog_player RESTART IDENTITY"))

    async with AsyncSessionLocal() as session:
        count = await rebuild_catalog_players(session)
        print(f"catalog_player rebuilt successfully with {count} rows")


if __name__ == "__main__":
    asyncio.run(main())
