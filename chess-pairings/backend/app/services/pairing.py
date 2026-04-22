from fastapi import HTTPException
from sqlalchemy import delete, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models.pairing import Pairing, PairingResult
from app.models.round import Round
from app.models.tournament import RoundStatus, Tournament, TournamentPlayer
from app.models.user import User
from app.schemas.pairing import PairingBoardOrderUpdate, PairingCreateResponse, PairingResultUpdate
from app.services.bbp_pairings import BbpPairingsService
from app.services.standings import StandingsService
from app.services.team_pairings import TeamPairingsService
from app.services import tournament as tournament_service


async def get_pairing(db: AsyncSession, pairing_id: int, user: User) -> Pairing | None:
    result = await db.execute(
        select(Pairing)
        .where(Pairing.id == pairing_id)
        .options(selectinload(Pairing.round).selectinload(Round.tournament))
    )
    pairing = result.scalar_one_or_none()
    if pairing is None:
        return None
    if user.role.value != "admin" and pairing.round.tournament.owner_id != user.id:
        return None
    return pairing


async def _get_round(db: AsyncSession, round_id: int) -> Round | None:
    result = await db.execute(
        select(Round)
        .where(Round.id == round_id)
        .options(
            selectinload(Round.tournament).selectinload(Tournament.players).selectinload(TournamentPlayer.team),
            selectinload(Round.pairings).selectinload(Pairing.white_player),
            selectinload(Round.pairings).selectinload(Pairing.black_player),
        )
    )
    return result.scalar_one_or_none()


def _generated_rounds(tournament: Tournament) -> list[Round]:
    return [
        round_model
        for round_model in sorted(tournament.rounds, key=lambda item: item.number)
        if round_model.pairings
    ]


def _latest_generated_round(tournament: Tournament) -> Round | None:
    rounds = _generated_rounds(tournament)
    return rounds[-1] if rounds else None


def _assert_latest_round_completed(tournament: Tournament) -> None:
    latest_round = _latest_generated_round(tournament)
    if latest_round is None:
        return

    if any(pairing.result == PairingResult.unplayed for pairing in latest_round.pairings):
        raise HTTPException(
            status_code=409,
            detail=f"Inserisci tutti i risultati del turno {latest_round.number} prima di generare il turno successivo.",
        )


async def generate_pairings(
    db: AsyncSession, tournament: Tournament
) -> PairingCreateResponse:
    tournament_id = tournament.id
    if not tournament.is_registration_closed:
        raise HTTPException(
            status_code=409,
            detail="Prima di generare il primo turno devi chiudere le iscrizioni del torneo.",
        )

    _assert_latest_round_completed(tournament)

    next_round = next(
        (
            round_model
            for round_model in sorted(tournament.rounds, key=lambda item: item.number)
            if not round_model.pairings
        ),
        None,
    )

    if next_round is None:
        latest_round = _latest_generated_round(tournament)
        if latest_round is None:
            raise HTTPException(status_code=404, detail="Nessun turno disponibile")
        return PairingCreateResponse(
            round=tournament_service.serialize_round(latest_round),
            standings=StandingsService().build_standings(tournament),
        )

    if tournament.type.value in ("team", "quadriglia"):
        rows = TeamPairingsService().generate_next_round(tournament, next_round.number)
    else:
        rows = BbpPairingsService().generate_next_round(tournament)

    for index, row in enumerate(rows, start=1):
        db.add(
                Pairing(
                    round_id=next_round.id,
                    match_number=row.get("match_number"),
                    board_number=row.get("board_number", index),
                    white_player_id=row["white_player_id"],
                    black_player_id=row.get("black_player_id"),
                    is_bye=row.get("is_bye", False),
                    result=PairingResult.bye.value if row.get("is_bye") else PairingResult.unplayed.value,
                    white_points=1 if row.get("is_bye") else 0,
                    black_points=0,
                )
            )

    next_round.status = RoundStatus.published
    await db.commit()

    db.expire_all()
    refreshed_tournament = await tournament_service._get_tournament_unscoped(db, tournament_id)
    refreshed_round = await _get_round(db, next_round.id)

    return PairingCreateResponse(
        round=tournament_service.serialize_round(refreshed_round),
        standings=StandingsService().build_standings(refreshed_tournament),
    )


async def update_pairing_result(
    db: AsyncSession, pairing: Pairing, data: PairingResultUpdate
) -> dict:
    round_result = await db.execute(
        select(Round)
        .where(Round.id == pairing.round_id)
        .options(selectinload(Round.tournament).selectinload(Tournament.rounds).selectinload(Round.pairings))
    )
    round_model = round_result.scalar_one()
    tournament = round_model.tournament
    latest_round = _latest_generated_round(tournament)

    if latest_round is None or latest_round.id != pairing.round_id:
        raise HTTPException(
            status_code=409,
            detail="Puoi modificare i risultati solo dell'ultimo turno generato. Per modificare un turno precedente devi prima eliminare i turni successivi.",
        )

    if tournament.type.value == "quadriglia" and pairing.match_number is not None:
        match_pairings = [item for item in round_model.pairings if item.match_number == pairing.match_number]
        for match_pairing in match_pairings:
            _apply_pairing_result(match_pairing, data.result)
    else:
        _apply_pairing_result(pairing, data.result)

    await db.commit()

    round_model = await _get_round(db, pairing.round_id)
    if round_model and round_model.pairings and all(
        item.result != PairingResult.unplayed for item in round_model.pairings
    ):
        round_model.status = RoundStatus.completed
        await db.commit()

    return {"ok": True, "pairingId": pairing.id, "result": pairing.result}


def _apply_pairing_result(pairing: Pairing, result: PairingResult) -> None:
    pairing.result = result

    if result == PairingResult.white_win:
        pairing.white_points = 1
        pairing.black_points = 0
    elif result == PairingResult.black_win:
        pairing.white_points = 0
        pairing.black_points = 1
    elif result == PairingResult.draw:
        pairing.white_points = 0.5
        pairing.black_points = 0.5
    elif result == PairingResult.white_forfeit_win:
        pairing.white_points = 1
        pairing.black_points = 0
    elif result == PairingResult.black_forfeit_win:
        pairing.white_points = 0
        pairing.black_points = 1
    elif result == PairingResult.double_forfeit_loss:
        pairing.white_points = 0
        pairing.black_points = 0
    elif result == PairingResult.double_forfeit_win:
        pairing.white_points = 1
        pairing.black_points = 1
    elif result == PairingResult.bye:
        pairing.white_points = 1
        pairing.black_points = 0
    else:
        pairing.white_points = 0
        pairing.black_points = 0


async def update_pairing_board_order(
    db: AsyncSession, pairing: Pairing, data: PairingBoardOrderUpdate
) -> dict:
    if data.side not in ("white", "black"):
        raise HTTPException(status_code=400, detail="Lato non valido.")
    if data.target_pairing_id <= 0:
        raise HTTPException(status_code=400, detail="Abbinamento di destinazione non valido.")

    round_result = await db.execute(
        select(Round)
        .where(Round.id == pairing.round_id)
        .options(selectinload(Round.tournament).selectinload(Tournament.rounds).selectinload(Round.pairings))
    )
    round_model = round_result.scalar_one()
    tournament = round_model.tournament
    latest_round = _latest_generated_round(tournament)

    if tournament.type.value not in ("team", "quadriglia"):
        raise HTTPException(status_code=409, detail="Questa funzione e disponibile solo per i tornei a squadre.")
    if tournament.enforce_board_order:
        raise HTTPException(status_code=409, detail="Non puoi cambiare l'ordine delle scacchiere quando l'ordine e obbligatorio.")
    if latest_round is None or latest_round.id != pairing.round_id:
        raise HTTPException(status_code=409, detail="Puoi riordinare le scacchiere solo dell'ultimo turno generato.")

    match_number = pairing.match_number or pairing.board_number
    match_pairings = sorted(
        [item for item in round_model.pairings if (item.match_number or item.board_number) == match_number],
        key=lambda item: item.board_number,
    )
    if any(item.result != PairingResult.unplayed for item in match_pairings):
        raise HTTPException(status_code=409, detail="Puoi cambiare l'ordine delle scacchiere solo se tutte le partite del match sono ancora senza risultato.")

    current_pairing = next((item for item in match_pairings if item.id == pairing.id), None)
    target_pairing = next((item for item in match_pairings if item.id == data.target_pairing_id), None)
    if current_pairing is None or target_pairing is None:
        raise HTTPException(status_code=404, detail="Abbinamento non trovato")
    if current_pairing.id == target_pairing.id:
        return {"ok": True, "pairingId": pairing.id}
    if data.side == "white":
        current_pairing.white_player_id, target_pairing.white_player_id = target_pairing.white_player_id, current_pairing.white_player_id
    else:
        current_pairing.black_player_id, target_pairing.black_player_id = target_pairing.black_player_id, current_pairing.black_player_id
    await db.commit()
    return {"ok": True, "pairingId": pairing.id}


async def delete_latest_round(db: AsyncSession, tournament: Tournament) -> dict:
    latest_round = _latest_generated_round(tournament)
    if latest_round is None:
        raise HTTPException(status_code=409, detail="Non ci sono turni generati da eliminare.")

    await db.execute(delete(Pairing).where(Pairing.round_id == latest_round.id))
    latest_round.status = RoundStatus.pending
    await db.commit()

    refreshed_tournament = await tournament_service._get_tournament_unscoped(db, tournament.id)
    return {
        "ok": True,
        "deletedRound": latest_round.number,
        "standings": StandingsService().build_standings(refreshed_tournament),
    }
