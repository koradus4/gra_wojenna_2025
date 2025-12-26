"""Generator torów kolejowych dla heksów.

Generuje tekstury torów kolejowych przecinających heks.
Kluczowe cechy:
- Tory jednotorowe i dwutorowe
- Łagodne dojazdy (rozjazdy) zamiast skrzyżowań - krzywe Béziera
- Wykluczenie prostopadłych połączeń (min kąt ~60° między torami)
- Realistyczne renderowanie: szyny, podkłady, podsypka
"""

from __future__ import annotations

import json
import math
import random
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, List, Optional, Sequence, Tuple

from PIL import Image, ImageDraw


# ============================================================================
# STAŁE I KOLORY
# ============================================================================

EXPORT_SIZE_BY_GRID = {64: 512, 128: 1024}

# Boki heksa (pointy-top)
HEX_SIDES = ("top", "top_right", "bottom_right", "bottom", "bottom_left", "top_left")

# Kąty boków heksa (stopnie, 0 = prawo, zgodnie z ruchem wskazówek zegara)
SIDE_ANGLES: Dict[str, float] = {
    "top": 270,
    "top_right": 330,
    "bottom_right": 30,
    "bottom": 90,
    "bottom_left": 150,
    "top_left": 210,
}

# Przeciwne boki
SIDE_OPPOSITE: Dict[str, str] = {
    "top": "bottom",
    "top_right": "bottom_left",
    "bottom_right": "top_left",
    "bottom": "top",
    "bottom_left": "top_right",
    "top_left": "bottom_right",
}

# Minimalny kąt między torami dojazdu (stopnie)
# Boki heksa są co 60°, więc dozwolone połączenia to sąsiednie boki
JUNCTION_MIN_ANGLE_DEG = 25.0

# Kolory torów - PIXEL ART STYLE
RAILWAY_COLORS = {
    # Szyny - stalowe
    "rail": (40, 40, 45, 255),           # Ciemna stal
    "rail_top": (100, 100, 110, 255),    # Jasny wierzch szyny
    
    # Podkłady - ciemne drewno, bardzo kontrastowe
    "sleeper_dark": (50, 30, 15, 255),   # Ciemny brąz - główny
    "sleeper_mid": (70, 45, 25, 255),    # Średni brąz
    "sleeper_light": (90, 60, 35, 255),  # Jasny brąz - góra
    
    # Podsypka - piaskowo-kamienna, pixel art
    "ballast_1": (180, 165, 130, 255),   # Jasny piasek
    "ballast_2": (160, 145, 110, 255),   # Średni piasek
    "ballast_3": (140, 125, 95, 255),    # Ciemniejszy piasek
    "ballast_4": (120, 105, 80, 255),    # Kamień ciemny
    "ballast_edge": (100, 85, 65, 255),  # Krawędź - brązowa
}

# Wymiary torów - GRUBE PODKŁADY
RAILWAY_DIMENSIONS = {
    "jednotorowy": {
        "track_gauge": 3.5,       # Rozstaw szyn
        "rail_width": 1.5,        # Grubość szyny
        "sleeper_width": 9.0,     # Długość podkładu - DŁUŻSZY
        "sleeper_height": 2.0,    # Grubość podkładu - GRUBSZY
        "sleeper_spacing": 3.5,   # Odstęp między podkładami
        "ballast_width": 12.0,    # Szerokość podsypki - SZERSZA
    },
    "dwutorowy": {
        "track_gauge": 3.5,
        "rail_width": 1.5,
        "sleeper_width": 8.0,
        "sleeper_height": 2.0,
        "sleeper_spacing": 3.5,
        "ballast_width": 22.0,
        "track_separation": 8.0,
    },
}


# ============================================================================
# DATACLASSES
# ============================================================================

@dataclass
class RailwayOptions:
    """Opcje generowania torów w heksie."""
    grid_size: int
    background: Path | None
    entry_side: str
    exit_side: str
    railway_type: str = "jednotorowy"  # jednotorowy, dwutorowy
    seed: int = 42
    # Opcjonalne dojazdy - lista dodatkowych boków (tylko łagodne kąty!)
    junctions: List[str] = field(default_factory=list)
    # Czy dojazdy mają być dwutorowe? (domyślnie False - jednotorowe)
    junction_double_track: bool = False


@dataclass
class RailwayResult:
    """Wynik generowania torów."""
    image_path: Path
    metadata_path: Path
    metadata: Dict[str, Any]


# ============================================================================
# FUNKCJE POMOCNICZE - GEOMETRIA HEKSA
# ============================================================================

def _clamp(value: float, min_val: float, max_val: float) -> float:
    return max(min_val, min(max_val, value))


def _hex_center(grid: int) -> Tuple[float, float]:
    return grid / 2.0, grid / 2.0


def _hex_vertices(grid: int) -> List[Tuple[float, float]]:
    """Zwraca wierzchołki heksa (pointy-top)."""
    cx, cy = _hex_center(grid)
    radius = grid / 2.0 - 0.5
    sqrt3 = math.sqrt(3.0)
    return [
        (cx - radius, cy),                                  # 0: lewa
        (cx - radius / 2.0, cy - (sqrt3 / 2.0) * radius),   # 1: góra-lewa
        (cx + radius / 2.0, cy - (sqrt3 / 2.0) * radius),   # 2: góra-prawa
        (cx + radius, cy),                                  # 3: prawa
        (cx + radius / 2.0, cy + (sqrt3 / 2.0) * radius),   # 4: dół-prawa
        (cx - radius / 2.0, cy + (sqrt3 / 2.0) * radius),   # 5: dół-lewa
    ]


def _side_to_edge_center(side: str, grid: int) -> Tuple[float, float]:
    """Zwraca środek krawędzi heksa dla danego boku."""
    vertices = _hex_vertices(grid)
    side_to_vertices = {
        "top": (1, 2),
        "top_right": (2, 3),
        "bottom_right": (3, 4),
        "bottom": (4, 5),
        "bottom_left": (5, 0),
        "top_left": (0, 1),
    }
    i1, i2 = side_to_vertices[side]
    x = (vertices[i1][0] + vertices[i2][0]) / 2.0
    y = (vertices[i1][1] + vertices[i2][1]) / 2.0
    return x, y


def _build_hex_mask(grid: int) -> List[List[bool]]:
    """Buduje maskę heksa."""
    vertices = _hex_vertices(grid)
    mask = [[False for _ in range(grid)] for _ in range(grid)]
    
    for row in range(grid):
        for col in range(grid):
            x, y = col + 0.5, row + 0.5
            if _point_in_polygon(x, y, vertices):
                mask[row][col] = True
    return mask


def _point_in_polygon(x: float, y: float, polygon: Sequence[Tuple[float, float]]) -> bool:
    """Sprawdza czy punkt jest wewnątrz wielokąta."""
    inside = False
    j = len(polygon) - 1
    for i in range(len(polygon)):
        xi, yi = polygon[i]
        xj, yj = polygon[j]
        if ((yi > y) != (yj > y)) and (x < (xj - xi) * (y - yi) / (yj - yi + 1e-10) + xi):
            inside = not inside
        j = i
    return inside


def _angle_between_sides(side1: str, side2: str) -> float:
    """Oblicza kąt między dwoma bokami heksa (0-180 stopni)."""
    a1 = SIDE_ANGLES[side1]
    a2 = SIDE_ANGLES[side2]
    diff = abs(a1 - a2)
    if diff > 180:
        diff = 360 - diff
    return diff


def _is_valid_junction(main_entry: str, main_exit: str, junction_side: str) -> bool:
    """
    Sprawdza czy dojazd z junction_side jest dozwolony.
    Wyklucza prostopadłe połączenia - dozwolone tylko łagodne łuki.
    """
    # Dojazd nie może być tym samym co wejście/wyjście główne
    if junction_side in (main_entry, main_exit):
        return False
    
    # Sprawdź kąt względem głównego toru
    # Główny tor idzie od entry do exit
    # Dojazd musi tworzyć łagodny kąt (nie prostopadły)
    
    # Dla heksa boki są co 60°, więc:
    # - Sąsiednie boki (60°) - OK, łagodny łuk
    # - Przez jeden bok (120°) - może być za ostro, ale dopuszczalne
    # - Naprzeciwko (180°) - to byłby odwrotny kierunek, nie dojazd
    # - 90° nie istnieje w heksie!
    
    angle_to_entry = _angle_between_sides(junction_side, main_entry)
    angle_to_exit = _angle_between_sides(junction_side, main_exit)
    
    # Dojazd powinien być "między" wejściem a wyjściem lub blisko jednego z nich
    # Nie dopuszczamy jeśli kąt jest zbyt mały (< 25°) - nakładałby się
    min_angle = JUNCTION_MIN_ANGLE_DEG
    
    return angle_to_entry >= min_angle and angle_to_exit >= min_angle


# ============================================================================
# KRZYWE BÉZIERA DLA ŁAGODNYCH ŁUKÓW
# ============================================================================

def _bezier_quadratic(p0: Tuple[float, float], p1: Tuple[float, float], 
                       p2: Tuple[float, float], t: float) -> Tuple[float, float]:
    """Kwadratowa krzywa Béziera."""
    x = (1 - t)**2 * p0[0] + 2 * (1 - t) * t * p1[0] + t**2 * p2[0]
    y = (1 - t)**2 * p0[1] + 2 * (1 - t) * t * p1[1] + t**2 * p2[1]
    return x, y


def _bezier_cubic(p0: Tuple[float, float], p1: Tuple[float, float],
                  p2: Tuple[float, float], p3: Tuple[float, float], 
                  t: float) -> Tuple[float, float]:
    """Sześcienna krzywa Béziera."""
    x = ((1 - t)**3 * p0[0] + 3 * (1 - t)**2 * t * p1[0] + 
         3 * (1 - t) * t**2 * p2[0] + t**3 * p3[0])
    y = ((1 - t)**3 * p0[1] + 3 * (1 - t)**2 * t * p1[1] + 
         3 * (1 - t) * t**2 * p2[1] + t**3 * p3[1])
    return x, y


def _generate_straight_path(
    entry: Tuple[float, float],
    exit_pt: Tuple[float, float],
    num_points: int = 20,
) -> List[Tuple[float, float]]:
    """Generuje prostą ścieżkę toru."""
    points = []
    for i in range(num_points):
        t = i / (num_points - 1)
        x = entry[0] + (exit_pt[0] - entry[0]) * t
        y = entry[1] + (exit_pt[1] - entry[1]) * t
        points.append((x, y))
    return points


def _generate_curved_path(
    entry: Tuple[float, float],
    exit_pt: Tuple[float, float],
    center: Tuple[float, float],
    curve_factor: float = 0.4,
    num_points: int = 24,
) -> List[Tuple[float, float]]:
    """Generuje zakrzywioną ścieżkę toru (dla zakrętów)."""
    # Punkt kontrolny - przesunięty w stronę centrum
    ctrl_x = center[0] + (entry[0] + exit_pt[0] - 2 * center[0]) * curve_factor
    ctrl_y = center[1] + (entry[1] + exit_pt[1] - 2 * center[1]) * curve_factor
    ctrl = (ctrl_x, ctrl_y)
    
    points = []
    for i in range(num_points):
        t = i / (num_points - 1)
        pt = _bezier_quadratic(entry, ctrl, exit_pt, t)
        points.append(pt)
    return points


def _generate_junction_curve(
    junction_entry: Tuple[float, float],
    merge_point: Tuple[float, float],
    main_direction: Tuple[float, float],
    junction_side: str,
    num_points: int = 40,
) -> List[Tuple[float, float]]:
    """
    Generuje REALISTYCZNY rozjazd kolejowy.
    Tor dochodzący łączy się pod małym kątem, W TYM SAMYM kierunku co tor główny.
    main_direction wskazuje kierunek OD ENTRY DO EXIT.
    """
    dx = merge_point[0] - junction_entry[0]
    dy = merge_point[1] - junction_entry[1]
    length = math.sqrt(dx*dx + dy*dy)
    
    if length < 1:
        return [junction_entry, merge_point]
    
    # Kierunek wejścia dojazdu (od krawędzi heksa do środka)
    entry_angle = SIDE_ANGLES[junction_side]
    entry_rad = math.radians(entry_angle + 180)
    entry_dir = (math.cos(entry_rad), math.sin(entry_rad))
    
    # Normalizuj kierunek głównego toru (od entry do exit)
    md_len = math.sqrt(main_direction[0]**2 + main_direction[1]**2)
    if md_len > 0:
        main_dir = (main_direction[0] / md_len, main_direction[1] / md_len)
    else:
        main_dir = (1, 0)
    
    # PUNKT KONTROLNY 1: Krótki prosty odcinek od wejścia dojazdu
    ctrl1_dist = length * 0.3
    ctrl1 = (
        junction_entry[0] + entry_dir[0] * ctrl1_dist,
        junction_entry[1] + entry_dir[1] * ctrl1_dist,
    )
    
    # PUNKT KONTROLNY 2: ZA merge_point w kierunku WYJŚCIA
    # (żeby krzywa wchodziła ZGODNIE z ruchem na torze głównym)
    ctrl2_dist = length * 0.5
    ctrl2 = (
        merge_point[0] + main_dir[0] * ctrl2_dist,
        merge_point[1] + main_dir[1] * ctrl2_dist,
    )
    
    # Krzywa kubiczna Béziera - ale ODWRÓCONA
    # bo ctrl2 jest ZA merge_point, więc rysujemy od merge do junction
    # i potem odwracamy listę punktów
    points = []
    for i in range(num_points):
        t = i / (num_points - 1)
        pt = _bezier_cubic(merge_point, ctrl2, ctrl1, junction_entry, t)
        points.append(pt)
    
    # Odwróć żeby szło od junction_entry do merge_point
    points.reverse()
    return points


# ============================================================================
# RENDEROWANIE TORÓW - PIXEL ART STYLE
# ============================================================================

def _draw_ballast_pixelart(
    img: Image.Image,
    path: List[Tuple[float, float]],
    width: float,
    rng: random.Random,
) -> None:
    """Rysuje podsypkę piaskowo-kamienną w stylu pixel art."""
    pixels = img.load()
    grid = img.size[0]
    
    colors = [
        RAILWAY_COLORS["ballast_1"],
        RAILWAY_COLORS["ballast_2"],
        RAILWAY_COLORS["ballast_3"],
        RAILWAY_COLORS["ballast_4"],
    ]
    edge_color = RAILWAY_COLORS["ballast_edge"]
    
    # Zbierz wszystkie piksele podsypki
    ballast_pixels = set()
    half_width = width / 2
    
    for i in range(len(path) - 1):
        x1, y1 = path[i]
        x2, y2 = path[i + 1]
        
        # Interpoluj wzdłuż segmentu
        dx = x2 - x1
        dy = y2 - y1
        length = math.sqrt(dx*dx + dy*dy)
        if length < 0.1:
            continue
        
        steps = int(length * 2) + 1
        for step in range(steps):
            t = step / max(1, steps - 1)
            cx = x1 + dx * t
            cy = y1 + dy * t
            
            # Wektor prostopadły
            nx, ny = -dy / length, dx / length
            
            # Wypełnij szerokość podsypki
            for offset in range(-int(half_width) - 1, int(half_width) + 2):
                px = int(cx + nx * offset)
                py = int(cy + ny * offset)
                if 0 <= px < grid and 0 <= py < grid:
                    dist_from_center = abs(offset)
                    ballast_pixels.add((px, py, dist_from_center))
    
    # Rysuj piksele z teksturą kamieni
    for px, py, dist in ballast_pixels:
        # Krawędź ciemniejsza
        if dist > half_width - 1.5:
            pixels[px, py] = edge_color
        else:
            # Losowy kolor kamyka - pixel art pattern
            noise = rng.random()
            if noise < 0.3:
                color = colors[0]  # Jasny
            elif noise < 0.55:
                color = colors[1]  # Średni
            elif noise < 0.8:
                color = colors[2]  # Ciemniejszy
            else:
                color = colors[3]  # Ciemny kamień
            pixels[px, py] = color


def _draw_ballast(
    draw: ImageDraw.Draw,
    path: List[Tuple[float, float]],
    width: float,
) -> None:
    """Rysuje podstawową podsypkę (backup)."""
    edge_color = RAILWAY_COLORS["ballast_edge"]
    main_color = RAILWAY_COLORS["ballast_2"]
    
    edge_width = width + 3
    for i in range(len(path) - 1):
        x1, y1 = path[i]
        x2, y2 = path[i + 1]
        draw.line([(x1, y1), (x2, y2)], fill=edge_color, width=int(edge_width))
    
    for i in range(len(path) - 1):
        x1, y1 = path[i]
        x2, y2 = path[i + 1]
        draw.line([(x1, y1), (x2, y2)], fill=main_color, width=int(width))


def _draw_sleepers(
    draw: ImageDraw.Draw,
    path: List[Tuple[float, float]],
    sleeper_width: float,
    sleeper_height: float,
    spacing: float,
) -> None:
    """Rysuje podkłady kolejowe - GRUBE z efektem 3D."""
    dark_color = RAILWAY_COLORS["sleeper_dark"]
    mid_color = RAILWAY_COLORS["sleeper_mid"]
    light_color = RAILWAY_COLORS["sleeper_light"]
    
    # Oblicz całkowitą długość ścieżki
    total_length = 0.0
    segment_lengths = []
    for i in range(len(path) - 1):
        dx = path[i+1][0] - path[i][0]
        dy = path[i+1][1] - path[i][1]
        seg_len = math.sqrt(dx*dx + dy*dy)
        segment_lengths.append(seg_len)
        total_length += seg_len
    
    if total_length < spacing:
        return
    
    # Rozmieść podkłady RÓWNOMIERNIE
    num_sleepers = int(total_length / spacing)
    if num_sleepers < 1:
        return
    
    actual_spacing = total_length / num_sleepers
    
    for sleeper_idx in range(num_sleepers):
        target_dist = sleeper_idx * actual_spacing + actual_spacing / 2
        
        # Znajdź pozycję na ścieżce
        current_dist = 0.0
        for seg_idx in range(len(segment_lengths)):
            seg_len = segment_lengths[seg_idx]
            
            if current_dist + seg_len >= target_dist:
                t = (target_dist - current_dist) / seg_len if seg_len > 0 else 0
                
                x1, y1 = path[seg_idx]
                x2, y2 = path[seg_idx + 1]
                
                x = x1 + (x2 - x1) * t
                y = y1 + (y2 - y1) * t
                
                dx = x2 - x1
                dy = y2 - y1
                length = math.sqrt(dx*dx + dy*dy)
                
                if length > 0:
                    tx, ty = dx / length, dy / length
                    nx, ny = -ty, tx
                    
                    half_w = sleeper_width / 2
                    half_h = sleeper_height / 2
                    
                    # WARSTWA 1: Cień (przesunięty w dół)
                    shadow_offset = 0.8
                    shadow_corners = [
                        (x - nx * half_w - tx * half_h + shadow_offset, y - ny * half_w - ty * half_h + shadow_offset),
                        (x + nx * half_w - tx * half_h + shadow_offset, y + ny * half_w - ty * half_h + shadow_offset),
                        (x + nx * half_w + tx * half_h + shadow_offset, y + ny * half_w + ty * half_h + shadow_offset),
                        (x - nx * half_w + tx * half_h + shadow_offset, y - ny * half_w + ty * half_h + shadow_offset),
                    ]
                    draw.polygon(shadow_corners, fill=dark_color)
                    
                    # WARSTWA 2: Główny podkład
                    main_corners = [
                        (x - nx * half_w - tx * half_h, y - ny * half_w - ty * half_h),
                        (x + nx * half_w - tx * half_h, y + ny * half_w - ty * half_h),
                        (x + nx * half_w + tx * half_h, y + ny * half_w + ty * half_h),
                        (x - nx * half_w + tx * half_h, y - ny * half_w + ty * half_h),
                    ]
                    draw.polygon(main_corners, fill=mid_color)
                    
                    # WARSTWA 3: Jasna górna część (efekt 3D)
                    top_h = half_h * 0.4
                    top_corners = [
                        (x - nx * half_w * 0.85 - tx * top_h, y - ny * half_w * 0.85 - ty * top_h),
                        (x + nx * half_w * 0.85 - tx * top_h, y + ny * half_w * 0.85 - ty * top_h),
                        (x + nx * half_w * 0.85 + tx * top_h, y + ny * half_w * 0.85 + ty * top_h),
                        (x - nx * half_w * 0.85 + tx * top_h, y - ny * half_w * 0.85 + ty * top_h),
                    ]
                    draw.polygon(top_corners, fill=light_color)
                
                break
            current_dist += seg_len


def _draw_rails(
    draw: ImageDraw.Draw,
    path: List[Tuple[float, float]],
    gauge: float,
    rail_width: float,
) -> None:
    """Rysuje szyny - ciemna stal z jasnym wierzchem."""
    rail_color = RAILWAY_COLORS["rail"]
    top_color = RAILWAY_COLORS["rail_top"]
    
    half_gauge = gauge / 2
    
    # Oblicz przesunięte ścieżki dla obu szyn
    left_rail = []
    right_rail = []
    
    for i in range(len(path)):
        x, y = path[i]
        
        # Oblicz wektor prostopadły
        if i == 0 and len(path) > 1:
            dx = path[1][0] - path[0][0]
            dy = path[1][1] - path[0][1]
        elif i == len(path) - 1 and len(path) > 1:
            dx = path[-1][0] - path[-2][0]
            dy = path[-1][1] - path[-2][1]
        elif len(path) > 2:
            dx = path[i + 1][0] - path[i - 1][0]
            dy = path[i + 1][1] - path[i - 1][1]
        else:
            dx, dy = 1, 0
        
        length = math.sqrt(dx*dx + dy*dy)
        if length > 0:
            nx, ny = -dy / length, dx / length
        else:
            nx, ny = 0, 1
        
        left_rail.append((x + nx * half_gauge, y + ny * half_gauge))
        right_rail.append((x - nx * half_gauge, y - ny * half_gauge))
    
    # Rysuj szyny - główny kolor (ciemny)
    for rail in [left_rail, right_rail]:
        for i in range(len(rail) - 1):
            draw.line([rail[i], rail[i + 1]], fill=rail_color, width=int(max(2, rail_width)))
    
    # Jasny wierzch szyn (odblaski)
    top_width = max(1, rail_width * 0.5)
    for rail in [left_rail, right_rail]:
        for i in range(len(rail) - 1):
            draw.line([rail[i], rail[i + 1]], fill=top_color, width=int(top_width))


def _get_parallel_paths(
    path: List[Tuple[float, float]], 
    separation: float
) -> Tuple[List[Tuple[float, float]], List[Tuple[float, float]]]:
    """Zwraca dwie równoległe ścieżki dla toru dwutorowego."""
    left_path = []
    right_path = []
    
    for i in range(len(path)):
        x, y = path[i]
        
        if i == 0:
            dx = path[1][0] - path[0][0]
            dy = path[1][1] - path[0][1]
        elif i == len(path) - 1:
            dx = path[-1][0] - path[-2][0]
            dy = path[-1][1] - path[-2][1]
        else:
            dx = path[i + 1][0] - path[i - 1][0]
            dy = path[i + 1][1] - path[i - 1][1]
        
        length = math.sqrt(dx*dx + dy*dy)
        if length > 0:
            nx, ny = -dy / length, dx / length
        else:
            nx, ny = 0, 1
        
        half_sep = separation / 2
        left_path.append((x + nx * half_sep, y + ny * half_sep))
        right_path.append((x - nx * half_sep, y - ny * half_sep))
    
    return left_path, right_path


def _draw_single_track(
    img: Image.Image,
    draw: ImageDraw.Draw,
    path: List[Tuple[float, float]],
    dims: Dict[str, float],
    rng: random.Random,
) -> None:
    """Rysuje pojedynczy tor (podsypka pixel art + podkłady + szyny)."""
    _draw_ballast_pixelart(img, path, dims["ballast_width"], rng)
    _draw_sleepers(draw, path, dims["sleeper_width"], dims["sleeper_height"],
                   dims["sleeper_spacing"])
    _draw_rails(draw, path, dims["track_gauge"], dims["rail_width"])


def _draw_double_track(
    img: Image.Image,
    draw: ImageDraw.Draw,
    path: List[Tuple[float, float]],
    dims: Dict[str, float],
    rng: random.Random,
) -> None:
    """Rysuje podwójny tor."""
    separation = dims["track_separation"]
    
    # Oblicz przesunięte ścieżki dla obu torów
    left_path = []
    right_path = []
    
    for i in range(len(path)):
        x, y = path[i]
        
        # Oblicz wektor prostopadły na podstawie sąsiednich punktów
        if i == 0:
            dx = path[1][0] - path[0][0]
            dy = path[1][1] - path[0][1]
        elif i == len(path) - 1:
            dx = path[-1][0] - path[-2][0]
            dy = path[-1][1] - path[-2][1]
        else:
            dx = path[i + 1][0] - path[i - 1][0]
            dy = path[i + 1][1] - path[i - 1][1]
        
        length = math.sqrt(dx*dx + dy*dy)
        if length > 0:
            nx, ny = -dy / length, dx / length
        else:
            nx, ny = 0, 1
        
        half_sep = separation / 2
        left_path.append((x + nx * half_sep, y + ny * half_sep))
        right_path.append((x - nx * half_sep, y - ny * half_sep))
    
    # Rysuj wspólną podsypkę pixel art
    _draw_ballast_pixelart(img, path, dims["ballast_width"], rng)
    
    # Podkłady i szyny dla lewego toru
    _draw_sleepers(draw, left_path, dims["sleeper_width"], dims["sleeper_height"],
                   dims["sleeper_spacing"])
    _draw_rails(draw, left_path, dims["track_gauge"], dims["rail_width"])
    
    # Podkłady i szyny dla prawego toru
    _draw_sleepers(draw, right_path, dims["sleeper_width"], dims["sleeper_height"],
                   dims["sleeper_spacing"])
    _draw_rails(draw, right_path, dims["track_gauge"], dims["rail_width"])


# ============================================================================
# GŁÓWNA FUNKCJA GENEROWANIA
# ============================================================================

def generate_railway(options: RailwayOptions, output_path: Path) -> RailwayResult:
    """Generuje teksturę torów kolejowych w heksie."""
    
    grid = options.grid_size
    rng = random.Random(options.seed)
    
    # Pobierz wymiary dla typu toru
    dims = RAILWAY_DIMENSIONS.get(options.railway_type, 
                                   RAILWAY_DIMENSIONS["jednotorowy"])
    
    center = _hex_center(grid)
    entry_pt = _side_to_edge_center(options.entry_side, grid)
    exit_pt = _side_to_edge_center(options.exit_side, grid)
    
    # Sprawdź czy tor jest prosty czy zakrzywiony
    # Prosty = przeciwne boki, zakrzywiony = inne
    is_straight = SIDE_OPPOSITE.get(options.entry_side) == options.exit_side
    
    # Generuj główną ścieżkę
    if is_straight:
        main_path = _generate_straight_path(entry_pt, exit_pt)
    else:
        main_path = _generate_curved_path(entry_pt, exit_pt, center)
    
    # Generuj ścieżki dojazdów (rozjazdów)
    junction_paths = []
    valid_junctions = []
    
    for junc_side in options.junctions:
        if not _is_valid_junction(options.entry_side, options.exit_side, junc_side):
            print(f"⚠️ Dojazd z {junc_side} wykluczony (zbyt ostry kąt lub konflikt)")
            continue
        
        valid_junctions.append(junc_side)
        junc_entry = _side_to_edge_center(junc_side, grid)
        
        # Znajdź punkt połączenia na głównym torze
        # Dojazd łączy się po PRZECIWNEJ stronie niż skąd wychodzi
        # To daje naturalny kształt "Y"
        dist_to_entry = math.sqrt((junc_entry[0] - entry_pt[0])**2 + (junc_entry[1] - entry_pt[1])**2)
        dist_to_exit = math.sqrt((junc_entry[0] - exit_pt[0])**2 + (junc_entry[1] - exit_pt[1])**2)
        
        # Jeśli dojazd jest bliżej WEJŚCIA - merge daleko, bliżej WYJŚCIA (3/4)
        # Jeśli dojazd jest bliżej WYJŚCIA - merge daleko, bliżej WEJŚCIA (1/4)
        if dist_to_entry < dist_to_exit:
            merge_index = (len(main_path) * 3) // 4
        else:
            merge_index = len(main_path) // 4
        
        merge_point = main_path[merge_index]
        
        # Kierunek głównego toru w punkcie połączenia
        if merge_index > 0 and merge_index < len(main_path) - 1:
            main_dir = (
                main_path[merge_index + 1][0] - main_path[merge_index - 1][0],
                main_path[merge_index + 1][1] - main_path[merge_index - 1][1],
            )
        else:
            main_dir = (exit_pt[0] - entry_pt[0], exit_pt[1] - entry_pt[1])
        
        junc_path = _generate_junction_curve(junc_entry, merge_point, main_dir, junc_side)
        junction_paths.append(junc_path)
    
    # === RENDEROWANIE ===
    
    # Wczytaj tło lub utwórz przezroczyste
    if options.background and options.background.exists():
        img = Image.open(options.background).convert("RGBA")
        if img.size != (grid, grid):
            img = img.resize((grid, grid), Image.NEAREST)
    else:
        img = Image.new("RGBA", (grid, grid), (0, 0, 0, 0))
    
    draw = ImageDraw.Draw(img)
    
    # === RENDEROWANIE WARSTWOWE ===
    # Rysujemy wszystko warstwami żeby połączenia były płynne:
    # 1. Wszystkie podsypki
    # 2. Wszystkie podkłady  
    # 3. Wszystkie szyny
    
    is_double = options.railway_type == "dwutorowy"
    single_dims = RAILWAY_DIMENSIONS["jednotorowy"]
    double_dims = RAILWAY_DIMENSIONS["dwutorowy"]
    
    # Zbierz wszystkie ścieżki do renderowania
    all_paths_with_dims = []
    
    # Dojazdy - jednotorowe LUB dwutorowe (zależnie od junction_double_track)
    junction_dims = double_dims if options.junction_double_track else single_dims
    junction_is_double = options.junction_double_track
    for junc_path in junction_paths:
        all_paths_with_dims.append((junc_path, junction_dims, junction_is_double))
    
    # Główny tor
    all_paths_with_dims.append((main_path, dims, is_double))
    
    # WARSTWA 1: Wszystkie podsypki
    for path, path_dims, is_dbl in all_paths_with_dims:
        _draw_ballast_pixelart(img, path, path_dims["ballast_width"], rng)
    
    # WARSTWA 2: Wszystkie podkłady
    for path, path_dims, is_dbl in all_paths_with_dims:
        if is_dbl:
            # Dla dwutorowego - oblicz ścieżki obu torów
            separation = path_dims["track_separation"]
            left_path, right_path = _get_parallel_paths(path, separation)
            _draw_sleepers(draw, left_path, path_dims["sleeper_width"], 
                          path_dims["sleeper_height"], path_dims["sleeper_spacing"])
            _draw_sleepers(draw, right_path, path_dims["sleeper_width"],
                          path_dims["sleeper_height"], path_dims["sleeper_spacing"])
        else:
            _draw_sleepers(draw, path, path_dims["sleeper_width"],
                          path_dims["sleeper_height"], path_dims["sleeper_spacing"])
    
    # WARSTWA 3: Wszystkie szyny
    for path, path_dims, is_dbl in all_paths_with_dims:
        if is_dbl:
            separation = path_dims["track_separation"]
            left_path, right_path = _get_parallel_paths(path, separation)
            _draw_rails(draw, left_path, path_dims["track_gauge"], path_dims["rail_width"])
            _draw_rails(draw, right_path, path_dims["track_gauge"], path_dims["rail_width"])
        else:
            _draw_rails(draw, path, path_dims["track_gauge"], path_dims["rail_width"])
    
    # Przytnij do maski heksa
    # UWAGA: Jeśli jest tło, nie kasuj pikseli poza maską - zachowaj tło!
    mask = _build_hex_mask(grid)
    pixels = img.load()
    
    if not options.background:
        # Tylko jeśli NIE ma tła - wyczyść piksele poza heksem
        for row in range(grid):
            for col in range(grid):
                if not mask[row][col]:
                    pixels[col, row] = (0, 0, 0, 0)
    
    # Skaluj do rozmiaru eksportu
    export_size = EXPORT_SIZE_BY_GRID.get(grid, 512)
    if export_size != grid:
        img = img.resize((export_size, export_size), Image.NEAREST)
    
    # Zapisz obraz
    output_path.parent.mkdir(parents=True, exist_ok=True)
    img.save(output_path, "PNG")
    
    # Zapisz metadane
    metadata = {
        "grid_size": grid,
        "export_size": export_size,
        "entry_side": options.entry_side,
        "exit_side": options.exit_side,
        "railway_type": options.railway_type,
        "seed": options.seed,
        "junctions": valid_junctions,
        "is_straight": is_straight,
    }
    
    metadata_path = output_path.with_suffix(".json")
    with open(metadata_path, "w", encoding="utf-8") as f:
        json.dump(metadata, f, indent=2, ensure_ascii=False)
    
    return RailwayResult(
        image_path=output_path,
        metadata_path=metadata_path,
        metadata=metadata,
    )


# ============================================================================
# GENEROWANIE PRZYKŁADÓW
# ============================================================================

def generate_examples(output_dir: Path) -> List[Path]:
    """Generuje zestaw przykładowych torów."""
    output_dir.mkdir(parents=True, exist_ok=True)
    generated = []
    
    examples = [
        # PROSTE TORY
        ("tor_01_jednotorowy_pionowy.png", {
            "entry_side": "top", "exit_side": "bottom",
            "railway_type": "jednotorowy", "junctions": []
        }),
        ("tor_02_jednotorowy_ukosny.png", {
            "entry_side": "top_left", "exit_side": "bottom_right",
            "railway_type": "jednotorowy", "junctions": []
        }),
        ("tor_03_dwutorowy_pionowy.png", {
            "entry_side": "top", "exit_side": "bottom",
            "railway_type": "dwutorowy", "junctions": []
        }),
        ("tor_04_dwutorowy_ukosny.png", {
            "entry_side": "top_right", "exit_side": "bottom_left",
            "railway_type": "dwutorowy", "junctions": []
        }),
        
        # ZAKRĘTY (łuki)
        ("tor_05_zakret_lagodny.png", {
            "entry_side": "top", "exit_side": "bottom_right",
            "railway_type": "jednotorowy", "junctions": []
        }),
        ("tor_06_zakret_ostry.png", {
            "entry_side": "top", "exit_side": "top_right",
            "railway_type": "jednotorowy", "junctions": []
        }),
        ("tor_07_zakret_dwutorowy.png", {
            "entry_side": "bottom", "exit_side": "top_left",
            "railway_type": "dwutorowy", "junctions": []
        }),
        
        # ROZJAZDY (dojazdy łagodne)
        ("rozjazd_08_prawy.png", {
            "entry_side": "top", "exit_side": "bottom",
            "railway_type": "jednotorowy", 
            "junctions": ["bottom_right"]  # Dojazd z prawej
        }),
        ("rozjazd_09_lewy.png", {
            "entry_side": "top", "exit_side": "bottom",
            "railway_type": "jednotorowy",
            "junctions": ["bottom_left"]  # Dojazd z lewej
        }),
        ("rozjazd_10_podwojny.png", {
            "entry_side": "top", "exit_side": "bottom",
            "railway_type": "jednotorowy",
            "junctions": ["bottom_right", "bottom_left"]  # Dwa dojazdy
        }),
        ("rozjazd_11_dwutorowy_z_dojazdem.png", {
            "entry_side": "top", "exit_side": "bottom",
            "railway_type": "dwutorowy",
            "junctions": ["top_right"]
        }),
        ("rozjazd_12_z_ukosnego.png", {
            "entry_side": "top_left", "exit_side": "bottom_right",
            "railway_type": "jednotorowy",
            "junctions": ["top"]  # Dojazd z góry
        }),
        
        # ZŁOŻONE KONFIGURACJE
        ("tor_13_trojkat.png", {
            "entry_side": "top", "exit_side": "bottom_left",
            "railway_type": "jednotorowy",
            "junctions": ["bottom_right"]
        }),
        ("tor_14_widelki.png", {
            "entry_side": "bottom", "exit_side": "top_right",
            "railway_type": "jednotorowy",
            "junctions": ["top_left"]
        }),
        ("tor_15_stacja.png", {
            "entry_side": "top", "exit_side": "bottom",
            "railway_type": "dwutorowy",
            "junctions": ["top_left", "bottom_right"]
        }),
    ]
    
    for i, (filename, params) in enumerate(examples):
        opts = RailwayOptions(
            grid_size=64,
            background=None,
            seed=42 + i,
            **params
        )
        result = generate_railway(opts, output_dir / filename)
        generated.append(result.image_path)
        print(f"✓ {filename}")
    
    return generated


# ============================================================================
# CLI
# ============================================================================

if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="Generator torów kolejowych dla heksów")
    parser.add_argument("--examples", action="store_true", help="Generuj przykłady")
    parser.add_argument("--grid", type=int, default=64, help="Rozmiar siatki")
    parser.add_argument("--entry", default="top", choices=HEX_SIDES, help="Strona wejścia")
    parser.add_argument("--exit", default="bottom", choices=HEX_SIDES, help="Strona wyjścia")
    parser.add_argument("--type", default="jednotorowy", 
                        choices=["jednotorowy", "dwutorowy"], help="Typ toru")
    parser.add_argument("--seed", type=int, default=42, help="Ziarno losowości")
    parser.add_argument("--output", type=str, default="railway_test.png", help="Ścieżka wyjściowa")
    parser.add_argument("--junctions", type=str, nargs="*", default=[], 
                        help="Dodatkowe dojazdy (boki heksa)")
    
    args = parser.parse_args()
    
    if args.examples:
        examples_dir = Path(__file__).parent / "railway_examples"
        generated = generate_examples(examples_dir)
        print(f"\n✅ Wygenerowano {len(generated)} przykładów w: {examples_dir}")
    else:
        opts = RailwayOptions(
            grid_size=args.grid,
            background=None,
            entry_side=args.entry,
            exit_side=args.exit,
            railway_type=args.type,
            seed=args.seed,
            junctions=args.junctions or [],
        )
        result = generate_railway(opts, Path(args.output))
        print(f"Wygenerowano: {result.image_path}")
