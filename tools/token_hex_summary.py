"""Utility to list the hexes visited by each token during a log session.

Usage:
    python tools/token_hex_summary.py ai/logs/tokens/text/2025-10-06.log
"""
from __future__ import annotations

import argparse
import re
from collections import OrderedDict
from pathlib import Path
from typing import Iterable, List, Tuple

TOKEN_PREFIX = re.compile(r"\[TOKEN\]\s+([^:]+):")
MOVE_STEP = re.compile(r"ruch na \((-?\d+),\s*(-?\d+)\)")
START_Q = re.compile(r"position_q=(-?\d+)")
START_R = re.compile(r"position_r=(-?\d+)")


Coord = Tuple[int, int]
PathMap = "OrderedDict[str, List[Coord]]"


def add_coord(storage: OrderedDict[str, List[Coord]], token_id: str, coord: Coord) -> None:
    path = storage.setdefault(token_id, [])
    if not path or path[-1] != coord:
        path.append(coord)


def parse_log(path: Path) -> OrderedDict[str, List[Coord]]:
    paths: OrderedDict[str, List[Coord]] = OrderedDict()
    with path.open("r", encoding="utf-8") as handle:
        for raw_line in handle:
            line = raw_line.strip()
            token_match = TOKEN_PREFIX.search(line)
            if not token_match:
                continue
            token_id = token_match.group(1).strip()

            if "start tury" in line:
                q_match = START_Q.search(line)
                r_match = START_R.search(line)
                if q_match and r_match:
                    coord = (int(q_match.group(1)), int(r_match.group(1)))
                    add_coord(paths, token_id, coord)

            move_match = MOVE_STEP.search(line)
            if move_match:
                coord = (int(move_match.group(1)), int(move_match.group(2)))
                add_coord(paths, token_id, coord)
    return paths


def main(argv: Iterable[str] | None = None) -> None:
    parser = argparse.ArgumentParser(description="List hex coordinates visited by tokens in a log")
    parser.add_argument("log_path", type=Path, help="Path to the token log file")
    parser.add_argument(
        "--prefix",
        metavar="PREFIX",
        help="Limit output to tokens starting with this prefix (e.g. 'Z_' for zaopatrzenie)",
    )
    parser.add_argument(
        "--unique",
        action="store_true",
        help="Show unique coordinates only (sorted by first occurrence)",
    )
    args = parser.parse_args(list(argv) if argv is not None else None)

    if not args.log_path.exists():
        raise SystemExit(f"Log file not found: {args.log_path}")

    paths = parse_log(args.log_path)
    selected = (
        {token: coords for token, coords in paths.items() if token.startswith(args.prefix)}
        if args.prefix
        else paths
    )

    for token, coords in selected.items():
        if args.unique:
            unique_coords: List[Coord] = []
            seen: set[Coord] = set()
            for coord in coords:
                if coord not in seen:
                    seen.add(coord)
                    unique_coords.append(coord)
            coords = unique_coords
        coord_list = ", ".join(f"({q},{r})" for q, r in coords)
        print(f"{token}: {coord_list}")


if __name__ == "__main__":
    main()
