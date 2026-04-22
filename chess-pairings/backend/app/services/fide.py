from sqlalchemy.ext.asyncio import AsyncSession

from app.schemas.player import FidePlayerSearchResult
from app.services import catalog


class FideService:
    async def search_players(
        self, db: AsyncSession, query: str, category: str | None = None
    ) -> list[FidePlayerSearchResult]:
        return await catalog.search_catalog_players(db, query, category)

    async def fetch_profile(
        self, db: AsyncSession, fide_id: str
    ) -> FidePlayerSearchResult:
        player = await catalog.get_catalog_player_by_fide_id(db, fide_id.strip())
        if player is None:
            raise ValueError(f"Giocatore con ID {fide_id} non trovato nel catalogo")
        return catalog._to_schema(player)
