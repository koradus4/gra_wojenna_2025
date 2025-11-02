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
import statistics
from collections import deque
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, Iterable, List, Optional, Sequence, Tuple

from PIL import Image


ASSET_DIR = Path("assets/terrain/hex_painted")
DEFAULT_OUTPUT_DIR = ASSET_DIR / "river_contours"
EXPORT_SIZE_BY_GRID = {64: 512, 128: 1024}
CENTERLINE_COLOR = (0, 0, 0, 255)
TRIBUTARY_COLOR = (0, 0, 255, 255)
PAINT_CENTERLINE_PIXELS = False
PAINT_TRIBUTARY_PIXELS = False
DEFAULT_BANK_COLOR = (214, 192, 138, 255)
DEFAULT_WATER_COLOR = (70, 120, 180, 255)
DEFAULT_WATER_CENTER_COLOR = (45, 90, 150, 255)
DEFAULT_WATER_SHORE_COLOR = (105, 160, 210, 255)
DEFAULT_BANK_OFFSET = 1.5
DEFAULT_BANK_VARIATION = 0.35
GLOBAL_BANK_WIDTH_MULTIPLIER = 3.0
DEFAULT_WATER_DEPTH_NOISE_STRENGTH = 0.32
WATER_DEPTH_NOISE_SCALE_X = 0.085
WATER_DEPTH_NOISE_SCALE_Y = 0.12
WATER_DEPTH_NOISE_SCALE_DIAGONAL = 0.1
BANK_COLOR_PRESETS: Dict[str, Tuple[int, int, int, int]] = {
	"default": DEFAULT_BANK_COLOR,
	"sand": (214, 192, 138, 255),
	"mud": (139, 108, 66, 255),
	"rock": (96, 104, 120, 255),
	"transparent": (0, 0, 0, 0),
	"none": (0, 0, 0, 0),
}
UINT32_MAX = 0xFFFFFFFF
MIN_TRIBUTARY_JOIN = 0.2
MAX_TRIBUTARY_JOIN = 0.8


def _clamp_byte(value: int) -> int:
	return max(0, min(255, value))


def _lerp_color(a: Tuple[int, int, int, int], b: Tuple[int, int, int, int], t: float) -> Tuple[int, int, int, int]:
	t_clamped = max(0.0, min(1.0, t))
	return tuple(int(round(a[i] + (b[i] - a[i]) * t_clamped)) for i in range(4))


def parse_color_argument(value: str) -> Tuple[int, int, int, int]:
	value_stripped = (value or "").strip()
	if not value_stripped:
		raise ValueError("Kolor brzegów nie został podany")
	value_lower = value_stripped.lower()
	if value_lower in BANK_COLOR_PRESETS:
		return BANK_COLOR_PRESETS[value_lower]
	if value_lower.startswith("rgba(") and value_lower.endswith(")"):
		inside = value_stripped[value_stripped.find("(") + 1 : -1]
		parts = [part.strip() for part in inside.split(",") if part.strip()]
		return _parse_color_components(parts)
	if value_lower.startswith("rgb(") and value_lower.endswith(")"):
		inside = value_stripped[value_stripped.find("(") + 1 : -1]
		parts = [part.strip() for part in inside.split(",") if part.strip()]
		return _parse_color_components(parts)
	if value_stripped.startswith("#"):
		hex_value = value_stripped[1:]
		if len(hex_value) == 6:
			r = int(hex_value[0:2], 16)
			g = int(hex_value[2:4], 16)
			b = int(hex_value[4:6], 16)
			return (_clamp_byte(r), _clamp_byte(g), _clamp_byte(b), 255)
		if len(hex_value) == 8:
			r = int(hex_value[0:2], 16)
			g = int(hex_value[2:4], 16)
			b = int(hex_value[4:6], 16)
			a = int(hex_value[6:8], 16)
			return (_clamp_byte(r), _clamp_byte(g), _clamp_byte(b), _clamp_byte(a))
		raise ValueError(f"Niepoprawna długość zapisu heksadecymalnego: '{value_stripped}'")
	if "," in value_stripped:
		parts = [part.strip() for part in value_stripped.split(",") if part.strip()]
		return _parse_color_components(parts)
	raise ValueError(f"Nieznany format koloru: '{value_stripped}'")


def _parse_color_components(parts: Sequence[str]) -> Tuple[int, int, int, int]:
	if len(parts) not in {3, 4}:
		raise ValueError("Kolor powinien mieć 3 lub 4 składowe (R,G,B[,A])")
	components: List[int] = []
	for index, part in enumerate(parts):
		try:
			value = int(part)
		except ValueError as err:
			raise ValueError(f"Niepoprawna wartość składowej koloru: '{part}'") from err
		components.append(_clamp_byte(value))
	if len(components) == 3:
		components.append(255)
	return components[0], components[1], components[2], components[3]


def rgba_to_hex(color: Tuple[int, int, int, int]) -> str:
	return "#{:02X}{:02X}{:02X}{:02X}".format(*color)


def parse_optional_color_argument(value: str | None) -> Tuple[int, int, int, int] | None:
	if value is None:
		return None
	value_stripped = value.strip()
	if not value_stripped:
		return None
	if value_stripped.lower() in {"same", "inherit"}:
		return None
	return parse_color_argument(value_stripped)


def _next_file_index(output_dir: Path, pattern: str) -> int:
	max_idx = 0
	if not output_dir.exists():
		return 1
	for path in output_dir.glob(pattern):
		stem = path.stem
		if not stem:
			continue
		index_str = stem.split("_")[-1]
		if index_str.isdigit():
			max_idx = max(max_idx, int(index_str))
	return max_idx + 1

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
	noise_amplitude: float
	noise_frequency: float
	seed: int
	bank_offset: float = DEFAULT_BANK_OFFSET
	bank_color: Tuple[int, int, int, int] = DEFAULT_BANK_COLOR
	bank_variation: float = DEFAULT_BANK_VARIATION
	tributary: "TributaryOptions" | None = None


@dataclass
class RiverCenterlineResult:
	image_path: Path
	metadata_path: Path
	metadata: Dict[str, Any]


@dataclass
class RiverCenterlineRender:
	image: Image.Image
	metadata: Dict[str, Any]
	centerline_cells: List[Tuple[int, int]]
	centerline_banks: Tuple[List[Tuple[int, int]], List[Tuple[int, int]]]
	tributary_cells: List[Tuple[int, int]] | None
	tributary_banks: Tuple[List[Tuple[int, int]], List[Tuple[int, int]]] | None


@dataclass
class TributaryOptions:
	entry_side: str
	join_ratio: float
	shape: str
	shape_strength: float
	noise_amplitude: float
	noise_frequency: float
	shape_direction: int | None = None
	shape_direction_mode: str = "auto"
	seed_offset: int = 1_000_000
	bank_offset: float | None = None
	bank_color: Tuple[int, int, int, int] | None = None
	bank_variation: float | None = None


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


def _side_midpoint(grid: int, side: str) -> Tuple[float, float]:
	center = (grid / 2.0, grid / 2.0)
	radius = grid / 2.0 - 0.5
	vertices = get_hex_vertices(center[0], center[1], radius)
	edges = list(zip(vertices, vertices[1:] + vertices[:1]))
	index = _side_to_edge_index(side)
	start, end = edges[index]
	return (start[0] + end[0]) * 0.5, (start[1] + end[1]) * 0.5


def _side_inward_vector(grid: int, side: str) -> Tuple[float, float]:
	midpoint = _side_midpoint(grid, side)
	center = _hex_center(grid)
	return _normalize((center[0] - midpoint[0], center[1] - midpoint[1]))


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


def _compute_polyline_normals(points: Sequence[Tuple[float, float]]) -> List[Tuple[float, float]]:
	n = len(points)
	if n == 0:
		return []
	if n == 1:
		return [(0.0, 0.0)]
	normals: List[Tuple[float, float]] = []
	for i, point in enumerate(points):
		if i == 0:
			dx = points[1][0] - point[0]
			dy = points[1][1] - point[1]
		elif i == n - 1:
			dx = point[0] - points[i - 1][0]
			dy = point[1] - points[i - 1][1]
		else:
			dx1 = point[0] - points[i - 1][0]
			dy1 = point[1] - points[i - 1][1]
			dx2 = points[i + 1][0] - point[0]
			dy2 = points[i + 1][1] - point[1]
			dx = dx1 + dx2
			dy = dy1 + dy2
		direction = _normalize((dx, dy))
		normal = (-direction[1], direction[0])
		normals.append(normal)
	for idx in range(1, len(normals)):
		if normals[idx] == (0.0, 0.0) and normals[idx - 1] != (0.0, 0.0):
			normals[idx] = normals[idx - 1]
	for idx in range(len(normals) - 2, -1, -1):
		if normals[idx] == (0.0, 0.0) and normals[idx + 1] != (0.0, 0.0):
			normals[idx] = normals[idx + 1]
	return normals


def offset_polyline(points: Sequence[Tuple[float, float]], offset: float) -> List[Tuple[float, float]]:
	if not points or offset == 0.0:
		return list(points)
	normals = _compute_polyline_normals(points)
	offset_points: List[Tuple[float, float]] = []
	for point, normal in zip(points, normals):
		offset_points.append((point[0] + normal[0] * offset, point[1] + normal[1] * offset))
	return offset_points


def _generate_offset_profile(
	length: int,
	base_offset: float,
	variation: float,
	seed: int,
	scale: float = 4.0,
) -> List[float]:
	if length <= 0:
		return []
	if variation <= 1e-3:
		return [max(0.0, base_offset)] * length
	profile: List[float] = []
	for idx in range(length):
		t = idx / max(1, length - 1)
		noise_value = _value_noise_fractal(seed, t * scale)
		delta = (noise_value - 0.5) * 2.0 * variation
		profile.append(max(0.0, base_offset + delta))
	return profile


def _offset_polyline_with_profile(
	points: Sequence[Tuple[float, float]],
	normals: Sequence[Tuple[float, float]],
	profile: Sequence[float],
	sign: float,
) -> List[Tuple[float, float]]:
	result: List[Tuple[float, float]] = []
	for point, normal, offset in zip(points, normals, profile):
		result.append((point[0] + normal[0] * offset * sign, point[1] + normal[1] * offset * sign))
	return result


def build_centerline_bank_cells(
	points: Sequence[Tuple[float, float]],
	mask: Sequence[Sequence[bool]],
	entry_dir: Tuple[float, float],
	exit_dir: Tuple[float, float],
	offset: float,
	variation: float,
	seed: int,
) -> Tuple[List[Tuple[int, int]], List[Tuple[int, int]]]:
	normals = _compute_polyline_normals(points)
	left_profile = _generate_offset_profile(len(points), offset, variation, seed)
	right_profile = _generate_offset_profile(len(points), offset, variation, seed + 977)
	left_points = _offset_polyline_with_profile(points, normals, left_profile, 1.0)
	right_points = _offset_polyline_with_profile(points, normals, right_profile, -1.0)
	left_cells = rasterize_polyline(left_points)
	right_cells = rasterize_polyline(right_points)
	left_cells = extend_line_to_edges(left_cells, mask, entry_dir, exit_dir)
	right_cells = extend_line_to_edges(right_cells, mask, entry_dir, exit_dir)
	return left_cells, right_cells


def build_tributary_bank_cells(
	points: Sequence[Tuple[float, float]],
	mask: Sequence[Sequence[bool]],
	entry_dir: Tuple[float, float],
	offset: float,
	variation: float,
	seed: int,
) -> Tuple[List[Tuple[int, int]], List[Tuple[int, int]]]:
	normals = _compute_polyline_normals(points)
	left_profile = _generate_offset_profile(len(points), offset, variation, seed)
	right_profile = _generate_offset_profile(len(points), offset, variation, seed + 977)
	left_points = _offset_polyline_with_profile(points, normals, left_profile, 1.0)
	right_points = _offset_polyline_with_profile(points, normals, right_profile, -1.0)
	left_cells = rasterize_polyline(left_points)
	right_cells = rasterize_polyline(right_points)
	left_cells = extend_line_to_entry_edge(left_cells, mask, entry_dir)
	right_cells = extend_line_to_entry_edge(right_cells, mask, entry_dir)
	return left_cells, right_cells


def _normalize(vec: Tuple[float, float]) -> Tuple[float, float]:
	length = math.hypot(vec[0], vec[1])
	if length < 1e-8:
		return 0.0, 0.0
	return vec[0] / length, vec[1] / length


def _midpoint(a: Tuple[float, float], b: Tuple[float, float]) -> Tuple[float, float]:
	return (a[0] + b[0]) * 0.5, (a[1] + b[1]) * 0.5


def _hash_to_unit(seed: int, coord: int) -> float:
	value = (coord * 374761393 + seed * 668265263) & UINT32_MAX
	value = (value ^ (value >> 13)) & UINT32_MAX
	value = (value * 1274126177) & UINT32_MAX
	value = (value ^ (value >> 16)) & UINT32_MAX
	if value == 0:
		return 0.0
	return value / UINT32_MAX


def _value_noise_single(seed: int, x: float) -> float:
	cell = math.floor(x)
	frac = x - cell
	n0 = _hash_to_unit(seed, cell)
	n1 = _hash_to_unit(seed, cell + 1)
	smooth = frac * frac * (3.0 - 2.0 * frac)
	return n0 + (n1 - n0) * smooth


def _value_noise_fractal(seed: int, x: float, octaves: int = 3) -> float:
	amplitude = 1.0
	frequency = 1.0
	total = 0.0
	norm = 0.0
	for octave in range(octaves):
		total += _value_noise_single(seed + octave * 101, x * frequency) * amplitude
		norm += amplitude
		amplitude *= 0.5
		frequency *= 2.0
	if norm <= 1e-9:
		return 0.0
	return total / norm


def _sample_water_depth_noise(seed: int, col: int, row: int) -> float:
	x_sample = col * WATER_DEPTH_NOISE_SCALE_X
	y_sample = row * WATER_DEPTH_NOISE_SCALE_Y
	diag_sample = (col + row) * WATER_DEPTH_NOISE_SCALE_DIAGONAL
	noise_x = _value_noise_fractal(seed, x_sample)
	noise_y = _value_noise_fractal(seed + 211, y_sample)
	noise_diag = _value_noise_fractal(seed + 421, diag_sample)
	return (noise_x + noise_y + noise_diag) / 3.0


def _median_filter(values: Sequence[float], window: int) -> List[float]:
	size = len(values)
	if window <= 1 or size == 0:
		return list(values)
	radius = max(1, window // 2)
	filtered: List[float] = []
	for idx in range(size):
		start = max(0, idx - radius)
		end = min(size, idx + radius + 1)
		slice_vals = values[start:end]
		filtered.append(float(statistics.median(slice_vals)))
	return filtered


def _sample_polyline_at_ratio(
	points: Sequence[Tuple[float, float]],
	ratio: float,
) -> Tuple[Tuple[float, float], Tuple[float, float]]:
	if not points:
		return (0.0, 0.0), (0.0, 0.0)
	if len(points) == 1:
		return points[0], (0.0, 1.0)
	clamped = max(0.0, min(ratio, 1.0))
	distances = [0.0]
	for idx in range(1, len(points)):
		segment = math.hypot(points[idx][0] - points[idx - 1][0], points[idx][1] - points[idx - 1][1])
		distances.append(distances[-1] + segment)
	total = distances[-1]
	if total <= 1e-6:
		return points[0], (0.0, 1.0)
	target = clamped * total
	for idx in range(1, len(points)):
		if distances[idx] >= target:
			prev = points[idx - 1]
			next_point = points[idx]
			seg_len = distances[idx] - distances[idx - 1]
			if seg_len <= 1e-6:
				point = next_point
			else:
				frac = (target - distances[idx - 1]) / seg_len
				point = (
					prev[0] + (next_point[0] - prev[0]) * frac,
					prev[1] + (next_point[1] - prev[1]) * frac,
				)
			direction = _normalize((next_point[0] - prev[0], next_point[1] - prev[1]))
			return point, direction
	return points[-1], _normalize((points[-1][0] - points[-2][0], points[-1][1] - points[-2][1]))


def _apply_noise_to_polyline(
	points: Sequence[Tuple[float, float]],
	amplitude: float,
	frequency: float,
	seed: int,
	grid: int,
	polygon: Sequence[Tuple[float, float]],
) -> Tuple[List[Tuple[float, float]], Dict[str, Any]]:
	if amplitude <= 1e-5 or len(points) < 3:
		return list(points), {
			"applied": False,
			"amplitude": amplitude,
			"frequency": frequency,
			"seed": seed,
			"max_offset_px": 0.0,
			"offset_stats": {"min": 0.0, "max": 0.0, "median": 0.0},
		}

	frequency = max(0.1, frequency)
	grid_scale = max(1.0, float(grid))
	max_offset = amplitude * (grid_scale * 0.08)
	max_offset = max(0.0, min(max_offset, grid_scale * 0.45))

	cumulative = [0.0]
	for idx in range(1, len(points)):
		segment = math.hypot(points[idx][0] - points[idx - 1][0], points[idx][1] - points[idx - 1][1])
		cumulative.append(cumulative[-1] + segment)
	total_length = cumulative[-1]
	if total_length < 1e-6:
		return list(points), {
			"applied": False,
			"amplitude": amplitude,
			"frequency": frequency,
			"seed": seed,
			"max_offset_px": 0.0,
			"offset_stats": {"min": 0.0, "max": 0.0, "median": 0.0},
		}

	t_values = [dist / total_length if total_length > 0 else 0.0 for dist in cumulative]
	normals: List[Tuple[float, float]] = []
	last_normal = (0.0, 1.0)
	count = len(points)
	for idx in range(count):
		if idx == 0:
			tangent = (
				points[idx + 1][0] - points[idx][0],
				points[idx + 1][1] - points[idx][1],
			)
		elif idx == count - 1:
			tangent = (
				points[idx][0] - points[idx - 1][0],
				points[idx][1] - points[idx - 1][1],
			)
		else:
			tangent = (
				points[idx + 1][0] - points[idx - 1][0],
				points[idx + 1][1] - points[idx - 1][1],
			)
		tangent = _normalize(tangent)
		if tangent == (0.0, 0.0):
			normal = last_normal
		else:
			normal = _normalize((-tangent[1], tangent[0]))
		if normal == (0.0, 0.0):
			normal = last_normal
		last_normal = normal
		normals.append(normal)

	raw_offsets: List[float] = []
	for idx, t_val in enumerate(t_values):
		if idx == 0 or idx == count - 1:
			raw_offsets.append(0.0)
			continue
		sample = _value_noise_fractal(seed, t_val * frequency)
		sample = sample * 2.0 - 1.0
		raw_offsets.append(sample * max_offset)

	smoothed = _median_filter(raw_offsets, window=5)
	if smoothed:
		smoothed[0] = 0.0
		smoothed[-1] = 0.0

	noisy_points: List[Tuple[float, float]] = []
	min_off = 0.0
	max_off = 0.0
	for idx, (point, normal, offset) in enumerate(zip(points, normals, smoothed)):
		if idx == 0 or idx == count - 1:
			offset = 0.0
		min_off = min(min_off, offset)
		max_off = max(max_off, offset)
		deformed = (
			point[0] + normal[0] * offset,
			point[1] + normal[1] * offset,
		)
		if idx not in (0, count - 1):
			deformed = _project_inside_hex(deformed, grid, polygon)
		noisy_points.append(deformed)

	median_off = float(statistics.median(smoothed)) if smoothed else 0.0
	return noisy_points, {
		"applied": True,
		"amplitude": amplitude,
		"frequency": frequency,
		"seed": seed,
		"max_offset_px": max_offset,
		"offset_stats": {
			"min": min_off,
			"max": max_off,
			"median": median_off,
		},
	}


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

def _build_curve_points(
	start: Tuple[float, float],
	end: Tuple[float, float],
	entry_inward: Tuple[float, float],
	exit_inward: Tuple[float, float],
	shape: str,
	shape_strength: float,
	shape_direction: Optional[int],
	noise_amplitude: float,
	noise_frequency: float,
	noise_seed: int,
	grid: int,
	polygon: Sequence[Tuple[float, float]],
	rng: random.Random,
) -> Tuple[List[Tuple[float, float]], Dict[str, Any]]:
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
	points, noise_metadata = _apply_noise_to_polyline(
		points,
		noise_amplitude,
		noise_frequency,
		noise_seed,
		grid,
		polygon,
	)

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
		"noise": noise_metadata,
	}
	return points, metadata


def build_centerline_points(
	start: Tuple[float, float],
	end: Tuple[float, float],
	entry_inward: Tuple[float, float],
	exit_inward: Tuple[float, float],
	shape: str,
	shape_strength: float,
	shape_direction: int | None,
	noise_amplitude: float,
	noise_frequency: float,
	noise_seed: int,
	mask: Sequence[Sequence[bool]],
	rng: random.Random,
) -> Tuple[List[Tuple[float, float]], Dict[str, Any]]:
	grid = len(mask)
	polygon = _hex_polygon(grid)
	return _build_curve_points(
		start,
		end,
		entry_inward,
		exit_inward,
		shape,
		shape_strength,
		shape_direction,
		noise_amplitude,
		noise_frequency,
		noise_seed,
		grid,
		polygon,
		rng,
	)


def build_tributary_points(
	main_points: Sequence[Tuple[float, float]],
	options: RiverCenterlineOptions,
	mask: Sequence[Sequence[bool]],
) -> Optional[
	Tuple[
		List[Tuple[float, float]],
		List[Tuple[int, int]],
		Dict[str, Any],
		Tuple[List[Tuple[int, int]], List[Tuple[int, int]]],
		Tuple[int, int, int, int],
	]
]:
	tributary_opts = options.tributary
	if not tributary_opts:
		return None
	grid = len(mask)
	polygon = _hex_polygon(grid)
	start = _side_midpoint(grid, tributary_opts.entry_side)
	entry_inward = _side_inward_vector(grid, tributary_opts.entry_side)
	if entry_inward == (0.0, 0.0):
		entry_inward = (0.0, 1.0)
	join_ratio = max(MIN_TRIBUTARY_JOIN, min(MAX_TRIBUTARY_JOIN, float(tributary_opts.join_ratio)))
	join_point, join_direction = _sample_polyline_at_ratio(main_points, join_ratio)
	if join_direction == (0.0, 0.0):
		join_direction = entry_inward
	exit_inward = _normalize((start[0] - join_point[0], start[1] - join_point[1]))
	if exit_inward == (0.0, 0.0):
		exit_inward = entry_inward
	noise_seed = options.seed + tributary_opts.seed_offset
	tributary_rng = random.Random(noise_seed)
	tributary_points, shape_metadata = _build_curve_points(
		start,
		join_point,
		entry_inward,
		exit_inward,
		tributary_opts.shape,
		max(0.0, min(1.0, tributary_opts.shape_strength)),
		tributary_opts.shape_direction,
		tributary_opts.noise_amplitude,
		tributary_opts.noise_frequency,
		noise_seed,
		grid,
		polygon,
		tributary_rng,
	)
	tributary_cells = rasterize_polyline(tributary_points)
	tributary_cells = extend_line_to_entry_edge(tributary_cells, mask, entry_inward)
	tributary_bank_offset = (
		tributary_opts.bank_offset
		if tributary_opts.bank_offset is not None
		else options.bank_offset
	)
	tributary_bank_variation = (
		tributary_opts.bank_variation
		if tributary_opts.bank_variation is not None
		else options.bank_variation
	)
	effective_tributary_bank_offset = tributary_bank_offset * GLOBAL_BANK_WIDTH_MULTIPLIER
	effective_tributary_bank_variation = tributary_bank_variation * GLOBAL_BANK_WIDTH_MULTIPLIER
	bank_seed = noise_seed + 4211
	tributary_bank_cells = build_tributary_bank_cells(
		tributary_points,
		mask,
		entry_inward,
		effective_tributary_bank_offset,
		effective_tributary_bank_variation,
		bank_seed,
	)
	tributary_bank_color = (
		tributary_opts.bank_color
		if tributary_opts.bank_color is not None
		else options.bank_color
	)
	metadata = {
		"entry_side": tributary_opts.entry_side,
		"join_ratio": join_ratio,
		"join_ratio_percent": join_ratio * 100.0,
		"join_point": {"x": join_point[0], "y": join_point[1]},
		"join_direction": {"x": join_direction[0], "y": join_direction[1]},
		"shape": tributary_opts.shape,
		"shape_strength": max(0.0, min(1.0, tributary_opts.shape_strength)),
		"shape_direction": tributary_opts.shape_direction,
		"shape_direction_mode": tributary_opts.shape_direction_mode,
		"noise_amplitude": tributary_opts.noise_amplitude,
		"noise_frequency": tributary_opts.noise_frequency,
		"noise_applied": bool(shape_metadata.get("noise", {}).get("applied")),
		"seed": noise_seed,
		"shape_metadata": shape_metadata,
		"bank_offset": tributary_bank_offset,
		"effective_bank_offset": effective_tributary_bank_offset,
		"bank_color": {
			"rgba": list(tributary_bank_color),
			"hex": rgba_to_hex(tributary_bank_color),
		},
		"bank_variation": tributary_bank_variation,
		"effective_bank_variation": effective_tributary_bank_variation,
		"bank_cell_count": {
			"left": len(tributary_bank_cells[0]),
			"right": len(tributary_bank_cells[1]),
		},
	}
	return (
		tributary_points,
		tributary_cells,
		metadata,
		tributary_bank_cells,
		tributary_bank_color,
	)

def _bresenham_line(ax: int, ay: int, bx: int, by: int) -> List[Tuple[int, int]]:
	cells: List[Tuple[int, int]] = []
	dx = abs(bx - ax)
	dy = -abs(by - ay)
	sx = 1 if ax < bx else -1
	sy = 1 if ay < by else -1
	err = dx + dy
	x, y = ax, ay
	while True:
		cells.append((x, y))
		if x == bx and y == by:
			break
		e2 = 2 * err
		if e2 >= dy:
			err += dy
			x += sx
		if e2 <= dx:
			err += dx
			y += sy
	return cells


def rasterize_polyline(points: Sequence[Tuple[float, float]]) -> List[Tuple[int, int]]:
	cells: List[Tuple[int, int]] = []
	if len(points) < 2:
		if points:
			cells.append((int(round(points[0][0])), int(round(points[0][1]))))
		return cells

	for a, b in zip(points, points[1:]):
		ax, ay = int(round(a[0])), int(round(a[1]))
		bx, by = int(round(b[0])), int(round(b[1]))
		segment = _bresenham_line(ax, ay, bx, by)
		if cells:
			cells.extend(segment[1:])
		else:
			cells.extend(segment)

	deduped: List[Tuple[int, int]] = []
	prev: Tuple[int, int] | None = None
	for cell in cells:
		if cell != prev:
			deduped.append(cell)
		prev = cell
	return deduped


def extend_line_to_entry_edge(
	line_cells: Sequence[Tuple[int, int]],
	mask: Sequence[Sequence[bool]],
	entry_dir: Tuple[float, float],
) -> List[Tuple[int, int]]:
	if not line_cells:
		return list(line_cells)

	ordered = list(line_cells)
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
			# Continue walking even outside mask - we want to reach hex edge
			next_cell = (col, row)
			if trail and next_cell == trail[-1]:
				continue
			if mask[row][col]:  # Only add cells that are within the hex
				trail.append(next_cell)
		return trail

	leading = walk_to_edge(deduped[0], (-entry_dir[0], -entry_dir[1]))
	return list(reversed(leading)) + deduped


def fill_water_regions(
	pixels: Any,
	grid_size: int,
	mask: Sequence[Sequence[bool]],
	seed_groups: Sequence[Sequence[Tuple[int, int]]],
	bank_groups: Sequence[Sequence[Tuple[int, int]]],
	water_color: Tuple[int, int, int, int],
	depth_noise_seed: int | None = None,
	depth_noise_strength: float = 0.0,
) -> None:
	"""Fill river water using flood-fill bounded by banks and apply gradient/noise."""
	if not seed_groups or not bank_groups:
		return

	bank_mask = [[False for _ in range(grid_size)] for _ in range(grid_size)]
	bank_cells: List[Tuple[int, int]] = []
	for group in bank_groups:
		for col, row in group:
			if not (0 <= col < grid_size and 0 <= row < grid_size):
				continue
			if not mask[row][col]:
				continue
			if not bank_mask[row][col]:
				bank_mask[row][col] = True
				bank_cells.append((col, row))

	if not bank_cells:
		return

	seed_set: set[Tuple[int, int]] = set()
	for group in seed_groups:
		for col, row in group:
			if not (0 <= col < grid_size and 0 <= row < grid_size):
				continue
			if not mask[row][col]:
				continue
			if bank_mask[row][col]:
				continue
			seed_set.add((col, row))

	if not seed_set:
		return

	water_mask = [[False for _ in range(grid_size)] for _ in range(grid_size)]
	queue: deque[Tuple[int, int]] = deque()
	for col, row in seed_set:
		water_mask[row][col] = True
		queue.append((col, row))

	neighbor_offsets = (
		(-1, 0),
		(1, 0),
		(0, -1),
		(0, 1),
	)

	while queue:
		col, row = queue.popleft()
		for dc, dr in neighbor_offsets:
			next_col = col + dc
			next_row = row + dr
			if not (0 <= next_col < grid_size and 0 <= next_row < grid_size):
				continue
			if not mask[next_row][next_col]:
				continue
			if bank_mask[next_row][next_col]:
				continue
			if water_mask[next_row][next_col]:
				continue
			water_mask[next_row][next_col] = True
			queue.append((next_col, next_row))

	void_mask = [[False for _ in range(grid_size)] for _ in range(grid_size)]
	outside_void = [[False for _ in range(grid_size)] for _ in range(grid_size)]
	queue_void: deque[Tuple[int, int]] = deque()
	for row in range(grid_size):
		for col in range(grid_size):
			if not mask[row][col]:
				continue
			if bank_mask[row][col] or water_mask[row][col]:
				continue
			void_mask[row][col] = True
			is_boundary = False
			if row == 0 or row == grid_size - 1 or col == 0 or col == grid_size - 1:
				is_boundary = True
			else:
				for dc, dr in neighbor_offsets:
					next_col = col + dc
					next_row = row + dr
					if not (0 <= next_col < grid_size and 0 <= next_row < grid_size):
						is_boundary = True
						break
					if not mask[next_row][next_col]:
						is_boundary = True
						break
			if is_boundary:
				outside_void[row][col] = True
				queue_void.append((col, row))

	while queue_void:
		col, row = queue_void.popleft()
		for dc, dr in neighbor_offsets:
			next_col = col + dc
			next_row = row + dr
			if not (0 <= next_col < grid_size and 0 <= next_row < grid_size):
				continue
			if not void_mask[next_row][next_col]:
				continue
			if outside_void[next_row][next_col]:
				continue
			outside_void[next_row][next_col] = True
			queue_void.append((next_col, next_row))

	for row in range(grid_size):
		for col in range(grid_size):
			if not void_mask[row][col]:
				continue
			if outside_void[row][col]:
				continue
			water_mask[row][col] = True

	bank_keep: set[Tuple[int, int]] = set()
	queue_bank: deque[Tuple[int, int]] = deque()
	for col, row in bank_cells:
		if not (0 <= col < grid_size and 0 <= row < grid_size):
			continue
		if not mask[row][col]:
			continue
		adjacent_land = False
		for dc, dr in neighbor_offsets:
			next_col = col + dc
			next_row = row + dr
			if not (0 <= next_col < grid_size and 0 <= next_row < grid_size):
				adjacent_land = True
				break
			if not mask[next_row][next_col]:
				adjacent_land = True
				break
			if not water_mask[next_row][next_col] and not bank_mask[next_row][next_col]:
				adjacent_land = True
				break
		if adjacent_land:
			bank_keep.add((col, row))
			queue_bank.append((col, row))

	while queue_bank:
		col, row = queue_bank.popleft()
		for dc, dr in neighbor_offsets:
			next_col = col + dc
			next_row = row + dr
			if not (0 <= next_col < grid_size and 0 <= next_row < grid_size):
				continue
			if not bank_mask[next_row][next_col]:
				continue
			if (next_col, next_row) in bank_keep:
				continue
			bank_keep.add((next_col, next_row))
			queue_bank.append((next_col, next_row))

	for col, row in bank_cells:
		if not (0 <= col < grid_size and 0 <= row < grid_size):
			continue
		if not mask[row][col]:
			continue
		if (col, row) in bank_keep:
			continue
		bank_mask[row][col] = False
		water_mask[row][col] = True

	final_bank_cells: List[Tuple[int, int]] = []
	for row in range(grid_size):
		for col in range(grid_size):
			if bank_mask[row][col]:
				final_bank_cells.append((col, row))

	distance = [[float("inf") for _ in range(grid_size)] for _ in range(grid_size)]
	distance_queue: deque[Tuple[int, int]] = deque()
	diagonal_cost = math.sqrt(2.0)
	distance_neighbors = (
		(-1, 0, 1.0),
		(1, 0, 1.0),
		(0, -1, 1.0),
		(0, 1, 1.0),
		(-1, -1, diagonal_cost),
		(-1, 1, diagonal_cost),
		(1, -1, diagonal_cost),
		(1, 1, diagonal_cost),
	)

	for col, row in final_bank_cells:
		distance[row][col] = 0.0
		distance_queue.append((col, row))

	while distance_queue:
		col, row = distance_queue.popleft()
		for dc, dr, cost in distance_neighbors:
			next_col = col + dc
			next_row = row + dr
			if not (0 <= next_col < grid_size and 0 <= next_row < grid_size):
				continue
			if not mask[next_row][next_col]:
				continue
			if distance[next_row][next_col] <= distance[row][col] + cost:
				continue
			distance[next_row][next_col] = distance[row][col] + cost
			distance_queue.append((next_col, next_row))

	if not final_bank_cells:
		return

	water_cells: List[Tuple[int, int]] = []
	max_distance = 0.0
	for row in range(grid_size):
		for col in range(grid_size):
			if not water_mask[row][col]:
				continue
			d = distance[row][col]
			if math.isinf(d):
				continue
			water_cells.append((col, row))
			if d > max_distance:
				max_distance = d

	if not water_cells:
		return

	if water_color == DEFAULT_WATER_COLOR:
		center_color = DEFAULT_WATER_CENTER_COLOR
	else:
		center_color = water_color
	shore_color = DEFAULT_WATER_SHORE_COLOR

	if max_distance <= 1e-6:
		max_distance = 1.0

	noise_strength = max(0.0, depth_noise_strength)
	for col, row in water_cells:
		d = min(distance[row][col], max_distance)
		t = max(0.0, 1.0 - d / max_distance)
		t = t**1.2
		if depth_noise_seed is not None and noise_strength > 1e-6:
			noise_value = _sample_water_depth_noise(depth_noise_seed, col, row)
			t = max(0.0, min(1.0, t + (noise_value - 0.5) * noise_strength))
		color = _lerp_color(shore_color, center_color, t)
		if depth_noise_seed is not None and noise_strength > 1e-6:
			noise_value = _sample_water_depth_noise(depth_noise_seed + 977, col, row)
			boost = (noise_value - 0.5) * noise_strength * 32.0
			r = _clamp_byte(int(color[0] + boost * 0.35))
			g = _clamp_byte(int(color[1] + boost * 0.5))
			b = _clamp_byte(int(color[2] + boost))
			color = (r, g, b, color[3])
		pixels[col, row] = color


def compose_image(
	grid: int,
	mask: Sequence[Sequence[bool]],
	background: Sequence[Sequence[Tuple[int, int, int, int] | None]],
	centerline_cells: Sequence[Tuple[int, int]],
	centerline_banks: Tuple[Sequence[Tuple[int, int]], Sequence[Tuple[int, int]]] | None = None,
	centerline_bank_color: Tuple[int, int, int, int] | None = None,
	tributary_cells: Sequence[Tuple[int, int]] | None = None,
	tributary_banks: Tuple[Sequence[Tuple[int, int]], Sequence[Tuple[int, int]]] | None = None,
	tributary_bank_color: Tuple[int, int, int, int] | None = None,
	water_seed: int | None = None,
	water_noise_strength: float = DEFAULT_WATER_DEPTH_NOISE_STRENGTH,
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
	bank_color_main = centerline_bank_color or DEFAULT_BANK_COLOR
	bank_color_tributary = tributary_bank_color or bank_color_main
	
	# Draw banks
	if centerline_banks:
		for bank_cells in centerline_banks:
			for col, row in bank_cells:
				if 0 <= row < grid and 0 <= col < grid and mask[row][col]:
					pixels[col, row] = bank_color_main
	if tributary_banks:
		for bank_cells in tributary_banks:
			for col, row in bank_cells:
				if 0 <= row < grid and 0 <= col < grid and mask[row][col]:
					pixels[col, row] = bank_color_tributary
	
	seed_groups: List[Sequence[Tuple[int, int]]] = [centerline_cells]
	if tributary_cells:
		seed_groups.append(tributary_cells)
	bank_groups: List[Sequence[Tuple[int, int]]] = []
	if centerline_banks:
		bank_groups.extend(centerline_banks)
	if tributary_banks:
		bank_groups.extend(tributary_banks)
	if bank_groups:
		fill_water_regions(
			pixels,
			grid,
			mask,
			seed_groups,
			bank_groups,
			DEFAULT_WATER_COLOR,
			water_seed,
			water_noise_strength if water_seed is not None else 0.0,
		)
	
	if PAINT_CENTERLINE_PIXELS:
		for col, row in centerline_cells:
			if 0 <= row < grid and 0 <= col < grid and mask[row][col]:
				pixels[col, row] = CENTERLINE_COLOR
	if PAINT_TRIBUTARY_PIXELS and tributary_cells:
		for col, row in tributary_cells:
			if 0 <= row < grid and 0 <= col < grid and mask[row][col]:
				pixels[col, row] = TRIBUTARY_COLOR
	return image


def save_metadata(image_path: Path, metadata: Dict[str, Any]) -> Path:
	meta_path = image_path.with_suffix(".json")
	meta_path.parent.mkdir(parents=True, exist_ok=True)
	with meta_path.open("w", encoding="utf-8") as handle:
		json.dump(metadata, handle, ensure_ascii=True, indent=2)
	return meta_path


def render_centerline(opts: RiverCenterlineOptions) -> RiverCenterlineRender:
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
		opts.noise_amplitude,
		opts.noise_frequency,
		opts.seed,
		mask,
		rng,
	)
	centerline_cells = rasterize_polyline(centerline_points)
	centerline_cells = extend_line_to_edges(centerline_cells, mask, entry_inward, exit_inward)
	effective_bank_offset = opts.bank_offset * GLOBAL_BANK_WIDTH_MULTIPLIER
	effective_bank_variation = opts.bank_variation * GLOBAL_BANK_WIDTH_MULTIPLIER
	centerline_bank_cells = build_centerline_bank_cells(
		centerline_points,
		mask,
		entry_inward,
		exit_inward,
		effective_bank_offset,
		effective_bank_variation,
		opts.seed + 311,
	)
	tributary_cells: List[Tuple[int, int]] | None = None
	tributary_metadata: Dict[str, Any] | None = None
	tributary_bank_cells: Tuple[List[Tuple[int, int]], List[Tuple[int, int]]] | None = None
	tributary_bank_color: Tuple[int, int, int, int] | None = None
	tributary_result = build_tributary_points(centerline_points, opts, mask)
	if tributary_result:
		_, tributary_cells, tributary_metadata, tributary_bank_cells, tributary_bank_color = (
			tributary_result
		)
		if tributary_metadata is not None:
			tributary_metadata["cell_count"] = len(tributary_cells)

	image = compose_image(
		opts.grid_size,
		mask,
		background,
		centerline_cells,
		centerline_bank_cells,
		opts.bank_color,
		tributary_cells,
		tributary_bank_cells,
		tributary_bank_color,
		opts.seed,
		DEFAULT_WATER_DEPTH_NOISE_STRENGTH,
	)
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
		"noise_amplitude": opts.noise_amplitude,
		"noise_frequency": opts.noise_frequency,
		"noise_applied": bool(shape_metadata.get("noise", {}).get("applied")),
		"shape_metadata": shape_metadata,
	}
	metadata["centerline_cell_count"] = len(centerline_cells)
	metadata["centerline_banks"] = {
		"offset": opts.bank_offset,
		"effective_offset": effective_bank_offset,
		"color": {
			"rgba": list(opts.bank_color),
			"hex": rgba_to_hex(opts.bank_color),
		},
		"variation": opts.bank_variation,
		"effective_variation": effective_bank_variation,
		"left_cell_count": len(centerline_bank_cells[0]),
		"right_cell_count": len(centerline_bank_cells[1]),
	}
	metadata["tributary_present"] = bool(tributary_metadata)
	metadata["tributary"] = tributary_metadata
	metadata["water_depth_noise"] = {
		"seed": opts.seed,
		"strength": DEFAULT_WATER_DEPTH_NOISE_STRENGTH,
	}

	return RiverCenterlineRender(
		image=image,
		metadata=metadata,
		centerline_cells=centerline_cells,
		centerline_banks=centerline_bank_cells,
		tributary_cells=tributary_cells,
		tributary_banks=tributary_bank_cells,
	)


def generate_centerline(opts: RiverCenterlineOptions, output_path: Path) -> RiverCenterlineResult:
	render = render_centerline(opts)
	output_path.parent.mkdir(parents=True, exist_ok=True)
	render.image.save(output_path)
	metadata_path = save_metadata(output_path, render.metadata)
	return RiverCenterlineResult(
		image_path=output_path,
		metadata_path=metadata_path,
		metadata=render.metadata,
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
			# Continue walking even outside mask - we want to reach hex edge
			next_cell = (col, row)
			if trail and next_cell == trail[-1]:
				continue
			if mask[row][col]:  # Only add cells that are within the hex
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
	parser.add_argument(
		"--noise-amplitude",
		type=float,
		default=0.0,
		help="Siła proceduralnego szumu (0-1)",
	)
	parser.add_argument(
		"--noise-frequency",
		type=float,
		default=2.0,
		help="Częstotliwość szumu (ilość fal na heksie)",
	)
	parser.add_argument(
		"--bank-offset",
		type=float,
		default=DEFAULT_BANK_OFFSET,
		help="Odsunięcie brzegów od nurtu w pikselach",
	)
	parser.add_argument(
		"--bank-variation",
		type=float,
		default=DEFAULT_BANK_VARIATION,
		help="Losowa zmienność odsunięcia brzegów (0 oznacza brak)",
	)
	parser.add_argument(
		"--bank-color",
		default="default",
		help="Kolor brzegów (#RRGGBB, #RRGGBBAA, R,G,B[,A] lub preset: sand/mud/rock/transparent)",
	)
	parser.add_argument(
		"--tributary-entry-side",
		choices=list(HEX_SIDES),
		help="Aktywuj dopływ z wybranej krawędzi",
	)
	parser.add_argument(
		"--tributary-join-ratio",
		type=float,
		default=0.55,
		help="Pozycja połączenia dopływu (zakres 0.2-0.8 wzdłuż głównego nurtu)",
	)
	parser.add_argument(
		"--tributary-shape",
		choices=PATH_SHAPES,
		default="curve",
		help="Kształt dopływu",
	)
	parser.add_argument(
		"--tributary-shape-strength",
		type=float,
		default=0.6,
		help="Siła łuku dopływu (0-1)",
	)
	parser.add_argument(
		"--tributary-shape-direction",
		choices=SHAPE_DIRECTION_CHOICES,
		default="auto",
		help="Kierunek łuku dopływu",
	)
	parser.add_argument(
		"--tributary-noise-amplitude",
		type=float,
		default=0.0,
		help="Siła szumu dla dopływu",
	)
	parser.add_argument(
		"--tributary-noise-frequency",
		type=float,
		default=2.5,
		help="Częstotliwość szumu dopływu",
	)
	parser.add_argument(
		"--tributary-bank-offset",
		type=float,
		help="Odsunięcie brzegów dopływu (domyślnie takie jak główny nurt)",
	)
	parser.add_argument(
		"--tributary-bank-variation",
		type=float,
		help="Zmienność odsunięcia brzegów dopływu (domyślnie jak główny nurt)",
	)
	parser.add_argument(
		"--tributary-bank-color",
		help="Kolor brzegów dopływu (#RRGGBB, #RRGGBBAA, R,G,B[,A], preset lub 'same')",
	)
	parser.add_argument(
		"--tributary-seed-offset",
		type=int,
		default=1_000_000,
		help="Offset seed dla dopływu",
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

	noise_amplitude = max(0.0, min(float(getattr(args, "noise_amplitude", 0.0)), 3.0))
	noise_frequency = max(0.1, float(getattr(args, "noise_frequency", 2.0)))
	noise_suffix = ""
	if noise_amplitude > 1e-3:
		noise_suffix = f"_noise{int(round(noise_amplitude * 100)):02d}f{int(round(noise_frequency * 10)):02d}"
	try:
		bank_color = parse_color_argument(getattr(args, "bank_color", "default"))
	except ValueError as err:
		print(f"Niepoprawny kolor brzegów: {err}")
		return
	bank_offset = max(0.0, float(getattr(args, "bank_offset", DEFAULT_BANK_OFFSET)))
	bank_variation = max(0.0, float(getattr(args, "bank_variation", DEFAULT_BANK_VARIATION)))
	tributary_bank_offset: float | None = None
	if getattr(args, "tributary_bank_offset", None) is not None:
		tributary_bank_offset = max(0.0, float(args.tributary_bank_offset))
	tributary_bank_variation: float | None = None
	if getattr(args, "tributary_bank_variation", None) is not None:
		tributary_bank_variation = max(0.0, float(args.tributary_bank_variation))
	try:
		tributary_bank_color = parse_optional_color_argument(getattr(args, "tributary_bank_color", None))
	except ValueError as err:
		print(f"Niepoprawny kolor brzegów dopływu: {err}")
		return
	tributary_opts: TributaryOptions | None = None
	tributary_entry = getattr(args, "tributary_entry_side", None)
	trib_suffix = ""
	if tributary_entry:
		if tributary_entry in {args.entry_side, args.exit_side}:
			print(
				"Dopływ nie może startować z tej samej krawędzi co główny nurt (wejście/wyjście)."
			)
			return
		tributary_join_ratio = max(
			MIN_TRIBUTARY_JOIN,
			min(MAX_TRIBUTARY_JOIN, float(getattr(args, "tributary_join_ratio", 0.55))),
		)
		tributary_shape = getattr(args, "tributary_shape", "curve")
		tributary_shape_strength = max(0.0, min(1.0, float(getattr(args, "tributary_shape_strength", 0.6))))
		tributary_shape_direction_choice = getattr(args, "tributary_shape_direction", "auto")
		tributary_shape_direction = resolve_shape_direction(tributary_shape_direction_choice)
		if tributary_shape not in {"curve", "turn"}:
			tributary_shape_direction = None
		tributary_noise_amplitude = max(0.0, min(float(getattr(args, "tributary_noise_amplitude", 0.0)), 3.0))
		tributary_noise_frequency = max(0.1, float(getattr(args, "tributary_noise_frequency", 2.5)))
		tributary_seed_offset = int(getattr(args, "tributary_seed_offset", 1_000_000))
		tributary_opts = TributaryOptions(
			entry_side=tributary_entry,
			join_ratio=tributary_join_ratio,
			shape=tributary_shape,
			shape_strength=tributary_shape_strength,
			noise_amplitude=tributary_noise_amplitude,
			noise_frequency=tributary_noise_frequency,
			shape_direction=tributary_shape_direction,
			shape_direction_mode=tributary_shape_direction_choice,
			seed_offset=tributary_seed_offset,
			bank_offset=tributary_bank_offset,
			bank_color=tributary_bank_color,
			bank_variation=tributary_bank_variation,
		)
	if tributary_opts:
		join_pct = int(round(tributary_opts.join_ratio * 100))
		trib_suffix = f"_trib_{tributary_opts.entry_side}_{join_pct:03d}"

	bg_label = "transparent" if background_path is None else background_path.stem
	base_pattern = (
		f"{args.prefix}_{bg_label}_{args.entry_side}_to_{args.exit_side}_"
		f"{args.shape}{direction_suffix}{noise_suffix}{trib_suffix}_g{args.grid}_*.png"
	)
	next_index = _next_file_index(args.output_dir, base_pattern)

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
			noise_amplitude=noise_amplitude,
			noise_frequency=noise_frequency,
			seed=seed,
			bank_offset=bank_offset,
			bank_color=bank_color,
			bank_variation=bank_variation,
			tributary=tributary_opts,
		)
		suffix = f"{next_index + index:02d}"
		direction_part = direction_suffix if args.shape in {"curve", "turn"} else ""
		file_name = (
			f"{args.prefix}_{bg_label}_{args.entry_side}_to_{args.exit_side}_"
			f"{args.shape}{direction_part}{noise_suffix}{trib_suffix}_g{args.grid}_{suffix}.png"
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
	noise_amplitude_var = tk.DoubleVar(value=0.0)
	noise_amplitude_value_var = tk.StringVar(value="0.00")
	noise_frequency_var = tk.DoubleVar(value=2.0)
	tributary_enabled_var = tk.BooleanVar(value=False)
	tributary_entry_side_var = tk.StringVar(value=side_display_pairs[2][0])
	tributary_join_ratio_var = tk.DoubleVar(value=55.0)
	tributary_join_ratio_value_var = tk.StringVar(value="55")
	tributary_shape_var = tk.StringVar(value=PATH_SHAPE_LABELS["curve"])
	tributary_shape_strength_var = tk.DoubleVar(value=0.6)
	tributary_shape_strength_value_var = tk.StringVar(value="0.60")
	tributary_shape_direction_var = tk.StringVar(value=SHAPE_DIRECTION_LABELS["auto"])
	tributary_noise_amplitude_var = tk.DoubleVar(value=0.0)
	tributary_noise_amplitude_value_var = tk.StringVar(value="0.00")
	tributary_noise_frequency_var = tk.DoubleVar(value=2.5)
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

	ttk.Label(frame, text="Amplituda szumu (0-1):").grid(row=7, column=0, sticky="w", pady=4)
	noise_amplitude_scale = ttk.Scale(
		frame,
		from_=0.0,
		to=3.0,
		orient="horizontal",
		variable=noise_amplitude_var,
	)
	noise_amplitude_scale.grid(row=7, column=1, sticky="we", pady=4)
	noise_amplitude_value_label = ttk.Label(
		frame,
		textvariable=noise_amplitude_value_var,
		width=5,
		anchor="e",
	)
	noise_amplitude_value_label.grid(row=7, column=2, sticky="e", padx=(6, 0))

	def on_noise_amplitude_change(value: str) -> None:
		try:
			num = float(value)
		except ValueError:
			num = noise_amplitude_var.get()
		noise_amplitude_value_var.set(f"{num:.2f}")

	noise_amplitude_scale.configure(command=on_noise_amplitude_change)
	on_noise_amplitude_change(str(noise_amplitude_var.get()))

	def on_tributary_join_change(value: str) -> None:
		try:
			num = float(value)
		except ValueError:
			num = tributary_join_ratio_var.get()
		tributary_join_ratio_value_var.set(f"{int(round(num))}")

	def on_tributary_strength_change(value: str) -> None:
		try:
			num = float(value)
		except ValueError:
			num = tributary_shape_strength_var.get()
		tributary_shape_strength_value_var.set(f"{num:.2f}")

	def on_tributary_noise_change(value: str) -> None:
		try:
			num = float(value)
		except ValueError:
			num = tributary_noise_amplitude_var.get()
		tributary_noise_amplitude_value_var.set(f"{num:.2f}")

	ttk.Label(frame, text="Częstotliwość szumu:").grid(row=8, column=0, sticky="w", pady=4)
	noise_frequency_spin = ttk.Spinbox(
		frame,
		from_=0.5,
		to=10.0,
		increment=0.5,
		textvariable=noise_frequency_var,
		width=6,
	)
	noise_frequency_spin.grid(row=8, column=1, sticky="we", pady=4)

	tributary_toggle = ttk.Checkbutton(
		frame,
		text="Dodaj dopływ",
		variable=tributary_enabled_var,
	)
	tributary_toggle.grid(row=9, column=0, sticky="w", pady=4)
	tributary_entry_box = ttk.Combobox(
		frame,
		values=[display for display, _ in side_display_pairs],
		state="readonly",
		textvariable=tributary_entry_side_var,
	)
	tributary_entry_box.grid(row=9, column=1, sticky="we", pady=4)

	ttk.Label(frame, text="Połączenie (20-80%):").grid(row=10, column=0, sticky="w", pady=4)
	tributary_join_scale = ttk.Scale(
		frame,
		from_=MIN_TRIBUTARY_JOIN * 100.0,
		to=MAX_TRIBUTARY_JOIN * 100.0,
		orient="horizontal",
		variable=tributary_join_ratio_var,
	)
	tributary_join_scale.grid(row=10, column=1, sticky="we", pady=4)
	tributary_join_label = ttk.Label(
		frame,
		textvariable=tributary_join_ratio_value_var,
		width=5,
		anchor="e",
	)
	tributary_join_label.grid(row=10, column=2, sticky="e", padx=(6, 0))

	ttk.Label(frame, text="Kształt dopływu:").grid(row=11, column=0, sticky="w", pady=4)
	tributary_shape_box = ttk.Combobox(
		frame,
		values=[display for display, _ in shape_display_pairs],
		state="readonly",
		textvariable=tributary_shape_var,
	)
	tributary_shape_box.grid(row=11, column=1, sticky="we", pady=4)

	ttk.Label(frame, text="Siła dopływu:").grid(row=12, column=0, sticky="w", pady=4)
	tributary_strength_scale = ttk.Scale(
		frame,
		from_=0.0,
		to=1.0,
		orient="horizontal",
		variable=tributary_shape_strength_var,
	)
	tributary_strength_scale.grid(row=12, column=1, sticky="we", pady=4)
	tributary_strength_label = ttk.Label(
		frame,
		textvariable=tributary_shape_strength_value_var,
		width=5,
		anchor="e",
	)
	tributary_strength_label.grid(row=12, column=2, sticky="e", padx=(6, 0))

	ttk.Label(frame, text="Kierunek dopływu:").grid(row=13, column=0, sticky="w", pady=4)
	tributary_direction_box = ttk.Combobox(
		frame,
		values=[display for display, _ in shape_direction_display_pairs],
		state="readonly",
		textvariable=tributary_shape_direction_var,
	)
	tributary_direction_box.grid(row=13, column=1, sticky="we", pady=4)

	ttk.Label(frame, text="Szum dopływu (0-1):").grid(row=14, column=0, sticky="w", pady=4)
	tributary_noise_scale = ttk.Scale(
		frame,
		from_=0.0,
		to=3.0,
		orient="horizontal",
		variable=tributary_noise_amplitude_var,
	)
	tributary_noise_scale.grid(row=14, column=1, sticky="we", pady=4)
	tributary_noise_label = ttk.Label(
		frame,
		textvariable=tributary_noise_amplitude_value_var,
		width=5,
		anchor="e",
	)
	tributary_noise_label.grid(row=14, column=2, sticky="e", padx=(6, 0))

	ttk.Label(frame, text="Częstotliwość dopływu:").grid(row=15, column=0, sticky="w", pady=4)
	tributary_noise_freq_spin = ttk.Spinbox(
		frame,
		from_=0.5,
		to=10.0,
		increment=0.5,
		textvariable=tributary_noise_frequency_var,
		width=6,
	)
	tributary_noise_freq_spin.grid(row=15, column=1, sticky="we", pady=4)
	tributary_join_scale.configure(command=on_tributary_join_change)
	on_tributary_join_change(str(tributary_join_ratio_var.get()))
	tributary_strength_scale.configure(command=on_tributary_strength_change)
	on_tributary_strength_change(str(tributary_shape_strength_var.get()))
	tributary_noise_scale.configure(command=on_tributary_noise_change)
	on_tributary_noise_change(str(tributary_noise_amplitude_var.get()))

	ttk.Label(frame, text="Siatka (64/128):").grid(row=16, column=0, sticky="w", pady=4)
	grid_box = ttk.Combobox(frame, values=[64, 128], state="readonly", textvariable=grid_var)
	grid_box.grid(row=16, column=1, sticky="we", pady=4)

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

		raw_amplitude = str(noise_amplitude_var.get()).strip().replace(",", ".")
		try:
			noise_amplitude = max(0.0, min(3.0, float(raw_amplitude)))
		except (ValueError, tk.TclError):
			noise_amplitude = 0.0
		raw_frequency = str(noise_frequency_var.get()).strip().replace(",", ".")
		try:
			noise_frequency = max(0.1, float(raw_frequency))
		except (ValueError, tk.TclError):
			noise_frequency = 2.0

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
		bg_label = "transparent" if background_path is None else background_path.stem
		direction_part = ""
		if shape_key in {"curve", "turn"} and shape_direction_key != "auto":
			direction_part = f"_{shape_direction_key}"
		noise_part = ""
		if noise_amplitude > 1e-3:
			noise_part = f"_noise{int(round(noise_amplitude * 100)):02d}f{int(round(noise_frequency * 10)):02d}"
		tributary_options: TributaryOptions | None = None
		trib_suffix = ""
		if tributary_enabled_var.get():
			tributary_entry_key = display_to_side.get(tributary_entry_side_var.get(), HEX_SIDES[2])
			if tributary_entry_key in {entry_side_key, exit_side_key}:
				messagebox.showerror(
					"Błędny dopływ",
					"Dopływ nie może startować z tej samej krawędzi co główny nurt.",
				)
				return
			tributary_join_percent = max(
				MIN_TRIBUTARY_JOIN * 100.0,
				min(MAX_TRIBUTARY_JOIN * 100.0, float(tributary_join_ratio_var.get())),
			)
			tributary_join_ratio = tributary_join_percent / 100.0
			tributary_shape_key = display_to_shape.get(tributary_shape_var.get(), "curve")
			tributary_shape_strength = max(0.0, min(1.0, float(tributary_shape_strength_var.get())))
			tributary_direction_key = display_to_shape_direction.get(tributary_shape_direction_var.get(), "auto")
			tributary_direction = resolve_shape_direction(tributary_direction_key)
			if tributary_shape_key not in {"curve", "turn"}:
				tributary_direction = None
			tributary_noise_amplitude = max(0.0, min(3.0, float(tributary_noise_amplitude_var.get())))
			tributary_noise_frequency = max(0.1, float(tributary_noise_frequency_var.get()))
			tributary_options = TributaryOptions(
				entry_side=tributary_entry_key,
				join_ratio=tributary_join_ratio,
				shape=tributary_shape_key,
				shape_strength=tributary_shape_strength,
				noise_amplitude=tributary_noise_amplitude,
				noise_frequency=tributary_noise_frequency,
				shape_direction=tributary_direction,
				shape_direction_mode=tributary_direction_key,
				seed_offset=1_000_000,
			)
			trib_suffix = f"_trib_{tributary_entry_key}_{int(round(tributary_join_ratio * 100)):03d}"
		pattern = (
			"hex_river_centerline_"
			f"{bg_label}_{entry_side_key}_to_{exit_side_key}_"
			f"{shape_key}{direction_part}{noise_part}{trib_suffix}_g{grid}_*.png"
		)
		next_index = _next_file_index(DEFAULT_OUTPUT_DIR, pattern)

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
				noise_amplitude=noise_amplitude,
				noise_frequency=noise_frequency,
				seed=seed,
				tributary=tributary_options,
			)
			suffix = f"{next_index + index:02d}"
			file_name = (
				f"hex_river_centerline_{bg_label}_{entry_side_key}_to_{exit_side_key}_"
				f"{shape_key}{direction_part}{noise_part}{trib_suffix}_g{grid}_{suffix}.png"
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
	generate_button.grid(row=17, column=0, columnspan=2, sticky="we", pady=(8, 4))

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
	clear_button.grid(row=18, column=0, columnspan=2, sticky="we", pady=4)

	status_label.grid(row=19, column=0, columnspan=2, sticky="we", pady=(8, 0))

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

