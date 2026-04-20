from app.models.tournament import Tournament, TournamentPlayer
from app.services.time_control import get_time_control_category


def get_player_seed_numbers(tournament: Tournament) -> dict[int, int]:
    ordered_players = sorted(
        tournament.players,
        key=lambda entry: (
            -(get_player_seed_rating(entry, tournament) or 0),
            entry.player.full_name,
        ),
    )

    assigned_numbers = {
        entry.seed_number
        for entry in ordered_players
        if entry.seed_number is not None and entry.seed_number > 0
    }
    next_available = 1
    seed_numbers: dict[int, int] = {}

    for entry in ordered_players:
        if entry.seed_number is not None and entry.seed_number > 0:
            seed_numbers[entry.player_id] = entry.seed_number
            continue

        while next_available in assigned_numbers:
            next_available += 1

        seed_numbers[entry.player_id] = next_available
        assigned_numbers.add(next_available)
        next_available += 1

    return seed_numbers


def get_player_seed_rating(entry: TournamentPlayer, tournament: Tournament) -> int | None:
    category = get_time_control_category(tournament.time_control)
    if category == "blitz":
        return entry.player.blitz_rating or entry.player.rating
    if category == "rapid":
        return entry.player.rapid_rating or entry.player.rating
    return entry.initial_rating or entry.player.rating
