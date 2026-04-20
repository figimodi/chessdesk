from collections import defaultdict
from decimal import Decimal
from math import log10

from app.models.pairing import PairingResult
from app.models.tournament import Tournament, TournamentPlayer
from app.schemas.pairing import StandingEntry
from app.services.seeding import get_player_seed_numbers
from app.services.time_control import get_time_control_category


DEFAULT_TIE_BREAKS = ["buchholz_cut1", "buchholz", "sonneborn_berger"]


class StandingsService:
    def build_standings(self, tournament: Tournament) -> list[StandingEntry]:
        generated_rounds = [
            round_model
            for round_model in sorted(tournament.rounds, key=lambda item: item.number)
            if round_model.pairings
        ]
        if generated_rounds and any(pairing.result == PairingResult.unplayed for pairing in generated_rounds[-1].pairings):
            locked_rounds = generated_rounds[:-1]
        else:
            locked_rounds = generated_rounds

        scores: dict[int, Decimal] = defaultdict(lambda: Decimal("0.0"))
        opponents: dict[int, list[int]] = defaultdict(list)
        sonneborn: dict[int, Decimal] = defaultdict(lambda: Decimal("0.0"))
        played_games: dict[int, int] = defaultdict(int)
        wins: dict[int, int] = defaultdict(int)
        black_wins: dict[int, int] = defaultdict(int)

        players_by_id = {entry.player_id: entry for entry in tournament.players}
        rating_category = get_time_control_category(tournament.time_control)
        seed_numbers = get_player_seed_numbers(tournament)
        elo_changes = self._elo_changes(tournament, players_by_id, rating_category, locked_rounds)

        for round_model in locked_rounds:
            for pairing in round_model.pairings:
                white_id = pairing.white_player_id
                black_id = pairing.black_player_id
                scores[white_id] += Decimal(str(pairing.white_points))

                if pairing.result != PairingResult.unplayed:
                    played_games[white_id] += 1
                if pairing.result == PairingResult.white_win:
                    wins[white_id] += 1

                if black_id is not None:
                    scores[black_id] += Decimal(str(pairing.black_points))
                    opponents[white_id].append(black_id)
                    opponents[black_id].append(white_id)
                    if pairing.result != PairingResult.unplayed:
                        played_games[black_id] += 1
                    if pairing.result == PairingResult.black_win:
                        wins[black_id] += 1
                        black_wins[black_id] += 1

        for round_model in locked_rounds:
            for pairing in round_model.pairings:
                if pairing.black_player_id is None or pairing.result == PairingResult.unplayed:
                    continue

                white_score = scores[pairing.white_player_id]
                black_score = scores[pairing.black_player_id]

                if pairing.result == PairingResult.white_win:
                    sonneborn[pairing.white_player_id] += black_score
                elif pairing.result == PairingResult.black_win:
                    sonneborn[pairing.black_player_id] += white_score
                elif pairing.result == PairingResult.draw:
                    sonneborn[pairing.white_player_id] += black_score / 2
                    sonneborn[pairing.black_player_id] += white_score / 2

        standings: list[StandingEntry] = []
        for association in tournament.players:
            player = players_by_id[association.player_id].player
            rated_opponents, performance_score = self._performance_inputs(
                players_by_id,
                rating_category,
                association.player_id,
                locked_rounds,
            )
            average_opponent_rating = round(sum(rated_opponents) / len(rated_opponents)) if rated_opponents else None
            opponent_scores = sorted(
                [scores[opponent_id] for opponent_id in opponents[association.player_id]]
            )
            buchholz = sum(opponent_scores)
            buchholz_cut1 = sum(opponent_scores[1:]) if len(opponent_scores) > 1 else sum(opponent_scores)
            standings.append(
                StandingEntry(
                    player_id=association.player_id,
                    full_name=player.full_name,
                    federation=player.federation,
                    team_board_order=association.team_board_order,
                    seed_number=seed_numbers.get(association.player_id),
                    rating=association.initial_rating or player.rating,
                    rapid_rating=player.rapid_rating,
                    blitz_rating=player.blitz_rating,
                    team_id=association.team_id,
                    team_name=association.team.name if association.team else None,
                    points=float(scores[association.player_id]),
                    buchholz=float(buchholz),
                    buchholz_cut1=float(buchholz_cut1),
                    sonneborn_berger=float(sonneborn[association.player_id]),
                    average_opponent_rating=average_opponent_rating,
                    performance_rating=self._performance_rating(rated_opponents, performance_score),
                    elo_change=elo_changes.get(association.player_id),
                    played_games=played_games[association.player_id],
                    wins=wins[association.player_id],
                    black_wins=black_wins[association.player_id],
                )
            )

        tie_breaks = [item for item in (tournament.tie_breaks or "").split(",") if item] or DEFAULT_TIE_BREAKS

        standings = sorted(standings, key=lambda item: (-item.points, item.full_name))
        groups = self._group_by_points(standings)
        for criterion in tie_breaks:
            next_groups: list[list[StandingEntry]] = []
            for group in groups:
                if len(group) <= 1:
                    next_groups.append(group)
                    continue
                next_groups.extend(self._split_group(group, criterion, locked_rounds))
            groups = next_groups

        flattened: list[StandingEntry] = []
        for group in groups:
            flattened.extend(group)
        return flattened

    def _group_by_points(self, standings: list[StandingEntry]) -> list[list[StandingEntry]]:
        groups: list[list[StandingEntry]] = []
        for item in standings:
            if groups and groups[-1][0].points == item.points:
                groups[-1].append(item)
            else:
                groups.append([item])
        return groups

    def _split_group(self, group: list[StandingEntry], criterion: str, rounds) -> list[list[StandingEntry]]:
        if criterion == "direct_encounter" and len(group) == 2:
            left, right = group
            result = self._direct_encounter(left.player_id, right.player_id, rounds)
            if result > 0:
                return [[left], [right]]
            if result < 0:
                return [[right], [left]]
            return [group]

        grouped: dict[tuple, list[StandingEntry]] = {}
        for item in group:
            key = self._criterion_key(item, criterion)
            grouped.setdefault(key, []).append(item)

        ordered_keys = sorted(grouped.keys(), reverse=True)
        return [sorted(grouped[key], key=lambda item: item.full_name) for key in ordered_keys]

    def _criterion_key(self, item: StandingEntry, criterion: str):
        if criterion == "buchholz_cut1":
            return (item.buchholz_cut1,)
        if criterion == "buchholz":
            return (item.buchholz,)
        if criterion == "sonneborn_berger":
            return (item.sonneborn_berger,)
        if criterion == "rating":
            return (float(item.rating or 0),)
        if criterion == "played_games":
            return (float(item.played_games),)
        if criterion == "wins_black":
            return (float(item.wins), float(item.black_wins))
        return (0.0,)

    def _performance_inputs(
        self,
        players_by_id: dict[int, TournamentPlayer],
        category: str,
        player_id: int,
        rounds,
    ) -> tuple[list[int], float]:
        opponent_ratings: list[int] = []
        score = Decimal("0.0")

        for round_model in rounds:
            for pairing in round_model.pairings:
                if pairing.result == PairingResult.unplayed or pairing.black_player_id is None:
                    continue

                if pairing.white_player_id == player_id:
                    opponent_id = pairing.black_player_id
                    player_score = Decimal(str(pairing.white_points))
                elif pairing.black_player_id == player_id:
                    opponent_id = pairing.white_player_id
                    player_score = Decimal(str(pairing.black_points))
                else:
                    continue

                opponent_rating = self._rating_for_category(players_by_id.get(opponent_id), category)
                if opponent_rating is None:
                    continue

                opponent_ratings.append(opponent_rating)
                score += player_score

        return opponent_ratings, float(score)

    def _performance_rating(self, opponent_ratings: list[int], score: float) -> int | None:
        if not opponent_ratings:
            return None

        average_rating = sum(opponent_ratings) / len(opponent_ratings)
        games_count = len(opponent_ratings)
        if score <= 0:
            return round(average_rating - 800)
        if score >= games_count:
            return round(average_rating + 800)

        score_ratio = score / games_count
        rating_delta = -400 * log10((1 / score_ratio) - 1)
        return round(average_rating + rating_delta)

    def _elo_changes(self, tournament: Tournament, players_by_id: dict[int, TournamentPlayer], category: str, rounds) -> dict[int, float | None]:
        if not tournament.is_elo_rated:
            return {}

        ratings: dict[int, float] = {}
        initial_ratings: dict[int, float] = {}
        for player_id, association in players_by_id.items():
            rating = self._rating_for_category(association, category)
            if rating is None:
                continue
            ratings[player_id] = float(rating)
            initial_ratings[player_id] = float(rating)

        for round_model in rounds:
            for pairing in round_model.pairings:
                if pairing.black_player_id is None or pairing.result in {
                    PairingResult.unplayed,
                    PairingResult.white_forfeit_win,
                    PairingResult.black_forfeit_win,
                    PairingResult.double_forfeit_loss,
                    PairingResult.double_forfeit_win,
                }:
                    continue

                white_id = pairing.white_player_id
                black_id = pairing.black_player_id
                white_rating = ratings.get(white_id)
                black_rating = ratings.get(black_id)
                white_k = self._k_factor_for_category(players_by_id.get(white_id), category)
                black_k = self._k_factor_for_category(players_by_id.get(black_id), category)
                if white_rating is None or black_rating is None:
                    continue

                white_score = float(pairing.white_points)
                black_score = float(pairing.black_points)
                white_expected = 1 / (1 + 10 ** ((black_rating - white_rating) / 400))
                black_expected = 1 / (1 + 10 ** ((white_rating - black_rating) / 400))
                ratings[white_id] = white_rating + white_k * (white_score - white_expected)
                ratings[black_id] = black_rating + black_k * (black_score - black_expected)

        return {
            player_id: round(ratings[player_id] - initial_ratings[player_id], 1)
            for player_id in ratings
        }

    def _rating_for_category(self, association, category: str) -> int | None:
        if association is None:
            return None

        player = association.player
        if category == "blitz":
            return player.blitz_rating or player.rating
        if category == "rapid":
            return player.rapid_rating or player.rating
        return association.initial_rating or player.rating

    def _k_factor_for_category(self, association, category: str) -> int:
        if association is None:
            return 20

        player = association.player
        if category == "blitz":
            return player.blitz_k or player.standard_k or 20
        if category == "rapid":
            return player.rapid_k or player.standard_k or 20
        return player.standard_k or 20

    def _direct_encounter(self, left_player_id: int, right_player_id: int, rounds) -> int:
        left_score = Decimal("0.0")
        right_score = Decimal("0.0")
        played = False
        for round_model in rounds:
            for pairing in round_model.pairings:
                if pairing.white_player_id == left_player_id and pairing.black_player_id == right_player_id:
                    left_score += Decimal(str(pairing.white_points))
                    right_score += Decimal(str(pairing.black_points))
                    played = True
                elif pairing.white_player_id == right_player_id and pairing.black_player_id == left_player_id:
                    left_score += Decimal(str(pairing.black_points))
                    right_score += Decimal(str(pairing.white_points))
                    played = True
        if not played:
            return 0
        if left_score > right_score:
            return 1
        if right_score > left_score:
            return -1
        return 0
