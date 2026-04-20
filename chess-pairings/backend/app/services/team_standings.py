from collections import defaultdict

from app.models.pairing import PairingResult
from app.models.tournament import Tournament
from app.schemas.team import TeamStandingEntry


TEAM_DEFAULT_TIE_BREAKS = ["individual_points", "head_to_head", "weighted_sonneborn"]


class TeamStandingsService:
    def build_standings(self, tournament: Tournament) -> list[TeamStandingEntry]:
        player_team_ids = {entry.player_id: entry.team_id for entry in tournament.players}
        generated_rounds = [round_model for round_model in sorted(tournament.rounds, key=lambda item: item.number) if round_model.pairings]
        if generated_rounds and any(pairing.result == PairingResult.unplayed for pairing in generated_rounds[-1].pairings):
            locked_rounds = generated_rounds[:-1]
        else:
            locked_rounds = generated_rounds

        match_points = defaultdict(float)
        individual_points = defaultdict(float)
        head_to_head = defaultdict(lambda: defaultdict(lambda: {"match": 0.0, "individual": 0.0}))
        encounters = defaultdict(set)
        weighted_components = defaultdict(list)

        for round_model in locked_rounds:
            for match in self._round_matches(round_model.pairings):
                white_team_id = player_team_ids.get(match[0].white_player_id)
                black_team_id = player_team_ids.get(match[0].black_player_id) if match[0].black_player_id is not None else None
                if white_team_id is None:
                    continue

                if black_team_id is None:
                    white_board_points = sum(float(pairing.white_points) for pairing in match)
                    match_points[white_team_id] += float(tournament.match_points_win or 2)
                    individual_points[white_team_id] += white_board_points
                    continue

                white_board_points = sum(float(pairing.white_points) for pairing in match)
                black_board_points = sum(float(pairing.black_points) for pairing in match)
                white_match_points, black_match_points = self._match_points(tournament, white_board_points, black_board_points)

                match_points[white_team_id] += white_match_points
                match_points[black_team_id] += black_match_points
                individual_points[white_team_id] += white_board_points
                individual_points[black_team_id] += black_board_points
                encounters[white_team_id].add(black_team_id)
                encounters[black_team_id].add(white_team_id)
                head_to_head[white_team_id][black_team_id]["match"] += white_match_points
                head_to_head[white_team_id][black_team_id]["individual"] += white_board_points
                head_to_head[black_team_id][white_team_id]["match"] += black_match_points
                head_to_head[black_team_id][white_team_id]["individual"] += black_board_points

        for round_model in locked_rounds:
            for match in self._round_matches(round_model.pairings):
                white_team_id = player_team_ids.get(match[0].white_player_id)
                black_team_id = player_team_ids.get(match[0].black_player_id) if match[0].black_player_id is not None else None
                if white_team_id is None or black_team_id is None:
                    continue

                white_board_points = sum(float(pairing.white_points) for pairing in match)
                black_board_points = sum(float(pairing.black_points) for pairing in match)
                weighted_components[white_team_id].append(match_points[black_team_id] * white_board_points)
                weighted_components[black_team_id].append(match_points[white_team_id] * black_board_points)

        standings = [
            TeamStandingEntry(
                team_id=team.id,
                name=team.name,
                match_points=match_points[team.id],
                individual_points=individual_points[team.id],
                head_to_head_applies=False,
                weighted_sonneborn=sum(weighted_components[team.id]),
            )
            for team in tournament.teams
        ]

        tie_breaks = [item for item in (tournament.tie_breaks or "").split(",") if item] or TEAM_DEFAULT_TIE_BREAKS
        standings.sort(key=lambda item: (-item.match_points, item.name))
        groups = self._group_by_match_points(standings)

        for criterion in tie_breaks:
            next_groups: list[list[TeamStandingEntry]] = []
            for group in groups:
                if len(group) <= 1:
                    next_groups.append(group)
                    continue
                if criterion == "individual_points":
                    next_groups.extend(self._group_by_value(group, lambda item: item.individual_points))
                    continue
                if criterion == "head_to_head":
                    next_groups.extend(self._split_head_to_head(group, head_to_head, encounters))
                    continue
                if criterion == "weighted_sonneborn":
                    next_groups.extend(self._group_by_value(group, lambda item: item.weighted_sonneborn))
                    continue
                next_groups.append(group)
            groups = next_groups

        flattened: list[TeamStandingEntry] = []
        for group in groups:
            flattened.extend(group)
        return flattened

    def _round_matches(self, pairings):
        grouped = defaultdict(list)
        for pairing in pairings:
            key = pairing.match_number or pairing.board_number
            grouped[key].append(pairing)
        return [sorted(grouped[key], key=lambda item: item.board_number) for key in sorted(grouped)]

    def _match_points(self, tournament: Tournament, white_points: float, black_points: float) -> tuple[float, float]:
        if white_points > black_points:
            return float(tournament.match_points_win or 2), float(tournament.match_points_loss or 0)
        if black_points > white_points:
            return float(tournament.match_points_loss or 0), float(tournament.match_points_win or 2)
        return float(tournament.match_points_draw or 1), float(tournament.match_points_draw or 1)

    def _group_by_match_points(self, standings: list[TeamStandingEntry]) -> list[list[TeamStandingEntry]]:
        groups: list[list[TeamStandingEntry]] = []
        for item in standings:
            if groups and groups[-1][0].match_points == item.match_points:
                groups[-1].append(item)
            else:
                groups.append([item])
        return groups

    def _group_by_value(self, group: list[TeamStandingEntry], selector):
        grouped = defaultdict(list)
        for item in group:
            grouped[selector(item)].append(item)
        return [sorted(grouped[key], key=lambda item: item.name) for key in sorted(grouped.keys(), reverse=True)]

    def _split_head_to_head(self, group, head_to_head, encounters):
        group_ids = {item.team_id for item in group}
        if any((group_ids - {item.team_id}) - encounters[item.team_id] for item in group):
            return [group]

        scored = []
        for item in group:
            match_score = 0.0
            individual_score = 0.0
            for opponent_id in group_ids - {item.team_id}:
                match_score += head_to_head[item.team_id][opponent_id]["match"]
                individual_score += head_to_head[item.team_id][opponent_id]["individual"]
            scored.append(
                TeamStandingEntry(
                    team_id=item.team_id,
                    name=item.name,
                    match_points=item.match_points,
                    individual_points=item.individual_points,
                    head_to_head_applies=True,
                    head_to_head_match_points=match_score,
                    head_to_head_individual_points=individual_score,
                    weighted_sonneborn=item.weighted_sonneborn,
                )
            )

        grouped = defaultdict(list)
        for item in scored:
            grouped[(item.head_to_head_match_points, item.head_to_head_individual_points)].append(item)
        return [sorted(grouped[key], key=lambda item: item.name) for key in sorted(grouped.keys(), reverse=True)]
