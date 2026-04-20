import shutil
import subprocess
from pathlib import Path

from app.core.config import settings
from app.core.exceptions import PairingEngineError
from app.models.pairing import PairingResult
from app.models.tournament import Tournament


class BbpPairingsService:
    def __init__(self) -> None:
        self.bin_path = settings.BBP_PAIRINGS_BIN
        self.system = settings.BBP_PAIRINGS_SYSTEM
        self.work_dir = Path(settings.PAIRINGS_WORK_DIR)
        self.work_dir.mkdir(parents=True, exist_ok=True)

    def generate_next_round(self, tournament: Tournament) -> list[dict]:
        cli_exists = shutil.which(self.bin_path) or Path(self.bin_path).exists()
        if not cli_exists:
            raise PairingEngineError(
                f"bbpPairings binary not found at '{self.bin_path}'. Install it or update BBP_PAIRINGS_BIN."
            )

        return self._run_bbp_cli(tournament)

    def _run_bbp_cli(self, tournament: Tournament) -> list[dict]:
        input_path = self.work_dir / f"tournament_{tournament.id}.trf"
        output_path = self.work_dir / f"tournament_{tournament.id}_paired.txt"
        checklist_path = self.work_dir / f"tournament_{tournament.id}_checklist.txt"
        input_path.write_text(self._serialize_trf(tournament), encoding="utf-8")

        command = [self.bin_path, f"--{self.system}", str(input_path), "-p", str(output_path), "-l", str(checklist_path)]
        completed = subprocess.run(command, check=False, capture_output=True, text=True)
        if completed.returncode != 0:
            raise PairingEngineError(completed.stderr.strip() or "unknown bbpPairings error")

        return self._parse_pairings_output(output_path, tournament)

    def _serialize_trf(self, tournament: Tournament) -> str:
        next_round_number = self._get_next_round_number(tournament)
        ordered_players = self._ordered_players(tournament)
        pairing_numbers = {
            entry.player_id: index for index, entry in enumerate(ordered_players, start=1)
        }

        lines = [f"012 {tournament.name}", "XXC white1"]
        for index, entry in enumerate(ordered_players, start=1):
            lines.append(
                self._build_player_line(
                    entry=entry,
                    pairing_number=index,
                    pairing_numbers=pairing_numbers,
                    rounds=[round_model for round_model in sorted(tournament.rounds, key=lambda item: item.number) if round_model.number < next_round_number],
                )
            )
        unavailable_pairing_numbers = self._unavailable_pairing_numbers(
            ordered_players,
            pairing_numbers,
            next_round_number,
        )
        if unavailable_pairing_numbers:
            lines.append(self._build_byes_line(next_round_number, unavailable_pairing_numbers))
        lines.append(f"XXR {next_round_number}")
        return "\n".join(lines) + "\n"

    def _ordered_players(self, tournament: Tournament):
        next_round_number = self._get_next_round_number(tournament)
        return sorted(
            [
                entry
                for entry in tournament.players
                if entry.is_active and entry.start_round_number <= next_round_number
            ],
            key=lambda entry: (
                entry.seed_number or 10**9,
                -(entry.initial_rating or entry.player.rating or 0),
                entry.player.full_name,
            ),
        )

    def _get_next_round_number(self, tournament: Tournament) -> int:
        for round_model in sorted(tournament.rounds, key=lambda item: item.number):
            if not round_model.pairings:
                return round_model.number
        raise PairingEngineError("No available round found for pairing generation")

    def _unavailable_pairing_numbers(self, ordered_players, pairing_numbers: dict[int, int], round_number: int) -> list[int]:
        unavailable = []
        for entry in ordered_players:
            availability = next(
                (item for item in entry.availabilities if item.round_number == round_number),
                None,
            )
            if availability is not None and not availability.is_available:
                unavailable.append(pairing_numbers[entry.player_id])
        return unavailable

    def _build_byes_line(self, round_number: int, pairing_numbers: list[int]) -> str:
        return f"240   {round_number:03d} " + " ".join(f"{number:04d}" for number in pairing_numbers)

    def _build_player_line(self, entry, pairing_number: int, pairing_numbers: dict[int, int], rounds: list) -> str:
        rating = entry.initial_rating or entry.player.rating or 0
        score = 0.0
        blocks: list[str] = []

        for round_model in rounds:
            player_pairing = next(
                (
                    pairing
                    for pairing in round_model.pairings
                    if pairing.white_player_id == entry.player_id or pairing.black_player_id == entry.player_id
                ),
                None,
            )
            if player_pairing is None:
                blocks.append(" " * 10)
                continue

            if player_pairing.result == PairingResult.unplayed:
                raise PairingEngineError(
                    f"Round {round_model.number} is not completed. Cannot generate the next round."
                )

            if player_pairing.is_bye:
                score += float(player_pairing.white_points)
                blocks.append("0000 - U  ")
                continue

            if player_pairing.white_player_id == entry.player_id:
                opponent_number = pairing_numbers[player_pairing.black_player_id]
                score += float(player_pairing.white_points)
                result_char = self._result_char(player_pairing.result, is_white=True)
                blocks.append(f"{opponent_number:>4} w {result_char}  ")
            else:
                opponent_number = pairing_numbers[player_pairing.white_player_id]
                score += float(player_pairing.black_points)
                result_char = self._result_char(player_pairing.result, is_white=False)
                blocks.append(f"{opponent_number:>4} b {result_char}  ")

        line = [" "] * (91 + len(blocks) * 10)
        line[0:4] = list("001 ")
        line[4:8] = list(f"{pairing_number:>4}")
        display_name = entry.player.full_name[:33].ljust(33)
        line[14:47] = list(display_name)
        line[48:52] = list(f"{rating:>4}")
        line[80:84] = list(f"{score:>4.1f}")
        line[84:91] = list(f"{pairing_number:>7}")
        for index, block in enumerate(blocks):
            start = 91 + index * 10
            line[start : start + 10] = list(block[:10].ljust(10))
        return "".join(line).rstrip()

    def _result_char(self, result: PairingResult, is_white: bool) -> str:
        if result == PairingResult.draw:
            return "="
        if result == PairingResult.white_win:
            return "1" if is_white else "0"
        if result == PairingResult.black_win:
            return "0" if is_white else "1"
        raise PairingEngineError(f"Unsupported pairing result '{result}' for bbpPairings export")

    def _parse_pairings_output(self, output_path: Path, tournament: Tournament) -> list[dict]:
        content = output_path.read_text(encoding="utf-8").splitlines()
        if not content:
            raise PairingEngineError("bbpPairings produced an empty output file")

        ordered_players = self._ordered_players(tournament)
        by_pairing_number = {
            index: entry.player_id for index, entry in enumerate(ordered_players, start=1)
        }

        rows: list[dict] = []
        for line in content[1:]:
            if not line.strip():
                continue
            parts = line.split()
            if len(parts) != 2:
                raise PairingEngineError(f"Invalid bbpPairings output line: '{line}'")

            white_number, black_number = (int(parts[0]), int(parts[1]))
            white_player_id = by_pairing_number.get(white_number)
            if white_player_id is None:
                raise PairingEngineError(f"Unknown white pairing number '{white_number}' in bbpPairings output")

            if black_number == 0:
                rows.append(
                    {
                        "white_player_id": white_player_id,
                        "black_player_id": None,
                        "is_bye": True,
                    }
                )
                continue

            black_player_id = by_pairing_number.get(black_number)
            if black_player_id is None:
                raise PairingEngineError(f"Unknown black pairing number '{black_number}' in bbpPairings output")

            rows.append(
                {
                    "white_player_id": white_player_id,
                    "black_player_id": black_player_id,
                    "is_bye": False,
                }
            )

        return rows
