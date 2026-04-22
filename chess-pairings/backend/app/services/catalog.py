from dataclasses import dataclass
from itertools import islice
from pathlib import Path

import re

from sqlalchemy import and_, insert, or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.models.catalog_player import CatalogPlayer
from app.schemas.player import FidePlayerSearchResult


@dataclass(frozen=True)
class CatalogPlayerRow:
    fide_id: str
    full_name: str
    federation: str | None
    rating: int | None
    standard_rating: int | None
    standard_k: int | None
    rapid_rating: int | None
    rapid_k: int | None
    blitz_rating: int | None
    blitz_k: int | None
    birth_year: int | None
    fide_title: str | None


def resolve_catalog_path() -> Path:
    configured_path = Path(settings.PLAYER_LIST_FILE)
    candidate_paths = [
        configured_path,
        Path("/app/data/players_list_foa.txt"),
        Path(__file__).resolve().parents[2] / "data" / "players_list_foa.txt",
    ]

    for path in candidate_paths:
        if path.exists():
            return path

    raise FileNotFoundError(
        "players_list_foa.txt non trovato. Percorsi verificati: "
        + ", ".join(str(path) for path in candidate_paths)
    )


def parse_catalog_file():
    file_path = resolve_catalog_path()
    with file_path.open("r", encoding="utf-8", errors="replace") as file:
        header = file.readline().rstrip("\n")
        if not header:
            return

        columns = _build_columns(header)

        for line in file:
            line = line.rstrip("\n")
            if not line.strip():
                continue

            values = {name: line[start:end].strip() for name, start, end in columns}
            fide_id = values["ID Number"]
            full_name = values["Name"]
            federation = values["Fed"] or None

            if not fide_id or not full_name or full_name.isdigit():
                continue

            standard_rating = _to_rating(values["SRtng"])
            rapid_rating = _to_rating(values["RRtng"])
            blitz_rating = _to_rating(values["BRtng"])

            yield CatalogPlayerRow(
                fide_id=fide_id,
                full_name=full_name,
                federation=federation,
                rating=standard_rating or rapid_rating or blitz_rating,
                standard_rating=standard_rating,
                standard_k=_to_int(values["SK"]),
                rapid_rating=rapid_rating,
                rapid_k=_to_int(values["Rk"]),
                blitz_rating=blitz_rating,
                blitz_k=_to_int(values["BK"]),
                birth_year=_to_int(values["B-day"]),
                fide_title=(values["Tit"] or values["OTit"] or None),
            )


async def rebuild_catalog_players(db: AsyncSession, batch_size: int = 5000) -> int:
    total = 0
    rows_iter = parse_catalog_file()

    while True:
        batch = list(islice(rows_iter, batch_size))
        if not batch:
            break

        await db.execute(
            insert(CatalogPlayer),
            [
                {
                    "fide_id": row.fide_id,
                    "full_name": row.full_name,
                    "federation": row.federation,
                    "rating": row.rating,
                    "standard_rating": row.standard_rating,
                    "standard_k": row.standard_k,
                    "rapid_rating": row.rapid_rating,
                    "rapid_k": row.rapid_k,
                    "blitz_rating": row.blitz_rating,
                    "blitz_k": row.blitz_k,
                    "birth_year": row.birth_year,
                    "fide_title": row.fide_title,
                }
                for row in batch
            ],
        )
        await db.commit()
        total += len(batch)

    return total


async def search_catalog_players(
    db: AsyncSession, query: str, category: str | None = None
) -> list[FidePlayerSearchResult]:
    normalized_query = query.strip()
    if not normalized_query:
        return []

    tokens = _query_tokens(normalized_query)
    name_filters = [CatalogPlayer.full_name.ilike(f"%{token}%") for token in tokens]

    statement = (
        select(CatalogPlayer)
        .where(
            or_(
                and_(*name_filters) if name_filters else CatalogPlayer.full_name.ilike(f"%{normalized_query}%"),
                CatalogPlayer.fide_id.ilike(f"%{normalized_query}%"),
            )
        )
        .order_by(_category_rating_column(category).desc().nullslast(), CatalogPlayer.full_name.asc())
        .limit(100)
    )
    result = await db.execute(statement)
    return [_to_schema(player) for player in result.scalars().all()]


async def get_catalog_player_by_fide_id(
    db: AsyncSession, fide_id: str
) -> CatalogPlayer | None:
    result = await db.execute(
        select(CatalogPlayer).where(CatalogPlayer.fide_id == fide_id)
    )
    return result.scalar_one_or_none()


def _to_schema(player: CatalogPlayer) -> FidePlayerSearchResult:
    return FidePlayerSearchResult(
        fide_id=player.fide_id,
        full_name=player.full_name,
        federation=player.federation,
        rating=player.rating,
        standard_rating=player.standard_rating,
        standard_k=player.standard_k,
        rapid_rating=player.rapid_rating,
        rapid_k=player.rapid_k,
        blitz_rating=player.blitz_rating,
        blitz_k=player.blitz_k,
        birth_year=player.birth_year,
        fide_title=player.fide_title,
    )


def _build_columns(header: str) -> list[tuple[str, int, int]]:
    labels = [
        "ID Number",
        "Name",
        "Fed",
        "Sex",
        "Tit",
        "WTit",
        "OTit",
        "FOA",
        "SRtng",
        "SGm",
        "SK",
        "RRtng",
        "RGm",
        "Rk",
        "BRtng",
        "BGm",
        "BK",
        "B-day",
        "Flag",
    ]
    starts = [(label, header.index(label)) for label in labels]
    columns: list[tuple[str, int, int]] = []

    for index, (label, start) in enumerate(starts):
        end = starts[index + 1][1] if index + 1 < len(starts) else len(header)
        columns.append((label, start, end))

    return columns


def _to_rating(value: str) -> int | None:
    if not value or not value.isdigit():
        return None
    rating = int(value)
    return rating if rating > 0 else None


def _to_int(value: str) -> int | None:
    if not value or not value.isdigit():
        return None
    parsed = int(value)
    return parsed if parsed > 0 else None


def _query_tokens(value: str) -> list[str]:
    normalized = re.sub(r"[,:;]+", " ", value)
    return [token for token in normalized.split() if token]


def _category_rating_column(category: str | None):
    if category == "blitz":
        return CatalogPlayer.blitz_rating
    if category == "rapid":
        return CatalogPlayer.rapid_rating
    return CatalogPlayer.standard_rating
