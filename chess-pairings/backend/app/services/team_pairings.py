from fastapi import HTTPException

from app.models.tournament import Tournament
from app.services.team_standings import TeamStandingsService
from app.services.time_control import get_time_control_category


class TeamPairingsService:
    def generate_next_round(self, tournament: Tournament, round_number: int) -> list[dict]:
        eligible_teams = [team for team in self._ordered_teams(tournament) if team.is_active and self._is_team_available(team, round_number)]
        rows: list[dict] = []
        boards = tournament.boards_per_match or 0
        bye_team = None

        if len(eligible_teams) % 2 != 0:
            bye_team = eligible_teams.pop()

        if bye_team is not None:
            bye_lineup = self._lineup_for_round(tournament, bye_team, round_number)
            if len(bye_lineup) < boards:
                raise HTTPException(
                    status_code=409,
                    detail=f"La squadra {bye_team.name} deve avere almeno {boards} giocatori schierabili per il turno {round_number}.",
                )
            for board_number in range(1, boards + 1):
                rows.append(
                    {
                        "match_number": 1,
                        "board_number": board_number,
                        "white_player_id": bye_lineup[board_number - 1].player_id,
                        "black_player_id": None,
                        "is_bye": True,
                    }
                )

        match_offset = 1 if bye_team is not None else 0
        for match_number, index in enumerate(range(0, len(eligible_teams), 2), start=1 + match_offset):
            white_team = eligible_teams[index]
            black_team = eligible_teams[index + 1]
            white_lineup = self._lineup_for_round(tournament, white_team, round_number)
            black_lineup = self._lineup_for_round(tournament, black_team, round_number)

            if len(white_lineup) < boards or len(black_lineup) < boards:
                raise HTTPException(
                    status_code=409,
                    detail=f"Le squadre {white_team.name} e {black_team.name} devono avere almeno {boards} giocatori disponibili per il turno {round_number}.",
                )

            for board_number in range(1, boards + 1):
                rows.append(
                    {
                        "match_number": match_number,
                        "board_number": board_number,
                        "white_player_id": white_lineup[board_number - 1].player_id,
                        "black_player_id": black_lineup[board_number - 1].player_id,
                        "is_bye": False,
                    }
                )

        return rows

    def _is_team_available(self, team, round_number: int) -> bool:
        availability_map = {item.round_number: item.is_available for item in team.availabilities}
        return availability_map.get(round_number, team.is_active)

    def _ordered_teams(self, tournament: Tournament):
        generated_rounds = [round_model for round_model in tournament.rounds if round_model.pairings]
        if len(generated_rounds) <= 1:
            return sorted(tournament.teams, key=lambda team: (-self._team_seed_rating(tournament, team), team.name))

        standings = TeamStandingsService().build_standings(tournament)
        standings_by_id = {entry.team_id: index for index, entry in enumerate(standings)}
        return sorted(tournament.teams, key=lambda team: (standings_by_id.get(team.id, 10**9), team.name))

    def _team_seed_rating(self, tournament: Tournament, team) -> float:
        category = get_time_control_category(tournament.time_control)
        ratings = []
        for member in team.members:
            player = member.player
            if category == "blitz":
                ratings.append(player.blitz_rating or player.rating or 0)
            elif category == "rapid":
                ratings.append(player.rapid_rating or player.rating or 0)
            else:
                ratings.append(member.initial_rating or player.rating or 0)
        return sum(ratings) / len(ratings) if ratings else 0

    def _lineup_for_round(self, tournament: Tournament, team, round_number: int):
        availability_map = {item.round_number: item.is_available for item in team.availabilities}
        if not team.is_active or not availability_map.get(round_number, team.is_active):
            return []

        ordered_members = sorted(team.members, key=lambda item: (item.team_board_order or 10**9, item.player.full_name))
        boards = tournament.boards_per_match or 0
        if len(ordered_members) <= boards:
            return [member for member in ordered_members if member.is_active and round_number >= member.start_round_number]

        lineup_map = {
            item.tournament_player_id: item.is_selected
            for item in team.lineups
            if item.round_number == round_number
        }
        available_members = []
        for member in ordered_members:
            default_selected = member.is_active and round_number >= member.start_round_number and (member.team_board_order or 10**9) <= boards
            is_selected = lineup_map.get(member.id, default_selected)
            if member.is_active and is_selected:
                available_members.append(member)

        if tournament.enforce_board_order:
            return available_members

        return sorted(available_members, key=lambda item: (-(item.initial_rating or item.player.rating or 0), item.player.full_name))
