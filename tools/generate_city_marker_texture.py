"""Generates the city marker flat texture used by the map editor.

The script mirrors the texture generation logic baked into MapEditor so that
we can check in a deterministic PNG ahead of time.
"""
from __future__ import annotations

import random
import math
from pathlib import Path

from PIL import Image

PRESET_KEY = "city_marker"
GRID_SIZE = 64
EXPORT_SIZE = 512
BASE_COLOR = "#6f9151"
ACCENT_COLOR = "#4c6d39"
ACCENT_CHANCE = 0.14
HIGHLIGHT_COLOR = "#9fbe6d"
HIGHLIGHT_CHANCE = 0.09
NOISE = 18


def clamp_channel(value: int) -> int:
    return max(0, min(255, value))


def hex_to_rgb(color: str) -> tuple[int, int, int]:
    stripped = color.lstrip("#")
    if len(stripped) != 6:
        raise ValueError(f"Niepoprawny kolor HEX: {color}")
    return int(stripped[0:2], 16), int(stripped[2:4], 16), int(stripped[4:6], 16)


def adjust_rgb(rgb: tuple[int, int, int], delta: tuple[int, int, int]) -> tuple[int, int, int]:
    return tuple(clamp_channel(channel + shift) for channel, shift in zip(rgb, delta))


def point_in_polygon(x: float, y: float, poly: list[tuple[float, float]]) -> bool:
    num = len(poly)
    j = num - 1
    inside = False
    for i in range(num):
        if ((poly[i][1] > y) != (poly[j][1] > y)) and (
            x < (poly[j][0] - poly[i][0]) * (y - poly[i][1]) / (poly[j][1] - poly[i][1] + 1e-10) + poly[i][0]
        ):
            inside = not inside
        j = i
    return inside


def get_hex_vertices(center_x: float, center_y: float, size: float) -> list[tuple[float, float]]:
    return [
        (center_x - size, center_y),
        (center_x - size / 2, center_y - (math.sqrt(3) / 2) * size),
        (center_x + size / 2, center_y - (math.sqrt(3) / 2) * size),
        (center_x + size, center_y),
        (center_x + size / 2, center_y + (math.sqrt(3) / 2) * size),
        (center_x - size / 2, center_y + (math.sqrt(3) / 2) * size),
    ]


def _build_hex_mask(grid_size: int) -> list[list[bool]]:
    center = grid_size / 2.0
    radius = grid_size / 2.0 - 0.5
    vertices = get_hex_vertices(center, center, radius)
    mask = [[False for _ in range(grid_size)] for _ in range(grid_size)]
    for row in range(grid_size):
        for col in range(grid_size):
            sample_points = [
                (col + 0.5, row + 0.5),
                (col, row),
                (col + 1.0, row),
                (col, row + 1.0),
                (col + 1.0, row + 1.0),
            ]
            if any(point_in_polygon(px, py, vertices) for px, py in sample_points):
                mask[row][col] = True
                continue
            for vx, vy in vertices:
                if col <= vx <= col + 1 and row <= vy <= row + 1:
                    mask[row][col] = True
                    break
    return mask


def _generate_pixels() -> list[list[tuple[int, int, int, int] | None]]:
    mask = _build_hex_mask(GRID_SIZE)
    rng = random.Random(f"{PRESET_KEY}-{GRID_SIZE}")
    base_rgb = hex_to_rgb(BASE_COLOR)
    accent_rgb = hex_to_rgb(ACCENT_COLOR)
    highlight_rgb = hex_to_rgb(HIGHLIGHT_COLOR)

    pixels: list[list[tuple[int, int, int, int] | None]] = [
        [None for _ in range(GRID_SIZE)] for _ in range(GRID_SIZE)
    ]
    for row in range(GRID_SIZE):
        for col in range(GRID_SIZE):
            if not mask[row][col]:
                continue
            delta = (
                rng.randint(-NOISE, NOISE),
                rng.randint(-NOISE, NOISE),
                rng.randint(-NOISE, NOISE),
            )
            pixel_rgb = adjust_rgb(base_rgb, delta)
            # Delicate accents and highlights to mimic the supplied texture.
            roll = rng.random()
            if roll < ACCENT_CHANCE:
                pixel_rgb = accent_rgb
            elif roll < ACCENT_CHANCE + HIGHLIGHT_CHANCE:
                pixel_rgb = highlight_rgb
            pixels[row][col] = (*pixel_rgb, 255)
    return pixels


def _pixels_to_image(pixels: list[list[tuple[int, int, int, int] | None]]) -> Image.Image:
    img = Image.new("RGBA", (GRID_SIZE, GRID_SIZE), (0, 0, 0, 0))
    for row in range(GRID_SIZE):
        for col in range(GRID_SIZE):
            value = pixels[row][col]
            if value is not None:
                img.putpixel((col, row), value)
    return img


def main() -> None:
    root = Path(__file__).resolve().parent.parent
    asset_root = root / "assets"
    output_path = asset_root / "terrain" / "hex_painted" / f"flat_{PRESET_KEY}_{GRID_SIZE}.png"
    output_path.parent.mkdir(parents=True, exist_ok=True)

    pixels = _generate_pixels()
    img = _pixels_to_image(pixels)
    export = img.resize((EXPORT_SIZE, EXPORT_SIZE), Image.NEAREST)
    export.save(output_path)
    print(f"Generated {output_path.relative_to(root)}")


if __name__ == "__main__":
    main()
