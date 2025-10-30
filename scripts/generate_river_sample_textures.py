from __future__ import annotations

import sys
import math
from datetime import datetime
from pathlib import Path
from typing import Iterable, Sequence

BASE_DIR = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(BASE_DIR / "edytory"))

from generate_river_hex_tile import (  # type: ignore
    DEFAULT_BANK_OFFSET,
    DEFAULT_BANK_VARIATION,
    RiverCenterlineOptions,
    TributaryOptions,
    generate_centerline,
)


AXIAL_DIRECTION_TO_SIDE = {
    (1, 0): "bottom_right",
    (1, -1): "top_right",
    (0, -1): "top",
    (-1, 0): "top_left",
    (-1, 1): "bottom_left",
    (0, 1): "bottom",
}

SIDE_OPPOSITE = {
    "top": "bottom",
    "top_right": "bottom_left",
    "bottom_right": "top_left",
    "bottom": "top",
    "bottom_left": "top_right",
    "top_left": "bottom_right",
}

AXIAL_DIRECTION_TO_CARTESIAN = {
    (1, 0): (1.5, math.sqrt(3.0) / 2.0),
    (1, -1): (1.5, -math.sqrt(3.0) / 2.0),
    (0, -1): (0.0, -math.sqrt(3.0)),
    (-1, 0): (-1.5, -math.sqrt(3.0) / 2.0),
    (-1, 1): (-1.5, math.sqrt(3.0) / 2.0),
    (0, 1): (0.0, math.sqrt(3.0)),
}

ASSET_ROOT = BASE_DIR / "assets"
RIVER_OUTPUT_DIR = ASSET_ROOT / "terrain" / "hex_painted" / "river_tool"
RIVER_OUTPUT_DIR.mkdir(parents=True, exist_ok=True)


def entry_exit_for_index(index: int, segments: Sequence[tuple[int, int]]) -> tuple[str, str]:
    if not segments:
        return "top", "bottom"
    if index == 0:
        exit_side = AXIAL_DIRECTION_TO_SIDE[segments[0]]
        entry_side = SIDE_OPPOSITE[exit_side]
        return entry_side, exit_side
    if index == len(segments):
        entry_side = SIDE_OPPOSITE[AXIAL_DIRECTION_TO_SIDE[segments[-1]]]
        exit_side = AXIAL_DIRECTION_TO_SIDE[segments[-1]]
        return entry_side, exit_side
    entry_side = SIDE_OPPOSITE[AXIAL_DIRECTION_TO_SIDE[segments[index - 1]]]
    exit_side = AXIAL_DIRECTION_TO_SIDE[segments[index]]
    return entry_side, exit_side


def accumulate_axial(segments: Sequence[tuple[int, int]]) -> list[tuple[int, int]]:
    coords = [(0, 0)]
    for dq, dr in segments:
        last_q, last_r = coords[-1]
        coords.append((last_q + dq, last_r + dr))
    return coords


def to_rel(path: Path) -> str:
    try:
        return str(path.relative_to(ASSET_ROOT))
    except ValueError:
        return str(path)


SAMPLES: Iterable[dict] = [
    {
        "name": "doplyw_lagodny_lewy",
        "segments": [(1, 0), (0, 1), (0, 1)],
        "grid_size": 64,
        "shape_preference": "curve",
        "strength": 0.6,
        "noise": 0.2,
        "frequency": 1.8,
        "seed": 931,
        "background": "terrain/hex_painted/flat_grass_fields_64.png",
        "tributary": {
            "index": 2,
            "entry_side": "top_right",
            "join_ratio": 0.45,
            "shape": "curve",
            "shape_strength": 0.7,
            "noise_amplitude": 0.25,
            "noise_frequency": 2.2,
            "shape_direction_mode": "left",
            "seed_offset": 1_000_123,
        },
    },
    {
        "name": "doplyw_ostry_prawy",
        "segments": [(1, 0), (1, -1), (1, -1)],
        "grid_size": 64,
        "shape_preference": "auto",
        "strength": 0.5,
        "noise": 0.3,
        "frequency": 1.4,
        "seed": 1337,
        "background": "terrain/hex_painted/flat_grass_sandy_mix_64.png",
        "tributary": {
            "index": 1,
            "entry_side": "bottom_left",
            "join_ratio": 0.65,
            "shape": "turn",
            "shape_strength": 0.85,
            "noise_amplitude": 0.4,
            "noise_frequency": 2.8,
            "shape_direction_mode": "right",
            "seed_offset": 1_000_456,
        },
    },
    {
        "name": "doplyw_pola",
        "segments": [(1, 0), (1, 0), (0, 1)],
        "grid_size": 64,
        "shape_preference": "auto",
        "strength": 0.55,
        "noise": 0.18,
        "frequency": 1.9,
        "seed": 2410,
        "bank_offset": DEFAULT_BANK_OFFSET * 0.95,
        "bank_variation": DEFAULT_BANK_VARIATION * 1.15,
        "background": "terrain/hex_painted/flat_grass_fields_64.png",
        "tributary": {
            "index": 2,
            "entry_side": "top_right",
            "join_ratio": 0.5,
            "shape": "curve",
            "shape_strength": 0.72,
            "noise_amplitude": 0.2,
            "noise_frequency": 2.4,
            "shape_direction_mode": "left",
            "seed_offset": 1_001_200,
        },
    },
    {
        "name": "doplyw_piaszczysty",
        "segments": [(1, 0), (1, -1), (1, -1), (0, -1)],
        "grid_size": 64,
        "shape_preference": "auto",
        "strength": 0.65,
        "noise": 0.28,
        "frequency": 2.5,
        "seed": 3891,
        "bank_offset": DEFAULT_BANK_OFFSET * 1.2,
        "bank_variation": DEFAULT_BANK_VARIATION,
        "background": "terrain/hex_painted/flat_grass_sandy_mix_64.png",
        "tributary": {
            "index": 1,
            "entry_side": "bottom_left",
            "join_ratio": 0.52,
            "shape": "turn",
            "shape_strength": 0.9,
            "noise_amplitude": 0.35,
            "noise_frequency": 3.0,
            "shape_direction_mode": "right",
            "seed_offset": 1_001_450,
        },
    },
    {
        "name": "doplyw_blotny",
        "segments": [(1, 0), (0, 1), (-1, 1), (-1, 1)],
        "grid_size": 64,
        "shape_preference": "auto",
        "strength": 0.48,
        "noise": 0.22,
        "frequency": 1.7,
        "seed": 5127,
        "bank_offset": DEFAULT_BANK_OFFSET,
        "bank_variation": DEFAULT_BANK_VARIATION * 1.25,
        "background": "terrain/hex_painted/flat_grass_muddy_mix_64.png",
        "tributary": {
            "index": 3,
            "entry_side": "bottom_right",
            "join_ratio": 0.6,
            "shape": "curve",
            "shape_strength": 0.68,
            "noise_amplitude": 0.18,
            "noise_frequency": 2.1,
            "shape_direction_mode": "left",
            "seed_offset": 1_001_780,
        },
    },
    {
        "name": "doplyw_waska_dolina",
        "segments": [(0, 1), (1, 0), (1, -1)],
        "grid_size": 64,
        "shape_preference": "auto",
        "strength": 0.58,
        "noise": 0.24,
        "frequency": 2.2,
        "seed": 3105,
        "bank_offset": DEFAULT_BANK_OFFSET * 1.05,
        "bank_variation": DEFAULT_BANK_VARIATION,
        "background": "terrain/hex_painted/flat_grass_fields_64.png",
        "tributary": {
            "index": 1,
            "entry_side": "bottom_left",
            "join_ratio": 0.42,
            "shape": "curve",
            "shape_strength": 0.75,
            "noise_amplitude": 0.22,
            "noise_frequency": 2.6,
            "shape_direction_mode": "left",
            "seed_offset": 1_002_050,
        },
    },
    {
        "name": "doplyw_wschodni_zbieg",
        "segments": [(1, -1), (1, 0), (0, 1)],
        "grid_size": 64,
        "shape_preference": "auto",
        "strength": 0.62,
        "noise": 0.26,
        "frequency": 2.1,
        "seed": 4219,
        "bank_offset": DEFAULT_BANK_OFFSET,
        "bank_variation": DEFAULT_BANK_VARIATION * 1.1,
        "background": "terrain/hex_painted/flat_grass_sandy_mix_64.png",
        "tributary": {
            "index": 2,
            "entry_side": "top_right",
            "join_ratio": 0.47,
            "shape": "turn",
            "shape_strength": 0.82,
            "noise_amplitude": 0.27,
            "noise_frequency": 2.9,
            "shape_direction_mode": "left",
            "seed_offset": 1_002_210,
        },
    },
    {
        "name": "doplyw_zachodni_zbieg",
        "segments": [(-1, 1), (-1, 0), (0, -1)],
        "grid_size": 64,
        "shape_preference": "turn",
        "strength": 0.53,
        "noise": 0.19,
        "frequency": 1.7,
        "seed": 2874,
        "bank_offset": DEFAULT_BANK_OFFSET * 0.9,
        "bank_variation": DEFAULT_BANK_VARIATION * 1.2,
        "background": "terrain/hex_painted/flat_grass_muddy_mix_64.png",
        "tributary": {
            "index": 1,
            "entry_side": "bottom",
            "join_ratio": 0.55,
            "shape": "curve",
            "shape_strength": 0.68,
            "noise_amplitude": 0.21,
            "noise_frequency": 2.0,
            "shape_direction_mode": "right",
            "seed_offset": 1_002_380,
        },
    },
    {
        "name": "doplyw_polnocny",
        "segments": [(0, -1), (1, -1), (1, 0)],
        "grid_size": 64,
        "shape_preference": "auto",
        "strength": 0.57,
        "noise": 0.23,
        "frequency": 2.3,
        "seed": 3541,
        "bank_offset": DEFAULT_BANK_OFFSET,
        "bank_variation": DEFAULT_BANK_VARIATION,
        "background": "terrain/hex_painted/flat_grass_fields_64.png",
        "tributary": {
            "index": 2,
            "entry_side": "top_left",
            "join_ratio": 0.52,
            "shape": "curve",
            "shape_strength": 0.74,
            "noise_amplitude": 0.24,
            "noise_frequency": 2.7,
            "shape_direction_mode": "right",
            "seed_offset": 1_002_560,
        },
    },
    {
        "name": "doplyw_poludniowy",
        "segments": [(0, 1), (-1, 1), (-1, 0)],
        "grid_size": 64,
        "shape_preference": "auto",
        "strength": 0.6,
        "noise": 0.25,
        "frequency": 2.4,
        "seed": 3998,
        "bank_offset": DEFAULT_BANK_OFFSET * 1.1,
        "bank_variation": DEFAULT_BANK_VARIATION * 0.9,
        "background": "terrain/hex_painted/flat_grass_fields_64.png",
        "tributary": {
            "index": 2,
            "entry_side": "bottom",
            "join_ratio": 0.48,
            "shape": "curve",
            "shape_strength": 0.7,
            "noise_amplitude": 0.23,
            "noise_frequency": 2.5,
            "shape_direction_mode": "left",
            "seed_offset": 1_002_710,
        },
    },
    {
        "name": "doplyw_meandrujacy",
        "segments": [(1, 0), (0, -1), (-1, 0), (0, 1)],
        "grid_size": 64,
        "shape_preference": "auto",
        "strength": 0.64,
        "noise": 0.29,
        "frequency": 2.8,
        "seed": 4685,
        "bank_offset": DEFAULT_BANK_OFFSET * 1.15,
        "bank_variation": DEFAULT_BANK_VARIATION,
        "background": "terrain/hex_painted/flat_grass_sandy_mix_64.png",
        "tributary": {
            "index": 2,
            "entry_side": "top_right",
            "join_ratio": 0.44,
            "shape": "turn",
            "shape_strength": 0.88,
            "noise_amplitude": 0.32,
            "noise_frequency": 3.1,
            "shape_direction_mode": "right",
            "seed_offset": 1_002_890,
        },
    },
    {
        "name": "doplyw_srodkowy",
        "segments": [(1, 0), (1, -1), (0, -1)],
        "grid_size": 64,
        "shape_preference": "auto",
        "strength": 0.52,
        "noise": 0.21,
        "frequency": 1.9,
        "seed": 5129,
        "bank_offset": DEFAULT_BANK_OFFSET,
        "bank_variation": DEFAULT_BANK_VARIATION * 1.05,
        "background": "terrain/hex_painted/flat_grass_fields_64.png",
        "tributary": {
            "index": 1,
            "entry_side": "bottom",
            "join_ratio": 0.5,
            "shape": "curve",
            "shape_strength": 0.66,
            "noise_amplitude": 0.2,
            "noise_frequency": 2.2,
            "shape_direction_mode": "left",
            "seed_offset": 1_003_040,
        },
    },
    {
        "name": "doplyw_zwinny",
        "segments": [(-1, 0), (-1, 1), (0, 1), (1, 0)],
        "grid_size": 64,
        "shape_preference": "auto",
        "strength": 0.59,
        "noise": 0.27,
        "frequency": 2.6,
        "seed": 5781,
        "bank_offset": DEFAULT_BANK_OFFSET * 1.05,
        "bank_variation": DEFAULT_BANK_VARIATION * 1.1,
        "background": "terrain/hex_painted/flat_grass_muddy_mix_64.png",
        "tributary": {
            "index": 2,
            "entry_side": "bottom_left",
            "join_ratio": 0.46,
            "shape": "curve",
            "shape_strength": 0.78,
            "noise_amplitude": 0.28,
            "noise_frequency": 2.9,
            "shape_direction_mode": "right",
            "seed_offset": 1_003_210,
        },
    },
]


def build_tributary(options: dict | None) -> tuple[TributaryOptions | None, int | None]:
    if not options:
        return None, None
    tributary = TributaryOptions(
        entry_side=options["entry_side"],
        join_ratio=float(options["join_ratio"]),
        shape=options.get("shape", "curve"),
        shape_strength=float(options.get("shape_strength", 0.6)),
        noise_amplitude=float(options.get("noise_amplitude", 0.15)),
        noise_frequency=float(options.get("noise_frequency", 2.0)),
        shape_direction=options.get("shape_direction"),
        shape_direction_mode=options.get("shape_direction_mode", "auto"),
        seed_offset=int(options.get("seed_offset", 1_000_000)),
        bank_offset=options.get("bank_offset"),
        bank_color=options.get("bank_color"),
        bank_variation=options.get("bank_variation"),
    )
    target_index = int(options.get("index", 0))
    return tributary, target_index


def determine_shape(
    index: int,
    segments: Sequence[tuple[int, int]],
    preference: str,
) -> tuple[str, int | None]:
    total_hexes = len(segments) + 1
    pref = preference if preference in {"auto", "straight", "curve", "turn"} else "auto"
    if pref == "auto":
        entry_side, exit_side = entry_exit_for_index(index, segments)
        if SIDE_OPPOSITE.get(entry_side) == exit_side:
            shape = "straight"
        else:
            shape = "turn" if 0 < index < total_hexes - 1 else "straight"
    else:
        shape = pref

    shape_direction = None
    if shape == "turn" and 0 < index < len(segments):
        prev_delta = segments[index - 1]
        next_delta = segments[index]
        vec_in = AXIAL_DIRECTION_TO_CARTESIAN.get(prev_delta)
        vec_out = AXIAL_DIRECTION_TO_CARTESIAN.get(next_delta)
        if vec_in and vec_out:
            cross = vec_in[0] * vec_out[1] - vec_in[1] * vec_out[0]
            if cross < -1e-6:
                shape_direction = 1
            elif cross > 1e-6:
                shape_direction = -1
    return shape, shape_direction


def main() -> None:
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    summary: list[str] = []

    for sample in SAMPLES:
        name = sample["name"]
        segments: Sequence[tuple[int, int]] = sample["segments"]
        coords = accumulate_axial(segments)
        tributary_cfg = sample.get("tributary")
        tributary, target_index = build_tributary(tributary_cfg)

        if tributary is None or target_index is None:
            print(f"[WARN] Pomijam próbkę {name}: brak zdefiniowanego dopływu.")
            continue
        if target_index < 0 or target_index >= len(coords):
            print(f"[WARN] Pomijam próbkę {name}: index dopływu {target_index} poza zakresem.")
            continue

        grid_size = int(sample.get("grid_size", 128))
        strength = float(sample.get("strength", 0.5))
        noise = float(sample.get("noise", 0.2))
        frequency = float(sample.get("frequency", 2.0))
        seed_base = int(sample.get("seed", 0))
        bank_offset = float(sample.get("bank_offset", DEFAULT_BANK_OFFSET))
        bank_variation = float(sample.get("bank_variation", DEFAULT_BANK_VARIATION))
        shape_preference = sample.get("shape_preference", "auto")
        shape_direction_override = sample.get("shape_direction")
        background_path = None
        background_spec = sample.get("background")
        if background_spec:
            candidate = ASSET_ROOT / background_spec
            if candidate.exists():
                background_path = candidate
            else:
                print(f"[WARN] Tło {background_spec} nie istnieje, pomijam dla próbki {name}.")

        sample_dir = RIVER_OUTPUT_DIR / name
        sample_dir.mkdir(parents=True, exist_ok=True)

        generated = []
        for idx, (q, r) in enumerate(coords):
            if idx != target_index:
                continue
            entry_side, exit_side = entry_exit_for_index(idx, segments)
            tributary_for_hex = None
            if entry_side == tributary.entry_side or exit_side == tributary.entry_side:
                print(
                    f"[WARN] Pomijam próbkę {name}: dopływ koliduje z kierunkiem głównego nurtu (hex {idx})."
                )
                tributary_for_hex = None
            else:
                tributary_for_hex = tributary

            shape_value, auto_direction = determine_shape(idx, segments, shape_preference)
            shape_direction = shape_direction_override if shape_direction_override is not None else auto_direction

            options = RiverCenterlineOptions(
                grid_size=grid_size,
                background=background_path,
                entry_side=entry_side,
                exit_side=exit_side,
                shape=shape_value,
                shape_strength=strength,
                shape_direction=shape_direction,
                noise_amplitude=noise,
                noise_frequency=frequency,
                seed=seed_base + idx,
                bank_offset=bank_offset,
                bank_variation=bank_variation,
                tributary=tributary_for_hex,
            )

            filename = f"sample_{name}_{idx:02d}_{timestamp}.png"
            output_path = sample_dir / filename
            result = generate_centerline(options, output_path)
            generated.append((output_path, result.metadata_path))

        generated_rel = ", ".join(to_rel(path) for path, _ in generated)
        summary.append(f"{name}: {generated_rel}")

    print("Wygenerowano zestaw próbek rzek:")
    for line in summary:
        print(" -", line)


if __name__ == "__main__":
    main()
