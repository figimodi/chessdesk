from __future__ import annotations

import re
from pathlib import Path


ROOT = Path(__file__).resolve().parent
DATA_DIR = ROOT / "data"
OUTPUT_DIR = ROOT / "output"
OUTPUT_FILE = OUTPUT_DIR / "matches.pgn"


def split_games(content: str) -> list[str]:
    normalized = content.replace("\r\n", "\n").strip()
    if not normalized:
        return []
    return [
        chunk.strip()
        for chunk in re.split(r"(?=\[Event\s)", normalized)
        if chunk.strip()
    ]


def strip_annotations(moves: str) -> str:
    result: list[str] = []
    in_braces = 0
    in_variation = 0
    in_semicolon_comment = False
    i = 0

    while i < len(moves):
        char = moves[i]

        if in_semicolon_comment:
            if char == "\n":
                in_semicolon_comment = False
                result.append(" ")
            i += 1
            continue

        if in_braces:
            if char == "{":
                in_braces += 1
            elif char == "}":
                in_braces -= 1
            i += 1
            continue

        if in_variation:
            if char == "(":
                in_variation += 1
            elif char == ")":
                in_variation -= 1
            i += 1
            continue

        if char == "{":
            in_braces = 1
        elif char == "(":
            in_variation = 1
        elif char == ";":
            in_semicolon_comment = True
        elif char == "$":
            i += 1
            while i < len(moves) and moves[i].isdigit():
                i += 1
            continue
        else:
            result.append(char)

        i += 1

    cleaned = "".join(result)
    cleaned = re.sub(r"\s+", " ", cleaned).strip()
    cleaned = re.sub(r"(?<=\S)[?!]+", "", cleaned)
    return cleaned


def clean_game(game_text: str) -> str:
    parts = game_text.split("\n\n", 1)
    headers = parts[0].strip()
    moves = parts[1].strip() if len(parts) > 1 else ""
    cleaned_moves = strip_annotations(moves)
    return f"{headers}\n\n{cleaned_moves}".strip()


def main() -> None:
    input_files = sorted(DATA_DIR.glob("*.pgn"))
    if not input_files:
        raise SystemExit(f"No PGN files found in {DATA_DIR}")

    cleaned_games: list[str] = []
    for input_file in input_files:
        cleaned_games.extend(
            clean_game(game)
            for game in split_games(input_file.read_text(encoding="utf-8"))
        )

    OUTPUT_DIR.mkdir(exist_ok=True)
    OUTPUT_FILE.write_text("\n\n".join(cleaned_games) + "\n", encoding="utf-8")
    print(f"Wrote {len(cleaned_games)} games to {OUTPUT_FILE}")


if __name__ == "__main__":
    main()
