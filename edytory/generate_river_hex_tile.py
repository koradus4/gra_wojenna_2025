"""Minimal river centerline generator for hex tiles.

This script draws only the central course of a river as a sequence of black squares.
It mirrors the pixel-grid workflow from the map editor so the output can be reused
later when full river rendering is implemented.
"""

from __future__ import annotations

import argparse
import json
import math
import random
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, Iterable, List, Sequence, Tuple

from PIL import Image


ASSET_DIR = Path("assets/terrain/hex_painted")
DEFAULT_OUTPUT_DIR = ASSET_DIR / "river_contours"
EXPORT_SIZE_BY_GRID = {64: 512, 128: 1024}
CENTERLINE_COLOR = (0, 0, 0, 255)

PATH_SHAPES = ("straight", "curve", "turn")
PATH_SHAPE_LABELS: Dict[str, str] = {
	"straight": "Prosty",
	"curve": "Zakole",
	"turn": "Zawrót",
}

SHAPE_DIRECTION_CHOICES = ("auto", "left", "right")
SHAPE_DIRECTION_LABELS: Dict[str, str] = {
	"auto": "Losowo",
	"left": "Lewo",
	"right": "Prawo",
}


HEX_SIDES = (
	"top",
	"top_right",
	"bottom_right",
	"bottom",
	"bottom_left",
	"top_left",
)

HEX_SIDE_LABELS: Dict[str, str] = {
	"top": "Górna",
	"top_right": "Górna prawa",
	"bottom_right": "Dolna prawa",
	"bottom": "Dolna",
	"bottom_left": "Dolna lewa",
	"top_left": "Górna lewa",
}


def _shape_direction_mode_from_value(value: int | None) -> str:
	if value == 1:
		return "left"
	if value == -1:
		return "right"
	return "auto"


@dataclass
class RiverCenterlineOptions:
	grid_size: int
	background: Path | None
	entry_side: str
	exit_side: str
	shape: str
	shape_strength: float
	shape_direction: int | None
	seed: int


@dataclass
class RiverCenterlineResult:
	image_path: Path
	metadata_path: Path
	metadata: Dict[str, Any]


def list_flat_backgrounds(directory: Path = ASSET_DIR) -> Dict[str, Path]:
	backgrounds: Dict[str, Path] = {}
	if not directory.exists():
		return backgrounds
	for path in sorted(directory.glob("flat_*.png")):
		backgrounds[path.stem] = path.resolve()
	return backgrounds


def point_in_polygon(x: float, y: float, polygon: Sequence[Tuple[float, float]]) -> bool:
	inside = False
	j = len(polygon) - 1
	for i, (ix, iy) in enumerate(polygon):
		jx, jy = polygon[j]
		intersects = ((iy > y) != (jy > y)) and (
			x < (jx - ix) * (y - iy) / ((jy - iy) + 1e-10) + ix
		)
		if intersects:
			inside = not inside
		j = i
	return inside


def get_hex_vertices(center_x: float, center_y: float, size: float) -> List[Tuple[float, float]]:
	sqrt3 = math.sqrt(3.0)
	return [
		(center_x - size, center_y),
		(center_x - size / 2.0, center_y - (sqrt3 / 2.0) * size),
		(center_x + size / 2.0, center_y - (sqrt3 / 2.0) * size),
		(center_x + size, center_y),
		(center_x + size / 2.0, center_y + (sqrt3 / 2.0) * size),
		(center_x - size / 2.0, center_y + (sqrt3 / 2.0) * size),
	]


def build_hex_mask(grid: int) -> List[List[bool]]:
	center = grid / 2.0
	radius = grid / 2.0 - 0.5
	vertices = get_hex_vertices(center, center, radius)
	mask = [[False for _ in range(grid)] for _ in range(grid)]
	for row in range(grid):
		for col in range(grid):
			samples = [
				(col + 0.5, row + 0.5),
				(col, row),
				(col + 1.0, row),
				(col, row + 1.0),
				(col + 1.0, row + 1.0),
			]
			if any(point_in_polygon(sx, sy, vertices) for sx, sy in samples):
				mask[row][col] = True
				continue
			for vx, vy in vertices:
				if col <= vx <= col + 1 and row <= vy <= row + 1:
					mask[row][col] = True
					break
	return mask


def load_background_pixels(
	grid: int,
	mask: Sequence[Sequence[bool]],
	texture_path: Path | None,
) -> List[List[Tuple[int, int, int, int] | None]]:
	pixels: List[List[Tuple[int, int, int, int] | None]] = [
		[None for _ in range(grid)]
		for _ in range(grid)
	]
	if texture_path is None:
		return pixels

	image = Image.open(texture_path).convert("RGBA")
	if image.size != (grid, grid):
		image = image.resize((grid, grid), Image.NEAREST)
	image_pixels = image.load()
	for row in range(grid):
		for col in range(grid):
			if mask[row][col]:
				pixels[row][col] = image_pixels[col, row]
	return pixels


def _hex_center(grid: int) -> Tuple[float, float]:
	coord = grid / 2.0
	return coord, coord


def _hex_polygon(grid: int) -> List[Tuple[float, float]]:
	center = _hex_center(grid)
	radius = grid / 2.0 - 0.5
	return get_hex_vertices(center[0], center[1], radius)


def _is_inside_hex(point: Tuple[float, float], polygon: Sequence[Tuple[float, float]]) -> bool:
	return point_in_polygon(point[0], point[1], polygon)


def _project_inside_hex(
	point: Tuple[float, float],
	grid: int,
	polygon: Sequence[Tuple[float, float]],
) -> Tuple[float, float]:
	if _is_inside_hex(point, polygon):
		return point
	cx, cy = _hex_center(grid)
	x, y = point
	for _ in range(10):
		x = 0.85 * x + 0.15 * cx
		y = 0.85 * y + 0.15 * cy
		if _is_inside_hex((x, y), polygon):
			break
	return x, y


def _side_to_edge_index(side: str) -> int:
	mapping: Dict[str, int] = {
		"top_left": 0,
		"top": 1,
		"top_right": 2,
		"bottom_right": 3,
		"bottom": 4,
		"bottom_left": 5,
	}
	if side not in mapping:
		raise KeyError(f"Nieznana krawędź heksa: {side}")
	return mapping[side]


def pick_flow_endpoints_by_side(
	grid: int,
	entry_side: str,
	exit_side: str,
) -> Tuple[Tuple[float, float], Tuple[float, float]]:
	center = (grid / 2.0, grid / 2.0)
	radius = grid / 2.0 - 0.5
	vertices = get_hex_vertices(center[0], center[1], radius)
	edges = list(zip(vertices, vertices[1:] + vertices[:1]))

	entry_index = _side_to_edge_index(entry_side)
	exit_index = _side_to_edge_index(exit_side)

	entry_edge = edges[entry_index]
	exit_edge = edges[exit_index]

	def midpoint(pair: Tuple[Tuple[float, float], Tuple[float, float]]) -> Tuple[float, float]:
		(a, b) = pair
		return (a[0] + b[0]) * 0.5, (a[1] + b[1]) * 0.5

	start = midpoint(entry_edge)
	end = midpoint(exit_edge)
	return start, end


def _normalize(vec: Tuple[float, float]) -> Tuple[float, float]:
	length = math.hypot(vec[0], vec[1])
	if length < 1e-8:
		return 0.0, 0.0
	return vec[0] / length, vec[1] / length


def _midpoint(a: Tuple[float, float], b: Tuple[float, float]) -> Tuple[float, float]:
	return (a[0] + b[0]) * 0.5, (a[1] + b[1]) * 0.5


def _distance_point_segment(
	point: Tuple[float, float],
	segment_start: Tuple[float, float],
	segment_end: Tuple[float, float],
) -> float:
	ax, ay = segment_start
	bx, by = segment_end
	px, py = point
	vx, vy = bx - ax, by - ay
	if abs(vx) < 1e-9 and abs(vy) < 1e-9:
		return math.hypot(px - ax, py - ay)
	wx, wy = px - ax, py - ay
	v_len_sq = vx * vx + vy * vy
	t = max(0.0, min(1.0, (wx * vx + wy * vy) / v_len_sq))
	cx = ax + vx * t
	cy = ay + vy * t
	return math.hypot(px - cx, py - cy)


def _flatten_bezier_adaptive(
	p0: Tuple[float, float],
	p1: Tuple[float, float],
	p2: Tuple[float, float],
	p3: Tuple[float, float],
	flatness: float,
) -> List[Tuple[float, float]]:
	if max(
		_distance_point_segment(p1, p0, p3),
		_distance_point_segment(p2, p0, p3),
	) <= flatness:
		return [p0, p3]

	m01 = _midpoint(p0, p1)
	m12 = _midpoint(p1, p2)
	m23 = _midpoint(p2, p3)
	m012 = _midpoint(m01, m12)
	m123 = _midpoint(m12, m23)
	m = _midpoint(m012, m123)

	left = _flatten_bezier_adaptive(p0, m01, m012, m, flatness)
	right = _flatten_bezier_adaptive(m, m123, m23, p3, flatness)
	return left[:-1] + right


def supercover_line(x0: int, y0: int, x1: int, y1: int) -> List[Tuple[int, int]]:
	cells: List[Tuple[int, int]] = []
	dx = abs(x1 - x0)
	dy = abs(y1 - y0)
	sx = 1 if x0 < x1 else -1
	sy = 1 if y0 < y1 else -1
	x, y = x0, y0
	err = dx - dy
	cells.append((x, y))
	while x != x1 or y != y1:
		e2 = err * 2
		step_x = e2 > -dy
		step_y = e2 < dx
		if step_x:
			err -= dy
			x += sx
		if step_y:
			err += dx
			y += sy
		cells.append((x, y))
		if step_x and step_y:
			cells.append((x - sx, y))
	seen: set[Tuple[int, int]] = set()
	unique: List[Tuple[int, int]] = []
	for cell in cells:
		if cell not in seen:
			unique.append(cell)
			seen.add(cell)
	return unique


def build_centerline_points(
	start: Tuple[float, float],
	end: Tuple[float, float],
	entry_inward: Tuple[float, float],
	exit_inward: Tuple[float, float],
	shape: str,
	shape_strength: float,
	shape_direction: int | None,
	mask: Sequence[Sequence[bool]],
	rng: random.Random,
) -> Tuple[List[Tuple[float, float]], Dict[str, Any]]:
	grid = len(mask)
	polygon = _hex_polygon(grid)

	dx = end[0] - start[0]
	dy = end[1] - start[1]
	span_len = math.hypot(dx, dy)
	if span_len < 1e-6:
		return [start, end], {
			"control_points": [
				{"x": start[0], "y": start[1]},
				{"x": start[0], "y": start[1]},
				{"x": end[0], "y": end[1]},
				{"x": end[0], "y": end[1]},
			],
			"handle_lengths": {"entry": 0.0, "exit": 0.0},
			"entry_inward": {"x": entry_inward[0], "y": entry_inward[1]},
			"exit_inward": {"x": exit_inward[0], "y": exit_inward[1]},
			"span_direction": {"x": 0.0, "y": 0.0},
			"lateral": {"x": 0.0, "y": 0.0},
		}

	shape_strength = max(0.0, min(shape_strength, 1.0))
	span_dir = _normalize((dx, dy))
	base_handle = span_len * (0.45 if shape == "straight" else (0.6 if shape == "curve" else 0.68))
	base_handle *= 0.85 + 0.3 * shape_strength

	lateral_dir = _normalize((-span_dir[1], span_dir[0]))
	if lateral_dir == (0.0, 0.0):
		lateral_dir = (0.0, 0.0)

	if shape in {"curve", "turn"}:
		if shape_direction in {1, -1}:
			lateral_sign = shape_direction
		else:
			lateral_sign = 1 if rng.random() < 0.5 else -1
		lateral_scale = (0.30 if shape == "curve" else 0.55) * shape_strength * span_len
		lateral = (
			lateral_dir[0] * lateral_scale * lateral_sign,
			lateral_dir[1] * lateral_scale * lateral_sign,
		)
	else:
		lateral_sign = 0
		lateral = (0.0, 0.0)

	p0 = start
	p3 = end
	p1 = (
		start[0] + entry_inward[0] * base_handle + lateral[0] * 0.5,
		start[1] + entry_inward[1] * base_handle + lateral[1] * 0.5,
	)
	p2 = (
		end[0] + exit_inward[0] * base_handle - lateral[0] * 0.5,
		end[1] + exit_inward[1] * base_handle - lateral[1] * 0.5,
	)

	p1 = _project_inside_hex(p1, grid, polygon)
	p2 = _project_inside_hex(p2, grid, polygon)

	points = _flatten_bezier_adaptive(p0, p1, p2, p3, flatness=0.25)

	metadata = {
		"control_points": [
			{"x": p0[0], "y": p0[1]},
			{"x": p1[0], "y": p1[1]},
			{"x": p2[0], "y": p2[1]},
			{"x": p3[0], "y": p3[1]},
		],
		"handle_lengths": {
			"entry": math.hypot(p1[0] - p0[0], p1[1] - p0[1]),
			"exit": math.hypot(p3[0] - p2[0], p3[1] - p2[1]),
		},
		"entry_inward": {"x": entry_inward[0], "y": entry_inward[1]},
		"exit_inward": {"x": exit_inward[0], "y": exit_inward[1]},
		"span_direction": {"x": span_dir[0], "y": span_dir[1]},
		"lateral": {"x": lateral[0], "y": lateral[1]},
		"lateral_sign": lateral_sign,
	}
	return points, metadata


def rasterize_polyline(points: Sequence[Tuple[float, float]]) -> List[Tuple[int, int]]:
	cells: List[Tuple[int, int]] = []
	if len(points) < 2:
		if points:
			cells.append((int(round(points[0][0])), int(round(points[0][1]))))
		return cells

	for a, b in zip(points, points[1:]):
		ax, ay = int(round(a[0])), int(round(a[1]))
		bx, by = int(round(b[0])), int(round(b[1]))
		cells.extend(supercover_line(ax, ay, bx, by))

	deduped: List[Tuple[int, int]] = []
	prev: Tuple[int, int] | None = None
	for cell in cells:
		if cell != prev:
			deduped.append(cell)
		prev = cell
	return deduped


def compose_image(
	grid: int,
	mask: Sequence[Sequence[bool]],
	background: Sequence[Sequence[Tuple[int, int, int, int] | None]],
	centerline_cells: Sequence[Tuple[int, int]],
) -> Image.Image:
	image = Image.new("RGBA", (grid, grid), (0, 0, 0, 0))
	pixels = image.load()
	for row in range(grid):
		for col in range(grid):
			if not mask[row][col]:
				continue
			color = background[row][col]
			if color is None:
				pixels[col, row] = (0, 0, 0, 0)
			else:
				pixels[col, row] = color
	for col, row in centerline_cells:
		if 0 <= row < grid and 0 <= col < grid and mask[row][col]:
			pixels[col, row] = CENTERLINE_COLOR
	export_size = EXPORT_SIZE_BY_GRID.get(grid, grid * 8)
	if export_size == grid:
		return image
	return image.resize((export_size, export_size), Image.NEAREST)


def save_metadata(image_path: Path, metadata: Dict[str, Any]) -> Path:
	meta_path = image_path.with_suffix(".json")
	meta_path.parent.mkdir(parents=True, exist_ok=True)
	with meta_path.open("w", encoding="utf-8") as handle:
		json.dump(metadata, handle, ensure_ascii=True, indent=2)
	return meta_path


def generate_centerline(opts: RiverCenterlineOptions, output_path: Path) -> RiverCenterlineResult:
	rng = random.Random(opts.seed)
	mask = build_hex_mask(opts.grid_size)
	background = load_background_pixels(opts.grid_size, mask, opts.background)

	start, end = pick_flow_endpoints_by_side(opts.grid_size, opts.entry_side, opts.exit_side)
	center = _hex_center(opts.grid_size)
	entry_inward = _normalize((center[0] - start[0], center[1] - start[1]))
	if entry_inward == (0.0, 0.0):
		entry_inward = _normalize((end[0] - start[0], end[1] - start[1]))
	if entry_inward == (0.0, 0.0):
		entry_inward = (0.0, 1.0)
	exit_inward = _normalize((center[0] - end[0], center[1] - end[1]))
	if exit_inward == (0.0, 0.0):
		exit_inward = _normalize((start[0] - end[0], start[1] - end[1]))
	if exit_inward == (0.0, 0.0):
		exit_inward = entry_inward

	centerline_points, shape_metadata = build_centerline_points(
		start,
		end,
		entry_inward,
		exit_inward,
		opts.shape,
		opts.shape_strength,
		opts.shape_direction,
		mask,
		rng,
	)
	centerline_cells = rasterize_polyline(centerline_points)
	centerline_cells = extend_line_to_edges(centerline_cells, mask, entry_inward, exit_inward)

	image = compose_image(opts.grid_size, mask, background, centerline_cells)
	output_path.parent.mkdir(parents=True, exist_ok=True)
	image.save(output_path)

	metadata = {
		"grid": opts.grid_size,
		"entry_side": opts.entry_side,
		"exit_side": opts.exit_side,
		"seed": opts.seed,
		"background": None if opts.background is None else str(opts.background),
		"start": {"x": start[0], "y": start[1]},
		"end": {"x": end[0], "y": end[1]},
		"shape": opts.shape,
		"shape_strength": opts.shape_strength,
		"shape_direction": opts.shape_direction,
		"shape_direction_mode": _shape_direction_mode_from_value(opts.shape_direction),
		"shape_metadata": shape_metadata,
	}
	metadata_path = save_metadata(output_path, metadata)

	return RiverCenterlineResult(
		image_path=output_path,
		metadata_path=metadata_path,
		metadata=metadata,
	)


def extend_line_to_edges(
	centerline_cells: Sequence[Tuple[int, int]],
	mask: Sequence[Sequence[bool]],
	entry_dir: Tuple[float, float],
	exit_dir: Tuple[float, float],
) -> List[Tuple[int, int]]:
	if not centerline_cells:
		return list(centerline_cells)

	ordered = list(centerline_cells)
	deduped: List[Tuple[int, int]] = []
	prev: Tuple[int, int] | None = None
	for cell in ordered:
		if cell != prev:
			deduped.append(cell)
		prev = cell

	if not deduped:
		return deduped

	grid = len(mask)

	def walk_to_edge(cell: Tuple[int, int], direction: Tuple[float, float]) -> List[Tuple[int, int]]:
		dir_norm = _normalize(direction)
		if dir_norm == (0.0, 0.0):
			return []
		x = cell[0] + 0.5
		y = cell[1] + 0.5
		trail: List[Tuple[int, int]] = []
		max_steps = grid * 2
		for _ in range(max_steps):
			x += dir_norm[0]
			y += dir_norm[1]
			col = int(math.floor(x))
			row = int(math.floor(y))
			if not (0 <= row < grid and 0 <= col < grid):
				break
			if not mask[row][col]:
				break
			next_cell = (col, row)
			if trail and next_cell == trail[-1]:
				continue
			trail.append(next_cell)
		return trail

	leading = walk_to_edge(deduped[0], (-entry_dir[0], -entry_dir[1]))
	trailing = walk_to_edge(deduped[-1], (-exit_dir[0], -exit_dir[1]))

	return list(reversed(leading)) + deduped + trailing



def parse_args(argv: Iterable[str] | None = None) -> argparse.Namespace:
	parser = argparse.ArgumentParser(description="Generator centralnego nurtu rzeki na heksie")
	parser.add_argument("--count", type=int, default=1, help="Liczba przykładów do wygenerowania (1-5)")
	parser.add_argument(
		"--background",
		default="transparent",
		help="Nazwa tekstury flat_* lub ścieżka (użyj 'transparent' aby pominąć tło)",
	)
	parser.add_argument(
		"--entry-side",
		choices=list(HEX_SIDES),
		default="top",
		help="Krawędź wejściowa nurtu",
	)
	parser.add_argument(
		"--exit-side",
		choices=list(HEX_SIDES),
		default="bottom",
		help="Krawędź wyjściowa nurtu",
	)
	parser.add_argument(
		"--shape",
		choices=PATH_SHAPES,
		default="straight",
		help="Typ zakrzywienia (prosty, zakole, zawrót)",
	)
	parser.add_argument(
		"--shape-strength",
		type=float,
		default=0.5,
		help="Siła zakrzywienia 0-1",
	)
	parser.add_argument(
		"--shape-direction",
		choices=SHAPE_DIRECTION_CHOICES,
		default="auto",
		help="Kierunek zakrzywienia (losowo/lewo/prawo)",
	)
	parser.add_argument(
		"--grid",
		type=int,
		default=64,
		choices=(64, 128),
		help="Rozmiar siatki heksa",
	)
	parser.add_argument("--seed", type=int, default=42, help="Bazowy seed RNG")
	parser.add_argument(
		"--output-dir",
		type=Path,
		default=DEFAULT_OUTPUT_DIR,
		help="Katalog docelowy",
	)
	parser.add_argument(
		"--prefix",
		default="hex_river_centerline",
		help="Prefiks nazw plików",
	)
	parser.add_argument("--list-backgrounds", action="store_true", help="Wyświetl dostępne tła i zakończ")
	parser.add_argument("--gui", action="store_true", help="Uruchom prosty interfejs graficzny")
	parser.add_argument("--no-gui", action="store_true", help="Wymuś tryb CLI")
	return parser.parse_args(list(argv) if argv is not None else None)


def resolve_background(choice: str, backgrounds: Dict[str, Path]) -> Path | None:
	if not choice or choice.lower() in {"transparent", "none"}:
		return None
	if choice in backgrounds:
		return backgrounds[choice]
	candidate = Path(choice)
	if candidate.exists():
		return candidate.resolve()
	raise FileNotFoundError(f"Nie znaleziono tła: {choice}")


def resolve_shape_direction(choice: str) -> int | None:
	choice = (choice or "auto").lower()
	if choice == "left":
		return 1
	if choice == "right":
		return -1
	return None


def run_cli(args: argparse.Namespace, backgrounds: Dict[str, Path]) -> None:
	try:
		background_path = resolve_background(args.background, backgrounds)
	except FileNotFoundError as err:
		print(err)
		return

	shape_direction_choice = getattr(args, "shape_direction", "auto")
	shape_direction = resolve_shape_direction(shape_direction_choice)
	direction_suffix = "" if shape_direction_choice == "auto" else f"_{shape_direction_choice}"

	if args.entry_side == args.exit_side:
		print("Wejście i wyjście muszą wskazywać różne krawędzie heksa.")
		return

	count = max(1, min(int(args.count), 5))
	args.output_dir.mkdir(parents=True, exist_ok=True)

	for index in range(count):
		seed = args.seed + index
		opts = RiverCenterlineOptions(
			grid_size=args.grid,
			background=background_path,
			entry_side=args.entry_side,
			exit_side=args.exit_side,
			shape=args.shape,
			shape_strength=max(0.0, min(args.shape_strength, 1.0)),
			shape_direction=shape_direction if args.shape in {"curve", "turn"} else None,
			seed=seed,
		)
		suffix = f"{index + 1:02d}"
		bg_label = "transparent" if background_path is None else background_path.stem
		direction_part = direction_suffix if args.shape in {"curve", "turn"} else ""
		file_name = (
			f"{args.prefix}_{bg_label}_{args.entry_side}_to_{args.exit_side}_"
			f"{args.shape}{direction_part}_g{args.grid}_{suffix}.png"
		)
		output_path = args.output_dir / file_name
		result = generate_centerline(opts, output_path)
		print(f"Zapisano obraz: {result.image_path}")
		print(f"Zapisano meta:  {result.metadata_path}")


def launch_gui(backgrounds: Dict[str, Path]) -> bool:
	try:
		import tkinter as tk
		from tkinter import ttk, messagebox
	except ImportError as err:
		print(f"Brak tkinter: {err}")
		return False

	root = tk.Tk()
	root.title("Generator nurtu rzeki")

	background_names = ["Transparent"] + sorted(backgrounds.keys())
	side_display_pairs = [(HEX_SIDE_LABELS[key], key) for key in HEX_SIDES]
	display_to_side = {display: key for display, key in side_display_pairs}
	default_exit_display = next(
		(display for display, key in side_display_pairs if key == "bottom"),
		side_display_pairs[-1][0],
	)

	count_var = tk.IntVar(value=1)
	background_var = tk.StringVar(value=background_names[0])
	entry_side_var = tk.StringVar(value=side_display_pairs[0][0])
	exit_side_var = tk.StringVar(value=default_exit_display)
	shape_var = tk.StringVar(value=PATH_SHAPE_LABELS[PATH_SHAPES[0]])
	shape_strength_var = tk.DoubleVar(value=0.5)
	shape_direction_var = tk.StringVar(value=SHAPE_DIRECTION_LABELS["auto"])
	grid_var = tk.IntVar(value=64)
	status_var = tk.StringVar(value="Gotowy")
	shape_strength_value_var = tk.StringVar(value="0.50")
	shape_display_pairs = [(PATH_SHAPE_LABELS[key], key) for key in PATH_SHAPES]
	display_to_shape = {display: key for display, key in shape_display_pairs}
	shape_direction_display_pairs = [
		(SHAPE_DIRECTION_LABELS[key], key) for key in SHAPE_DIRECTION_CHOICES
	]
	display_to_shape_direction = {
		display: key for display, key in shape_direction_display_pairs
	}

	frame = ttk.Frame(root, padding=12)
	frame.grid(row=0, column=0, sticky="nsew")
	root.columnconfigure(0, weight=1)
	root.rowconfigure(0, weight=1)

	ttk.Label(frame, text="Liczba przykładów (1-5):").grid(row=0, column=0, sticky="w", pady=4)
	count_spin = ttk.Spinbox(frame, from_=1, to=5, textvariable=count_var, width=5)
	count_spin.grid(row=0, column=1, sticky="we", pady=4)

	ttk.Label(frame, text="Tło:").grid(row=1, column=0, sticky="w", pady=4)
	background_box = ttk.Combobox(frame, values=background_names, state="readonly", textvariable=background_var)
	background_box.grid(row=1, column=1, sticky="we", pady=4)

	tk.Label(frame, text="Wejście:").grid(row=2, column=0, sticky="w", pady=4)
	entry_side_box = ttk.Combobox(
		frame,
		values=[display for display, _ in side_display_pairs],
		state="readonly",
		textvariable=entry_side_var,
	)
	entry_side_box.grid(row=2, column=1, sticky="we", pady=4)

	tk.Label(frame, text="Wyjście:").grid(row=3, column=0, sticky="w", pady=4)
	exit_side_box = ttk.Combobox(
		frame,
		values=[display for display, _ in side_display_pairs],
		state="readonly",
		textvariable=exit_side_var,
	)
	exit_side_box.grid(row=3, column=1, sticky="we", pady=4)

	ttk.Label(frame, text="Typ łuku:").grid(row=4, column=0, sticky="w", pady=4)
	shape_box = ttk.Combobox(
		frame,
		values=[display for display, _ in shape_display_pairs],
		state="readonly",
		textvariable=shape_var,
	)
	shape_box.grid(row=4, column=1, sticky="we", pady=4)

	ttk.Label(frame, text="Kierunek łuku:").grid(row=5, column=0, sticky="w", pady=4)
	shape_direction_box = ttk.Combobox(
		frame,
		values=[display for display, _ in shape_direction_display_pairs],
		state="readonly",
		textvariable=shape_direction_var,
	)
	shape_direction_box.grid(row=5, column=1, sticky="we", pady=4)

	ttk.Label(frame, text="Siła łuku (0-1):").grid(row=6, column=0, sticky="w", pady=4)
	shape_strength_scale = ttk.Scale(
		frame,
		from_=0.0,
		to=1.0,
		orient="horizontal",
		variable=shape_strength_var,
	)
	shape_strength_scale.grid(row=6, column=1, sticky="we", pady=4)
	shape_strength_value_label = ttk.Label(
		frame,
		textvariable=shape_strength_value_var,
		width=5,
		anchor="e",
	)
	shape_strength_value_label.grid(row=6, column=2, sticky="e", padx=(6, 0))

	def on_shape_strength_change(value: str) -> None:
		try:
			num = float(value)
		except ValueError:
			num = shape_strength_var.get()
		shape_strength_value_var.set(f"{num:.2f}")

	shape_strength_scale.configure(command=on_shape_strength_change)
	on_shape_strength_change(str(shape_strength_var.get()))

	ttk.Label(frame, text="Siatka (64/128):").grid(row=7, column=0, sticky="w", pady=4)
	grid_box = ttk.Combobox(frame, values=[64, 128], state="readonly", textvariable=grid_var)
	grid_box.grid(row=7, column=1, sticky="we", pady=4)

	status_label = ttk.Label(frame, textvariable=status_var, foreground="#305068")

	frame.columnconfigure(1, weight=1)
	frame.columnconfigure(2, weight=0)

	def resolve_background_choice() -> Path | None:
		choice = background_var.get()
		if choice == "Transparent":
			return None
		if choice in backgrounds:
			return backgrounds[choice]
		raise FileNotFoundError(f"Brak tła: {choice}")

	def handle_generate() -> None:
		try:
			count = max(1, min(5, int(count_var.get())))
		except ValueError:
			count = 1

		entry_side_key = display_to_side.get(entry_side_var.get(), HEX_SIDES[0])
		exit_side_key = display_to_side.get(exit_side_var.get(), entry_side_key)
		shape_key = display_to_shape.get(shape_var.get(), "straight")
		shape_strength = max(0.0, min(1.0, float(shape_strength_var.get())))
		shape_direction_key = display_to_shape_direction.get(shape_direction_var.get(), "auto")
		shape_direction = resolve_shape_direction(shape_direction_key)
		if entry_side_key == exit_side_key:
			messagebox.showerror(
				"Błędne krawędzie",
				"Wejściowa i wyjściowa krawędź muszą być różne.",
			)
			return
		shape_direction_effective = shape_direction if shape_key in {"curve", "turn"} else None

		try:
			grid = int(grid_var.get())
		except ValueError:
			grid = 64
		if grid not in (64, 128):
			messagebox.showerror("Błędna siatka", "Dozwolone wartości to 64 lub 128")
			return

		try:
			background_path = resolve_background_choice()
		except FileNotFoundError as err:
			messagebox.showerror("Błąd tła", str(err))
			return

		DEFAULT_OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
		base_seed = random.randint(0, 1_000_000)

		generated: List[RiverCenterlineResult] = []
		for index in range(count):
			seed = base_seed + index
			opts = RiverCenterlineOptions(
				grid_size=grid,
				background=background_path,
				entry_side=entry_side_key,
				exit_side=exit_side_key,
				shape=shape_key,
				shape_strength=shape_strength,
				shape_direction=shape_direction_effective,
				seed=seed,
			)
			suffix = f"{index + 1:02d}"
			bg_label = "transparent" if background_path is None else background_path.stem
			direction_part = ""
			if shape_key in {"curve", "turn"} and shape_direction_key != "auto":
				direction_part = f"_{shape_direction_key}"
			file_name = (
				f"hex_river_centerline_{bg_label}_{entry_side_key}_to_{exit_side_key}_"
				f"{shape_key}{direction_part}_g{grid}_{suffix}.png"
			)
			output_path = DEFAULT_OUTPUT_DIR / file_name
			try:
				result = generate_centerline(opts, output_path)
			except Exception as err:  # noqa: BLE001
				messagebox.showerror("Błąd generowania", str(err))
				return
			generated.append(result)

		if generated:
			status_var.set(
				f"Wygenerowano {len(generated)} plików (+meta), pierwszy: {generated[0].image_path.name}"
			)
		else:
			status_var.set("Brak wygenerowanych plików")

	generate_button = ttk.Button(frame, text="Generuj", command=handle_generate)
	generate_button.grid(row=8, column=0, columnspan=2, sticky="we", pady=(8, 4))

	def handle_clear_outputs() -> None:
		files: List[Path] = []
		if DEFAULT_OUTPUT_DIR.exists():
			png_files = [path for path in DEFAULT_OUTPUT_DIR.glob("*.png") if path.is_file()]
			json_files = [path for path in DEFAULT_OUTPUT_DIR.glob("*.json") if path.is_file()]
			files = png_files + json_files
		if not files:
			status_var.set("Brak plików do usunięcia")
			return
		if not messagebox.askyesno(
			"Usuń wygenerowane",
			f"Czy na pewno usunąć {len(files)} plików (PNG+JSON) z katalogu {DEFAULT_OUTPUT_DIR.name}?",
		):
			return
		failed: List[Path] = []
		for file_path in files:
			try:
				file_path.unlink()
			except OSError:
				failed.append(file_path)
		if failed:
			missing = ", ".join(path.name for path in failed[:3])
			if len(failed) > 3:
				missing += ", ..."
			messagebox.showwarning(
				"Nie udało się usunąć wszystkich",
				f"Niektóre pliki pozostały: {missing}",
			)
			status_var.set(f"Nie udało się usunąć {len(failed)} plików")
		else:
			status_var.set(f"Usunięto {len(files)} plików")

	clear_button = ttk.Button(frame, text="Usuń wygenerowane", command=handle_clear_outputs)
	clear_button.grid(row=9, column=0, columnspan=2, sticky="we", pady=4)

	status_label.grid(row=10, column=0, columnspan=2, sticky="we", pady=(8, 0))

	root.mainloop()
	return True


def main(argv: Iterable[str] | None = None) -> None:
	args = parse_args(argv)
	backgrounds = list_flat_backgrounds()

	if args.list_backgrounds:
		if not backgrounds:
			print("Brak tekstur flat_* w katalogu assets/terrain/hex_painted.")
		else:
			print("Dostępne tła:")
			for name in backgrounds:
				print(f" - {name}")
		return

	should_launch_gui = args.gui or (not args.no_gui and len(sys.argv) == 1)
	if should_launch_gui:
		if launch_gui(backgrounds):
			return
		print("GUI niedostępne, przechodzę w tryb CLI")

	run_cli(args, backgrounds)


if __name__ == "__main__":
	main()

