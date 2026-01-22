"""Generator lasu dla heksów.

Nanosi drzewa na istniejące tekstury heksów z kontrolowaną gęstością.
Wykorzystuje istniejące assety drzew (JSON+PNG) w oryginalnych rozmiarach.
Drzewa są rozmieszczone losowo ale nie wystają poza granicę heksa.
"""

from __future__ import annotations

import json
import math
import random
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, List, Optional, Sequence, Tuple

from PIL import Image

try:
    from PIL.Image import Resampling
    RESAMPLE_NEAREST = Resampling.NEAREST
except Exception:
    RESAMPLE_NEAREST = getattr(Image, "NEAREST", 0)


# ============================================================================
# STAŁE
# ============================================================================

ASSET_ROOT = Path(__file__).parent.parent / "assets"
FOREST_ASSET_DIR = ASSET_ROOT / "terrain" / "presets" / "user_assets" / "forest"
HEX_TEXTURE_DIR = ASSET_ROOT / "terrain" / "hex_painted"
FOREST_OUTPUT_DIR = HEX_TEXTURE_DIR / "forest_tool"
FOREST_OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

EXPORT_SIZE_BY_GRID = {64: 512, 128: 1024}

# Gęstość lasu - liczba prób umieszczenia drzew
DENSITY_PRESETS = {
    "rzadki": {"min_trees": 1, "max_trees": 2, "attempts_multiplier": 15.0, "min_distance": 1.0},
    "średni": {"min_trees": 2, "max_trees": 4, "attempts_multiplier": 25.0, "min_distance": 0.5},
    "gęsty": {"min_trees": 3, "max_trees": 6, "attempts_multiplier": 40.0, "min_distance": 0.2},
}


# ============================================================================
# DATACLASSES
# ============================================================================

@dataclass
class ForestOptions:
    """Opcje generowania lasu."""
    grid_size: int = 64
    density: str = "średni"  # rzadki, średni, gęsty
    seed: Optional[int] = None
    background_texture: Optional[Path] = None
    mix_types: bool = True  # Czy mieszać iglaste i liściaste
    tree_type: str = "mixed"  # mixed, iglaste, lisciaste


@dataclass
class ForestResult:
    """Wynik generowania lasu."""
    output_path: Path
    tree_count: int
    trees_placed: List[Dict[str, Any]]


# ============================================================================
# FUNKCJE POMOCNICZE
# ============================================================================

def _find_available_tree_assets() -> Dict[str, List[Path]]:
    """Znajduje wszystkie dostępne assety drzew z kompletnymi plikami."""
    assets = {"iglaste": [], "lisciaste": [], "all": []}
    
    if not FOREST_ASSET_DIR.exists():
        return assets
    
    for json_path in FOREST_ASSET_DIR.glob("drzewo_*.json"):
        png_path = json_path.with_suffix(".png")
        if png_path.exists():
            assets["all"].append(json_path)
            if "iglaste" in json_path.stem:
                assets["iglaste"].append(json_path)
            elif "lisciaste" in json_path.stem:
                assets["lisciaste"].append(json_path)
    
    return assets


def _load_tree_asset(json_path: Path, target_grid: int) -> Tuple[Image.Image, Tuple[float, float], Dict[str, Any]]:
    """Ładuje asset drzewa (JSON+PNG) i zwraca obraz RGBA + hotspot + metadane."""
    meta = json.loads(json_path.read_text(encoding="utf-8"))
    source_grid = int(meta.get("grid_size", target_grid) or target_grid)
    
    # Ścieżka do obrazu
    rel_image = str(meta.get("image", "")).replace("\\\\", "/")
    if not rel_image:
        raise ValueError(f"Brak ścieżki obrazu w {json_path}")
    
    # Szukaj względem assets root
    image_path = ASSET_ROOT / rel_image
    if not image_path.exists():
        # Fallback - szukaj obok JSON
        image_path = json_path.parent / Path(rel_image).name
    
    if not image_path.exists():
        raise FileNotFoundError(f"Nie znaleziono obrazu: {rel_image}")
    
    img = Image.open(image_path).convert("RGBA")
    
    # Pobierz rozmiar i origin
    origin = meta.get("origin", {})
    size = meta.get("size", {})
    hotspot = meta.get("hotspot", {})
    
    try:
        origin_row = int(origin.get("row", 0))
        origin_col = int(origin.get("col", 0))
        size_rows = int(size.get("rows", source_grid))
        size_cols = int(size.get("cols", source_grid))
        use_origin = origin_row > 0 or origin_col > 0
    except (TypeError, ValueError):
        origin_row = origin_col = 0
        size_rows = size_cols = source_grid
        use_origin = False
    
    size_rows = max(1, min(size_rows, source_grid))
    size_cols = max(1, min(size_cols, source_grid))
    
    # Hotspot z metadanych (w układzie source_grid)
    hx = float(hotspot.get("col", source_grid / 2.0))
    hy = float(hotspot.get("row", source_grid / 2.0))
    
    # Wytnij fragment jeśli użyto origin I jeśli PNG nie jest już przycięty
    # (niektóre assety są zapisane już w postaci przyciętej, wtedy cropowanie się pomija)
    if use_origin and (img.width != size_cols or img.height != size_rows):
        crop_box = (
            origin_col, origin_row,
            origin_col + size_cols, origin_row + size_rows
        )
        img = img.crop(crop_box)
        # Dostosuj hotspot - był w układzie source, teraz w układzie wyciętego fragmentu
        hx -= origin_col
        hy -= origin_row
    elif use_origin and img.width == size_cols and img.height == size_rows:
        # PNG już przycięty - tylko hotspot adjustment
        hx -= origin_col
        hy -= origin_row
    else:
        # Bez origin - hotspot pozostaje bez zmian
        pass
    
    # Skaluj jeśli potrzeba
    if source_grid != target_grid:
        scale = target_grid / source_grid
        new_w = int(img.width * scale)
        new_h = int(img.height * scale)
        img = img.resize((new_w, new_h), RESAMPLE_NEAREST)
        # Skaluj hotspot
        hx *= scale
        hy *= scale
    
    # Jeśli nie było origin, ale rozmiar jest inny niż source_grid, hotspot może być poza obrazem
    # Użyj bezpiecznego hotspo środka obrazu jeśli hotspot jest poza zakresem
    if hx < 0 or hx > img.width or hy < 0 or hy > img.height:
        hx = img.width / 2.0
        hy = img.height / 2.0
    
    return img, (hx, hy), meta


def _hex_center(grid: int) -> Tuple[float, float]:
    """Środek heksa."""
    coord = grid / 2.0
    return (coord, coord)


def _hex_vertices(grid: int) -> List[Tuple[float, float]]:
    """Wierzchołki heksa (pointy-top)."""
    cx, cy = _hex_center(grid)
    radius = grid / 2.0 - 0.5
    sqrt3 = math.sqrt(3.0)
    
    return [
        (cx - radius, cy),
        (cx - radius / 2.0, cy - (sqrt3 / 2.0) * radius),
        (cx + radius / 2.0, cy - (sqrt3 / 2.0) * radius),
        (cx + radius, cy),
        (cx + radius / 2.0, cy + (sqrt3 / 2.0) * radius),
        (cx - radius / 2.0, cy + (sqrt3 / 2.0) * radius),
    ]


def _point_in_polygon(x: float, y: float, polygon: Sequence[Tuple[float, float]]) -> bool:
    """Sprawdza czy punkt jest wewnątrz wielokąta."""
    inside = False
    j = len(polygon) - 1
    for i, (ix, iy) in enumerate(polygon):
        jx, jy = polygon[j]
        if ((iy > y) != (jy > y)) and (x < (jx - ix) * (y - iy) / (jy - iy) + ix):
            inside = not inside
        j = i
    return inside


def _build_hex_mask(grid: int) -> List[List[bool]]:
    """Tworzy maskę heksa."""
    polygon = _hex_vertices(grid)
    mask = [[False for _ in range(grid)] for _ in range(grid)]
    
    for row in range(grid):
        for col in range(grid):
            if _point_in_polygon(col + 0.5, row + 0.5, polygon):
                mask[row][col] = True
    
    return mask


def _calculate_tree_bounds(
    tree_img: Image.Image,
    hotspot: Tuple[float, float],
    position: Tuple[float, float],
    grid: int
) -> Tuple[int, int, int, int]:
    """Oblicza granice drzewa (min_col, min_row, max_col, max_row)."""
    hx, hy = hotspot
    px, py = position
    
    # Offset - gdzie zaczynamy rysować
    offset_col = int(px - hx)
    offset_row = int(py - hy)
    
    min_col = offset_col
    min_row = offset_row
    max_col = offset_col + tree_img.width
    max_row = offset_row + tree_img.height
    
    return (min_col, min_row, max_col, max_row)


def _check_tree_fits_in_hex(
    tree_img: Image.Image,
    hotspot: Tuple[float, float],
    position: Tuple[float, float],
    mask: Sequence[Sequence[bool]],
    grid: int,
    margin: float = 0.0
) -> bool:
    """Sprawdza czy drzewo mieści się w heksie (nie wystaje poza maskę)."""
    min_col, min_row, max_col, max_row = _calculate_tree_bounds(tree_img, hotspot, position, grid)
    
    # KLUCZOWE: Sprawdź czy offset jest w granicach (inaczej paste() nic nie zrobi!)
    if min_col < 0 or min_row < 0:
        return False
    if max_col > grid or max_row > grid:
        return False
    
    # Sprawdź czy wszystkie nieprzezroczyste piksele są w masce
    tree_pixels = tree_img.load()
    
    for tree_row in range(tree_img.height):
        for tree_col in range(tree_img.width):
            # Pozycja w siatce globalnej
            global_col = min_col + tree_col
            global_row = min_row + tree_row
            
            # Sprawdź alpha
            pixel = tree_pixels[tree_col, tree_row]
            if len(pixel) >= 4 and pixel[3] > 10:  # Prawie nieprzezroczysty
                # Czy w masce?
                if not mask[global_row][global_col]:
                    return False
    
    return True


def _check_tree_overlap(
    position: Tuple[float, float],
    tree_size: Tuple[int, int],
    placed_trees: List[Tuple[Tuple[float, float], Tuple[int, int]]],
    min_distance: float
) -> bool:
    """Sprawdza czy drzewo nie nachodzi na inne drzewa."""
    px, py = position
    tw, th = tree_size
    
    for other_pos, other_size in placed_trees:
        ox, oy = other_pos
        ow, oh = other_size
        
        # Prostokątne granice
        dx = abs(px - ox)
        dy = abs(py - oy)
        
        # Minimalna odległość między środkami
        if dx < (tw + ow) / 2.0 + min_distance and dy < (th + oh) / 2.0 + min_distance:
            return True
    
    return False


def _load_background(grid: int, mask: Sequence[Sequence[bool]], texture_path: Optional[Path]) -> Image.Image:
    """Ładuje teksturę tła lub tworzy przezroczystą."""
    if texture_path and texture_path.exists():
        bg = Image.open(texture_path).convert("RGBA")
        if bg.size != (grid, grid):
            bg = bg.resize((grid, grid), RESAMPLE_NEAREST)
        return bg
    else:
        # Przezroczyste tło
        return Image.new("RGBA", (grid, grid), (0, 0, 0, 0))


def _composite_tree(
    base: Image.Image,
    tree_img: Image.Image,
    hotspot: Tuple[float, float],
    position: Tuple[float, float]
) -> None:
    """Nanosi drzewo na obraz bazowy."""
    hx, hy = hotspot
    px, py = position
    
    offset_col = int(px - hx)
    offset_row = int(py - hy)
    
    base.paste(tree_img, (offset_col, offset_row), tree_img)


# ============================================================================
# GŁÓWNA FUNKCJA GENEROWANIA
# ============================================================================

def generate_forest(options: ForestOptions, output_path: Path) -> ForestResult:
    """Generuje las na heksie.
    
    Args:
        options: Opcje generowania lasu
        output_path: Ścieżka zapisu tekstury
        
    Returns:
        ForestResult z informacjami o wygenerowanym lesie
    """
    grid = options.grid_size
    density_key = options.density if options.density in DENSITY_PRESETS else "średni"
    density_config = DENSITY_PRESETS[density_key]
    
    rng = random.Random(options.seed)
    
    # Znajdź dostępne assety
    tree_assets = _find_available_tree_assets()
    
    # Wybierz pulę drzew według typu
    if options.tree_type == "iglaste":
        tree_pool = tree_assets["iglaste"]
    elif options.tree_type == "lisciaste":
        tree_pool = tree_assets["lisciaste"]
    else:  # mixed
        tree_pool = tree_assets["all"]
    
    if not tree_pool:
        raise ValueError("Brak dostępnych assetów drzew!")
    
    # Utwórz maskę heksa
    mask = _build_hex_mask(grid)
    
    # Załaduj tło
    base_img = _load_background(grid, mask, options.background_texture)
    
    # Parametry rozmieszczenia
    min_trees = density_config["min_trees"]
    max_trees = density_config["max_trees"]
    attempts = int(max_trees * density_config["attempts_multiplier"])
    min_distance = density_config["min_distance"]
    
    target_trees = rng.randint(min_trees, max_trees)
    
    placed_trees: List[Tuple[Tuple[float, float], Tuple[int, int]]] = []
    trees_placed_info: List[Dict[str, Any]] = []
    
    # Próbuj umieścić drzewa
    for attempt in range(attempts):
        if len(placed_trees) >= target_trees:
            break
        
        # Losuj pozycję w heksie (większy promień, mniej marginesu)
        cx, cy = _hex_center(grid)
        radius = grid / 2.0 - 0.5  # Minimalny margines
        
        # Losuj kąt i promień
        angle = rng.uniform(0, 2 * math.pi)
        r = rng.uniform(0, radius) * math.sqrt(rng.random())  # Dystrybucja równomierna
        
        pos_x = cx + r * math.cos(angle)
        pos_y = cy + r * math.sin(angle)
        
        # Losuj drzewo
        tree_json = rng.choice(tree_pool)
        
        try:
            tree_img, hotspot, meta = _load_tree_asset(tree_json, grid)
        except (FileNotFoundError, ValueError) as e:
            # Pomin asset ktory nie dziala
            continue
        
        # Sprawdz czy miesci sie w heksie
        if not _check_tree_fits_in_hex(tree_img, hotspot, (pos_x, pos_y), mask, grid):
            continue
        
        # Sprawdz czy nie nachodzi na inne
        tree_size = (tree_img.width, tree_img.height)
        
        if _check_tree_overlap((pos_x, pos_y), tree_size, placed_trees, min_distance):
            continue
        
        # Umiesc drzewo
        _composite_tree(base_img, tree_img, hotspot, (pos_x, pos_y))
        placed_trees.append(((pos_x, pos_y), tree_size))
        
        trees_placed_info.append({
            "asset": tree_json.stem,
            "position": (pos_x, pos_y),
            "hotspot": hotspot,
            "size": tree_size,
        })
    
    # Eksportuj do większego rozmiaru
    export_size = EXPORT_SIZE_BY_GRID.get(grid, grid * 8)
    output_img = base_img.resize((export_size, export_size), RESAMPLE_NEAREST)
    
    # Zapisz
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_img.save(output_path, "PNG")
    
    return ForestResult(
        output_path=output_path,
        tree_count=len(placed_trees),
        trees_placed=trees_placed_info,
    )


# ============================================================================
# CLI - PRZYKŁADOWE UŻYCIE
# ============================================================================

def main():
    """Przykład użycia generatora."""
    import argparse
    
    parser = argparse.ArgumentParser(description="Generator lasu dla heksów")
    parser.add_argument("--density", choices=["rzadki", "średni", "gęsty"], default="średni")
    parser.add_argument("--tree-type", choices=["mixed", "iglaste", "lisciaste"], default="mixed")
    parser.add_argument("--seed", type=int, default=None)
    parser.add_argument("--grid", type=int, default=64)
    parser.add_argument("--background", type=str, default=None)
    parser.add_argument("--output", type=str, default=None)
    
    args = parser.parse_args()
    
    background_path = Path(args.background) if args.background else None
    
    if args.output:
        output_path = Path(args.output)
    else:
        # Automatyczna nazwa
        import time
        timestamp = int(time.time())
        output_path = FOREST_OUTPUT_DIR / f"forest_{args.density}_{timestamp}.png"
    
    options = ForestOptions(
        grid_size=args.grid,
        density=args.density,
        seed=args.seed,
        background_texture=background_path,
        tree_type=args.tree_type,
    )
    
    result = generate_forest(options, output_path)
    
    print(f"[OK] Las wygenerowany: {output_path}")
    print(f"  Drzew umieszczono: {result.tree_count}")
    print(f"  Szczegoly:")
    for tree_info in result.trees_placed:
        print(f"    - {tree_info['asset']} @ ({tree_info['position'][0]:.1f}, {tree_info['position'][1]:.1f})")


if __name__ == "__main__":
    main()
