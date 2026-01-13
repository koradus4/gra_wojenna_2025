"""Generator jeziora na kaflu heksowym.

Cel:
- osobny byt wizualny: jezioro/rozlewisko (woda + brzegi)
- wariant 1-heksowy (pojedynczy)
- wariant "lake3" dla układu: center + 2 sąsiady (spójny kształt na stykach)
- opcjonalny odpływ (outflow_side) jako "źródło dopływu".

Uwaga: To jest generator użytkowy do edytorów/QA (Hex Inspector + replay).
"""

from __future__ import annotations

import argparse
import json
import math
import random
from dataclasses import dataclass, replace
from pathlib import Path
from typing import Any, Dict, List, Optional, Sequence, Tuple

from PIL import Image


try:
    from PIL.Image import Resampling  # type: ignore

    RESAMPLE_NEAREST = Resampling.NEAREST
except Exception:
    # Fallback dla starszych Pillow / stubów typów
    RESAMPLE_NEAREST = getattr(Image, "NEAREST", 0)


ASSET_DIR = Path("assets/terrain/hex_painted")

HEX_SIDES = (
    "top",
    "top_right",
    "bottom_right",
    "bottom",
    "bottom_left",
    "top_left",
)

SIDE_OPPOSITE: Dict[str, str] = {
    "top": "bottom",
    "top_right": "bottom_left",
    "bottom_right": "top_left",
    "bottom": "top",
    "bottom_left": "top_right",
    "top_left": "bottom_right",
}

DEFAULT_BANK_COLOR = (214, 192, 138, 255)
DEFAULT_WATER_COLOR = (70, 120, 180, 255)
DEFAULT_WATER_CENTER_COLOR = (45, 90, 150, 255)
DEFAULT_WATER_SHORE_COLOR = (105, 160, 210, 255)


def _clamp_byte(value: int) -> int:
    return max(0, min(255, value))


def _lerp_color(a: Tuple[int, int, int, int], b: Tuple[int, int, int, int], t: float) -> Tuple[int, int, int, int]:
    t_clamped = max(0.0, min(1.0, float(t)))
    return (
        int(round(a[0] + (b[0] - a[0]) * t_clamped)),
        int(round(a[1] + (b[1] - a[1]) * t_clamped)),
        int(round(a[2] + (b[2] - a[2]) * t_clamped)),
        int(round(a[3] + (b[3] - a[3]) * t_clamped)),
    )


def rgba_to_hex(color: Tuple[int, int, int, int]) -> str:
    return "#{:02X}{:02X}{:02X}{:02X}".format(*color)


def point_in_polygon(x: float, y: float, polygon: Sequence[Tuple[float, float]]) -> bool:
    inside = False
    j = len(polygon) - 1
    for i, (ix, iy) in enumerate(polygon):
        jx, jy = polygon[j]
        intersects = ((iy > y) != (jy > y)) and (x < (jx - ix) * (y - iy) / ((jy - iy) + 1e-10) + ix)
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


def _hex_center(grid: int) -> Tuple[float, float]:
    coord = grid / 2.0
    return coord, coord


def _hex_polygon(grid: int) -> List[Tuple[float, float]]:
    cx, cy = _hex_center(grid)
    radius = grid / 2.0 - 0.5
    return get_hex_vertices(cx, cy, radius)


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
    idx = _side_to_edge_index(side)
    start, end = edges[idx]
    return (start[0] + end[0]) * 0.5, (start[1] + end[1]) * 0.5


def _normalize(vec: Tuple[float, float]) -> Tuple[float, float]:
    length = math.hypot(vec[0], vec[1])
    if length < 1e-8:
        return 0.0, 0.0
    return vec[0] / length, vec[1] / length


def _distance_point_to_segment(
    px: float,
    py: float,
    ax: float,
    ay: float,
    bx: float,
    by: float,
) -> float:
    abx = bx - ax
    aby = by - ay
    apx = px - ax
    apy = py - ay
    denom = abx * abx + aby * aby
    if denom <= 1e-12:
        return math.hypot(px - ax, py - ay)
    t = (apx * abx + apy * aby) / denom
    t = max(0.0, min(1.0, t))
    qx = ax + abx * t
    qy = ay + aby * t
    return math.hypot(px - qx, py - qy)


def _edge_segments_by_side(grid: int) -> Dict[str, Tuple[Tuple[float, float], Tuple[float, float]]]:
    poly = _hex_polygon(grid)
    edges = list(zip(poly, poly[1:] + poly[:1]))
    out: Dict[str, Tuple[Tuple[float, float], Tuple[float, float]]] = {}
    for side in HEX_SIDES:
        out[side] = edges[_side_to_edge_index(side)]
    return out


def _cluster_allowed_boundary_sides(grid: int, opts: "LakeOptions") -> set[str]:
    """Zwraca boki, na których woda może dochodzić do krawędzi heksa (bo to styk z innym jeziorem lub odpływ)."""
    if not (opts.cluster_seed is not None and opts.cluster_neighbors and opts.cluster_tile):
        return set()

    active = {"center", *set(opts.cluster_neighbors)}
    tile = str(opts.cluster_tile)
    if tile not in active:
        return set()

    centers = _cluster7_tile_centers(grid)
    if tile not in centers:
        return set()

    # wektory sąsiadów w układzie _cluster7_tile_centers
    radius = grid / 2.0
    dx = 1.5 * radius
    dy = math.sqrt(3.0) * radius
    dy_half = dy / 2.0
    side_deltas: Dict[str, Tuple[float, float]] = {
        "top": (0.0, -dy),
        "top_right": (dx, -dy_half),
        "bottom_right": (dx, dy_half),
        "bottom": (0.0, dy),
        "bottom_left": (-dx, dy_half),
        "top_left": (-dx, -dy_half),
    }

    cx, cy = centers[tile]
    allowed: set[str] = set()
    tol = 1e-6
    for other in active:
        if other == tile:
            continue
        if other not in centers:
            continue
        ox, oy = centers[other]
        ddx = ox - cx
        ddy = oy - cy
        for side, (sdx, sdy) in side_deltas.items():
            if abs(ddx - sdx) < tol and abs(ddy - sdy) < tol:
                allowed.add(side)
                break

    # odpływ: pozwól wodzie dojść do krawędzi na tym boku
    if tile == "center" and opts.outflow_side:
        allowed.add(str(opts.outflow_side))

    return allowed


def _apply_external_edge_margin(
    water: List[List[bool]],
    mask: Sequence[Sequence[bool]],
    *,
    forbidden_sides: set[str],
    margin: float,
    grid: int,
) -> None:
    if not forbidden_sides:
        return
    edges = _edge_segments_by_side(grid)
    for row in range(grid):
        for col in range(grid):
            if not mask[row][col] or not water[row][col]:
                continue
            px = col + 0.5
            py = row + 0.5
            for side in forbidden_sides:
                (a, b) = edges[side]
                d = _distance_point_to_segment(px, py, a[0], a[1], b[0], b[1])
                if d <= margin:
                    water[row][col] = False
                    break


def _sample_jitter(seed: int, angle: float) -> float:
    # Mała, deterministyczna modulacja brzegu; bez zależności od Pillow/NumPy.
    return (
        0.085 * math.sin(angle * 3.0 + seed * 0.0017)
        + 0.055 * math.sin(angle * 7.0 + seed * 0.0031)
        + 0.03 * math.sin(angle * 11.0 + seed * 0.0063)
    )


def _load_background(grid: int, mask: Sequence[Sequence[bool]], texture_path: Optional[Path]) -> List[List[Tuple[int, int, int, int] | None]]:
    pixels: List[List[Tuple[int, int, int, int] | None]] = [[None for _ in range(grid)] for _ in range(grid)]
    if texture_path is None:
        return pixels
    img = Image.open(texture_path).convert("RGBA")
    if img.size != (grid, grid):
        img = img.resize((grid, grid), RESAMPLE_NEAREST)
    ip = img.load()
    assert ip is not None
    for row in range(grid):
        for col in range(grid):
            if mask[row][col]:
                pixels[row][col] = ip[col, row]
    return pixels


@dataclass
class LakeOptions:
    grid_size: int
    background: Optional[Path]
    seed: int

    # Rozmiar jeziora: dla single typowo ~0.26-0.42 (względem promienia heksa)
    # Dla lake3 typowo ~0.9-1.1 (względem grid_size).
    lake_radius: float = 0.34

    # Grubość brzegu w pikselach siatki (po wyznaczeniu "shoreline")
    shore_width: int = 2

    bank_color: Tuple[int, int, int, int] = DEFAULT_BANK_COLOR
    water_color: Tuple[int, int, int, int] = DEFAULT_WATER_COLOR

    # Odpływ jako "źródło dopływu" (kanał wychodzący do krawędzi)
    outflow_side: Optional[str] = None
    outflow_width: float = 2.2

    # Opcje klastrowe (spójny kształt na stykach)
    cluster_seed: Optional[int] = None
    # Aktywne sąsiedztwo w trybie cluster7: dowolny podzbiór (1..6) z HEX_SIDES.
    # Dla klasycznego lake3 będą to 2 elementy.
    cluster_neighbors: Optional[Tuple[str, ...]] = None
    cluster_tile: Optional[str] = None  # nazwa kafla w cluster7: center/top/... 


def _normalize_opts(opts: LakeOptions) -> LakeOptions:
    lake_radius = float(opts.lake_radius)
    if lake_radius < 0.05:
        lake_radius = 0.05
    if lake_radius > 1.5:
        lake_radius = 1.5
    shore_width = int(opts.shore_width)
    if shore_width < 0:
        shore_width = 0

    outflow_side = opts.outflow_side
    if outflow_side is not None and outflow_side not in HEX_SIDES:
        outflow_side = None

    if (
        lake_radius == float(opts.lake_radius)
        and shore_width == int(opts.shore_width)
        and outflow_side == opts.outflow_side
    ):
        return opts

    return replace(opts, lake_radius=lake_radius, shore_width=shore_width, outflow_side=outflow_side)


def _cluster7_tile_centers(grid: int) -> Dict[str, Tuple[float, float]]:
    # Układ spójny z Hex Inspectorem / replay: radius = grid/2
    radius = grid / 2.0
    dx = 1.5 * radius
    dy = math.sqrt(3.0) * radius
    dy_half = dy / 2.0
    return {
        "center": (0.0, 0.0),
        "top": (0.0, -dy),
        "bottom": (0.0, dy),
        "top_right": (dx, -dy_half),
        "bottom_right": (dx, dy_half),
        "top_left": (-dx, -dy_half),
        "bottom_left": (-dx, dy_half),
    }


def _global_lake_field_params(grid: int, seed: int, neighbors: Tuple[str, ...]) -> Tuple[Tuple[float, float], float]:
    centers = _cluster7_tile_centers(grid)
    chosen = ["center", *list(neighbors)]
    pts = [centers[name] for name in chosen if name in centers]
    if not pts:
        return (0.0, 0.0), (grid / 2.0)

    cx = sum(p[0] for p in pts) / float(len(pts))
    cy = sum(p[1] for p in pts) / float(len(pts))

    # Dobierz promień na podstawie geometrii aktywnych kafli:
    # - licz max dystans od środka (centroid) do centrów aktywnych kafli
    # - dodaj stały margines (0.25 * promień heksa), żeby zostały naturalne brzegi
    # Ta heurystyka skaluje się do 2..7 heksów w cluster7 i daje sensowny lake3.
    hex_r = grid / 2.0
    max_d = 0.0
    for px, py in pts:
        d = math.hypot(px - cx, py - cy)
        if d > max_d:
            max_d = d
    base_radius = max_d + (hex_r * 0.25)

    # Lekka losowość, ale stabilna dla seed.
    rng = random.Random(seed + 1337)
    base_radius *= 0.95 + rng.random() * 0.10

    return (cx, cy), base_radius


def _compute_water_mask_single(grid: int, mask: Sequence[Sequence[bool]], opts: LakeOptions) -> List[List[bool]]:
    cx, cy = _hex_center(grid)
    # lake_radius jest względem promienia heksa (grid/2)
    base_r = (grid / 2.0) * float(opts.lake_radius)
    seed = int(opts.seed)

    water = [[False for _ in range(grid)] for _ in range(grid)]
    for row in range(grid):
        for col in range(grid):
            if not mask[row][col]:
                continue
            dx = (col + 0.5) - cx
            dy = (row + 0.5) - cy
            dist = math.hypot(dx, dy)
            angle = math.atan2(dy, dx)
            jitter = _sample_jitter(seed, angle)
            if dist <= base_r * (1.0 + jitter):
                water[row][col] = True

    # outflow: kanał do krawędzi
    if opts.outflow_side:
        water = _carve_outflow_channel_single(water, mask, opts)

    return water


def _compute_water_mask_cluster3(grid: int, mask: Sequence[Sequence[bool]], opts: LakeOptions) -> List[List[bool]]:
    assert opts.cluster_seed is not None
    assert opts.cluster_neighbors is not None
    assert opts.cluster_tile is not None

    centers = _cluster7_tile_centers(grid)
    tile_offset = centers.get(opts.cluster_tile, (0.0, 0.0))
    lake_center, base_r = _global_lake_field_params(grid, int(opts.cluster_seed), opts.cluster_neighbors)
    # W trybie klastrowym lake_radius jest mnożnikiem promienia pola (typowo 0.85..1.15).
    base_r *= float(opts.lake_radius)

    # Pracujemy w układzie współrzędnych "środek heksa = (0,0)" dla każdego kafla,
    # a potem przesuwamy o offset środka kafla w klastrze. To zapewnia ciągłość
    # kształtu jeziora na stykach między heksami.
    local_cx, local_cy = _hex_center(grid)

    seed = int(opts.cluster_seed)
    water = [[False for _ in range(grid)] for _ in range(grid)]
    for row in range(grid):
        for col in range(grid):
            if not mask[row][col]:
                continue
            # global coords: tile local shifted by tile_offset
            gx = ((col + 0.5) - local_cx) + tile_offset[0]
            gy = ((row + 0.5) - local_cy) + tile_offset[1]
            dx = gx - lake_center[0]
            dy = gy - lake_center[1]
            dist = math.hypot(dx, dy)
            angle = math.atan2(dy, dx)
            jitter = _sample_jitter(seed, angle)
            if dist <= base_r * (1.0 + jitter):
                water[row][col] = True

    # outflow: na razie tylko na kaflu center (najczytelniej)
    outflow_trace: List[Tuple[float, float, float]] | None = None
    if opts.outflow_side and opts.cluster_tile == "center":
        water, outflow_trace = _carve_outflow_channel_single(water, mask, opts, return_trace=True)

    # Zapewnij "zewnętrzny" pas lądu pod brzeg: tam gdzie nie ma sąsiedniego heksa jeziora,
    # cofamy wodę od krawędzi heksa, żeby bank mógł się narysować na całym obwodzie.
    allowed = _cluster_allowed_boundary_sides(grid, opts)
    forbidden: set[str] = set(HEX_SIDES) - set(allowed)
    # margin w komórkach siatki: zależny od shore_width (ale zawsze >= 1)
    margin = max(1.0, float(getattr(opts, "shore_width", 1)) + 0.65)
    _apply_external_edge_margin(water, mask, forbidden_sides=forbidden, margin=margin, grid=grid)

    # Jeżeli lake3 ma odpływ, to zwykłe "pozwolenie wodzie dojść do krawędzi" często daje
    # zbyt szerokie otwarcie (wygląda jak urwany brzeg). Zawężamy ujście: w pasie przy krawędzi
    # odpływu zostawiamy wodę tylko blisko osi kanału.
    if (
        outflow_trace
        and opts.outflow_side
        and opts.cluster_tile == "center"
        and str(opts.outflow_side) in HEX_SIDES
    ):
        _constrict_outflow_mouth(
            water,
            mask,
            grid=grid,
            outflow_side=str(opts.outflow_side),
            edge_band=margin,
            trace=outflow_trace,
        )

    return water


def _constrict_outflow_mouth(
    water: List[List[bool]],
    mask: Sequence[Sequence[bool]],
    *,
    grid: int,
    outflow_side: str,
    edge_band: float,
    trace: Sequence[Tuple[float, float, float]],
) -> None:
    """Zawęża ujście odpływu w pasie przy krawędzi outflow_side.

    Zostawia wodę tylko w pobliżu osi kanału odpływu, żeby brzeg dookoła ujścia
    miał miejsce na narysowanie banku.
    """

    if not trace:
        return
    edges = _edge_segments_by_side(grid)
    if outflow_side not in edges:
        return

    (ax, ay), (bx, by) = edges[outflow_side]

    # szerokość "tolerancji" wokół osi kanału (poza samą szerokością kanału)
    max_half = max(hw for (_, _, hw) in trace)
    keep_extra = 0.75
    keep_dist = max(1.0, float(max_half) + keep_extra)

    for row in range(grid):
        for col in range(grid):
            if not mask[row][col] or not water[row][col]:
                continue
            px = col + 0.5
            py = row + 0.5
            # interesuje nas tylko woda blisko krawędzi odpływu
            if _distance_point_to_segment(px, py, ax, ay, bx, by) > edge_band:
                continue

            # sprawdź odległość do osi kanału (po próbkach)
            min_d = 1e9
            for sx, sy, _ in trace:
                d = math.hypot(px - sx, py - sy)
                if d < min_d:
                    min_d = d
                    if min_d <= keep_dist:
                        break

            if min_d > keep_dist:
                water[row][col] = False


def _carve_outflow_channel_single(
    water: List[List[bool]],
    mask: Sequence[Sequence[bool]],
    opts: LakeOptions,
    *,
    return_trace: bool = False,
) -> Any:
    grid = len(water)
    side = opts.outflow_side
    if not side:
        return (water, None) if return_trace else water

    cx, cy = _hex_center(grid)
    end = _side_midpoint(grid, side)
    dir_vec = _normalize((end[0] - cx, end[1] - cy))
    if dir_vec == (0.0, 0.0):
        return (water, None) if return_trace else water

    # Lekko „przestrzel” punkt końcowy poza krawędź, a potem tnij do maski.
    # Dzięki temu kanał pewniej dociera do samej krawędzi heksa.
    end = (end[0] + dir_vec[0] * 1.6, end[1] + dir_vec[1] * 1.6)

    # Start kanału wyznaczaj na podstawie faktycznej maski wody, aby w trybie lake3
    # (globalne pole) nie zaczynać „z lądu” przez niedopasowanie heurystyki.
    def _is_water_at(xf: float, yf: float) -> bool:
        c = int(math.floor(xf))
        r = int(math.floor(yf))
        if not (0 <= r < grid and 0 <= c < grid):
            return False
        if not mask[r][c]:
            return False
        return bool(water[r][c])

    # Szukamy ostatniego punktu na promieniu, który jest jeszcze w wodzie.
    # Zaczynamy od środka i idziemy w stronę krawędzi.
    samples = max(24, int(grid * 2.0))
    last_water: Tuple[float, float] | None = None
    for i in range(samples + 1):
        t = i / max(1, samples)
        x = cx + (end[0] - cx) * t
        y = cy + (end[1] - cy) * t
        if _is_water_at(x, y):
            last_water = (x, y)
        elif last_water is not None:
            break

    if last_water is None:
        # Fallback: jeżeli z jakiegoś powodu środek nie jest w wodzie, zachowaj stare zachowanie.
        base_r = (grid / 2.0) * float(opts.lake_radius)
        start = (cx + dir_vec[0] * base_r * 0.78, cy + dir_vec[1] * base_r * 0.78)
    else:
        # Cofnij o 1.5 komórki w głąb, żeby kanał startował w jeziorze.
        start = (last_water[0] - dir_vec[0] * 1.5, last_water[1] - dir_vec[1] * 1.5)

    width = max(1.2, float(opts.outflow_width))

    # próbkowanie od start do end
    steps = int(max(12, math.hypot(end[0] - start[0], end[1] - start[1]) * 2.0))
    trace: List[Tuple[float, float, float]] = []
    for i in range(steps + 1):
        t = i / max(1, steps)
        x = start[0] + (end[0] - start[0]) * t
        y = start[1] + (end[1] - start[1]) * t
        # Zmiana szerokości: nieco węższy przy starcie, wyraźniej szerszy przy krawędzi
        # (łatwiejsze łączenie z rzeką w sąsiednim heksie).
        local_width = width * (0.85 + 0.35 * t)
        half = local_width / 2.0
        trace.append((x, y, half))
        col0 = int(math.floor(x))
        row0 = int(math.floor(y))
        for dr in range(-2, 3):
            for dc in range(-2, 3):
                col = col0 + dc
                row = row0 + dr
                if not (0 <= row < grid and 0 <= col < grid):
                    continue
                if not mask[row][col]:
                    continue
                # dystans od środka komórki do punktu linii
                dx = (col + 0.5) - x
                dy = (row + 0.5) - y
                if math.hypot(dx, dy) <= half:
                    water[row][col] = True
    return (water, trace) if return_trace else water


def _compute_banks(mask: Sequence[Sequence[bool]], water: Sequence[Sequence[bool]], shore_width: int) -> List[List[bool]]:
    grid = len(water)
    bank = [[False for _ in range(grid)] for _ in range(grid)]
    offsets = ((-1, 0), (1, 0), (0, -1), (0, 1))

    # shoreline: ląd przy wodzie
    for row in range(grid):
        for col in range(grid):
            if not mask[row][col]:
                continue
            if water[row][col]:
                continue
            for dc, dr in offsets:
                nc = col + dc
                nr = row + dr
                if 0 <= nr < grid and 0 <= nc < grid and mask[nr][nc] and water[nr][nc]:
                    bank[row][col] = True
                    break

    # poszerz brzeg
    for _ in range(max(0, shore_width - 1)):
        next_bank = [row[:] for row in bank]
        for row in range(grid):
            for col in range(grid):
                if not mask[row][col] or water[row][col] or bank[row][col]:
                    continue
                for dc, dr in offsets:
                    nc = col + dc
                    nr = row + dr
                    if 0 <= nr < grid and 0 <= nc < grid and bank[nr][nc]:
                        next_bank[row][col] = True
                        break
        bank = next_bank

    return bank


def _water_gradient_fill(
    pixels: Any,
    grid: int,
    mask: Sequence[Sequence[bool]],
    water: Sequence[Sequence[bool]],
    bank: Sequence[Sequence[bool]],
    seed: int,
    base_water: Tuple[int, int, int, int],
) -> None:
    # BFS od brzegu (woda przy lądzie) w głąb jeziora
    from collections import deque

    shore_color = DEFAULT_WATER_SHORE_COLOR
    center_color = DEFAULT_WATER_CENTER_COLOR if base_water == DEFAULT_WATER_COLOR else base_water

    dist = [[-1 for _ in range(grid)] for _ in range(grid)]
    q: deque[Tuple[int, int]] = deque()

    offsets = ((-1, 0), (1, 0), (0, -1), (0, 1))

    for row in range(grid):
        for col in range(grid):
            if not mask[row][col] or not water[row][col]:
                continue
            # jeśli dotyka lądu/brzegu => dystans 0
            touching = False
            for dc, dr in offsets:
                nc = col + dc
                nr = row + dr
                if not (0 <= nr < grid and 0 <= nc < grid) or not mask[nr][nc]:
                    touching = True
                    break
                if bank[nr][nc] or (not water[nr][nc]):
                    touching = True
                    break
            if touching:
                dist[row][col] = 0
                q.append((col, row))

    while q:
        col, row = q.popleft()
        for dc, dr in offsets:
            nc = col + dc
            nr = row + dr
            if not (0 <= nr < grid and 0 <= nc < grid):
                continue
            if not mask[nr][nc] or not water[nr][nc]:
                continue
            if dist[nr][nc] != -1:
                continue
            dist[nr][nc] = dist[row][col] + 1
            q.append((nc, nr))

    max_d = 1
    for row in range(grid):
        for col in range(grid):
            if dist[row][col] > max_d:
                max_d = dist[row][col]

    rng = random.Random(seed + 999)
    for row in range(grid):
        for col in range(grid):
            if not mask[row][col] or not water[row][col]:
                continue
            d = dist[row][col]
            if d < 0:
                d = 0
            t = min(1.0, float(d) / float(max_d))
            # lekka "głębia" w środku
            t = t**1.25
            # drobny dithering
            t = max(0.0, min(1.0, t + (rng.random() - 0.5) * 0.03))
            color = _lerp_color(shore_color, center_color, t)
            pixels[col, row] = color


def _hash_unit(seed: int, ix: int, iy: int) -> float:
    """Deterministyczny 'random' w [0,1) zależny od seed i współrzędnych."""
    # Prosty 32-bit mix (bez zależności od numpy).
    v = (seed ^ (ix * 0x9E3779B1) ^ (iy * 0x85EBCA77)) & 0xFFFFFFFF
    v ^= (v >> 16)
    v = (v * 0x7FEB352D) & 0xFFFFFFFF
    v ^= (v >> 15)
    v = (v * 0x846CA68B) & 0xFFFFFFFF
    v ^= (v >> 16)
    return (v & 0xFFFFFFFF) / 4294967296.0


def _water_fill_cluster3(
    pixels: Any,
    grid: int,
    mask: Sequence[Sequence[bool]],
    water: Sequence[Sequence[bool]],
    seed: int,
    base_water: Tuple[int, int, int, int],
    *,
    lake_center: Tuple[float, float],
    base_r: float,
    noise_offset: Tuple[float, float],
) -> None:
    """Spójny (bezszwowy) fill wody dla lake3.

    BFS od brzegu w pojedynczym heksie traktuje granice heksów w klastrze jak ląd,
    co daje widoczne szwy. Tutaj kolor zależy od globalnej odległości od wspólnego
    centrum jeziora, więc przejście jest ciągłe między heksami.
    """

    shore_color = DEFAULT_WATER_SHORE_COLOR
    center_color = DEFAULT_WATER_CENTER_COLOR if base_water == DEFAULT_WATER_COLOR else base_water

    # Normalizacja: 0 przy brzegu (ok. base_r), 1 bliżej środka.
    denom = max(1e-6, float(base_r) * 1.05)
    offx, offy = noise_offset

    for row in range(grid):
        for col in range(grid):
            if not mask[row][col] or not water[row][col]:
                continue
            gx = (col + 0.5) + offx
            gy = (row + 0.5) + offy
            d = math.hypot(gx - lake_center[0], gy - lake_center[1])
            t = 1.0 - max(0.0, min(1.0, d / denom))
            t = t**1.25

            # deterministyczny dithering (w globalnych współrzędnych, by nie było szwu)
            qx = int(round(gx * 2.0))
            qy = int(round(gy * 2.0))
            jitter = (_hash_unit(seed + 999, qx, qy) - 0.5) * 0.03
            t = max(0.0, min(1.0, t + jitter))

            pixels[col, row] = _lerp_color(shore_color, center_color, t)


def render_lake(opts: LakeOptions) -> Tuple[Image.Image, Dict[str, Any]]:
    opts = _normalize_opts(opts)
    grid = int(opts.grid_size)
    mask = build_hex_mask(grid)
    background = _load_background(grid, mask, opts.background)

    # water mask
    is_cluster = bool(opts.cluster_seed is not None and opts.cluster_neighbors and opts.cluster_tile)
    lake_center: Tuple[float, float] | None = None
    base_r: float | None = None
    noise_offset: Tuple[float, float] | None = None
    if is_cluster:
        assert opts.cluster_seed is not None
        assert opts.cluster_neighbors is not None
        assert opts.cluster_tile is not None

        cluster_seed = int(opts.cluster_seed)
        water = _compute_water_mask_cluster3(grid, mask, opts)
        seed_for_fill = cluster_seed
        mode = "lake3"
        # parametry globalne do bezszwowego fill (spójne z _compute_water_mask_cluster3)
        centers = _cluster7_tile_centers(grid)
        tile_offset = centers.get(str(opts.cluster_tile), (0.0, 0.0))
        local_cx, local_cy = _hex_center(grid)
        lake_center, base_r = _global_lake_field_params(grid, cluster_seed, opts.cluster_neighbors)
        noise_offset = (-local_cx + tile_offset[0], -local_cy + tile_offset[1])
    else:
        water = _compute_water_mask_single(grid, mask, opts)
        seed_for_fill = int(opts.seed)
        mode = "lake1"

    bank = _compute_banks(mask, water, opts.shore_width)

    img = Image.new("RGBA", (grid, grid), (0, 0, 0, 0))
    px = img.load()
    assert px is not None

    # tło
    for row in range(grid):
        for col in range(grid):
            if not mask[row][col]:
                continue
            color = background[row][col]
            px[col, row] = (0, 0, 0, 0) if color is None else color

    # brzeg
    for row in range(grid):
        for col in range(grid):
            if not mask[row][col] or not bank[row][col]:
                continue
            px[col, row] = opts.bank_color

    # woda (gradient)
    if is_cluster:
        assert lake_center is not None
        assert base_r is not None
        assert noise_offset is not None
        _water_fill_cluster3(
            px,
            grid,
            mask,
            water,
            seed_for_fill,
            opts.water_color,
            lake_center=lake_center,
            base_r=base_r,
            noise_offset=noise_offset,
        )
    else:
        _water_gradient_fill(px, grid, mask, water, bank, seed_for_fill, opts.water_color)

    meta: Dict[str, Any] = {
        "category": "lake",
        "mode": mode,
        "grid": grid,
        "seed": int(opts.seed),
        "lake_radius": float(opts.lake_radius),
        "shore_width": int(opts.shore_width),
        "outflow_side": opts.outflow_side,
        "outflow_width": float(opts.outflow_width),
        "bank_color": {"rgba": list(opts.bank_color), "hex": rgba_to_hex(opts.bank_color)},
        "water_color": {"rgba": list(opts.water_color), "hex": rgba_to_hex(opts.water_color)},
    }
    if opts.cluster_seed is not None:
        meta["cluster_seed"] = int(opts.cluster_seed)
        meta["cluster_neighbors"] = list(opts.cluster_neighbors or [])
        meta["cluster_tile"] = opts.cluster_tile

    return img, meta


def generate_lake(opts: LakeOptions, output_path: Path) -> Dict[str, Any]:
    img, meta = render_lake(opts)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    img.save(output_path)
    return meta


def main(argv: Optional[List[str]] = None) -> int:
    p = argparse.ArgumentParser(description="Generate lake hex tile (single) for editors/QA")
    p.add_argument("--grid", type=int, default=64)
    p.add_argument("--background", type=str, default=None)
    p.add_argument("--seed", type=int, default=12345)
    p.add_argument("--lake-radius", type=float, default=0.34)
    p.add_argument("--shore-width", type=int, default=2)
    p.add_argument("--outflow-side", type=str, default=None)
    p.add_argument("--out", type=str, default=str(ASSET_DIR / "lake_test.png"))
    args = p.parse_args(argv)

    bg = (ASSET_DIR / args.background) if args.background else None
    opts = LakeOptions(
        grid_size=args.grid,
        background=bg,
        seed=args.seed,
        lake_radius=args.lake_radius,
        shore_width=args.shore_width,
        outflow_side=args.outflow_side,
    )
    meta = generate_lake(opts, Path(args.out))
    Path(args.out).with_suffix(".json").write_text(json.dumps(meta, ensure_ascii=False, indent=2), encoding="utf-8")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
