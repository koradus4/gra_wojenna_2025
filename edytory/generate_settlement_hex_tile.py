#!/usr/bin/env python3
"""
Generator tekstur heksów z miejscowościami (wioski, miasteczka, miasta).

Hierarchia wielkości:
- WIOSKA: 1 heks (2-4 budynki)
- MAŁA MIEJSCOWOŚĆ: 2-3 heksy (5-10 budynków)
- MIASTO: 5+ heksów (15+ budynków)

Automatycznie wykrywa infrastrukturę sąsiadów (drogi, koleje, rzeki)
i generuje wewnętrzne ulice łączące się z siecią.
"""

from __future__ import annotations

import json
import math
import random
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, List, Optional, Sequence, Set, Tuple, Any

from PIL import Image, ImageDraw

# Katalogi
ASSETS_ROOT = Path(__file__).parent.parent / "assets"
SETTLEMENT_ASSETS_DIR = ASSETS_ROOT / "terrain" / "presets" / "user_assets" / "settlement"

# Rozmiary eksportu
EXPORT_SIZE_BY_GRID = {64: 512, 128: 1024}
RESAMPLE_NEAREST = Image.Resampling.NEAREST

# Kolory dróg wewnętrznych (dopasowane do generatora dróg)
ROAD_COLOR_DIRT = (150, 130, 100, 255)  # Gruntowa
ROAD_COLOR_COBBLE = (120, 115, 110, 255)  # Brukowana

# Hierarchia wielkości
SETTLEMENT_SIZE_THRESHOLDS = {
    "village": (1, 1),      # 1 heks = wioska
    "town": (2, 4),         # 2-4 heksy = miasteczko
    "city": (5, 100),       # 5+ heksów = miasto
}

# Konfiguracja budynków według wielkości miejscowości
BUILDING_POOLS = {
    "village": {
        "dom_1": 0.6,
        "shop_1": 0.4,
    },
    "town": {
        "dom_1": 0.4,
        "shop_1": 0.2,
        "szkola_1": 0.15,
        "kamienica_miejska1": 0.15,
        "kamieniac_miejska2": 0.1,
    },
    "city": {
        "ratusz_1": 0.05,       # Tylko 1 w mieście
        "dworzec_1": 0.05,      # Tylko jeśli jest kolej
        "kamienica_miejska1": 0.2,
        "kamieniac_miejska2": 0.15,
        "kamieniaca_miejska3": 0.15,
        "kamienica_czarny_dach1": 0.1,
        "kamienica_miejska4": 0.1,
        "szkola_1": 0.1,
        "shop_1": 0.05,
        "dom_1": 0.05,
    },
}

# Konfiguracja gęstości budynków
DENSITY_CONFIG = {
    "village": {"min_buildings": 2, "max_buildings": 4, "attempts_multiplier": 3.0},
    "town": {"min_buildings": 5, "max_buildings": 10, "attempts_multiplier": 2.5},
    "city": {"min_buildings": 15, "max_buildings": 30, "attempts_multiplier": 2.0},
}


@dataclass
class SettlementOptions:
    """Opcje generowania miejscowości."""
    hex_ids: List[str]
    grid_size: int
    seed: Optional[int]
    neighbor_info: Dict[str, Dict[str, Any]]  # hex_id -> {sides: {side: type}}
    background_textures: Dict[str, Optional[Path]]


@dataclass
class SettlementResult:
    """Wynik generowania miejscowości."""
    output_path: Path
    settlement_type: str
    building_count: int
    buildings_placed: List[Dict[str, Any]]


def _determine_settlement_type(hex_count: int) -> str:
    """Określa typ miejscowości na podstawie liczby heksów."""
    for stype, (min_h, max_h) in SETTLEMENT_SIZE_THRESHOLDS.items():
        if min_h <= hex_count <= max_h:
            return stype
    return "city"


def _build_hex_mask(grid: int) -> List[List[bool]]:
    """Buduje maskę heksa (pointy-top)."""
    mask = [[False] * grid for _ in range(grid)]
    cx, cy = grid / 2.0, grid / 2.0
    s = grid / 2.0
    
    vertices = [
        (cx - s, cy),
        (cx - s/2, cy - (math.sqrt(3)/2)*s),
        (cx + s/2, cy - (math.sqrt(3)/2)*s),
        (cx + s, cy),
        (cx + s/2, cy + (math.sqrt(3)/2)*s),
        (cx - s/2, cy + (math.sqrt(3)/2)*s),
    ]
    
    for row in range(grid):
        for col in range(grid):
            if _point_in_polygon(col + 0.5, row + 0.5, vertices):
                mask[row][col] = True
    
    return mask


def _point_in_polygon(x: float, y: float, poly: List[Tuple[float, float]]) -> bool:
    """Sprawdza czy punkt leży w wielokącie."""
    n = len(poly)
    inside = False
    j = n - 1
    for i in range(n):
        xi, yi = poly[i]
        xj, yj = poly[j]
        if ((yi > y) != (yj > y)) and (x < (xj - xi) * (y - yi) / (yj - yi) + xi):
            inside = not inside
        j = i
    return inside


def _axial_to_pixel(q: int, r: int, grid: int) -> Tuple[float, float]:
    """Konwersja współrzędnych axial na pixel (środek heksu)."""
    x = grid * (3.0/2.0 * q)
    y = grid * (math.sqrt(3)/2.0 * q + math.sqrt(3) * r)
    return x, y


def _build_cluster_layout(hex_ids: Sequence[str], grid: int) -> Tuple[Dict[str, Tuple[float, float]], Tuple[int, int]]:
    """Buduje układ klastra heksów."""
    centers = {}
    all_q, all_r = [], []
    
    for hex_id in hex_ids:
        q, r = map(int, hex_id.split(','))
        all_q.append(q)
        all_r.append(r)
    
    min_q, max_q = min(all_q), max(all_q)
    min_r, max_r = min(all_r), max(all_r)
    
    for hex_id in hex_ids:
        q, r = map(int, hex_id.split(','))
        px, py = _axial_to_pixel(q - min_q, r - min_r, grid)
        centers[hex_id] = (px + grid/2, py + grid/2)
    
    width = int(_axial_to_pixel(max_q - min_q + 1, 0, grid)[0] + grid)
    height = int(_axial_to_pixel(0, max_r - min_r + 1, grid)[1] + grid)
    
    return centers, (width, height)


def _build_cluster_mask(centers: Dict[str, Tuple[float, float]], size: Tuple[int, int], grid: int) -> Image.Image:
    """Buduje maskę binarna dla całego klastra."""
    mask_img = Image.new("L", size, 0)
    
    half = grid / 2.0
    s = half
    
    for cx, cy in centers.values():
        vertices = [
            (cx - s, cy),
            (cx - s/2, cy - (math.sqrt(3)/2)*s),
            (cx + s/2, cy - (math.sqrt(3)/2)*s),
            (cx + s, cy),
            (cx + s/2, cy + (math.sqrt(3)/2)*s),
            (cx - s/2, cy + (math.sqrt(3)/2)*s),
        ]
        
        draw = ImageDraw.Draw(mask_img)
        draw.polygon(vertices, fill=255)
    
    return mask_img


def _load_building_asset(json_path: Path, grid: int) -> Tuple[Image.Image, Tuple[float, float], Dict]:
    """Ładuje asset budynku."""
    with open(json_path, 'r', encoding='utf-8') as f:
        meta = json.load(f)
    
    img_path = SETTLEMENT_ASSETS_DIR / Path(meta['image']).name
    if not img_path.exists():
        raise FileNotFoundError(f"Nie znaleziono obrazu: {img_path}")
    
    img = Image.open(img_path).convert("RGBA")
    
    hotspot = (meta['hotspot']['col'], meta['hotspot']['row'])
    
    return img, hotspot, meta


def _find_available_building_assets() -> Dict[str, Path]:
    """Znajduje dostępne assety budynków."""
    assets = {}
    
    for json_file in SETTLEMENT_ASSETS_DIR.glob("*.json"):
        name = json_file.stem
        assets[name] = json_file
    
    return assets


def _draw_internal_roads(
    base_img: Image.Image,
    centers: Dict[str, Tuple[float, float]],
    neighbor_info: Dict[str, Dict[str, Any]],
    grid: int,
    settlement_type: str,
    rng: random.Random
) -> List[Tuple[Tuple[float, float], Tuple[float, float]]]:
    """Rysuje wewnętrzne ulice miasta łączące się z sąsiadami.
    
    Zwraca: lista segmentów dróg (start, end)
    """
    draw = ImageDraw.Draw(base_img)
    
    # Kolor i szerokość zależne od typu miejscowości
    if settlement_type == "village":
        road_color = ROAD_COLOR_DIRT
        road_width = 3
    elif settlement_type == "town":
        road_color = ROAD_COLOR_DIRT
        road_width = 4
    else:  # city
        road_color = ROAD_COLOR_COBBLE
        road_width = 5
    
    road_segments = []
    
    # Dla każdego heksu sprawdź które krawędzie mają drogi
    for hex_id, (cx, cy) in centers.items():
        sides_with_roads = neighbor_info.get(hex_id, {}).get("sides_with_roads", [])
        
        # Oblicz punkty na krawędziach heksu
        s = grid / 2.0
        edge_points = {
            "top": (cx, cy - s * math.sqrt(3) / 2),
            "top_right": (cx + s * 0.75, cy - s * math.sqrt(3) / 4),
            "bottom_right": (cx + s * 0.75, cy + s * math.sqrt(3) / 4),
            "bottom": (cx, cy + s * math.sqrt(3) / 2),
            "bottom_left": (cx - s * 0.75, cy + s * math.sqrt(3) / 4),
            "top_left": (cx - s * 0.75, cy - s * math.sqrt(3) / 4),
        }
        
        # Połącz drogi przez środek heksu
        if len(sides_with_roads) >= 2:
            # Łącz pierwsze dwie drogi
            p1 = edge_points[sides_with_roads[0]]
            p2 = edge_points[sides_with_roads[1]]
            draw.line([p1, (cx, cy), p2], fill=road_color, width=road_width)
            road_segments.append((p1, p2))
            
            # Jeśli są więcej niż 2, dodaj więcej połączeń
            for i in range(2, len(sides_with_roads)):
                p = edge_points[sides_with_roads[i]]
                draw.line([(cx, cy), p], fill=road_color, width=road_width)
        elif len(sides_with_roads) == 1:
            # Prosta droga przez środek
            p1 = edge_points[sides_with_roads[0]]
            draw.line([p1, (cx, cy)], fill=road_color, width=road_width)
    
    return road_segments


def _composite_building(
    base: Image.Image,
    building_img: Image.Image,
    hotspot: Tuple[float, float],
    position: Tuple[float, float]
) -> None:
    """Nanosi budynek na obraz bazowy."""
    hx, hy = hotspot
    px, py = position
    
    offset_col = int(px - hx)
    offset_row = int(py - hy)
    
    base.paste(building_img, (offset_col, offset_row), building_img)


def generate_settlement_cluster(
    hex_ids: Sequence[str],
    *,
    grid_size: int,
    seed: Optional[int],
    neighbor_info: Dict[str, Dict[str, Any]],
    background_textures: Dict[str, Optional[Path]],
    output_paths: Dict[str, Path],
) -> Tuple[int, str, Dict[str, SettlementResult]]:
    """Generuje spójną miejscowość na klastrze heksów.
    
    Returns:
        (liczba budynków, typ miejscowości, mapowanie hex_id -> SettlementResult)
    """
    settlement_type = _determine_settlement_type(len(hex_ids))
    density_config = DENSITY_CONFIG[settlement_type]
    building_pool = BUILDING_POOLS[settlement_type]
    
    rng = random.Random(seed)
    
    # Znajdź dostępne assety
    available_assets = _find_available_building_assets()
    
    # Zbuduj layout klastra
    centers, size = _build_cluster_layout(hex_ids, grid_size)
    mask_img = _build_cluster_mask(centers, size, grid_size)
    
    # Utwórz obraz bazowy z tłem
    base_img = Image.new("RGBA", size, (0, 0, 0, 0))
    
    half = grid_size / 2.0
    for hex_id, (cx, cy) in centers.items():
        bg_path = background_textures.get(hex_id)
        if bg_path and bg_path.exists():
            try:
                bg = Image.open(bg_path).convert("RGBA")
                if bg.size != (grid_size, grid_size):
                    bg = bg.resize((grid_size, grid_size), RESAMPLE_NEAREST)
                
                left = int(round(cx - half))
                top = int(round(cy - half))
                base_img.alpha_composite(bg, (left, top))
            except Exception:
                pass
    
    # Narysuj wewnętrzne drogi
    road_segments = _draw_internal_roads(base_img, centers, neighbor_info, grid_size, settlement_type, rng)
    
    # Rozmieść budynki
    min_buildings = density_config["min_buildings"]
    max_buildings = density_config["max_buildings"]
    target_buildings = rng.randint(min_buildings, max_buildings)
    attempts = int(target_buildings * density_config["attempts_multiplier"])
    
    placed_buildings: List[Tuple[Tuple[float, float], Tuple[int, int]]] = []
    buildings_placed_info: List[Dict[str, Any]] = []
    
    # Specjalne budynki (1x na miasto)
    special_buildings = {"ratusz_1", "dworzec_1"}
    placed_special = set()
    
    for _ in range(attempts):
        if len(placed_buildings) >= target_buildings:
            break
        
        # Wybierz budynek według wag
        building_choices = []
        building_weights = []
        
        for building_name, weight in building_pool.items():
            # Pomiń specjalne budynki jeśli już umieszczone
            if building_name in special_buildings and building_name in placed_special:
                continue
            
            if building_name in available_assets:
                building_choices.append(building_name)
                building_weights.append(weight)
        
        if not building_choices:
            break
        
        building_name = rng.choices(building_choices, weights=building_weights)[0]
        building_json = available_assets[building_name]
        
        try:
            building_img, hotspot, meta = _load_building_asset(building_json, grid_size)
        except (FileNotFoundError, ValueError):
            continue
        
        # Losuj pozycję wzdłuż drogi lub w centrum heksu
        if road_segments and rng.random() < 0.7:
            # Pozycja przy drodze
            segment = rng.choice(road_segments)
            t = rng.uniform(0.2, 0.8)
            pos_x = segment[0][0] * (1 - t) + segment[1][0] * t
            pos_y = segment[0][1] * (1 - t) + segment[1][1] * t
            
            # Offset od drogi
            offset_dist = grid_size * rng.uniform(0.15, 0.3)
            angle = rng.uniform(0, 2 * math.pi)
            pos_x += offset_dist * math.cos(angle)
            pos_y += offset_dist * math.sin(angle)
        else:
            # Losowa pozycja w klastrze
            pos_x = rng.uniform(0, size[0])
            pos_y = rng.uniform(0, size[1])
        
        # Sprawdź czy w masce
        ix, iy = int(pos_x), int(pos_y)
        if ix < 0 or iy < 0 or ix >= mask_img.width or iy >= mask_img.height:
            continue
        if mask_img.getpixel((ix, iy)) == 0:
            continue
        
        # Sprawdź kolizje (prostsza logika niż w lesie)
        building_size = (building_img.width, building_img.height)
        min_distance = 15  # Minimalna odległość między budynkami
        
        collision = False
        for (bx, by), (bw, bh) in placed_buildings:
            dx = abs(pos_x - bx)
            dy = abs(pos_y - by)
            if dx < (building_size[0] + bw) / 2 + min_distance and dy < (building_size[1] + bh) / 2 + min_distance:
                collision = True
                break
        
        if collision:
            continue
        
        # Umieść budynek
        _composite_building(base_img, building_img, hotspot, (pos_x, pos_y))
        placed_buildings.append(((pos_x, pos_y), building_size))
        buildings_placed_info.append({
            "asset": building_name,
            "position": (pos_x, pos_y),
            "hotspot": hotspot,
            "size": building_size,
        })
        
        if building_name in special_buildings:
            placed_special.add(building_name)
    
    # Wyciągnij kafle per heks
    results: Dict[str, SettlementResult] = {}
    for hex_id, (cx, cy) in centers.items():
        left = int(round(cx - half))
        top = int(round(cy - half))
        tile = base_img.crop((left, top, left + grid_size, top + grid_size))
        
        output_path = output_paths.get(hex_id)
        if not output_path:
            continue
        
        output_path.parent.mkdir(parents=True, exist_ok=True)
        export_size = EXPORT_SIZE_BY_GRID.get(grid_size, grid_size * 8)
        output_img = tile.resize((export_size, export_size), RESAMPLE_NEAREST)
        output_img.save(output_path, "PNG")
        
        results[hex_id] = SettlementResult(
            output_path=output_path,
            settlement_type=settlement_type,
            building_count=len(placed_buildings),
            buildings_placed=buildings_placed_info,
        )
    
    return len(placed_buildings), settlement_type, results


if __name__ == "__main__":
    # Przykład użycia
    print("Generator miejscowości - użyj przez Hex Inspector lub Map Editor")
