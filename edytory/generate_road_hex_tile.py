"""Generator dróg dla heksów.

Generuje tekstury dróg przecinających heks - podobnie jak generator rzek,
ale z prostszą logiką (brak brzegów wodnych, gradient kolorów drogi).
"""

from __future__ import annotations

import json
import math
import random
from dataclasses import dataclass, replace
from pathlib import Path
from typing import Any, Dict, List, Optional, Sequence, Tuple

from PIL import Image, ImageDraw, ImageFilter


# ============================================================================
# STAŁE I KOLORY
# ============================================================================

EXPORT_SIZE_BY_GRID = {64: 512, 128: 1024}

# Kolory dróg
ROAD_COLOR_PRESETS: Dict[str, Dict[str, Tuple[int, int, int, int]]] = {
    "gruntowa": {
        "center": (139, 119, 85, 255),      # Ciemny brąz - środek
        "edge": (165, 145, 110, 255),       # Jaśniejszy brąz - brzeg
        "border": (110, 90, 60, 255),       # Krawędź
    },
    "brukowana": {
        "center": (128, 128, 128, 255),     # Szary - środek
        "edge": (160, 160, 160, 255),       # Jaśniejszy szary
        "border": (90, 90, 90, 255),        # Ciemna krawędź
    },
    "glowna": {
        "center": (180, 170, 150, 255),     # Jasny beż
        "edge": (200, 190, 170, 255),       # Kremowy
        "border": (140, 130, 110, 255),     # Ciemniejszy beż
    },
    "piaszczysta": {
        "center": (210, 190, 140, 255),     # Piaskowy
        "edge": (230, 215, 170, 255),       # Jasny piasek
        "border": (180, 160, 110, 255),     # Ciemny piasek
    },
    "asfaltowa": {
        "center": (60, 60, 60, 255),        # Ciemny asfalt
        "edge": (80, 80, 80, 255),          # Jaśniejszy asfalt
        "border": (40, 40, 40, 255),        # Czarna krawędź
        "shoulder": (120, 110, 90, 255),    # Brązowe pobocze
    },
    "dojazdowa": {
        "center": (100, 90, 70, 255),       # Brązowo-szary
        "edge": (130, 120, 100, 255),       # Jaśniejszy
        "border": (70, 60, 50, 255),        # Ciemny
    },
}

# Szerokości dróg (w komórkach siatki 64x64)
ROAD_WIDTH_PRESETS: Dict[str, float] = {
    "wąska": 2.5,       # Ścieżka/droga polna
    "średnia": 4.0,     # Typowa droga
    "szeroka": 6.0,     # Droga główna/trakt
    "bardzo_szeroka": 8.0,  # Autostrada/droga ekspresowa
}

# Mapowanie boków heksa na kąty (pointy-top)
HEX_SIDES = ("top", "top_right", "bottom_right", "bottom", "bottom_left", "top_left")

SIDE_ANGLES: Dict[str, float] = {
    "top": 270,           # góra
    "top_right": 330,     # góra-prawo
    "bottom_right": 30,   # dół-prawo
    "bottom": 90,         # dół
    "bottom_left": 150,   # dół-lewo
    "top_left": 210,      # góra-lewo
}

SIDE_OPPOSITE: Dict[str, str] = {
    "top": "bottom",
    "top_right": "bottom_left",
    "bottom_right": "top_left",
    "bottom": "top",
    "bottom_left": "top_right",
    "top_left": "bottom_right",
}


# ============================================================================
# DATACLASSES
# ============================================================================

@dataclass
class RoadOptions:
    """Opcje generowania drogi w heksie."""
    grid_size: int
    background: Path | None
    entry_side: str
    # exit_side=None oznacza drogę zakończoną w heksie (dead-end / dojazd).
    exit_side: str | None
    road_type: str = "gruntowa"  # gruntowa, brukowana, glowna, piaszczysta
    width: str = "średnia"       # wąska, średnia, szeroka
    noise_amplitude: float = 0.3  # Jak bardzo droga się wije (0-1)
    seed: int = 42
    # Opcjonalne skrzyżowanie - lista dodatkowych boków
    crossroads: List[str] | None = None
    # Opcjonalny cap na zakończeniu (np. budynek) jako preset JSON z assets/terrain/presets/user_assets/...
    endcap_preset: Path | None = None


@dataclass 
class RoadResult:
    """Wynik generowania drogi."""
    image_path: Path
    metadata_path: Path
    metadata: Dict[str, Any]


def _normalize_road_options(options: RoadOptions) -> RoadOptions:
    """Normalizuje opcje pod kątem realizmu i stabilności.

    To jest "twarda" warstwa semantyki: działa niezależnie od tego,
    czy caller to Hex Inspector, Map Editor czy skrypt.
    """
    if options.entry_side not in HEX_SIDES:
        raise ValueError(f"Nieznany entry_side: {options.entry_side}")

    exit_side = options.exit_side
    if exit_side is not None:
        if exit_side not in HEX_SIDES:
            raise ValueError(f"Nieznany exit_side: {exit_side}")
        if options.entry_side == exit_side:
            raise ValueError("entry_side i exit_side muszą być różne")

    road_type = options.road_type if options.road_type in ROAD_COLOR_PRESETS else "gruntowa"
    width_key = options.width if options.width in ROAD_WIDTH_PRESETS else "średnia"

    # Clamp (UI zwykle podaje 0-1, ale generator powinien być odporny).
    noise_amplitude = float(options.noise_amplitude)
    if noise_amplitude < 0.0:
        noise_amplitude = 0.0
    if noise_amplitude > 1.0:
        noise_amplitude = 1.0

    crossroads_in = list(options.crossroads) if options.crossroads else []
    crossroads_out: List[str] = []
    for side in crossroads_in:
        if side not in HEX_SIDES:
            continue
        if side in (options.entry_side, exit_side):
            continue
        if side not in crossroads_out:
            crossroads_out.append(side)
    crossroads = crossroads_out or None

    # Dead-end nie może mieć skrzyżowań.
    if exit_side is None:
        crossroads = None

    # Semantyka: 'bardzo_szeroka' tylko dla prostej bez skrzyżowań.
    is_straight = (exit_side is not None) and (SIDE_OPPOSITE.get(options.entry_side) == exit_side)
    is_junction = bool(crossroads)

    # Semantyka: 'piaszczysta' + 'bardzo_szeroka' wygląda jak plama.
    if road_type == "piaszczysta" and width_key == "bardzo_szeroka":
        width_key = "szeroka" if "szeroka" in ROAD_WIDTH_PRESETS else "średnia"

    if width_key == "bardzo_szeroka" and (is_junction or not is_straight):
        width_key = "szeroka" if "szeroka" in ROAD_WIDTH_PRESETS else "średnia"

    if (
        road_type == options.road_type
        and width_key == options.width
        and noise_amplitude == float(options.noise_amplitude)
        and crossroads == options.crossroads
        and exit_side is options.exit_side
    ):
        return options

    return replace(
        options,
        road_type=road_type,
        width=width_key,
        noise_amplitude=noise_amplitude,
        crossroads=crossroads,
        exit_side=exit_side,
    )


def _dead_end_point(entry_pt: Tuple[float, float], center: Tuple[float, float], grid: int) -> Tuple[float, float]:
    """Punkt zakończenia drogi wewnątrz heksa (dla exit_side=None)."""
    # Punkt pomiędzy krawędzią a środkiem, dość blisko środka, żeby było miejsce na cap.
    t = 0.45
    x = center[0] + (entry_pt[0] - center[0]) * t
    y = center[1] + (entry_pt[1] - center[1]) * t
    # Minimalny clamp do wnętrza siatki
    x = _clamp(x, 1.0, grid - 2.0)
    y = _clamp(y, 1.0, grid - 2.0)
    return (x, y)


def _find_assets_root(path: Path) -> Optional[Path]:
    for parent in path.resolve().parents:
        if parent.name.lower() == "assets":
            return parent
    return None


def _load_user_asset_canvas(meta_path: Path, target_grid: int) -> Tuple[Image.Image, Tuple[float, float]]:
    """Ładuje preset user_asset (JSON+PNG) i zwraca canvas RGBA (target_grid x target_grid) + hotspot (x,y)."""
    meta = json.loads(meta_path.read_text(encoding="utf-8"))
    source_grid = int(meta.get("grid_size", target_grid) or target_grid)

    assets_root = _find_assets_root(meta_path) or meta_path.parent
    rel_image = str(meta.get("image") or "").replace("\\\\", "/")
    if not rel_image:
        raise ValueError(f"Preset bez pola 'image': {meta_path}")
    image_path = (assets_root / rel_image).resolve() if not Path(rel_image).is_absolute() else Path(rel_image)
    if not image_path.exists():
        # fallback: obok json-a
        image_path = meta_path.with_suffix(".png")

    img = Image.open(image_path).convert("RGBA")

    origin = meta.get("origin") or {}
    size = meta.get("size") or {}
    hotspot = meta.get("hotspot") or {}

    try:
        origin_row = int(round(origin.get("row", 0)))
        origin_col = int(round(origin.get("col", 0)))
        size_rows = int(round(size.get("rows", img.height)))
        size_cols = int(round(size.get("cols", img.width)))
        use_origin = True
    except (TypeError, ValueError):
        origin_row = 0
        origin_col = 0
        size_rows = img.height
        size_cols = img.width
        use_origin = False

    size_rows = max(1, min(size_rows, source_grid))
    size_cols = max(1, min(size_cols, source_grid))

    if use_origin:
        source_canvas = Image.new("RGBA", (source_grid, source_grid), (0, 0, 0, 0))
        paste_x = max(0, min(source_grid - size_cols, origin_col))
        paste_y = max(0, min(source_grid - size_rows, origin_row))
        if (size_cols, size_rows) != img.size:
            img = img.resize((size_cols, size_rows), Image.NEAREST)
        source_canvas.paste(img, (paste_x, paste_y), img)
    else:
        source_canvas = img
        if source_canvas.size != (source_grid, source_grid):
            source_canvas = source_canvas.resize((source_grid, source_grid), Image.NEAREST)

    if source_grid != target_grid:
        source_canvas = source_canvas.resize((target_grid, target_grid), Image.NEAREST)

    hx = float(hotspot.get("col", target_grid / 2.0))
    hy = float(hotspot.get("row", target_grid / 2.0))
    if source_grid != target_grid:
        scale = target_grid / float(source_grid)
        hx *= scale
        hy *= scale
    return source_canvas, (hx, hy)


def _alpha_composite_with_offset(base: Image.Image, overlay: Image.Image, offset_x: int, offset_y: int) -> None:
    """Alpha-composite overlay na base z przesunięciem (offset w px)."""
    tmp = Image.new("RGBA", base.size, (0, 0, 0, 0))
    tmp.paste(overlay, (offset_x, offset_y), overlay)
    base.alpha_composite(tmp)


# ============================================================================
# FUNKCJE POMOCNICZE
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
        (cx - radius, cy),                              # lewa
        (cx - radius / 2.0, cy - (sqrt3 / 2.0) * radius),  # góra-lewa
        (cx + radius / 2.0, cy - (sqrt3 / 2.0) * radius),  # góra-prawa
        (cx + radius, cy),                              # prawa
        (cx + radius / 2.0, cy + (sqrt3 / 2.0) * radius),  # dół-prawa
        (cx - radius / 2.0, cy + (sqrt3 / 2.0) * radius),  # dół-lewa
    ]


def _side_to_edge_center(side: str, grid: int) -> Tuple[float, float]:
    """Zwraca środek krawędzi heksa dla danego boku."""
    vertices = _hex_vertices(grid)
    # Mapowanie boków na pary wierzchołków (pointy-top)
    side_to_vertices = {
        "top": (1, 2),           # góra
        "top_right": (2, 3),     # góra-prawo  
        "bottom_right": (3, 4),  # dół-prawo
        "bottom": (4, 5),        # dół
        "bottom_left": (5, 0),   # dół-lewo
        "top_left": (0, 1),      # góra-lewo
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
            # Sprawdź czy punkt jest wewnątrz heksa
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


def _generate_road_path(
    entry: Tuple[float, float],
    exit_pt: Tuple[float, float],
    center: Tuple[float, float],
    noise_amp: float,
    rng: random.Random,
    num_points: int = 12,
) -> List[Tuple[float, float]]:
    """Generuje ścieżkę drogi z lekkim szumem."""
    points = [entry]
    
    for i in range(1, num_points - 1):
        t = i / (num_points - 1)
        # Interpolacja liniowa
        x = entry[0] + (exit_pt[0] - entry[0]) * t
        y = entry[1] + (exit_pt[1] - entry[1]) * t
        
        # Dodaj szum prostopadły do kierunku
        dx = exit_pt[0] - entry[0]
        dy = exit_pt[1] - entry[1]
        length = math.sqrt(dx*dx + dy*dy)
        if length > 0:
            # Wektor prostopadły
            nx, ny = -dy / length, dx / length
            # Szum sinusoidalny + losowy
            wave = math.sin(t * math.pi * 2) * noise_amp * 3
            noise = (rng.random() - 0.5) * noise_amp * 2
            x += nx * (wave + noise)
            y += ny * (wave + noise)
        
        points.append((x, y))
    
    points.append(exit_pt)
    return points


def _smooth_path(points: List[Tuple[float, float]], iterations: int = 2) -> List[Tuple[float, float]]:
    """Wygładza ścieżkę metodą uśredniania."""
    if len(points) < 3:
        return points
    
    result = points[:]
    for _ in range(iterations):
        new_points = [result[0]]  # Zachowaj początek
        for i in range(1, len(result) - 1):
            x = (result[i-1][0] + result[i][0] * 2 + result[i+1][0]) / 4
            y = (result[i-1][1] + result[i][1] * 2 + result[i+1][1]) / 4
            new_points.append((x, y))
        new_points.append(result[-1])  # Zachowaj koniec
        result = new_points
    
    return result


def _lerp_color(
    c1: Tuple[int, int, int, int],
    c2: Tuple[int, int, int, int], 
    t: float
) -> Tuple[int, int, int, int]:
    """Interpolacja liniowa kolorów."""
    t = _clamp(t, 0.0, 1.0)
    return (
        int(c1[0] + (c2[0] - c1[0]) * t),
        int(c1[1] + (c2[1] - c1[1]) * t),
        int(c1[2] + (c2[2] - c1[2]) * t),
        int(c1[3] + (c2[3] - c1[3]) * t),
    )


# ============================================================================
# GŁÓWNA FUNKCJA GENEROWANIA
# ============================================================================

def generate_road(options: RoadOptions, output_path: Path) -> RoadResult:
    """Generuje teksturę drogi w heksie."""

    options = _normalize_road_options(options)
    
    grid = options.grid_size
    rng = random.Random(options.seed)
    
    # Pobierz kolory i szerokość
    colors = ROAD_COLOR_PRESETS.get(options.road_type, ROAD_COLOR_PRESETS["gruntowa"])
    width = ROAD_WIDTH_PRESETS.get(options.width, ROAD_WIDTH_PRESETS["średnia"])
    
    # Oblicz punkty wejścia/wyjścia
    entry_pt = _side_to_edge_center(options.entry_side, grid)
    center = _hex_center(grid)

    if options.exit_side is None:
        exit_pt = _dead_end_point(entry_pt, center, grid)
    else:
        exit_pt = _side_to_edge_center(options.exit_side, grid)
    
    # Generuj główną ścieżkę
    main_path = _generate_road_path(
        entry_pt, exit_pt, center, 
        options.noise_amplitude, rng
    )
    main_path = _smooth_path(main_path)
    
    # Dodatkowe ścieżki dla skrzyżowań
    crossroad_paths = []
    if options.crossroads:
        for cross_side in options.crossroads:
            if cross_side in (options.entry_side, options.exit_side):
                continue
            cross_pt = _side_to_edge_center(cross_side, grid)
            
            # Odnogi wychodzą Z CENTRUM do krawędzi - zawsze się spotkają w środku
            # Daje to czyste skrzyżowanie w centrum heksa
            cross_path = _generate_road_path(
                center, cross_pt, center,
                options.noise_amplitude * 0.3, rng, num_points=6
            )
            cross_path = _smooth_path(cross_path, iterations=1)
            crossroad_paths.append(cross_path)
    
    # === RENDEROWANIE ===
    
    # Wczytaj tło lub utwórz przezroczyste
    if options.background and options.background.exists():
        img = Image.open(options.background).convert("RGBA")
        if img.size != (grid, grid):
            img = img.resize((grid, grid), Image.NEAREST)
    else:
        img = Image.new("RGBA", (grid, grid), (0, 0, 0, 0))
    
    draw = ImageDraw.Draw(img)
    
    # Maska heksa
    mask = _build_hex_mask(grid)
    
    # Rysuj drogi WARSTWOWO - najpierw wszystkie pobocza, potem wszystkie bordery itd.
    # To zapewnia płynne łączenie na skrzyżowaniach bez widocznych krawędzi
    all_paths = [main_path] + crossroad_paths
    
    # Specjalna obsługa dla drogi asfaltowej z poboczem
    has_shoulder = "shoulder" in colors
    
    # WARSTWA 0: Wszystkie pobocza (najszersza)
    if has_shoulder:
        shoulder_width = width + 3.0
        for path in all_paths:
            for i in range(len(path) - 1):
                x1, y1 = path[i]
                x2, y2 = path[i + 1]
                draw.line([(x1, y1), (x2, y2)], fill=colors["shoulder"], width=int(shoulder_width))
    
    # WARSTWA 1: Wszystkie krawędzie
    border_width = width + 1.5
    for path in all_paths:
        for i in range(len(path) - 1):
            x1, y1 = path[i]
            x2, y2 = path[i + 1]
            draw.line([(x1, y1), (x2, y2)], fill=colors["border"], width=int(border_width))
    
    # WARSTWA 2: Wszystkie zewnętrzne
    edge_width = width + 0.5
    for path in all_paths:
        for i in range(len(path) - 1):
            x1, y1 = path[i]
            x2, y2 = path[i + 1]
            draw.line([(x1, y1), (x2, y2)], fill=colors["edge"], width=int(edge_width))
    
    # WARSTWA 3: Wszystkie środki (najwęższa)
    center_width = width - 0.5
    for path in all_paths:
        for i in range(len(path) - 1):
            x1, y1 = path[i]
            x2, y2 = path[i + 1]
            draw.line([(x1, y1), (x2, y2)], fill=colors["center"], width=int(max(1, center_width)))
    
    # Dodaj teksturę szumu do drogi
    _add_road_texture(img, all_paths, width, rng, colors)
    
    # Przytnij do maski heksa
    pixels = img.load()
    for row in range(grid):
        for col in range(grid):
            if not mask[row][col]:
                pixels[col, row] = (0, 0, 0, 0)

    # Opcjonalny cap na dead-end (np. dom). Rysujemy po drogach i przed skalowaniem.
    if options.exit_side is None and options.endcap_preset and Path(options.endcap_preset).exists():
        try:
            overlay, hotspot = _load_user_asset_canvas(Path(options.endcap_preset), grid)
            # Dopasuj hotspot do końca drogi.
            target_x, target_y = exit_pt
            off_x = int(round(target_x - hotspot[0]))
            off_y = int(round(target_y - hotspot[1]))
            _alpha_composite_with_offset(img, overlay, off_x, off_y)

            # Ponownie przytnij maską (żeby cap nie wystawał poza heks).
            pixels = img.load()
            for row in range(grid):
                for col in range(grid):
                    if not mask[row][col]:
                        pixels[col, row] = (0, 0, 0, 0)
        except Exception:
            # Cap jest opcjonalny – w razie problemu nie blokuj generowania drogi.
            pass
    
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
        "dead_end": bool(options.exit_side is None),
        "road_type": options.road_type,
        "width": options.width,
        "noise_amplitude": options.noise_amplitude,
        "seed": options.seed,
        "crossroads": options.crossroads or [],
        "path_points": len(main_path),
    }
    
    metadata_path = output_path.with_suffix(".json")
    with open(metadata_path, "w", encoding="utf-8") as f:
        json.dump(metadata, f, indent=2, ensure_ascii=False)
    
    return RoadResult(
        image_path=output_path,
        metadata_path=metadata_path,
        metadata=metadata,
    )


def _add_road_texture(
    img: Image.Image,
    paths: List[List[Tuple[float, float]]],
    width: float,
    rng: random.Random,
    colors: Dict[str, Tuple[int, int, int, int]],
) -> None:
    """Dodaje teksturę szumu do drogi (kamyki, koleiny itp.)."""
    pixels = img.load()
    grid = img.size[0]
    
    # Zbierz wszystkie piksele drogi
    road_pixels = set()
    for path in paths:
        for pt in path:
            x, y = int(pt[0]), int(pt[1])
            for dx in range(-int(width), int(width) + 1):
                for dy in range(-int(width), int(width) + 1):
                    nx, ny = x + dx, y + dy
                    if 0 <= nx < grid and 0 <= ny < grid:
                        dist = math.sqrt(dx*dx + dy*dy)
                        if dist <= width:
                            road_pixels.add((nx, ny))
    
    # Dodaj losowy szum
    for x, y in road_pixels:
        if rng.random() < 0.15:  # 15% szans na zmianę
            current = pixels[x, y]
            if current[3] > 0:  # Nie przezroczysty
                # Losowo rozjaśnij lub przyciemnij
                delta = rng.randint(-20, 20)
                new_color = (
                    _clamp(current[0] + delta, 0, 255),
                    _clamp(current[1] + delta, 0, 255),
                    _clamp(current[2] + delta, 0, 255),
                    current[3],
                )
                pixels[x, y] = tuple(int(c) for c in new_color)


# ============================================================================
# CLI
# ============================================================================

if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="Generator dróg dla heksów")
    parser.add_argument("--grid", type=int, default=64, help="Rozmiar siatki")
    parser.add_argument("--entry", default="top", choices=HEX_SIDES, help="Strona wejścia")
    parser.add_argument("--exit", default="bottom", choices=HEX_SIDES, help="Strona wyjścia")
    parser.add_argument("--type", default="gruntowa", choices=list(ROAD_COLOR_PRESETS.keys()), help="Typ drogi")
    parser.add_argument("--width", default="średnia", choices=list(ROAD_WIDTH_PRESETS.keys()), help="Szerokość")
    parser.add_argument("--noise", type=float, default=0.3, help="Amplituda szumu (0-1)")
    parser.add_argument("--seed", type=int, default=42, help="Ziarno losowości")
    parser.add_argument("--output", type=str, default="road_test.png", help="Ścieżka wyjściowa")
    parser.add_argument("--background", type=str, default=None, help="Ścieżka do tła")
    parser.add_argument("--crossroads", type=str, nargs="*", default=None, help="Dodatkowe boki dla skrzyżowania")
    
    args = parser.parse_args()
    
    options = RoadOptions(
        grid_size=args.grid,
        background=Path(args.background) if args.background else None,
        entry_side=args.entry,
        exit_side=args.exit,
        road_type=args.type,
        width=args.width,
        noise_amplitude=args.noise,
        seed=args.seed,
        crossroads=args.crossroads,
    )
    
    result = generate_road(options, Path(args.output))
    print(f"Wygenerowano: {result.image_path}")
    print(f"Metadane: {result.metadata_path}")
