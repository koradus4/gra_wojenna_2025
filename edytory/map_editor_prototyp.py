from __future__ import annotations

import tkinter as tk
from tkinter import messagebox, filedialog, simpledialog, ttk, colorchooser
import json
import math
import os
import random
import re
import shutil
from collections import deque
from datetime import datetime
from pathlib import Path
from typing import TYPE_CHECKING

from PIL import Image, ImageTk, ImageFont, ImageDraw

try:
    from generate_river_hex_tile import (
        DEFAULT_BANK_OFFSET,
        DEFAULT_BANK_VARIATION,
        DEFAULT_BANK_COLOR,
        MAX_TRIBUTARY_JOIN,
        MIN_TRIBUTARY_JOIN,
        RiverCenterlineOptions,
        TributaryOptions,
        generate_centerline,
        render_centerline,
    )
except ImportError:  # pragma: no cover - w trybie edytora brak generatora
    RiverCenterlineOptions = None
    TributaryOptions = None
    generate_centerline = None
    render_centerline = None
    MIN_TRIBUTARY_JOIN = 0.2
    MAX_TRIBUTARY_JOIN = 0.8
    DEFAULT_BANK_OFFSET = 1.5
    DEFAULT_BANK_VARIATION = 0.35
    DEFAULT_BANK_COLOR = (214, 192, 138, 255)

# Import generatora dróg
try:
    from generate_road_hex_tile import (
        RoadOptions,
        RoadResult,
        generate_road,
        ROAD_COLOR_PRESETS,
        ROAD_WIDTH_PRESETS,
        HEX_SIDES as ROAD_HEX_SIDES,
    )
except ImportError:
    RoadOptions = None
    RoadResult = None
    generate_road = None
    ROAD_COLOR_PRESETS = {}
    ROAD_WIDTH_PRESETS = {}
    ROAD_HEX_SIDES = ()

# Import generatora torów kolejowych
try:
    from generate_railway_hex_tile import (
        RailwayOptions,
        RailwayResult,
        generate_railway,
        HEX_SIDES as RAILWAY_HEX_SIDES,
        SIDE_OPPOSITE,
    )
except ImportError:
    RailwayOptions = None
    RailwayResult = None
    generate_railway = None
    RAILWAY_HEX_SIDES = ()
    SIDE_OPPOSITE = {}

# Import generatora jezior
try:
    from generate_lake_hex_tile import (
        LakeOptions,
        render_lake,
        HEX_SIDES as LAKE_HEX_SIDES,
    )
except ImportError:
    LakeOptions = None
    render_lake = None
    LAKE_HEX_SIDES = ()
    
try:
    from hex_feature_semantics import normalize_railway_options, normalize_road_options
except Exception:
    normalize_road_options = None
    normalize_railway_options = None

# Folder „assets” obok map_editor_prototyp.py
ASSET_ROOT = Path(__file__).parent.parent / "assets"

def fix_image_path(relative_path):
    """Naprawia ścieżki obrazów, usuwając podwójne assets/"""
    if isinstance(relative_path, str):
        # Usuń assets/ z początku, jeśli występuje
        if relative_path.startswith("assets/"):
            relative_path = relative_path[7:]  # usuń "assets/"
        elif relative_path.startswith("assets\\"):
            relative_path = relative_path[8:]  # usuń "assets\"
    
    # Tworzymy pełną ścieżkę
    full_path = ASSET_ROOT / relative_path
    return full_path
ASSET_ROOT.mkdir(exist_ok=True)

# Dodajemy folder data na potrzeby silnika i testów
DATA_ROOT = Path(__file__).parent.parent / "data"
DATA_ROOT.mkdir(exist_ok=True)

DEFAULT_MAP_FILE = str(ASSET_ROOT / "mapa_globalna.jpg")
DEFAULT_MAP_DIR = ASSET_ROOT
# Zmieniamy domyślną ścieżkę zapisu danych mapy na data/map_data.json
DATA_FILENAME_WORKING = DATA_ROOT / "map_data.json"
SOLID_BACKGROUND_COLOR = (48, 64, 40)
HEX_TEXTURE_GRID_OPTIONS = (64,)
DEFAULT_HEX_TEXTURE_GRID_SIZE = HEX_TEXTURE_GRID_OPTIONS[0]
HEX_TEXTURE_EXPORT_SIZES = {
    64: 512,
    128: 1024,
}
LARGE_RIVER_WIDTH_MULTIPLIER = 2.5
NEIGHBOR_PREVIEW_SCALE = 1.0
CONTEXT_CANVAS_SCALE = 1.8
EDGE_BAND_CELLS_DEFAULT = 6
EDGE_BAND_CELLS_MIN = 2
EDGE_BAND_CELLS_MAX = 12
EDGE_BLEND_DEFAULT_STRENGTH = 65
EDGE_BLEND_PROFILE_DEFAULT = "smooth"
EDGE_BLEED_DEPTH_DEFAULT = 1
EDGE_BLEND_PROFILES = {
    "linear": {"label": "Liniowy", "exponent": 1.0},
    "smooth": {"label": "Łagodny", "exponent": 1.6},
    "strong": {"label": "Silny", "exponent": 2.4},
}
EDGE_BLEND_PROFILE_LABEL_TO_KEY = {meta["label"]: key for key, meta in EDGE_BLEND_PROFILES.items()}
BRUSH_RADIUS_MIN = 0
BRUSH_RADIUS_MAX = 4
BRUSH_RADIUS_DEFAULT = 1

HEX_TEXTURE_DIR = ASSET_ROOT / "terrain" / "hex_painted"
HEX_TEXTURE_DIR.mkdir(parents=True, exist_ok=True)

RIVER_OUTPUT_DIR = HEX_TEXTURE_DIR / "river_tool"
RIVER_OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

ROAD_OUTPUT_DIR = HEX_TEXTURE_DIR / "road_tool"
ROAD_OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

LAKE_OUTPUT_DIR = HEX_TEXTURE_DIR / "lake_tool"
LAKE_OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

# Konfiguracja dróg
ROAD_TYPE_LABELS = {
    "gruntowa": "Droga gruntowa",
    "brukowana": "Droga brukowana",
    "glowna": "Droga główna (trakt)",
    "piaszczysta": "Droga piaszczysta",
    "asfaltowa": "Droga asfaltowa (z poboczem)",
    "dojazdowa": "Droga dojazdowa",
}
ROAD_TYPE_LABEL_TO_KEY = {label: key for key, label in ROAD_TYPE_LABELS.items()}

ROAD_WIDTH_LABELS = {
    "wąska": "Wąska (ścieżka)",
    "średnia": "Średnia (typowa)",
    "szeroka": "Szeroka (trakt)",
    "bardzo_szeroka": "Bardzo szeroka (ekspresowa)",
}
ROAD_WIDTH_LABEL_TO_KEY = {label: key for key, label in ROAD_WIDTH_LABELS.items()}

RIVER_SHAPE_LABELS = {
    "auto": "Automatycznie",
    "straight": "Odcinek prosty",
    "curve": "Łagodne zakole",
    "turn": "Ostry zakręt",
}
RIVER_SHAPE_LABEL_TO_KEY = {label: key for key, label in RIVER_SHAPE_LABELS.items()}

TRIBUTARY_SHAPE_LABELS = {
    "straight": "Dopływ prosty",
    "curve": "Dopływ zakole",
    "turn": "Dopływ ostry zakręt",
}
TRIBUTARY_SHAPE_LABEL_TO_KEY = {label: key for key, label in TRIBUTARY_SHAPE_LABELS.items()}

TRIBUTARY_DIRECTION_LABELS = {
    "auto": "Losowo",
    "left": "Lewy łuk",
    "right": "Prawy łuk",
}
TRIBUTARY_DIRECTION_LABEL_TO_KEY = {label: key for key, label in TRIBUTARY_DIRECTION_LABELS.items()}


CUSTOM_PROFILE_LABEL = "Niestandardowo (zachowaj)"

# ============================================================================
# UPROSZCZONE PRESETY RZEK - jeden wybór ustawia wszystko
# ============================================================================
RIVER_QUICK_PRESETS = {
    "Strumień (prosty)": {
        "description": "Wąski, prosty strumień z stabilnymi brzegami",
        "size": "Strumień",
        "curvature": "Prosta", 
        "bank": "Stabilny brzeg",
    },
    "Strumień (kręty)": {
        "description": "Wąski strumień z łagodnymi zakrętami",
        "size": "Strumień",
        "curvature": "Łagodna",
        "bank": "Stabilny brzeg",
    },
    "Mała rzeka (łagodna)": {
        "description": "Typowa mała rzeka z delikatnymi meandrami",
        "size": "Mała rzeka",
        "curvature": "Łagodna",
        "bank": "Stabilny brzeg",
    },
    "Mała rzeka (meandrująca)": {
        "description": "Mała rzeka z wyraźnymi zakrętami",
        "size": "Mała rzeka",
        "curvature": "Meandrująca",
        "bank": "Erozyjny brzeg",
    },
    "Duża rzeka (spokojna)": {
        "description": "Szeroka rzeka z łagodnymi łukami",
        "size": "Duża rzeka",
        "curvature": "Łagodna",
        "bank": "Piaszczysty brzeg",
    },
    "Duża rzeka (dynamiczna)": {
        "description": "Szeroka rzeka z silnymi meandrami",
        "size": "Duża rzeka",
        "curvature": "Dynamiczna",
        "bank": "Błotnisty brzeg",
    },
}

RIVER_SIZE_OPTIONS = {
    CUSTOM_PROFILE_LABEL: None,
    "Duża rzeka": {
        "grid_size": 64,
        "bank_offset": DEFAULT_BANK_OFFSET * 1.55,
        "bank_variation": DEFAULT_BANK_VARIATION * 1.2,
    },
    "Mała rzeka": {
        "grid_size": 64,
        "bank_offset": DEFAULT_BANK_OFFSET * 1.05,
        "bank_variation": DEFAULT_BANK_VARIATION,
    },
    "Strumień": {
        "grid_size": 64,
        "bank_offset": DEFAULT_BANK_OFFSET * 0.78,
        "bank_variation": DEFAULT_BANK_VARIATION * 0.85,
    },
}

RIVER_CURVATURE_OPTIONS = {
    CUSTOM_PROFILE_LABEL: None,
    "Prosta": {
        "shape_preference": "straight",
        "shape_strength": 0.25,
        "noise_amplitude": 0.05,
        "noise_frequency": 1.2,
    },
    "Łagodna": {
        "shape_preference": "curve",
        "shape_strength": 0.45,
        "noise_amplitude": 0.18,
        "noise_frequency": 1.8,
    },
    "Meandrująca": {
        "shape_preference": "curve",
        "shape_strength": 0.7,
        "noise_amplitude": 0.3,
        "noise_frequency": 2.4,
    },
    "Dynamiczna": {
        "shape_preference": "turn",
        "shape_strength": 0.85,
        "noise_amplitude": 0.45,
        "noise_frequency": 3.0,
    },
}

RIVER_BANK_OPTIONS = {
    CUSTOM_PROFILE_LABEL: None,
    "Stabilny brzeg": {
        "offset_multiplier": 1.0,
        "variation_multiplier": 0.85,
        "variation_add": 0.0,
    },
    "Erozyjny brzeg": {
        "offset_multiplier": 1.15,
        "variation_multiplier": 1.25,
        "variation_add": 0.08,
    },
    "Piaszczysty brzeg": {
        "offset_multiplier": 1.25,
        "variation_multiplier": 0.95,
        "variation_add": -0.02,
    },
    "Błotnisty brzeg": {
        "offset_multiplier": 0.9,
        "variation_multiplier": 1.35,
        "variation_add": 0.1,
    },
}

RIVER_TEMPLATE_SEGMENTS = {
    "Prosty": [(1, 0), (1, 0), (1, 0)],
    "Łuk w lewo": [(1, 0), (0, 1), (-1, 1)],
    "Łuk w prawo": [(1, 0), (1, -1), (0, -1)],
    "Meander": [(1, 0), (0, 1), (-1, 1), (-1, 0)],
    "Zygzak": [(1, 0), (1, -1), (1, 0), (1, -1)],
}

TRIBUTARY_SIZE_OPTIONS = {
    CUSTOM_PROFILE_LABEL: None,
    "Mały dopływ": {
        "bank_offset_scale": 0.65,
        "variation_scale": 0.9,
    },
    "Średni dopływ": {
        "bank_offset_scale": 0.8,
        "variation_scale": 1.0,
    },
    "Duży dopływ": {
        "bank_offset_scale": 1.0,
        "variation_scale": 1.15,
    },
}

TRIBUTARY_CHARACTER_OPTIONS = {
    CUSTOM_PROFILE_LABEL: None,
    "Łagodny dopływ": {
        "shape": "curve",
        "shape_strength": 0.55,
        "noise_amplitude": 0.18,
        "noise_frequency": 2.2,
        "shape_direction_mode": "auto",
    },
    "Ostry dopływ": {
        "shape": "turn",
        "shape_strength": 0.85,
        "noise_amplitude": 0.32,
        "noise_frequency": 2.9,
        "shape_direction_mode": "auto",
    },
    "Esowaty dopływ": {
        "shape": "curve",
        "shape_strength": 0.75,
        "noise_amplitude": 0.28,
        "noise_frequency": 2.6,
        "shape_direction_mode": "auto",
    },
}

TRIBUTARY_ENTRY_OPTIONS = {
    "z prawego górnego": {"entry_side": "top_right", "default_join": 0.35},
    "z górnego": {"entry_side": "top", "default_join": 0.25},
    "z lewego górnego": {"entry_side": "top_left", "default_join": 0.45},
    "z prawego dolnego": {"entry_side": "bottom_right", "default_join": 0.65},
    "z dolnego": {"entry_side": "bottom", "default_join": 0.75},
    "z lewego dolnego": {"entry_side": "bottom_left", "default_join": 0.55},
}

TRIBUTARY_ENTRY_SIDE_TO_LABEL = {config["entry_side"]: label for label, config in TRIBUTARY_ENTRY_OPTIONS.items()}

SQRT_3 = math.sqrt(3.0)

AXIAL_DIRECTION_TO_SIDE = {
    (1, 0): "bottom_right",
    (1, -1): "top_right",
    (0, -1): "top",
    (-1, 0): "top_left",
    (-1, 1): "bottom_left",
    (0, 1): "bottom",
}

SIDE_TO_AXIAL_DIRECTION = {value: key for key, value in AXIAL_DIRECTION_TO_SIDE.items()}

SIDE_OPPOSITE = {
    "top": "bottom",
    "top_right": "bottom_left",
    "bottom_right": "top_left",
    "bottom": "top",
    "bottom_left": "top_right",
    "top_left": "bottom_right",
}

HEX_SIDE_LABELS_PL = {
    "top": "górna",
    "top_right": "górna prawa",
    "bottom_right": "dolna prawa",
    "bottom": "dolna",
    "bottom_left": "dolna lewa",
    "top_left": "górna lewa",
}

HEX_SIDE_DISPLAY_LABELS = {
    key: value.title() if isinstance(value, str) else str(value)
    for key, value in HEX_SIDE_LABELS_PL.items()
}
HEX_SIDE_DISPLAY_TO_KEY = {label: key for key, label in HEX_SIDE_DISPLAY_LABELS.items()}

AXIAL_DIRECTION_TO_CARTESIAN = {
    (1, 0): (1.5, SQRT_3 / 2.0),
    (1, -1): (1.5, -SQRT_3 / 2.0),
    (0, -1): (0.0, -SQRT_3),
    (-1, 0): (-1.5, -SQRT_3 / 2.0),
    (-1, 1): (-1.5, SQRT_3 / 2.0),
    (0, 1): (0.0, SQRT_3),
}

CUSTOM_ASSET_ROOT = ASSET_ROOT / "terrain" / "presets" / "user_assets"
CUSTOM_ASSET_ROOT.mkdir(parents=True, exist_ok=True)
USER_ASSET_THUMB_SIZE = 128

USER_ASSET_CATEGORY_DEFS = {
    "forest": {"label": "Lasy", "icon": "🌲"},
    "settlement": {"label": "Budynki i dworce", "icon": "🏘️"},
    "bridge": {"label": "Mosty", "icon": "🌉"},
    "mountain": {"label": "Góry / pagórki / skały", "icon": "⛰️"},
    "lake": {"label": "Jeziora", "icon": "🌊"},
    "swamp": {"label": "Bagna", "icon": "🪵"},
}


def sanitize_asset_slug(name: str) -> str:
    slug = name.strip().lower()
    slug = re.sub(r"[^a-z0-9_-]+", "_", slug)
    slug = re.sub(r"_+", "_", slug).strip("_")
    return slug or "asset"

def to_rel(path: str) -> str:
    """Zwraca ścieżkę assets/... względem katalogu projektu."""
    try:
        return str(Path(path).relative_to(ASSET_ROOT))
    except ValueError:
        return str(path)   # gdy ktoś wybierze plik spoza assets/

# ----------------------------
# Konfiguracja rodzajów terenu
# ----------------------------
TERRAIN_TYPES = {
    "teren_płaski": {"move_mod": 0, "defense_mod": 0},
    "mała rzeka": {"move_mod": 2, "defense_mod": 1},
    "duża rzeka": {"move_mod": 5, "defense_mod": -1},  # przekraczalna, koszt ruchu 6
    "las": {"move_mod": 2, "defense_mod": 2},
    "bagno": {"move_mod": 3, "defense_mod": 1},
    "mała miejscowość": {"move_mod": 1, "defense_mod": 2},
    "miasto": {"move_mod": 2, "defense_mod": 2},
    "most": {"move_mod": 0, "defense_mod": -1}
}

# Kolory poglądowe dla podglądu sąsiednich heksów, używane gdy brak dedykowanej tekstury.
TERRAIN_PREVIEW_COLORS = {
    "teren_płaski": "#91a86b",
    "mała rzeka": "#3fa5d6",
    "duża rzeka": "#2b7aa6",
    "las": "#3f6d3a",
    "bagno": "#62795c",
    "mała miejscowość": "#b88b5a",
    "miasto": "#8a7c74",
    "most": "#d1b27c",
}


def clamp_channel(value: int) -> int:
    return max(0, min(255, value))


def hex_to_rgb(color: str) -> tuple[int, int, int]:
    stripped = color.lstrip("#")
    if len(stripped) != 6:
        raise ValueError(f"Niepoprawny kolor HEX: {color}")
    return int(stripped[0:2], 16), int(stripped[2:4], 16), int(stripped[4:6], 16)


def rgb_to_hex(rgb: tuple[int, int, int]) -> str:
    r, g, b = rgb
    return f"#{r:02x}{g:02x}{b:02x}"


def adjust_rgb(rgb: tuple[int, int, int], delta: tuple[int, int, int]) -> tuple[int, int, int]:
    return tuple(clamp_channel(channel + shift) for channel, shift in zip(rgb, delta))


def blend_rgb(rgb_a: tuple[int, int, int], rgb_b: tuple[int, int, int], factor: float) -> tuple[int, int, int]:
    mix = max(0.0, min(1.0, factor))
    return (
        clamp_channel(int(rgb_a[0] * (1 - mix) + rgb_b[0] * mix)),
        clamp_channel(int(rgb_a[1] * (1 - mix) + rgb_b[1] * mix)),
        clamp_channel(int(rgb_a[2] * (1 - mix) + rgb_b[2] * mix)),
    )


def mix_hex_colors(color_a: str | None, color_b: str | None, factor: float) -> str | None:
    blend = max(0.0, min(1.0, factor))
    if color_a is None and color_b is None:
        return None
    if color_a is None:
        return color_b
    if color_b is None:
        return color_a
    rgb_a = hex_to_rgb(color_a)
    rgb_b = hex_to_rgb(color_b)
    return rgb_to_hex(blend_rgb(rgb_a, rgb_b, blend))


FLAT_TERRAIN_TEXTURE_PRESETS = [
    {
        "key": "none",
        "name": "Brak tekstury",
        "description": "Czyści dodatkową teksturę i pozostawia domyślny wygląd terenu płaskiego.",
        "type": "clear",
    },
    {
        "key": "city_marker",
        "name": "Znacznik miasta",
        "description": "Wzór orientacyjny do oznaczania heksów miast.",
        "type": "builtin",
        "seed": 20251019,
        "base_color": "#6f9151",
        "noise": 18,
        "accent_color": "#4c6d39",
        "accent_chance": 0.14,
        "highlight_color": "#9fbe6d",
        "highlight_chance": 0.09,
        "pattern": "noise",
    },
    {
        "key": "grass_dense",
        "name": "Trawa gęsta",
        "description": "Gęste, ciemniejsze kępki trawy z delikatnie losową fakturą.",
        "type": "builtin",
        "seed": 101,
        "base_color": "#6f9151",
        "noise": 16,
        "accent_color": "#4f7038",
        "accent_chance": 0.08,
        "highlight_color": "#96bf6c",
        "highlight_chance": 0.04,
        "pattern": "noise",
    },
    {
        "key": "grass_dry",
        "name": "Trawa sucha",
        "description": "Jaśniejsza, wysuszona trawa z jaśniejszymi przebłyskami.",
        "type": "builtin",
        "seed": 305,
        "base_color": "#9bad6c",
        "noise": 12,
        "accent_color": "#c9d892",
        "accent_chance": 0.06,
        "highlight_color": "#f0f3c2",
        "highlight_chance": 0.03,
        "pattern": "noise",
    },
    {
        "key": "grass_fields",
        "name": "Łany pól",
        "description": "Regularne pasy pól uprawnych układające się w łany.",
        "type": "builtin",
        "seed": 712,
        "base_color": "#8aa45c",
        "secondary_color": "#b8cc7b",
        "band_width": 7,
        "band_strength": 0.55,
        "noise": 8,
        "pattern": "stripes",
    },
    {
        "key": "grass_muddy_mix",
        "name": "Mokry teren",
        "description": "Mieszanka zieleni z błotnistymi plamami po opadach.",
        "type": "builtin",
        "seed": 512,
        "base_color": "#6e7b4a",
        "secondary_color": "#4f3b2b",
        "patch_size": 8,
        "patch_jitter": 0.25,
        "noise": 10,
        "pattern": "patches",
    },
    {
        "key": "grass_sandy_mix",
        "name": "Piaskowo-trawiasty",
        "description": "Przesuszone fragmenty piasku wymieszane z zielenią.",
        "type": "builtin",
        "seed": 914,
        "base_color": "#bca66d",
        "secondary_color": "#8aa15b",
        "patch_size": 6,
        "patch_jitter": 0.35,
        "noise": 9,
        "pattern": "patches",
        "accent_color": "#d5c89c",
        "accent_chance": 0.05,
    },
]

FLAT_TERRAIN_PRESET_LOOKUP = {preset["key"]: preset for preset in FLAT_TERRAIN_TEXTURE_PRESETS}

# mapowanie państw → kolor mgiełki
SPAWN_OVERLAY = {
    "Polska": "#ffcccc;#ffffff",   # białe od góry, czerwone na dole
    "Niemcy": "#ccccff"    # jasnoniebieska
}

def zapisz_dane_hex(hex_data, filename=DATA_FILENAME_WORKING):
    'Zapisuje dane terenu do pliku JSON (roboczy plik).'
    directory = os.path.dirname(filename)
    if directory and not os.path.exists(directory):
        try:
            os.makedirs(directory)
        except Exception as e:
            print(f"Nie można utworzyć katalogu {directory}: {e}")
            # Jeśli nie można utworzyć katalogu, zapisz w katalogu skryptu
            filename = os.path.join(os.path.dirname(os.path.abspath(__file__)), os.path.basename(filename))
    with open(filename, "w", encoding="utf-8") as f:
        json.dump(hex_data, f, indent=2, ensure_ascii=False)

def wczytaj_dane_hex(filename=DATA_FILENAME_WORKING):
    'Wczytuje dane terenu z pliku JSON.'
    try:
        with open(filename, "r", encoding="utf-8") as f:
            return json.load(f)
    except FileNotFoundError:
        return {}

# ----------------------------
# Konfiguracja mapy
# ----------------------------
CONFIG = {
    'map_settings': {
        'map_image_path': r"C:\\ścieżka\\do\\tła\\mapa.jpg",  # Pełna ścieżka do obrazu tła mapy
        'hex_size': 30,
        'grid_cols': 56,   # liczba kolumn heksów
        'grid_rows': 40    # liczba wierszy heksów
    }
}

def point_in_polygon(x, y, poly):
    'Sprawdza, czy punkt (x,y) leży wewnątrz wielokąta poly.'
    num = len(poly)
    j = num - 1
    c = False
    for i in range(num):
        if ((poly[i][1] > y) != (poly[j][1] > y)) and \
           (x < (poly[j][0] - poly[i][0]) * (y - poly[i][1]) / (poly[j][1] - poly[i][1] + 1e-10) + poly[i][0]):
            c = not c
        j = i
    return c

def get_hex_vertices(center_x, center_y, s):
    # Zwraca wierzchołki heksu (POINTY‑TOP) w układzie axial.
    return [
        (center_x - s, center_y),
        (center_x - s/2, center_y - (math.sqrt(3)/2)*s),
        (center_x + s/2, center_y - (math.sqrt(3)/2)*s),
        (center_x + s, center_y),
        (center_x + s/2, center_y + (math.sqrt(3)/2)*s),
        (center_x - s/2, center_y + (math.sqrt(3)/2)*s)
    ]

def offset_to_axial(col: int, row: int) -> tuple[int, int]:
    # Pointy-top even-q offset: q = col, r = row - (col // 2)
    q = col
    r = row - (col // 2)
    return q, r

class MapEditor:
    def __init__(self, root, config):
        # --- Podstawy ---
        self.root = root
        self.root.configure(bg="darkolivegreen")
        self.config = config["map_settings"]
        self.map_image_path = self.get_last_modified_map()  # Automatyczne otwieranie ostatniej mapy
        if self.map_image_path:
            self.background_info = {
                "type": "image",
                "path": to_rel(str(self.map_image_path))
            }
        else:
            self.background_info = {
                "type": "solid",
                "color": list(SOLID_BACKGROUND_COLOR)
            }

        # --- Ustawienia heksów ---
        self.hex_size = self.config.get("hex_size", 30)
        self.hex_defaults = {"defense_mod": 0, "move_mod": 0}
        self.current_working_file = DATA_FILENAME_WORKING
        self.size_hard_limits = {"cols": (10, 160), "rows": (10, 120), "hex_size": (16, 64)}
        self.size_soft_limits = {"cols": 120, "rows": 90, "hex_size": 48}

        # --- Dane mapy ---
        self.hex_data: dict[str, dict] = {}
        self.key_points: dict[str, dict] = {}
        self.spawn_points: dict[str, list[str]] = {}

        # --- Selekcja ---
        self.selected_hex: str | None = None

        # --- Typy punktów kluczowych ---
        self.available_key_point_types = {
            "most": 50,
            "miasto": 100,
            "węzeł komunikacyjny": 75,
            "fortyfikacja": 150
        }

        # --- Nacje / żetony ---
        self.available_nations = ["Polska", "Niemcy"]
        self.hex_tokens: dict[str, str] = {}
        self.token_images: dict[str, ImageTk.PhotoImage] = {}
        self.hex_texture_cache: dict[tuple[str, int], ImageTk.PhotoImage] = {}
        self.flat_texture_preview_cache: dict[str, ImageTk.PhotoImage] = {}
        self.selected_flat_texture_preset: str | None = None
        self.flat_texture_window: tk.Toplevel | None = None

        # --- Nowy system palety żetonów ---
        self.token_index: list[dict] = []  # Lista wszystkich żetonów z index.json
        self.filtered_tokens: list[dict] = []  # Przefiltrowana lista żetonów
        self.selected_token = None  # Aktualnie wybrany żeton do wstawiania
        self.selected_token_button = None  # Przycisk zaznaczonego żetonu
        self.uniqueness_mode = True  # Tryb unikalności żetonów
        self.multi_placement_mode = False  # Tryb wielokrotnego wstawiania (Shift)
        
        # Filtry - tylko konkretny dowódca
        self.filter_commander = tk.StringVar(value="Wszystkie")
        self.commander_var = tk.StringVar(value="Wszyscy dowódcy")  # dla dropdown
        self.commander_filter = None  # aktualny filtr dowódcy
        
        # Auto-save debounce
        self._auto_save_after = None
        self.auto_save_enabled = True  # domyślnie włączony auto-save

        # --- Cache dla ghost (półprzezroczyste obrazy) ---
        self._ghost_cache: dict[tuple[Path, int], ImageTk.PhotoImage] = {}

        # --- Narzędzie rzek ---
        self.river_mode_active = False
        self.river_path: list[str] = []
        self.river_shape_var = tk.StringVar(value=RIVER_SHAPE_LABELS["auto"])
        self.river_strength_var = tk.DoubleVar(value=0.5)
        self.river_noise_var = tk.DoubleVar(value=0.0)
        self.river_frequency_var = tk.DoubleVar(value=2.0)
        self.river_seed_var = tk.IntVar(value=random.randint(0, 9999))
        self.river_bank_offset_var = tk.DoubleVar(value=DEFAULT_BANK_OFFSET)
        self.river_bank_variation_var = tk.DoubleVar(value=DEFAULT_BANK_VARIATION)
        self.river_grid_var = tk.StringVar(value=str(DEFAULT_HEX_TEXTURE_GRID_SIZE))
        self.river_grid_info_var = tk.StringVar(value="Siatka: 64 (512 px)")
        self.river_seed_label_var = tk.StringVar(value=f"Seed: {self.river_seed_var.get()}")
        self.river_size_profile_var = tk.StringVar(value="Mała rzeka")
        self.river_curvature_profile_var = tk.StringVar(value="Łagodna")
        self.river_bank_profile_var = tk.StringVar(value="Stabilny brzeg")
        self.river_large_mode_var = tk.BooleanVar(value=False)
        self._current_river_params: dict[str, float | str] = {
            "grid_size": DEFAULT_HEX_TEXTURE_GRID_SIZE,
            "shape_preference": "auto",
            "shape_strength": 0.5,
            "noise_amplitude": 0.0,
            "noise_frequency": 2.0,
            "base_bank_offset": DEFAULT_BANK_OFFSET,
            "base_bank_variation": DEFAULT_BANK_VARIATION,
            "bank_offset": DEFAULT_BANK_OFFSET,
            "bank_variation": DEFAULT_BANK_VARIATION,
        }
        self.river_status_var = tk.StringVar(value="Ścieżka rzeki: 0 heksów")
        self._river_resume_expected_exit: str | None = None
        self._river_resume_branch: str = "main"
        self._skip_river_mode_popup = False
        # Uproszczony tryb dopływu
        self._tributary_mode = False
        self._tributary_source_hex: str | None = None
        self._tributary_entry_side: str | None = None
        self.river_tributary_enabled_var = tk.BooleanVar(value=False)
        default_entry_label = next(iter(TRIBUTARY_ENTRY_OPTIONS))
        self.river_tributary_entry_var = tk.StringVar(value=default_entry_label)
        self.river_tributary_join_var = tk.DoubleVar(value=55.0)
        self.river_tributary_shape_var = tk.StringVar(value=TRIBUTARY_SHAPE_LABELS["curve"])
        self.river_tributary_strength_var = tk.DoubleVar(value=0.6)
        self.river_tributary_noise_var = tk.DoubleVar(value=0.0)
        self.river_tributary_frequency_var = tk.DoubleVar(value=2.5)
        self.river_tributary_direction_var = tk.StringVar(value=TRIBUTARY_DIRECTION_LABELS["auto"])
        self.river_tributary_seed_offset_var = tk.IntVar(value=1_000_000)
        self.tributary_size_profile_var = tk.StringVar(value="Średni dopływ")
        self.tributary_character_profile_var = tk.StringVar(value="Łagodny dopływ")
        self.tributary_entry_profile_var = self.river_tributary_entry_var
        default_size_cfg = TRIBUTARY_SIZE_OPTIONS.get("Średni dopływ", {})
        default_char_cfg = TRIBUTARY_CHARACTER_OPTIONS.get("Łagodny dopływ", {})
        self._current_tributary_params: dict[str, float | str] = {
            "bank_offset_scale": default_size_cfg.get("bank_offset_scale", 0.8),
            "variation_scale": default_size_cfg.get("variation_scale", 1.0),
            "shape": default_char_cfg.get("shape", "curve"),
            "shape_strength": default_char_cfg.get("shape_strength", 0.6),
            "noise_amplitude": default_char_cfg.get("noise_amplitude", 0.0),
            "noise_frequency": default_char_cfg.get("noise_frequency", 2.5),
            "shape_direction_mode": default_char_cfg.get("shape_direction_mode", "auto"),
        }
        self._river_tributary_widgets: list[tuple[tk.Widget, str]] = []
        self.river_tributary_enabled_var.trace_add("write", lambda *_: self._update_tributary_controls_state())
        self.river_preview_caption_var = tk.StringVar(
            value="Podgląd rzeki: dodaj co najmniej dwa heksy."
        )
        self.river_preview_label: tk.Label | None = None
        self._river_preview_photo: ImageTk.PhotoImage | None = None
        self._river_preview_cache_key: tuple | None = None

        # --- Narzędzie dróg ---
        self.road_mode_active = False
        self.road_path: list[str] = []

        # --- Narzędzie torów kolejowych ---
        self.railway_mode_active = False
        self.railway_path: list[str] = []
        self.railway_type_var = tk.StringVar(value="jednotorowy")
        self.railway_status_var = tk.StringVar(value="Trasa torów: 0 heksów")
        self.railway_junction_mode = False
        self.railway_junction_target_hex: str | None = None
        self.railway_junctions: dict[str, list[str]] = {}  # {hex_id: ["top", "top_right"]}

        # --- Narzędzie jezior ---
        self.lake_mode_active = False
        self.lake_cluster: list[str] = []  # Lista heksów w klastrze jeziora
        self.lake_center_hex: str | None = None
        self.lake_neighbor_side: str | None = None
        self.lake_size_var = tk.StringVar(value="średnie")  # rozmiar jeziora
        self.lake_status_var = tk.StringVar(value="Tryb jezior nieaktywny")
        self.lake_grid_var = tk.StringVar(value=str(DEFAULT_HEX_TEXTURE_GRID_SIZE))
        self.lake_seed_var = tk.IntVar(value=random.randint(0, 9999))
        self._lake_overlay_ids: list[int] = []  # ID elementów canvas overlay

        # --- Inicjalizacja GUI i danych ---
        self.load_token_index()
        self.build_gui()
        self.load_data()
        
        # Wymuś odświeżenie palety po inicjalizacji
        self.root.after(100, self.force_refresh_palette)

    def load_token_index(self):
        """Ładuje index żetonów z assets/tokens/index.json"""
        index_path = ASSET_ROOT / "tokens" / "index.json"
        try:
            with open(index_path, "r", encoding="utf-8") as f:
                self.token_index = json.load(f)
            # Konwertuj ścieżki obrazów na względne jeśli są absolutne
            for token in self.token_index:
                if "image" in token:
                    token["image"] = token["image"].replace("\\", "/")
                    if token["image"].startswith("assets/"):
                        # Już względna ścieżka
                        pass
                    else:
                        # Konwertuj do względnej
                        token["image"] = to_rel(token["image"])
            print(f"Załadowano {len(self.token_index)} żetonów z indeksu")
        except Exception as e:
            print(f"Błąd ładowania indeksu żetonów: {e}")
            self.token_index = []
        self.update_filtered_tokens()

    def update_filtered_tokens(self):
        """Aktualizuje listę przefiltrowanych żetonów według aktualnych filtrów"""
        self.filtered_tokens = []
        
        # Debug info
        print(f"[FILTER] Filtrowanie zetonow: total={len(self.token_index)}")
        
        # Pobierz używane żetony jeśli unikalność włączona
        used_tokens = set()
        if self.uniqueness_mode:
            for terrain in self.hex_data.values():
                token = terrain.get("token")
                if token and "unit" in token:
                    used_tokens.add(token["unit"])
            print(f"[UNIQUE] Uzyte zetony (unikalnosc ON): {len(used_tokens)}")
        
        for token in self.token_index:
            # Filtr unikalności
            if self.uniqueness_mode and token["id"] in used_tokens:
                continue
                
            # Filtr dowódcy - obsługa formatu dropdown "Dow. X (Nacja)"
            commander_filter = self.filter_commander.get()
            if commander_filter != "Wszystkie":
                # Wyciągnij numer dowódcy z "Dow. 2 (Polska)" -> "2"
                if commander_filter.startswith("Dow. "):
                    commander_num = commander_filter.split()[1]
                    token_owner = token.get("owner", "")
                    # Sprawdź czy owner zaczyna się od numeru dowódcy
                    if not token_owner.startswith(commander_num + " "):
                        continue
                    
            self.filtered_tokens.append(token)
        
        print(f"✅ Przefiltrowane żetony: {len(self.filtered_tokens)}")
        
        # Odśwież paletę żetonów
        if hasattr(self, 'token_palette_frame'):
            self.refresh_token_palette()

    def force_refresh_palette(self):
        """Wymusza odświeżenie palety żetonów po inicjalizacji"""
        print("🔄 Wymuszenie odświeżenia palety...")
        print(f"📊 Stan: {len(self.token_index)} żetonów w indeksie")
        print(f"🔒 Unikalność: {self.uniqueness_mode}")
        print(f"�️  Filtr dowódcy: {self.filter_commander.get()}")
        
        # Wymuś reset filtra na domyślny
        self.filter_commander.set("Wszystkie")
        
        # Wymuś aktualizację
        self.update_filtered_tokens()
        
        # Dodatkowo odśwież canvas
        if hasattr(self, 'tokens_canvas'):
            self.tokens_canvas.update_idletasks()

    def clear_texture_caches(self) -> None:
        self.hex_texture_cache.clear()
        self.flat_texture_preview_cache.clear()
        self._ghost_cache.clear()
        if hasattr(self, "_hex_texture_masks"):
            self._hex_texture_masks.clear()
        if hasattr(self, "_hex_texture_vertices"):
            self._hex_texture_vertices.clear()
        print("🧹 Wyczyszczono cache tekstur i podglądów")
        try:
            self.draw_grid()
        except Exception as exc:
            print(f"Nie udało się odświeżyć siatki po czyszczeniu cache: {exc}")
        messagebox.showinfo(
            "Cache",
            "Cache tekstur został wyczyszczony. Podgląd mapy odświeżony.",
            parent=self.root,
        )

    def open_cleanup_dialog(self) -> None:
        existing = getattr(self, "_cleanup_dialog", None)
        if existing and existing.winfo_exists():
            existing.deiconify()
            existing.lift()
            existing.focus_set()
            return

        dialog = tk.Toplevel(self.root)
        dialog.title("Czyszczenie mapy")
        dialog.transient(self.root)
        dialog.grab_set()
        dialog.configure(bg="darkolivegreen")
        dialog.resizable(False, False)
        self._cleanup_dialog = dialog

        def on_close() -> None:
            if getattr(self, "_cleanup_dialog", None) is dialog:
                self._cleanup_dialog = None
            dialog.destroy()

        dialog.protocol("WM_DELETE_WINDOW", on_close)

        container = tk.Frame(dialog, bg="darkolivegreen", padx=16, pady=16)
        container.pack(fill=tk.BOTH, expand=True)

        tk.Label(
            container,
            text="Wybierz elementy do wyczyszczenia:",
            bg="darkolivegreen",
            fg="white",
            font=("Arial", 10, "bold"),
            anchor="w"
        ).pack(fill=tk.X, pady=(0, 8))

        hexes_var = tk.BooleanVar(value=True)
        tokens_var = tk.BooleanVar(value=False)

        tk.Checkbutton(
            container,
            text="Dane heksów (teren, punkty kluczowe, spawn)",
            variable=hexes_var,
            bg="darkolivegreen",
            fg="white",
            selectcolor="darkolivegreen",
            anchor="w",
            justify="left"
        ).pack(fill=tk.X, pady=2)

        tk.Checkbutton(
            container,
            text="Żetony (start_tokens.json, assets/tokens, powiązania na mapie)",
            variable=tokens_var,
            bg="darkolivegreen",
            fg="white",
            selectcolor="darkolivegreen",
            anchor="w",
            justify="left"
        ).pack(fill=tk.X, pady=2)

        tk.Label(
            container,
            text="Operacje mogą usuwać pliki – wykonaj backup jeśli to konieczne.",
            bg="darkolivegreen",
            fg="#f4e19c",
            font=("Arial", 9),
            anchor="w",
            wraplength=360
        ).pack(fill=tk.X, pady=(10, 12))

        buttons = tk.Frame(container, bg="darkolivegreen")
        buttons.pack(fill=tk.X)

        def run_cleanup() -> None:
            selections = {
                "clear_hexes": hexes_var.get(),
                "clear_tokens": tokens_var.get(),
            }
            if not any(selections.values()):
                messagebox.showinfo("Czyszczenie mapy", "Zaznacz przynajmniej jedną operację.", parent=dialog)
                return

            summary_lines = []
            if selections["clear_hexes"]:
                summary_lines.append("• Dane heksów")
            if selections["clear_tokens"]:
                summary_lines.append("• Żetony")

            confirm_text = "Uruchomić czyszczenie obejmujące:\n" + "\n".join(summary_lines)
            if not messagebox.askyesno("Potwierdź czyszczenie", confirm_text, parent=dialog):
                return

            on_close()
            self.root.after(10, lambda: self._perform_map_cleanup(**selections))

        tk.Button(
            buttons,
            text="Anuluj",
            command=on_close,
            bg="#6b3d1f",
            fg="white",
            activebackground="#6b3d1f",
            activeforeground="white",
            width=12
        ).pack(side=tk.RIGHT, padx=4)

        tk.Button(
            buttons,
            text="Uruchom",
            command=run_cleanup,
            bg="#2f6b2f",
            fg="white",
            activebackground="#2f6b2f",
            activeforeground="white",
            width=12
        ).pack(side=tk.RIGHT, padx=4)

    def _perform_map_cleanup(self, *, clear_hexes: bool, clear_tokens: bool) -> None:
        results: list[str] = []
        errors: list[str] = []

        if clear_hexes:
            ok, msg = self._cleanup_hex_data()
            (results if ok else errors).append(msg)

        if clear_tokens:
            ok, msg = self._cleanup_tokens()
            (results if ok else errors).append(msg)

        if errors:
            messagebox.showerror(
                "Czyszczenie mapy",
                "\n".join(errors + results),
                parent=self.root,
            )
        else:
            messagebox.showinfo(
                "Czyszczenie mapy",
                "\n".join(results) if results else "Operacje zakończone.",
                parent=self.root,
            )

    def _cleanup_hex_data(self) -> tuple[bool, str]:
        original_hexes = self.hex_data
        hex_count = len(original_hexes)
        token_count = sum(1 for terrain in original_hexes.values() if isinstance(terrain, dict) and terrain.get("token"))
        key_points = len(self.key_points)
        spawn_points = sum(len(v) for v in self.spawn_points.values())

        preserved_keys = {
            "token",
            "token_history",
            "token_rotation",
            "token_scale",
            "token_origin",
        }

        new_hex_data: dict[str, dict] = {}
        new_hex_tokens: dict[str, str] = {}

        for hex_id, terrain in original_hexes.items():
            if not isinstance(terrain, dict):
                continue
            kept_record: dict[str, object] = {}
            for key, value in terrain.items():
                if key in preserved_keys or key.startswith("token"):
                    kept_record[key] = value
            token = terrain.get("token")
            if isinstance(token, dict) and token.get("image"):
                kept_record.setdefault("token", token)
                new_hex_tokens[hex_id] = token["image"]
            if kept_record:
                new_hex_data[hex_id] = kept_record

        self.hex_data = new_hex_data
        self.key_points = {}
        self.spawn_points = {}
        self.hex_tokens = new_hex_tokens
        self.selected_hex = None

        self.save_data()
        self.export_start_tokens(show_message=False)
        self.draw_grid()
        self.canvas.delete("highlight")
        self._reset_hex_info_panel()
        self.update_filtered_tokens()
        self.set_status("Wyczyszczono dane mapy.")

        textures_removed, texture_errors = self._cleanup_generated_hex_textures()

        if texture_errors:
            error_text = "; ".join(texture_errors)
            return False, (
                "Wyzerowano dane heksów, ale niektórych tekstur nie udało się usunąć: "
                + error_text
            )

        token_msg = " Żetony na mapie zostały zachowane." if token_count else " Brak żetonów do zachowania."
        texture_msg = (
            f" Usunięto {textures_removed} plików tekstur i metadanych rzek." if textures_removed else " Brak tekstur do usunięcia."
        )
        self._update_map_info_label()

        return True, (
            "Wyzerowano dane heksów"
            f" (heksy: {hex_count}, key points: {key_points}, spawn: {spawn_points})."
            + token_msg
            + texture_msg
        )

    def _cleanup_generated_hex_textures(self) -> tuple[int, list[str]]:
        removed = 0
        issues: list[str] = []

        # Usuń główne pliki tekstur
        if HEX_TEXTURE_DIR.exists():
            for texture_path in HEX_TEXTURE_DIR.glob("hex_*.png"):
                try:
                    texture_path.unlink()
                    removed += 1
                except Exception as exc:  # noqa: BLE001
                    issues.append(f"{texture_path.name}: {exc}")

        # Usuń pliki dróg z road_tool
        if ROAD_OUTPUT_DIR.exists():
            for file_path in ROAD_OUTPUT_DIR.glob("*"):
                try:
                    file_path.unlink()
                    removed += 1
                except Exception as exc:  # noqa: BLE001
                    issues.append(f"{file_path.name}: {exc}")

        # Usuń pliki rzek z river_tool
        if RIVER_OUTPUT_DIR.exists():
            for file_path in RIVER_OUTPUT_DIR.glob("*"):
                try:
                    file_path.unlink()
                    removed += 1
                except Exception as exc:  # noqa: BLE001
                    issues.append(f"{file_path.name}: {exc}")

        if RIVER_OUTPUT_DIR.exists():
            for pattern in ("hex_*.png", "hex_*.json"):
                for river_path in RIVER_OUTPUT_DIR.glob(pattern):
                    try:
                        river_path.unlink()
                        removed += 1
                    except Exception as exc:  # noqa: BLE001
                        issues.append(f"river_tool/{river_path.name}: {exc}")

        # Usuń pliki jezior z lake_tool
        if LAKE_OUTPUT_DIR.exists():
            for file_path in LAKE_OUTPUT_DIR.glob("*"):
                try:
                    file_path.unlink()
                    removed += 1
                except Exception as exc:  # noqa: BLE001
                    issues.append(f"lake_tool/{file_path.name}: {exc}")

        # Usuń pliki torów z railway_tool
        railway_dir = HEX_TEXTURE_DIR / "railway_tool"
        if railway_dir.exists():
            for file_path in railway_dir.glob("*"):
                try:
                    file_path.unlink()
                    removed += 1
                except Exception as exc:  # noqa: BLE001
                    issues.append(f"railway_tool/{file_path.name}: {exc}")

        return removed, issues

    def _cleanup_tokens(self) -> tuple[bool, str]:
        self.save_data()
        try:
            from czyszczenie.reset_tokens_simple import clear_map_tokens, purge_tokens_dir, reset_start_tokens
        except Exception as exc:  # noqa: BLE001
            return False, f"Nie można zaimportować narzędzia resetu żetonów: {exc}"

        ok_purge = purge_tokens_dir()
        ok_start = reset_start_tokens()
        ok_map = clear_map_tokens()

        self.load_data()
        self.load_token_index()
        self.clear_token_selection()
        if hasattr(self, "canvas"):
            self.canvas.delete("highlight")
        self._reset_hex_info_panel()
        self.set_status("Zresetowano żetony.")
        self._update_map_info_label()

        if ok_purge and ok_start and ok_map:
            return True, "Żetony zostały zresetowane (assets/tokens, start_tokens.json, map_data.json)."
        return False, "Zakończono z błędami podczas resetu żetonów – sprawdź log w konsoli."

    def _reset_hex_info_panel(self) -> None:
        if hasattr(self, "hex_info_label"):
            self.hex_info_label.config(text="Heks: brak")
        if hasattr(self, "terrain_info_label"):
            self.terrain_info_label.config(text="Teren: brak")
        if hasattr(self, "token_info_label"):
            self.token_info_label.config(text="Żeton: brak")
        if hasattr(self, "texture_info_label"):
            self.texture_info_label.config(text="Tekstura: domyślna")
        if hasattr(self, "flat_texture_info_label"):
            self.flat_texture_info_label.config(text="Wzór płaski: brak")
        if hasattr(self, "key_point_info_label"):
            self.key_point_info_label.config(text="")
        if hasattr(self, "spawn_point_info_label"):
            self.spawn_point_info_label.config(text="")
        if hasattr(self, "map_info_label"):
            self._update_map_info_label()

    def get_last_modified_map(self):
        # zawsze używamy predefiniowanej mapy
        if os.path.exists(DEFAULT_MAP_FILE):
            return DEFAULT_MAP_FILE
        # jeśli nie ma pliku, pozwalamy wybrać ręcznie
        print("⚠️  Nie znaleziono pliku domyślnej mapy. Użytkownik może wybrać ręcznie.")
        return filedialog.askopenfilename(
            title="Wybierz mapę",
            initialdir=os.path.dirname(DEFAULT_MAP_FILE),
            filetypes=[("Obrazy", "*.jpg *.png *.bmp"), ("Wszystkie pliki", "*.*")]
        )

    def build_gui(self):
        'Tworzy interfejs użytkownika.'
        # Panel boczny z przyciskami i paletą żetonów
        self.panel_frame = tk.Frame(self.root, bg="darkolivegreen", relief=tk.RIDGE, bd=5)
        self.panel_frame.pack(side=tk.RIGHT, fill=tk.Y, padx=5, pady=5)
        
        # === SEKCJA OPERACJI (na górze) ===
        buttons_frame = tk.Frame(self.panel_frame, bg="darkolivegreen")
        buttons_frame.pack(side=tk.TOP, fill=tk.X)

        # Przycisk "Otwórz Mapę + Dane"
        self.open_map_and_data_button = tk.Button(
            buttons_frame, text="Otwórz Mapę + Dane", command=self.open_map_and_data,
            bg="saddlebrown", fg="white", activebackground="saddlebrown", activeforeground="white"
        )
        self.open_map_and_data_button.pack(padx=5, pady=2, fill=tk.X)

        # Przycisk "Zapisz dane mapy"
        self.save_map_and_data_button = tk.Button(
            buttons_frame, text="Zapisz dane mapy", command=self.save_map_and_data,
            bg="saddlebrown", fg="white", activebackground="saddlebrown", activeforeground="white"
        )
        self.save_map_and_data_button.pack(padx=5, pady=2, fill=tk.X)

        # === CHECKBOX AUTO-SAVE ===
        self.auto_save_var = tk.BooleanVar(value=True)
        auto_save_cb = tk.Checkbutton(buttons_frame, text="🔄 Auto-save", variable=self.auto_save_var,
                                     bg="darkolivegreen", fg="white", selectcolor="darkolivegreen",
                                     command=self.toggle_auto_save)
        auto_save_cb.pack(padx=5, pady=2, anchor="w")

        # Przycisk konfiguracji mapy
        self.configure_map_button = tk.Button(
            buttons_frame,
            text="Konfiguracja mapy…",
            command=self.open_map_configuration_dialog,
            bg="saddlebrown",
            fg="white",
            activebackground="saddlebrown",
            activeforeground="white"
        )
        self.configure_map_button.pack(padx=5, pady=2, fill=tk.X)

        self.clear_cache_button = tk.Button(
            buttons_frame,
            text="Wyczyść cache tekstur",
            command=self.clear_texture_caches,
            bg="#444444",
            fg="white",
            activebackground="#444444",
            activeforeground="white"
        )
        self.clear_cache_button.pack(padx=5, pady=2, fill=tk.X)

        self.map_cleanup_button = tk.Button(
            buttons_frame,
            text="Czyszczenie mapy…",
            command=self.open_cleanup_dialog,
            bg="#4f2a12",
            fg="white",
            activebackground="#4f2a12",
            activeforeground="white"
        )
        self.map_cleanup_button.pack(padx=5, pady=2, fill=tk.X)

        self.hex_cleanup_button = tk.Button(
            buttons_frame,
            text="Czyszczenie heksa",
            command=self.clear_selected_hex_smart,
            bg="#4f2a12",
            fg="white",
            activebackground="#4f2a12",
            activeforeground="white"
        )
        self.hex_cleanup_button.pack(padx=5, pady=2, fill=tk.X)

        # === UTWORZENIE PANED WINDOW DLA LEPSZEGO ZARZĄDZANIA PRZESTRZENIĄ ===
        # Paned window dzieli pozostałą przestrzeń na paletę żetonów i panel informacyjny
        self.main_paned = tk.PanedWindow(self.panel_frame, orient=tk.VERTICAL, bg="darkolivegreen")
        self.main_paned.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)

        # === GÓRNA CZĘŚĆ: Paleta żetonów i inne sekcje ===
        self.upper_container = tk.Frame(self.main_paned, bg="darkolivegreen")
        # Górny panel ma przejmować całą dodatkową przestrzeń na scrollowane sekcje
        self.main_paned.add(self.upper_container, minsize=200, stretch="always")
        self.upper_canvas = tk.Canvas(self.upper_container, bg="darkolivegreen", highlightthickness=0)
        self.upper_canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        self.upper_scrollbar = tk.Scrollbar(self.upper_container, orient=tk.VERTICAL, command=self.upper_canvas.yview)
        self.upper_scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        self.upper_canvas.configure(yscrollcommand=self.upper_scrollbar.set)
        self.upper_frame = tk.Frame(self.upper_canvas, bg="darkolivegreen")
        self.upper_frame_window = self.upper_canvas.create_window((0, 0), window=self.upper_frame, anchor="nw")
        self.upper_frame.bind("<Configure>", lambda _e: self.upper_canvas.configure(scrollregion=self.upper_canvas.bbox("all")))
        self.upper_canvas.bind("<Configure>", lambda e: self.upper_canvas.itemconfigure(self.upper_frame_window, width=e.width))
        self.upper_canvas.bind("<MouseWheel>", self._scroll_upper_panel)
        self.upper_frame.bind("<MouseWheel>", self._scroll_upper_panel)
        self.upper_canvas.bind("<Button-4>", self._scroll_upper_panel)
        self.upper_canvas.bind("<Button-5>", self._scroll_upper_panel)
        self.upper_frame.bind("<Button-4>", self._scroll_upper_panel)
        self.upper_frame.bind("<Button-5>", self._scroll_upper_panel)

        # === PALETA ŻETONÓW ===
        self.build_token_palette_in_frame(self.upper_frame)

        # === NARZĘDZIE RZEK ===
        self.river_section_container = tk.Frame(self.upper_frame, bg="darkolivegreen")
        self.river_section_container.pack(fill=tk.X, padx=5, pady=(6, 4))

        self._river_section_expanded = False
        self.river_section_toggle_button = tk.Button(
            self.river_section_container,
            text="[+] Rzeki (beta)",
            command=self.toggle_river_section_visibility,
            bg="#2f4d34",
            fg="white",
            activebackground="#2f4d34",
            activeforeground="white",
            anchor="w",
            font=("Arial", 9, "bold"),
        )
        self.river_section_toggle_button.pack(fill=tk.X)

        self.river_frame = tk.LabelFrame(
            self.river_section_container,
            text="Rzeki (beta)",
            bg="darkolivegreen",
            fg="white",
            font=("Arial", 9, "bold"),
        )

        self.toggle_river_mode_button = tk.Button(
            self.river_frame,
            text="Włącz tryb rzeki",
            command=self.toggle_river_mode,
            bg="#1f5d7a",
            fg="white",
            activebackground="#1f5d7a",
            activeforeground="white",
        )
        self.toggle_river_mode_button.pack(fill=tk.X, pady=(0, 4))

        self.river_status_label = tk.Label(
            self.river_frame,
            textvariable=self.river_status_var,
            bg="darkolivegreen",
            fg="#d4f2bf",
            anchor="w",
            justify="left",
            wraplength=190,
        )
        self.river_status_label.pack(fill=tk.X, pady=(0, 4))

        # === SZYBKI WYBÓR TYPU RZEKI (uproszczony interfejs) ===
        quick_preset_frame = tk.LabelFrame(
            self.river_frame,
            text="⚡ Szybki wybór typu",
            bg="darkolivegreen",
            fg="#ffd166",
            font=("Arial", 9, "bold"),
        )
        quick_preset_frame.pack(fill=tk.X, pady=(0, 6))
        
        self.river_quick_preset_var = tk.StringVar(value="Mała rzeka (łagodna)")
        quick_preset_values = list(RIVER_QUICK_PRESETS.keys())
        self.river_quick_preset_combo = ttk.Combobox(
            quick_preset_frame,
            textvariable=self.river_quick_preset_var,
            values=quick_preset_values,
            state="readonly",
            width=22,
        )
        self.river_quick_preset_combo.pack(fill=tk.X, padx=4, pady=4)
        self.river_quick_preset_combo.bind("<<ComboboxSelected>>", lambda *_: self._apply_quick_river_preset())
        self.create_tooltip(
            self.river_quick_preset_combo,
            "Wybierz gotowy typ rzeki - automatycznie ustawi rozmiar, krętość i brzegi.",
        )
        
        self.river_quick_preset_desc = tk.Label(
            quick_preset_frame,
            text="Typowa mała rzeka z delikatnymi meandrami",
            bg="darkolivegreen",
            fg="#d4f2bf",
            font=("Arial", 8, "italic"),
            anchor="w",
            wraplength=190,
        )
        self.river_quick_preset_desc.pack(fill=tk.X, padx=4, pady=(0, 4))

        # === SZCZEGÓŁOWE USTAWIENIA (opcjonalnie rozwijane) ===
        self._river_advanced_expanded = False
        self.river_advanced_toggle = tk.Button(
            self.river_frame,
            text="[+] Szczegółowe ustawienia",
            command=self._toggle_river_advanced_settings,
            bg="#3d5a40",
            fg="white",
            relief=tk.FLAT,
            font=("Arial", 8),
        )
        self.river_advanced_toggle.pack(fill=tk.X, pady=(0, 2))
        
        self.river_advanced_frame = tk.Frame(self.river_frame, bg="darkolivegreen")
        # Domyślnie ukryte - nie pakujemy

        river_controls = tk.Frame(self.river_advanced_frame, bg="darkolivegreen")
        river_controls.pack(fill=tk.X)
        river_controls.columnconfigure(1, weight=1)

        size_label = tk.Label(river_controls, text="Rozmiar", bg="darkolivegreen", fg="white")
        size_label.grid(row=0, column=0, sticky="w")
        size_values = list(RIVER_SIZE_OPTIONS.keys())
        self.river_size_combo = ttk.Combobox(
            river_controls,
            textvariable=self.river_size_profile_var,
            values=size_values,
            state="readonly",
            width=18,
        )
        self.river_size_combo.grid(row=0, column=1, sticky="we", pady=1)
        self.river_size_combo.bind("<<ComboboxSelected>>", lambda *_: self._apply_river_profiles())
        self.create_tooltip(
            self.river_size_combo,
            "Wybierz szerokość nurtu: od strumienia po dużą rzekę.",
        )

        curve_label = tk.Label(river_controls, text="Krętość", bg="darkolivegreen", fg="white")
        curve_label.grid(row=1, column=0, sticky="w")
        curve_values = list(RIVER_CURVATURE_OPTIONS.keys())
        self.river_curvature_combo = ttk.Combobox(
            river_controls,
            textvariable=self.river_curvature_profile_var,
            values=curve_values,
            state="readonly",
            width=18,
        )
        self.river_curvature_combo.grid(row=1, column=1, sticky="we", pady=1)
        self.river_curvature_combo.bind("<<ComboboxSelected>>", lambda *_: self._apply_river_profiles())
        self.create_tooltip(
            self.river_curvature_combo,
            "Określ jak mocno rzeka zakręca: od prostego koryta po dynamiczne meandry.",
        )

        bank_label = tk.Label(river_controls, text="Typ brzegu", bg="darkolivegreen", fg="white")
        bank_label.grid(row=2, column=0, sticky="w")
        bank_values = list(RIVER_BANK_OPTIONS.keys())
        self.river_bank_combo = ttk.Combobox(
            river_controls,
            textvariable=self.river_bank_profile_var,
            values=bank_values,
            state="readonly",
            width=18,
        )
        self.river_bank_combo.grid(row=2, column=1, sticky="we", pady=1)
        self.river_bank_combo.bind("<<ComboboxSelected>>", lambda *_: self._apply_river_profiles())
        self.create_tooltip(
            self.river_bank_combo,
            "Wybierz charakter brzegów: stabilne, piaszczyste, błotniste lub erozyjne.",
        )

        grid_info = tk.Label(
            river_controls,
            textvariable=self.river_grid_info_var,
            bg="darkolivegreen",
            fg="#d4f2bf",
            anchor="w",
        )
        grid_info.grid(row=3, column=0, columnspan=2, sticky="we", pady=(2, 0))

        seed_frame = tk.Frame(river_controls, bg="darkolivegreen")
        seed_frame.grid(row=4, column=0, columnspan=2, sticky="we", pady=(2, 0))
        seed_label = tk.Label(seed_frame, textvariable=self.river_seed_label_var, bg="darkolivegreen", fg="white")
        seed_label.pack(side=tk.LEFT)
        self.create_tooltip(
            seed_label,
            "Bieżący seed wpływający na losowość koryta. Możesz wylosować nowy gdy chcesz odmienny układ.",
        )
        seed_button = tk.Button(
            seed_frame,
            text="Losuj ziarno",
            command=self._randomize_river_seed,
            bg="#446b2f",
            fg="white",
            relief=tk.FLAT,
        )
        seed_button.pack(side=tk.RIGHT)
        self.create_tooltip(
            seed_button,
            "Losuje nowy seed dla rzeki, zachowując pozostałe ustawienia profilu.",
        )

        template_frame = tk.LabelFrame(
            self.river_advanced_frame,
            text="Szablony nurtu",
            bg="darkolivegreen",
            fg="white",
            font=("Arial", 9, "bold"),
        )
        template_frame.pack(fill=tk.X, pady=(4, 4))
        template_frame.columnconfigure(0, weight=1)
        template_frame.columnconfigure(1, weight=1)
        for idx, (template_label, _) in enumerate(RIVER_TEMPLATE_SEGMENTS.items()):
            btn = tk.Button(
                template_frame,
                text=template_label,
                command=lambda name=template_label: self._apply_river_template(name),
                bg="#2f6b2f",
                fg="white",
            )
            row_idx, col_idx = divmod(idx, 2)
            btn.grid(row=row_idx, column=col_idx, sticky="we", padx=2, pady=2)
            self.create_tooltip(
                btn,
                "Dodaje do ścieżki serię heksów zgodnie z wybranym wzorem (wymagany początkowy heks).",
            )

        tributary_frame = tk.LabelFrame(
            self.river_advanced_frame,
            text="Dopływ (opcjonalnie)",
            bg="darkolivegreen",
            fg="white",
            font=("Arial", 9, "bold"),
        )
        tributary_frame.pack(fill=tk.X, pady=(4, 4))

        tributary_toggle = tk.Checkbutton(
            tributary_frame,
            text="Dodaj dopływ do generowanego heksu",
            variable=self.river_tributary_enabled_var,
            bg="darkolivegreen",
            fg="white",
            activebackground="darkolivegreen",
            activeforeground="white",
            selectcolor="#2f6b2f",
            indicatoron=True,
            highlightthickness=0,
            onvalue=True,
            offvalue=False,
            anchor="w",
        )
        tributary_toggle.pack(fill=tk.X, padx=4, pady=(2, 4))
        self.create_tooltip(
            tributary_toggle,
            "Jeśli dopływ jest aktywny, heks dostanie dodatkowe koryto łączące się z główną rzeką.",
        )

        tributary_controls = tk.Frame(tributary_frame, bg="darkolivegreen")
        tributary_controls.pack(fill=tk.X, padx=4, pady=(0, 2))
        for col_idx in (1,):
            tributary_controls.columnconfigure(col_idx, weight=1)

        tk.Label(tributary_controls, text="Rozmiar", bg="darkolivegreen", fg="white").grid(row=0, column=0, sticky="w")
        tributary_size_values = list(TRIBUTARY_SIZE_OPTIONS.keys())
        self.tributary_size_combo = ttk.Combobox(
            tributary_controls,
            values=tributary_size_values,
            textvariable=self.tributary_size_profile_var,
            state="readonly",
            width=18,
        )
        self.tributary_size_combo.grid(row=0, column=1, sticky="we", pady=1)
        self.tributary_size_combo.bind("<<ComboboxSelected>>", lambda *_: self._apply_tributary_profiles())
        self._register_tributary_control(self.tributary_size_combo, enabled_state="readonly")
        self.create_tooltip(
            self.tributary_size_combo,
            "Określ, jak szeroki ma być dopływ względem głównej rzeki.",
        )

        tk.Label(tributary_controls, text="Charakter", bg="darkolivegreen", fg="white").grid(
            row=1, column=0, sticky="w"
        )
        tributary_character_values = list(TRIBUTARY_CHARACTER_OPTIONS.keys())
        self.tributary_character_combo = ttk.Combobox(
            tributary_controls,
            values=tributary_character_values,
            textvariable=self.tributary_character_profile_var,
            state="readonly",
            width=18,
        )
        self.tributary_character_combo.grid(row=1, column=1, sticky="we", pady=1)
        self.tributary_character_combo.bind("<<ComboboxSelected>>", lambda *_: self._apply_tributary_profiles())
        self._register_tributary_control(self.tributary_character_combo, enabled_state="readonly")
        self.create_tooltip(
            self.tributary_character_combo,
            "Wybierz jak dopływ ma zakręcać: łagodnie, ostro lub esowato.",
        )

        tk.Label(tributary_controls, text="Kierunek wejścia", bg="darkolivegreen", fg="white").grid(
            row=2, column=0, sticky="w"
        )
        entry_values = list(TRIBUTARY_ENTRY_OPTIONS.keys())
        self.river_tributary_entry_combo = ttk.Combobox(
            tributary_controls,
            values=entry_values,
            textvariable=self.tributary_entry_profile_var,
            state="readonly",
            width=18,
        )
        self.river_tributary_entry_combo.grid(row=2, column=1, sticky="we", pady=1)
        self.river_tributary_entry_combo.bind("<<ComboboxSelected>>", self._on_tributary_entry_change)
        self._register_tributary_control(self.river_tributary_entry_combo, enabled_state="readonly")
        self.create_tooltip(
            self.river_tributary_entry_combo,
            "Wskaż, z której krawędzi heksu dopływ ma wpadać do głównego nurtu.",
        )

        tk.Label(tributary_controls, text="Połączenie (%)", bg="darkolivegreen", fg="white").grid(
            row=3, column=0, sticky="w"
        )
        self.river_tributary_join_spinbox = tk.Spinbox(
            tributary_controls,
            from_=int(MIN_TRIBUTARY_JOIN * 100),
            to=int(MAX_TRIBUTARY_JOIN * 100),
            increment=1,
            textvariable=self.river_tributary_join_var,
            width=6,
        )
        self.river_tributary_join_spinbox.grid(row=3, column=1, sticky="we", pady=1)
        self._register_tributary_control(self.river_tributary_join_spinbox)
        self.create_tooltip(
            self.river_tributary_join_spinbox,
            "Określa punkt połączenia dopływu (20% to początek nurtu, 80% blisko końca).",
        )

        tk.Label(
            tributary_frame,
            text="Dopływ łączy się z heksowym nurtem; parametry zapiszą się w metadanych.",
            bg="darkolivegreen",
            fg="#d4f2bf",
            font=("Arial", 8, "italic"),
            anchor="w",
            wraplength=190,
        ).pack(fill=tk.X, padx=4, pady=(2, 0))

        buttons_inner = tk.Frame(self.river_frame, bg="darkolivegreen")
        buttons_inner.pack(fill=tk.X, pady=(4, 0))

        self.river_generate_button = tk.Button(
            buttons_inner,
            text="🌊 Generuj rzekę",
            command=self.generate_river_path,
            bg="#2f6b2f",
            fg="white",
            state=tk.DISABLED,
            font=("Arial", 9, "bold"),
        )
        self.river_generate_button.pack(fill=tk.X, pady=1)

        # === UPROSZCZONA SEKCJA DOPŁYWÓW ===
        tributary_simple_frame = tk.LabelFrame(
            self.river_frame,
            text="🔀 Dopływy i rozgałęzienia",
            bg="darkolivegreen",
            fg="#7dd3fc",
            font=("Arial", 9, "bold"),
        )
        tributary_simple_frame.pack(fill=tk.X, pady=(6, 4))
        
        tk.Label(
            tributary_simple_frame,
            text="Aby dodać dopływ:\n1. Kliknij heks z rzeką\n2. Kliknij 'Dodaj dopływ'\n3. Kliknij sąsiedni heks (źródło dopływu)",
            bg="darkolivegreen",
            fg="#d4f2bf",
            font=("Arial", 8),
            anchor="w",
            justify="left",
            wraplength=190,
        ).pack(fill=tk.X, padx=4, pady=(2, 4))
        
        # Kontrolki wielkości dopływu
        tributary_size_frame = tk.Frame(tributary_simple_frame, bg="darkolivegreen")
        tributary_size_frame.pack(fill=tk.X, padx=4, pady=(0, 4))
        
        tk.Label(tributary_size_frame, text="Wielkość dopływu:", bg="darkolivegreen", fg="white").pack(side=tk.LEFT)
        
        self.tributary_size_var = tk.StringVar(value="mały")
        tributary_sizes = ["mały", "średni", "duży"]
        self.tributary_size_combo = ttk.Combobox(
            tributary_size_frame,
            textvariable=self.tributary_size_var,
            values=tributary_sizes,
            state="readonly",
            width=10,
        )
        self.tributary_size_combo.pack(side=tk.RIGHT, padx=(4, 0))
        self.create_tooltip(
            self.tributary_size_combo,
            "Szerokość dopływu wpływającego do głównej rzeki.",
        )
        
        self.add_tributary_button = tk.Button(
            tributary_simple_frame,
            text="➕ Dodaj dopływ",
            command=self._start_simple_tributary,
            bg="#1f5d7a",
            fg="white",
        )
        self.add_tributary_button.pack(fill=tk.X, padx=4, pady=(0, 4))
        self.create_tooltip(
            self.add_tributary_button,
            "Po kliknięciu wskaż sąsiedni heks skąd płynie dopływ.",
        )
        
        # Status dopływu
        self.tributary_status_var = tk.StringVar(value="")
        self.tributary_status_label = tk.Label(
            tributary_simple_frame,
            textvariable=self.tributary_status_var,
            bg="darkolivegreen",
            fg="#ffd166",
            font=("Arial", 8, "italic"),
            anchor="w",
            wraplength=190,
        )
        self.tributary_status_label.pack(fill=tk.X, padx=4, pady=(0, 2))

        # === POZOSTAŁE PRZYCISKI ===
        other_buttons = tk.Frame(self.river_frame, bg="darkolivegreen")
        other_buttons.pack(fill=tk.X, pady=(4, 0))

        self.river_continue_button = tk.Button(
            other_buttons,
            text="↪ Kontynuuj rzekę z heksu",
            command=self.continue_river_from_selected_hex,
            bg="#1f4a6b",
            fg="white",
        )
        self.river_continue_button.pack(fill=tk.X, pady=1)

        self.river_undo_button = tk.Button(
            other_buttons,
            text="⬅ Cofnij ostatni",
            command=self.river_pop_last_hex,
            bg="#6b3d1f",
            fg="white",
            state=tk.DISABLED,
        )
        self.river_undo_button.pack(fill=tk.X, pady=1)

        self.river_clear_button = tk.Button(
            other_buttons,
            text="Wyczyść ścieżkę",
            command=self.clear_river_path,
            bg="#444444",
            fg="white",
            state=tk.DISABLED,
        )
        self.river_clear_button.pack(fill=tk.X, pady=(0, 1))

        tk.Label(
            self.river_frame,
            text="LPM dodaje, PPM cofa ost. heks.",
            bg="darkolivegreen",
            fg="#d4f2bf",
            font=("Arial", 8, "italic"),
            anchor="w",
            wraplength=190,
        ).pack(fill=tk.X, pady=(2, 0))

        preview_container = tk.LabelFrame(
            self.river_frame,
            text="Podgląd heksu",
            bg="darkolivegreen",
            fg="white",
            font=("Arial", 9, "bold"),
        )
        preview_container.pack(fill=tk.X, pady=(4, 0))

        preview_caption = tk.Label(
            preview_container,
            textvariable=self.river_preview_caption_var,
            bg="darkolivegreen",
            fg="#d4f2bf",
            anchor="w",
            justify="left",
            wraplength=190,
        )
        preview_caption.pack(fill=tk.X, padx=4, pady=(2, 4))

        self.river_preview_label = tk.Label(
            preview_container,
            bg="darkolivegreen",
            fg="#d4f2bf",
            text="Brak podglądu",
        )
        self.river_preview_label.pack(padx=4, pady=(0, 6))

        self._apply_river_profiles()
        self._apply_tributary_profiles()
        self._on_tributary_entry_change()
        self._update_river_seed_label()
        self._river_update_status()
        self._set_river_section_visibility(False)
        self._update_river_preview_image()

        # === SEKCJA TORÓW KOLEJOWYCH ===
        self._railway_section_expanded = False
        
        self.railway_section_toggle_button = tk.Button(
            self.upper_frame,
            text="[+] Tory kolejowe (beta)",
            command=self.toggle_railway_section_visibility,
            bg="#4a4a4a",
            fg="white",
            activebackground="#5a5a5a",
            activeforeground="white",
            anchor="w",
            font=("Arial", 9, "bold"),
        )
        self.railway_section_toggle_button.pack(fill=tk.X, padx=5, pady=2)

        # Kontener na rozwijaną sekcję torów
        self.railway_section_container = tk.Frame(self.upper_frame, bg="darkolivegreen")
        # Domyślnie ukryte - nie pakujemy

        self.railway_frame = tk.Frame(
            self.railway_section_container, bg="darkolivegreen"
        )
        self.railway_frame.pack(fill=tk.X, pady=(2, 0))

        # === TOGGLE TRYBU TORÓW ===
        self.railway_mode_button = tk.Button(
            self.railway_frame,
            text="Włącz tryb torów",
            command=self.toggle_railway_mode,
            bg="#4a4a4a",
            fg="white",
            activebackground="#5a5a5a",
            activeforeground="white",
            font=("Arial", 9, "bold"),
        )
        self.railway_mode_button.pack(fill=tk.X, pady=(0, 6))

        # Status
        self.railway_status_label = tk.Label(
            self.railway_frame,
            textvariable=self.railway_status_var,
            bg="darkolivegreen",
            fg="#d4f2bf",
            anchor="w",
            justify="left",
            wraplength=190,
        )
        self.railway_status_label.pack(fill=tk.X, pady=(0, 4))

        # === TYP TORU ===
        type_frame = tk.LabelFrame(
            self.railway_frame,
            text="Typ toru",
            bg="darkolivegreen",
            fg="#ffd166",
            font=("Arial", 9, "bold"),
        )
        type_frame.pack(fill=tk.X, pady=(0, 6))

        railway_types = ["jednotorowy", "dwutorowy"]
        for rtype in railway_types:
            rb = tk.Radiobutton(
                type_frame,
                text=rtype.capitalize(),
                variable=self.railway_type_var,
                value=rtype,
                bg="darkolivegreen",
                fg="white",
                selectcolor="#2f4d34",
                activebackground="darkolivegreen",
                activeforeground="white",
            )
            rb.pack(anchor="w")

        # === PRZYCISKI AKCJI ===
        actions_frame = tk.Frame(self.railway_frame, bg="darkolivegreen")
        actions_frame.pack(fill=tk.X, pady=(6, 0))

        self.railway_generate_btn = tk.Button(
            actions_frame,
            text="🚂 Generuj tory",
            command=self.generate_railway_path,
            bg="#4a4a4a",
            fg="white",
            activebackground="#5a5a5a",
            activeforeground="white",
            state=tk.DISABLED,
        )
        self.railway_generate_btn.pack(fill=tk.X, pady=(0, 4))

        self.railway_undo_btn = tk.Button(
            actions_frame,
            text="↩️ Cofnij ostatni",
            command=self.railway_pop_last_hex,
            bg="#4a4a4a",
            fg="white",
            state=tk.DISABLED,
        )
        self.railway_undo_btn.pack(fill=tk.X, pady=(0, 4))

        self.railway_clear_btn = tk.Button(
            actions_frame,
            text="🗑️ Wyczyść trasę",
            command=self.clear_railway_path,
            bg="#4a4a4a",
            fg="white",
            state=tk.DISABLED,
        )
        self.railway_clear_btn.pack(fill=tk.X, pady=(0, 6))

        # === SEKCJA ROZJAZDÓW ===
        junctions_section = tk.LabelFrame(
            self.railway_frame,
            text="🔀 Rozjazdy",
            bg="darkolivegreen",
            fg="#ffd166",
            font=("Arial", 9, "bold"),
        )
        junctions_section.pack(fill=tk.X, pady=(0, 4))

        tk.Label(
            junctions_section,
            text="Aby dodać rozjazd:\n1. Zaznacz heks z torami (LPM)\n2. Wybierz typ rozjazdu\n3. Kliknij 'Dodaj rozjazd'\n4. Kliknij sąsiedni heks",
            bg="darkolivegreen",
            fg="#d4f2bf",
            font=("Arial", 8),
            anchor="w",
            justify="left",
            wraplength=190,
        ).pack(fill=tk.X, padx=4, pady=(2, 4))

        # Typ rozjazdu
        junction_type_frame = tk.LabelFrame(
            junctions_section,
            text="Typ rozjazdu",
            bg="darkolivegreen",
            fg="#ffd166",
            font=("Arial", 8, "bold"),
        )
        junction_type_frame.pack(fill=tk.X, padx=4, pady=(0, 6))

        self.railway_junction_type_var = tk.StringVar(value="jednotorowy")
        
        for jtype in ["jednotorowy", "dwutorowy"]:
            rb = tk.Radiobutton(
                junction_type_frame,
                text=jtype.capitalize(),
                variable=self.railway_junction_type_var,
                value=jtype,
                bg="darkolivegreen",
                fg="white",
                selectcolor="#2f4d34",
                activebackground="darkolivegreen",
                activeforeground="white",
            )
            rb.pack(anchor="w")

        self.railway_add_junction_btn = tk.Button(
            junctions_section,
            text="➕ Dodaj rozjazd",
            command=self.start_railway_junction_mode,
            bg="#4a4a4a",
            fg="white",
            state=tk.DISABLED,
        )
        self.railway_add_junction_btn.pack(fill=tk.X, padx=4, pady=(0, 4))

        self.railway_junction_status_var = tk.StringVar(value="")
        self.railway_junction_status_label = tk.Label(
            junctions_section,
            textvariable=self.railway_junction_status_var,
            bg="darkolivegreen",
            fg="#ffd166",
            font=("Arial", 8, "italic"),
            anchor="w",
            wraplength=190,
        )
        self.railway_junction_status_label.pack(fill=tk.X, padx=4, pady=(0, 2))

        self._set_railway_section_visibility(False)

        # === SEKCJA DRÓG ===
        self._road_section_expanded = False
        
        # Inicjalizacja zmiennych dróg (MUSI BYĆ PRZED GUI)
        self.road_status_var = tk.StringVar(value="Ścieżka drogi: 0 heksów")
        self.road_type_var = tk.StringVar(value="Droga gruntowa")
        self.road_width_var = tk.StringVar(value="Średnia (typowa)")
        self.road_noise_var = tk.DoubleVar(value=0.3)
        self.road_seed_var = tk.StringVar(value="42")
        self.road_crossroads_mode = False  # Tryb dodawania skrzyżowań
        self.road_crossroads_sides: list[str] = []  # Dodatkowe boki dla skrzyżowań
        self.road_crossroads_hex: str | None = None  # Heks na którym jest skrzyżowanie
        self.road_crossroads_status_var = tk.StringVar(value="")  # Status skrzyżowania
        self.road_modify_status_var = tk.StringVar(value="")  # Status modyfikacji drogi
        
        self.road_section_toggle_button = tk.Button(
            self.upper_frame,
            text="[+] Drogi (beta)",
            command=self.toggle_road_section_visibility,
            bg="#5a4a3a",
            fg="white",
            activebackground="#6a5a4a",
            activeforeground="white",
            anchor="w",
            font=("Arial", 9, "bold"),
        )
        self.road_section_toggle_button.pack(fill=tk.X, padx=5, pady=2)

        # Kontener na rozwijaną sekcję dróg
        self.road_section_container = tk.Frame(self.upper_frame, bg="darkolivegreen")
        # Domyślnie ukryte - nie pakujemy

        self.road_frame = tk.Frame(
            self.road_section_container, bg="darkolivegreen"
        )
        self.road_frame.pack(fill=tk.X, pady=(2, 0))

        # Przycisk trybu
        self.toggle_road_mode_button = tk.Button(
            self.road_frame, text="Włącz tryb drogi",
            command=self.toggle_road_mode,
            bg="#5a4a3a", fg="white",
            activebackground="#6a5a4a", activeforeground="white",
        )
        self.toggle_road_mode_button.pack(fill=tk.X, padx=4, pady=2)

        # Status
        road_status_label = tk.Label(
            self.road_frame, textvariable=self.road_status_var,
            bg="darkolivegreen", fg="#ffe4b5", font=("Arial", 8),
        )
        road_status_label.pack(fill=tk.X, padx=4, pady=(0, 4))

        # Typ drogi
        road_type_frame = tk.Frame(self.road_frame, bg="darkolivegreen")
        road_type_frame.pack(fill=tk.X, padx=4, pady=2)
        tk.Label(road_type_frame, text="Typ:", bg="darkolivegreen", fg="white", width=8, anchor="w").pack(side=tk.LEFT)
        road_type_combo = ttk.Combobox(
            road_type_frame, textvariable=self.road_type_var,
            values=list(ROAD_TYPE_LABELS.values()), state="readonly", width=18,
        )
        road_type_combo.pack(side=tk.LEFT, fill=tk.X, expand=True)

        # Szerokość drogi
        road_width_frame = tk.Frame(self.road_frame, bg="darkolivegreen")
        road_width_frame.pack(fill=tk.X, padx=4, pady=2)
        tk.Label(road_width_frame, text="Szerokość:", bg="darkolivegreen", fg="white", width=8, anchor="w").pack(side=tk.LEFT)
        road_width_combo = ttk.Combobox(
            road_width_frame, textvariable=self.road_width_var,
            values=list(ROAD_WIDTH_LABELS.values()), state="readonly", width=18,
        )
        road_width_combo.pack(side=tk.LEFT, fill=tk.X, expand=True)

        # Szum (krętość)
        road_noise_frame = tk.Frame(self.road_frame, bg="darkolivegreen")
        road_noise_frame.pack(fill=tk.X, padx=4, pady=2)
        tk.Label(road_noise_frame, text="Krętość:", bg="darkolivegreen", fg="white", width=8, anchor="w").pack(side=tk.LEFT)
        road_noise_scale = tk.Scale(
            road_noise_frame, from_=0.0, to=1.0, resolution=0.1,
            orient=tk.HORIZONTAL, variable=self.road_noise_var,
            bg="darkolivegreen", fg="white", highlightthickness=0,
        )
        road_noise_scale.pack(side=tk.LEFT, fill=tk.X, expand=True)

        # === SEKCJA SKRZYŻOWAŃ (podobna do dopływów w rzece) ===
        road_crossroads_section = tk.LabelFrame(
            self.road_frame,
            text="🔀 Skrzyżowania i odnogi",
            bg="darkolivegreen",
            fg="#ffd166",
            font=("Arial", 9, "bold"),
        )
        road_crossroads_section.pack(fill=tk.X, padx=4, pady=(6, 4))
        
        tk.Label(
            road_crossroads_section,
            text="Aby dodać skrzyżowanie:\n1. Zaznacz heks na drodze (LPM)\n2. Kliknij 'Dodaj skrzyżowanie'\n3. Kliknij sąsiedni heks (kierunek odnogi)",
            bg="darkolivegreen",
            fg="#d4f2bf",
            font=("Arial", 8),
            anchor="w",
            justify="left",
            wraplength=190,
        ).pack(fill=tk.X, padx=4, pady=(2, 4))
        
        self.add_crossroads_button = tk.Button(
            road_crossroads_section,
            text="➕ Dodaj skrzyżowanie",
            command=self._start_crossroads_mode,
            bg="#5a4a3a",
            fg="white",
            state=tk.DISABLED,
        )
        self.add_crossroads_button.pack(fill=tk.X, padx=4, pady=(0, 4))
        
        # Status skrzyżowania
        self.road_crossroads_status_var = tk.StringVar(value="")
        self.road_crossroads_status_label = tk.Label(
            road_crossroads_section,
            textvariable=self.road_crossroads_status_var,
            bg="darkolivegreen",
            fg="#ffd166",
            font=("Arial", 8, "italic"),
            anchor="w",
            wraplength=190,
        )
        self.road_crossroads_status_label.pack(fill=tk.X, padx=4, pady=(0, 2))

        # === PRZYCISKI AKCJI (jak w rzece) ===
        road_buttons_frame = tk.Frame(self.road_frame, bg="darkolivegreen")
        road_buttons_frame.pack(fill=tk.X, padx=4, pady=(4, 0))

        self.road_generate_button = tk.Button(
            road_buttons_frame, text="🛤️ Generuj drogę",
            command=self.generate_road_path,
            bg="#4a6a4a", fg="white", state=tk.DISABLED,
            font=("Arial", 9, "bold"),
        )
        self.road_generate_button.pack(fill=tk.X, pady=1)

        self.road_undo_button = tk.Button(
            road_buttons_frame, text="⬅ Cofnij ostatni",
            command=self.road_pop_last_hex,
            bg="#6a5a4a", fg="white", state=tk.DISABLED,
        )
        self.road_undo_button.pack(fill=tk.X, pady=1)

        self.road_clear_button = tk.Button(
            road_buttons_frame, text="Wyczyść ścieżkę",
            command=self.clear_road_path,
            bg="#8a4a4a", fg="white", state=tk.DISABLED,
        )
        self.road_clear_button.pack(fill=tk.X, pady=(0, 1))

        # === SEKCJA MODYFIKACJI ISTNIEJĄCEJ DROGI ===
        road_modify_section = tk.LabelFrame(
            self.road_frame,
            text="🔧 Modyfikuj istniejącą drogę",
            bg="darkolivegreen",
            fg="#7dd3fc",
            font=("Arial", 9, "bold"),
        )
        road_modify_section.pack(fill=tk.X, padx=4, pady=(6, 4))
        
        tk.Label(
            road_modify_section,
            text="Zaznacz heks z wygenerowaną drogą:",
            bg="darkolivegreen",
            fg="#d4f2bf",
            font=("Arial", 8),
            anchor="w",
            wraplength=190,
        ).pack(fill=tk.X, padx=4, pady=(2, 4))
        
        # Przyciski skrzyżowań
        road_junction_frame = tk.Frame(road_modify_section, bg="darkolivegreen")
        road_junction_frame.pack(fill=tk.X, padx=4, pady=(0, 4))
        
        self.road_junction_t_button = tk.Button(
            road_junction_frame,
            text="⊥ Skrzyżowanie T",
            command=self._add_junction_t,
            bg="#5a5a3a",
            fg="white",
            state=tk.DISABLED,
        )
        self.road_junction_t_button.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(0, 2))
        
        self.road_junction_x_button = tk.Button(
            road_junction_frame,
            text="✚ Skrzyżowanie X",
            command=self._add_junction_x,
            bg="#5a5a3a",
            fg="white",
            state=tk.DISABLED,
        )
        self.road_junction_x_button.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(2, 0))
        
        self.road_continue_button = tk.Button(
            road_modify_section,
            text="↪ Kontynuuj drogę z heksu",
            command=self._continue_road_from_hex,
            bg="#1f4a6b",
            fg="white",
            state=tk.DISABLED,
        )
        self.road_continue_button.pack(fill=tk.X, padx=4, pady=(0, 4))
        
        # Status modyfikacji
        self.road_modify_status_var = tk.StringVar(value="")
        self.road_modify_status_label = tk.Label(
            road_modify_section,
            textvariable=self.road_modify_status_var,
            bg="darkolivegreen",
            fg="#7dd3fc",
            font=("Arial", 8, "italic"),
            anchor="w",
            wraplength=190,
        )
        self.road_modify_status_label.pack(fill=tk.X, padx=4, pady=(0, 2))

        tk.Label(
            self.road_frame,
            text="LPM dodaje heks, PPM dodaje odnogę.",
            bg="darkolivegreen",
            fg="#d4f2bf",
            font=("Arial", 8, "italic"),
            anchor="w",
            wraplength=190,
        ).pack(fill=tk.X, pady=(2, 0))

        self._set_road_section_visibility(False)

        # === SEKCJA JEZIOR ===
        self._lake_section_expanded = False
        
        self.lake_section_toggle_button = tk.Button(
            self.upper_frame,
            text="[+] Jeziora (beta)",
            command=self.toggle_lake_section_visibility,
            bg="#1a4d5c",
            fg="white",
            activebackground="#2a5d6c",
            activeforeground="white",
            anchor="w",
            font=("Arial", 9, "bold"),
        )
        self.lake_section_toggle_button.pack(fill=tk.X, padx=5, pady=2)

        # Kontener na rozwijaną sekcję jezior
        self.lake_section_container = tk.Frame(self.upper_frame, bg="darkolivegreen")
        # Domyślnie ukryte - nie pakujemy

        self.lake_frame = tk.Frame(
            self.lake_section_container, bg="darkolivegreen"
        )
        self.lake_frame.pack(fill=tk.X, pady=(2, 0))

        # Przycisk trybu
        self.toggle_lake_mode_button = tk.Button(
            self.lake_frame, text="Włącz tryb jezior",
            command=self.toggle_lake_mode,
            bg="#1a4d5c", fg="white",
            activebackground="#2a5d6c", activeforeground="white",
        )
        self.toggle_lake_mode_button.pack(fill=tk.X, padx=4, pady=2)

        # Status
        lake_status_label = tk.Label(
            self.lake_frame, textvariable=self.lake_status_var,
            bg="darkolivegreen", fg="#b3e5fc", font=("Arial", 8),
        )
        lake_status_label.pack(fill=tk.X, padx=4, pady=(0, 4))

        # Rozmiar jeziora
        lake_size_frame = tk.Frame(self.lake_frame, bg="darkolivegreen")
        lake_size_frame.pack(fill=tk.X, padx=4, pady=2)
        tk.Label(lake_size_frame, text="Rozmiar:", bg="darkolivegreen", fg="white", width=12, anchor="w").pack(side=tk.LEFT)
        lake_size_combo = ttk.Combobox(
            lake_size_frame, textvariable=self.lake_size_var,
            values=["mały staw", "średnie", "duże zbiornik"], state="readonly", width=18,
        )
        lake_size_combo.pack(side=tk.LEFT, fill=tk.X, expand=True)

        # Auto-łączenie zawsze aktywne (bez UI)

        # Szybkie generowanie układów (auto Y / 1+6)
        lake_quick_frame = tk.LabelFrame(
            self.lake_frame,
            text="Szybkie generowanie",
            bg="darkolivegreen",
            fg="#ffd166",
            font=("Arial", 9, "bold"),
        )
        lake_quick_frame.pack(fill=tk.X, padx=4, pady=(0, 6))

        lake_quick_hint = tk.Label(
            lake_quick_frame,
            text="Wybierz heks środka, potem kliknij przycisk:",
            bg="darkolivegreen",
            fg="#b3e5fc",
            font=("Arial", 8),
            anchor="w",
        )
        lake_quick_hint.pack(fill=tk.X, padx=4, pady=(2, 2))

        self.lake_quick_single_btn = tk.Button(
            lake_quick_frame,
            text="⚡ Generuj single (1 heks)",
            command=self.quick_generate_lake_single,
            bg="#0d7377",
            fg="white",
            activebackground="#14a085",
            activeforeground="white",
        )
        self.lake_quick_single_btn.pack(fill=tk.X, padx=4, pady=(0, 2))

        self.lake_quick_y_btn = tk.Button(
            lake_quick_frame,
            text="⚡ Generuj Y (3 heksy)",
            command=self.quick_generate_lake_y,
            bg="#0d7377",
            fg="white",
            activebackground="#14a085",
            activeforeground="white",
        )
        self.lake_quick_y_btn.pack(fill=tk.X, padx=4, pady=(0, 2))

        self.lake_quick_7_btn = tk.Button(
            lake_quick_frame,
            text="⚡ Generuj 1+6 (7 heksów)",
            command=self.quick_generate_lake_1plus6,
            bg="#0d7377",
            fg="white",
            activebackground="#14a085",
            activeforeground="white",
        )
        self.lake_quick_7_btn.pack(fill=tk.X, padx=4, pady=(0, 2))

        # Przyciski akcji
        lake_actions = tk.Frame(self.lake_frame, bg="darkolivegreen")
        lake_actions.pack(fill=tk.X, padx=4, pady=(0, 4))

        # Regeneracja jezior przeniesiona poza panel (brak przycisku w UI).

        self._set_lake_section_visibility(False)
        self._update_lake_ui_state()

        # === SEKCJA TERENU (ROZWIJANA) ===
        self._terrain_expanded = False
        self.terrain_toggle_button = tk.Button(
            self.upper_frame,
            text="[+] Rodzaje terenu",
            command=self._toggle_terrain_section,
            bg="#4f2a12", fg="white",
            activebackground="#5f3a22", activeforeground="white",
            font=("Arial", 9, "bold"), anchor="w",
        )
        self.terrain_toggle_button.pack(fill=tk.X, padx=5, pady=2)

        # Kontener na rozwijaną zawartość
        self.terrain_frame = tk.Frame(self.upper_frame, bg="darkolivegreen")
        # Domyślnie ukryte - nie pakujemy

        self.current_brush = None
        self.terrain_buttons = {}

        for terrain_key in TERRAIN_TYPES.keys():
            btn = tk.Button(
                self.terrain_frame,
                text=terrain_key.replace("_", " ").title(),
                width=16,
                bg="saddlebrown",
                fg="white",
                activebackground="saddlebrown",
                activeforeground="white",
                command=lambda k=terrain_key: self.toggle_brush(k)
            )
            btn.pack(padx=4, pady=1, fill=tk.X)
            self.terrain_buttons[terrain_key] = btn

        # === TEKSTURY TERENU PŁASKIEGO ===
        self.flat_texture_status_var = tk.StringVar(value="Aktywny wzór: brak")
        flat_texture_button = tk.Button(
            self.upper_frame,
            text="Tekstury terenu płaskiego (Ctrl+Shift+F)",
            command=self.open_flat_texture_window,
            bg="forestgreen",
            fg="white",
            activebackground="forestgreen",
            activeforeground="white",
            anchor="w",
            font=("Arial", 9, "bold")
        )
        flat_texture_button.pack(padx=5, pady=2, fill=tk.X)

        # === PUNKTY KLUCZOWE ===
        self.add_key_point_button = tk.Button(
            self.upper_frame,
            text="Dodaj punkt kluczowy",
            command=self.add_key_point_dialog,
            bg="saddlebrown", fg="white",
            activebackground="saddlebrown", activeforeground="white"
        )
        self.add_key_point_button.pack(padx=5, pady=2, fill=tk.X)

        # === PUNKTY ZRZUTU ===
        self.add_spawn_point_button = tk.Button(
            self.upper_frame,
            text="Dodaj punkt wystawienia",
            command=self.add_spawn_point_dialog,
            bg="saddlebrown", fg="white",
            activebackground="saddlebrown", activeforeground="white"
        )
        self.add_spawn_point_button.pack(padx=5, pady=2, fill=tk.X)

        # === RESET HEKSU ===
        self.reset_hex_button = tk.Button(
            self.upper_frame,
            text="Resetuj wybrany heks",
            command=self.reset_selected_hex,
            bg="saddlebrown", fg="white",
            activebackground="saddlebrown", activeforeground="white"
        )
        self.reset_hex_button.pack(padx=5, pady=2, fill=tk.X)

        # === EKSPORT ŻETONÓW ===
        self.export_tokens_button = tk.Button(
            self.upper_frame,
            text="Eksportuj rozmieszczenie żetonów",
            command=self.export_start_tokens,
            bg="saddlebrown", fg="white", activebackground="saddlebrown", activeforeground="white"
        )
        self.export_tokens_button.pack(padx=5, pady=2, fill=tk.X)

        # === DOLNA CZĘŚĆ: Panel informacyjny ===
        self.lower_frame = tk.Frame(self.main_paned, bg="darkolivegreen")
        # Dolny panel pokazuje tylko informacje o aktywnym heksie, więc trzymamy go kompaktowo
        self.main_paned.add(self.lower_frame, minsize=230, stretch="never")

        # === PANEL INFORMACYJNY ===
        self.build_info_panel_in_frame(self.lower_frame)
        self.root.update_idletasks()
        try:
            self.main_paned.paneconfigure(self.lower_frame, height=250)
        except Exception:
            pass

        # === CANVAS MAPY ===
        self.build_map_canvas()
        self._update_map_info_label()

    def _toggle_river_advanced_settings(self) -> None:
        """Przełącza widoczność zaawansowanych ustawień rzeki."""
        self._river_advanced_expanded = not self._river_advanced_expanded
        if self._river_advanced_expanded:
            self.river_advanced_frame.pack(fill=tk.X, pady=(0, 4))
            self.river_advanced_toggle.config(text="[-] Szczegółowe ustawienia")
        else:
            self.river_advanced_frame.pack_forget()
            self.river_advanced_toggle.config(text="[+] Szczegółowe ustawienia")

    def _toggle_terrain_section(self) -> None:
        """Przełącza widoczność sekcji rodzajów terenu."""
        self._terrain_expanded = not self._terrain_expanded
        if self._terrain_expanded:
            self.terrain_frame.pack(fill=tk.X, padx=5, pady=(2, 4), after=self.terrain_toggle_button)
            self.terrain_toggle_button.config(text="[-] Rodzaje terenu")
        else:
            self.terrain_frame.pack_forget()
            self.terrain_toggle_button.config(text="[+] Rodzaje terenu")

    def _apply_quick_river_preset(self) -> None:
        """Stosuje szybki preset rzeki, ustawiając wszystkie parametry naraz."""
        preset_name = self.river_quick_preset_var.get()
        preset = RIVER_QUICK_PRESETS.get(preset_name)
        if not preset:
            return
        
        # Aktualizuj opis
        description = preset.get("description", "")
        self.river_quick_preset_desc.config(text=description)
        
        # Ustaw poszczególne profile
        size_name = preset.get("size", "Mała rzeka")
        curvature_name = preset.get("curvature", "Łagodna")
        bank_name = preset.get("bank", "Stabilny brzeg")
        
        # Aktualizuj combobox'y
        self.river_size_profile_var.set(size_name)
        self.river_curvature_profile_var.set(curvature_name)
        self.river_bank_profile_var.set(bank_name)
        
        # Zastosuj profile
        self._apply_river_profiles()
        
        self.set_status(f"Zastosowano preset: {preset_name}")

    def _update_river_seed_label(self) -> None:
        try:
            seed_value = int(self.river_seed_var.get())
        except (TypeError, ValueError):
            seed_value = random.randint(0, 9999)
            self.river_seed_var.set(seed_value)
        self.river_seed_label_var.set(f"Seed: {seed_value}")

    def _randomize_river_seed(self) -> None:
        self.river_seed_var.set(random.randint(0, 9999))
        self._update_river_seed_label()
        self._update_river_preview_image()

    def _apply_river_profiles(self) -> None:
        params = dict(self._current_river_params)

        size_label = (self.river_size_profile_var.get() or CUSTOM_PROFILE_LABEL).strip()
        size_cfg = RIVER_SIZE_OPTIONS.get(size_label)
        if size_cfg:
            grid_size = int(size_cfg.get("grid_size", DEFAULT_HEX_TEXTURE_GRID_SIZE))
            base_bank_offset = float(size_cfg.get("bank_offset", DEFAULT_BANK_OFFSET))
            base_bank_variation = float(size_cfg.get("bank_variation", DEFAULT_BANK_VARIATION))
        else:
            grid_size = int(params.get("grid_size", DEFAULT_HEX_TEXTURE_GRID_SIZE))
            try:
                grid_size = int(self.river_grid_var.get())
            except (TypeError, ValueError):
                pass
            try:
                base_bank_offset = float(self.river_bank_offset_var.get())
            except (tk.TclError, TypeError, ValueError):
                base_bank_offset = float(params.get("base_bank_offset", DEFAULT_BANK_OFFSET))
            try:
                base_bank_variation = float(self.river_bank_variation_var.get())
            except (tk.TclError, TypeError, ValueError):
                base_bank_variation = float(params.get("base_bank_variation", DEFAULT_BANK_VARIATION))

        curvature_label = (self.river_curvature_profile_var.get() or CUSTOM_PROFILE_LABEL).strip()
        curvature_cfg = RIVER_CURVATURE_OPTIONS.get(curvature_label)
        if curvature_cfg:
            shape_preference = curvature_cfg.get("shape_preference", "auto")
            shape_strength = float(curvature_cfg.get("shape_strength", 0.5))
            noise_amplitude = float(curvature_cfg.get("noise_amplitude", 0.0))
            noise_frequency = float(curvature_cfg.get("noise_frequency", 2.0))
        else:
            shape_preference = str(params.get("shape_preference", "auto"))
            try:
                shape_strength = float(self.river_strength_var.get())
            except (tk.TclError, TypeError, ValueError):
                shape_strength = float(params.get("shape_strength", 0.5))
            try:
                noise_amplitude = float(self.river_noise_var.get())
            except (tk.TclError, TypeError, ValueError):
                noise_amplitude = float(params.get("noise_amplitude", 0.0))
            try:
                noise_frequency = float(self.river_frequency_var.get())
            except (tk.TclError, TypeError, ValueError):
                noise_frequency = float(params.get("noise_frequency", 2.0))

        bank_label = (self.river_bank_profile_var.get() or CUSTOM_PROFILE_LABEL).strip()
        bank_cfg = RIVER_BANK_OPTIONS.get(bank_label)
        if bank_cfg:
            bank_offset = base_bank_offset * float(bank_cfg.get("offset_multiplier", 1.0))
            bank_variation = (
                base_bank_variation * float(bank_cfg.get("variation_multiplier", 1.0))
                + float(bank_cfg.get("variation_add", 0.0))
            )
        else:
            try:
                bank_offset = float(self.river_bank_offset_var.get())
            except (tk.TclError, TypeError, ValueError):
                bank_offset = float(params.get("bank_offset", base_bank_offset))
            try:
                bank_variation = float(self.river_bank_variation_var.get())
            except (tk.TclError, TypeError, ValueError):
                bank_variation = float(params.get("bank_variation", base_bank_variation))

        if grid_size not in HEX_TEXTURE_GRID_OPTIONS:
            grid_size = DEFAULT_HEX_TEXTURE_GRID_SIZE
        bank_offset = max(0.5, min(3.5, bank_offset))
        bank_variation = max(0.0, min(0.9, bank_variation))
        shape_strength = max(0.0, min(1.0, shape_strength))
        noise_amplitude = max(0.0, min(3.0, noise_amplitude))
        noise_frequency = max(0.1, min(6.0, noise_frequency))

        export_size = HEX_TEXTURE_EXPORT_SIZES.get(grid_size)
        self.river_grid_var.set(str(grid_size))
        if export_size:
            self.river_grid_info_var.set(f"Siatka: {grid_size} ({export_size} px)")
        else:
            self.river_grid_info_var.set(f"Siatka: {grid_size}")

        shape_label = RIVER_SHAPE_LABELS.get(shape_preference, RIVER_SHAPE_LABELS["auto"])
        self.river_shape_var.set(shape_label)
        self.river_strength_var.set(round(shape_strength, 3))
        self.river_noise_var.set(round(noise_amplitude, 3))
        self.river_frequency_var.set(round(noise_frequency, 3))
        self.river_bank_offset_var.set(round(bank_offset, 3))
        self.river_bank_variation_var.set(round(bank_variation, 3))
        self.river_large_mode_var.set(False)

        params.update(
            grid_size=grid_size,
            shape_preference=shape_preference,
            shape_strength=shape_strength,
            noise_amplitude=noise_amplitude,
            noise_frequency=noise_frequency,
            base_bank_offset=base_bank_offset,
            base_bank_variation=base_bank_variation,
            bank_offset=bank_offset,
            bank_variation=bank_variation,
        )
        self._current_river_params = params
        self._update_river_preview_image()

    def _apply_tributary_profiles(self) -> None:
        params = dict(self._current_tributary_params)

        size_label = (self.tributary_size_profile_var.get() or CUSTOM_PROFILE_LABEL).strip()
        size_cfg = TRIBUTARY_SIZE_OPTIONS.get(size_label)
        if size_cfg:
            bank_offset_scale = float(size_cfg.get("bank_offset_scale", 0.8))
            variation_scale = float(size_cfg.get("variation_scale", 1.0))
        else:
            bank_offset_scale = float(params.get("bank_offset_scale", 0.8))
            variation_scale = float(params.get("variation_scale", 1.0))

        character_label = (self.tributary_character_profile_var.get() or CUSTOM_PROFILE_LABEL).strip()
        character_cfg = TRIBUTARY_CHARACTER_OPTIONS.get(character_label)
        if character_cfg:
            shape_key = character_cfg.get("shape", "curve")
            shape_strength = float(character_cfg.get("shape_strength", 0.6))
            noise_amplitude = float(character_cfg.get("noise_amplitude", 0.0))
            noise_frequency = float(character_cfg.get("noise_frequency", 2.5))
            direction_mode = character_cfg.get("shape_direction_mode", "auto")
        else:
            shape_label = (self.river_tributary_shape_var.get() or TRIBUTARY_SHAPE_LABELS["curve"]).strip()
            shape_key = TRIBUTARY_SHAPE_LABEL_TO_KEY.get(shape_label, str(params.get("shape", "curve")))
            try:
                shape_strength = float(self.river_tributary_strength_var.get())
            except (tk.TclError, TypeError, ValueError):
                shape_strength = float(params.get("shape_strength", 0.6))
            try:
                noise_amplitude = float(self.river_tributary_noise_var.get())
            except (tk.TclError, TypeError, ValueError):
                noise_amplitude = float(params.get("noise_amplitude", 0.0))
            try:
                noise_frequency = float(self.river_tributary_frequency_var.get())
            except (tk.TclError, TypeError, ValueError):
                noise_frequency = float(params.get("noise_frequency", 2.5))
            dir_label = (self.river_tributary_direction_var.get() or TRIBUTARY_DIRECTION_LABELS["auto"]).strip()
            direction_mode = TRIBUTARY_DIRECTION_LABEL_TO_KEY.get(dir_label, str(params.get("shape_direction_mode", "auto")))

        shape_strength = max(0.0, min(1.0, shape_strength))
        noise_amplitude = max(0.0, min(3.0, noise_amplitude))
        noise_frequency = max(0.1, min(6.0, noise_frequency))
        if direction_mode not in TRIBUTARY_DIRECTION_LABELS:
            direction_mode = "auto"

        self.river_tributary_shape_var.set(TRIBUTARY_SHAPE_LABELS.get(shape_key, TRIBUTARY_SHAPE_LABELS["curve"]))
        self.river_tributary_strength_var.set(round(shape_strength, 3))
        self.river_tributary_noise_var.set(round(noise_amplitude, 3))
        self.river_tributary_frequency_var.set(round(noise_frequency, 3))
        self.river_tributary_direction_var.set(TRIBUTARY_DIRECTION_LABELS[direction_mode])

        params.update(
            bank_offset_scale=bank_offset_scale,
            variation_scale=variation_scale,
            shape=shape_key,
            shape_strength=shape_strength,
            noise_amplitude=noise_amplitude,
            noise_frequency=noise_frequency,
            shape_direction_mode=direction_mode,
        )
        self._current_tributary_params = params
        self._update_river_preview_image()

    def _on_tributary_entry_change(self, *_event: object) -> None:
        entry_label = (self.tributary_entry_profile_var.get() or "").strip()
        entry_cfg = TRIBUTARY_ENTRY_OPTIONS.get(entry_label)
        if not entry_cfg:
            return

        self.river_tributary_entry_var.set(entry_label)
        join_ratio = entry_cfg.get("default_join")
        if join_ratio is not None:
            self.river_tributary_join_var.set(int(round(join_ratio * 100.0)))

        params = dict(self._current_tributary_params)
        params.update(entry_side=entry_cfg.get("entry_side"))
        self._current_tributary_params = params

    def open_map_configuration_dialog(self):
        dialog = tk.Toplevel(self.root)
        dialog.title("Konfiguracja mapy")
        dialog.transient(self.root)
        dialog.grab_set()
        dialog.configure(bg="darkolivegreen")
        dialog.resizable(False, False)

        current_cols = self.config.get("grid_cols", 56)
        current_rows = self.config.get("grid_rows", 40)
        current_hex = self.hex_size

        cols_var = tk.IntVar(value=current_cols)
        rows_var = tk.IntVar(value=current_rows)
        hex_var = tk.IntVar(value=current_hex)
        export_var = tk.BooleanVar(value=True)
        backup_var = tk.BooleanVar(value=True)

        main_frame = tk.Frame(dialog, bg="darkolivegreen", padx=12, pady=12)
        main_frame.pack(fill=tk.BOTH, expand=True)

        fields = tk.Frame(main_frame, bg="darkolivegreen")
        fields.pack(fill=tk.X)

        def build_spinbox(parent, label_text, var, limits):
            row = tk.Frame(parent, bg="darkolivegreen")
            row.pack(fill=tk.X, pady=3)
            tk.Label(row, text=label_text, bg="darkolivegreen", fg="white", width=20, anchor="w").pack(side=tk.LEFT)
            spin = tk.Spinbox(
                row,
                from_=limits[0],
                to=limits[1],
                textvariable=var,
                width=6,
                justify="right"
            )
            spin.pack(side=tk.LEFT)
            return spin

        build_spinbox(fields, "Szerokość (kolumny)", cols_var, self.size_hard_limits["cols"])
        build_spinbox(fields, "Wysokość (wiersze)", rows_var, self.size_hard_limits["rows"])
        build_spinbox(fields, "Rozmiar heksa", hex_var, self.size_hard_limits["hex_size"])

        preset_frame = tk.Frame(main_frame, bg="darkolivegreen")
        preset_frame.pack(fill=tk.X, pady=(6, 0))

        def apply_preset(cols, rows, size):
            cols_var.set(cols)
            rows_var.set(rows)
            hex_var.set(size)

        tk.Label(preset_frame, text="Presety:", bg="darkolivegreen", fg="yellow").pack(side=tk.LEFT)
        tk.Button(preset_frame, text="Potyczka", command=lambda: apply_preset(30, 20, 28)).pack(side=tk.LEFT, padx=2)
        tk.Button(preset_frame, text="Standard", command=lambda: apply_preset(56, 40, 30)).pack(side=tk.LEFT, padx=2)
        tk.Button(preset_frame, text="Kampania", command=lambda: apply_preset(120, 80, 32)).pack(side=tk.LEFT, padx=2)

        flags_frame = tk.Frame(main_frame, bg="darkolivegreen")
        flags_frame.pack(fill=tk.X, pady=(10, 0))
        tk.Checkbutton(flags_frame, text="Eksportuj startowe żetony", variable=export_var, bg="darkolivegreen", fg="white", selectcolor="darkolivegreen").pack(anchor="w")
        tk.Checkbutton(flags_frame, text="Zrób kopię mapy przed zmianą", variable=backup_var, bg="darkolivegreen", fg="white", selectcolor="darkolivegreen").pack(anchor="w")

        info_var = tk.StringVar(value="")
        warning_var = tk.StringVar(value="")

        info_label = tk.Label(main_frame, textvariable=info_var, bg="darkolivegreen", fg="white", justify="left", wraplength=340)
        info_label.pack(fill=tk.X, pady=(10, 4))
        warning_label = tk.Label(main_frame, textvariable=warning_var, bg="darkolivegreen", fg="orange", justify="left", wraplength=340)
        warning_label.pack(fill=tk.X)

        buttons = tk.Frame(main_frame, bg="darkolivegreen")
        buttons.pack(fill=tk.X, pady=(12, 0))
        tk.Button(buttons, text="Anuluj", command=dialog.destroy, bg="saddlebrown", fg="white", width=10).pack(side=tk.RIGHT, padx=4)

        def update_preview():
            try:
                new_cols = int(cols_var.get())
                new_rows = int(rows_var.get())
                new_hex = int(hex_var.get())
            except (tk.TclError, ValueError):
                info_var.set("Nieprawidłowe wartości.")
                warning_var.set("")
                return

            preview = self._calculate_config_change_effects(new_cols, new_rows, new_hex)
            if preview["errors"]:
                info_var.set("Błędy: " + "; ".join(preview["errors"]))
                warning_var.set("")
                return
            info_var.set(preview["summary"])
            warning_var.set(preview["warning"])  # może być pusty

        def apply_changes():
            try:
                new_cols = int(cols_var.get())
                new_rows = int(rows_var.get())
                new_hex = int(hex_var.get())
            except (tk.TclError, ValueError):
                messagebox.showerror("Błąd", "Podano nieprawidłowe wartości.")
                return
            result = self._apply_map_configuration(
                new_cols,
                new_rows,
                new_hex,
                export_tokens=export_var.get(),
                make_backup=backup_var.get()
            )
            preview_canvas.tag_lower("neighbor_preview", "edge_band")
            if edge_sync_status_label is not None:
                status_text = (
                    f"Podgląd sąsiada: {entry['neighbor_id']} "
                    f"(aktywny pas: {local_band_total} pól, druga strona: {neighbor_band_total} pól"
                )
                if drawn and drawn != local_band_total:
                    status_text += f", podgląd koloru: {drawn}"
                elif not drawn:
                    status_text += ", podgląd koloru: brak"
                status_text += ")"
                edge_sync_status_label.config(
                    text=status_text,
                    fg="#b7f28d" if neighbor_band_total else "#f2d7d5",
                )
        if not (min_cols <= cols <= max_cols):
            errors.append(f"Kolumny poza zakresem ({min_cols}-{max_cols}).")
        if not (min_rows <= rows <= max_rows):
            errors.append(f"Wiersze poza zakresem ({min_rows}-{max_rows}).")
        if not (min_hex <= hex_size <= max_hex):
            errors.append(f"Rozmiar heksa poza zakresem ({min_hex}-{max_hex}).")

        soft_cols = self.size_soft_limits["cols"]
        soft_rows = self.size_soft_limits["rows"]
        soft_hex = self.size_soft_limits["hex_size"]

        if cols > soft_cols or rows > soft_rows:
            warnings.append("Duża siatka może wydłużyć ładowanie i ruch AI.")
        if hex_size > soft_hex:
            warnings.append("Duże heksy mogą nie zmieścić się na ekranie.")

        allowed_hexes = self._build_allowed_hex_ids(cols, rows)
        current_hexes = set(self.hex_data.keys())
        removed_hexes = current_hexes - allowed_hexes

        tokens_removed = sum(1 for hid in removed_hexes if self.hex_data.get(hid, {}).get("token"))
        key_points_removed = sum(1 for hid in self.key_points if hid not in allowed_hexes)
        spawn_removed = 0
        for nation, hex_list in self.spawn_points.items():
            spawn_removed += sum(1 for hid in hex_list if hid not in allowed_hexes)

        min_move_mod = min(value.get("move_mod", 0) for value in TERRAIN_TYPES.values())
        estimated_range = max(6, int(12 / max(1, 1 + min_move_mod)))

        required_width, required_height = self._estimate_canvas_size(cols, rows, hex_size)
        current_width = getattr(self, "world_width", required_width)
        current_height = getattr(self, "world_height", required_height)
        if required_width > current_width or required_height > current_height:
            warnings.append("Aktualne tło jest za małe – zostanie zastąpione jednolitym tłem.")

        total_hexes = len(allowed_hexes)
        summary_lines = [
            f"Nowa siatka: {cols} × {rows} ({total_hexes} heksów).",
            f"Szacowany zasięg kawalerii przy płaskim terenie: ok. {estimated_range} heksów.",
        ]
        if removed_hexes:
            summary_lines.append(
                f"Do wyzerowania: {len(removed_hexes)} heksów (żetony: {tokens_removed}, spawn: {spawn_removed}, key pointy: {key_points_removed})."
            )
        else:
            summary_lines.append("Brak utraty obecnych danych.")
        if cols == self.config.get("grid_cols") and rows == self.config.get("grid_rows") and hex_size == self.hex_size:
            summary_lines.append("Parametry bez zmian.")

        return {
            "summary": "\n".join(summary_lines),
            "warning": "\n".join(warnings),
            "errors": errors,
            "removed": {
                "hexes": len(removed_hexes),
                "tokens": tokens_removed,
                "spawn": spawn_removed,
                "key_points": key_points_removed,
            },
            "allowed_hexes": allowed_hexes,
            "canvas_size": (required_width, required_height),
        }

    def _estimate_canvas_size(self, cols: int, rows: int, hex_size: int) -> tuple[int, int]:
        horizontal_spacing = 1.5 * hex_size
        width = int(hex_size * 2 + max(0, cols - 1) * horizontal_spacing + hex_size)
        hex_height = math.sqrt(3) * hex_size
        height = int((math.sqrt(3) / 2) * hex_size + rows * hex_height + hex_size)
        return max(200, width), max(200, height)

    def _build_allowed_hex_ids(self, cols: int, rows: int) -> set[str]:
        allowed = set()
        for col in range(max(0, cols)):
            for row in range(max(0, rows)):
                q = col
                r = row - (col // 2)
                allowed.add(f"{q},{r}")
        return allowed

    def _apply_background_metadata(self, meta: dict | None) -> None:
        if not meta:
            if self.map_image_path:
                self.background_info = {
                    "type": "image",
                    "path": to_rel(str(self.map_image_path))
                }
            else:
                self.background_info = {
                    "type": "solid",
                    "color": list(SOLID_BACKGROUND_COLOR)
                }
            return

        bg_type = meta.get("type")
        if bg_type == "image":
            raw_path = meta.get("path")
            resolved: Path | str | None
            if raw_path:
                if os.path.isabs(raw_path):
                    resolved = Path(raw_path)
                else:
                    resolved = ASSET_ROOT / raw_path
            else:
                resolved = None
            if resolved and Path(resolved).exists():
                abs_path = str(Path(resolved))
                self.map_image_path = abs_path
                self.config["map_image_path"] = abs_path
                self.background_info = {
                    "type": "image",
                    "path": to_rel(str(resolved))
                }
            else:
                self.map_image_path = None
                self.config["map_image_path"] = None
                self.background_info = {
                    "type": "solid",
                    "color": list(SOLID_BACKGROUND_COLOR)
                }
        elif bg_type == "solid":
            color = meta.get("color", list(SOLID_BACKGROUND_COLOR))
            if isinstance(color, tuple):
                color = list(color)
            self.background_info = {
                "type": "solid",
                "color": color
            }
            self.map_image_path = None
            self.config["map_image_path"] = None
        else:
            if self.map_image_path:
                self.background_info = {
                    "type": "image",
                    "path": to_rel(str(self.map_image_path))
                }
            else:
                self.background_info = {
                    "type": "solid",
                    "color": list(SOLID_BACKGROUND_COLOR)
                }

        width = meta.get("width") or meta.get("canvas_width")
        height = meta.get("height") or meta.get("canvas_height")
        if width and height:
            self.world_width, self.world_height = int(width), int(height)

    def _serialize_background_info(self) -> dict:
        info = dict(getattr(self, "background_info", {}))
        if not info:
            return {}
        if info.get("type") == "image":
            path_to_store = None
            if self.map_image_path:
                path_to_store = to_rel(str(self.map_image_path))
            elif info.get("path"):
                path_to_store = info["path"]
            if path_to_store:
                info["path"] = path_to_store
            else:
                info.pop("path", None)
        if info.get("type") == "solid":
            color = info.get("color", list(SOLID_BACKGROUND_COLOR))
            if isinstance(color, tuple):
                color = list(color)
            info["color"] = color
        width = getattr(self, "world_width", None)
        height = getattr(self, "world_height", None)
        if width:
            info["width"] = int(width)
        if height:
            info["height"] = int(height)
        return info

    def _apply_map_configuration(self, cols: int, rows: int, hex_size: int, *, export_tokens: bool, make_backup: bool) -> str | None:
        preview = self._calculate_config_change_effects(cols, rows, hex_size)
        if preview["errors"]:
            messagebox.showerror("Błąd konfiguracji", "\n".join(preview["errors"]))
            return None

        if cols == self.config.get("grid_cols") and rows == self.config.get("grid_rows") and hex_size == self.hex_size:
            return "Parametry mapy pozostają bez zmian."

        removed = preview["removed"]
        if any(removed.values()):
            if not messagebox.askyesno(
                "Potwierdzenie",
                (
                    "Zmiana rozmiaru zresetuje dane mapy.\n"
                    f"Wyzerowane zostaną wpisy dla {removed['hexes']} heksów, {removed['tokens']} żetonów, "
                    f"{removed['spawn']} punktów spawn i {removed['key_points']} punktów kluczowych. Kontynuować?"
                ),
            ):
                return None

        backup_path = None
        if make_backup:
            backup_path = self._create_map_backup()

        previous_auto_save = self.auto_save_enabled
        self.auto_save_enabled = False

        try:
            self.config["grid_cols"] = cols
            self.config["grid_rows"] = rows
            self.hex_size = hex_size

            self.hex_data = {}
            self.key_points = {}
            self.spawn_points = {}
            self.hex_tokens.clear()
            self.selected_hex = None

            required_width, required_height = preview["canvas_size"]
            self.bg_image = Image.new("RGB", (required_width, required_height), SOLID_BACKGROUND_COLOR)
            self.photo_bg = ImageTk.PhotoImage(self.bg_image)
            self.world_width, self.world_height = self.bg_image.size
            self.map_image_path = None
            self.canvas.config(scrollregion=(0, 0, self.world_width, self.world_height))
            self.config["map_image_path"] = None
            self.background_info = {
                "type": "solid",
                "color": list(SOLID_BACKGROUND_COLOR),
                "width": self.world_width,
                "height": self.world_height
            }

            if hasattr(self, "hex_info_label"):
                self.hex_info_label.config(text="Heks: brak")
            if hasattr(self, "terrain_info_label"):
                self.terrain_info_label.config(text="Teren: brak")
            if hasattr(self, "token_info_label"):
                self.token_info_label.config(text="Żeton: brak")
            if hasattr(self, "key_point_info_label"):
                self.key_point_info_label.config(text="")
            if hasattr(self, "spawn_point_info_label"):
                self.spawn_point_info_label.config(text="")
            self.canvas.delete("hover_zoom")

            self.draw_grid()
            self.save_data()
            if export_tokens:
                self.export_start_tokens(show_message=False)
            self.force_refresh_palette()
            self._update_map_info_label()
        finally:
            self.auto_save_enabled = previous_auto_save

        result_lines = [f"Zastosowano: {cols} × {rows}, hex {hex_size}."]
        if backup_path:
            result_lines.append(f"Backup zapisany jako: {backup_path.name}")
        result_lines.append("Mapa została zresetowana do domyślnej siatki.")
        return "\n".join(result_lines)

    def _create_map_backup(self) -> Path | None:
        source = Path(self.current_working_file)
        if not source.exists():
            return None
        timestamp = datetime.now().strftime("%Y%m%d-%H%M%S")
        backup_path = DATA_ROOT / f"map_data.json.bak-{timestamp}"
        try:
            shutil.copy2(source, backup_path)
        except Exception as exc:
            messagebox.showwarning("Backup", f"Nie udało się utworzyć kopii zapasowej: {exc}")
            return None
        self._trim_old_backups()
        return backup_path

    def _trim_old_backups(self, keep: int = 5) -> None:
        backups = sorted(DATA_ROOT.glob("map_data.json.bak-*"), reverse=True)
        for obsolete in backups[keep:]:
            try:
                obsolete.unlink()
            except OSError:
                pass

    def build_token_palette_in_frame(self, parent_frame):
        """Buduje paletę żetonów z filtrami w podanym frame"""
        palette_frame = tk.LabelFrame(parent_frame, text="Paleta żetonów", bg="darkolivegreen", fg="white",
                                     font=("Arial", 10, "bold"))
        # Kompaktowa paleta - nie zajmuje całej przestrzeni
        palette_frame.pack(fill=tk.X, padx=2, pady=2)
        
        # === FILTRY ===
        filters_frame = tk.Frame(palette_frame, bg="darkolivegreen")
        filters_frame.pack(fill=tk.X, padx=2, pady=2)
        
        # Checkbox unikalności
        self.uniqueness_var = tk.BooleanVar(value=True)
        uniqueness_cb = tk.Checkbutton(filters_frame, text="Unikalność", variable=self.uniqueness_var,
                                      bg="darkolivegreen", fg="white", selectcolor="darkolivegreen",
                                      command=self.toggle_uniqueness)
        uniqueness_cb.pack(side=tk.LEFT)
        
        # Filtry dowódcy (dropdown) - skalowalne rozwiązanie
        commanders_container = tk.Frame(palette_frame, bg="darkolivegreen", relief="sunken", bd=2)
        commanders_container.pack(fill=tk.X, padx=2, pady=3)
        
        tk.Label(commanders_container, text="🎖️ WYBÓR DOWÓDCY:", bg="darkolivegreen", fg="yellow", 
                font=("Arial", 10, "bold")).pack(side=tk.LEFT, padx=(5,10))
        
        # Pobierz wszystkich dowódców z indeksu dynamicznie
        commanders_list = ["Wszystkie"]
        if self.token_index:
            unique_commanders = set()
            for token in self.token_index:
                owner = token.get("owner", "")
                if owner:
                    # Wyciągnij numer dowódcy z formatu "5 (Niemcy)" -> "5"
                    commander_num = owner.split()[0] if owner else ""
                    if commander_num.isdigit():
                        unique_commanders.add(commander_num)
            
            # Sortuj dowódców i dodaj z opisem nacji
            for commander_num in sorted(unique_commanders):
                # Znajdź nację dla tego dowódcy
                nation = ""
                for token in self.token_index:
                    if token.get("owner", "").startswith(commander_num + " "):
                        nation = token.get("nation", "")
                        break
                commanders_list.append(f"Dow. {commander_num} ({nation})")
        
        # Dropdown dowódców
        self.commander_dropdown = ttk.Combobox(commanders_container, 
                                             textvariable=self.filter_commander, 
                                             values=commanders_list, 
                                             state="readonly", 
                                             width=20)
        self.commander_dropdown.pack(side=tk.LEFT, padx=5)
        self.commander_dropdown.bind("<<ComboboxSelected>>", self.on_commander_selected)
        
        # Ustaw domyślny wybór
        self.filter_commander.set("Wszystkie")
        
        # === LISTA ŻETONÓW ===
        # Kontener z przewijaniem - KOMPAKTOWA WYSOKOŚĆ
        tokens_container = tk.Frame(palette_frame, bg="darkolivegreen")
        tokens_container.pack(fill=tk.X, padx=2, pady=2)
        
        # Ustaw mniejszą wysokość dla kontenera żetonów (około 200px)
        self.tokens_canvas = tk.Canvas(tokens_container, bg="darkolivegreen", highlightthickness=0, height=200)
        tokens_scrollbar = tk.Scrollbar(tokens_container, orient="vertical", command=self.tokens_canvas.yview)
        self.token_palette_frame = tk.Frame(self.tokens_canvas, bg="darkolivegreen")
        
        self.tokens_canvas.create_window((0, 0), window=self.token_palette_frame, anchor="nw")
        self.tokens_canvas.configure(yscrollcommand=tokens_scrollbar.set)
        
        self.tokens_canvas.pack(side="left", fill="x")
        tokens_scrollbar.pack(side="right", fill="y")
        
        # Bind scroll
        self.token_palette_frame.bind('<Configure>', lambda e: self.tokens_canvas.configure(scrollregion=self.tokens_canvas.bbox("all")))
        
        # Mouse wheel scrolling dla palety żetonów
        def on_mouse_wheel(event):
            self.tokens_canvas.yview_scroll(int(-1*(event.delta/120)), "units")
        
        self.tokens_canvas.bind("<MouseWheel>", on_mouse_wheel)
        self.token_palette_frame.bind("<MouseWheel>", on_mouse_wheel)
        
        # Wypełnij paletę
        self.refresh_token_palette()

    def _update_map_info_label(self) -> None:
        if not hasattr(self, "map_info_label"):
            return
        cols_val = self.config.get("grid_cols")
        rows_val = self.config.get("grid_rows")
        size_val = self.hex_size
        try:
            cols_int = int(cols_val) if cols_val is not None else None
            rows_int = int(rows_val) if rows_val is not None else None
            size_int = int(size_val) if size_val is not None else None
        except (TypeError, ValueError):
            cols_int = rows_int = size_int = None

        if cols_int and rows_int and size_int:
            total = cols_int * rows_int
            self.map_info_label.config(
                text=(
                    f"Mapa: {cols_int} × {rows_int} heksów "
                    f"(łącznie {total}), rozmiar heksa: {size_int} px"
                )
            )
        else:
            self.map_info_label.config(text="Mapa: -- × -- heksów, rozmiar: --")

    def _update_map_info_label(self) -> None:
        if not hasattr(self, "map_info_label"):
            return
        cols = self.config.get("grid_cols")
        rows = self.config.get("grid_rows")
        size = self.hex_size
        try:
            cols_val = int(cols) if cols is not None else None
            rows_val = int(rows) if rows is not None else None
            size_val = int(size) if size is not None else None
        except (TypeError, ValueError):
            cols_val = rows_val = size_val = None

        if cols_val and rows_val and size_val:
            total = cols_val * rows_val
            self.map_info_label.config(
                text=(
                    f"Mapa: {cols_val} × {rows_val} heksów "
                    f"(łącznie {total}), rozmiar heksa: {size_val} px"
                )
            )
        else:
            self.map_info_label.config(text="Mapa: -- × -- heksów, rozmiar: --")

    def build_info_panel_in_frame(self, parent_frame):
        """Buduje panel informacyjny o wybranym heksie w podanym frame"""
        self.control_panel_frame = tk.Frame(parent_frame, bg="darkolivegreen", relief=tk.RIDGE, bd=3, height=260)
        # Panel z informacjami siedzi na dole i nie rozciąga się w pionie
        self.control_panel_frame.pack(side=tk.BOTTOM, fill=tk.X, expand=False, padx=2, pady=2)
        self.control_panel_frame.pack_propagate(False)
        
        tk.Label(
            self.control_panel_frame,
            text="Informacje o mapie i heksie",
            bg="darkolivegreen",
            fg="white",
            font=("Arial", 10, "bold")
        ).pack(pady=2)

        tools_frame = tk.Frame(self.control_panel_frame, bg="darkolivegreen")
        tools_frame.pack(side=tk.TOP, fill=tk.X, padx=5, pady=(4, 6))

        self.edit_texture_button = tk.Button(
            tools_frame,
            text="🎨 Edytuj wygląd heksa",
            command=self.open_selected_hex_texture_editor,
            bg="saddlebrown",
            fg="white",
            activebackground="saddlebrown",
            activeforeground="white"
        )
        self.edit_texture_button.pack(fill=tk.X)
        self.edit_texture_button.config(state=tk.DISABLED)

        # Kontener na informacje podstawowe
        basic_info_frame = tk.Frame(self.control_panel_frame, bg="darkolivegreen")
        basic_info_frame.pack(side=tk.TOP, fill=tk.BOTH, expand=True, padx=5, pady=2)

        self.hex_info_label = tk.Label(basic_info_frame, text="Heks: brak", bg="darkolivegreen", fg="white", font=("Arial", 9))
        self.hex_info_label.pack(anchor="w", pady=1)
        
        self.map_info_label = tk.Label(
            basic_info_frame,
            text="Mapa: -- × -- heksów, rozmiar: --",
            bg="darkolivegreen",
            fg="white",
            font=("Arial", 9)
        )
        self.map_info_label.pack(anchor="w", pady=1)

        self.terrain_info_label = tk.Label(basic_info_frame, text="Teren: brak", bg="darkolivegreen", fg="white", font=("Arial", 9))
        self.terrain_info_label.pack(anchor="w", pady=1)
        
        self.token_info_label = tk.Label(basic_info_frame, text="Żeton: brak", bg="darkolivegreen", fg="white", font=("Arial", 9))
        self.token_info_label.pack(anchor="w", pady=1)

        self.texture_info_label = tk.Label(basic_info_frame, text="Tekstura: domyślna", bg="darkolivegreen", fg="white", font=("Arial", 9))
        self.texture_info_label.pack(anchor="w", pady=1)

        self.flat_texture_info_label = tk.Label(basic_info_frame, text="Wzór płaski: brak", bg="darkolivegreen", fg="white", font=("Arial", 9))
        self.flat_texture_info_label.pack(anchor="w", pady=1)

    def build_map_canvas(self):
        """Buduje canvas mapy z przewijaniem"""
        self.canvas_frame = tk.Frame(self.root)
        self.canvas_frame.pack(fill=tk.BOTH, expand=True)

        self.canvas = tk.Canvas(self.canvas_frame, bg="white", cursor="cross")
        self.canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

        # Dodanie suwaka pionowego
        self.v_scrollbar = tk.Scrollbar(self.canvas_frame, orient=tk.VERTICAL, command=self.canvas.yview)
        self.v_scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

        # Przeniesienie poziomego suwaka do root
        self.h_scrollbar = tk.Scrollbar(self.root, orient=tk.HORIZONTAL, command=self.canvas.xview)
        self.h_scrollbar.pack(side=tk.BOTTOM, fill=tk.X)
        self.canvas.configure(xscrollcommand=self.h_scrollbar.set, yscrollcommand=self.v_scrollbar.set)

        # Bindowanie eventów
        self.canvas.bind("<Button-1>", self.on_canvas_click)
        self.canvas.bind("<Button-3>", self.on_canvas_right_click)  # PPM - usuń żeton
        self.canvas.bind("<B1-Motion>", self.on_canvas_drag)  # Przeciąganie żetonów
        self.canvas.bind("<ButtonRelease-1>", self.on_canvas_release)  # Koniec przeciągania
        self.canvas.bind("<B2-Motion>", self.do_pan)
        self.canvas.bind("<ButtonPress-2>", self.start_pan)
        self.canvas.bind("<Motion>", self.on_canvas_hover)
        
        # Bind klawiatury
        self.root.bind("<Delete>", self.delete_token_from_selected_hex)
        self.root.bind("<KeyPress-Shift_L>", self.enable_multi_placement)
        self.root.bind("<KeyRelease-Shift_L>", self.disable_multi_placement)
        self.root.bind("<Control-Shift-F>", self.toggle_flat_texture_window)
        self.root.focus_set()  # Aby klawiatura działała
        
        # Zmienne dla drag & drop
        self.drag_start_hex = None
        self.drag_token_data = None

    def refresh_token_palette(self):
        """Odświeża paletę żetonów według aktualnych filtrów"""
        print(f"🎨 Odświeżanie palety żetonów: {len(self.filtered_tokens)} do wyświetlenia")
        
        # Wyczyść poprzednie przyciski
        for widget in self.token_palette_frame.winfo_children():
            widget.destroy()
            
        if not self.filtered_tokens:
            # Pokaż komunikat jeśli brak żetonów
            no_tokens_label = tk.Label(self.token_palette_frame, 
                                     text="Brak żetonów\ndo wyświetlenia", 
                                     bg="darkolivegreen", fg="yellow", 
                                     font=("Arial", 10, "bold"))
            no_tokens_label.pack(pady=20)
            print("⚠️  Brak żetonów do wyświetlenia - dodano komunikat")
        else:
            # Utwórz przyciski dla przefiltrowanych żetonów
            created_buttons = 0
            for i, token in enumerate(self.filtered_tokens):
                try:
                    btn_frame = tk.Frame(self.token_palette_frame, bg="darkolivegreen")
                    btn_frame.pack(fill=tk.X, padx=2, pady=1)
                    
                    # Miniatura żetonu - napraw podwójną ścieżkę assets
                    img_path = fix_image_path(token["image"])
                    
                    if img_path.exists():
                        try:
                            img = Image.open(img_path).resize((32, 32))
                            img_tk = ImageTk.PhotoImage(img)
                            
                            # Skróć tekst przycisku
                            btn_text = token.get("label", token["id"])
                            if len(btn_text) > 20:
                                btn_text = btn_text[:17] + "..."
                            
                            btn = tk.Button(btn_frame, image=img_tk, text=btn_text,
                                           compound="left", anchor="w", 
                                           bg="saddlebrown", fg="white", relief="raised",
                                           command=lambda t=token: self.select_token_for_placement(t))
                            btn.image = img_tk  # Zachowaj referencję
                            btn.pack(fill=tk.X)
                            
                            # Dodaj tooltip z pełnymi informacjami
                            tooltip_text = f"ID: {token['id']}\nNacja: {token.get('nation', 'N/A')}\nTyp: {token.get('unitType', 'N/A')}\nRozmiar: {token.get('unitSize', 'N/A')}"
                            if 'combat_value' in token:
                                tooltip_text += f"\nWalka: {token['combat_value']}"
                            if 'price' in token:
                                tooltip_text += f"\nCena: {token['price']}"
                            
                            self.create_tooltip(btn, tooltip_text)
                            
                            # Zapamiętaj przycisk w tokenie dla późniejszego podświetlenia
                            token['_button'] = btn
                            created_buttons += 1
                            
                        except Exception as e:
                            print(f"❌ Błąd obrazu dla {token['id']}: {e}")
                            # Fallback dla uszkodzonych obrazów
                            btn = tk.Button(btn_frame, text=token.get("label", token["id"])[:20],
                                           bg="saddlebrown", fg="white", relief="raised",
                                           command=lambda t=token: self.select_token_for_placement(t))
                            btn.pack(fill=tk.X)
                            token['_button'] = btn
                            created_buttons += 1
                    else:
                        print(f"❌ Brak obrazu: {img_path}")
                        # Fallback dla brakujących obrazów
                        btn = tk.Button(btn_frame, text=f"❌ {token.get('label', token['id'])[:15]}",
                                       bg="red", fg="white", relief="raised",
                                       command=lambda t=token: self.select_token_for_placement(t))
                        btn.pack(fill=tk.X)
                        token['_button'] = btn
                        created_buttons += 1
                        
                except Exception as e:
                    print(f"❌ Błąd tworzenia przycisku dla {token.get('id', 'UNKNOWN')}: {e}")
            
            print(f"✅ Utworzono {created_buttons} przycisków żetonów")
        
        # Aktualizuj scroll region
        self.token_palette_frame.update_idletasks()
        self.tokens_canvas.configure(scrollregion=self.tokens_canvas.bbox("all"))
        print("📐 Zaktualizowano scroll region")

    def _scroll_upper_panel(self, event):
        if not hasattr(self, "upper_canvas"):
            return
        widget = getattr(event, "widget", None)
        if widget is getattr(self, "tokens_canvas", None) or widget is getattr(self, "token_palette_frame", None):
            return
        step = 0
        if hasattr(event, "delta") and event.delta:
            step = -1 if event.delta > 0 else 1
        elif getattr(event, "num", None) in (4, 5):
            step = -1 if event.num == 4 else 1
        if step:
            self.upper_canvas.yview_scroll(step, "units")
            return "break"

    def create_tooltip(self, widget, text):
        """Tworzy tooltip dla widgetu"""
        def show_tooltip(event):
            tooltip = tk.Toplevel(widget)
            tooltip.wm_overrideredirect(True)
            label = tk.Label(
                tooltip,
                text=text,
                background="lightyellow",
                relief="solid",
                borderwidth=1,
                font=("Arial", 8),
                justify="left",
                wraplength=280,
            )
            label.pack(ipadx=4, ipady=2)
            tooltip.update_idletasks()

            screen_w = widget.winfo_screenwidth()
            screen_h = widget.winfo_screenheight()
            width = tooltip.winfo_width()
            height = tooltip.winfo_height()

            x = event.x_root + 12
            y = event.y_root + 12
            if x + width > screen_w:
                x = event.x_root - width - 12
            if x < 0:
                x = 0
            if y + height > screen_h:
                y = event.y_root - height - 12
            if y < 0:
                y = 0

            tooltip.wm_geometry(f"+{x}+{y}")
            widget.tooltip = tooltip
            
        def hide_tooltip(event):
            if hasattr(widget, 'tooltip'):
                widget.tooltip.destroy()
                del widget.tooltip
                
        widget.bind("<Enter>", show_tooltip)
        widget.bind("<Leave>", hide_tooltip)

    def select_token_for_placement(self, token):
        """Wybiera żeton do wstawiania"""
        # Wyczyść poprzedni wybór
        if self.selected_token and '_button' in self.selected_token:
            try:
                self.selected_token['_button'].config(relief="raised", bg="saddlebrown")
            except tk.TclError:
                # Przycisk został usunięty podczas odświeżania palety, ignoruj błąd
                pass
            
        # Ustaw nowy wybór
        self.selected_token = token
        if '_button' in token:
            try:
                token['_button'].config(relief="sunken", bg="orange")
            except tk.TclError:
                # Przycisk został usunięty podczas odświeżania palety, ignoruj błąd
                pass
            
        print(f"🎯 Wybrano żeton: {token['id']} ({token.get('nation', 'N/A')})")

    def toggle_uniqueness(self):
        """Przełącza tryb unikalności żetonów"""
        self.uniqueness_mode = self.uniqueness_var.get()
        self.update_filtered_tokens()
        print(f"🔒 Tryb unikalności: {'ON' if self.uniqueness_mode else 'OFF'}")

    def set_commander_filter(self, commander):
        """Ustawia filtr konkretnego dowódcy"""
        self.filter_commander.set(commander)
        self.update_filtered_tokens()
        
        # Zaktualizuj przyciski dowódców
        for commander_name, btn in self.commander_buttons.items():
            if commander_name == commander:
                btn.config(relief="sunken", bg="orange")
            else:
                btn.config(relief="raised", bg="saddlebrown")
        
        print(f"�️  Ustawiono filtr dowódcy: {commander}")

    def enable_multi_placement(self, event):
        """Włącza tryb wielokrotnego wstawiania (Shift)"""
        self.multi_placement_mode = True
        print("⚡ Tryb wielokrotnego wstawiania: ON (Shift)")

    def disable_multi_placement(self, event):
        """Wyłącza tryb wielokrotnego wstawiania"""
        self.multi_placement_mode = False
        print("⚡ Tryb wielokrotnego wstawiania: OFF")

    def delete_token_from_selected_hex(self, event):
        """Usuwa żeton z zaznaczonego heksu (klawisz Delete)"""
        if self.selected_hex and self.selected_hex in self.hex_data:
            terrain = self.hex_data[self.selected_hex]
            if "token" in terrain:
                del terrain["token"]
                self.draw_grid()
                self.auto_save_and_export("usunięto żeton")
                print(f"Usunięto żeton z heksu {self.selected_hex}")
                self.update_filtered_tokens()  # Odśwież listę dostępnych żetonów

    def select_default_map_path(self):
        'Pozwala użytkownikowi wybrać nowe tło mapy.'
        file_path = filedialog.askopenfilename(
            title="Wybierz domyślną mapę",
            filetypes=[("Obrazy", "*.jpg *.png *.bmp"), ("Wszystkie pliki", "*.*")]
        )
        if file_path:
            self.map_image_path = file_path
            self.config["map_image_path"] = file_path
            self.background_info = {
                "type": "image",
                "path": to_rel(str(file_path))
            }
            self.load_map_image()
            messagebox.showinfo("Sukces", "Wybrano nową domyślną mapę.")
        else:
            messagebox.showinfo("Anulowano", "Nie wybrano nowej mapy.")

    def load_map_image(self):
        'Wczytuje obraz mapy jako tło i ustawia rozmiary.'
        bg_meta = getattr(self, "background_info", {})
        bg_type = bg_meta.get("type")

        if bg_type == "solid":
            color = tuple(bg_meta.get("color", list(SOLID_BACKGROUND_COLOR)))
            width = bg_meta.get("width") or getattr(self, "world_width", None)
            height = bg_meta.get("height") or getattr(self, "world_height", None)
            if not width or not height:
                width, height = self._estimate_canvas_size(
                    self.config.get("grid_cols"),
                    self.config.get("grid_rows"),
                    self.hex_size
                )
            self.world_width, self.world_height = int(width), int(height)
            self.bg_image = Image.new("RGB", (self.world_width, self.world_height), color)
            self.photo_bg = ImageTk.PhotoImage(self.bg_image)
            self.canvas.config(scrollregion=(0, 0, self.world_width, self.world_height))
            self.background_info = {
                "type": "solid",
                "color": list(color),
                "width": self.world_width,
                "height": self.world_height
            }
            self.draw_grid()
            return

        path_to_load = self.map_image_path
        if not path_to_load:
            raw_path = bg_meta.get("path")
            if raw_path:
                path_to_load = raw_path if os.path.isabs(raw_path) else ASSET_ROOT / raw_path

        try:
            if not path_to_load:
                raise FileNotFoundError("Brak ścieżki tła mapy")
            self.bg_image = Image.open(path_to_load).convert("RGB")
            self.map_image_path = str(path_to_load)
        except Exception as e:
            print(f"⚠️  Nie udało się załadować tła mapy: {e}")
            width, height = self._estimate_canvas_size(
                self.config.get("grid_cols"),
                self.config.get("grid_rows"),
                self.hex_size
            )
            self.world_width, self.world_height = width, height
            self.bg_image = Image.new("RGB", (width, height), SOLID_BACKGROUND_COLOR)
            self.photo_bg = ImageTk.PhotoImage(self.bg_image)
            self.canvas.config(scrollregion=(0, 0, width, height))
            self.background_info = {
                "type": "solid",
                "color": list(SOLID_BACKGROUND_COLOR),
                "width": width,
                "height": height
            }
            self.map_image_path = None
            self.config["map_image_path"] = None
            self.draw_grid()
            return

        self.world_width, self.world_height = self.bg_image.size
        self.photo_bg = ImageTk.PhotoImage(self.bg_image)
        # Ustaw obszar przewijania
        self.canvas.config(scrollregion=(0, 0, self.world_width, self.world_height))
        self.config["map_image_path"] = self.map_image_path
        self.background_info = {
            "type": "image",
            "path": to_rel(str(self.map_image_path)),
            "width": self.world_width,
            "height": self.world_height
        }
        # Rysuj ponownie siatkę
        self.draw_grid()

    def draw_grid(self):
        """Rysuje siatkę heksów i aktualizuje wyświetlane żetony."""
        self.canvas.delete("all")
        if getattr(self, "world_width", None) and getattr(self, "world_height", None):
            self.canvas.config(scrollregion=(0, 0, self.world_width, self.world_height))
        if not hasattr(self, 'photo_bg'):
            self.photo_bg = ImageTk.PhotoImage(Image.new("RGB", (1, 1), (255, 255, 255)))
        self.canvas.create_image(0, 0, anchor=tk.NW, image=self.photo_bg)
        self.hex_centers = {}
        s = self.hex_size
        hex_height = math.sqrt(3) * s
        horizontal_spacing = 1.5 * s
        grid_cols = self.config.get("grid_cols")
        grid_rows = self.config.get("grid_rows")
        self.canvas.image_store = []

        # GENERUJEMY SIATKĘ W UKŁADZIE OFFSETOWYM EVEN-Q (prostokąt)
        for col in range(grid_cols):
            for row in range(grid_rows):
                # Konwersja offset -> axial (even-q)
                q = col
                r = row - (col // 2)
                center_x = s + col * horizontal_spacing
                center_y = (s * math.sqrt(3) / 2) + row * hex_height
                if col % 2 == 1:
                    center_y += hex_height / 2
                if center_x + s > self.world_width or center_y + (s * math.sqrt(3) / 2) > self.world_height:
                    continue
                hex_id = f"{q},{r}"
                self.hex_centers[hex_id] = (center_x, center_y)

                # Dodanie domyślnych danych terenu płaskiego, jeśli brak danych
                if hex_id not in self.hex_data:
                    self.hex_data[hex_id] = {
                        "terrain_key": "teren_płaski",
                        "move_mod": 0,
                        "defense_mod": 0
                    }

                terrain = self.hex_data.get(hex_id, self.hex_defaults)
                texture_rel = terrain.get("texture")
                if texture_rel:
                    texture_image = self._get_hex_texture_image(texture_rel)
                    if texture_image:
                        self.canvas.create_image(center_x, center_y, image=texture_image)
                        self.canvas.image_store.append(texture_image)
                self.draw_hex(hex_id, center_x, center_y, s, terrain)

    # Rysowanie żetonów na mapie
        for hex_id, terrain in self.hex_data.items():
            token = terrain.get("token")
            if token and "image" in token and hex_id in self.hex_centers:
                # normalizuj slashy na wszelki wypadek
                token["image"] = token["image"].replace("\\", "/")
                img_path = fix_image_path(token["image"])
                
                if not img_path.exists():
                    print(f"[WARN] Missing token image: {img_path}")
                    continue          # pomijamy brakujący plik
                img = Image.open(img_path).resize((self.hex_size, self.hex_size))
                tk_img = ImageTk.PhotoImage(img)
                cx, cy = self.hex_centers[hex_id]
                self.canvas.create_image(cx, cy, image=tk_img)
                self.canvas.image_store.append(tk_img)

        # nakładka mgiełki dla punktów zrzutu
        for nation, hex_list in self.spawn_points.items():
            for hex_id in hex_list:
                self.draw_spawn_marker(nation, hex_id)

        # rysowanie znaczników kluczowych punktów
        for hex_id, kp in self.key_points.items():
            self.draw_key_point_marker(kp['type'], kp['value'], hex_id)

        if self.river_path:
            self._draw_river_path_overlay()

        # Overlay ścieżki drogi
        if self.road_path:
            self._draw_road_path_overlay()
        
        # Overlay ścieżki torów
        if self.railway_path or self.railway_junction_mode:
            self._draw_railway_overlay()
        
        # Overlay klastra jezior
        if self.lake_mode_active and self.lake_cluster:
            self._draw_lake_overlay()
        
        # Wizualizacja trybu skrzyżowania
        if self.road_crossroads_mode and self.selected_hex:
            self._draw_crossroads_overlay()

        # Wizualizacja trybu prostego dopływu
        if getattr(self, "_simple_tributary_mode", False):
            self._draw_simple_tributary_overlay()

        # Podświetlenie wybranego heksu
        if self.selected_hex is not None:
            self.highlight_hex(self.selected_hex)

    def draw_hex(self, hex_id, center_x, center_y, s, terrain=None):
        'Rysuje pojedynczy heksagon na canvasie wraz z tekstem modyfikatorów.'
        points = get_hex_vertices(center_x, center_y, s)
        self.canvas.create_polygon(points, outline="red", fill="", width=2, tags=hex_id)        # usuwamy poprzedni tekst
        self.canvas.delete(f"tekst_{hex_id}")
        # rysujemy modyfikatory tylko jeśli ten heks ma niestandardowe dane
        if hex_id in self.hex_data:
            move_mod = terrain.get('move_mod', 0)
            defense_mod = terrain.get('defense_mod', 0)
            tekst = f"M:{move_mod} D:{defense_mod}"
            self.canvas.create_text(
                center_x, center_y,
                text=tekst,
                fill="blue",
                font=("Arial", 10),
                anchor="center",
                tags=f"tekst_{hex_id}"
            )

    def draw_spawn_marker(self, nation, hex_id):
        """Rysuje prosty, wyraźny znacznik punktu wystawienia (kolorowa obwódka + litera nacji)."""
        if hex_id not in self.hex_centers:
            return
        cx, cy = self.hex_centers[hex_id]
        color_map = {"Polska": ("#ff5555", "P"), "Niemcy": ("#5555ff", "N")}
        outline, letter = color_map.get(nation, ("#ffffff", nation[:1].upper()))
        r_c = int(self.hex_size * 0.55)
        self.canvas.create_oval(
            cx - r_c, cy - r_c, cx + r_c, cy + r_c,
            outline=outline, width=3, tags=f"spawn_{nation}_{hex_id}"
        )
        self.canvas.create_text(
            cx, cy + self.hex_size * 0.60,
            text=letter,
            fill=outline,
            font=("Arial", 10, "bold"),
            tags=f"spawn_{nation}_{hex_id}"
        )

    def draw_key_point_marker(self, key_type, value, hex_id):
        """Rysuje kolorowy znacznik punktu kluczowego (kółko + skrót typu)."""
        if hex_id not in self.hex_centers:
            return
        cx, cy = self.hex_centers[hex_id]
        
        # Mapowanie typów na kolory i skróty (max 2 znaki)
        color_map = {
            "most": ("#FFD700", "Mo"),          # Złoty
            "miasto": ("#FF6B35", "Mi"),        # Pomarańczowy
            "węzeł komunikacyjny": ("#4ECDC4", "WK"),  # Turkusowy
            "fortyfikacja": ("#45B7D1", "Fo")   # Niebieski
        }
        
        outline, letter = color_map.get(key_type, ("#FFFF00", key_type[:2].upper()))
        
        # Rysuj kółko (mniejsze niż spawn points)
        r_c = int(self.hex_size * 0.45)
        self.canvas.create_oval(
            cx - r_c, cy - r_c, cx + r_c, cy + r_c,
            outline=outline, width=3, fill="",  # Bez wypełnienia, tylko obramowanie
            tags=f"key_point_{key_type}_{hex_id}"
        )
        
        # Rysuj skrót typu
        self.canvas.create_text(
            cx, cy,
            text=letter,
            fill="black",
            font=("Arial", 9, "bold"),
            tags=f"key_point_{key_type}_{hex_id}"
        )
        
        # Rysuj wartość pod kółkiem
        self.canvas.create_text(
            cx, cy + self.hex_size * 0.65,
            text=str(value),
            fill=outline,
            font=("Arial", 8, "bold"),
            tags=f"key_point_{key_type}_{hex_id}"
        )

    def get_clicked_hex(self, x, y):
        for hex_id, (cx, cy) in self.hex_centers.items():
            vertices = get_hex_vertices(cx, cy, self.hex_size)
            if point_in_polygon(x, y, vertices):
                return hex_id  # Zwracaj hex_id jako string "q,r"
        return None

    def on_canvas_click(self, event):
        """Obsługuje LPM na canvasie - wstawia żeton lub wybiera heks"""
        # Wyczyść stan przeciągania na wszelki wypadek
        self.drag_start_hex = None
        self.drag_token_data = None
        
        x = self.canvas.canvasx(event.x)
        y = self.canvas.canvasy(event.y)
        hex_id = self.get_clicked_hex(x, y)
        
        # Obsługa prostego trybu dopływu (przed innymi trybami)
        if hex_id and getattr(self, "_simple_tributary_mode", False):
            if self._handle_simple_tributary_click(hex_id):
                return
        
        if self.river_mode_active:
            if hex_id:
                self._river_handle_left_click(hex_id)
            return

        # Obsługa trybu drogi
        if self.road_mode_active:
            if hex_id:
                self._road_handle_left_click(hex_id)
            return

        # Obsługa trybu torów kolejowych
        if self.railway_mode_active:
            if hex_id:
                self._railway_handle_left_click(hex_id)
            return

        # Obsługa trybu jezior
        if self.lake_mode_active:
            if hex_id:
                self._lake_handle_left_click(hex_id)
            return

        if hex_id:
            # Jeśli mamy wybrany żeton do wstawienia
            if self.selected_token:
                self.place_token_on_hex_new(self.selected_token, hex_id)
                
                # Jeśli nie jest tryb wielokrotnego wstawiania, wyczyść wybór
                if not self.multi_placement_mode:
                    self.clear_token_selection_new()
                return
                
            # Kompatybilność z starym systemem
            if hasattr(self, 'selected_token_for_deployment') and self.selected_token_for_deployment:
                self.place_token_on_hex(self.selected_token_for_deployment, hex_id)
                self.clear_token_selection()
                return
                
            # Jeśli jest aktywny pędzel terenu
            if self.current_brush:
                q, r = map(int, hex_id.split(","))
                self.paint_hex((q, r), self.current_brush)
                return
                
            # Standardowe zaznaczenie heksu
            self.selected_hex = hex_id
            self.highlight_hex(hex_id)
            self.update_hex_info_display(hex_id)
        else:
            # Kliknięcie w pustą przestrzeń - wyczyść wybór żetonu
            if self.selected_token:
                self.clear_token_selection_new()
            elif hasattr(self, 'selected_token_for_deployment') and self.selected_token_for_deployment:
                self.clear_token_selection()
            self.edit_texture_button.config(state=tk.DISABLED)
            self.texture_info_label.config(text="Tekstura: domyślna")

    def on_canvas_right_click(self, event):
        """Obsługuje PPM na canvasie - usuwa żeton z heksu lub wybiera boki dla skrzyżowania"""
        x = self.canvas.canvasx(event.x)
        y = self.canvas.canvasy(event.y)
        hex_id = self.get_clicked_hex(x, y)

        # Tryb skrzyżowania - PPM na sąsiednim heksie przełącza bok
        if self.road_mode_active and self.road_crossroads_mode and hex_id:
            # Jeśli kliknięto na aktualnie wybrany heks - pokaż dialog
            if hex_id == self.selected_hex:
                self._show_crossroads_side_selector(hex_id)
                return
            
            # Jeśli kliknięto na sąsiedni heks - przełącz bok
            if self.selected_hex and self.selected_hex in self.road_path:
                if self._toggle_crossroads_neighbor(hex_id):
                    return

        if self.river_mode_active:
            self._river_handle_right_click(hex_id)
            return

        if self.railway_mode_active:
            self._railway_handle_right_click(hex_id)
            return
        
        if hex_id and hex_id in self.hex_data:
            terrain = self.hex_data[hex_id]
            if "token" in terrain:
                del terrain["token"]
                self.draw_grid()
                self.auto_save_and_export("usunięto żeton PPM")
                print(f"Usunięto żeton z heksu {hex_id}")
                self.update_filtered_tokens()  # Odśwież listę dostępnych żetonów

    def on_canvas_drag(self, event):
        """Obsługuje przeciąganie żetonów między heksami"""
        if self.river_mode_active:
            return
        if not self.drag_start_hex:
            # Rozpocznij przeciąganie jeśli kliknięto na heks z żetonem
            x = self.canvas.canvasx(event.x)
            y = self.canvas.canvasy(event.y)
            hex_id = self.get_clicked_hex(x, y)
            
            if hex_id and hex_id in self.hex_data:
                terrain = self.hex_data[hex_id]
                if "token" in terrain and not self.selected_token:  # Tylko jeśli nie ma wybranego żetonu do wstawienia
                    self.drag_start_hex = hex_id
                    self.drag_token_data = terrain["token"].copy()
                    print(f"Rozpoczęto przeciąganie żetonu z {hex_id}")

    def on_canvas_release(self, event):
        """Obsługuje zakończenie przeciągania żetonu"""
        if self.river_mode_active:
            return
        if self.drag_start_hex and self.drag_token_data:
            x = self.canvas.canvasx(event.x)
            y = self.canvas.canvasy(event.y)
            target_hex = self.get_clicked_hex(x, y)
            
            if target_hex and target_hex != self.drag_start_hex:
                # Sprawdź czy docelowy heks jest pusty
                if target_hex not in self.hex_data or "token" not in self.hex_data[target_hex]:
                    # Przenieś żeton
                    if target_hex not in self.hex_data:
                        self.hex_data[target_hex] = {
                            "terrain_key": "teren_płaski",
                            "move_mod": 0,
                            "defense_mod": 0
                        }
                    
                    # Dodaj żeton do docelowego heksu
                    self.hex_data[target_hex]["token"] = self.drag_token_data
                    
                    # Usuń żeton ze źródłowego heksu
                    del self.hex_data[self.drag_start_hex]["token"]
                    
                    # Odśwież mapę
                    self.draw_grid()
                    self.auto_save_and_export("przeniesiono żeton")
                    print(f"Przeniesiono żeton z {self.drag_start_hex} do {target_hex}")
                else:
                    print(f"Docelowy heks {target_hex} już ma żeton")
            
        # Wyczyść stan przeciągania
        self.drag_start_hex = None
        self.drag_token_data = None

    def place_token_on_hex_new(self, token, hex_id):
        """Umieszcza żeton na heksie (nowa wersja)"""
        # Sprawdź czy heks już ma żeton
        if hex_id in self.hex_data and "token" in self.hex_data[hex_id]:
            print(f"Heks {hex_id} już ma żeton")
            return
            
        # Sprawdź unikalność
        if self.uniqueness_mode:
            for terrain in self.hex_data.values():
                existing_token = terrain.get("token")
                if existing_token and existing_token.get("unit") == token["id"]:
                    print(f"Żeton {token['id']} już jest na mapie (tryb unikalności)")
                    return
        
        # Jeśli brak wpisu dla heksu, utwórz domyślny
        if hex_id not in self.hex_data:
            self.hex_data[hex_id] = {
                "terrain_key": "teren_płaski",
                "move_mod": 0,
                "defense_mod": 0
            }
        
        # Dodaj żeton
        rel_path = token["image"].replace("\\", "/")
        self.hex_data[hex_id]["token"] = {
            "unit": token["id"],
            "image": rel_path
        }
        
        # Odśwież mapę i zapisz
        self.draw_grid()
        self.auto_save_and_export("wstawiono żeton")
        print(f"Wstawiono żeton {token['id']} na heks {hex_id}")
        
        # Odśwież listę dostępnych żetonów
        self.update_filtered_tokens()

    def clear_token_selection_new(self):
        """Czyści wybór żetonu (nowa wersja)"""
        if self.selected_token and '_button' in self.selected_token:
            try:
                # Sprawdź czy przycisk nadal istnieje w interfejsie
                self.selected_token['_button'].config(relief="raised", bg="saddlebrown")
            except tk.TclError:
                # Przycisk został usunięty podczas odświeżania palety, ignoruj błąd
                pass
        self.selected_token = None
        print("Wyczyszczono wybór żetonu")

    # === Narzędzie rzek ===

    def toggle_river_section_visibility(self) -> None:
        self._set_river_section_visibility(not self._river_section_expanded)

    def _set_river_section_visibility(self, visible: bool) -> None:
        self._river_section_expanded = visible
        if visible:
            self.river_frame.pack(fill=tk.X, pady=(4, 0))
            self.river_section_toggle_button.config(text="[-] Rzeki (beta)")
        else:
            self.river_frame.pack_forget()
            self.river_section_toggle_button.config(text="[+] Rzeki (beta)")

    def toggle_river_mode(self) -> None:
        self._set_river_mode(not self.river_mode_active)

    def _set_river_mode(self, active: bool) -> None:
        if self.river_mode_active == active:
            return
        self.river_mode_active = active
        skip_popup = getattr(self, "_skip_river_mode_popup", False)
        self._skip_river_mode_popup = False
        if not active:
            self.river_path.clear()
            self._river_resume_expected_exit = None
        else:
            self._river_resume_expected_exit = None
        if hasattr(self, "toggle_river_mode_button"):
            if active:
                self.toggle_river_mode_button.config(text="Wyłącz tryb rzeki", bg="#1c4d66")
            else:
                self.toggle_river_mode_button.config(text="Włącz tryb rzeki", bg="#1f5d7a")
        self._river_update_status()
        self.draw_grid()
        if active and not skip_popup:
            message = (
                "Tryb rzeki aktywny. Kliknij LPM, aby zbudować ścieżkę, a następnie użyj "
                "'Generuj rzekę'."
            )
            messagebox.showinfo("Tryb rzeki", message, parent=self.root)

    def _river_update_status(self) -> None:
        count = len(self.river_path)
        branch_mode = getattr(self, "_river_resume_branch", "main")
        is_tributary = branch_mode == "tributary"
        
        if is_tributary:
            # W trybie dopływu pierwszy heks to źródło - pokazujemy ile dodano heksów dopływu
            tributary_count = count - 1 if count > 0 else 0
            self.river_status_var.set(f"Ścieżka dopływu: {tributary_count} heksów")
            min_for_generate = 2  # źródło + 1 heks dopływu
        else:
            self.river_status_var.set(f"Ścieżka rzeki: {count} heksów")
            min_for_generate = 2
        
        generate_state = tk.NORMAL if self.river_mode_active and count >= min_for_generate else tk.DISABLED
        undo_state = tk.NORMAL if self.river_mode_active and count >= 1 else tk.DISABLED
        if hasattr(self, "river_generate_button"):
            self.river_generate_button.config(state=generate_state)
        if hasattr(self, "river_undo_button"):
            self.river_undo_button.config(state=undo_state)
        if hasattr(self, "river_clear_button"):
            self.river_clear_button.config(state=undo_state)
        self._update_tributary_controls_state()

    def _apply_river_template(self, template_name: str) -> None:
        segments = RIVER_TEMPLATE_SEGMENTS.get(template_name)
        if not segments:
            self.set_status(f"Brak szablonu o nazwie: {template_name}.")
            return
        if not self.river_mode_active:
            messagebox.showinfo(
                "Szablony nurtu",
                "Włącz tryb rzeki, aby użyć szablonu.",
                parent=self.root,
            )
            return
        if not self.river_path:
            messagebox.showinfo(
                "Szablony nurtu",
                "Dodaj początkowy heks do ścieżki przed użyciem szablonu.",
                parent=self.root,
            )
            return

        try:
            start_q, start_r = map(int, self.river_path[-1].split(","))
        except ValueError:
            messagebox.showerror(
                "Szablony nurtu",
                "Nie można odczytać współrzędnych ostatniego heksu ścieżki.",
                parent=self.root,
            )
            return

        candidate_hexes: list[str] = []
        current_q, current_r = start_q, start_r
        for delta_q, delta_r in segments:
            if (delta_q, delta_r) not in AXIAL_DIRECTION_TO_SIDE:
                messagebox.showerror(
                    "Szablony nurtu",
                    "Konfiguracja szablonu zawiera nieobsługiwany kierunek.",
                    parent=self.root,
                )
                return
            current_q += delta_q
            current_r += delta_r
            hex_id = f"{current_q},{current_r}"
            if hex_id not in self.hex_centers:
                messagebox.showwarning(
                    "Szablony nurtu",
                    "Szablon wychodzi poza dozwoloną siatkę. Dodaj brakujący heks ręcznie lub wybierz inny wzór.",
                    parent=self.root,
                )
                return
            candidate_hexes.append(hex_id)

        if not candidate_hexes:
            self.set_status("Szablon nie zawiera dodatkowych segmentów.")
            return

        self.river_path.extend(candidate_hexes)
        self.selected_hex = candidate_hexes[-1]
        if len(self.river_path) >= 2:
            self._river_resume_expected_exit = None

        self._river_update_status()
        self.draw_grid()
        self.update_hex_info_display(self.selected_hex)
        self.set_status(f"Dodano {len(candidate_hexes)} heksów według szablonu '{template_name}'.")

    def _register_tributary_control(self, widget: tk.Widget, *, enabled_state: str = "normal") -> None:
        self._river_tributary_widgets.append((widget, enabled_state))

    def _update_tributary_controls_state(self) -> None:
        enabled = bool(self.river_tributary_enabled_var.get())
        for widget, enabled_state in self._river_tributary_widgets:
            try:
                state = enabled_state if enabled else "disabled"
                widget.configure(state=state)
            except tk.TclError:
                continue
        if enabled:
            self._ensure_tributary_defaults()
        self._update_river_preview_image()

    def _ensure_tributary_defaults(self) -> None:
        if self.river_tributary_join_var.get() in ("", None):
            self.river_tributary_join_var.set(55.0)
        if self.river_tributary_shape_var.get() in ("", None):
            self.river_tributary_shape_var.set(TRIBUTARY_SHAPE_LABELS["curve"])
        if self.river_tributary_direction_var.get() in ("", None):
            self.river_tributary_direction_var.set(TRIBUTARY_DIRECTION_LABELS["auto"])
        if self.river_tributary_strength_var.get() in ("", None):
            self.river_tributary_strength_var.set(0.6)
        if self.river_tributary_noise_var.get() in ("", None):
            self.river_tributary_noise_var.set(0.0)
        if self.river_tributary_frequency_var.get() in ("", None):
            self.river_tributary_frequency_var.set(2.5)
        try:
            _ = self.river_tributary_seed_offset_var.get()
        except tk.TclError:
            self.river_tributary_seed_offset_var.set(1_000_000)

    def _build_tributary_options(self, *, silent: bool = False) -> TributaryOptions | None:
        if TributaryOptions is None:
            if not silent:
                messagebox.showwarning(
                    "Generator rzeki",
                    "Moduł generujący dopływy nie jest dostępny. Zainstaluj generate_river_hex_tile.py.",
                    parent=self.root,
                )
            return None

        entry_label = (self.river_tributary_entry_var.get() or "").strip()
        entry_cfg = TRIBUTARY_ENTRY_OPTIONS.get(entry_label)
        if not entry_cfg:
            if not silent:
                messagebox.showerror(
                    "Dopływ",
                    "Wybierz poprawną krawędź wejścia dopływu.",
                    parent=self.root,
                )
            return None
        entry_side = entry_cfg.get("entry_side")

        try:
            join_percent = float(self.river_tributary_join_var.get())
        except (tk.TclError, TypeError, ValueError):
            join_percent = float(entry_cfg.get("default_join", 0.55) * 100.0)
        join_ratio = max(MIN_TRIBUTARY_JOIN, min(MAX_TRIBUTARY_JOIN, join_percent / 100.0))

        shape_label = (self.river_tributary_shape_var.get() or TRIBUTARY_SHAPE_LABELS["curve"]).strip()
        shape_key = TRIBUTARY_SHAPE_LABEL_TO_KEY.get(
            shape_label,
            str(self._current_tributary_params.get("shape", "curve")),
        )

        try:
            strength = float(self.river_tributary_strength_var.get())
        except (tk.TclError, TypeError, ValueError):
            strength = 0.6
        strength = max(0.0, min(1.0, strength))

        try:
            noise_amp = float(self.river_tributary_noise_var.get())
        except (tk.TclError, TypeError, ValueError):
            noise_amp = 0.0
        noise_amp = max(0.0, min(3.0, noise_amp))

        try:
            noise_freq = float(self.river_tributary_frequency_var.get())
        except (tk.TclError, TypeError, ValueError):
            noise_freq = 2.5
        noise_freq = max(0.1, min(6.0, noise_freq))

        direction_label = (self.river_tributary_direction_var.get() or TRIBUTARY_DIRECTION_LABELS["auto"]).strip()
        direction_key = TRIBUTARY_DIRECTION_LABEL_TO_KEY.get(
            direction_label,
            str(self._current_tributary_params.get("shape_direction_mode", "auto")),
        )
        if direction_key == "left":
            shape_direction = 1
        elif direction_key == "right":
            shape_direction = -1
        else:
            shape_direction = None
            direction_key = "auto"

        try:
            seed_offset = int(self.river_tributary_seed_offset_var.get())
        except (tk.TclError, TypeError, ValueError):
            seed_offset = 1_000_000
        seed_offset = max(0, seed_offset)

        try:
            base_bank_offset = float(self.river_bank_offset_var.get())
        except (tk.TclError, TypeError, ValueError):
            base_bank_offset = DEFAULT_BANK_OFFSET
        bank_offset_scale = float(self._current_tributary_params.get("bank_offset_scale", 0.8))
        bank_offset = max(0.5, min(3.5, base_bank_offset * bank_offset_scale))

        try:
            bank_variation = float(self.river_bank_variation_var.get())
        except (tk.TclError, TypeError, ValueError):
            bank_variation = DEFAULT_BANK_VARIATION
        variation_scale = float(self._current_tributary_params.get("variation_scale", 1.0))
        bank_variation = max(0.0, min(0.9, bank_variation * variation_scale))

        return TributaryOptions(
            entry_side=entry_side,
            join_ratio=join_ratio,
            shape=shape_key,
            shape_strength=strength,
            noise_amplitude=noise_amp,
            noise_frequency=noise_freq,
            shape_direction=shape_direction,
            shape_direction_mode=direction_key,
            seed_offset=seed_offset,
            bank_offset=bank_offset,
            bank_variation=bank_variation,
        )

    def _update_river_preview_image(self) -> None:
        label = self.river_preview_label
        if label is None:
            return

        def reset_preview(message: str) -> None:
            self.river_preview_caption_var.set(message)
            label.configure(image="", text="Brak podglądu")
            label.image = None
            self._river_preview_photo = None
            self._river_preview_cache_key = None

        if render_centerline is None or RiverCenterlineOptions is None:
            reset_preview("Podgląd rzeki: moduł generatora jest niedostępny.")
            return

        branch_mode = getattr(self, "_river_resume_branch", "main")
        is_tributary = branch_mode == "tributary"
        min_hexes = 2  # Zarówno dla głównej rzeki jak i dopływu
        
        if len(self.river_path) < min_hexes:
            if is_tributary:
                reset_preview(f"Podgląd dopływu: dodaj jeszcze {min_hexes - len(self.river_path)} heks(ów).")
            else:
                reset_preview("Podgląd rzeki: dodaj co najmniej dwa heksy.")
            return

        try:
            coords = [tuple(map(int, hid.split(","))) for hid in self.river_path]
        except ValueError:
            reset_preview("Podgląd rzeki: ścieżka zawiera nieprawidłowe współrzędne.")
            return

        segments: list[tuple[int, int]] = []
        for idx in range(len(coords) - 1):
            dq = coords[idx + 1][0] - coords[idx][0]
            dr = coords[idx + 1][1] - coords[idx][1]
            delta = (dq, dr)
            if delta not in AXIAL_DIRECTION_TO_SIDE:
                reset_preview("Podgląd rzeki: ścieżka zawiera heksy, które nie sąsiadują ze sobą.")
                return
            segments.append(delta)

        branch_mode = getattr(self, "_river_resume_branch", "main")
        is_tributary = branch_mode == "tributary"
        preview_index = len(self.river_path) - 1
        if is_tributary and len(self.river_path) > 1:
            preview_index = 1
        preview_index = max(0, min(preview_index, len(self.river_path) - 1))

        # Oblicz entry/exit - dla dopływu użyj specjalnej logiki
        tributary_entry_to_main = getattr(self, "_tributary_entry_side", None)
        if is_tributary and preview_index == 1 and tributary_entry_to_main:
            # Dla pierwszego heksu dopływu: wyjście w kierunku głównego nurtu
            exit_side = tributary_entry_to_main
            if len(segments) > 1:
                entry_side = SIDE_OPPOSITE[AXIAL_DIRECTION_TO_SIDE[segments[1]]]
            else:
                entry_side = SIDE_OPPOSITE[exit_side]
        else:
            entry_side, exit_side = self._river_entry_exit_for_index(preview_index, segments)

        try:
            grid_size = int(self.river_grid_var.get())
        except (TypeError, ValueError):
            grid_size = DEFAULT_HEX_TEXTURE_GRID_SIZE
        if grid_size not in HEX_TEXTURE_GRID_OPTIONS:
            grid_size = DEFAULT_HEX_TEXTURE_GRID_SIZE

        def clamp(value: float, low: float, high: float) -> float:
            return max(low, min(high, value))

        try:
            strength = float(self.river_strength_var.get())
        except (tk.TclError, TypeError, ValueError):
            strength = 0.5
        strength = clamp(strength, 0.0, 1.0)

        try:
            noise = float(self.river_noise_var.get())
        except (tk.TclError, TypeError, ValueError):
            noise = 0.0
        noise = clamp(noise, 0.0, 3.0)

        try:
            frequency = float(self.river_frequency_var.get())
        except (tk.TclError, TypeError, ValueError):
            frequency = 2.0
        frequency = max(0.1, frequency)

        try:
            seed_base = int(self.river_seed_var.get())
        except (tk.TclError, TypeError, ValueError):
            seed_base = 0
        seed = seed_base + preview_index

        try:
            base_bank_offset = float(self.river_bank_offset_var.get())
        except (tk.TclError, TypeError, ValueError):
            base_bank_offset = DEFAULT_BANK_OFFSET
        base_bank_offset = clamp(base_bank_offset, 0.6, 3.2)
        bank_offset = (
            base_bank_offset * LARGE_RIVER_WIDTH_MULTIPLIER
            if self.river_large_mode_var.get()
            else base_bank_offset
        )

        try:
            bank_variation = float(self.river_bank_variation_var.get())
        except (tk.TclError, TypeError, ValueError):
            bank_variation = DEFAULT_BANK_VARIATION
        bank_variation = clamp(bank_variation, 0.0, 0.8)

        shape_label = (self.river_shape_var.get() or "").strip()
        shape_preference = RIVER_SHAPE_LABEL_TO_KEY.get(shape_label, "auto")
        shape, shape_direction = self._river_determine_shape(preview_index, segments, shape_preference)

        hex_id = self.river_path[preview_index]
        terrain = self.hex_data.get(hex_id) or {}
        background_path = None
        background_key = None

        tributary_options = None
        tributary_key: tuple | None = None
        target_tributary_index: int | None = None
        if self.river_tributary_enabled_var.get():
            tributary_options = self._build_tributary_options(silent=True)
            if tributary_options is None:
                reset_preview("Podgląd rzeki: ustawienia dopływu są niekompletne.")
                return
            target_tributary_index = len(self.river_path) - 1

        current_tributary = None
        if (
            tributary_options is not None
            and target_tributary_index is not None
            and preview_index == target_tributary_index
        ):
            if (
                entry_side == tributary_options.entry_side
                or exit_side == tributary_options.entry_side
            ):
                reset_preview(
                    "Podgląd rzeki: dopływ nie może wchodzić przez używaną krawędź."
                )
                return
            current_tributary = tributary_options
            tributary_key = (
                tributary_options.entry_side,
                round(tributary_options.join_ratio, 4),
                tributary_options.shape,
                round(tributary_options.shape_strength, 4),
                round(tributary_options.noise_amplitude, 4),
                round(tributary_options.noise_frequency, 4),
                tributary_options.shape_direction,
                tributary_options.shape_direction_mode,
                tributary_options.seed_offset,
                None if tributary_options.bank_offset is None else round(tributary_options.bank_offset, 4),
                None if tributary_options.bank_variation is None else round(tributary_options.bank_variation, 4),
            )

        cache_key = (
            tuple(self.river_path),
            preview_index,
            tuple(segments),
            grid_size,
            round(strength, 4),
            round(noise, 4),
            round(frequency, 4),
            seed,
            round(bank_offset, 4),
            round(bank_variation, 4),
            shape,
            shape_direction,
            entry_side,
            exit_side,
            background_key,
            bool(self.river_large_mode_var.get()),
            branch_mode,
            tributary_key,
        )

        entry_label_pl = HEX_SIDE_DISPLAY_LABELS.get(entry_side, entry_side)
        exit_label_pl = HEX_SIDE_DISPLAY_LABELS.get(exit_side, exit_side)
        shape_label_pl = RIVER_SHAPE_LABELS.get(shape, shape)
        export_px = HEX_TEXTURE_EXPORT_SIZES.get(grid_size, grid_size)
        caption_lines = [
            f"Podgląd heksu {preview_index + 1}/{len(self.river_path)}: {hex_id}",
            f"Wejście: {entry_label_pl}, wyjście: {exit_label_pl}",
            f"Siatka {grid_size} ({export_px} px), seed {seed}",
            f"Profil: {shape_label_pl}, siła {strength:.2f}, szum {noise:.2f}",
        ]
        if branch_mode == "tributary":
            caption_lines.append("Tryb: dopływ")
        elif self.river_tributary_enabled_var.get() and target_tributary_index is not None:
            caption_lines.append("Dopływ: aktywny na ostatnim heksie")
        if self.river_large_mode_var.get():
            caption_lines.append("Tryb: szeroki nurt")
        caption = "\n".join(caption_lines)

        if self._river_preview_cache_key == cache_key and self._river_preview_photo is not None:
            self.river_preview_caption_var.set(caption)
            label.configure(image=self._river_preview_photo, text="")
            label.image = self._river_preview_photo
            return

        try:
            opts = RiverCenterlineOptions(
                grid_size=grid_size,
                background=background_path,
                entry_side=entry_side,
                exit_side=exit_side,
                shape=shape,
                shape_strength=strength,
                shape_direction=shape_direction,
                noise_amplitude=noise,
                noise_frequency=frequency,
                seed=seed,
                bank_offset=bank_offset,
                bank_variation=bank_variation,
                tributary=current_tributary,
            )
            render = render_centerline(opts)
        except Exception as exc:  # noqa: BLE001
            reset_preview(f"Podgląd rzeki: nie udało się wygenerować obrazu ({exc}).")
            return

        src_img = render.image
        if src_img.width <= 0 or src_img.height <= 0:
            reset_preview("Podgląd rzeki: generator zwrócił pusty obraz.")
            return
        scale_factor = 3 if src_img.width <= 64 else 2
        preview_size = max(src_img.width * scale_factor, src_img.width)
        preview_img = src_img.resize((preview_size, preview_size), Image.NEAREST)
        photo = ImageTk.PhotoImage(preview_img)

        self._river_preview_photo = photo
        self._river_preview_cache_key = cache_key
        self.river_preview_caption_var.set(caption)
        label.configure(image=photo, text="")
        label.image = photo

    def _river_handle_left_click(self, hex_id: str) -> None:
        if not self.river_mode_active:
            return
        if hex_id not in self.hex_centers:
            return
        if not self.river_path:
            self._river_resume_branch = "main"
        if self.river_path:
            if self.river_path[-1] == hex_id:
                return
            if len(self.river_path) > 1 and self.river_path[-2] == hex_id:
                self.river_path.pop()
                self._river_update_status()
                self.draw_grid()
                return
            last_q, last_r = map(int, self.river_path[-1].split(","))
            next_q, next_r = map(int, hex_id.split(","))
            delta = (next_q - last_q, next_r - last_r)
            if delta not in AXIAL_DIRECTION_TO_SIDE:
                messagebox.showwarning(
                    "Ścieżka rzeki",
                    "Wybrany heks nie sąsiaduje z poprzednim.",
                    parent=self.root,
                )
                return
            if len(self.river_path) == 1 and self._river_resume_expected_exit:
                expected_delta = SIDE_TO_AXIAL_DIRECTION.get(self._river_resume_expected_exit)
                if expected_delta and delta != expected_delta:
                    side_label = HEX_SIDE_LABELS_PL.get(self._river_resume_expected_exit, self._river_resume_expected_exit)
                    proceed = messagebox.askyesno(
                        "Kontynuacja rzeki",
                        (
                            "Ten heks nie leży po oczekiwanej stronie "
                            f"({side_label}). Czy mimo to kontynuować z tego pola?"
                        ),
                        parent=self.root,
                    )
                    if not proceed:
                        return
                    self._river_resume_expected_exit = None
        self.river_path.append(hex_id)
        self.selected_hex = hex_id
        if len(self.river_path) == 2:
            self._river_resume_expected_exit = None
        self._river_update_status()
        self.draw_grid()
        self.update_hex_info_display(hex_id)

    def _river_handle_right_click(self, hex_id: str | None) -> None:
        if not self.river_mode_active or not self.river_path:
            return
        if hex_id and hex_id in self.river_path:
            index = self.river_path.index(hex_id)
            self.river_path = self.river_path[:index]
        else:
            self.river_path.pop()
        self._river_update_status()
        self.draw_grid()

    def river_pop_last_hex(self) -> None:
        if not self.river_path:
            return
        self.river_path.pop()
        if not self.river_path:
            self._river_resume_expected_exit = None
            self._river_resume_branch = "main"
        elif len(self.river_path) == 1:
            self._river_resume_expected_exit = None
        self._river_update_status()
        self.draw_grid()

    def clear_river_path(self) -> None:
        if not self.river_path:
            return
        self.river_path.clear()
        self._river_resume_expected_exit = None
        self._river_resume_branch = "main"
        self._tributary_mode = False
        self._tributary_source_hex = None
        self._simple_tributary_mode = False
        self._update_tributary_status()
        self._river_update_status()
        self.draw_grid()

    def _start_simple_tributary(self) -> None:
        """Prosty tryb dopływu: wybierz heks z rzeką, potem kliknij skąd płynie dopływ."""
        if self.selected_hex is None:
            messagebox.showinfo(
                "Dopływ",
                "Najpierw kliknij heks z istniejącą rzeką.",
                parent=self.root,
            )
            return
        
        # Sprawdź czy heks ma rzekę
        record = self.hex_data.get(self.selected_hex)
        if not record:
            messagebox.showwarning(
                "Dopływ",
                "Wybrany heks nie ma danych terenu.",
                parent=self.root,
            )
            return
        
        river_meta = record.get("river_generation_meta")
        if not river_meta:
            # Sprawdź po teksturze
            texture_rel = record.get("texture")
            has_river = False
            if texture_rel:
                try:
                    texture_path = fix_image_path(texture_rel)
                    texture_path.relative_to(RIVER_OUTPUT_DIR)
                    has_river = True
                except (ValueError, AttributeError):
                    pass
            if not has_river:
                messagebox.showwarning(
                    "Dopływ",
                    "Wybrany heks nie zawiera rzeki.\nNajpierw wygeneruj główną rzekę.",
                    parent=self.root,
                )
                return
        
        # Włącz tryb oczekiwania na kliknięcie źródła dopływu
        self._simple_tributary_mode = True
        self._simple_tributary_target = self.selected_hex
        self._simple_tributary_meta = river_meta
        
        self.tributary_status_var.set("Kliknij sąsiedni heks\n(źródło dopływu)")
        self.set_status("Kliknij sąsiedni heks skąd płynie dopływ...")
        self.draw_grid()

    def _handle_simple_tributary_click(self, hex_id: str) -> bool:
        """Obsługuje kliknięcie w trybie prostego dopływu. Zwraca True jeśli obsłużono."""
        if not getattr(self, "_simple_tributary_mode", False):
            return False
        
        target_hex = getattr(self, "_simple_tributary_target", None)
        if not target_hex:
            self._simple_tributary_mode = False
            return False
        
        # Sprawdź czy kliknięty heks sąsiaduje z celem
        try:
            tq, tr = map(int, target_hex.split(","))
            sq, sr = map(int, hex_id.split(","))
        except ValueError:
            return False
        
        dq, dr = sq - tq, sr - tr
        delta = (dq, dr)
        
        if delta not in AXIAL_DIRECTION_TO_SIDE:
            messagebox.showwarning(
                "Dopływ",
                "Musisz kliknąć heks sąsiadujący z rzeką!",
                parent=self.root,
            )
            return True
        
        # Oblicz stronę wejścia dopływu
        entry_side = AXIAL_DIRECTION_TO_SIDE[delta]
        
        # Sprawdź czy strona nie jest zajęta przez główny nurt
        river_meta = getattr(self, "_simple_tributary_meta", None)
        if river_meta:
            existing_entry = river_meta.get("entry_side")
            existing_exit = river_meta.get("exit_side")
            if entry_side in (existing_entry, existing_exit):
                occupied_label = HEX_SIDE_LABELS_PL.get(entry_side, entry_side)
                messagebox.showwarning(
                    "Dopływ",
                    f"Ta strona ({occupied_label}) jest już zajęta przez główny nurt!\n"
                    f"Wybierz inny sąsiedni heks.",
                    parent=self.root,
                )
                return True
        
        # Generuj dopływ!
        self._generate_simple_tributary(target_hex, hex_id, entry_side)
        
        # Wyczyść tryb
        self._simple_tributary_mode = False
        self._simple_tributary_target = None
        self._simple_tributary_meta = None
        self.tributary_status_var.set("Dopływ dodany ✓")
        self.draw_grid()
        
        return True

    def _generate_simple_tributary(self, river_hex: str, source_hex: str, entry_side: str) -> None:
        """Generuje dopływ z source_hex do river_hex."""
        if generate_centerline is None or RiverCenterlineOptions is None:
            messagebox.showerror(
                "Generator niedostępny",
                "Nie można załadować modułu generate_river_hex_tile.",
                parent=self.root,
            )
            return
        
        # Pobierz parametry
        try:
            grid_size = int(self.river_grid_var.get())
        except (TypeError, ValueError):
            grid_size = DEFAULT_HEX_TEXTURE_GRID_SIZE
        if grid_size not in HEX_TEXTURE_GRID_OPTIONS:
            grid_size = DEFAULT_HEX_TEXTURE_GRID_SIZE
        
        # Wielkość dopływu
        size_label = getattr(self, "tributary_size_var", tk.StringVar(value="mały")).get()
        
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        
        # Pobierz istniejące dane heksu z rzeką
        record = self.hex_data.get(river_hex, {})
        river_meta = record.get("river_generation_meta", {})
        
        main_entry = river_meta.get("entry_side", "top")
        main_exit = river_meta.get("exit_side", "bottom")
        
        # Bez tła (zgodnie z innymi generatorami)
        background_path = None
        
        # Utwórz opcje dopływu (używamy poprawnych argumentów z TributaryOptions)
        # Wielkość dopływu kontrolujemy przez shape_strength i bank_offset
        size_to_params = {
            "mały": {"strength": 0.3, "bank_offset": 0.8, "noise_amp": 0.3},
            "średni": {"strength": 0.5, "bank_offset": 1.5, "noise_amp": 0.5},
            "duży": {"strength": 0.7, "bank_offset": 2.2, "noise_amp": 0.7},
        }
        trib_params = size_to_params.get(size_label, size_to_params["mały"])
        
        tributary_opts = TributaryOptions(
            entry_side=entry_side,
            join_ratio=0.5,  # Środek rzeki
            shape="curve",
            shape_strength=trib_params["strength"],
            noise_amplitude=trib_params["noise_amp"],
            noise_frequency=2.0,
            bank_offset=trib_params["bank_offset"],  # Jawnie ustawiamy rozmiar banków dopływu
            bank_color=DEFAULT_BANK_COLOR,  # Dopływ używa domyślnego koloru
            bank_variation=DEFAULT_BANK_VARIATION,  # Dopływ używa domyślnej wariacji
        )
        
        # Oblicz kształt na podstawie kątów
        if SIDE_OPPOSITE.get(main_entry) == main_exit:
            shape = "straight"
        else:
            shape = "curve"
        
        # Pobierz oryginalne parametry generowania z metadanych (zabezpieczenie przeciwko zmianie rozmiaru)
        shape_strength = river_meta.get("shape_strength", river_meta.get("shape_strength", 0.5))
        noise_amp = river_meta.get("noise_amplitude", 0.0)
        noise_freq = river_meta.get("noise_frequency", 2.0)
        seed = river_meta.get("seed", 42)
        # bank params mogą być w top-level lub w centerline_banks
        centerline_banks = river_meta.get("centerline_banks", {})
        bank_offset = river_meta.get("bank_offset", centerline_banks.get("offset", DEFAULT_BANK_OFFSET))
        bank_variation = river_meta.get("bank_variation", centerline_banks.get("variation", DEFAULT_BANK_VARIATION))
        bank_color_rgba = None
        bank_color_cfg = river_meta.get("bank_color") or centerline_banks.get("color")
        if isinstance(bank_color_cfg, dict):
            bank_color_rgba = tuple(bank_color_cfg.get("rgba", DEFAULT_BANK_COLOR))
        elif isinstance(bank_color_cfg, (list, tuple)):
            bank_color_rgba = tuple(bank_color_cfg)
        else:
            bank_color_rgba = DEFAULT_BANK_COLOR
        
        # Generuj teksturę z dopływem
        output_filename = f"hex_{river_hex.replace(',', '_')}_river_{timestamp}.png"
        output_path = RIVER_OUTPUT_DIR / output_filename
        
        options = RiverCenterlineOptions(
            grid_size=grid_size,
            background=background_path,
            entry_side=main_entry,
            exit_side=main_exit,
            shape=shape,
            shape_strength=shape_strength,
            shape_direction=river_meta.get("shape_direction"),
            noise_amplitude=noise_amp,
            noise_frequency=noise_freq,
            seed=seed,
            bank_offset=bank_offset,
            bank_color=bank_color_rgba,
            bank_variation=bank_variation,
            tributary=tributary_opts,
        )
        
        try:
            result = generate_centerline(options, output_path)
            # result to RiverCenterlineResult z image_path, metadata_path, metadata
        except Exception as e:
            messagebox.showerror(
                "Błąd generowania",
                f"Nie udało się wygenerować dopływu:\n{e}",
                parent=self.root,
            )
            return
        
        # Zapisz nową teksturę - użyj ścieżki względem katalogu projektu
        project_root = Path(__file__).resolve().parent.parent
        rel_path = str(output_path.relative_to(project_root)).replace("\\", "/")
        
        # Zaktualizuj metadane
        if river_hex not in self.hex_data:
            self.hex_data[river_hex] = {
                "terrain_key": "teren_płaski",
                "move_mod": 0,
                "defense_mod": 0,
            }
        
        self.hex_data[river_hex]["texture"] = rel_path
        
        # Dodaj info o dopływie do metadanych
        tributaries = river_meta.get("tributaries", [])
        tributaries.append({
            "entry_side": entry_side,
            "source_hex": source_hex,
            "size": size_label,
        })
        river_meta["tributaries"] = tributaries
        self.hex_data[river_hex]["river_generation_meta"] = river_meta
        
        # Odśwież widok - wyczyść cache dla nowej tekstury
        self.hex_texture_cache = {
            key: value for key, value in self.hex_texture_cache.items() if key[0] != rel_path
        }
        self.draw_grid()
        self.auto_save("dodano dopływ")
        
        side_name = HEX_SIDE_LABELS_PL.get(entry_side, entry_side)
        self.set_status(f"Dodano dopływ z: {side_name}")
        messagebox.showinfo(
            "Dopływ",
            f"Dopływ dodany!\n\nWpływa od strony: {side_name}",
            parent=self.root,
        )

    def _draw_simple_tributary_overlay(self) -> None:
        """Rysuje wizualizację trybu prostego dopływu - podświetla heks docelowy i sąsiadów."""
        target_hex = getattr(self, "_simple_tributary_target", None)
        if not target_hex or target_hex not in self.hex_centers:
            return
        
        cx, cy = self.hex_centers[target_hex]
        s = self.hex_size
        
        # Podświetl heks docelowy (z rzeką) na niebiesko
        self.canvas.create_oval(
            cx - s * 0.7, cy - s * 0.7, cx + s * 0.7, cy + s * 0.7,
            outline="#00bfff", width=4, fill="", dash=(5, 3),
        )
        self.canvas.create_text(
            cx, cy - s * 0.85,
            text="🏞️ Rzeka",
            fill="#00bfff",
            font=("Arial", 9, "bold"),
        )
        
        # Pobierz zajęte strony
        river_meta = getattr(self, "_simple_tributary_meta", {}) or {}
        occupied = {river_meta.get("entry_side"), river_meta.get("exit_side")} - {None}
        
        # Podświetl sąsiednie heksy (możliwe źródła dopływu)
        try:
            tq, tr = map(int, target_hex.split(","))
        except ValueError:
            return
        
        for delta, side in AXIAL_DIRECTION_TO_SIDE.items():
            nq, nr = tq + delta[0], tr + delta[1]
            neighbor_id = f"{nq},{nr}"
            
            if neighbor_id not in self.hex_centers:
                continue
            
            ncx, ncy = self.hex_centers[neighbor_id]
            
            # Czy ta strona jest zajęta przez główny nurt?
            if side in occupied:
                # Czerwony - niedostępny
                color = "#ff4444"
                label = "✖"
            else:
                # Zielony - dostępny
                color = "#44ff44"
                label = "✔"
            
            self.canvas.create_oval(
                ncx - s * 0.5, ncy - s * 0.5, ncx + s * 0.5, ncy + s * 0.5,
                outline=color, width=3, fill="", dash=(3, 2),
            )
            self.canvas.create_text(
                ncx, ncy,
                text=label,
                fill=color,
                font=("Arial", 14, "bold"),
            )

    def _start_tributary_from_selected(self) -> None:
        """Rozpoczyna rysowanie dopływu od wybranego heksu z istniejącą rzeką."""
        if self.selected_hex is None:
            messagebox.showinfo(
                "Dopływ",
                "Najpierw wybierz heks z istniejącą rzeką na mapie.",
                parent=self.root,
            )
            return
        
        # Sprawdź czy heks ma rzekę
        record = self.hex_data.get(self.selected_hex)
        if not record:
            messagebox.showwarning(
                "Dopływ",
                "Wybrany heks nie ma zapisanych danych terenu.",
                parent=self.root,
            )
            return
        
        texture_rel = record.get("texture")
        river_meta = record.get("river_generation_meta")
        
        # Sprawdź czy to heks z rzeką
        has_river = False
        if texture_rel:
            try:
                texture_path = fix_image_path(texture_rel)
                texture_path.relative_to(RIVER_OUTPUT_DIR)
                has_river = True
            except (ValueError, AttributeError):
                pass
        
        if river_meta:
            has_river = True
        
        if not has_river:
            messagebox.showwarning(
                "Dopływ",
                "Wybrany heks nie zawiera rzeki.\nNajpierw narysuj główną rzekę, potem dodaj dopływy.",
                parent=self.root,
            )
            return
        
        # Pobierz konfigurację z TRIBUTARY_ENTRY_OPTIONS
        side_label = self.tributary_side_var.get()
        entry_cfg = TRIBUTARY_ENTRY_OPTIONS.get(side_label)
        if not entry_cfg:
            messagebox.showerror(
                "Dopływ",
                "Wybierz poprawną stronę wejścia dopływu z listy.",
                parent=self.root,
            )
            return
        entry_side = entry_cfg["entry_side"]
        
        # Sprawdź czy wybrana strona nie koliduje z istniejącym nurtem
        if river_meta:
            existing_entry = river_meta.get("entry_side")
            existing_exit = river_meta.get("exit_side")
            occupied_sides = {existing_entry, existing_exit} - {None}
            if entry_side in occupied_sides:
                # Znajdź dostępne strony
                all_sides = {"top", "top_right", "bottom_right", "bottom", "bottom_left", "top_left"}
                free_sides = all_sides - occupied_sides
                free_labels = [TRIBUTARY_ENTRY_SIDE_TO_LABEL.get(s, s) for s in free_sides]
                occupied_labels = [TRIBUTARY_ENTRY_SIDE_TO_LABEL.get(s, s) for s in occupied_sides]
                messagebox.showwarning(
                    "Dopływ",
                    f"Ta krawędź jest już zajęta przez główny nurt!\n\n"
                    f"Zajęte strony: {', '.join(occupied_labels)}\n\n"
                    f"Dostępne strony:\n• " + "\n• ".join(free_labels),
                    parent=self.root,
                )
                return
        
        # Włącz tryb rzeki jeśli nie jest aktywny
        if not self.river_mode_active:
            self._skip_river_mode_popup = True
            self._set_river_mode(True)
        
        # Ustaw tryb dopływu
        self._tributary_mode = True
        self._tributary_source_hex = self.selected_hex
        self._tributary_entry_side = entry_side
        
        # Wyczyść ścieżkę i zacznij od heksu źródłowego
        self.river_path = [self.selected_hex]
        self._river_resume_branch = "tributary"
        
        # Ustaw oczekiwany kierunek - dopływ wchodzi z danej strony
        self._river_resume_expected_exit = entry_side
        
        # Ustaw parametry dopływu
        self.river_tributary_enabled_var.set(True)
        self.river_tributary_entry_var.set(side_label)
        self._on_tributary_entry_change()
        
        self._update_tributary_status()
        self._river_update_status()
        self.draw_grid()
        self.update_hex_info_display(self.selected_hex)
        
        side_name = HEX_SIDE_LABELS_PL.get(entry_side, entry_side)
        self.set_status(f"Tryb dopływu: dodaj heksy ścieżki dopływu (wejście z: {side_name})")
        
        messagebox.showinfo(
            "Dopływ",
            f"Tryb dopływu aktywny!\n\n"
            f"• Klikaj heksy LPM aby narysować ścieżkę dopływu\n"
            f"• Dopływ wejdzie do rzeki od strony: {side_name}\n"
            f"• Kliknij 'Generuj rzekę' gdy skończysz\n"
            f"• PPM cofa ostatni heks",
            parent=self.root,
        )

    def _update_tributary_status(self) -> None:
        """Aktualizuje status trybu dopływu."""
        if not hasattr(self, "tributary_status_var"):
            return
        
        if getattr(self, "_tributary_mode", False):
            source = getattr(self, "_tributary_source_hex", "?")
            side = getattr(self, "_tributary_entry_side", "?")
            side_name = HEX_SIDE_LABELS_PL.get(side, side)
            self.tributary_status_var.set(
                f"🔀 Tryb dopływu aktywny\n"
                f"Źródło: {source}\n"
                f"Wejście: {side_name}"
            )
        else:
            self.tributary_status_var.set("")

    def _draw_river_path_overlay(self) -> None:
        """Rysuje wizualizację ścieżki rzeki ze strzałkami kierunku przepływu."""
        if not getattr(self, "canvas", None):
            return
        coords = []
        for hex_id in self.river_path:
            center = self.hex_centers.get(hex_id)
            if center:
                coords.append(center)
        
        # Różne kolory dla trybu dopływu vs głównej rzeki
        is_tributary = getattr(self, "_tributary_mode", False)
        if is_tributary:
            line_color = "#7dd3fc"  # jasnoniebieski
            arrow_color = "#38bdf8"
            source_fill = "#1e40af"  # niebieski (połączenie z rzeką)
            source_outline = "#60a5fa"
            end_fill = "#0e7490"  # cyjan (źródło dopływu)
            end_outline = "#22d3d3"
            mid_fill = "#1e3a5f"
            mid_outline = "#7dd3fc"
            legend_text = "🔵 Połączenie  ⬅️  🔹 Źródło dopływu"
        else:
            line_color = "#57a1d2"
            arrow_color = "#ffd166"
            source_fill = "#2d5a27"  # zielony (źródło)
            source_outline = "#7ddf6a"
            end_fill = "#5a2727"  # czerwony (ujście)
            end_outline = "#df6a6a"
            mid_fill = "#1f4a6b"
            mid_outline = "#57a1d2"
            legend_text = "🟢 Źródło  ➡️  🔴 Ujście"
        
        for idx, center in enumerate(coords):
            if idx > 0:
                prev_center = coords[idx - 1]
                # Rysuj linię łączącą
                self.canvas.create_line(
                    prev_center[0],
                    prev_center[1],
                    center[0],
                    center[1],
                    fill=line_color,
                    width=3,
                    dash=(4, 2),
                )
                # Rysuj strzałkę w połowie odcinka wskazującą kierunek
                mid_x = (prev_center[0] + center[0]) / 2
                mid_y = (prev_center[1] + center[1]) / 2
                dx = center[0] - prev_center[0]
                dy = center[1] - prev_center[1]
                length = math.hypot(dx, dy)
                if length > 0:
                    # Znormalizowany wektor kierunku
                    ux, uy = dx / length, dy / length
                    # Prostopadły wektor
                    px, py = -uy, ux
                    # Rozmiar strzałki
                    arrow_size = max(6, int(self.hex_size * 0.2))
                    # Punkty strzałki
                    tip_x = mid_x + ux * arrow_size * 0.5
                    tip_y = mid_y + uy * arrow_size * 0.5
                    left_x = mid_x - ux * arrow_size * 0.5 + px * arrow_size * 0.4
                    left_y = mid_y - uy * arrow_size * 0.5 + py * arrow_size * 0.4
                    right_x = mid_x - ux * arrow_size * 0.5 - px * arrow_size * 0.4
                    right_y = mid_y - uy * arrow_size * 0.5 - py * arrow_size * 0.4
                    self.canvas.create_polygon(
                        tip_x, tip_y,
                        left_x, left_y,
                        right_x, right_y,
                        fill=arrow_color,
                        outline=line_color,
                    )
            
            # Rysuj kółko z numerem heksu
            radius = max(6, int(self.hex_size * 0.28))
            if idx == 0:
                fill_color = source_fill
                outline_color = source_outline
            elif idx == len(coords) - 1:
                fill_color = end_fill
                outline_color = end_outline
            else:
                fill_color = mid_fill
                outline_color = mid_outline
            
            self.canvas.create_oval(
                center[0] - radius,
                center[1] - radius,
                center[0] + radius,
                center[1] + radius,
                fill=fill_color,
                outline=outline_color,
                width=2,
            )
            self.canvas.create_text(
                center[0],
                center[1],
                text=str(idx + 1),
                fill="white",
                font=("Arial", 9, "bold"),
            )
        
        # Dodaj legendę jeśli jest ścieżka
        if len(coords) >= 1:
            legend_y = 20
            self.canvas.create_text(
                60, legend_y,
                text=legend_text,
                fill="#ffd166",
                font=("Arial", 9, "bold"),
                anchor="w",
            )

    def generate_river_path(self) -> None:
        if not self.river_mode_active:
            messagebox.showinfo("Tryb rzeki", "Aktywuj tryb rzeki, aby generować nowe tekstury.", parent=self.root)
            return
        branch_mode = getattr(self, "_river_resume_branch", "main")
        min_hexes = 2  # Zarówno dla głównej rzeki jak i dopływu
        if len(self.river_path) < min_hexes:
            if branch_mode == "tributary":
                messagebox.showwarning(
                    "Ścieżka dopływu",
                    f"Dodaj co najmniej 1 heks do ścieżki dopływu (obecnie: {len(self.river_path) - 1}).\n"
                    f"Pierwszy heks to źródło (istniejąca rzeka), kolejne to dopływ.",
                    parent=self.root,
                )
            else:
                messagebox.showwarning("Ścieżka rzeki", "Dodaj co najmniej dwa heksy do ścieżki.", parent=self.root)
            return
        if RiverCenterlineOptions is None or generate_centerline is None:
            messagebox.showerror(
                "Generator niedostępny",
                "Nie można załadować modułu generate_river_hex_tile.py.",
                parent=self.root,
            )
            return

        # branch_mode już ustawiony powyżej

        try:
            coords = [tuple(map(int, hid.split(","))) for hid in self.river_path]
        except ValueError:
            messagebox.showerror("Ścieżka rzeki", "Nieprawidłowe współrzędne heksów.", parent=self.root)
            return

        segments: list[tuple[int, int]] = []
        for idx in range(len(coords) - 1):
            dq = coords[idx + 1][0] - coords[idx][0]
            dr = coords[idx + 1][1] - coords[idx][1]
            delta = (dq, dr)
            if delta not in AXIAL_DIRECTION_TO_SIDE:
                messagebox.showerror(
                    "Ścieżka rzeki",
                    "Ścieżka zawiera heksy, które nie sąsiadują ze sobą.",
                    parent=self.root,
                )
                return
            segments.append(delta)

        try:
            grid_size = int(self.river_grid_var.get())
        except (TypeError, ValueError):
            grid_size = DEFAULT_HEX_TEXTURE_GRID_SIZE
        if grid_size not in HEX_TEXTURE_GRID_OPTIONS:
            grid_size = DEFAULT_HEX_TEXTURE_GRID_SIZE

        try:
            strength = float(self.river_strength_var.get())
        except (TypeError, ValueError):
            strength = 0.5
        strength = max(0.0, min(strength, 1.0))

        try:
            noise = float(self.river_noise_var.get())
        except (TypeError, ValueError):
            noise = 0.0
        noise = max(0.0, min(noise, 3.0))

        try:
            frequency = float(self.river_frequency_var.get())
        except (TypeError, ValueError):
            frequency = 2.0
        frequency = max(0.1, frequency)

        try:
            seed_base = int(self.river_seed_var.get())
        except (TypeError, ValueError):
            seed_base = random.randint(0, 9999)

        try:
            base_bank_offset = float(self.river_bank_offset_var.get())
        except (tk.TclError, TypeError, ValueError):
            base_bank_offset = DEFAULT_BANK_OFFSET
        base_bank_offset = max(0.6, min(3.2, base_bank_offset))
        bank_offset = (
            base_bank_offset * LARGE_RIVER_WIDTH_MULTIPLIER
            if self.river_large_mode_var.get()
            else base_bank_offset
        )

        try:
            bank_variation = float(self.river_bank_variation_var.get())
        except (tk.TclError, TypeError, ValueError):
            bank_variation = DEFAULT_BANK_VARIATION
        bank_variation = max(0.0, min(0.8, bank_variation))

        shape_label = (self.river_shape_var.get() or "").strip()
        shape_preference = RIVER_SHAPE_LABEL_TO_KEY.get(shape_label, "auto")
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        tributary_options = None
        target_tributary_index: int | None = None
        if self.river_tributary_enabled_var.get():
            tributary_options = self._build_tributary_options()
            if tributary_options is None:
                return
            target_tributary_index = len(self.river_path) - 1
        generation_results = []
        affected_paths: set[str] = set()
        old_texture_paths: set[str] = set()
        background_paths_used: dict[str, str | None] = {}  # hex_id -> original texture path (relative)

        skip_origin = branch_mode == "tributary"
        # Dla dopływu: pobierz stronę wejścia do głównego nurtu
        tributary_entry_to_main = getattr(self, "_tributary_entry_side", None)
        
        for idx, hex_id in enumerate(self.river_path):
            if skip_origin and idx == 0:
                generation_results.append(None)
                continue
            
            # Dla dopływu pierwszy generowany heks (idx=1) ma specjalne wyjście
            if skip_origin and idx == 1 and tributary_entry_to_main:
                # Dopływ WYCHODZI w kierunku głównego nurtu (opposite entry_to_main)
                # i WCHODZI z kierunku następnego heksu dopływu
                exit_side = tributary_entry_to_main
                if len(segments) > 1:
                    # Wejście z następnego segmentu (odwrotność kierunku do następnego heksu)
                    entry_side = SIDE_OPPOSITE[AXIAL_DIRECTION_TO_SIDE[segments[1]]]
                else:
                    # Tylko 2 heksy w dopływie - wejście naprzeciw wyjścia
                    entry_side = SIDE_OPPOSITE[exit_side]
            else:
                entry_side, exit_side = self._river_entry_exit_for_index(idx, segments)
            if (
                tributary_options
                and target_tributary_index is not None
                and idx == target_tributary_index
                and (entry_side == tributary_options.entry_side or exit_side == tributary_options.entry_side)
            ):
                messagebox.showwarning(
                    "Dopływ",
                    "Dopływ nie może zaczynać się na tej samej krawędzi co wejście lub wyjście głównego nurtu.",
                    parent=self.root,
                )
                return
            shape, shape_direction = self._river_determine_shape(idx, segments, shape_preference)
            terrain = self.hex_data.setdefault(hex_id, {
                "terrain_key": "teren_płaski",
                "move_mod": 0,
                "defense_mod": 0,
            })
            texture_rel = terrain.get("texture")
            background_path = None
            if texture_rel and "river" in texture_rel:
                old_texture_paths.add(texture_rel)
            if hex_id not in background_paths_used:
                background_paths_used[hex_id] = None

            output_filename = f"hex_{hex_id.replace(',', '_')}_river_{timestamp}_{idx:02d}.png"
            output_path = RIVER_OUTPUT_DIR / output_filename
            current_tributary = None
            if tributary_options and target_tributary_index is not None and idx == target_tributary_index:
                current_tributary = tributary_options

            options = RiverCenterlineOptions(
                grid_size=grid_size,
                background=background_path,
                entry_side=entry_side,
                exit_side=exit_side,
                shape=shape,
                shape_strength=strength,
                shape_direction=shape_direction,
                noise_amplitude=noise,
                noise_frequency=frequency,
                seed=seed_base + idx,
                bank_offset=bank_offset,
                bank_variation=bank_variation,
                tributary=current_tributary,
            )
            try:
                result = generate_centerline(options, output_path)
            except Exception as exc:  # noqa: BLE001
                messagebox.showerror(
                    "Generator rzeki",
                    f"Nie udało się wygenerować tekstury dla {hex_id}: {exc}",
                    parent=self.root,
                )
                for produced in generation_results:
                    if produced is None:
                        continue
                    try:
                        produced.image_path.unlink(missing_ok=True)
                        produced.metadata_path.unlink(missing_ok=True)
                    except Exception:
                        pass
                return
            generation_results.append(result)
            if texture_rel:
                affected_paths.add(texture_rel)

        for idx, hex_id in enumerate(self.river_path):
            record = self.hex_data.setdefault(hex_id, {
                "terrain_key": "teren_płaski",
                "move_mod": 0,
                "defense_mod": 0,
            })
            result = generation_results[idx]
            if result is None:
                continue
            # Zapisz kierunki wejścia/wyjścia dla auto-łączenia jezior
            if skip_origin and idx == 1 and tributary_entry_to_main:
                exit_side = tributary_entry_to_main
                if len(segments) > 1:
                    entry_side = SIDE_OPPOSITE[AXIAL_DIRECTION_TO_SIDE[segments[1]]]
                else:
                    entry_side = SIDE_OPPOSITE[exit_side]
            else:
                entry_side, exit_side = self._river_entry_exit_for_index(idx, segments)
            record["river_entry_side"] = entry_side
            record["river_exit_side"] = exit_side
            record["river_bank_offset"] = bank_offset
            record["river_bank_variation"] = bank_variation
            if tributary_options and target_tributary_index is not None and idx == target_tributary_index:
                record["tributary_entry_side"] = tributary_options.entry_side
                record["tributary_bank_offset"] = tributary_options.bank_offset
                record["tributary_bank_variation"] = tributary_options.bank_variation
            rel_path = to_rel(str(result.image_path))
            record["texture"] = rel_path
            record["texture_grid"] = grid_size
            record["river_metadata_path"] = to_rel(str(result.metadata_path))
            record["river_has_tributary"] = bool(result.metadata.get("tributary_present"))
            # Zapisz original_background dla przyszłych regeneracji (dopływy, modyfikacje)
            orig_bg = background_paths_used.get(hex_id)
            if orig_bg:
                result.metadata["original_background"] = orig_bg
            record["river_generation_meta"] = result.metadata
            affected_paths.add(rel_path)

        if affected_paths:
            self.hex_texture_cache = {
                key: value for key, value in self.hex_texture_cache.items() if key[0] not in affected_paths
            }

        for old_path in old_texture_paths:
            self._delete_hex_texture_if_unused(old_path)

        self.draw_grid()
        self.auto_save_and_export("wygenerowano rzekę")
        self.river_seed_var.set(seed_base + len(self.river_path))
        produced_count = sum(1 for item in generation_results if item is not None)
        summary_label = "tekstur rzeki" if branch_mode != "tributary" else "tekstur dopływu"
        messagebox.showinfo(
            "Generator rzeki",
            f"Zapisano {produced_count} nowych {summary_label}.",
            parent=self.root,
        )
        self.clear_river_path()

    def _river_entry_exit_for_index(
        self,
        index: int,
        segments: list[tuple[int, int]],
    ) -> tuple[str, str]:
        """Oblicza krawędzie wejścia i wyjścia rzeki dla heksu o danym indeksie.
        
        Logika:
        - Dla pierwszego heksu (index=0): wejście to przeciwległa krawędź do kierunku 
          pierwszego segmentu, wyjście to krawędź w kierunku pierwszego segmentu.
        - Dla ostatniego heksu (index=len(segments)): wejście to krawędź z której 
          przyszliśmy (przeciwległa do ostatniego segmentu), wyjście to przeciwległa 
          krawędź wejścia (rzeka "wychodzi" prosto przed siebie).
        - Dla heksów środkowych: wejście z poprzedniego segmentu, wyjście do następnego.
        """
        if not segments:
            return "top", "bottom"
        
        if index == 0:
            # Pierwszy heks: wyjście w kierunku pierwszego segmentu
            exit_side = AXIAL_DIRECTION_TO_SIDE[segments[0]]
            entry_side = SIDE_OPPOSITE[exit_side]
            return entry_side, exit_side
        
        if index >= len(segments):
            # Ostatni heks: wejście z kierunku ostatniego segmentu
            # Ostatni segment wskazuje SKĄD przyszliśmy do tego heksu
            incoming_direction = segments[-1]
            entry_side = SIDE_OPPOSITE[AXIAL_DIRECTION_TO_SIDE[incoming_direction]]
            # Wyjście: kontynuujemy w tym samym kierunku (przeciwległa krawędź wejścia)
            exit_side = SIDE_OPPOSITE[entry_side]
            return entry_side, exit_side
        
        # Heksy środkowe: wejście z poprzedniego segmentu, wyjście do następnego
        entry_side = SIDE_OPPOSITE[AXIAL_DIRECTION_TO_SIDE[segments[index - 1]]]
        exit_side = AXIAL_DIRECTION_TO_SIDE[segments[index]]
        return entry_side, exit_side

    def _river_determine_shape(
        self,
        index: int,
        segments: list[tuple[int, int]],
        preference: str,
    ) -> tuple[str, int | None]:
        total_hexes = len(segments) + 1
        pref = preference if preference in {"auto", "straight", "curve", "turn"} else "auto"
        if pref == "auto":
            entry_side, exit_side = self._river_entry_exit_for_index(index, segments)
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

    # === NARZĘDZIE DRÓG ===

    def toggle_road_section_visibility(self) -> None:
        self._set_road_section_visibility(not self._road_section_expanded)

    def _set_road_section_visibility(self, visible: bool) -> None:
        self._road_section_expanded = visible
        if visible:
            self.road_section_container.pack(fill=tk.X, padx=5, pady=(0, 4), after=self.road_section_toggle_button)
            self.road_section_toggle_button.config(text="[-] Drogi (beta)")
        else:
            self.road_section_container.pack_forget()
            self.road_section_toggle_button.config(text="[+] Drogi (beta)")

    # === FUNKCJE TORÓW KOLEJOWYCH ===
    
    def toggle_railway_section_visibility(self) -> None:
        self._set_railway_section_visibility(not self._railway_section_expanded)

    def _set_railway_section_visibility(self, visible: bool) -> None:
        self._railway_section_expanded = visible
        if visible:
            self.railway_section_container.pack(fill=tk.X, padx=5, pady=(0, 4), after=self.railway_section_toggle_button)
            self.railway_section_toggle_button.config(text="[-] Tory kolejowe (beta)")
        else:
            self.railway_section_container.pack_forget()
            self.railway_section_toggle_button.config(text="[+] Tory kolejowe (beta)")

    def _update_railway_status(self) -> None:
        """Aktualizuje status i waliduje wybrane boki."""
        entry = self.railway_entry_side_var.get()
        exit_side = self.railway_exit_side_var.get()
        
        if not entry or not exit_side:
            self.railway_status_var.set("Wybierz 2 boki heksa")
            return
        
        if entry == exit_side:
            self.railway_status_var.set("❌ Entry i exit muszą być różne!")
            return
        
        # Sprawdź czy to tor prosty czy zakrzywiony
        is_straight = SIDE_OPPOSITE.get(entry) == exit_side
        track_type = "prosty" if is_straight else "zakrzywiony"
        
        self.railway_status_var.set(f"✓ Tor {track_type}: {entry} → {exit_side}")

    def generate_railway_for_hex(self) -> None:
        """Generuje teksturę torów dla aktualnie wybranego heksa."""
        if not generate_railway:
            messagebox.showerror(
                "Błąd",
                "Generator torów nie jest dostępny (brak modułu generate_railway_hex_tile.py)",
                parent=self.root,
            )
            return
        
        # Sprawdź czy wybrano heks
        if not self.selected_hex:
            messagebox.showwarning(
                "Brak heksa",
                "Najpierw wybierz heks na mapie (kliknij na heks).",
                parent=self.root,
            )
            return
        
        # Walidacja boków
        entry_side = self.railway_entry_side_var.get()
        exit_side = self.railway_exit_side_var.get()
        
        if not entry_side or not exit_side:
            messagebox.showwarning(
                "Brak konfiguracji",
                "Wybierz boki wejścia i wyjścia toru.",
                parent=self.root,
            )
            return
        
        if entry_side == exit_side:
            messagebox.showwarning(
                "Niepoprawna konfiguracja",
                "Boki wejścia i wyjścia muszą być różne!",
                parent=self.root,
            )
            return
        
        # Zbierz dojazdy
        junctions = []
        for side, var in self.railway_junctions_vars.items():
            if var.get():
                junctions.append(side)
        
        # Pobierz pozostałe parametry
        railway_type = self.railway_type_var.get()
        junction_double = self.railway_junction_double_var.get()
        
        try:
            seed = int(self.railway_seed_var.get())
        except ValueError:
            seed = 42
        
        # Sprawdź czy istnieje tło dla heksa
        q, r = self.selected_hex
        hex_key = f"{q}_{r}"
        
        # Pobierz istniejącą teksturę lub None
        existing_texture = self.hex_data.get(hex_key, {}).get("hex_texture_path")
        background_path = None
        
        if existing_texture:
            # Użyj istniejącej tekstury jako tła
            bg_file = fix_image_path(existing_texture)
            if bg_file.exists():
                background_path = bg_file
        
        # Nazwa pliku wyjściowego
        output_filename = f"railway_{hex_key}_{entry_side}_{exit_side}_{railway_type}.png"
        output_path = (HEX_TEXTURE_DIR / "railway_tool") / output_filename
        
        # Utwórz opcje
        options = RailwayOptions(
            grid_size=DEFAULT_HEX_TEXTURE_GRID_SIZE,
            background=background_path,
            entry_side=entry_side,
            exit_side=exit_side,
            railway_type=railway_type,
            junctions=junctions,
            junction_double_track=junction_double,
            seed=seed,
        )

        if normalize_railway_options:
            options, _notes = normalize_railway_options(options)
            if _notes:
                print(f"[Railway Semantics] {hex_key}: " + "; ".join(_notes))
        
        try:
            # Generuj tory
            result = generate_railway(options, output_path)
            
            # Zapisz w metadanych heksa
            if hex_key not in self.hex_data:
                self.hex_data[hex_key] = {}
            
            # Zapisz ścieżkę do wygenerowanej tekstury
            rel_path = to_rel(str(result.image_path))
            self.hex_data[hex_key]["hex_texture_path"] = rel_path
            
            # Opcjonalnie dodaj metadane torów
            self.hex_data[hex_key]["railway_config"] = {
                "entry_side": entry_side,
                "exit_side": exit_side,
                "railway_type": railway_type,
                "junctions": junctions,
                "junction_double_track": junction_double,
                "seed": seed,
            }
            
            # Odśwież teksturę
            self.clear_texture_caches()
            self.redraw_canvas()

            messagebox.showinfo(
                "Sukces",
                f"Wygenerowano tory kolejowe!\n\nPlik: {output_path.name}\n"
                f"Typ: {railway_type}\n"
                f"Rozjazdy: {len(junctions)}",
                parent=self.root,
            )
            
        except Exception as e:
            messagebox.showerror(
                "Błąd generowania",
                f"Nie udało się wygenerować torów:\n\n{e}",
                parent=self.root,
            )
            import traceback
            traceback.print_exc()

    # === FUNKCJE DRÓG ===
    
    def toggle_road_mode(self) -> None:
        self._set_road_mode(not self.road_mode_active)

    def _start_crossroads_mode(self) -> None:
        """Rozpoczyna tryb dodawania skrzyżowania z wybranego heksu (jak dopływ w rzece)."""
        if not self.road_mode_active:
            messagebox.showinfo(
                "Skrzyżowanie",
                "Najpierw włącz tryb drogi.",
                parent=self.root,
            )
            return
        
        if not self.selected_hex or self.selected_hex not in self.road_path:
            messagebox.showinfo(
                "Skrzyżowanie",
                "Najpierw zaznacz heks ze ścieżki drogi na mapie.",
                parent=self.root,
            )
            return
        
        # Ustaw tryb skrzyżowania
        self.road_crossroads_mode = True
        self.road_crossroads_hex = self.selected_hex
        self.road_crossroads_sides.clear()
        
        self.road_crossroads_status_var.set(f"Wskaż sąsiedni heks (PPM) dla odnogi od {self.selected_hex}")
        self.add_crossroads_button.config(text="❌ Anuluj skrzyżowanie", bg="#8a4a4a", command=self._cancel_crossroads_mode)
        
        self.draw_grid()
        self.set_status("Tryb skrzyżowania: kliknij PPM na zielonym sąsiednim heksie aby dodać odnogę")

    def _cancel_crossroads_mode(self) -> None:
        """Anuluje tryb dodawania skrzyżowania."""
        self.road_crossroads_mode = False
        self.road_crossroads_sides.clear()
        self.road_crossroads_hex = None
        self.road_crossroads_status_var.set("")
        self.add_crossroads_button.config(text="➕ Dodaj skrzyżowanie", bg="#5a4a3a", command=self._start_crossroads_mode)
        self.draw_grid()
        self.set_status("Anulowano tryb skrzyżowania.")

    def _get_hex_road_sides(self, hex_id: str) -> list[str]:
        """Zwraca listę boków drogi na danym heksie z metadanych."""
        record = self.hex_data.get(hex_id, {})
        meta = record.get("road_generation_meta", {})
        sides = list(meta.get("road_sides", []))
        # Dodaj entry/exit jeśli nie ma road_sides
        if not sides:
            entry = meta.get("entry_side")
            exit_side = meta.get("exit_side")
            if entry:
                sides.append(entry)
            if exit_side:
                sides.append(exit_side)
            # Dodaj crossroads jeśli są
            crossroads = meta.get("crossroads", [])
            sides.extend(crossroads)
        return list(set(sides))  # Usuń duplikaty

    def _hex_has_road(self, hex_id: str) -> bool:
        """Sprawdza czy heks ma wygenerowaną drogę."""
        record = self.hex_data.get(hex_id, {})
        return "road_generation_meta" in record

    def _update_road_modify_buttons(self) -> None:
        """Aktualizuje przyciski modyfikacji drogi w zależności od wybranego heksu."""
        has_road = self.selected_hex and self._hex_has_road(self.selected_hex)
        state = tk.NORMAL if has_road else tk.DISABLED
        
        if hasattr(self, "road_junction_t_button"):
            self.road_junction_t_button.config(state=state)
        if hasattr(self, "road_junction_x_button"):
            self.road_junction_x_button.config(state=state)
        if hasattr(self, "road_continue_button"):
            self.road_continue_button.config(state=state)
        
        if has_road:
            sides = self._get_hex_road_sides(self.selected_hex)
            sides_str = ", ".join(HEX_SIDE_LABELS_PL.get(s, s) for s in sides)
            self.road_modify_status_var.set(f"Boki drogi: {sides_str}")
        else:
            self.road_modify_status_var.set("")

    def _add_junction_t(self) -> None:
        """Dodaje skrzyżowanie T do wybranego heksu (dodaje 1 bok)."""
        if not self.selected_hex or not self._hex_has_road(self.selected_hex):
            messagebox.showinfo("Skrzyżowanie T", "Najpierw zaznacz heks z istniejącą drogą.", parent=self.root)
            return
        
        current_sides = self._get_hex_road_sides(self.selected_hex)
        
        # Znajdź dostępne boki (nie zajęte przez drogę)
        all_sides = list(HEX_SIDE_LABELS_PL.keys())
        available = [s for s in all_sides if s not in current_sides]
        
        if not available:
            messagebox.showwarning("Skrzyżowanie T", "Wszystkie boki są już zajęte!", parent=self.root)
            return
        
        # Pokaż dialog wyboru boku
        self._show_junction_side_dialog(available, junction_type="T")

    def _add_junction_x(self) -> None:
        """Dodaje skrzyżowanie X do wybranego heksu (dodaje 2 boki)."""
        if not self.selected_hex or not self._hex_has_road(self.selected_hex):
            messagebox.showinfo("Skrzyżowanie X", "Najpierw zaznacz heks z istniejącą drogą.", parent=self.root)
            return
        
        current_sides = self._get_hex_road_sides(self.selected_hex)
        
        # Znajdź dostępne boki
        all_sides = list(HEX_SIDE_LABELS_PL.keys())
        available = [s for s in all_sides if s not in current_sides]
        
        if len(available) < 2:
            messagebox.showwarning("Skrzyżowanie X", "Za mało wolnych boków dla skrzyżowania X!", parent=self.root)
            return
        
        # Pokaż dialog wyboru boków
        self._show_junction_side_dialog(available, junction_type="X")

    def _show_junction_side_dialog(self, available_sides: list[str], junction_type: str) -> None:
        """Pokazuje dialog wyboru boków dla skrzyżowania."""
        dialog = tk.Toplevel(self.root)
        dialog.title(f"Skrzyżowanie {junction_type}")
        dialog.geometry("300x280")
        dialog.configure(bg="darkolivegreen")
        
        max_select = 1 if junction_type == "T" else 2
        
        tk.Label(
            dialog, 
            text=f"Wybierz {'bok' if max_select == 1 else '2 boki'} dla odnogi:",
            bg="darkolivegreen", fg="white", font=("Arial", 10, "bold"),
        ).pack(pady=10)
        
        # Checkboxy
        side_vars = {}
        for side in available_sides:
            var = tk.BooleanVar(value=False)
            side_vars[side] = var
            
            cb = tk.Checkbutton(
                dialog,
                text=HEX_SIDE_LABELS_PL[side].title(),
                variable=var,
                bg="darkolivegreen", fg="white",
                selectcolor="#4a6a4a",
                activebackground="darkolivegreen",
                activeforeground="white",
            )
            cb.pack(anchor="w", padx=20, pady=2)
        
        def apply_junction():
            selected = [s for s, var in side_vars.items() if var.get()]
            if len(selected) < max_select:
                messagebox.showwarning(
                    "Wybór boków",
                    f"Wybierz {'co najmniej 1 bok' if max_select == 1 else 'dokładnie 2 boki'}.",
                    parent=dialog,
                )
                return
            if len(selected) > max_select:
                selected = selected[:max_select]
            
            dialog.destroy()
            self._regenerate_road_with_junction(self.selected_hex, selected)
        
        tk.Button(
            dialog,
            text="Zastosuj",
            command=apply_junction,
            bg="#4a6a4a", fg="white",
        ).pack(pady=10)

    def _regenerate_road_with_junction(self, hex_id: str, new_sides: list[str]) -> None:
        """Regeneruje teksturę drogi z dodatkowymi bokami."""
        if RoadOptions is None or generate_road is None:
            messagebox.showerror("Generator", "Generator dróg niedostępny.", parent=self.root)
            return
        
        record = self.hex_data.get(hex_id, {})
        meta = record.get("road_generation_meta", {})
        
        # Zachowaj starą teksturę do usunięcia
        old_texture_rel = record.get("texture")
        
        # Pobierz istniejące boki
        current_sides = self._get_hex_road_sides(hex_id)
        all_sides = list(set(current_sides + new_sides))
        
        # Zachowaj oryginalny entry/exit z metadanych - to główna droga!
        entry_side = meta.get("entry_side")
        exit_side = meta.get("exit_side")
        
        # Jeśli nie ma w metadanych, spróbuj odtworzyć z boków
        if not entry_side or not exit_side:
            if len(current_sides) >= 2:
                entry_side = current_sides[0]
                exit_side = current_sides[1]
            elif len(all_sides) >= 2:
                entry_side = all_sides[0]
                exit_side = all_sides[1]
            else:
                entry_side = all_sides[0] if all_sides else "top"
                exit_side = SIDE_OPPOSITE.get(entry_side, "bottom")
        
        # Crossroads = wszystkie boki POZA entry i exit
        crossroads = [s for s in all_sides if s not in (entry_side, exit_side)]
        
        # Pobierz parametry z metadanych lub domyślne
        road_type = meta.get("road_type", "gruntowa")
        road_width = meta.get("width", "średnia")
        noise = meta.get("noise_amplitude", 0.3)
        seed = meta.get("seed", 42)
        
        # Pobierz tło terenu - szukamy oryginalnej tekstury terenu
        background_path = None
        terrain_key = record.get("terrain_key", "teren_płaski")
        
        # Sprawdź czy jest oryginalne tło w metadanych (zapisane przy pierwszym generowaniu)
        original_background = meta.get("original_background")
        if original_background:
            bg_abs = fix_image_path(original_background)
            if bg_abs.exists():
                background_path = bg_abs
                print(f"[Junction] Znaleziono original_background: {bg_abs}")
        
        # Jeśli nie ma w metadanych, szukaj tekstury terenu
        if not background_path and terrain_key:
            terrain_data = TERRAIN_TYPES.get(terrain_key, {})
            tex_pattern = terrain_data.get("texture_pattern")
            if tex_pattern:
                # Szukaj w katalogach z teksturami
                search_dirs = [
                    TERRAIN_DIR,
                    ASSET_ROOT / "terrain",
                    Path(__file__).parent / "assets" / "terrain",
                    Path(__file__).parent.parent / "assets" / "terrain",
                ]
                for search_dir in search_dirs:
                    if search_dir.exists():
                        matches = list(search_dir.glob(tex_pattern))
                        if matches:
                            background_path = matches[0]
                            print(f"[Junction] Znaleziono teksturę terenu: {background_path}")
                            break
        
        # Jeśli nadal nie ma tła, użyj aktualnej tekstury heksu (która może już zawierać drogę)
        # ale lepiej niż przezroczyste tło!
        if not background_path:
            current_texture = record.get("texture")
            if current_texture:
                candidate = fix_image_path(current_texture)
                if candidate.exists():
                    # UWAGA: to już zawiera drogę, więc regeneracja może być nieczysta
                    # ale przynajmniej zachowa tło terenu
                    background_path = candidate
                    print(f"[Junction] Używam aktualnej tekstury jako fallback: {candidate}")
        
        if not background_path:
            print(f"[Junction] UWAGA: Brak tła dla heksu {hex_id}, generuję na przezroczystym!")
        
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        output_filename = f"hex_{hex_id.replace(',', '_')}_road_{timestamp}_junction.png"
        output_path = ROAD_OUTPUT_DIR / output_filename
        
        options = RoadOptions(
            grid_size=64,
            background=background_path,
            entry_side=entry_side,
            exit_side=exit_side,
            road_type=road_type,
            width=road_width,
            noise_amplitude=noise,
            seed=seed,
            crossroads=crossroads if crossroads else None,
        )
        
        if normalize_road_options:
            options, _notes = normalize_road_options(options)
            if _notes:
                print(f"[Road Semantics] {hex_id}: " + "; ".join(_notes))
        
        try:
            result = generate_road(options, output_path)
        except Exception as exc:
            messagebox.showerror("Generator", f"Błąd generowania: {exc}", parent=self.root)
            return
        
        # Zaktualizuj dane heksu
        rel_path = to_rel(str(result.image_path))
        record["texture"] = rel_path
        record["texture_grid"] = 64
        record["road_metadata_path"] = to_rel(str(result.metadata_path))
        
        # Zapisz wszystkie boki w metadanych
        result.metadata["road_sides"] = all_sides
        record["road_generation_meta"] = result.metadata
        
        # Odśwież cache
        if rel_path in [key[0] for key in self.hex_texture_cache]:
            self.hex_texture_cache = {
                key: value for key, value in self.hex_texture_cache.items() if key[0] != rel_path
            }
        
        # Usuń starą teksturę jeśli nie jest już używana
        if old_texture_rel:
            self._delete_hex_texture_if_unused(old_texture_rel)
        
        self.draw_grid()
        self.auto_save_and_export("dodano skrzyżowanie")
        self._update_road_modify_buttons()
        
        sides_str = ", ".join(HEX_SIDE_LABELS_PL.get(s, s) for s in all_sides)
        messagebox.showinfo("Skrzyżowanie", f"Dodano skrzyżowanie.\nBoki: {sides_str}", parent=self.root)

    def _continue_road_from_hex(self) -> None:
        """Kontynuuje drogę z wybranego heksu."""
        if not self.selected_hex or not self._hex_has_road(self.selected_hex):
            messagebox.showinfo("Kontynuuj", "Najpierw zaznacz heks z istniejącą drogą.", parent=self.root)
            return
        
        # Włącz tryb drogi jeśli nie jest aktywny
        if not self.road_mode_active:
            self._set_road_mode(True)
        
        # Wyczyść ścieżkę i zacznij od wybranego heksu
        self.road_path.clear()
        self.road_path.append(self.selected_hex)
        
        self._road_update_status()
        self.draw_grid()
        
        sides = self._get_hex_road_sides(self.selected_hex)
        sides_str = ", ".join(HEX_SIDE_LABELS_PL.get(s, s) for s in sides)
        self.set_status(f"Kontynuuj drogę z {self.selected_hex}. Istniejące boki: {sides_str}")
        
        messagebox.showinfo(
            "Kontynuuj drogę",
            f"Ścieżka rozpoczęta od heksu {self.selected_hex}.\n"
            f"Istniejące boki drogi: {sides_str}\n\n"
            "Klikaj LPM aby dodać kolejne heksy, następnie 'Generuj drogę'.\n"
            "Nowa droga połączy się z istniejącą na skrzyżowaniu.",
            parent=self.root,
        )

    def toggle_road_crossroads_mode(self) -> None:
        """Przełącza tryb dodawania skrzyżowań (kompatybilność wsteczna)."""
        if self.road_crossroads_mode:
            self._cancel_crossroads_mode()
        else:
            self._start_crossroads_mode()

    def _set_road_mode(self, active: bool) -> None:
        if self.road_mode_active == active:
            return
        self.road_mode_active = active
        if not active:
            self.road_path.clear()
        if hasattr(self, "toggle_road_mode_button"):
            if active:
                self.toggle_road_mode_button.config(text="Wyłącz tryb drogi", bg="#6a5a4a")
            else:
                self.toggle_road_mode_button.config(text="Włącz tryb drogi", bg="#5a4a3a")
        self._road_update_status()
        self.draw_grid()
        if active:
            messagebox.showinfo(
                "Tryb drogi",
                "Tryb drogi aktywny. Kliknij LPM, aby zbudować ścieżkę, a następnie użyj 'Generuj drogę'.",
                parent=self.root,
            )

    def _road_update_status(self) -> None:
        count = len(self.road_path)
        self.road_status_var.set(f"Ścieżka drogi: {count} heksów")
        generate_state = tk.NORMAL if self.road_mode_active and count >= 2 else tk.DISABLED
        undo_state = tk.NORMAL if self.road_mode_active and count >= 1 else tk.DISABLED
        
        # Przycisk skrzyżowania aktywny gdy jest zaznaczony heks na ścieżce
        crossroads_state = tk.NORMAL if (
            self.road_mode_active and 
            count >= 1 and 
            self.selected_hex and 
            self.selected_hex in self.road_path and
            not self.road_crossroads_mode
        ) else tk.DISABLED
        
        if hasattr(self, "road_generate_button"):
            self.road_generate_button.config(state=generate_state)
        if hasattr(self, "road_undo_button"):
            self.road_undo_button.config(state=undo_state)
        if hasattr(self, "road_clear_button"):
            self.road_clear_button.config(state=undo_state)
        if hasattr(self, "add_crossroads_button") and not self.road_crossroads_mode:
            self.add_crossroads_button.config(state=crossroads_state)

    def _road_handle_left_click(self, hex_id: str) -> None:
        """Obsługuje kliknięcie w trybie drogi."""
        if hex_id in self.road_path:
            self.set_status(f"Heks {hex_id} już jest w ścieżce drogi.")
            return
        
        if self.road_path:
            last_hex = self.road_path[-1]
            try:
                last_q, last_r = map(int, last_hex.split(","))
                cur_q, cur_r = map(int, hex_id.split(","))
            except ValueError:
                return
            delta = (cur_q - last_q, cur_r - last_r)
            if delta not in AXIAL_DIRECTION_TO_SIDE:
                self.set_status(f"Heks {hex_id} nie sąsiaduje z ostatnim heksem ścieżki.")
                return
        
        self.road_path.append(hex_id)
        self.selected_hex = hex_id
        self._road_update_status()
        self.draw_grid()
        self.update_hex_info_display(hex_id)
        self.set_status(f"Dodano heks {hex_id} do ścieżki drogi.")

    def road_pop_last_hex(self) -> None:
        """Usuwa ostatni heks ze ścieżki drogi."""
        if self.road_path:
            removed = self.road_path.pop()
            self.set_status(f"Usunięto heks {removed} ze ścieżki drogi.")
            if self.road_path:
                self.selected_hex = self.road_path[-1]
            self._road_update_status()
            self.draw_grid()

    def clear_road_path(self) -> None:
        """Czyści całą ścieżkę drogi."""
        self.road_path.clear()
        self.road_crossroads_sides.clear()
        self.road_crossroads_hex = None
        self._road_update_status()
        self.draw_grid()
        self.set_status("Wyczyszczono ścieżkę drogi.")

    def _toggle_crossroads_neighbor(self, neighbor_hex: str) -> bool:
        """Przełącza bok skrzyżowania na podstawie klikniętego sąsiedniego heksu. Zwraca True jeśli obsłużono."""
        if not self.selected_hex or self.selected_hex not in self.road_path:
            return False
        
        # Oblicz deltę między wybranym heksem a sąsiadem
        try:
            tq, tr = map(int, self.selected_hex.split(","))
            nq, nr = map(int, neighbor_hex.split(","))
        except ValueError:
            return False
        
        dq, dr = nq - tq, nr - tr
        delta = (dq, dr)
        
        if delta not in AXIAL_DIRECTION_TO_SIDE:
            return False  # Nie jest sąsiadem
        
        side = AXIAL_DIRECTION_TO_SIDE[delta]
        
        # Sprawdź czy strona nie jest zajęta przez główną drogę
        idx = self.road_path.index(self.selected_hex)
        try:
            coords = [tuple(map(int, hid.split(","))) for hid in self.road_path]
            segments = []
            for i in range(len(coords) - 1):
                dq_seg = coords[i + 1][0] - coords[i][0]
                dr_seg = coords[i + 1][1] - coords[i][1]
                segments.append((dq_seg, dr_seg))
            
            entry_side, exit_side = self._road_entry_exit_for_index(idx, segments)
            if side in (entry_side, exit_side):
                # Strona zajęta - pokaż komunikat
                side_label = HEX_SIDE_LABELS_PL.get(side, side)
                self.set_status(f"Strona {side_label} jest zajęta przez główną drogę!")
                return True
        except:
            pass
        
        # Przełącz bok
        if side in self.road_crossroads_sides:
            self.road_crossroads_sides.remove(side)
            side_label = HEX_SIDE_LABELS_PL.get(side, side)
            self.set_status(f"Usunięto odnogę: {side_label}")
        else:
            self.road_crossroads_sides.append(side)
            side_label = HEX_SIDE_LABELS_PL.get(side, side)
            self.set_status(f"Dodano odnogę: {side_label}")
        
        self.road_crossroads_hex = self.selected_hex
        
        # Zaktualizuj status skrzyżowania
        if self.road_crossroads_sides:
            sides_str = ", ".join(HEX_SIDE_LABELS_PL.get(s, s) for s in self.road_crossroads_sides)
            self.road_crossroads_status_var.set(f"Odnogi: {sides_str}")
        else:
            self.road_crossroads_status_var.set("Brak odnóg - kliknij PPM na zielony heks")
        
        self.draw_grid()
        return True

    def _draw_crossroads_overlay(self) -> None:
        """Rysuje wizualizację trybu skrzyżowania - podświetla dozwolone sąsiednie heksy."""
        if not self.selected_hex or self.selected_hex not in self.hex_centers:
            return
        
        if self.selected_hex not in self.road_path:
            return
        
        cx, cy = self.hex_centers[self.selected_hex]
        s = self.hex_size
        
        # Podświetl wybrany heks (miejsce skrzyżowania) na żółto
        self.canvas.create_oval(
            cx - s * 0.7, cy - s * 0.7, cx + s * 0.7, cy + s * 0.7,
            outline="#ffaa00", width=4, fill="", dash=(5, 3),
        )
        self.canvas.create_text(
            cx, cy - s * 0.85,
            text="🔀 Skrzyżowanie",
            fill="#ffaa00",
            font=("Arial", 9, "bold"),
        )
        
        # Oblicz zajęte strony (entry/exit głównej drogi)
        idx = self.road_path.index(self.selected_hex)
        try:
            coords = [tuple(map(int, hid.split(","))) for hid in self.road_path]
            segments = []
            for i in range(len(coords) - 1):
                dq = coords[i + 1][0] - coords[i][0]
                dr = coords[i + 1][1] - coords[i][1]
                segments.append((dq, dr))
            
            entry_side, exit_side = self._road_entry_exit_for_index(idx, segments)
            occupied = {entry_side, exit_side}
        except:
            occupied = set()
        
        # Podświetl sąsiednie heksy
        try:
            tq, tr = map(int, self.selected_hex.split(","))
        except ValueError:
            return
        
        for delta, side in AXIAL_DIRECTION_TO_SIDE.items():
            nq, nr = tq + delta[0], tr + delta[1]
            neighbor_id = f"{nq},{nr}"
            
            if neighbor_id not in self.hex_centers:
                continue
            
            ncx, ncy = self.hex_centers[neighbor_id]
            
            # Czy ta strona jest zajęta przez główną drogę?
            if side in occupied:
                # Czerwony - niedostępny
                color = "#ff4444"
                label = "✖"
            else:
                # Zielony - dostępny
                if side in self.road_crossroads_sides:
                    color = "#00ff00"  # Jasny zielony - już wybrane
                    label = "✔"
                else:
                    color = "#44ff44"  # Zielony - dostępny
                    label = "➕"
            
            self.canvas.create_oval(
                ncx - s * 0.5, ncy - s * 0.5, ncx + s * 0.5, ncy + s * 0.5,
                outline=color, width=3, fill="", dash=(3, 2),
            )
            self.canvas.create_text(
                ncx, ncy,
                text=label,
                fill=color,
                font=("Arial", 14, "bold"),
            )

    def _show_crossroads_side_selector(self, hex_id: str) -> None:
        """Pokazuje dialog wyboru dodatkowych boków dla skrzyżowania."""
        dialog = tk.Toplevel(self.root)
        dialog.title("Wybierz boki dla skrzyżowania")
        dialog.geometry("300x250")
        dialog.configure(bg="darkolivegreen")
        
        tk.Label(
            dialog, 
            text=f"Skrzyżowanie na heksie {hex_id}\nZaznacz dodatkowe boki:",
            bg="darkolivegreen", fg="white", font=("Arial", 10, "bold"),
        ).pack(pady=10)
        
        # Pobierz entry/exit głównej drogi dla tego heksu
        idx = self.road_path.index(hex_id) if hex_id in self.road_path else -1
        if idx < 0:
            dialog.destroy()
            return
        
        # Oblicz które boki są zajęte przez główną drogę
        try:
            coords = [tuple(map(int, hid.split(","))) for hid in self.road_path]
            segments = []
            for i in range(len(coords) - 1):
                dq = coords[i + 1][0] - coords[i][0]
                dr = coords[i + 1][1] - coords[i][1]
                segments.append((dq, dr))
            
            entry_side, exit_side = self._road_entry_exit_for_index(idx, segments)
            blocked_sides = {entry_side, exit_side}
        except:
            blocked_sides = set()
        
        # Checkboxy dla każdego boku
        side_vars = {}
        for side in HEX_SIDE_LABELS_PL.keys():
            if side in blocked_sides:
                continue  # Nie pokazuj boków zajętych przez główną drogę
            
            var = tk.BooleanVar(value=side in self.road_crossroads_sides)
            side_vars[side] = var
            
            cb = tk.Checkbutton(
                dialog,
                text=HEX_SIDE_LABELS_PL[side].title(),
                variable=var,
                bg="darkolivegreen", fg="white",
                selectcolor="#4a6a4a",
                activebackground="darkolivegreen",
                activeforeground="white",
            )
            cb.pack(anchor="w", padx=20, pady=2)
        
        def apply_selection():
            self.road_crossroads_sides = [
                side for side, var in side_vars.items() if var.get()
            ]
            self.road_crossroads_hex = hex_id  # Zapisz który heks ma skrzyżowanie
            self.draw_grid()
            dialog.destroy()
            self.set_status(f"Wybrano {len(self.road_crossroads_sides)} dodatkowych boków dla skrzyżowania")
        
        tk.Button(
            dialog,
            text="Zastosuj",
            command=apply_selection,
            bg="#4a6a4a", fg="white",
        ).pack(pady=10)

    def generate_road_path(self) -> None:
        """Generuje tekstury drogi dla zaznaczonej ścieżki."""
        if not self.road_mode_active:
            messagebox.showinfo("Tryb drogi", "Aktywuj tryb drogi, aby generować tekstury.", parent=self.root)
            return
        if len(self.road_path) < 2:
            messagebox.showwarning("Ścieżka drogi", "Dodaj co najmniej dwa heksy do ścieżki.", parent=self.root)
            return
        if RoadOptions is None or generate_road is None:
            messagebox.showerror(
                "Generator niedostępny",
                "Nie można załadować modułu generate_road_hex_tile.py.",
                parent=self.root,
            )
            return

        try:
            coords = [tuple(map(int, hid.split(","))) for hid in self.road_path]
        except ValueError:
            messagebox.showerror("Ścieżka drogi", "Nieprawidłowe współrzędne heksów.", parent=self.root)
            return

        # Oblicz segmenty
        segments: list[tuple[int, int]] = []
        for idx in range(len(coords) - 1):
            dq = coords[idx + 1][0] - coords[idx][0]
            dr = coords[idx + 1][1] - coords[idx][1]
            delta = (dq, dr)
            if delta not in AXIAL_DIRECTION_TO_SIDE:
                messagebox.showerror(
                    "Ścieżka drogi",
                    "Ścieżka zawiera heksy, które nie sąsiadują ze sobą.",
                    parent=self.root,
                )
                return
            segments.append(delta)

        # Pobierz parametry
        road_type_label = self.road_type_var.get()
        road_type = ROAD_TYPE_LABEL_TO_KEY.get(road_type_label, "gruntowa")
        
        road_width_label = self.road_width_var.get()
        road_width = ROAD_WIDTH_LABEL_TO_KEY.get(road_width_label, "średnia")
        
        try:
            noise = float(self.road_noise_var.get())
        except (TypeError, ValueError):
            noise = 0.3
        noise = max(0.0, min(noise, 1.0))

        try:
            seed_base = int(self.road_seed_var.get())
        except (TypeError, ValueError):
            seed_base = 42

        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        generation_results: list[RoadResult | None] = []
        old_texture_paths: set[str] = set()
        affected_paths: set[str] = set()
        background_paths_used: dict[str, Path | None] = {}  # hex_id -> background_path

        for idx, hex_id in enumerate(self.road_path):
            # Oblicz wejście i wyjście
            entry_side, exit_side = self._road_entry_exit_for_index(idx, segments)

            # Sprawdź czy to heks ze skrzyżowaniem
            crossroads_sides = []
            if hex_id in self.road_path and idx < len(self.road_path):
                # Jeśli aktualnie przeglądany heks ma dodatkowe boki
                if hasattr(self, 'road_crossroads_hex') and self.road_crossroads_hex == hex_id:
                    crossroads_sides = list(self.road_crossroads_sides)

            # Pobierz tło
            terrain = self.hex_data.setdefault(hex_id, {
                "terrain_key": "teren_płaski",
                "move_mod": 0,
                "defense_mod": 0,
            })
            texture_rel = terrain.get("texture")
            background_path = None
            if texture_rel:
                old_texture_paths.add(texture_rel)
                candidate = fix_image_path(texture_rel)
                if candidate.exists():
                    background_path = candidate
            
            # Jeśli nie ma tekstury, użyj domyślnej tekstury trawy
            if not background_path:
                default_textures = [
                    ASSET_ROOT / "terrain" / "hex_painted" / "flat_grass_dry_64.png",
                    ASSET_ROOT / "terrain" / "hex_painted" / "flat_grass_dense_64.png",
                    Path(__file__).parent.parent / "assets" / "terrain" / "hex_painted" / "flat_grass_dry_64.png",
                ]
                for default_tex in default_textures:
                    if default_tex.exists():
                        background_path = default_tex
                        print(f"[Road] Użyto domyślnej tekstury dla {hex_id}: {background_path}")
                        break
            
            # Zapisz użyte tło dla tego heksu
            background_paths_used[hex_id] = background_path

            output_filename = f"hex_{hex_id.replace(',', '_')}_road_{timestamp}_{idx:02d}.png"
            output_path = ROAD_OUTPUT_DIR / output_filename

            options = RoadOptions(
                grid_size=64,
                background=background_path,
                entry_side=entry_side,
                exit_side=exit_side,
                road_type=road_type,
                width=road_width,
                noise_amplitude=noise,
                seed=seed_base + idx,
                crossroads=crossroads_sides if crossroads_sides else None,
            )

            if normalize_road_options:
                options, _notes = normalize_road_options(options)
                if _notes:
                    print(f"[Road Semantics] {hex_id}: " + "; ".join(_notes))

            try:
                result = generate_road(options, output_path)
            except Exception as exc:
                messagebox.showerror(
                    "Generator drogi",
                    f"Nie udało się wygenerować tekstury dla {hex_id}: {exc}",
                    parent=self.root,
                )
                # Usuń już wygenerowane
                for produced in generation_results:
                    if produced is None:
                        continue
                    try:
                        produced.image_path.unlink(missing_ok=True)
                        produced.metadata_path.unlink(missing_ok=True)
                    except Exception:
                        pass
                return
            
            generation_results.append(result)
            if texture_rel:
                affected_paths.add(texture_rel)

        # Zapisz wyniki
        for idx, hex_id in enumerate(self.road_path):
            record = self.hex_data.setdefault(hex_id, {
                "terrain_key": "teren_płaski",
                "move_mod": 0,
                "defense_mod": 0,
            })
            result = generation_results[idx]
            if result is None:
                continue
            rel_path = to_rel(str(result.image_path))
            record["texture"] = rel_path
            record["texture_grid"] = 64
            record["road_metadata_path"] = to_rel(str(result.metadata_path))
            
            # Oblicz wszystkie boki drogi dla tego heksu
            entry_side, exit_side = self._road_entry_exit_for_index(idx, segments)
            road_sides = [entry_side, exit_side]
            # Dodaj crossroads jeśli to heks ze skrzyżowaniem
            if hex_id == self.road_crossroads_hex and self.road_crossroads_sides:
                road_sides.extend(self.road_crossroads_sides)
            result.metadata["road_sides"] = list(set(road_sides))
            
            # Zapisz original_background dla przyszłych regeneracji (skrzyżowania, modyfikacje)
            bg_used = background_paths_used.get(hex_id)
            if bg_used:
                result.metadata["original_background"] = to_rel(str(bg_used))
            record["road_generation_meta"] = result.metadata
            affected_paths.add(rel_path)

        # Odśwież cache
        if affected_paths:
            self.hex_texture_cache = {
                key: value for key, value in self.hex_texture_cache.items() if key[0] not in affected_paths
            }

        # Usuń stare, nieużywane tekstury dróg
        for old_path in old_texture_paths:
            self._delete_hex_texture_if_unused(old_path)

        self.draw_grid()
        self.auto_save_and_export("wygenerowano drogę")
        self.road_seed_var.set(str(seed_base + len(self.road_path)))
        
        produced_count = sum(1 for item in generation_results if item is not None)
        messagebox.showinfo(
            "Generator drogi",
            f"Zapisano {produced_count} nowych tekstur drogi.",
            parent=self.root,
        )
        self.clear_road_path()

    def _road_entry_exit_for_index(
        self,
        index: int,
        segments: list[tuple[int, int]],
    ) -> tuple[str, str]:
        """Oblicza krawędzie wejścia i wyjścia drogi dla heksu o danym indeksie."""
        if index == 0:
            # Pierwszy heks - wejście z przeciwnej strony niż kierunek do następnego
            exit_side = AXIAL_DIRECTION_TO_SIDE[segments[0]]
            entry_side = SIDE_OPPOSITE[exit_side]
        elif index == len(segments):
            # Ostatni heks - wyjście z przeciwnej strony niż kierunek z poprzedniego
            entry_side = SIDE_OPPOSITE[AXIAL_DIRECTION_TO_SIDE[segments[-1]]]
            exit_side = SIDE_OPPOSITE[entry_side]
        else:
            # Środkowy heks
            entry_side = SIDE_OPPOSITE[AXIAL_DIRECTION_TO_SIDE[segments[index - 1]]]
            exit_side = AXIAL_DIRECTION_TO_SIDE[segments[index]]
        return entry_side, exit_side

    def _draw_road_path_overlay(self) -> None:
        """Rysuje podświetlenie ścieżki drogi na mapie."""
        if not self.road_mode_active or not self.road_path:
            return
        
        for idx, hex_id in enumerate(self.road_path):
            if hex_id not in self.hex_centers:
                continue
            cx, cy = self.hex_centers[hex_id]
            s = self.hex_size
            
            # Kolor zależny od pozycji
            if idx == 0:
                color = "#8B4513"  # Brązowy - początek
            elif idx == len(self.road_path) - 1:
                color = "#D2691E"  # Jasnobrązowy - koniec
            else:
                color = "#A0522D"  # Sienna - środek
            
            # Rysuj okrąg
            r = s * 0.3
            self.canvas.create_oval(
                cx - r, cy - r, cx + r, cy + r,
                outline=color, width=3, fill="",
                tags=("road_overlay",),
            )
            
            # Numer kolejny
            self.canvas.create_text(
                cx, cy,
                text=str(idx + 1),
                fill=color,
                font=("Arial", 10, "bold"),
                tags=("road_overlay",),
            )
            
            # Ikona skrzyżowania (jeśli jest)
            if hex_id == self.road_crossroads_hex and self.road_crossroads_sides:
                # Rysuj krzyżyk
                cross_size = s * 0.15
                self.canvas.create_line(
                    cx - cross_size, cy, cx + cross_size, cy,
                    fill="yellow", width=2, tags=("road_overlay",)
                )
                self.canvas.create_line(
                    cx, cy - cross_size, cx, cy + cross_size,
                    fill="yellow", width=2, tags=("road_overlay",)
                )

    # ========================
    # FUNKCJE TORÓW KOLEJOWYCH
    # ========================

    def toggle_railway_mode(self) -> None:
        """Przełącza tryb interaktywny torów kolejowych."""
        self._set_railway_mode(not self.railway_mode_active)

    def _set_railway_mode(self, active: bool) -> None:
        """Ustawia tryb torów kolejowych."""
        if self.railway_mode_active == active:
            return
        
        self.railway_mode_active = active
        
        if not active:
            self.railway_path.clear()
            self.railway_junction_mode = False
            self.railway_junction_target_hex = None
        
        # Aktualizuj przycisk trybu
        if hasattr(self, "railway_mode_button"):
            if active:
                self.railway_mode_button.config(
                    text="Wyłącz tryb torów",
                    bg="#6a6a6a"
                )
            else:
                self.railway_mode_button.config(
                    text="Włącz tryb torów",
                    bg="#4a4a4a"
                )
        
        self._railway_update_status()
        self.draw_grid()
        
        if active:
            messagebox.showinfo(
                "Tryb torów",
                "Tryb torów aktywny. Kliknij LPM, aby zbudować trasę torów (min 2 heksy), "
                "a następnie użyj 'Generuj tory'.",
                parent=self.root
            )

    def _railway_update_status(self) -> None:
        """Aktualizuje status trasy torów."""
        count = len(self.railway_path)
        self.railway_status_var.set(f"Trasa torów: {count} heksów")
        
        # Aktualizuj przyciski
        generate_state = tk.NORMAL if self.railway_mode_active and count >= 2 else tk.DISABLED
        undo_state = tk.NORMAL if self.railway_mode_active and count >= 1 else tk.DISABLED
        clear_state = tk.NORMAL if self.railway_mode_active and count >= 1 else tk.DISABLED
        
        if hasattr(self, "railway_generate_btn"):
            self.railway_generate_btn.config(state=generate_state)
        if hasattr(self, "railway_undo_btn"):
            self.railway_undo_btn.config(state=undo_state)
        if hasattr(self, "railway_clear_btn"):
            self.railway_clear_btn.config(state=clear_state)
        
        # Przycisk rozjazdu - aktywny gdy zaznaczony heks ma tory
        junction_state = tk.DISABLED
        if self.selected_hex and self.selected_hex in self.hex_data:
            terrain = self.hex_data[self.selected_hex]
            # Sprawdź czy heks ma wygenerowane tory
            if (terrain.get("railway_entry_side") or terrain.get("railway_exit_side")) or terrain.get("railway_sides"):
                junction_state = tk.NORMAL
        
        if hasattr(self, "railway_add_junction_btn"):
            self.railway_add_junction_btn.config(state=junction_state)

    def _railway_handle_left_click(self, hex_id: str) -> None:
        """Obsługuje kliknięcie LPM w trybie torów."""
        # Tryb dodawania rozjazdu
        if self.railway_junction_mode:
            self._railway_add_junction(hex_id)
            return
        
        # Dodawanie do ścieżki torów
        if not self.railway_path:
            # Pierwszy heks
            self.railway_path.append(hex_id)
            self.set_status(f"Dodano pierwszy heks torów: {hex_id}")
        else:
            # Sprawdź czy to sąsiad
            last_hex = self.railway_path[-1]
            if self._are_hexes_neighbors(last_hex, hex_id):
                if hex_id not in self.railway_path:
                    self.railway_path.append(hex_id)
                    self.set_status(f"Dodano heks do torów: {hex_id}")
                else:
                    messagebox.showwarning(
                        "Duplikat",
                        f"Heks {hex_id} już jest w trasie torów!",
                        parent=self.root
                    )
            else:
                messagebox.showwarning(
                    "Nie sąsiaduje",
                    f"Heks {hex_id} nie sąsiaduje z poprzednim ({last_hex})!",
                    parent=self.root
                )
        
        self._railway_update_status()
        self.draw_grid()

    def _railway_handle_right_click(self, hex_id: str | None) -> None:
        """Obsługuje kliknięcie PPM w trybie torów."""
        if hex_id and hex_id in self.railway_path:
            # Cofnij ostatni heks
            self.railway_pop_last_hex()
        else:
            # Anuluj tryb torów
            self._set_railway_mode(False)

    def railway_pop_last_hex(self) -> None:
        """Usuwa ostatni heks z trasy torów."""
        if self.railway_path:
            removed = self.railway_path.pop()
            self.set_status(f"Cofnięto heks: {removed}")
            self._railway_update_status()
            self.draw_grid()

    def clear_railway_path(self) -> None:
        """Czyści całą trasę torów."""
        if self.railway_path:
            self.railway_path.clear()
            self.set_status("Wyczyszczono trasę torów")
            self._railway_update_status()
            self.draw_grid()

    def start_railway_junction_mode(self) -> None:
        """Rozpoczyna tryb dodawania rozjazdu."""
        if not self.railway_mode_active:
            messagebox.showinfo(
                "Rozjazd",
                "Najpierw włącz tryb torów.",
                parent=self.root
            )
            return
        
        if not self.selected_hex:
            messagebox.showinfo(
                "Rozjazd",
                "Najpierw zaznacz heks z torami na mapie.",
                parent=self.root
            )
            return
        
        # Sprawdź czy heks ma tory
        terrain = self.hex_data.get(self.selected_hex, {})
        if not (terrain.get("railway_entry_side") or terrain.get("railway_exit_side")):
            messagebox.showinfo(
                "Rozjazd",
                "Wybrany heks nie ma torów!",
                parent=self.root
            )
            return
        
        self.railway_junction_mode = True
        self.railway_junction_target_hex = self.selected_hex
        self.railway_junction_status_var.set(
            f"Wskaż sąsiedni heks dla rozjazdu od {self.selected_hex}"
        )
        
        if hasattr(self, "railway_add_junction_btn"):
            self.railway_add_junction_btn.config(
                text="❌ Anuluj rozjazd",
                bg="#8a4a4a",
                command=self._cancel_railway_junction_mode
            )
        
        self.draw_grid()
        self.set_status("Tryb rozjazdu: kliknij LPM na sąsiednim heksie")

    def _cancel_railway_junction_mode(self) -> None:
        """Anuluje tryb dodawania rozjazdu."""
        self.railway_junction_mode = False
        self.railway_junction_target_hex = None
        self.railway_junction_status_var.set("")
        
        if hasattr(self, "railway_add_junction_btn"):
            self.railway_add_junction_btn.config(
                text="➕ Dodaj rozjazd",
                bg="#4a4a4a",
                command=self.start_railway_junction_mode
            )
        
        self.draw_grid()
        self.set_status("Anulowano tryb rozjazdu.")

    def _railway_add_junction(self, junction_hex: str) -> None:
        """Dodaje rozjazd do heksa z torami."""
        if not self.railway_junction_target_hex:
            print("[DEBUG] Brak target hex")
            return
        
        print(f"[DEBUG] Dodawanie rozjazdu: target={self.railway_junction_target_hex}, junction={junction_hex}")
        
        # Sprawdź czy to sąsiad
        if not self._are_hexes_neighbors(self.railway_junction_target_hex, junction_hex):
            messagebox.showwarning(
                "Nie sąsiaduje",
                f"Heks {junction_hex} nie sąsiaduje z {self.railway_junction_target_hex}!",
                parent=self.root
            )
            return
        
        # Oblicz kierunek rozjazdu
        delta = self._get_hex_delta(self.railway_junction_target_hex, junction_hex)
        print(f"[DEBUG] Delta: {delta}")
        if delta not in AXIAL_DIRECTION_TO_SIDE:
            messagebox.showerror(
                "Błąd",
                "Nie można określić kierunku rozjazdu!",
                parent=self.root
            )
            return
        
        junction_side = AXIAL_DIRECTION_TO_SIDE[delta]
        print(f"[DEBUG] Junction side: {junction_side}")
        
        # Dodaj do słownika rozjazdów
        if self.railway_junction_target_hex not in self.railway_junctions:
            self.railway_junctions[self.railway_junction_target_hex] = []
        
        if junction_side not in self.railway_junctions[self.railway_junction_target_hex]:
            self.railway_junctions[self.railway_junction_target_hex].append(junction_side)
            self.railway_junction_status_var.set(
                f"Dodano rozjazd: {HEX_SIDE_LABELS_PL.get(junction_side, junction_side)}"
            )
            self.set_status(f"Dodano rozjazd z boku {junction_side}")
            
            print(f"[DEBUG] Rozjazdy dla {self.railway_junction_target_hex}: {self.railway_junctions[self.railway_junction_target_hex]}")
            
            # Regeneruj heks z rozjazdem
            self._regenerate_railway_hex_with_junctions(self.railway_junction_target_hex)
        else:
            messagebox.showinfo(
                "Duplikat",
                f"Rozjazd z tego boku już istnieje!",
                parent=self.root
            )
        
        # Zakończ tryb rozjazdu
        self._cancel_railway_junction_mode()

    def _regenerate_railway_hex_with_junctions(self, hex_id: str) -> None:
        """Regeneruje heks torów z dodanymi rozjazdami."""
        terrain = self.hex_data.get(hex_id, {})
        print(f"[DEBUG] Regeneracja rozjazdów dla {hex_id}")
        print(f"[DEBUG] Terrain data: {terrain}")
        
        # Sprawdź czy heks ma tory
        has_railway = (terrain.get("railway_entry_side") or 
                      terrain.get("railway_exit_side") or 
                      terrain.get("railway_sides"))
        
        if not has_railway:
            print(f"[DEBUG] Brak torów w heksie {hex_id}")
            return
        
        entry_side = terrain.get("railway_entry_side")
        exit_side = terrain.get("railway_exit_side")
        railway_type = terrain.get("railway_type", "jednotorowy")
        
        print(f"[DEBUG] Entry: {entry_side}, Exit: {exit_side}, Type: {railway_type}")
        
        # Pobierz rozjazdy
        junctions = self.railway_junctions.get(hex_id, [])
        print(f"[DEBUG] Junctions: {junctions}")
        
        # Typ rozjazdu - z wybranej opcji w GUI
        junction_type = getattr(self, 'railway_junction_type_var', None)
        junction_double = (junction_type.get() == "dwutorowy") if junction_type else False
        print(f"[DEBUG] Junction double track: {junction_double}")
        
        # Generuj tory z rozjazdami - użyj losowego seeda opartego o pozycję
        q, r = map(int, hex_id.split(","))
        seed = abs(hash((q, r, len(junctions)))) % 999999
        
        # Generuj tory z rozjazdami
        self._generate_railway_for_hex(
            hex_id=hex_id,
            entry_side=entry_side,
            exit_side=exit_side,
            railway_type=railway_type,
            junctions=junctions,
            junction_double=junction_double,
            seed=seed
        )
        
        self.draw_grid()

    def generate_railway_path(self) -> None:
        """Generuje tory dla całej ścieżki."""
        if len(self.railway_path) < 2:
            messagebox.showwarning(
                "Za mało heksów",
                "Trasa torów musi mieć co najmniej 2 heksy!",
                parent=self.root
            )
            return
        
        railway_type = self.railway_type_var.get()
        
        for i, hex_id in enumerate(self.railway_path):
            # Określ entry/exit na podstawie sąsiadów
            if i == 0:
                # Pierwszy heks - exit=kierunek do następnego, entry=opposite
                exit_direction = self._get_side_between_hexes(hex_id, self.railway_path[i + 1])
                exit_side = exit_direction
                entry_side = SIDE_OPPOSITE.get(exit_side) if exit_side else "top"
            elif i == len(self.railway_path) - 1:
                # Ostatni heks - entry=bok z poprzedniego, exit=opposite
                entry_direction = self._get_side_between_hexes(self.railway_path[i - 1], hex_id)
                entry_side = SIDE_OPPOSITE.get(entry_direction) if entry_direction else "bottom"
                exit_side = SIDE_OPPOSITE.get(entry_side) if entry_side else "top"
            else:
                # Środkowy heks - entry z poprzedniego, exit do następnego
                entry_direction = self._get_side_between_hexes(self.railway_path[i - 1], hex_id)
                entry_side = SIDE_OPPOSITE.get(entry_direction) if entry_direction else "top"
                exit_direction = self._get_side_between_hexes(hex_id, self.railway_path[i + 1])
                exit_side = exit_direction if exit_direction else "bottom"
            
            # Pobierz rozjazdy (jeśli są)
            junctions = self.railway_junctions.get(hex_id, [])
            
            # Generuj tory (seed automatyczny)
            self._generate_railway_for_hex(
                hex_id=hex_id,
                entry_side=entry_side,
                exit_side=exit_side,
                railway_type=railway_type,
                junctions=junctions,
                junction_double=False  # Główna trasa - bez dwutorowych rozjazdów
            )
        
        messagebox.showinfo(
            "Sukces",
            f"Wygenerowano tory dla {len(self.railway_path)} heksów!",
            parent=self.root
        )
        
        # Wyczyść trasę ale zostaw tryb aktywny
        self.railway_path.clear()
        self._railway_update_status()
        self.draw_grid()
        self.auto_save_and_export("wygenerowano tory kolejowe")

    def _generate_railway_for_hex(
        self,
        hex_id: str,
        entry_side: str | None,
        exit_side: str | None,
        railway_type: str,
        junctions: list[str],
        junction_double: bool = False,
        seed: int = None
    ) -> None:
        """Generuje teksturę torów dla pojedynczego heksa."""
        if generate_railway is None:
            messagebox.showerror(
                "Brak generatora",
                "Generator torów nie jest dostępny!",
                parent=self.root
            )
            return
        
        # Pobierz istniejące tło heksa
        terrain = self.hex_data.setdefault(hex_id, {
            "terrain_key": "teren_płaski",
            "move_mod": 0,
            "defense_mod": 0,
        })
        
        # Przygotuj ścieżkę tła (jeśli istnieje)
        background_path = None
        texture_path = terrain.get("texture")
        if texture_path:
            try:
                full_path = fix_image_path(texture_path)
                if full_path.exists():
                    background_path = full_path
            except Exception as e:
                print(f"Błąd wczytywania tła: {e}")
        
        # Przygotuj output
        output_dir = HEX_TEXTURE_DIR / "railway_tool"
        output_dir.mkdir(parents=True, exist_ok=True)
        
        # Automatyczny seed jeśli nie podano
        if seed is None:
            q, r = map(int, hex_id.split(","))
            seed = abs(hash((q, r))) % 999999
        
        filename = f"railway_{hex_id.replace(',', '_')}_{seed}.png"
        filepath = output_dir / filename
        
        # Opcje generatora
        options = RailwayOptions(
            entry_side=entry_side,
            exit_side=exit_side,
            railway_type=railway_type,
            junctions=junctions,
            junction_double_track=junction_double,
            seed=seed,
            grid_size=64,
            background=background_path
        )
        
        if normalize_railway_options:
            options, _notes = normalize_railway_options(options)
            if _notes:
                print(f"[Railway Semantics] {hex_id}: " + "; ".join(_notes))
        
        # Generuj
        try:
            result = generate_railway(options, filepath)
            
            # Aktualizuj metadane
            terrain["texture"] = to_rel(str(result.image_path))
            terrain["railway_sides"] = result.metadata.get("sides", [])
            terrain["railway_entry_side"] = entry_side
            terrain["railway_exit_side"] = exit_side
            terrain["railway_type"] = railway_type
            terrain["railway_seed"] = seed
            terrain["railway_junctions"] = junctions.copy()
            
            print(f"✓ Wygenerowano tory dla {hex_id}: {filename}")
        except Exception as e:
            messagebox.showerror(
                "Błąd generacji",
                f"Nie udało się wygenerować torów dla {hex_id}!\n{str(e)}",
                parent=self.root
            )

    def _get_side_between_hexes(self, from_hex: str, to_hex: str) -> str | None:
        """Zwraca bok po stronie to_hex względem from_hex."""
        delta = self._get_hex_delta(from_hex, to_hex)
        return AXIAL_DIRECTION_TO_SIDE.get(delta)

    def _get_hex_delta(self, from_hex: str, to_hex: str) -> tuple[int, int]:
        """Zwraca różnicę współrzędnych axial między heksami."""
        q1, r1 = map(int, from_hex.split(","))
        q2, r2 = map(int, to_hex.split(","))
        return (q2 - q1, r2 - r1)

    def _are_hexes_neighbors(self, hex1: str, hex2: str) -> bool:
        """Sprawdza czy dwa heksy sąsiadują."""
        delta = self._get_hex_delta(hex1, hex2)
        return delta in AXIAL_DIRECTION_TO_SIDE

    def _draw_railway_overlay(self) -> None:
        """Rysuje overlay trasy torów."""
        self.canvas.delete("railway_overlay")
        
        if not self.railway_mode_active:
            return
        
        # Rysuj linię łączącą heksy
        if len(self.railway_path) >= 2:
            points = []
            for hex_id in self.railway_path:
                if hex_id in self.hex_centers:
                    cx, cy = self.hex_centers[hex_id]
                    points.extend([cx, cy])
            
            if len(points) >= 4:
                self.canvas.create_line(
                    *points,
                    fill="#4a4a4a",
                    width=4,
                    dash=(10, 5),
                    tags=("railway_overlay",)
                )
        
        # Rysuj okręgi na heksach
        for idx, hex_id in enumerate(self.railway_path):
            if hex_id not in self.hex_centers:
                continue
            cx, cy = self.hex_centers[hex_id]
            s = self.hex_size
            
            # Kolor zależny od pozycji
            if idx == 0:
                color = "#2a2a2a"  # Ciemnoszary - początek
            elif idx == len(self.railway_path) - 1:
                color = "#7a7a7a"  # Jasnoszary - koniec
            else:
                color = "#4a4a4a"  # Szary - środek
            
            # Rysuj okrąg
            r = s * 0.3
            self.canvas.create_oval(
                cx - r, cy - r, cx + r, cy + r,
                outline=color, width=3, fill="",
                tags=("railway_overlay",),
            )
            
            # Numer kolejny
            self.canvas.create_text(
                cx, cy,
                text=str(idx + 1),
                fill=color,
                font=("Arial", 10, "bold"),
                tags=("railway_overlay",),
            )
        
        # Podświetl dozwolone heksy w trybie rozjazdu
        if self.railway_junction_mode and self.railway_junction_target_hex:
            if self.railway_junction_target_hex in self.hex_centers:
                tq, tr = map(int, self.railway_junction_target_hex.split(","))
                
                for delta, side in AXIAL_DIRECTION_TO_SIDE.items():
                    neighbor_id = f"{tq + delta[0]},{tr + delta[1]}"
                    if neighbor_id in self.hex_centers:
                        cx, cy = self.hex_centers[neighbor_id]
                        s = self.hex_size
                        r = s * 0.4
                        
                        self.canvas.create_oval(
                            cx - r, cy - r, cx + r, cy + r,
                            outline="#00ff00", width=2, fill="#00ff0030",
                            tags=("railway_overlay",)
                        )

    # === FUNKCJE JEZIOR ===

    def toggle_lake_section_visibility(self) -> None:
        """Przełącza widoczność sekcji jezior."""
        self._lake_section_expanded = not self._lake_section_expanded
        if self._lake_section_expanded:
            self.lake_section_container.pack(fill=tk.X, padx=5, pady=(0, 4), after=self.lake_section_toggle_button)
            self.lake_section_toggle_button.config(text="[-] Jeziora (beta)")
        else:
            self.lake_section_container.pack_forget()
            self.lake_section_toggle_button.config(text="[+] Jeziora (beta)")

    def _set_lake_section_visibility(self, visible: bool) -> None:
        """Ustawia widoczność sekcji jezior."""
        self._lake_section_expanded = visible
        if visible:
            self.lake_section_container.pack(fill=tk.X, padx=5, pady=(0, 4), after=self.lake_section_toggle_button)
            self.lake_section_toggle_button.config(text="[-] Jeziora (beta)")
        else:
            self.lake_section_container.pack_forget()
            self.lake_section_toggle_button.config(text="[+] Jeziora (beta)")

    def toggle_lake_mode(self) -> None:
        """Włącza/wyłącza tryb jezior."""
        if not render_lake:
            messagebox.showerror(
                "Błąd",
                "Generator jezior nie jest dostępny (brak modułu generate_lake_hex_tile.py)",
                parent=self.root,
            )
            return

        self.lake_mode_active = not self.lake_mode_active

        if self.lake_mode_active:
            # Wyłącz inne tryby
            if self.river_mode_active:
                self.toggle_river_mode()
            if self.road_mode_active:
                self.toggle_road_mode()
            if self.railway_mode_active:
                self.toggle_railway_mode()

            self.toggle_lake_mode_button.config(text="Wyłącz tryb jezior", bg="#0d7377")
            self.lake_status_var.set("Kliknij heks aby wybrać środek jeziora")
            self.set_status("Tryb jezior włączony")
        else:
            self.toggle_lake_mode_button.config(text="Włącz tryb jezior", bg="#1a4d5c")
            self.lake_status_var.set("Tryb jezior nieaktywny")
            self.clear_lake_cluster()
            self.set_status("Tryb jezior wyłączony")

        self._update_lake_ui_state()
        self.draw_grid()

    def _update_lake_ui_state(self) -> None:
        """Aktualizuje stan przycisków UI jezior."""
        if not self.lake_mode_active:
            self.lake_quick_single_btn.config(state=tk.DISABLED)
            self.lake_quick_y_btn.config(state=tk.DISABLED)
            self.lake_quick_7_btn.config(state=tk.DISABLED)
            return

        # Przyciski aktywne po włączeniu trybu; brak wyboru obsługiwany komunikatem w handlerach.
        self.lake_quick_single_btn.config(state=tk.NORMAL)
        self.lake_quick_y_btn.config(state=tk.NORMAL)
        self.lake_quick_7_btn.config(state=tk.NORMAL)

    def _lake_handle_left_click(self, hex_id: str) -> None:
        """Obsługuje LPM w trybie jezior."""
        if not self.lake_mode_active:
            return

        print(f"[LAKE] Kliknięto {hex_id}, cluster_size={len(self.lake_cluster)}")
        if self._is_hex_valid_for_lake(hex_id):
            if not self.lake_center_hex:
                self.lake_center_hex = hex_id
                self.selected_hex = hex_id
                self.lake_neighbor_side = None
                self.lake_status_var.set(f"Środek: {hex_id}. Opcjonalnie kliknij sąsiada dla kierunku Y.")
            else:
                if hex_id == self.lake_center_hex:
                    self.lake_center_hex = None
                    self.lake_neighbor_side = None
                    self.lake_status_var.set("Kliknij heks aby wybrać środek jeziora")
                else:
                    side = self._get_side_between_hexes(self.lake_center_hex, hex_id)
                    if side:
                        self.lake_neighbor_side = side
                        self.lake_status_var.set(f"Środek: {self.lake_center_hex}, kierunek Y: {HEX_SIDE_LABELS_PL.get(side, side)}")
                    else:
                        messagebox.showwarning(
                            "Nie sąsiaduje",
                            "Kliknięty heks nie sąsiaduje ze środkiem.",
                            parent=self.root,
                        )
        else:
            messagebox.showwarning(
                "Niedozwolony heks",
                "Ten heks ma już zawartość lub nie nadaje się na jezioro.",
                parent=self.root,
            )

        self._update_lake_ui_state()
        self._draw_lake_overlay()

    def _get_neighbor_hex_id(self, center_hex: str, side: str) -> str | None:
        try:
            dq, dr = SIDE_TO_AXIAL_DIRECTION.get(side, (None, None))
        except Exception:
            dq, dr = (None, None)
        if dq is None or dr is None:
            return None
        try:
            q, r = map(int, center_hex.split(","))
        except Exception:
            return None
        return f"{q + int(dq)},{r + int(dr)}"

    def _is_hex_in_grid(self, hex_id: str) -> bool:
        cols = int(self.config.get("grid_cols", 0) or 0)
        rows = int(self.config.get("grid_rows", 0) or 0)
        allowed = self._build_allowed_hex_ids(cols, rows)
        return hex_id in allowed

    def _build_lake_cluster_from_center(self, center_hex: str, sides: list[str]) -> list[str] | None:
        if not center_hex:
            return None
        if not self._is_hex_in_grid(center_hex) or not self._is_hex_valid_for_lake(center_hex):
            return None
        cluster = [center_hex]
        for side in sides:
            neighbor_id = self._get_neighbor_hex_id(center_hex, side)
            if not neighbor_id:
                return None
            if not self._is_hex_in_grid(neighbor_id):
                return None
            if not self._is_hex_valid_for_lake(neighbor_id):
                return None
            cluster.append(neighbor_id)
        return cluster

    def quick_generate_lake_y(self) -> None:
        """Szybko generuje układ Y (3 heksy) z wybranego heksa jako środka."""
        if not self.lake_mode_active:
            messagebox.showinfo("Tryb jezior wyłączony", "Najpierw włącz tryb jezior.", parent=self.root)
            return
        center_hex = self.lake_center_hex or self.selected_hex
        if not center_hex:
            messagebox.showinfo("Brak wyboru", "Najpierw kliknij heks środka.", parent=self.root)
            return

        if not self.lake_neighbor_side:
            messagebox.showinfo(
                "Brak kierunku Y",
                "Kliknij sąsiada środka, aby ustawić kierunek Y.",
                parent=self.root,
            )
            return

        # Jeżeli wskazano sąsiada, dopasuj Y do tego kierunku.
        preferred_pairs: list[tuple[str, str]] = []
        try:
            if self.lake_neighbor_side:
                side_to_neighbor = self.lake_neighbor_side
                side_idx = list(LAKE_HEX_SIDES).index(side_to_neighbor)
                prev_side = LAKE_HEX_SIDES[(side_idx - 1) % len(LAKE_HEX_SIDES)]
                next_side = LAKE_HEX_SIDES[(side_idx + 1) % len(LAKE_HEX_SIDES)]
                preferred_pairs = [(prev_side, side_to_neighbor), (side_to_neighbor, next_side)]
        except Exception:
            preferred_pairs = []

        # Szukamy pary sąsiadujących boków, która mieści się w siatce.
        adjacent_pairs = preferred_pairs or [
            ("top", "top_right"),
            ("top_right", "bottom_right"),
            ("bottom_right", "bottom"),
            ("bottom", "bottom_left"),
            ("bottom_left", "top_left"),
            ("top_left", "top"),
        ]

        chosen_cluster = None
        for a, b in adjacent_pairs:
            candidate = self._build_lake_cluster_from_center(center_hex, [a, b])
            if candidate:
                chosen_cluster = candidate
                break

        if not chosen_cluster:
            messagebox.showwarning(
                "Brak miejsca",
                "Nie można utworzyć układu Y w tym miejscu (brak sąsiadów lub heksy zajęte).",
                parent=self.root,
            )
            return

        self.lake_cluster = chosen_cluster
        self.generate_lake_cluster()

    def quick_generate_lake_1plus6(self) -> None:
        """Szybko generuje układ 1+6 (7 heksów) z wybranego heksa jako środka."""
        if not self.lake_mode_active:
            messagebox.showinfo("Tryb jezior wyłączony", "Najpierw włącz tryb jezior.", parent=self.root)
            return
        center_hex = self.selected_hex
        if not center_hex:
            messagebox.showinfo("Brak wyboru", "Najpierw kliknij heks środka.", parent=self.root)
            return

        sides = list(LAKE_HEX_SIDES)
        cluster = self._build_lake_cluster_from_center(center_hex, sides)
        if not cluster or len(cluster) != 7:
            messagebox.showwarning(
                "Brak miejsca",
                "Nie można utworzyć układu 1+6 w tym miejscu (brak sąsiadów lub heksy zajęte).",
                parent=self.root,
            )
            return

        self.lake_cluster = cluster
        self.generate_lake_cluster()

    def quick_generate_lake_single(self) -> None:
        """Szybko generuje pojedyncze jezioro na wybranym heksie."""
        if not self.lake_mode_active:
            messagebox.showinfo("Tryb jezior wyłączony", "Najpierw włącz tryb jezior.", parent=self.root)
            return
        center_hex = self.selected_hex
        if not center_hex:
            messagebox.showinfo("Brak wyboru", "Najpierw kliknij heks środka.", parent=self.root)
            return
        if not self._is_hex_valid_for_lake(center_hex):
            messagebox.showwarning(
                "Niedozwolony heks",
                "Ten heks ma już zawartość lub nie nadaje się na jezioro.",
                parent=self.root,
            )
            return

        try:
            grid_size = int(self.lake_grid_var.get())
        except (TypeError, ValueError):
            grid_size = DEFAULT_HEX_TEXTURE_GRID_SIZE

        self._generate_single_lake(center_hex, grid_size)
        self.draw_grid()
        self.auto_save_and_export("wygenerowano jezioro (single)")

    def _is_hex_valid_for_lake(self, hex_id: str) -> bool:
        """Sprawdza czy heks może być jeziorem (nie ma tekstury/rzeki/drogi/toru)."""
        if hex_id not in self.hex_data:
            return True  # Pusty heks OK

        terrain = self.hex_data[hex_id]
        
        # Sprawdź czy ma już teksturę
        if terrain.get("texture"):
            return False
        
        # Sprawdź czy ma rzekę/drogę/tory
        if any(key.startswith(("river_", "road_", "railway_")) for key in terrain):
            return False

        return True

    def _can_add_to_lake_cluster(self, hex_id: str) -> bool:
        """Sprawdza czy heks może być dodany do klastra."""
        if not self._is_hex_valid_for_lake(hex_id):
            return False

        if not self.lake_cluster:
            return True  # Pierwszy heks zawsze OK

        # Sprawdź czy sąsiaduje z którymkolwiek heksem w klastrze
        for cluster_hex in self.lake_cluster:
            if self._are_hexes_neighbors(hex_id, cluster_hex):
                return True

        return False

    def generate_lake_cluster(self) -> None:
        """Generuje jezioro dla wszystkich heksów w klastrze."""
        if not self.lake_cluster:
            messagebox.showinfo("Brak klastra", "Najpierw dodaj heksy do klastra.", parent=self.root)
            return

        cluster_size = len(self.lake_cluster)

        try:
            grid_size = int(self.lake_grid_var.get())
        except (TypeError, ValueError):
            grid_size = DEFAULT_HEX_TEXTURE_GRID_SIZE

        if cluster_size == 1:
            # Jednoheksowe jezioro
            self._generate_single_lake(self.lake_cluster[0], grid_size)
        elif cluster_size in (3, 7):
            # Spójny klaster cluster7: center + 1..6 bezpośrednich sąsiadów (do 7 heksów)
            self._generate_lake_cluster_cluster7(grid_size)
        else:
            messagebox.showerror(
                "Błąd klastra",
                "Dozwolone są tylko: 1 heks, 3 heksy (Y) albo 7 heksów (1+6).",
                parent=self.root,
            )
            return

        self.clear_lake_cluster()
        self.draw_grid()
        self.auto_save_and_export("wygenerowano jezioro")
        self.set_status(f"Wygenerowano jezioro ({cluster_size} heks(ów))")

    def _generate_single_lake(self, hex_id: str, grid_size: int, override_seed: int | None = None) -> None:
        """Generuje jednoheksowe jezioro."""
        # Sprawdź auto-connect
        outflow_side, outflow_width = self._detect_lake_auto_connect(hex_id)

        # Nazwa pliku
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        seed = override_seed if override_seed is not None else self.lake_seed_var.get()
        filename = f"lake_{hex_id.replace(',', '_')}_{timestamp}_s{seed}.png"
        filepath = LAKE_OUTPUT_DIR / filename

        # Przygotuj parametry
        # Rozmiar single
        size_label = (self.lake_size_var.get() or "średnie").strip().lower()
        single_radius = {
            "małe": 0.26,
            "male": 0.26,
            "mały staw": 0.26,
            "maly staw": 0.26,
            "średnie": 0.34,
            "srednie": 0.34,
            "duże": 0.42,
            "duze": 0.42,
            "duże zbiornik": 0.42,
            "duze zbiornik": 0.42,
        }.get(size_label, 0.34)

        shore_width = 2
        lake_opts_params = {
            "grid_size": grid_size,
            "background": None,
            "cluster_tile": None,  # single lake
            "seed": seed,
            "lake_radius": single_radius,
            "shore_width": shore_width,
        }
        
        if outflow_side:
            lake_opts_params["outflow_side"] = outflow_side
            lake_opts_params["outflow_width"] = outflow_width
        
        options = LakeOptions(**lake_opts_params)

        try:
            image, metadata = render_lake(options)
            
            # Zapisz obraz
            filepath.parent.mkdir(parents=True, exist_ok=True)
            image.save(filepath)
            
            # Zapisz metadane
            terrain = self.hex_data.setdefault(hex_id, {})
            terrain["texture"] = to_rel(str(filepath))
            terrain["lake_mode"] = "lake1"
            terrain["lake_outflow_side"] = outflow_side
            terrain["lake_outflow_width"] = outflow_width if outflow_side else None
            terrain["lake_seed"] = seed
            terrain["lake_radius"] = float(single_radius)
            terrain["lake_shore_width"] = int(shore_width)

            print(f"✓ Wygenerowano jezioro dla {hex_id}: {filename}")
        except Exception as e:
            messagebox.showerror(
                "Błąd generacji",
                f"Nie udało się wygenerować jeziora!\n{str(e)}",
                parent=self.root,
            )

    def _generate_lake_cluster_3hex(self, grid_size: int) -> None:
        """Generuje klaster 3-heksowy. Środkowy heks ma outflow, pozostałe są kontynuacją."""
        if len(self.lake_cluster) != 3:
            messagebox.showerror(
                "Błąd klastra",
                "Klaster 3-heksowy wymaga dokładnie 3 heksów!",
                parent=self.root,
            )
            return

        # Zachowaj kompatybilność: 3-heksowy klaster jest szczególnym przypadkiem cluster7.
        self._generate_lake_cluster_cluster7(grid_size, require_size=3)
        return

    def _generate_lake_cluster_cluster7(self, grid_size: int, require_size: int | None = None) -> None:
        """Generuje spójny klaster jeziora dla układu cluster7.

        Obsługuje 2..7 heksów: jeden center + 1..6 bezpośrednich sąsiadów.
        Jeśli require_size jest ustawione, wymusza dokładną liczbę heksów.
        """
        if require_size is not None and len(self.lake_cluster) != require_size:
            messagebox.showerror(
                "Błąd klastra",
                f"Klaster wymaga dokładnie {require_size} heksów!",
                parent=self.root,
            )
            return

        if len(self.lake_cluster) < 2:
            messagebox.showerror(
                "Błąd klastra",
                "Klaster wymaga co najmniej 3 heksów (Y) lub 7 heksów (1+6).",
                parent=self.root,
            )
            return

        if len(self.lake_cluster) > 7:
            messagebox.showerror(
                "Błąd klastra",
                "Klaster może mieć maksymalnie 7 heksów (center + 6 sąsiadów).",
                parent=self.root,
            )
            return

        if len(self.lake_cluster) not in (3, 7):
            messagebox.showerror(
                "Błąd klastra",
                "Dozwolone są tylko: 3 heksy (Y) albo 7 heksów (1+6).",
                parent=self.root,
            )
            return

        # Wybierz center automatycznie: heks, który sąsiaduje ze wszystkimi pozostałymi.
        center_hex: str | None = None
        neighbor_tile_for_hex: dict[str, str] = {}

        def _side_order(side: str) -> int:
            try:
                return list(LAKE_HEX_SIDES).index(side)
            except Exception:
                return 999

        for candidate in self.lake_cluster:
            mapping: dict[str, str] = {}
            ok = True
            for other in self.lake_cluster:
                if other == candidate:
                    continue
                tile_name = self._get_side_between_hexes(candidate, other)
                if not tile_name:
                    ok = False
                    break
                mapping[other] = tile_name
            if ok:
                # Walidacja kształtu Y: 3 heksy, dwa ramiona NIE mogą być przeciwległe
                if len(self.lake_cluster) == 3:
                    sides = list(mapping.values())
                    if len(sides) != 2:
                        ok = False
                    else:
                        if SIDE_OPPOSITE.get(sides[0]) == sides[1]:
                            ok = False
                if ok:
                    center_hex = candidate
                    neighbor_tile_for_hex = mapping
                    break

        if not center_hex:
            messagebox.showerror(
                "Błąd klastra",
                "Klaster musi mieć formę: 3 heksy w układzie Y albo 7 heksów (1+6).\n"
                "Tip: kliknij najpierw heks środka, a potem sąsiadów.",
                parent=self.root,
            )
            return

        neighbors = [h for h in self.lake_cluster if h != center_hex]

        # cluster_neighbors: lista pozycji (np. bottom, top_left...) aktywnych względem center
        neighbor_positions = [neighbor_tile_for_hex[h] for h in neighbors if h in neighbor_tile_for_hex]
        # Stabilna kolejność (dla deterministycznych metadanych / łatwiejszego replay)
        neighbor_positions_sorted = sorted(neighbor_positions, key=_side_order)
        cluster_neighbors_tuple = tuple(neighbor_positions_sorted)

        # Sprawdź auto-connect (center lub sąsiad) i wybierz tile odpływu
        outflow_side = None
        outflow_width = None
        outflow_tile: str | None = None
        for candidate in [center_hex, *neighbors]:
            candidate_side, candidate_width = self._detect_lake_auto_connect(candidate)
            if candidate_side:
                outflow_side = candidate_side
                outflow_width = candidate_width
                outflow_tile = "center" if candidate == center_hex else neighbor_tile_for_hex.get(candidate)
                break

        # Rozmiar klastrowy (mnożnik promienia pola)
        size_label = (self.lake_size_var.get() or "średnie").strip().lower()
        cluster_scale = {
            "małe": 0.80,
            "male": 0.80,
            "mały staw": 0.80,
            "maly staw": 0.80,
            "średnie": 1.00,
            "srednie": 1.00,
            "duże": 1.25,
            "duze": 1.25,
            "duże zbiornik": 1.25,
            "duze zbiornik": 1.25,
        }.get(size_label, 1.00)

        # Global seed
        seed = self.lake_seed_var.get()
        cluster_seed = seed
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")

        print(f"[LAKE CLUSTER] Center: {center_hex}, Neighbors: {neighbors}")
        print(f"[LAKE CLUSTER] Cluster positions: center + {cluster_neighbors_tuple}")

        # --- center ---
        filename_center = f"lake_cluster_center_{center_hex.replace(',', '_')}_{timestamp}_s{cluster_seed}.png"
        filepath_center = LAKE_OUTPUT_DIR / filename_center
        cluster_shape = "y" if len(self.lake_cluster) == 3 else None
        shore_width = 2

        center_opts_params = {
            "grid_size": grid_size,
            "background": None,
            "cluster_tile": "center",
            "cluster_seed": cluster_seed,
            "cluster_neighbors": cluster_neighbors_tuple,
            "lake_radius": float(cluster_scale),
            "seed": cluster_seed,
            "cluster_shape": cluster_shape,
            "shore_width": shore_width,
        }
        if outflow_side:
            center_opts_params["outflow_side"] = outflow_side
            center_opts_params["outflow_width"] = outflow_width
            center_opts_params["outflow_tile"] = outflow_tile

        options_center = LakeOptions(**center_opts_params)

        try:
            image_center, _metadata_center = render_lake(options_center)
            filepath_center.parent.mkdir(parents=True, exist_ok=True)
            image_center.save(filepath_center)

            terrain_center = self.hex_data.setdefault(center_hex, {})
            terrain_center["texture"] = to_rel(str(filepath_center))
            terrain_center["lake_mode"] = "lake_y" if len(self.lake_cluster) == 3 else "lake_cluster7"
            terrain_center["lake_cluster_tile"] = "center"
            terrain_center["lake_cluster_seed"] = cluster_seed
            terrain_center["lake_cluster_neighbors"] = list(cluster_neighbors_tuple)
            terrain_center["lake_cluster_shape"] = cluster_shape
            terrain_center["lake_outflow_side"] = outflow_side
            terrain_center["lake_outflow_width"] = outflow_width if outflow_side else None
            terrain_center["lake_outflow_tile"] = outflow_tile if outflow_side else None
            terrain_center["lake_seed"] = cluster_seed
            terrain_center["lake_radius"] = float(cluster_scale)
            terrain_center["lake_shore_width"] = int(shore_width)

            print(f"✓ Wygenerowano center klastra: {filename_center}")
        except Exception as e:
            messagebox.showerror("Błąd", f"Nie udało się wygenerować center klastra!\n{str(e)}", parent=self.root)
            return

        # --- neighbors ---
        for neighbor_hex in neighbors:
            tile_name = neighbor_tile_for_hex.get(neighbor_hex)
            if not tile_name:
                continue

            filename_neighbor = f"lake_cluster_{tile_name}_{neighbor_hex.replace(',', '_')}_{timestamp}_s{cluster_seed}.png"
            filepath_neighbor = LAKE_OUTPUT_DIR / filename_neighbor

            options_neighbor = LakeOptions(
                grid_size=grid_size,
                background=None,
                cluster_tile=tile_name,
                cluster_seed=cluster_seed,
                cluster_neighbors=cluster_neighbors_tuple,
                lake_radius=float(cluster_scale),
                seed=cluster_seed,
                cluster_shape=cluster_shape,
                shore_width=shore_width,
                outflow_side=outflow_side,
                outflow_width=outflow_width if outflow_side else 2.2,
                outflow_tile=outflow_tile,
            )

            try:
                image_neighbor, _metadata_neighbor = render_lake(options_neighbor)
                filepath_neighbor.parent.mkdir(parents=True, exist_ok=True)
                image_neighbor.save(filepath_neighbor)

                terrain_neighbor = self.hex_data.setdefault(neighbor_hex, {})
                terrain_neighbor["texture"] = to_rel(str(filepath_neighbor))
                terrain_neighbor["lake_mode"] = "lake_y" if len(self.lake_cluster) == 3 else "lake_cluster7"
                terrain_neighbor["lake_cluster_tile"] = tile_name
                terrain_neighbor["lake_cluster_seed"] = cluster_seed
                terrain_neighbor["lake_cluster_neighbors"] = list(cluster_neighbors_tuple)
                terrain_neighbor["lake_cluster_shape"] = cluster_shape
                terrain_neighbor["lake_seed"] = cluster_seed
                terrain_neighbor["lake_radius"] = float(cluster_scale)
                terrain_neighbor["lake_shore_width"] = int(shore_width)
                terrain_neighbor["lake_outflow_side"] = outflow_side
                terrain_neighbor["lake_outflow_width"] = outflow_width if outflow_side else None
                terrain_neighbor["lake_outflow_tile"] = outflow_tile if outflow_side else None

                print(f"✓ Wygenerowano neighbor klastra: {filename_neighbor}")
            except Exception as e:
                messagebox.showerror("Błąd", f"Nie udało się wygenerować neighbor!\n{str(e)}", parent=self.root)

    def regenerate_lake_textures_from_metadata(self, only_selected: bool = False) -> None:
        """Regeneruje tekstury jezior na podstawie zapisanych metadanych.

        Użyj po zmianach w generatorze jezior, aby odświeżyć wygląd bez ręcznego
        klikania wszystkich heksów.
        """
        if LakeOptions is None or render_lake is None:
            messagebox.showerror(
                "Brak generatora",
                "Generator jezior nie jest dostępny (brak modułu generate_lake_hex_tile.py)",
                parent=self.root,
            )
            return

        if only_selected:
            if not self.selected_hex:
                messagebox.showinfo("Brak wyboru", "Najpierw wybierz heks z jeziorem.", parent=self.root)
                return
            hex_ids = [self.selected_hex]
        else:
            hex_ids = [hex_id for hex_id, data in self.hex_data.items() if isinstance(data, dict) and data.get("lake_mode")]

        if not hex_ids:
            messagebox.showinfo("Brak jezior", "Nie znaleziono jezior do regeneracji.", parent=self.root)
            return

        updated = 0
        skipped = 0
        errors = 0

        for hex_id in hex_ids:
            record = self.hex_data.get(hex_id)
            if not isinstance(record, dict):
                skipped += 1
                continue

            lake_mode = record.get("lake_mode")
            if not lake_mode:
                skipped += 1
                continue

            texture_rel = record.get("texture")
            grid_raw = record.get("texture_grid") or self.lake_grid_var.get() or DEFAULT_HEX_TEXTURE_GRID_SIZE
            try:
                grid_size = int(grid_raw)
            except (TypeError, ValueError):
                grid_size = DEFAULT_HEX_TEXTURE_GRID_SIZE

            lake_radius = record.get("lake_radius")
            if lake_radius is None:
                lake_radius = 0.34 if lake_mode == "lake1" else 1.00

            shore_width = record.get("lake_shore_width")
            if shore_width is None:
                shore_width = 2

            seed = record.get("lake_seed") or record.get("lake_cluster_seed") or 1
            outflow_side = record.get("lake_outflow_side")
            outflow_width = record.get("lake_outflow_width")
            outflow_tile = record.get("lake_outflow_tile")

            cluster_tile = record.get("lake_cluster_tile")
            cluster_seed = record.get("lake_cluster_seed")
            cluster_neighbors = record.get("lake_cluster_neighbors")
            cluster_shape = record.get("lake_cluster_shape")

            options = LakeOptions(
                grid_size=grid_size,
                background=None,
                seed=int(seed),
                lake_radius=float(lake_radius),
                shore_width=int(shore_width),
                outflow_side=outflow_side,
                outflow_width=float(outflow_width) if outflow_width else 2.2,
                outflow_tile=str(outflow_tile) if outflow_tile else None,
                cluster_tile=str(cluster_tile) if cluster_tile else None,
                cluster_seed=int(cluster_seed) if cluster_seed is not None else None,
                cluster_neighbors=tuple(cluster_neighbors) if cluster_neighbors else None,
                cluster_shape=str(cluster_shape) if cluster_shape else None,
            )

            try:
                image, _metadata = render_lake(options)

                if texture_rel:
                    texture_path = fix_image_path(texture_rel)
                else:
                    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                    filename = f"lake_regen_{hex_id.replace(',', '_')}_{timestamp}_s{seed}.png"
                    texture_path = LAKE_OUTPUT_DIR / filename
                    record["texture"] = to_rel(str(texture_path))
                    texture_rel = record["texture"]

                texture_path.parent.mkdir(parents=True, exist_ok=True)
                image.save(texture_path)

                record["lake_seed"] = int(seed)
                record["lake_radius"] = float(lake_radius)
                record["lake_shore_width"] = int(shore_width)

                if texture_rel:
                    self.hex_texture_cache = {k: v for k, v in self.hex_texture_cache.items() if k[0] != texture_rel}

                updated += 1
            except Exception as exc:
                errors += 1
                print(f"[LAKE REGEN] Nie udało się odtworzyć {hex_id}: {exc}")

        self.draw_grid()
        if updated:
            self.auto_save_and_export("regenerowano jeziora")
        self.set_status(f"Regeneracja jezior: {updated} OK, {errors} błędów, {skipped} pominiętych")

    def _detect_lake_auto_connect(self, hex_id: str) -> tuple[str | None, float | None]:
        """Wykrywa czy sąsiednie heksy mają rzeki/dopływy i zwraca outflow_side + width."""
        # Sprawdź 6 sąsiadów
        q, r = map(int, hex_id.split(","))

        def _outflow_width_from_bank(bank_offset: float | None) -> float:
            base = DEFAULT_BANK_OFFSET if bank_offset is None else float(bank_offset)
            width = max(1.2, base * 1.6)
            return width
        
        for delta, side_name in AXIAL_DIRECTION_TO_SIDE.items():
            neighbor_id = f"{q + delta[0]},{r + delta[1]}"
            
            if neighbor_id not in self.hex_data:
                continue
            
            neighbor_terrain = self.hex_data[neighbor_id]
            river_meta = neighbor_terrain.get("river_generation_meta") or {}
            if not river_meta:
                metadata_rel = neighbor_terrain.get("river_metadata_path")
                if metadata_rel:
                    metadata_path = fix_image_path(metadata_rel)
                    if metadata_path.exists():
                        try:
                            with metadata_path.open("r", encoding="utf-8") as handle:
                                river_meta = json.load(handle) or {}
                        except Exception:
                            river_meta = {}
            
            # Sprawdź entry/exit rzeki (najpierw z rekordu, potem z metadanych)
            river_entry = neighbor_terrain.get("river_entry_side") or river_meta.get("entry_side")
            river_exit = neighbor_terrain.get("river_exit_side") or river_meta.get("exit_side")
            opposite_side = SIDE_OPPOSITE.get(side_name)
            if river_entry or river_exit:
                if river_entry == opposite_side or river_exit == opposite_side:
                    # bank_offset * 6.0 = outflow_width
                    bank_offset = neighbor_terrain.get("river_bank_offset")
                    if bank_offset is None:
                        bank_offset = river_meta.get("centerline_banks", {}).get("offset", DEFAULT_BANK_OFFSET)
                    outflow_width = _outflow_width_from_bank(bank_offset)
                    print(f"[AUTO-CONNECT] Znaleziono rzekę w {neighbor_id}, entry={river_entry}, exit={river_exit}, outflow={side_name}, width={outflow_width}")
                    return side_name, outflow_width

            # Sprawdź tributary w sąsiedzie
            trib_entry = neighbor_terrain.get("tributary_entry_side")
            if not trib_entry:
                trib_meta = river_meta.get("tributary") or {}
                trib_entry = trib_meta.get("entry_side")
            if trib_entry:
                opposite_side = SIDE_OPPOSITE.get(side_name)
                if trib_entry == opposite_side:
                    # tributary ma własny bank_offset (jeśli dostępny)
                    main_bank = neighbor_terrain.get("river_bank_offset")
                    if main_bank is None:
                        main_bank = river_meta.get("centerline_banks", {}).get("offset", DEFAULT_BANK_OFFSET)
                    trib_bank = neighbor_terrain.get("tributary_bank_offset")
                    if trib_bank is None:
                        trib_meta = river_meta.get("tributary") or {}
                        trib_bank = trib_meta.get("bank_offset")
                    if trib_bank is None:
                        trib_bank = main_bank * 0.8
                    outflow_width = _outflow_width_from_bank(trib_bank)
                    print(f"[AUTO-CONNECT] Znaleziono dopływ w {neighbor_id}, entry={trib_entry}, outflow={side_name}, width={outflow_width}")
                    return side_name, outflow_width

            # Fallback: jeśli sąsiad wygląda na rzekę, a brak dopasowania entry/exit,
            # połącz na podstawie samej obecności rzeki.
            has_river = bool(river_entry or river_exit or river_meta.get("centerline_banks") or river_meta.get("shape"))
            if not has_river:
                texture_rel = neighbor_terrain.get("texture")
                if texture_rel:
                    try:
                        texture_path = fix_image_path(texture_rel)
                        texture_path.relative_to(RIVER_OUTPUT_DIR)
                        has_river = True
                    except Exception:
                        has_river = False
            if has_river:
                bank_offset = neighbor_terrain.get("river_bank_offset")
                if bank_offset is None:
                    bank_offset = river_meta.get("centerline_banks", {}).get("offset", DEFAULT_BANK_OFFSET)
                outflow_width = _outflow_width_from_bank(bank_offset)
                print(f"[AUTO-CONNECT] Fallback: rzeka w {neighbor_id}, outflow={side_name}, width={outflow_width}")
                return side_name, outflow_width

        # Nie znaleziono
        return None, None

    def clear_lake_cluster(self) -> None:
        """Czyści klaster jezior."""
        self.lake_cluster.clear()
        self.lake_center_hex = None
        self.lake_neighbor_side = None
        self.lake_status_var.set("Kliknij heks aby wybrać środek jeziora" if self.lake_mode_active else "Tryb jezior nieaktywny")
        self._clear_lake_overlay()
        self._update_lake_ui_state()

    def _draw_lake_overlay(self) -> None:
        """Rysuje overlay dla wybranego środka jeziora."""
        self._clear_lake_overlay()
        if not self.lake_mode_active:
            return

        selected_hex = getattr(self, "selected_hex", None)
        if not selected_hex or selected_hex not in self.hex_centers:
            return

        cx, cy = self.hex_centers[selected_hex]
        s = self.hex_size
        r = s * 0.45

        oval_id = self.canvas.create_oval(
            cx - r, cy - r, cx + r, cy + r,
            outline="#ffd166", width=3, fill="",
        )
        self._lake_overlay_ids.append(oval_id)

        text_id = self.canvas.create_text(
            cx, cy,
            text="◎",
            fill="#ffd166",
            font=("Arial", 14, "bold"),
        )
        self._lake_overlay_ids.append(text_id)

    def _clear_lake_overlay(self) -> None:
        """Usuwa overlay jezior z canvas."""
        for item_id in self._lake_overlay_ids:
            self.canvas.delete(item_id)
        self._lake_overlay_ids.clear()


    def open_selected_hex_texture_editor(self):
        if not getattr(self, "selected_hex", None):
            messagebox.showinfo("Brak wyboru", "Najpierw wybierz heks na mapie.")
            return
        self.open_hex_texture_editor(self.selected_hex)

    def open_hex_texture_editor(
        self,
        hex_id: str,
        *,
        grid_size: int | None = None,
        initial_pixels: list[list[str | None]] | None = None,
    ) -> None:
        # Zamknij poprzednie okno jeśli jeszcze istnieje
        if hasattr(self, "_texture_editor_window") and self._texture_editor_window:
            try:
                self._texture_editor_window.destroy()
            except tk.TclError:
                pass

        terrain = self.hex_data.setdefault(hex_id, {
            "terrain_key": "teren_płaski",
            "move_mod": 0,
            "defense_mod": 0,
        })

        candidate_grid = grid_size if grid_size is not None else terrain.get("texture_grid")
        try:
            selected_grid = int(candidate_grid) if candidate_grid is not None else DEFAULT_HEX_TEXTURE_GRID_SIZE
        except (TypeError, ValueError):
            selected_grid = DEFAULT_HEX_TEXTURE_GRID_SIZE
        if selected_grid not in HEX_TEXTURE_GRID_OPTIONS:
            selected_grid = DEFAULT_HEX_TEXTURE_GRID_SIZE

        if initial_pixels is not None:
            pixels = initial_pixels
        else:
            pixels = self._load_hex_texture_pixels(terrain.get("texture"), selected_grid)

        editor = tk.Toplevel(self.root)
        editor.title(f"Edytor tekstury heksa {hex_id}")
        editor.configure(bg="darkolivegreen")
        editor.transient(self.root)
        editor.grab_set()
        editor.geometry("820x520")
        try:
            editor.state("zoomed")
        except Exception:
            try:
                editor.attributes("-zoomed", True)
            except Exception:
                pass

        editor.grid_rowconfigure(0, weight=0)
        editor.grid_rowconfigure(1, weight=1)
        editor.grid_columnconfigure(0, weight=1)
        editor.grid_columnconfigure(1, weight=0, minsize=360)

        self._texture_editor_window = editor

        grid_size = selected_grid
        canvas_target_size = 480
        cell_size = max(14, min(28, canvas_target_size // grid_size))
        if cell_size <= 0:
            cell_size = 14
        canvas_size = grid_size * cell_size
        if CONTEXT_CANVAS_SCALE <= 1.0:
            extra_cells_per_side = 0
        else:
            extra_cells_per_side = max(1, int(math.ceil(((CONTEXT_CANVAS_SCALE - 1.0) * grid_size) / 2.0)))
        context_grid_size = grid_size + extra_cells_per_side * 2
        context_canvas_size = context_grid_size * cell_size
        grid_offset = extra_cells_per_side * cell_size

        preview_wrapper = tk.Frame(editor, bg="#111111")
        preview_wrapper.grid(row=0, column=0, rowspan=2, padx=12, pady=12, sticky="nsew")
        preview_wrapper.grid_rowconfigure(0, weight=1)
        preview_wrapper.grid_columnconfigure(0, weight=1)

        preview_canvas = tk.Canvas(
            preview_wrapper,
            width=context_canvas_size,
            height=context_canvas_size,
            bg="#111111",
            highlightthickness=0,
            takefocus=1
        )
        preview_canvas.place(relx=0.5, rely=0.5, anchor="center")

        hex_mask = self._precompute_hex_mask(grid_size)
        center = grid_size / 2.0
        mask_vertices = getattr(self, "_hex_texture_vertices", {}).get(grid_size)
        if not mask_vertices:
            radius = grid_size / 2.0 - 0.5
            mask_vertices = get_hex_vertices(center, center, radius)

        mask_radius_units = grid_size / 2.0 - 0.5
        mask_radius_px = mask_radius_units * cell_size
        q, r = map(int, hex_id.split(","))
        current_hex_id = hex_id
        neighbor_dirs = [(1, 0), (1, -1), (0, -1), (-1, 0), (-1, 1), (0, 1)]
        centers = getattr(self, "hex_centers", {})
        edge_definitions = [
            {"key": "E", "label": "Prawa krawędź", "direction": (1, 0)},
            {"key": "NE", "label": "Prawa górna krawędź", "direction": (1, -1)},
            {"key": "NW", "label": "Lewa górna krawędź", "direction": (0, -1)},
            {"key": "W", "label": "Lewa krawędź", "direction": (-1, 0)},
            {"key": "SW", "label": "Lewa dolna krawędź", "direction": (-1, 1)},
            {"key": "SE", "label": "Prawa dolna krawędź", "direction": (0, 1)},
        ]

        def canvas_offset_for_hex(target_hex_id: str, dq: int, dr: int) -> tuple[float, float]:
            current_center = centers.get(current_hex_id)
            target_center = centers.get(target_hex_id)
            units_scale = (mask_radius_units / self.hex_size) if (current_center and target_center and self.hex_size) else None
            if units_scale:
                dx_units = (target_center[0] - current_center[0]) * units_scale
                dy_units = (target_center[1] - current_center[1]) * units_scale
            else:
                dx_units = (3.0 / 2.0) * dq * mask_radius_units
                dy_units = (math.sqrt(3) * (dr + dq / 2.0)) * mask_radius_units
            dx_cells = int(round(dx_units))
            dy_cells = int(round(dy_units))
            return dx_cells * cell_size, dy_cells * cell_size

        def build_edge_mode_data(
            band_cells: int,
            existing_neighbors: dict[str, dict] | None = None,
            cached_neighbors: dict[str, dict] | None = None,
        ) -> dict[str, dict]:
            band_limit = max(EDGE_BAND_CELLS_MIN, min(EDGE_BAND_CELLS_MAX, int(band_cells)))
            data: dict[str, dict] = {}
            for entry in edge_definitions:
                dq, dr = entry["direction"]
                neighbor_id = f"{q + dq},{r + dr}"
                enabled = neighbor_id in centers
                edge_data = {
                    "key": entry["key"],
                    "label": entry["label"],
                    "direction": (dq, dr),
                    "neighbor_id": neighbor_id,
                    "enabled": enabled,
                    "dx_cells": 0,
                    "dy_cells": 0,
                    "band_mask": [[False for _ in range(grid_size)] for _ in range(grid_size)],
                    "band_distance": [[None for _ in range(grid_size)] for _ in range(grid_size)],
                    "band_max_distance": 0,
                    "neighbor_pixels": None,
                    "neighbor_texture_rel": None,
                    "neighbor_mask": hex_mask,
                    "neighbor_band_mask": [[False for _ in range(grid_size)] for _ in range(grid_size)],
                    "neighbor_band_distance": [[None for _ in range(grid_size)] for _ in range(grid_size)],
                    "neighbor_band_max_distance": 0,
                    "dirty": False,
                }
                if not enabled:
                    data[entry["key"]] = edge_data
                    continue
                dx_canvas, dy_canvas = canvas_offset_for_hex(neighbor_id, dq, dr)
                dx_cells = int(round(dx_canvas / cell_size))
                dy_cells = int(round(dy_canvas / cell_size))
                edge_data["dx_cells"] = dx_cells
                edge_data["dy_cells"] = dy_cells
                base_band = [[False for _ in range(grid_size)] for _ in range(grid_size)]
                for row in range(grid_size):
                    if not any(hex_mask[row]):
                        continue
                    for col in range(grid_size):
                        if not hex_mask[row][col]:
                            continue
                        n_row = row - dy_cells
                        n_col = col - dx_cells
                        if 0 <= n_row < grid_size and 0 <= n_col < grid_size and hex_mask[n_row][n_col]:
                            base_band[row][col] = True
                distances = [[None for _ in range(grid_size)] for _ in range(grid_size)]
                queue: deque[tuple[int, int]] = deque()
                for row in range(grid_size):
                    for col in range(grid_size):
                        if base_band[row][col]:
                            distances[row][col] = 0
                            queue.append((row, col))
                max_distance = 0
                while queue:
                    row, col = queue.popleft()
                    current_dist = distances[row][col]
                    if current_dist is None or current_dist >= band_limit - 1:
                        continue
                    for d_row, d_col in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                        n_row = row + d_row
                        n_col = col + d_col
                        if 0 <= n_row < grid_size and 0 <= n_col < grid_size and hex_mask[n_row][n_col]:
                            if distances[n_row][n_col] is None:
                                next_dist = current_dist + 1
                                distances[n_row][n_col] = next_dist
                                queue.append((n_row, n_col))
                                if next_dist > max_distance:
                                    max_distance = next_dist
                band_mask = [[distances[row][col] is not None for col in range(grid_size)] for row in range(grid_size)]
                edge_data["band_mask"] = band_mask
                edge_data["band_distance"] = distances
                edge_data["band_max_distance"] = max_distance
                neighbor_distances = [[None for _ in range(grid_size)] for _ in range(grid_size)]
                neighbor_queue: deque[tuple[int, int]] = deque()
                neighbor_source_row = [[None for _ in range(grid_size)] for _ in range(grid_size)]
                neighbor_source_col = [[None for _ in range(grid_size)] for _ in range(grid_size)]
                for row in range(grid_size):
                    band_row = band_mask[row]
                    if not any(band_row):
                        continue
                    for col in range(grid_size):
                        if not band_row[col]:
                            continue
                        nr = row - dy_cells
                        nc = col - dx_cells
                        if 0 <= nr < grid_size and 0 <= nc < grid_size and hex_mask[nr][nc]:
                            if neighbor_distances[nr][nc] is None:
                                neighbor_distances[nr][nc] = 0
                                neighbor_source_row[nr][nc] = row
                                neighbor_source_col[nr][nc] = col
                                neighbor_queue.append((nr, nc))
                neighbor_max_distance = 0
                while neighbor_queue:
                    nr, nc = neighbor_queue.popleft()
                    current_dist = neighbor_distances[nr][nc]
                    if current_dist is None or current_dist >= band_limit - 1:
                        continue
                    for d_row, d_col in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                        nnr = nr + d_row
                        nnc = nc + d_col
                        if 0 <= nnr < grid_size and 0 <= nnc < grid_size and hex_mask[nnr][nnc]:
                            if neighbor_distances[nnr][nnc] is None:
                                next_dist = current_dist + 1
                                neighbor_distances[nnr][nnc] = next_dist
                                neighbor_source_row[nnr][nnc] = neighbor_source_row[nr][nc]
                                neighbor_source_col[nnr][nnc] = neighbor_source_col[nr][nc]
                                neighbor_queue.append((nnr, nnc))
                                if next_dist > neighbor_max_distance:
                                    neighbor_max_distance = next_dist
                neighbor_band_mask = [[neighbor_distances[row][col] is not None for col in range(grid_size)] for row in range(grid_size)]
                edge_data["neighbor_band_distance"] = neighbor_distances
                edge_data["neighbor_band_mask"] = neighbor_band_mask
                edge_data["neighbor_band_max_distance"] = neighbor_max_distance
                edge_data["neighbor_source_row"] = neighbor_source_row
                edge_data["neighbor_source_col"] = neighbor_source_col
                neighbor_record = self.hex_data.get(neighbor_id)
                neighbor_texture_rel = neighbor_record.get("texture") if neighbor_record else None
                existing_entry = existing_neighbors.get(entry["key"]) if existing_neighbors else None
                if existing_entry and existing_entry.get("neighbor_id") != neighbor_id:
                    existing_entry = None
                if existing_entry and existing_entry.get("neighbor_pixels") is not None:
                    neighbor_pixels = existing_entry["neighbor_pixels"]
                else:
                    neighbor_pixels = self._load_hex_texture_pixels(
                        neighbor_texture_rel,
                        grid_size,
                    )
                if cached_neighbors:
                    cached_entry = cached_neighbors.get(neighbor_id)
                    if cached_entry:
                        cached_pixels = cached_entry.get("pixels")
                        if cached_pixels is not None:
                            neighbor_pixels = [row[:] for row in cached_pixels]
                edge_data["neighbor_pixels"] = neighbor_pixels
                if existing_entry and existing_entry.get("neighbor_texture_rel") is not None:
                    edge_data["neighbor_texture_rel"] = existing_entry.get("neighbor_texture_rel")
                else:
                    edge_data["neighbor_texture_rel"] = neighbor_texture_rel
                if existing_entry:
                    edge_data["dirty"] = existing_entry.get("dirty", False)
                has_band = any(any(row) for row in edge_data["band_mask"])
                edge_data["enabled"] = enabled and has_band
                data[entry["key"]] = edge_data
            return data

        initial_edge_band_cells = EDGE_BAND_CELLS_DEFAULT
        edge_mode_data = build_edge_mode_data(initial_edge_band_cells)

        def pixels_to_image(pixel_grid: list[list[str | None]]) -> Image.Image:
            img = Image.new("RGBA", (grid_size, grid_size), (0, 0, 0, 0))
            for row in range(grid_size):
                for col in range(grid_size):
                    color = pixel_grid[row][col]
                    if color:
                        r_c = int(color[1:3], 16)
                        g_c = int(color[3:5], 16)
                        b_c = int(color[5:7], 16)
                        img.putpixel((col, row), (r_c, g_c, b_c, 255))
            return img

        def blank_pixel_grid() -> list[list[str | None]]:
            return [[None for _ in range(grid_size)] for _ in range(grid_size)]

        def hex_to_rgba(color: str, alpha: int = 255) -> tuple[int, int, int, int]:
            return int(color[1:3], 16), int(color[3:5], 16), int(color[5:7], 16), alpha

        def create_stamp_overlay_image(pixel_grid: list[list[str | None]], alpha: int = 180) -> Image.Image:
            base = pixels_to_image(pixel_grid).resize((canvas_size, canvas_size), Image.NEAREST)
            if alpha >= 255:
                return base
            overlay = base.copy()
            overlay_data = []
            for r, g, b, a in overlay.getdata():
                if a == 0:
                    overlay_data.append((r, g, b, 0))
                else:
                    overlay_data.append((r, g, b, alpha))
            overlay.putdata(overlay_data)
            return overlay

        def build_preset_preview_photo(pixel_grid: list[list[str | None]]) -> ImageTk.PhotoImage:
            mini = pixels_to_image(pixel_grid)
            preview_bg = Image.new("RGBA", mini.size, (36, 48, 32, 255))
            preview_bg.alpha_composite(mini)
            preview = preview_bg.resize((96, 96), Image.NEAREST)
            return ImageTk.PhotoImage(preview)

        def set_pixel(grid: list[list[str | None]], row: int, col: int, color: str) -> None:
            if 0 <= row < grid_size and 0 <= col < grid_size and hex_mask[row][col]:
                grid[row][col] = color

        def set_pixel_if_empty(grid: list[list[str | None]], row: int, col: int, color: str) -> None:
            if 0 <= row < grid_size and 0 <= col < grid_size and hex_mask[row][col] and grid[row][col] is None:
                grid[row][col] = color

        def paint_disc(grid: list[list[str | None]], center_row: int, center_col: int, radius: int,
                       palette: list[str]) -> None:
            if radius <= 0:
                return
            palette_len = len(palette)
            for row in range(center_row - radius, center_row + radius + 1):
                if row < 0 or row >= grid_size:
                    continue
                for col in range(center_col - radius, center_col + radius + 1):
                    if col < 0 or col >= grid_size or not hex_mask[row][col]:
                        continue
                    dy = row - center_row
                    dx = col - center_col
                    dist = math.sqrt(dx * dx + dy * dy)
                    if dist <= radius + 0.35:
                        t = dist / max(1.0, radius)
                        idx = min(palette_len - 1, int(t * (palette_len - 1)))
                        set_pixel(grid, row, col, palette[idx])

        def paint_soft_patch(grid: list[list[str | None]], center_row: int, center_col: int,
                             radius_row: int, radius_col: int, palette: list[str]) -> None:
            palette_len = len(palette)
            for row in range(center_row - radius_row, center_row + radius_row + 1):
                if row < 0 or row >= grid_size:
                    continue
                for col in range(center_col - radius_col, center_col + radius_col + 1):
                    if col < 0 or col >= grid_size or not hex_mask[row][col]:
                        continue
                    dy = (row - center_row) / max(1.0, radius_row)
                    dx = (col - center_col) / max(1.0, radius_col)
                    dist = math.sqrt(dx * dx + dy * dy)
                    if dist <= 1.0:
                        idx = min(palette_len - 1, int(dist * (palette_len - 1)))
                        set_pixel_if_empty(grid, row, col, palette[idx])

        def _bresenham_line(r0: int, c0: int, r1: int, c1: int) -> list[tuple[int, int]]:
            """Classic Bresenham ensures the backbone stays one pixel wide."""
            path: list[tuple[int, int]] = []
            x0, y0 = c0, r0
            x1, y1 = c1, r1
            dx = abs(x1 - x0)
            sx = 1 if x0 < x1 else -1
            dy = -abs(y1 - y0)
            sy = 1 if y0 < y1 else -1
            err = dx + dy
            x, y = x0, y0
            while True:
                path.append((y, x))
                if x == x1 and y == y1:
                    break
                e2 = 2 * err
                if e2 >= dy:
                    err += dy
                    x += sx
                if e2 <= dx:
                    err += dx
                    y += sy
            return path

        def draw_polyline(grid: list[list[str | None]], points: list[tuple[int, int]], width: int,
                          palette: list[str], overwrite: bool = True) -> None:
            if len(points) < 2 or not palette:
                return
            width = max(0, width)
            palette_len = len(palette)
            path_cells: list[tuple[int, int]] = []
            for idx in range(len(points) - 1):
                r0, c0 = points[idx]
                r1, c1 = points[idx + 1]
                segment = _bresenham_line(r0, c0, r1, c1)
                if path_cells:
                    path_cells.extend(segment[1:])
                else:
                    path_cells.extend(segment)
            for row, col in path_cells:
                if row < 0 or row >= grid_size or col < 0 or col >= grid_size:
                    continue
                if not hex_mask[row][col]:
                    continue
                for dy in range(-width, width + 1):
                    target_row = row + dy
                    if target_row < 0 or target_row >= grid_size:
                        continue
                    for dx in range(-width, width + 1):
                        target_col = col + dx
                        if target_col < 0 or target_col >= grid_size or not hex_mask[target_row][target_col]:
                            continue
                        dist = math.sqrt(dx * dx + dy * dy)
                        if dist <= width + 0.35:
                            shade = dist / max(1.0, width)
                            color_idx = min(palette_len - 1, int(shade * (palette_len - 1)))
                            if overwrite or grid[target_row][target_col] is None:
                                set_pixel(grid, target_row, target_col, palette[color_idx])

        def draw_dashed_line(grid: list[list[str | None]], points: list[tuple[int, int]], spacing: float,
                             color: str) -> None:
            if len(points) < 2:
                return
            spacing = max(0.1, spacing)
            path_cells: list[tuple[int, int]] = []
            for idx in range(len(points) - 1):
                r0, c0 = points[idx]
                r1, c1 = points[idx + 1]
                segment = _bresenham_line(r0, c0, r1, c1)
                if path_cells:
                    path_cells.extend(segment[1:])
                else:
                    path_cells.extend(segment)
            if not path_cells:
                return
            distance_acc = 0.0
            last_row, last_col = path_cells[0]
            if (
                0 <= last_row < grid_size
                and 0 <= last_col < grid_size
                and hex_mask[last_row][last_col]
                and int(distance_acc / spacing) % 2 == 0
            ):
                set_pixel(grid, last_row, last_col, color)
            for row, col in path_cells[1:]:
                segment = math.sqrt((row - last_row) ** 2 + (col - last_col) ** 2)
                distance_acc += segment
                last_row, last_col = row, col
                if row < 0 or row >= grid_size or col < 0 or col >= grid_size:
                    continue
                if not hex_mask[row][col]:
                    continue
                if int(distance_acc / spacing) % 2 == 0:
                    set_pixel(grid, row, col, color)

        def fill_rect(grid: list[list[str | None]], top: int, left: int, height: int, width_rect: int,
                      palette: list[str]) -> None:
            if height <= 0 or width_rect <= 0:
                return
            palette_len = len(palette)
            for row in range(top, top + height):
                if row < 0 or row >= grid_size:
                    continue
                for col in range(left, left + width_rect):
                    if col < 0 or col >= grid_size or not hex_mask[row][col]:
                        continue
                    rel_row = (row - top) / max(1, height - 1)
                    rel_col = (col - left) / max(1, width_rect - 1)
                    weight = max(0.0, min(0.999, rel_row * 0.6 + rel_col * 0.4))
                    idx = min(palette_len - 1, int(weight * (palette_len - 1)))
                    set_pixel(grid, row, col, palette[idx])

        def sprinkle_windows(grid: list[list[str | None]], top: int, left: int, height: int, width_rect: int,
                              color: str, stride: int) -> None:
            for row in range(top, top + height):
                if row < 0 or row >= grid_size:
                    continue
                for col in range(left, left + width_rect):
                    if col < 0 or col >= grid_size or not hex_mask[row][col]:
                        continue
                    if (row + col) % stride == 0:
                        set_pixel(grid, row, col, color)

        def paint_gradient_disc(grid: list[list[str | None]], center_row: int, center_col: int,
                                radius: int, inner_color: str, outer_color: str) -> None:
            """Maluje okrąg z gradientem od środka (inner) do brzegu (outer)"""
            if radius <= 0:
                return
            inner_r = int(inner_color[1:3], 16)
            inner_g = int(inner_color[3:5], 16)
            inner_b = int(inner_color[5:7], 16)
            outer_r = int(outer_color[1:3], 16)
            outer_g = int(outer_color[3:5], 16)
            outer_b = int(outer_color[5:7], 16)
            for row in range(center_row - radius, center_row + radius + 1):
                if row < 0 or row >= grid_size:
                    continue
                for col in range(center_col - radius, center_col + radius + 1):
                    if col < 0 or col >= grid_size or not hex_mask[row][col]:
                        continue
                    dy = row - center_row
                    dx = col - center_col
                    dist = math.sqrt(dx * dx + dy * dy)
                    if dist <= radius + 0.35:
                        t = dist / max(1.0, radius)
                        r = int(inner_r + (outer_r - inner_r) * t)
                        g = int(inner_g + (outer_g - inner_g) * t)
                        b = int(inner_b + (outer_b - inner_b) * t)
                        set_pixel(grid, row, col, f"#{r:02x}{g:02x}{b:02x}")

        def add_procedural_noise(grid: list[list[str | None]], center_row: int, center_col: int,
                                 radius: int, base_color: str, noise_amount: int, seed: int) -> None:
            """Dodaje subtelny szum do istniejących pikseli w okręgu (efekt tekstury)"""
            import random
            rng = random.Random(seed)
            base_r = int(base_color[1:3], 16)
            base_g = int(base_color[3:5], 16)
            base_b = int(base_color[5:7], 16)
            for row in range(center_row - radius, center_row + radius + 1):
                if row < 0 or row >= grid_size:
                    continue
                for col in range(center_col - radius, center_col + radius + 1):
                    if col < 0 or col >= grid_size or not hex_mask[row][col]:
                        continue
                    dy = row - center_row
                    dx = col - center_col
                    dist = math.sqrt(dx * dx + dy * dy)
                    if dist <= radius and grid[row][col] is not None:
                        offset = rng.randint(-noise_amount, noise_amount)
                        r = max(0, min(255, base_r + offset))
                        g = max(0, min(255, base_g + offset))
                        b = max(0, min(255, base_b + offset))
                        set_pixel(grid, row, col, f"#{r:02x}{g:02x}{b:02x}")

        def paint_bark_texture(grid: list[list[str | None]], col_left: int, col_right: int,
                               row_top: int, row_bottom: int, bark_palette: list[str], seed: int) -> None:
            """Pionowe paski imitujące korę drzewa"""
            import random
            rng = random.Random(seed)
            palette_len = len(bark_palette)
            for row in range(row_top, row_bottom + 1):
                if row < 0 or row >= grid_size:
                    continue
                stripe_shift = rng.randint(0, 2) - 1
                for col in range(col_left, col_right + 1):
                    adj_col = col + stripe_shift
                    if adj_col < 0 or adj_col >= grid_size or not hex_mask[row][adj_col]:
                        continue
                    idx = rng.randint(0, palette_len - 1)
                    set_pixel(grid, row, adj_col, bark_palette[idx])

        def paint_specular_highlight(grid: list[list[str | None]], center_row: int, center_col: int,
                                     radius: int, color: str) -> None:
            """Dodaje jasne akcenty (refleksy światła)"""
            for row in range(center_row - radius, center_row + radius + 1):
                if row < 0 or row >= grid_size:
                    continue
                for col in range(center_col - radius, center_col + radius + 1):
                    if col < 0 or col >= grid_size or not hex_mask[row][col]:
                        continue
                    dy = row - center_row
                    dx = col - center_col
                    dist = math.sqrt(dx * dx + dy * dy)
                    if dist <= radius:
                        set_pixel(grid, row, col, color)

        def load_custom_image_presets() -> list[dict]:
            """Skanuje folder assets/terrain/presets/custom/ i ładuje PNG jako presety"""
            presets: list[dict] = []
            custom_dir = ASSET_ROOT / "terrain" / "presets" / "custom"
            try:
                custom_dir.mkdir(parents=True, exist_ok=True)
            except Exception:
                pass
            if not custom_dir.exists():
                return presets
            for png_file in sorted(custom_dir.glob("*.png")):
                try:
                    img = Image.open(png_file).convert("RGBA")
                    img.thumbnail((grid_size, grid_size), Image.Resampling.LANCZOS)
                    canvas = Image.new("RGBA", (grid_size, grid_size), (0, 0, 0, 0))
                    offset_x = (grid_size - img.width) // 2
                    offset_y = (grid_size - img.height) // 2
                    canvas.paste(img, (offset_x, offset_y), img)
                    grid = blank_pixel_grid()
                    px = canvas.load()
                    for row in range(grid_size):
                        for col in range(grid_size):
                            if not hex_mask[row][col]:
                                continue
                            r, g, b, a = px[col, row]
                            if a > 30:
                                grid[row][col] = f"#{r:02x}{g:02x}{b:02x}"
                    presets.append({
                        "id": f"custom_{png_file.stem}",
                        "name": f"📷 {png_file.stem.replace('_', ' ').title()}",
                        "pixels": grid,
                        "preview_photo": build_preset_preview_photo(grid),
                        "hotspot": (grid_size / 2.0, grid_size / 2.0),
                    })
                except Exception as exc:
                    print(f"⚠️  Nie udało się załadować {png_file.name}: {exc}")
            return presets

        def load_user_asset_presets(category_key: str) -> list[dict]:
            presets: list[dict] = []
            target_dir = CUSTOM_ASSET_ROOT / category_key
            try:
                target_dir.mkdir(parents=True, exist_ok=True)
            except Exception:
                pass
            if not target_dir.exists():
                return presets
            for meta_file in sorted(target_dir.glob("*.json")):
                try:
                    with meta_file.open("r", encoding="utf-8") as fh:
                        meta = json.load(fh)
                except Exception as exc:
                    print(f"⚠️  Nie udało się odczytać metadanych {meta_file.name}: {exc}")
                    continue
                image_path = target_dir / f"{meta_file.stem}.png"
                if not image_path.exists():
                    continue
                try:
                    img = Image.open(image_path).convert("RGBA")
                except Exception as exc:
                    print(f"⚠️  Nie udało się załadować {image_path.name}: {exc}")
                    continue
                source_grid_size = int(meta.get("grid_size", grid_size)) or grid_size
                origin_meta = meta.get("origin") or {}
                size_meta = meta.get("size") or {}
                try:
                    origin_row = int(round(origin_meta.get("row", 0)))
                    origin_col = int(round(origin_meta.get("col", 0)))
                    size_rows = int(round(size_meta.get("rows", img.height)))
                    size_cols = int(round(size_meta.get("cols", img.width)))
                    use_origin = True
                except (TypeError, ValueError):
                    origin_row = 0
                    origin_col = 0
                    size_rows = img.height
                    size_cols = img.width
                    use_origin = False

                size_rows = max(1, min(size_rows, source_grid_size))
                size_cols = max(1, min(size_cols, source_grid_size))

                if use_origin:
                    source_canvas = Image.new("RGBA", (source_grid_size, source_grid_size), (0, 0, 0, 0))
                    paste_x = max(0, min(source_grid_size - size_cols, origin_col))
                    paste_y = max(0, min(source_grid_size - size_rows, origin_row))
                    if (size_cols, size_rows) != img.size:
                        img = img.resize((size_cols, size_rows), Image.NEAREST)
                    source_canvas.paste(img, (paste_x, paste_y), img)
                else:
                    source_canvas = img
                    if source_canvas.size != (source_grid_size, source_grid_size):
                        source_canvas = source_canvas.resize((source_grid_size, source_grid_size), Image.NEAREST)

                if source_grid_size != grid_size:
                    source_canvas = source_canvas.resize((grid_size, grid_size), Image.NEAREST)

                grid = blank_pixel_grid()
                px = source_canvas.load()
                for row in range(grid_size):
                    for col in range(grid_size):
                        if not hex_mask[row][col]:
                            continue
                        r_val, g_val, b_val, a_val = px[col, row]
                        if a_val:
                            grid[row][col] = f"#{r_val:02x}{g_val:02x}{b_val:02x}"
                display_name = meta.get("name") or meta_file.stem
                hotspot_meta = meta.get("hotspot")
                if isinstance(hotspot_meta, dict):
                    hotspot_row = float(hotspot_meta.get("row", grid_size / 2.0))
                    hotspot_col = float(hotspot_meta.get("col", grid_size / 2.0))
                else:
                    bounds_meta = meta.get("bounds", {})
                    row_min = bounds_meta.get("row_min", 0)
                    row_max = bounds_meta.get("row_max", grid_size - 1)
                    col_min = bounds_meta.get("col_min", 0)
                    col_max = bounds_meta.get("col_max", grid_size - 1)
                    hotspot_row = row_min + (row_max - row_min + 1) / 2.0
                    hotspot_col = col_min + (col_max - col_min + 1) / 2.0
                presets.append({
                    "id": f"user_{category_key}_{meta_file.stem}",
                    "name": f"⭐ {display_name}",
                    "pixels": grid,
                    "preview_photo": build_preset_preview_photo(grid),
                    "hotspot": (hotspot_row, hotspot_col),
                    "meta_path": meta_file,
                    "image_path": image_path,
                    "thumb_path": target_dir / f"{meta_file.stem}_thumb.png",
                    "category_key": category_key,
                })
            return presets

        def delete_user_asset(preset: dict, category: dict) -> None:
            meta_path_raw = preset.get("meta_path")
            if not meta_path_raw:
                return
            meta_path = Path(meta_path_raw)
            confirm_parent = state.get("preset_detail_window")
            confirm = messagebox.askyesno(
                "Usuń asset",
                f"Czy na pewno usunąć asset „{preset.get('name', meta_path.stem)}”?",
                parent=confirm_parent if confirm_parent and confirm_parent.winfo_exists() else editor,
            )
            if not confirm:
                return
            files_to_remove: list[Path] = []
            for key in ("image_path", "thumb_path"):
                raw_path = preset.get(key)
                if raw_path:
                    files_to_remove.append(Path(raw_path))
            files_to_remove.append(meta_path)
            errors: list[str] = []
            for path in files_to_remove:
                try:
                    if path.exists():
                        path.unlink()
                except Exception as exc:
                    errors.append(f"{path.name}: {exc}")
            if errors:
                messagebox.showerror(
                    "Usuń asset",
                    "Nie udało się usunąć plików:\n" + "\n".join(errors),
                    parent=confirm_parent if confirm_parent and confirm_parent.winfo_exists() else editor,
                )
            else:
                if state.get("stamp_label") == preset.get("name"):
                    clear_stamp_mode()
                messagebox.showinfo(
                    "Usuń asset",
                    "Asset został usunięty.",
                    parent=confirm_parent if confirm_parent and confirm_parent.winfo_exists() else editor,
                )
            window = state.get("preset_detail_window")
            if window and window.winfo_exists():
                try:
                    window.destroy()
                except tk.TclError:
                    pass
            open_presets_for_category(category)

        def delete_all_user_assets(category: dict) -> None:
            user_key = category.get("user_key")
            if not user_key:
                return
            target_dir = CUSTOM_ASSET_ROOT / user_key
            if not target_dir.exists():
                return
            window = state.get("preset_detail_window")
            confirm = messagebox.askyesno(
                "Usuń assety",
                f"Usunąć wszystkie assety w kategorii „{category.get('label', user_key)}”?",
                parent=window if window and window.winfo_exists() else editor,
            )
            if not confirm:
                return
            errors: list[str] = []
            removed_any = False
            for meta_file in list(target_dir.glob("*.json")):
                stem = meta_file.stem
                related_files = [meta_file, target_dir / f"{stem}.png", target_dir / f"{stem}_thumb.png"]
                for path in related_files:
                    try:
                        if path.exists():
                            path.unlink()
                            removed_any = True
                    except Exception as exc:
                        errors.append(f"{path.name}: {exc}")
            if errors:
                messagebox.showerror(
                    "Usuń assety",
                    "Nie wszystkie pliki udało się usunąć:\n" + "\n".join(errors),
                    parent=window if window and window.winfo_exists() else editor,
                )
            else:
                if removed_any:
                    clear_stamp_mode()
                messagebox.showinfo(
                    "Usuń assety",
                    "Assety kategorii zostały usunięte.",
                    parent=window if window and window.winfo_exists() else editor,
                )
            if window and window.winfo_exists():
                try:
                    window.destroy()
                except tk.TclError:
                    pass
            open_presets_for_category(category)

        def build_forest_presets() -> list[dict]:
            canopy_palette = ["#173220", "#1f4a2f", "#2e663f", "#3f8454", "#58a86c"]
            highlight_palette = ["#6ec57f", "#8bdc99"]
            ground_palette = ["#1f2d22", "#273a2c", "#304736"]
            bark_palette = ["#3d2817", "#4a3420", "#5c4230", "#6e5138"]
            shadow_color = "#0f1a12"
            center_row = grid_size // 2
            center_col = grid_size // 2
            
            # Proste presety (istniejące)
            simple_specs = [
                {
                    "id": "forest_grove_small",
                    "label": "Las • zagajnik",
                    "ground": {"offset": (2, 0), "radius_row": 18, "radius_col": 20},
                    "trees": [(-8, -6, 4), (-6, 6, 3), (0, -2, 4), (7, 5, 3)],
                },
                {
                    "id": "forest_dense_cluster",
                    "label": "Las • gęsty klaster",
                    "ground": {"offset": (0, 0), "radius_row": 22, "radius_col": 22},
                    "trees": [(-10, -4, 5), (-2, -8, 4), (-4, 6, 5), (6, -1, 4), (8, 7, 3)],
                },
                {
                    "id": "forest_edge",
                    "label": "Las • skraj",
                    "ground": {"offset": (4, -2), "radius_row": 20, "radius_col": 24},
                    "trees": [(-12, -2, 4), (-6, 5, 4), (2, 8, 4), (10, 2, 3), (4, -6, 3)],
                },
            ]
            
            # Zaawansowane presety (nowe)
            advanced_specs = [
                {
                    "id": "forest_advanced_oak",
                    "label": "🌳 Las • dąb majestatyczny",
                    "type": "advanced",
                    "ground_shadow": {"center": (2, 0), "radius": 12, "inner": "#1a2e1d", "outer": "#0d1a0f"},
                    "trunk": {"col": 0, "top": -6, "bottom": 6, "width": 2, "seed": 100},
                    "canopy_layers": [
                        {"offset": (-8, -2), "radius": 7, "inner": "#2d5016", "outer": "#1a3810"},
                        {"offset": (-6, 2), "radius": 6, "inner": "#3a6b1e", "outer": "#2d5016"},
                        {"offset": (-4, -1), "radius": 5, "inner": "#4a8527", "outer": "#3a6b1e"},
                        {"offset": (-7, 1), "radius": 4, "inner": "#5a9f31", "outer": "#4a8527"},
                    ],
                    "highlights": [(-9, -1, 2, "#7cbd42"), (-5, 2, 1, "#8ed155")],
                    "noise": {"center": (-6, 0), "radius": 8, "base": "#3a6b1e", "amount": 12, "seed": 101},
                },
                {
                    "id": "forest_advanced_pine",
                    "label": "🌲 Las • sosna nordycka",
                    "type": "advanced",
                    "ground_shadow": {"center": (1, 0), "radius": 9, "inner": "#1c2d1e", "outer": "#0e1910"},
                    "trunk": {"col": 0, "top": -4, "bottom": 8, "width": 1, "seed": 200},
                    "canopy_layers": [
                        {"offset": (-12, 0), "radius": 3, "inner": "#1f4a2f", "outer": "#14301f"},
                        {"offset": (-9, 0), "radius": 4, "inner": "#2e663f", "outer": "#1f4a2f"},
                        {"offset": (-6, 0), "radius": 5, "inner": "#3f8454", "outer": "#2e663f"},
                        {"offset": (-3, 0), "radius": 5, "inner": "#4a9860", "outer": "#3f8454"},
                        {"offset": (0, 0), "radius": 4, "inner": "#58a86c", "outer": "#4a9860"},
                    ],
                    "highlights": [(-11, 0, 1, "#6ec57f"), (-7, -1, 1, "#7dd18a")],
                    "noise": {"center": (-6, 0), "radius": 10, "base": "#3f8454", "amount": 10, "seed": 201},
                },
                {
                    "id": "forest_advanced_birch",
                    "label": "🍂 Las • brzoza jesienią",
                    "type": "advanced",
                    "ground_shadow": {"center": (3, 1), "radius": 10, "inner": "#2a1f1a", "outer": "#1a120e"},
                    "trunk": {"col": 0, "top": -5, "bottom": 7, "width": 1, "seed": 300},
                    "trunk_spots": [(-3, 0), (-1, 0), (2, 0), (5, 0)],  # Białe plamy na pniu
                    "canopy_layers": [
                        {"offset": (-8, -1), "radius": 6, "inner": "#c49a3d", "outer": "#9a6f28"},
                        {"offset": (-6, 1), "radius": 5, "inner": "#d4ac52", "outer": "#c49a3d"},
                        {"offset": (-5, -2), "radius": 4, "inner": "#e6c76b", "outer": "#d4ac52"},
                        {"offset": (-7, 0), "radius": 4, "inner": "#f2d98a", "outer": "#e6c76b"},
                    ],
                    "highlights": [(-9, -1, 2, "#f9e8a8"), (-6, 1, 1, "#ffe5b5")],
                    "noise": {"center": (-6, 0), "radius": 7, "base": "#d4ac52", "amount": 15, "seed": 301},
                },
            ]
            
            presets: list[dict] = []
            
            # Renderuj proste presety
            for spec in simple_specs:
                grid = blank_pixel_grid()
                ground = spec.get("ground")
                if ground:
                    paint_soft_patch(
                        grid,
                        center_row + ground["offset"][0],
                        center_col + ground["offset"][1],
                        ground["radius_row"],
                        ground["radius_col"],
                        ground_palette,
                    )
                for offset_row, offset_col, radius in spec["trees"]:
                    tree_center_row = center_row + offset_row
                    tree_center_col = center_col + offset_col
                    paint_disc(grid, tree_center_row, tree_center_col, radius, canopy_palette)
                    paint_disc(grid, tree_center_row - 1, tree_center_col - 1, max(1, radius - 2), highlight_palette)
                presets.append({
                    "id": spec["id"],
                    "name": spec["label"],
                    "pixels": grid,
                    "preview_photo": build_preset_preview_photo(grid),
                })
            
            # Renderuj zaawansowane presety
            for spec in advanced_specs:
                grid = blank_pixel_grid()
                
                # 1. Cień pod drzewem (gradientowy okrąg)
                shadow = spec.get("ground_shadow")
                if shadow:
                    paint_gradient_disc(
                        grid,
                        center_row + shadow["center"][0],
                        center_col + shadow["center"][1],
                        shadow["radius"],
                        shadow["inner"],
                        shadow["outer"]
                    )
                
                # 2. Pień z teksturą kory
                trunk = spec.get("trunk")
                if trunk:
                    trunk_col = center_col + trunk["col"]
                    trunk_left = trunk_col - trunk["width"] // 2
                    trunk_right = trunk_left + trunk["width"]
                    paint_bark_texture(
                        grid,
                        trunk_left,
                        trunk_right,
                        center_row + trunk["top"],
                        center_row + trunk["bottom"],
                        bark_palette,
                        trunk["seed"]
                    )
                
                # 2b. Białe plamy (brzoza)
                trunk_spots = spec.get("trunk_spots")
                if trunk_spots:
                    for spot_offset_row, spot_offset_col in trunk_spots:
                        spot_row = center_row + spot_offset_row
                        spot_col = center_col + spot_offset_col
                        if 0 <= spot_row < grid_size and 0 <= spot_col < grid_size and hex_mask[spot_row][spot_col]:
                            set_pixel(grid, spot_row, spot_col, "#e8e8e8")
                            if spot_col - 1 >= 0 and hex_mask[spot_row][spot_col - 1]:
                                set_pixel(grid, spot_row, spot_col - 1, "#d4d4d4")
                
                # 3. Wielowarstwowa korona (od najciemniejszej do najjaśniejszej)
                canopy_layers = spec.get("canopy_layers", [])
                for layer in canopy_layers:
                    layer_row = center_row + layer["offset"][0]
                    layer_col = center_col + layer["offset"][1]
                    paint_gradient_disc(
                        grid,
                        layer_row,
                        layer_col,
                        layer["radius"],
                        layer["inner"],
                        layer["outer"]
                    )
                
                # 4. Szum proceduralny (tekstura liści)
                noise_spec = spec.get("noise")
                if noise_spec:
                    add_procedural_noise(
                        grid,
                        center_row + noise_spec["center"][0],
                        center_col + noise_spec["center"][1],
                        noise_spec["radius"],
                        noise_spec["base"],
                        noise_spec["amount"],
                        noise_spec["seed"]
                    )
                
                # 5. Akcenty światła (highlights)
                highlights = spec.get("highlights", [])
                for h_offset_row, h_offset_col, h_radius, h_color in highlights:
                    paint_specular_highlight(
                        grid,
                        center_row + h_offset_row,
                        center_col + h_offset_col,
                        h_radius,
                        h_color
                    )
                
                presets.append({
                    "id": spec["id"],
                    "name": spec["label"],
                    "pixels": grid,
                    "preview_photo": build_preset_preview_photo(grid),
                })
            
            return presets

        def build_river_presets() -> list[dict]:
            water_palette = ["#17384f", "#20506c", "#2e6d8c", "#3f8fb5", "#55abd4"]
            shoreline_palette = ["#243b32", "#2c4a3b", "#335744", "#3e664f"]
            center_row = grid_size // 2
            center_col = grid_size // 2
            specs = [
                {
                    "id": "river_meander",
                    "label": "Rzeka • meandry",
                    "branches": [
                        [(-26, -18), (-16, -8), (-4, 0), (10, 10), (24, 18)],
                    ],
                    "width": 3,
                },
                {
                    "id": "river_diagonal",
                    "label": "Rzeka • ukośna",
                    "branches": [
                        [(-24, 16), (-10, 6), (6, -4), (24, -14)],
                    ],
                    "width": 3,
                },
                {
                    "id": "river_fork",
                    "label": "Rzeka • rozwidlenie",
                    "branches": [
                        [(-26, -6), (-12, -2), (4, 4), (20, 10)],
                        [(4, 4), (14, -8), (26, -16)],
                    ],
                    "width": 3,
                },
            ]
            presets: list[dict] = []
            for spec in specs:
                grid = blank_pixel_grid()
                for branch in spec["branches"]:
                    absolute_points = [(center_row + r, center_col + c) for r, c in branch]
                    draw_polyline(grid, absolute_points, spec["width"], water_palette, overwrite=True)
                    draw_polyline(grid, absolute_points, spec["width"] + 1, shoreline_palette, overwrite=False)
                presets.append({
                    "id": spec["id"],
                    "name": spec["label"],
                    "pixels": grid,
                    "preview_photo": build_preset_preview_photo(grid),
                })
            return presets

        def build_city_presets() -> list[dict]:
            wall_palette = ["#8f8780", "#a69f98", "#c1bbb5", "#dedad5"]
            roof_palette = ["#b95f40", "#d17d55", "#e69b6f"]
            window_color = "#f2e6c9"
            plaza_palette = ["#5d564d", "#6c655b", "#7a7366"]
            center_row = grid_size // 2
            center_col = grid_size // 2
            specs = [
                {
                    "id": "city_quarters",
                    "label": "Miasto • kwartały",
                    "blocks": [
                        {"top": -10, "left": -14, "height": 12, "width": 10},
                        {"top": -8, "left": 2, "height": 13, "width": 11},
                        {"top": 4, "left": -6, "height": 9, "width": 12},
                    ],
                    "plaza": {"top": -2, "left": -4, "height": 6, "width": 8},
                },
                {
                    "id": "city_riverside",
                    "label": "Miasto • nad rzeką",
                    "blocks": [
                        {"top": -14, "left": -6, "height": 10, "width": 12},
                        {"top": -2, "left": -12, "height": 12, "width": 9},
                        {"top": 6, "left": 0, "height": 10, "width": 11},
                    ],
                    "plaza": {"top": 0, "left": -3, "height": 5, "width": 7},
                },
                {
                    "id": "city_fortified",
                    "label": "Miasto • rynek",
                    "blocks": [
                        {"top": -8, "left": -10, "height": 14, "width": 8},
                        {"top": -8, "left": 2, "height": 14, "width": 8},
                        {"top": -3, "left": -3, "height": 6, "width": 6},
                    ],
                    "plaza": {"top": -4, "left": -2, "height": 8, "width": 4},
                },
            ]
            presets: list[dict] = []
            for spec in specs:
                grid = blank_pixel_grid()
                plaza = spec.get("plaza")
                if plaza:
                    fill_rect(
                        grid,
                        center_row + plaza["top"],
                        center_col + plaza["left"],
                        plaza["height"],
                        plaza["width"],
                        plaza_palette,
                    )
                for block in spec["blocks"]:
                    top = center_row + block["top"]
                    left = center_col + block["left"]
                    fill_rect(grid, top, left, block["height"], block["width"], wall_palette)
                    sprinkle_windows(grid, top + 1, left + 1, max(1, block["height"] - 2), max(1, block["width"] - 2), window_color, 5)
                    roof_height = max(1, block["height"] // 3)
                    fill_rect(grid, top, left, roof_height, block["width"], roof_palette)
                presets.append({
                    "id": spec["id"],
                    "name": spec["label"],
                    "pixels": grid,
                    "preview_photo": build_preset_preview_photo(grid),
                })
            return presets

        def build_bridge_presets() -> list[dict]:
            water_palette = ["#123249", "#1a4f70", "#256e96", "#3c8db9"]
            deck_palette = ["#654d33", "#7a6040", "#937757", "#b3956f"]
            railing_palette = ["#c9c0a9", "#e3d8bd"]
            center_row = grid_size // 2
            center_col = grid_size // 2
            specs = [
                {
                    "id": "bridge_horizontal",
                    "label": "Most • poziomy",
                    "water_patch": {"radius_row": 24, "radius_col": 26, "offset": (0, 0)},
                    "deck": [(-2, -26), (-1, 26)],
                    "railing": [(-4, -26), (-3, 26)],
                    "railing_offset": 4,
                },
            {
                    "id": "bridge_diagonal",
                    "label": "Most • ukośny",
                    "water_patch": {"radius_row": 26, "radius_col": 24, "offset": (2, 0)},
                    "deck": [(-24, -20), (-12, -8), (8, 6), (24, 18)],
                    "railing": [(-24, -20), (-12, -8), (8, 6), (24, 18)],
                    "railing_offset": 3,
                },
            ]
            presets: list[dict] = []
            for spec in specs:
                grid = blank_pixel_grid()
                patch = spec["water_patch"]
                paint_soft_patch(
                    grid,
                    center_row + patch["offset"][0],
                    center_col + patch["offset"][1],
                    patch["radius_row"],
                    patch["radius_col"],
                    water_palette,
                )
                deck_points = [(center_row + r, center_col + c) for r, c in spec["deck"]]
                draw_polyline(grid, deck_points, 2, deck_palette, overwrite=True)
                railing_points = [(center_row + r, center_col + c) for r, c in spec["railing"]]
                draw_polyline(grid, railing_points, spec["railing_offset"], railing_palette, overwrite=False)
                presets.append({
                    "id": spec["id"],
                    "name": spec["label"],
                    "pixels": grid,
                    "preview_photo": build_preset_preview_photo(grid),
                })
            return presets

        def build_road_presets() -> list[dict]:
            asphalt_palette = ["#1f1c18", "#2a2723", "#37322d", "#4a453f"]
            shoulder_palette = ["#514a41", "#6a6257", "#7d7467"]
            center_line_color = "#d9c86a"
            center_row = grid_size // 2
            center_col = grid_size // 2
            specs = [
                {
                    "id": "road_s_curve",
                    "label": "Droga • łuk",
                    "path": [(-26, -12), (-12, -6), (0, 0), (12, 6), (26, 12)],
                    "width": 2,
                },
                {
                    "id": "road_diagonal",
                    "label": "Droga • ukośna",
                    "path": [(-24, 14), (-8, 6), (8, -4), (24, -12)],
                    "width": 2,
                },
                {
                    "id": "road_crossing",
                    "label": "Droga • skrzyżowanie",
                    "path": [(-26, 0), (-14, 0), (0, 0), (16, 0), (26, 0)],
                    "width": 2,
                },
            ]
            presets: list[dict] = []
            for spec in specs:
                grid = blank_pixel_grid()
                path_points = [(center_row + r, center_col + c) for r, c in spec["path"]]
                draw_polyline(grid, path_points, spec["width"], asphalt_palette, overwrite=True)
                draw_polyline(grid, path_points, spec["width"] + 1, shoulder_palette, overwrite=False)
                draw_dashed_line(grid, path_points, spacing=3.5, color=center_line_color)
                presets.append({
                    "id": spec["id"],
                    "name": spec["label"],
                    "pixels": grid,
                    "preview_photo": build_preset_preview_photo(grid),
                })
            return presets

        def build_rail_presets() -> list[dict]:
            rail_palette = ["#3f454d", "#59616a", "#7b858f"]
            sleeper_color = "#6a5139"
            center_row = grid_size // 2
            center_col = grid_size // 2
            specs = [
                {
                    "id": "rail_vertical",
                    "label": "Kolej • pionowa",
                    "rails": [
                        [(-26, -4), (-12, -3), (0, -2), (14, -1), (26, 0)],
                        [(-26, 4), (-12, 3), (0, 2), (14, 1), (26, 0)],
                    ],
                    "ties": {"orientation": "horizontal", "start": -24, "end": 24, "step": 4, "half_width": 5},
                },
                {
                    "id": "rail_diagonal",
                    "label": "Kolej • ukośna",
                    "rails": [
                        [(-24, -18), (-10, -8), (8, 6), (24, 16)],
                        [(-24, -12), (-10, -2), (8, 10), (24, 18)],
                    ],
                    "ties": {"orientation": "diagonal", "start": -18, "end": 18, "step": 5, "length": 6},
                },
            ]
            presets: list[dict] = []
            for spec in specs:
                grid = blank_pixel_grid()
                rail_paths = []
                for rail in spec["rails"]:
                    points = [(center_row + r, center_col + c) for r, c in rail]
                    rail_paths.append(points)
                    draw_polyline(grid, points, 1, rail_palette, overwrite=True)
                ties = spec["ties"]
                if ties["orientation"] == "horizontal":
                    for r_offset in range(ties["start"], ties["end"] + 1, ties["step"]):
                        row = center_row + r_offset
                        for col in range(center_col - ties["half_width"], center_col + ties["half_width"] + 1):
                            set_pixel_if_empty(grid, row, col, sleeper_color)
                else:
                    length = ties.get("length", 6)
                    for diag in range(ties["start"], ties["end"] + 1, ties["step"]):
                        row = center_row + diag
                        col = center_col + diag
                        for offset in range(-length // 2, length // 2 + 1):
                            set_pixel_if_empty(grid, row - offset, col + offset, sleeper_color)
                presets.append({
                    "id": spec["id"],
                    "name": spec["label"],
                    "pixels": grid,
                    "preview_photo": build_preset_preview_photo(grid),
                })
            return presets

        preset_categories = [
            {
                "key": "custom",
                "label": "Importowane PNG",
                "icon": "🗂️",
                "builder": load_custom_image_presets,
            },
        ]

        for user_key, user_meta in USER_ASSET_CATEGORY_DEFS.items():
            preset_categories.append({
                "key": f"user_{user_key}",
                "label": f"{user_meta['label']} • własne",
                "icon": user_meta["icon"],
                "builder": (lambda ck=user_key: load_user_asset_presets(ck)),
                "user_key": user_key,
            })

        neighbor_outline_points: list[list[float]] = []

        def rebuild_neighbor_outlines() -> None:
            neighbor_outline_points.clear()
            for dq, dr in neighbor_dirs:
                neighbor_id = f"{q + dq},{r + dr}"
                dx_canvas, dy_canvas = canvas_offset_for_hex(neighbor_id, dq, dr)
                poly_points: list[float] = []
                for vx, vy in mask_vertices:
                    poly_points.extend((vx * cell_size + grid_offset + dx_canvas,
                                        vy * cell_size + grid_offset + dy_canvas))
                neighbor_outline_points.append(poly_points)

        rebuild_neighbor_outlines()

        preview_color_cache: dict[str, list[list[str | None]]] = {}

        cache_debug_enabled = os.environ.get("HEX_EDITOR_CACHE_DEBUG") == "1"

        def debug_cache(message: str) -> None:
            if not cache_debug_enabled:
                return
            active_hex = None
            try:
                active_hex = state.get("current_hex_id")  # type: ignore[name-defined]
            except NameError:
                active_hex = hex_id
            except AttributeError:
                active_hex = hex_id
            label = active_hex or hex_id
            print(f"[edge-cache] {label}: {message}")

        def solid_color_pixels(color: str) -> list[list[str | None]]:
            cached = preview_color_cache.get(color)
            if cached is not None:
                return cached
            grid = [[None for _ in range(grid_size)] for _ in range(grid_size)]
            for row in range(grid_size):
                for col in range(grid_size):
                    if hex_mask[row][col]:
                        grid[row][col] = color
            preview_color_cache[color] = grid
            return grid

        def get_context_pixels(
            target_hex_id: str,
            overrides: dict[str, dict] | None = None,
            neighbor_cache: dict[str, dict] | None = None,
        ) -> list[list[str | None]] | None:
            try:
                current_hex_identifier = state.get("current_hex_id", hex_id)
            except NameError:
                current_hex_identifier = hex_id
            if target_hex_id == current_hex_identifier:
                debug_cache(
                    f"get_context_pixels {target_hex_id}: skipped (current hex {current_hex_identifier})"
                )
                return None
            sources = None
            try:
                sources = state.get("last_context_sources")
            except NameError:
                sources = None
            if overrides:
                for entry in overrides.values():
                    if entry.get("neighbor_id") == target_hex_id:
                        override_pixels = entry.get("neighbor_pixels")
                        if override_pixels is not None:
                            if sources is not None:
                                sources[target_hex_id] = "override"
                            debug_cache(f"get_context_pixels {target_hex_id}: using override entry")
                            return override_pixels
            if neighbor_cache:
                cached_entry = neighbor_cache.get(target_hex_id)
                if cached_entry is not None:
                    cached_pixels = cached_entry.get("pixels")
                    if cached_pixels is not None:
                        if sources is not None:
                            sources[target_hex_id] = "neighbor_cache"
                        debug_cache(f"get_context_pixels {target_hex_id}: using neighbor_cache copy")
                        return [row[:] for row in cached_pixels]
            terrain_data = self.hex_data.get(target_hex_id)
            if not terrain_data:
                if sources is not None:
                    sources[target_hex_id] = "none"
                debug_cache(f"get_context_pixels {target_hex_id}: missing terrain data")
                return None
            texture_rel = terrain_data.get("texture")
            if texture_rel:
                if sources is not None:
                    sources[target_hex_id] = "texture_disk"
                debug_cache(f"get_context_pixels {target_hex_id}: loaded texture_rel {texture_rel}")
                return self._load_hex_texture_pixels(texture_rel, grid_size)
            terrain_key = terrain_data.get("terrain_key")
            if terrain_key:
                preview_color = TERRAIN_PREVIEW_COLORS.get(terrain_key)
                if preview_color:
                    if sources is not None:
                        sources[target_hex_id] = "terrain_color"
                    debug_cache(f"get_context_pixels {target_hex_id}: using terrain preview color {terrain_key}")
                    return solid_color_pixels(preview_color)
            if sources is not None:
                sources[target_hex_id] = "none"
            debug_cache(f"get_context_pixels {target_hex_id}: no data available")
            return None

        def build_texture_context(
            overrides: dict[str, dict] | None = None,
            neighbor_cache: dict[str, dict] | None = None,
        ) -> Image.Image | None:
            try:
                state.get("last_context_sources", {}).clear()
            except NameError:
                pass
            debug_cache(
                "build_texture_context start "
                f"overrides={bool(overrides)} cache={bool(neighbor_cache)}"
            )
            context_img = Image.new("RGBA", (context_canvas_size, context_canvas_size), (0, 0, 0, 0))
            has_any = False
            for dq, dr in neighbor_dirs:
                neighbor_id = f"{q + dq},{r + dr}"
                neighbor_pixels = get_context_pixels(neighbor_id, overrides, neighbor_cache)
                if not neighbor_pixels:
                    debug_cache(f"build_texture_context neighbor {neighbor_id}: no pixels")
                    continue
                neighbor_img = pixels_to_image(neighbor_pixels)
                if neighbor_img.getbbox() is None:
                    debug_cache(f"build_texture_context neighbor {neighbor_id}: empty bbox")
                    continue
                neighbor_size = max(canvas_size, int(round(canvas_size * NEIGHBOR_PREVIEW_SCALE)))
                neighbor_size = min(context_canvas_size, neighbor_size)
                neighbor_img = neighbor_img.resize((neighbor_size, neighbor_size), Image.NEAREST)
                offset_x, offset_y = canvas_offset_for_hex(neighbor_id, dq, dr)
                center_px = context_canvas_size / 2.0
                paste_x = int(round(center_px + offset_x - neighbor_size / 2.0))
                paste_y = int(round(center_px + offset_y - neighbor_size / 2.0))
                context_img.paste(neighbor_img, (paste_x, paste_y), neighbor_img)
                debug_cache(
                    f"build_texture_context neighbor {neighbor_id}: pasted {neighbor_size}x{neighbor_size}"
                )
                has_any = True
            debug_cache(f"build_texture_context complete has_any={has_any}")
            return context_img if has_any else None

        background_photo = None
        outline_points: list[float] = []
        for vx, vy in mask_vertices:
            outline_points.extend((vx * cell_size + grid_offset, vy * cell_size + grid_offset))

        def resample_pixel_grid(
            source_pixels: list[list[str | None]],
            source_size: int,
            target_size: int,
        ) -> list[list[str | None]]:
            if target_size == source_size:
                return [row[:] for row in source_pixels]
            source_image = pixels_to_image(source_pixels)
            resized = source_image.resize((target_size, target_size), Image.NEAREST)
            target_mask = self._precompute_hex_mask(target_size)
            result = [[None for _ in range(target_size)] for _ in range(target_size)]
            for row in range(target_size):
                for col in range(target_size):
                    if not target_mask[row][col]:
                        continue
                    r_px, g_px, b_px, a_px = resized.getpixel((col, row))
                    if a_px:
                        result[row][col] = f"#{r_px:02x}{g_px:02x}{b_px:02x}"
            return result

        state = {
            "pixels": pixels,
            "grid_size": grid_size,
            "current_color": "#ffffff",
            "eraser": False,
            "mask": hex_mask,
            "background_photo": background_photo,
            "background_item_id": None,
            "stamp_pixels": None,
            "stamp_overlay_photo": None,
            "stamp_preview_id": None,
            "stamp_offset": (0, 0),
            "stamp_hotspot": (grid_size / 2.0, grid_size / 2.0),
            "stamp_pointer_position": (grid_size / 2.0, grid_size / 2.0),
            "preset_preview_refs": [],
            "preset_category_window": None,
            "preset_detail_window": None,
            "preset_categories": preset_categories,
            "edge_mode_active": False,
            "edge_current_key": None,
            "edge_neighbors": edge_mode_data,
            "edge_band_cells": initial_edge_band_cells,
            "edge_bleed_depth": min(initial_edge_band_cells, EDGE_BLEED_DEPTH_DEFAULT),
            "edge_blend_strength": EDGE_BLEND_DEFAULT_STRENGTH,
            "edge_blend_profile": EDGE_BLEND_PROFILE_DEFAULT,
            "undo_stack": [],
            "redo_stack": [],
            "history_action_active": False,
            "history_edit_dirty": False,
            "stamp_scale_percent": 100.0,
            "stamp_base_pixels": None,
            "stamp_label": None,
            "view_offset": (0, 0),
            "asset_mode_active": False,
            "asset_selection_start": None,
            "asset_selection_rect": None,
            "asset_selection_bounds": None,
            "precision_mode_active": False,
            "precision_points": [],
            "precision_hover_cell": None,
            "brush_radius": BRUSH_RADIUS_DEFAULT,
            "current_hex_id": hex_id,
            "neighbor_hex_data": {},
            "last_context_sources": {},
            "cache_debug_enabled": cache_debug_enabled,
        }

        context_background = build_texture_context(
            state.get("edge_neighbors"),
            state.get("neighbor_hex_data"),
        )
        if context_background:
            background_photo = ImageTk.PhotoImage(context_background)
            state["background_photo"] = background_photo
        else:
            state["background_photo"] = None

        stamp_status_label = None
        selected_edge_var = tk.StringVar(value="")
        edge_status_label = None
        edge_sync_status_label = None
        edge_band_width_value_label = None
        edge_blend_strength_value_label = None
        edge_bleed_depth_value_label = None
        edge_bleed_depth_scale = None
        edge_button_widgets: dict[str, tk.Radiobutton] = {}
        edge_band_width_var = tk.IntVar(master=editor, value=state["edge_band_cells"])
        edge_blend_strength_var = tk.IntVar(master=editor, value=int(state["edge_blend_strength"]))
        edge_bleed_depth_var = tk.IntVar(master=editor, value=int(state["edge_bleed_depth"]))
        edge_blend_profile_display_var = tk.StringVar(
            master=editor,
            value=EDGE_BLEND_PROFILES[state["edge_blend_profile"]]["label"],
        )
        brush_radius_var = tk.IntVar(master=editor, value=state["brush_radius"])
        brush_radius_value_label = None
        undo_btn = None
        redo_btn = None
        stamp_scale_label = None
        stamp_scale_widget = None
        stamp_scale_var = tk.DoubleVar(master=editor, value=100.0)
        asset_mode_btn = None
        precision_mode_btn = None
        precision_undo_btn = None

        HISTORY_LIMIT = 40

        def clone_pixels(source: list[list[str | None]]) -> list[list[str | None]]:
            return [row[:] for row in source]

        def capture_snapshot() -> dict:
            neighbors_state: dict[str, dict] = {}
            for key, entry in state["edge_neighbors"].items():
                neighbor_pixels = entry.get("neighbor_pixels")
                neighbors_state[key] = {
                    "pixels": clone_pixels(neighbor_pixels) if neighbor_pixels is not None else None,
                    "dirty": entry.get("dirty", False),
                }
            return {
                "pixels": clone_pixels(state["pixels"]),
                "neighbors": neighbors_state,
            }

        def restore_snapshot(snapshot: dict) -> None:
            state["pixels"] = clone_pixels(snapshot["pixels"])
            for key, neighbor_state in snapshot.get("neighbors", {}).items():
                entry = state["edge_neighbors"].get(key)
                if not entry:
                    continue
                entry["dirty"] = neighbor_state.get("dirty", False)
                pixels_snapshot = neighbor_state.get("pixels")
                entry["neighbor_pixels"] = clone_pixels(pixels_snapshot) if pixels_snapshot is not None else None
            state["history_edit_dirty"] = False

        def update_history_buttons() -> None:
            if undo_btn is not None:
                undo_btn.config(state=tk.NORMAL if state["undo_stack"] else tk.DISABLED)
            if redo_btn is not None:
                redo_btn.config(state=tk.NORMAL if state["redo_stack"] else tk.DISABLED)

        def begin_edit_action() -> None:
            if state["history_action_active"]:
                return
            state["undo_stack"].append(capture_snapshot())
            if len(state["undo_stack"]) > HISTORY_LIMIT:
                state["undo_stack"].pop(0)
            state["redo_stack"].clear()
            state["history_action_active"] = True
            state["history_edit_dirty"] = False
            update_history_buttons()

        def finish_edit_action(event=None) -> None:
            if not state["history_action_active"]:
                return
            if not state["history_edit_dirty"] and state["undo_stack"]:
                state["undo_stack"].pop()
            state["history_action_active"] = False
            state["history_edit_dirty"] = False
            update_history_buttons()

        def undo_action(event=None):
            if state["history_action_active"]:
                finish_edit_action()
            if not state["undo_stack"]:
                return "break"
            snapshot = state["undo_stack"].pop()
            state["redo_stack"].append(capture_snapshot())
            if len(state["redo_stack"]) > HISTORY_LIMIT:
                state["redo_stack"].pop(0)
            restore_snapshot(snapshot)
            draw_grid()
            refresh_edge_preview(refresh_background=True)
            update_history_buttons()
            return "break"

        def redo_action(event=None):
            if state["history_action_active"]:
                finish_edit_action()
            if not state["redo_stack"]:
                return "break"
            snapshot = state["redo_stack"].pop()
            state["undo_stack"].append(capture_snapshot())
            if len(state["undo_stack"]) > HISTORY_LIMIT:
                state["undo_stack"].pop(0)
            restore_snapshot(snapshot)
            draw_grid()
            refresh_edge_preview(refresh_background=True)
            update_history_buttons()
            return "break"

        def scale_pixels(source_pixels: list[list[str | None]], percent: float) -> list[list[str | None]]:
            percent = max(10.0, min(100.0, percent))
            target = max(1, min(grid_size, int(round(grid_size * percent / 100.0))))
            if target == grid_size:
                return clone_pixels(source_pixels)
            img = pixels_to_image(source_pixels)
            resized = img.resize((target, target), Image.NEAREST)
            result = blank_pixel_grid()
            offset_row = (grid_size - target) // 2
            offset_col = (grid_size - target) // 2
            for row in range(target):
                for col in range(target):
                    r, g, b, a = resized.getpixel((col, row))
                    if a == 0:
                        continue
                    dst_row = row + offset_row
                    dst_col = col + offset_col
                    if 0 <= dst_row < grid_size and 0 <= dst_col < grid_size and hex_mask[dst_row][dst_col]:
                        result[dst_row][dst_col] = f"#{r:02x}{g:02x}{b:02x}"
            return result

        def refresh_stamp_from_scale() -> None:
            if state.get("stamp_base_pixels") is None:
                return
            percent = state.get("stamp_scale_percent", 100.0)
            scaled = scale_pixels(state["stamp_base_pixels"], percent)
            state["stamp_pixels"] = scaled
            state["stamp_overlay_photo"] = ImageTk.PhotoImage(create_stamp_overlay_image(scaled))
            if state.get("stamp_preview_id") is not None:
                preview_canvas.itemconfig(state["stamp_preview_id"], image=state["stamp_overlay_photo"])
            update_stamp_overlay_position()

        def on_scale_change(value: str) -> None:
            try:
                percent = float(value)
            except (TypeError, ValueError):
                percent = 100.0
            percent = max(10.0, min(100.0, percent))
            state["stamp_scale_percent"] = percent
            if stamp_scale_label is not None:
                stamp_scale_label.config(text=f"Skala: {int(round(percent))}%")
            refresh_stamp_from_scale()
            if stamp_status_label is not None:
                if state.get("stamp_label"):
                    stamp_status_label.config(text=f"Preset: {state['stamp_label']} — kliknij, aby wstawić (skala {int(round(percent))}%)")
                elif state.get("stamp_pixels") is None:
                    stamp_status_label.config(text="Preset: brak")

        def apply_color_to_neighbor(edge_entry: dict, row: int, col: int, new_val: str | None) -> bool:
            if not edge_entry or not edge_entry.get("enabled"):
                return False
            nr = row - edge_entry["dy_cells"]
            nc = col - edge_entry["dx_cells"]
            if not (0 <= nr < grid_size and 0 <= nc < grid_size):
                return False
            neighbor_mask = edge_entry.get("neighbor_mask", hex_mask)
            if not neighbor_mask[nr][nc]:
                return False
            neighbor_pixels = edge_entry.get("neighbor_pixels")
            if neighbor_pixels is None:
                return False
            if neighbor_pixels[nr][nc] == new_val:
                return False
            neighbor_pixels[nr][nc] = new_val
            edge_entry["dirty"] = True
            return True

        def update_stamp_overlay_position(target_row: float | None = None, target_col: float | None = None, *, from_pointer: bool = True) -> None:
            if state.get("stamp_pixels") is None or state.get("stamp_overlay_photo") is None:
                if state.get("stamp_preview_id") is not None:
                    preview_canvas.delete(state["stamp_preview_id"])
                    state["stamp_preview_id"] = None
                return
            hotspot_row, hotspot_col = state.get("stamp_hotspot", (grid_size / 2.0, grid_size / 2.0))
            if target_row is None or target_col is None:
                pointer_row, pointer_col = state.get("stamp_pointer_position", (float(hotspot_row), float(hotspot_col)))
                from_pointer = False
            else:
                pointer_row = float(target_row)
                pointer_col = float(target_col)
                if from_pointer:
                    state["stamp_pointer_position"] = (pointer_row, pointer_col)
            if from_pointer:
                preview_top_left_row = pointer_row - hotspot_row
                preview_top_left_col = pointer_col - hotspot_col
                state["stamp_offset"] = (
                    int(math.floor(preview_top_left_row)),
                    int(math.floor(preview_top_left_col)),
                )
            else:
                preview_top_left_row = pointer_row - hotspot_row
                preview_top_left_col = pointer_col - hotspot_col
            offset_x, offset_y = state.get("view_offset", (0, 0))
            x = grid_offset + preview_top_left_col * cell_size + offset_x
            y = grid_offset + preview_top_left_row * cell_size + offset_y
            if state.get("stamp_preview_id") is None:
                state["stamp_preview_id"] = preview_canvas.create_image(
                    x,
                    y,
                    anchor="nw",
                    image=state["stamp_overlay_photo"],
                    tags="stamp_preview"
                )
            else:
                preview_canvas.coords(state["stamp_preview_id"], x, y)
            preview_canvas.tag_lower("stamp_preview", "outline")

        def get_cell_from_event(event, clamp: bool = True) -> tuple[int, int] | None:
            offset_x, offset_y = state.get("view_offset", (0, 0))
            col = int((event.x - grid_offset - offset_x) // cell_size)
            row = int((event.y - grid_offset - offset_y) // cell_size)
            if clamp:
                col = max(0, min(grid_size - 1, col))
                row = max(0, min(grid_size - 1, row))
                return row, col
            if 0 <= row < grid_size and 0 <= col < grid_size:
                return row, col
            return None

        def get_pointer_position(event, clamp: bool = False) -> tuple[float, float] | None:
            offset_x, offset_y = state.get("view_offset", (0, 0))
            col = (event.x - grid_offset - offset_x) / cell_size
            row = (event.y - grid_offset - offset_y) / cell_size
            if clamp:
                col = max(0.0, min(grid_size - 1e-6, col))
                row = max(0.0, min(grid_size - 1e-6, row))
                return row, col
            if 0 <= row < grid_size and 0 <= col < grid_size:
                return row, col
            return None

        def asset_bounds_to_canvas_coords(bounds: tuple[int, int, int, int]) -> tuple[float, float, float, float]:
            row_min, row_max, col_min, col_max = bounds
            offset_x, offset_y = state.get("view_offset", (0, 0))
            x0 = grid_offset + col_min * cell_size + offset_x
            y0 = grid_offset + row_min * cell_size + offset_y
            x1 = grid_offset + (col_max + 1) * cell_size + offset_x
            y1 = grid_offset + (row_max + 1) * cell_size + offset_y
            return x0, y0, x1, y1

        def clear_asset_selection_overlay() -> None:
            rect_id = state.get("asset_selection_rect")
            if rect_id is not None:
                try:
                    preview_canvas.delete(rect_id)
                except tk.TclError:
                    pass
            state["asset_selection_rect"] = None

        def draw_asset_selection(bounds: tuple[int, int, int, int]) -> None:
            coords = asset_bounds_to_canvas_coords(bounds)
            rect_id = state.get("asset_selection_rect")
            if rect_id is None:
                rect_id = preview_canvas.create_rectangle(
                    *coords,
                    outline="#ffcc66",
                    width=2,
                    dash=(6, 4),
                    fill="",
                    tags="asset_selection"
                )
                state["asset_selection_rect"] = rect_id
            else:
                preview_canvas.coords(rect_id, *coords)
            preview_canvas.tag_raise("asset_selection")

        def clear_precision_overlay() -> None:
            try:
                preview_canvas.delete("precision_overlay")
                preview_canvas.delete("precision_hover")
            except tk.TclError:
                pass

        def update_precision_overlay() -> None:
            clear_precision_overlay()
            if not state.get("precision_mode_active"):
                refresh_precision_hover()
                return
            points = state.get("precision_points") or []
            if not points:
                refresh_precision_hover()
                return
            offset_x, offset_y = state.get("view_offset", (0, 0))
            line_coords: list[float] = []
            for row, col in points:
                x0 = grid_offset + col * cell_size + offset_x
                y0 = grid_offset + row * cell_size + offset_y
                x1 = x0 + cell_size
                y1 = y0 + cell_size
                preview_canvas.create_rectangle(
                    x0,
                    y0,
                    x1,
                    y1,
                    outline="#ffd966",
                    width=1,
                    tags=("precision_overlay", "precision_cell"),
                )
                line_coords.append(grid_offset + (col + 0.5) * cell_size + offset_x)
                line_coords.append(grid_offset + (row + 0.5) * cell_size + offset_y)
            if len(line_coords) >= 4:
                preview_canvas.create_line(
                    *line_coords,
                    fill="#ffd966",
                    width=2,
                    tags=("precision_overlay", "precision_path"),
                )
            first_row, first_col = points[0]
            first_x = grid_offset + (first_col + 0.5) * cell_size + offset_x
            first_y = grid_offset + (first_row + 0.5) * cell_size + offset_y
            preview_canvas.create_oval(
                first_x - 4,
                first_y - 4,
                first_x + 4,
                first_y + 4,
                fill="#ffd966",
                outline="#333333",
                width=1,
                tags=("precision_overlay", "precision_start"),
            )
            preview_canvas.tag_raise("precision_overlay")
            preview_canvas.tag_raise("precision_hover")
            refresh_precision_hover()

        def refresh_precision_hover() -> None:
            preview_canvas.delete("precision_hover")
            if not state.get("precision_mode_active"):
                return
            cell = state.get("precision_hover_cell")
            if cell is None:
                return
            offset_x, offset_y = state.get("view_offset", (0, 0))
            row, col = cell
            cell_x0 = grid_offset + col * cell_size + offset_x
            cell_y0 = grid_offset + row * cell_size + offset_y
            cell_x1 = cell_x0 + cell_size
            cell_y1 = cell_y0 + cell_size
            points = state.get("precision_points") or []
            line_color = "#ff7b7b"
            path_cells: list[tuple[int, int]] = []
            path_result: list[tuple[int, int]] | None = None
            if points:
                last = points[-1]
                path_result = compute_precision_path(last, cell) if cell != last else []
                if path_result is not None:
                    path_cells = path_result
                    line_color = "#ffd966"
                else:
                    line_color = "#ff7b7b"
                if cell != last:
                    coord_sequence: list[tuple[float, float]] = []
                    coord_sequence.append((grid_offset + (last[1] + 0.5) * cell_size + offset_x, grid_offset + (last[0] + 0.5) * cell_size + offset_y))
                    if path_cells:
                        for pr, pc in path_cells:
                            coord_sequence.append((grid_offset + (pc + 0.5) * cell_size + offset_x, grid_offset + (pr + 0.5) * cell_size + offset_y))
                    else:
                        coord_sequence.append((grid_offset + (col + 0.5) * cell_size + offset_x, grid_offset + (row + 0.5) * cell_size + offset_y))
                    if len(coord_sequence) >= 2:
                        preview_canvas.create_line(
                            *[coord for point in coord_sequence for coord in point],
                            fill=line_color,
                            width=2,
                            dash=(4, 2),
                            tags="precision_hover",
                        )
            cell_valid = 0 <= row < grid_size and 0 <= col < grid_size and hex_mask[row][col]
            if not points:
                valid_path = cell_valid
            elif cell == points[-1]:
                valid_path = True
            else:
                valid_path = cell_valid and path_result is not None
            color = "#ffd966" if valid_path else "#ff7b7b"
            for pr, pc in path_cells:
                rect_x0 = grid_offset + pc * cell_size + offset_x
                rect_y0 = grid_offset + pr * cell_size + offset_y
                rect_x1 = rect_x0 + cell_size
                rect_y1 = rect_y0 + cell_size
                preview_canvas.create_rectangle(
                    rect_x0,
                    rect_y0,
                    rect_x1,
                    rect_y1,
                    outline=line_color,
                    width=1,
                    dash=(2, 2),
                    tags="precision_hover",
                )
            preview_canvas.create_rectangle(
                cell_x0,
                cell_y0,
                cell_x1,
                cell_y1,
                outline=color,
                width=2,
                dash=(4, 2),
                tags="precision_hover",
            )
            preview_canvas.tag_raise("precision_hover")

        def update_precision_hover(cell: tuple[int, int] | None) -> None:
            state["precision_hover_cell"] = cell
            refresh_precision_hover()

        def update_precision_controls() -> None:
            if precision_undo_btn is not None:
                has_points = bool(state.get("precision_points"))
                precision_undo_btn.config(state=tk.NORMAL if has_points else tk.DISABLED)

        def compute_precision_path(
            start: tuple[int, int],
            end: tuple[int, int],
        ) -> list[tuple[int, int]] | None:
            sr, sc = start
            er, ec = end
            dr = er - sr
            dc = ec - sc
            if dr == 0 and dc == 0:
                return []
            if abs(dr) <= 1 and abs(dc) <= 1:
                step_r = dr
                step_c = dc
            elif dr == 0:
                step_r = 0
                step_c = 1 if dc > 0 else -1
            elif dc == 0:
                step_r = 1 if dr > 0 else -1
                step_c = 0
            elif abs(dr) == abs(dc):
                step_r = 1 if dr > 0 else -1
                step_c = 1 if dc > 0 else -1
            else:
                return None
            length = max(abs(dr), abs(dc))
            if length == 0:
                return []
            path: list[tuple[int, int]] = []
            cur_r, cur_c = sr, sc
            for _ in range(length):
                cur_r += step_r
                cur_c += step_c
                if not (0 <= cur_r < grid_size and 0 <= cur_c < grid_size):
                    return None
                if not hex_mask[cur_r][cur_c]:
                    return None
                path.append((cur_r, cur_c))
            return path

        def compute_content_bounds(bounds: tuple[int, int, int, int]) -> tuple[int, int, int, int] | None:
            row_min, row_max, col_min, col_max = bounds
            found = False
            content_row_min = row_max
            content_row_max = row_min
            content_col_min = col_max
            content_col_max = col_min
            for row in range(row_min, row_max + 1):
                for col in range(col_min, col_max + 1):
                    if not hex_mask[row][col]:
                        continue
                    if state["pixels"][row][col] is None:
                        continue
                    if row < content_row_min:
                        content_row_min = row
                    if row > content_row_max:
                        content_row_max = row
                    if col < content_col_min:
                        content_col_min = col
                    if col > content_col_max:
                        content_col_max = col
                    found = True
            if not found:
                return None
            return content_row_min, content_row_max, content_col_min, content_col_max

        def deactivate_precision_mode(update_button: bool = True) -> None:
            if not state.get("precision_mode_active"):
                return
            state["precision_mode_active"] = False
            state["precision_points"] = []
            state["precision_hover_cell"] = None
            clear_precision_overlay()
            if update_button and precision_mode_btn is not None:
                precision_mode_btn.config(relief=tk.RAISED)
            cursor = ""
            if state.get("asset_mode_active"):
                cursor = "tcross"
            elif state.get("stamp_pixels") is not None:
                cursor = "hand2"
            preview_canvas.config(cursor=cursor)
            update_precision_controls()

        def activate_precision_mode() -> None:
            if state.get("precision_mode_active"):
                return
            if state.get("stamp_pixels") is not None:
                clear_stamp_mode()
            if state.get("asset_mode_active"):
                deactivate_asset_mode(update_button=True)
            state["precision_mode_active"] = True
            state["precision_points"] = []
            state["precision_hover_cell"] = None
            clear_precision_overlay()
            preview_canvas.config(cursor="tcross")
            if precision_mode_btn is not None:
                precision_mode_btn.config(relief=tk.SUNKEN)
            preview_canvas.focus_set()
            update_precision_overlay()
            update_precision_controls()

        def toggle_precision_mode() -> None:
            if state.get("precision_mode_active"):
                deactivate_precision_mode()
            else:
                activate_precision_mode()

        def precision_add_point(event) -> None:
            if not state.get("precision_mode_active"):
                return
            cell = get_cell_from_event(event)
            if cell is None:
                return
            row, col = cell
            if not hex_mask[row][col]:
                return
            points = state.get("precision_points")
            if not points:
                state["precision_points"] = [(row, col)]
                update_precision_overlay()
                update_precision_controls()
                update_precision_hover(None)
                return
            last_row, last_col = points[-1]
            if (row, col) == (last_row, last_col):
                return
            if (row, col) == points[0]:
                if len(points) < 3:
                    messagebox.showwarning("Asset", "Dodaj co najmniej trzy punkty przed zamknięciem obrysu.", parent=editor)
                    return
                path_to_start = compute_precision_path(points[-1], points[0]) if points[-1] != points[0] else []
                if path_to_start is None:
                    messagebox.showwarning("Asset", "Nie można domknąć obrysu — upewnij się, że ostatni odcinek jest prosty i biegnie przez dozwolone pola.", parent=editor)
                    return
                if path_to_start:
                    intermediate = path_to_start[:-1]
                    for step in intermediate:
                        if step in points:
                            messagebox.showwarning("Asset", "Odcinek domykający nachodzi na istniejące punkty.", parent=editor)
                            return
                    points.extend(intermediate)
                    update_precision_overlay()
                    update_precision_controls()
                complete_precision_asset(force_close=True)
                return
            if (row, col) in points:
                messagebox.showwarning("Asset", "To pole jest już w obrysie.", parent=editor)
                return
            path = compute_precision_path(points[-1], (row, col))
            if path is None:
                messagebox.showwarning("Asset", "Odcinek musi być prosty (w poziomie, pionie lub po skosie) i przechodzić przez dozwolone pola.", parent=editor)
                return
            duplicates = [step for step in path if step in points]
            if duplicates:
                messagebox.showwarning("Asset", "Odcinek nachodzi na istniejące punkty obrysu.", parent=editor)
                return
            points.extend(path)
            update_precision_overlay()
            update_precision_controls()
            update_precision_hover(None)

        def precision_remove_last(event=None):
            if not state.get("precision_mode_active"):
                return
            points = state.get("precision_points")
            if not points:
                return "break" if event is not None else None
            points.pop()
            if not points:
                state["precision_hover_cell"] = None
            update_precision_overlay()
            update_precision_controls()
            return "break" if event is not None else None

        def precision_cancel(event=None):
            if not state.get("precision_mode_active"):
                return
            if state.get("precision_points"):
                state["precision_points"] = []
                state["precision_hover_cell"] = None
                clear_precision_overlay()
                update_precision_controls()
                update_precision_overlay()
                return "break" if event is not None else None
            deactivate_precision_mode()
            return "break" if event is not None else None

        def precision_attempt_finish(event=None):
            if not state.get("precision_mode_active"):
                return
            complete_precision_asset(force_close=True)
            return "break"

        def complete_precision_asset(*, force_close: bool = False) -> None:
            if not state.get("precision_mode_active"):
                return
            points = list(state.get("precision_points") or [])
            if len(points) < 3:
                messagebox.showwarning("Asset", "Dodaj co najmniej trzy punkty, aby zamknąć obrys.", parent=editor)
                return
            loop_points = points[:]
            if force_close and loop_points[0] != loop_points[-1]:
                path_to_start = compute_precision_path(loop_points[-1], loop_points[0])
                if path_to_start is None:
                    messagebox.showwarning(
                        "Asset",
                        "Nie można domknąć obrysu — upewnij się, że ostatni odcinek jest prosty i biegnie przez dozwolone pola.",
                        parent=editor,
                    )
                    return
                if path_to_start:
                    loop_points.extend(path_to_start[:-1])
            polygon_points = loop_points[:]
            if polygon_points[0] != polygon_points[-1]:
                polygon_points.append(polygon_points[0])
            rows = [row for row, _ in polygon_points]
            cols = [col for _, col in polygon_points]
            row_min = max(0, min(rows))
            row_max = min(grid_size - 1, max(rows))
            col_min = max(0, min(cols))
            col_max = min(grid_size - 1, max(cols))
            poly_xy = [(col + 0.5, row + 0.5) for row, col in polygon_points]
            path_cells = set(loop_points)
            selected_cells: set[tuple[int, int]] = set()
            for row in range(row_min, row_max + 1):
                for col in range(col_min, col_max + 1):
                    if not hex_mask[row][col]:
                        continue
                    if (row, col) in path_cells:
                        selected_cells.add((row, col))
                        continue
                    if point_in_polygon(col + 0.5, row + 0.5, poly_xy):
                        selected_cells.add((row, col))
            if not selected_cells:
                messagebox.showwarning("Asset", "Obrys nie obejmuje żadnych komórek.", parent=editor)
                return
            has_color = any(state["pixels"][row][col] for (row, col) in selected_cells)
            if not has_color:
                messagebox.showwarning("Asset", "Zaznaczony obszar nie zawiera kolorów.", parent=editor)
                return
            rows_selected = [row for row, _ in selected_cells]
            cols_selected = [col for _, col in selected_cells]
            bounds = (
                min(rows_selected),
                max(rows_selected),
                min(cols_selected),
                max(cols_selected),
            )
            name_suggestion = f"asset_precise_{hex_id.replace(',', '_')}_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
            response = prompt_asset_metadata(name_suggestion)
            if response is None:
                return
            asset_name, category_key = response
            selection_meta = {
                "type": "polygon",
                "loop": [{"row": r, "col": c} for r, c in loop_points],
                "cell_count": len(selected_cells),
            }
            if save_asset_from_selection(asset_name, category_key, bounds, selected_cells, selection_meta):
                deactivate_precision_mode()
                if state.get("preset_detail_window"):
                    close_preset_window("preset_detail_window")
                if state.get("preset_category_window"):
                    close_preset_window("preset_category_window")
                messagebox.showinfo("Asset", f"Zapisano asset „{asset_name}”.", parent=editor)

        def deactivate_asset_mode(update_button: bool = True) -> None:
            state["asset_mode_active"] = False
            state["asset_selection_start"] = None
            state["asset_selection_bounds"] = None
            clear_asset_selection_overlay()
            if update_button and asset_mode_btn is not None:
                asset_mode_btn.config(relief=tk.RAISED)
            cursor = ""
            if state.get("precision_mode_active"):
                cursor = "tcross"
            elif state.get("stamp_pixels") is not None:
                cursor = "hand2"
            preview_canvas.config(cursor=cursor)

        def toggle_asset_mode() -> None:
            if state.get("asset_mode_active"):
                deactivate_asset_mode()
                return
            if state.get("stamp_pixels") is not None:
                clear_stamp_mode()
            if state.get("precision_mode_active"):
                deactivate_precision_mode(update_button=True)
            state["asset_mode_active"] = True
            state["asset_selection_start"] = None
            state["asset_selection_bounds"] = None
            if asset_mode_btn is not None:
                asset_mode_btn.config(relief=tk.SUNKEN)
            preview_canvas.config(cursor="tcross")

        def start_asset_selection(event) -> None:
            cell = get_cell_from_event(event)
            if not state.get("asset_mode_active") or cell is None:
                return
            row, col = cell
            clear_asset_selection_overlay()
            state["asset_selection_start"] = (row, col)
            state["asset_selection_bounds"] = (row, row, col, col)
            draw_asset_selection((row, row, col, col))

        def update_asset_selection(event) -> None:
            if not state.get("asset_mode_active"):
                return
            start = state.get("asset_selection_start")
            if start is None:
                return
            cell = get_cell_from_event(event)
            if cell is None:
                return
            row, col = cell
            start_row, start_col = start
            row_min = min(start_row, row)
            row_max = max(start_row, row)
            col_min = min(start_col, col)
            col_max = max(start_col, col)
            bounds = (row_min, row_max, col_min, col_max)
            state["asset_selection_bounds"] = bounds
            draw_asset_selection(bounds)

        def prompt_asset_metadata(default_name: str) -> tuple[str, str] | None:
            dialog = tk.Toplevel(editor)
            dialog.title("Nowy asset")
            dialog.configure(bg="darkolivegreen")
            dialog.transient(editor)
            dialog.grab_set()
            name_var = tk.StringVar(value=default_name)
            label_to_key = {meta["label"]: key for key, meta in USER_ASSET_CATEGORY_DEFS.items()}
            labels = list(label_to_key.keys())
            default_label = labels[0] if labels else ""
            category_var = tk.StringVar(value=default_label)

            tk.Label(dialog, text="Nazwa assetu", bg="darkolivegreen", fg="white").pack(fill=tk.X, padx=12, pady=(12, 4))
            name_entry = tk.Entry(dialog, textvariable=name_var)
            name_entry.pack(fill=tk.X, padx=12)

            tk.Label(dialog, text="Kategoria", bg="darkolivegreen", fg="white").pack(fill=tk.X, padx=12, pady=(10, 4))
            category_combo = ttk.Combobox(dialog, values=labels, state="readonly", textvariable=category_var)
            category_combo.pack(fill=tk.X, padx=12)
            if labels:
                category_combo.current(0)

            result: dict[str, tuple[str, str] | None] = {"value": None}

            def accept() -> None:
                name_value = name_var.get().strip()
                label_value = category_var.get()
                if not name_value:
                    messagebox.showwarning("Asset", "Podaj nazwę assetu.", parent=dialog)
                    return
                key = label_to_key.get(label_value)
                if not key:
                    messagebox.showwarning("Asset", "Wybierz kategorię.", parent=dialog)
                    return
                result["value"] = (name_value, key)
                dialog.destroy()

            def cancel() -> None:
                result["value"] = None
                dialog.destroy()

            button_row = tk.Frame(dialog, bg="darkolivegreen")
            button_row.pack(fill=tk.X, padx=12, pady=(14, 12))
            tk.Button(button_row, text="Zapisz", command=accept, bg="forestgreen", fg="white").pack(side=tk.LEFT, expand=True, fill=tk.X, padx=(0, 6))
            tk.Button(button_row, text="Anuluj", command=cancel, bg="#555555", fg="white").pack(side=tk.LEFT, expand=True, fill=tk.X)

            name_entry.focus_set()
            dialog.wait_window()
            return result["value"]

        def save_asset_from_selection(
            name: str,
            category_key: str,
            bounds: tuple[int, int, int, int],
            selected_cells: set[tuple[int, int]] | None = None,
            selection_meta: dict | None = None,
        ) -> bool:
            slug = sanitize_asset_slug(name)
            target_dir = CUSTOM_ASSET_ROOT / category_key
            try:
                target_dir.mkdir(parents=True, exist_ok=True)
            except Exception as exc:
                messagebox.showerror("Asset", f"Nie udało się utworzyć katalogu docelowego: {exc}")
                return False
            base_path = target_dir / slug
            suffix_counter = 1
            png_path = base_path.with_suffix(".png")
            json_path = base_path.with_suffix(".json")
            thumb_path = target_dir / f"{slug}_thumb.png"
            while png_path.exists() or json_path.exists() or thumb_path.exists():
                suffix_counter += 1
                slug_variant = f"{slug}_{suffix_counter}"
                base_path = target_dir / slug_variant
                png_path = base_path.with_suffix(".png")
                json_path = base_path.with_suffix(".json")
                thumb_path = target_dir / f"{slug_variant}_thumb.png"

            row_min, row_max, col_min, col_max = bounds
            allowed_cells = set(selected_cells) if selected_cells else None
            width = col_max - col_min + 1
            height = row_max - row_min + 1
            export_img = Image.new("RGBA", (width, height), (0, 0, 0, 0))
            for local_row, row in enumerate(range(row_min, row_max + 1)):
                for local_col, col in enumerate(range(col_min, col_max + 1)):
                    if allowed_cells is not None and (row, col) not in allowed_cells:
                        continue
                    if not hex_mask[row][col]:
                        continue
                    color_val = state["pixels"][row][col]
                    if color_val:
                        r_val = int(color_val[1:3], 16)
                        g_val = int(color_val[3:5], 16)
                        b_val = int(color_val[5:7], 16)
                        export_img.putpixel((local_col, local_row), (r_val, g_val, b_val, 255))

            try:
                export_img.save(png_path)
            except Exception as exc:
                messagebox.showerror("Asset", f"Nie udało się zapisać obrazu: {exc}")
                return False

            try:
                if width > 0 and height > 0:
                    scale = min(
                        USER_ASSET_THUMB_SIZE / max(1, width),
                        USER_ASSET_THUMB_SIZE / max(1, height),
                    )
                    thumb_width = max(1, int(round(width * scale)))
                    thumb_height = max(1, int(round(height * scale)))
                    scaled = export_img.resize((thumb_width, thumb_height), Image.NEAREST)
                    thumb_canvas = Image.new("RGBA", (USER_ASSET_THUMB_SIZE, USER_ASSET_THUMB_SIZE), (0, 0, 0, 0))
                    paste_x = (USER_ASSET_THUMB_SIZE - thumb_width) // 2
                    paste_y = (USER_ASSET_THUMB_SIZE - thumb_height) // 2
                    thumb_canvas.paste(scaled, (paste_x, paste_y), scaled)
                    thumb_canvas.save(thumb_path)
            except Exception as exc:
                print(f"⚠️  Nie udało się zapisać miniatury {thumb_path.name}: {exc}")

            metadata = {
                "name": name,
                "category": category_key,
                "grid_size": grid_size,
                "bounds": {
                    "row_min": row_min,
                    "row_max": row_max,
                    "col_min": col_min,
                    "col_max": col_max,
                },
                "origin": {
                    "row": row_min,
                    "col": col_min,
                },
                "size": {
                    "rows": height,
                    "cols": width,
                },
                "hotspot": {
                    "row": row_min + (row_max - row_min + 1) / 2.0,
                    "col": col_min + (col_max - col_min + 1) / 2.0,
                },
                "created_at": datetime.now().isoformat(timespec="seconds"),
                "source_hex": hex_id,
                "image": to_rel(str(png_path)),
                "thumbnail": to_rel(str(thumb_path)) if thumb_path.exists() else None,
            }
            if selection_meta:
                metadata["selection"] = selection_meta

            try:
                with json_path.open("w", encoding="utf-8") as fh:
                    json.dump(metadata, fh, indent=2, ensure_ascii=False)
            except Exception as exc:
                messagebox.showerror("Asset", f"Nie udało się zapisać metadanych: {exc}")
                return False

            print(f"✅ Zapisano asset: {json_path.name} ({metadata['category']})")
            return True

        def finalize_asset_selection(event) -> None:
            if not state.get("asset_mode_active"):
                return
            if state.get("asset_selection_start") is None:
                return
            update_asset_selection(event)
            bounds = state.get("asset_selection_bounds")
            if not bounds:
                return
            content_bounds = compute_content_bounds(bounds)
            if content_bounds is None:
                messagebox.showwarning("Asset", "Zaznaczenie nie zawiera kolorów, nie można utworzyć assetu.", parent=editor)
                return
            state["asset_selection_bounds"] = content_bounds
            draw_asset_selection(content_bounds)
            name_suggestion = f"asset_{hex_id.replace(',', '_')}_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
            response = prompt_asset_metadata(name_suggestion)
            if response is None:
                return
            asset_name, category_key = response
            if save_asset_from_selection(asset_name, category_key, content_bounds):
                deactivate_asset_mode()
                if state.get("preset_detail_window"):
                    close_preset_window("preset_detail_window")
                if state.get("preset_category_window"):
                    close_preset_window("preset_category_window")
                messagebox.showinfo("Asset", f"Zapisano asset „{asset_name}”.", parent=editor)

        def cancel_asset_mode() -> None:
            deactivate_asset_mode()

        def clear_stamp_mode(update_label: bool = True) -> None:
            state["stamp_pixels"] = None
            state["stamp_overlay_photo"] = None
            state["stamp_offset"] = (0, 0)
            state["stamp_base_pixels"] = None
            state["stamp_label"] = None
            if state.get("stamp_preview_id") is not None:
                preview_canvas.delete(state["stamp_preview_id"])
                state["stamp_preview_id"] = None
            cursor = ""
            if state.get("asset_mode_active") or state.get("precision_mode_active"):
                cursor = "tcross"
            preview_canvas.config(cursor=cursor)
            if update_label and stamp_status_label is not None:
                stamp_status_label.config(text="Preset: brak")

        def enter_stamp_mode(preset: dict) -> None:
            clear_stamp_mode(update_label=False)
            deactivate_precision_mode(update_button=True)
            deactivate_asset_mode()
            state["stamp_base_pixels"] = preset["pixels"]
            state["stamp_label"] = preset["name"]
            preset_hotspot = preset.get("hotspot")
            if isinstance(preset_hotspot, dict):
                hotspot_row = float(preset_hotspot.get("row", grid_size / 2.0))
                hotspot_col = float(preset_hotspot.get("col", grid_size / 2.0))
                state["stamp_hotspot"] = (hotspot_row, hotspot_col)
            elif isinstance(preset_hotspot, (list, tuple)) and len(preset_hotspot) >= 2:
                state["stamp_hotspot"] = (float(preset_hotspot[0]), float(preset_hotspot[1]))
            else:
                state["stamp_hotspot"] = (grid_size / 2.0, grid_size / 2.0)
            state["stamp_offset"] = (0, 0)
            state["stamp_scale_percent"] = float(stamp_scale_var.get())
            refresh_stamp_from_scale()
            preview_canvas.config(cursor="hand2")
            pointer_row, pointer_col = state.get("stamp_pointer_position", (grid_size / 2.0, grid_size / 2.0))
            update_stamp_overlay_position(pointer_row, pointer_col)
            if stamp_status_label is not None:
                stamp_status_label.config(text=f"Preset: {preset['name']} — kliknij, aby wstawić (skala {int(round(state['stamp_scale_percent']))}%)")

        def apply_stamp_at(pointer_row: float, pointer_col: float) -> None:
            if state.get("stamp_pixels") is None:
                return
            hotspot_row, hotspot_col = state.get("stamp_hotspot", (grid_size / 2.0, grid_size / 2.0))
            top_left_row_float = pointer_row - hotspot_row
            top_left_col_float = pointer_col - hotspot_col
            top_left_row = int(math.floor(top_left_row_float))
            top_left_col = int(math.floor(top_left_col_float))
            state["stamp_offset"] = (top_left_row, top_left_col)
            update_stamp_overlay_position(pointer_row, pointer_col)
            changed = False
            neighbor_changed = False
            stamp_pixels = state["stamp_pixels"]
            neighbor_entry = None
            if state.get("edge_mode_active") and state.get("edge_current_key"):
                neighbor_entry = state["edge_neighbors"].get(state["edge_current_key"])
                if neighbor_entry and not neighbor_entry.get("enabled"):
                    neighbor_entry = None
            neighbor_candidates = [
                entry
                for entry in state["edge_neighbors"].values()
                if entry and entry.get("enabled") and entry.get("neighbor_pixels") is not None
            ]
            for src_row in range(grid_size):
                target_row = top_left_row + src_row
                if not (0 <= target_row < grid_size):
                    local_row_in_bounds = False
                else:
                    local_row_in_bounds = True
                for src_col in range(grid_size):
                    target_col = top_left_col + src_col
                    if not (0 <= target_col < grid_size):
                        local_col_in_bounds = False
                    else:
                        local_col_in_bounds = True
                    color = stamp_pixels[src_row][src_col]
                    if color is None:
                        continue
                    local_applied = False
                    if local_row_in_bounds and local_col_in_bounds:
                        if state["mask"][target_row][target_col]:
                            if state["pixels"][target_row][target_col] != color:
                                state["pixels"][target_row][target_col] = color
                                changed = True
                            local_applied = True
                            if neighbor_entry and color is not None:
                                if apply_color_to_neighbor(neighbor_entry, target_row, target_col, color):
                                    changed = True
                                    neighbor_changed = True
                    if local_applied:
                        continue
                    if not neighbor_candidates:
                        continue
                    for entry in neighbor_candidates:
                        dx_cells = entry.get("dx_cells", 0)
                        dy_cells = entry.get("dy_cells", 0)
                        nr = target_row - dy_cells
                        nc = target_col - dx_cells
                        if not (0 <= nr < grid_size and 0 <= nc < grid_size):
                            continue
                        neighbor_mask = entry.get("neighbor_mask", hex_mask)
                        if not neighbor_mask[nr][nc]:
                            continue
                        neighbor_pixels = entry.get("neighbor_pixels")
                        if neighbor_pixels is None:
                            continue
                        if neighbor_pixels[nr][nc] != color:
                            neighbor_pixels[nr][nc] = color
                            entry["dirty"] = True
                            changed = True
                        neighbor_changed = True
                    # koniec synchronizacji sąsiadów
            if changed:
                state["history_edit_dirty"] = True
                draw_grid()
                if neighbor_changed:
                    refresh_edge_preview(refresh_background=True)

        def canvas_motion(event):
            if state.get("precision_mode_active"):
                update_precision_hover(get_cell_from_event(event, clamp=False))
                return
            if state.get("asset_mode_active"):
                if state.get("asset_selection_start") is not None:
                    update_asset_selection(event)
                return
            if state.get("stamp_pixels") is None:
                return
            pointer = get_pointer_position(event, clamp=False)
            if pointer is None:
                return
            row, col = pointer
            update_stamp_overlay_position(row, col)

        def reset_view_offset(event=None) -> str | None:
            if state.get("view_offset") != (0, 0):
                state["view_offset"] = (0, 0)
                draw_grid()
            return "break" if event is not None else None

        def pan_view(delta_x_px: int, delta_y_px: int) -> None:
            offset_x, offset_y = state.get("view_offset", (0, 0))
            max_span = grid_size * cell_size + grid_offset
            new_x = max(-max_span, min(max_span, offset_x + delta_x_px))
            new_y = max(-max_span, min(max_span, offset_y + delta_y_px))
            if (new_x, new_y) != (offset_x, offset_y):
                state["view_offset"] = (new_x, new_y)
                draw_grid()

        def handle_pan_key(event) -> str:
            base_step = max(cell_size * 3, 42)
            if event.state & 0x0001:  # Shift pressed
                base_step *= 2
            if event.keysym == "Left":
                pan_view(base_step, 0)
            elif event.keysym == "Right":
                pan_view(-base_step, 0)
            elif event.keysym == "Up":
                pan_view(0, base_step)
            elif event.keysym == "Down":
                pan_view(0, -base_step)
            else:
                return "break"
            return "break"


        def draw_grid():
            preview_canvas.delete("background")
            preview_canvas.delete("neighbor_preview")
            offset_x, offset_y = state.get("view_offset", (0, 0))
            background_photo = state.get("background_photo")
            if background_photo:
                bg_id = preview_canvas.create_image(
                    offset_x,
                    offset_y,
                    anchor="nw",
                    image=background_photo,
                    tags="background",
                )
                state["background_item_id"] = bg_id
                preview_canvas._background_photo = background_photo
            else:
                state["background_item_id"] = None
            preview_canvas.delete("cell")
            preview_canvas.delete("outline")
            preview_canvas.delete("neighbor_outline")
            preview_canvas.delete("stamp_preview")
            preview_canvas.delete("edge_band")
            for row in range(grid_size):
                for col in range(grid_size):
                    if not state["mask"][row][col]:
                        continue
                    x0 = col * cell_size + grid_offset + offset_x
                    y0 = row * cell_size + grid_offset + offset_y
                    fill = state["pixels"][row][col] or ""
                    preview_canvas.create_rectangle(
                        x0,
                        y0,
                        x0 + cell_size,
                        y0 + cell_size,
                        fill=fill if fill else "",
                        outline="#333333",
                        width=1,
                        tags=("cell", f"cell_{row}_{col}")
                    )
            for poly_points in neighbor_outline_points:
                shifted = []
                for idx in range(0, len(poly_points), 2):
                    shifted.append(poly_points[idx] + offset_x)
                    shifted.append(poly_points[idx + 1] + offset_y)
                preview_canvas.create_polygon(
                    *shifted,
                    outline="#555555",
                    fill="",
                    width=1,
                    tags="neighbor_outline",
                    smooth=False
                )
            shifted_outline = []
            for idx in range(0, len(outline_points), 2):
                shifted_outline.append(outline_points[idx] + offset_x)
                shifted_outline.append(outline_points[idx + 1] + offset_y)
            preview_canvas.create_polygon(
                *shifted_outline,
                outline="#bbbbbb",
                fill="",
                width=2,
                tags="outline",
                smooth=False
            )
            if state.get("edge_mode_active") and state.get("edge_current_key"):
                edge_entry = state["edge_neighbors"].get(state["edge_current_key"])
                if edge_entry and edge_entry.get("enabled"):
                    for row in range(grid_size):
                        band_row = edge_entry["band_mask"][row]
                        if not any(band_row):
                            continue
                        for col in range(grid_size):
                            if not band_row[col]:
                                continue
                            x0 = col * cell_size + grid_offset + offset_x
                            y0 = row * cell_size + grid_offset + offset_y
                            preview_canvas.create_rectangle(
                                x0,
                                y0,
                                x0 + cell_size,
                                y0 + cell_size,
                                outline="#ffd966",
                                width=1,
                                tags="edge_band"
                            )
                    preview_canvas.tag_lower("edge_band", "outline")
            if state.get("asset_mode_active") and state.get("asset_selection_bounds"):
                draw_asset_selection(state["asset_selection_bounds"])
            update_precision_overlay()
            update_stamp_overlay_position()
            refresh_edge_preview()

        def refresh_edge_preview(*, refresh_background: bool = False) -> None:
            offset_x, offset_y = state.get("view_offset", (0, 0))
            if refresh_background:
                context_image = build_texture_context(
                    state.get("edge_neighbors"),
                    state.get("neighbor_hex_data"),
                )
                if context_image:
                    new_photo = ImageTk.PhotoImage(context_image)
                    state["background_photo"] = new_photo
                    bg_id = state.get("background_item_id")
                    if bg_id:
                        preview_canvas.itemconfig(bg_id, image=new_photo)
                    else:
                        bg_id = preview_canvas.create_image(
                            offset_x,
                            offset_y,
                            anchor="nw",
                            image=new_photo,
                            tags="background",
                        )
                        state["background_item_id"] = bg_id
                    preview_canvas._background_photo = new_photo
                else:
                    state["background_photo"] = None
                    if state.get("background_item_id"):
                        preview_canvas.delete("background")
                        state["background_item_id"] = None
            preview_canvas.delete("neighbor_preview")
            default_status = "Podgląd sąsiada: wyłączony"
            default_color = "#d4f2bf"
            if not state.get("edge_mode_active") or not state.get("edge_current_key"):
                if edge_sync_status_label is not None:
                    edge_sync_status_label.config(text=default_status, fg=default_color)
                return
            entry = state["edge_neighbors"].get(state["edge_current_key"])
            if not entry or not entry.get("enabled"):
                if edge_sync_status_label is not None:
                    edge_sync_status_label.config(
                        text="Podgląd sąsiada: niedostępny",
                        fg="#f2b6b6",
                    )
                return
            neighbor_pixels = entry.get("neighbor_pixels")
            if neighbor_pixels is None:
                if edge_sync_status_label is not None:
                    edge_sync_status_label.config(
                        text=f"Podgląd sąsiada: {entry['neighbor_id']} (brak danych)",
                        fg="#f2d7d5",
                    )
                return
            neighbor_mask = entry.get("neighbor_mask", hex_mask)
            band_mask = entry.get("band_mask")
            if not band_mask:
                if edge_sync_status_label is not None:
                    edge_sync_status_label.config(
                        text=f"Podgląd sąsiada: {entry['neighbor_id']} (pas niedostępny)",
                        fg="#f2d7d5",
                    )
                return
            neighbor_band_mask = entry.get("neighbor_band_mask")
            if neighbor_band_mask is None:
                neighbor_band_mask = [[False for _ in range(grid_size)] for _ in range(grid_size)]
            dx_cells = entry.get("dx_cells", 0)
            dy_cells = entry.get("dy_cells", 0)
            local_band_total = sum(sum(1 for cell in row if cell) for row in band_mask)
            neighbor_band_total = sum(sum(1 for cell in row if cell) for row in neighbor_band_mask)
            # Rysuj siatkę sąsiada, żeby było widać kratki
            for nr in range(grid_size):
                row_mask = neighbor_mask[nr]
                if not any(row_mask):
                    continue
                for nc in range(grid_size):
                    if not row_mask[nc]:
                        continue
                    x0 = (nc + dx_cells) * cell_size + grid_offset + offset_x
                    y0 = (nr + dy_cells) * cell_size + grid_offset + offset_y
                    preview_canvas.create_rectangle(
                        x0,
                        y0,
                        x0 + cell_size,
                        y0 + cell_size,
                        outline="#3e3e3e",
                        width=1,
                        fill="",
                        tags=("neighbor_preview", "neighbor_grid"),
                    )

            drawn = 0
            for nr in range(grid_size):
                for nc in range(grid_size):
                    if not neighbor_mask[nr][nc]:
                        continue
                    row = nr + dy_cells
                    col = nc + dx_cells
                    if not (0 <= row < grid_size and 0 <= col < grid_size):
                        continue
                    if not band_mask[row][col]:
                        continue
                    color = neighbor_pixels[nr][nc]
                    if not color:
                        continue
                    display_color = color
                    x0 = (nc + dx_cells) * cell_size + grid_offset + offset_x
                    y0 = (nr + dy_cells) * cell_size + grid_offset + offset_y
                    preview_canvas.create_rectangle(
                        x0,
                        y0,
                        x0 + cell_size,
                        y0 + cell_size,
                        fill=display_color,
                        outline="#6f8a3a",
                        width=1,
                        tags="neighbor_preview",
                    )
                    drawn += 1
            
            # Wizualizacja pasów w przestrzeni kontekstu sąsiada
            projected_band_cells = 0
            for row in range(grid_size):
                for col in range(grid_size):
                    if not band_mask[row][col]:
                        continue
                    nr = row - dy_cells
                    nc = col - dx_cells
                    if not (0 <= nr < grid_size and 0 <= nc < grid_size):
                        continue
                    if not neighbor_mask[nr][nc]:
                        continue
                    x0 = (nc + dx_cells) * cell_size + grid_offset + offset_x
                    y0 = (nr + dy_cells) * cell_size + grid_offset + offset_y
                    preview_canvas.create_rectangle(
                        x0,
                        y0,
                        x0 + cell_size,
                        y0 + cell_size,
                        outline="#ff9933",
                        width=2,
                        fill="",
                        tags="neighbor_preview",
                    )
                    projected_band_cells += 1

            neighbor_band_drawn = 0
            for nr in range(grid_size):
                band_row = neighbor_band_mask[nr]
                if not any(band_row):
                    continue
                for nc in range(grid_size):
                    if not band_row[nc]:
                        continue
                    x0 = (nc + dx_cells) * cell_size + grid_offset + offset_x
                    y0 = (nr + dy_cells) * cell_size + grid_offset + offset_y
                    preview_canvas.create_rectangle(
                        x0,
                        y0,
                        x0 + cell_size,
                        y0 + cell_size,
                        outline="#ff9933",
                        width=2,
                        fill="",
                        tags=("neighbor_preview", "neighbor_band"),
                    )
                    neighbor_band_drawn += 1

            status_text = (
                f"Podgląd sąsiada: {entry['neighbor_id']} "
                f"(aktywny pas: {local_band_total} pól, druga strona: {neighbor_band_total} pól"
            )
            if drawn and drawn != local_band_total:
                status_text += f", podgląd koloru: {drawn}"
            if projected_band_cells and projected_band_cells != local_band_total:
                status_text += f", projekcja pasa: {projected_band_cells}"
            if neighbor_band_drawn and neighbor_band_drawn != neighbor_band_total:
                status_text += f", pas sąsiada: {neighbor_band_drawn}"
            status_text += ")"
            if edge_sync_status_label is not None:
                edge_sync_status_label.config(text=status_text, fg="#d4f2bf")

        def enter_edge_mode(edge_key: str) -> None:
            entry = state["edge_neighbors"].get(edge_key)
            if not entry or not entry.get("enabled"):
                return
            clear_stamp_mode()
            state["edge_mode_active"] = True
            state["edge_current_key"] = edge_key
            selected_edge_var.set(edge_key)
            if edge_status_label is not None:
                edge_status_label.config(
                    text=f"Aktywny: {entry['label']} (sąsiad {entry['neighbor_id']})"
                )
            draw_grid()
            refresh_edge_preview(refresh_background=True)

        def exit_edge_mode() -> None:
            state["edge_mode_active"] = False
            state["edge_current_key"] = None
            selected_edge_var.set("")
            if edge_status_label is not None:
                edge_status_label.config(text="Aktywny: brak")
            draw_grid()
            refresh_edge_preview(refresh_background=True)

        def refresh_edge_button_states() -> None:
            for key, widget in edge_button_widgets.items():
                entry = state["edge_neighbors"].get(key)
                if not entry or not entry.get("enabled"):
                    widget.config(state=tk.DISABLED, fg="#555555")
                else:
                    widget.config(state=tk.NORMAL, fg="white")

        def on_edge_band_width_change(value: str) -> None:
            nonlocal edge_mode_data
            try:
                new_width = int(float(value))
            except (TypeError, ValueError):
                new_width = state.get("edge_band_cells", EDGE_BAND_CELLS_DEFAULT)
            new_width = max(EDGE_BAND_CELLS_MIN, min(EDGE_BAND_CELLS_MAX, new_width))
            if state.get("edge_band_cells") == new_width:
                if edge_band_width_value_label is not None:
                    edge_band_width_value_label.config(text=f"Szerokość: {new_width} komórek")
                return
            state["edge_band_cells"] = new_width
            existing_neighbors = state.get("edge_neighbors")
            cached_neighbors = state.get("neighbor_hex_data")
            edge_mode_data = build_edge_mode_data(new_width, existing_neighbors, cached_neighbors)
            state["edge_neighbors"] = edge_mode_data
            refresh_edge_button_states()
            current_key = state.get("edge_current_key")
            if current_key:
                current_entry = state["edge_neighbors"].get(current_key)
                if not current_entry or not current_entry.get("enabled"):
                    exit_edge_mode()
            if edge_band_width_value_label is not None:
                edge_band_width_value_label.config(text=f"Szerokość: {new_width} komórek")
            max_bleed = state.get("edge_band_cells", new_width)
            if state.get("edge_bleed_depth", 0) > max_bleed:
                state["edge_bleed_depth"] = max_bleed
                edge_bleed_depth_var.set(max_bleed)
                on_edge_bleed_depth_change(str(max_bleed))
            else:
                if edge_bleed_depth_scale is not None:
                    edge_bleed_depth_scale.config(to=max_bleed)
                on_edge_bleed_depth_change(str(state.get("edge_bleed_depth", 0)))
            draw_grid()
            refresh_edge_preview(refresh_background=True)

        def on_edge_bleed_depth_change(value: str) -> None:
            try:
                depth = int(float(value))
            except (TypeError, ValueError):
                depth = state.get("edge_bleed_depth", EDGE_BLEED_DEPTH_DEFAULT)
            max_allowed = state.get("edge_band_cells", EDGE_BAND_CELLS_DEFAULT)
            depth = max(0, min(max_allowed, depth))
            state["edge_bleed_depth"] = depth
            if edge_bleed_depth_scale is not None:
                edge_bleed_depth_scale.config(to=max_allowed)
            if edge_bleed_depth_value_label is not None:
                edge_bleed_depth_value_label.config(text=bleed_depth_label_for_value(depth))
            if edge_bleed_depth_var.get() != depth:
                edge_bleed_depth_var.set(depth)

        def on_edge_blend_strength_change(value: str) -> None:
            try:
                strength = int(float(value))
            except (TypeError, ValueError):
                strength = EDGE_BLEND_DEFAULT_STRENGTH
            strength = max(0, min(100, strength))
            state["edge_blend_strength"] = strength
            if edge_blend_strength_value_label is not None:
                edge_blend_strength_value_label.config(text=f"Moc: {strength}%")

        def on_edge_blend_profile_change(event=None) -> None:
            label = edge_blend_profile_display_var.get()
            profile_key = EDGE_BLEND_PROFILE_LABEL_TO_KEY.get(label, EDGE_BLEND_PROFILE_DEFAULT)
            state["edge_blend_profile"] = profile_key

        def blend_active_edge() -> None:
            edge_key = state.get("edge_current_key")
            if not state.get("edge_mode_active") or not edge_key:
                if edge_status_label is not None:
                    edge_status_label.config(text="Aktywny: brak — wybierz krawędź do wygładzenia")
                return
            entry = state["edge_neighbors"].get(edge_key)
            if not entry or not entry.get("enabled"):
                if edge_status_label is not None:
                    edge_status_label.config(text="Aktywny: brak — wybierz krawędź do wygładzenia")
                return
            band_mask = entry.get("band_mask")
            distance_map = entry.get("band_distance")
            max_distance = entry.get("band_max_distance", 0)
            neighbor_pixels = entry.get("neighbor_pixels")
            neighbor_distance_map = entry.get("neighbor_band_distance")
            neighbor_max_distance = entry.get("neighbor_band_max_distance", 0)
            neighbor_source_row_map = entry.get("neighbor_source_row")
            neighbor_source_col_map = entry.get("neighbor_source_col")
            bleed_depth_setting = int(state.get("edge_bleed_depth", EDGE_BLEED_DEPTH_DEFAULT))
            bleed_depth_setting = max(0, min(bleed_depth_setting, state.get("edge_band_cells", EDGE_BAND_CELLS_DEFAULT)))
            if bleed_depth_setting <= 0:
                neighbor_effective_max = -1
            else:
                neighbor_effective_max = min(neighbor_max_distance, bleed_depth_setting - 1)
            if not band_mask or distance_map is None or neighbor_pixels is None:
                return
            strength = max(0, min(100, int(state.get("edge_blend_strength", EDGE_BLEND_DEFAULT_STRENGTH))))
            if strength <= 0:
                return
            strength_factor = strength / 100.0
            profile_key = state.get("edge_blend_profile", EDGE_BLEND_PROFILE_DEFAULT)
            profile_meta = EDGE_BLEND_PROFILES.get(profile_key, EDGE_BLEND_PROFILES[EDGE_BLEND_PROFILE_DEFAULT])
            exponent = profile_meta.get("exponent", 1.0)
            begin_edit_action()
            changes_made = False
            try:
                for row in range(grid_size):
                    for col in range(grid_size):
                        if not band_mask[row][col]:
                            continue
                        distance_value = distance_map[row][col]
                        if distance_value is None:
                            continue
                        ratio = 0.0 if max_distance <= 0 else float(distance_value) / float(max_distance)
                        weight = strength_factor * (1.0 - math.pow(ratio, exponent))
                        current_color = state["pixels"][row][col]
                        neighbor_row = row - entry["dy_cells"]
                        neighbor_col = col - entry["dx_cells"]
                        neighbor_color = None
                        if 0 <= neighbor_row < grid_size and 0 <= neighbor_col < grid_size:
                            neighbor_color = neighbor_pixels[neighbor_row][neighbor_col]
                        if weight <= 0.0:
                            continue
                        new_color = mix_hex_colors(current_color, neighbor_color, weight)
                        if new_color != current_color:
                            state["pixels"][row][col] = new_color
                            preview_canvas.itemconfig(
                                f"cell_{row}_{col}",
                                fill=new_color if new_color else "",
                            )
                            changes_made = True
                if (
                    bleed_depth_setting > 0
                    and neighbor_distance_map is not None
                    and neighbor_source_row_map is not None
                    and neighbor_source_col_map is not None
                ):
                    for nr in range(grid_size):
                        for nc in range(grid_size):
                            neighbor_distance_value = neighbor_distance_map[nr][nc]
                            if neighbor_distance_value is None or neighbor_distance_value >= bleed_depth_setting:
                                continue
                            if neighbor_effective_max <= 0:
                                neighbor_weight = strength_factor
                            else:
                                neighbor_ratio = 0.0 if neighbor_effective_max <= 0 else float(neighbor_distance_value) / float(neighbor_effective_max)
                                neighbor_ratio = max(0.0, min(1.0, neighbor_ratio))
                                neighbor_weight = strength_factor * (1.0 - math.pow(neighbor_ratio, exponent))
                            if neighbor_weight <= 0.0:
                                continue
                            source_row = neighbor_source_row_map[nr][nc]
                            source_col = neighbor_source_col_map[nr][nc]
                            if source_row is None or source_col is None:
                                continue
                            if not (0 <= source_row < grid_size and 0 <= source_col < grid_size):
                                continue
                            source_color = state["pixels"][source_row][source_col]
                            neighbor_color = neighbor_pixels[nr][nc]
                            new_neighbor_color = mix_hex_colors(neighbor_color, source_color, neighbor_weight)
                            if new_neighbor_color != neighbor_color:
                                neighbor_pixels[nr][nc] = new_neighbor_color
                                entry["dirty"] = True
                                changes_made = True
                if changes_made:
                    state["history_edit_dirty"] = True
                    draw_grid()
                    refresh_edge_preview(refresh_background=True)
                    if edge_status_label is not None:
                        edge_status_label.config(
                            text=f"Aktywny: {entry['label']} (sąsiad {entry['neighbor_id']}) — wygładzono"
                        )
            finally:
                finish_edit_action()

        def close_preset_window(ref_key: str) -> None:
            nonlocal stamp_scale_label, stamp_scale_widget
            window = state.get(ref_key)
            if window and window.winfo_exists():
                try:
                    window.destroy()
                except tk.TclError:
                    pass
            state[ref_key] = None
            if ref_key == "preset_category_window":
                stamp_scale_label = None
                stamp_scale_widget = None

        def open_presets_for_category(category: dict) -> None:
            existing = state.get("preset_detail_window")
            if existing and existing.winfo_exists():
                existing.destroy()
            win = tk.Toplevel(editor)
            win.title(f"Presety — {category['label']}")
            win.configure(bg="darkolivegreen")
            win.transient(editor)
            win.geometry("420x420")
            state["preset_detail_window"] = win

            def on_close_detail() -> None:
                close_preset_window("preset_detail_window")

            win.protocol("WM_DELETE_WINDOW", on_close_detail)

            header = tk.Label(win, text=category["label"], bg="darkolivegreen", fg="white", font=("Arial", 12, "bold"))
            header.pack(fill=tk.X, pady=(10, 6))

            content = tk.Frame(win, bg="darkolivegreen")
            content.pack(fill=tk.BOTH, expand=True, padx=12, pady=(0, 12))

            scroll_container = tk.Frame(content, bg="darkolivegreen")
            scroll_container.pack(fill=tk.BOTH, expand=True)

            presets_canvas = tk.Canvas(
                scroll_container,
                bg="darkolivegreen",
                highlightthickness=0
            )
            presets_canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

            presets_scrollbar = ttk.Scrollbar(
                scroll_container,
                orient=tk.VERTICAL,
                command=presets_canvas.yview
            )
            presets_scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

            presets_canvas.configure(yscrollcommand=presets_scrollbar.set)

            presets_inner = tk.Frame(presets_canvas, bg="darkolivegreen")
            presets_window = presets_canvas.create_window((0, 0), window=presets_inner, anchor="nw")

            def update_scroll_region(event=None) -> None:
                presets_canvas.configure(scrollregion=presets_canvas.bbox("all"))

            presets_inner.bind("<Configure>", update_scroll_region)

            def sync_inner_width(event=None) -> None:
                presets_canvas.itemconfigure(presets_window, width=presets_canvas.winfo_width())

            presets_canvas.bind("<Configure>", sync_inner_width)

            def _on_mousewheel(event):
                presets_canvas.yview_scroll(int(-1 * (event.delta / 120)), "units")

            presets_canvas.bind("<MouseWheel>", _on_mousewheel)
            presets_inner.bind("<MouseWheel>", _on_mousewheel)

            presets = category["builder"]()
            state["preset_preview_refs"] = [preset["preview_photo"] for preset in presets]

            if not presets:
                tk.Label(
                    presets_inner,
                    text="Brak presetów w tej kategorii",
                    bg="darkolivegreen",
                    fg="#f2d7d5",
                    font=("Arial", 10)
                ).pack(pady=12)
                return

            if category.get("user_key"):
                bulk_actions = tk.Frame(presets_inner, bg="darkolivegreen")
                bulk_actions.pack(fill=tk.X, pady=(0, 8))
                tk.Button(
                    bulk_actions,
                    text="Usuń wszystkie assety z tej kategorii",
                    command=lambda c=category: delete_all_user_assets(c),
                    bg="#663333",
                    fg="white",
                    activebackground="#884444",
                    activeforeground="white",
                    bd=1,
                ).pack(fill=tk.X)

            grid = tk.Frame(presets_inner, bg="darkolivegreen")
            grid.pack(fill=tk.BOTH, expand=True)
            columns = 2
            for idx, preset in enumerate(presets):
                grid.grid_columnconfigure(idx % columns, weight=1)
                item = tk.Frame(grid, bg="darkolivegreen", bd=1, relief=tk.GROOVE)
                item.grid(row=idx // columns, column=idx % columns, padx=6, pady=6, sticky="nsew")

                def _select_preset(preset=preset):
                    enter_stamp_mode(preset)
                    close_preset_window("preset_detail_window")

                preview_btn = tk.Button(
                    item,
                    image=preset["preview_photo"],
                    text=preset["name"],
                    compound="top",
                    bg="darkolivegreen",
                    fg="white",
                    activebackground="darkolivegreen",
                    activeforeground="white",
                    bd=1,
                    relief=tk.RIDGE,
                    wraplength=150,
                    justify="center",
                    command=_select_preset,
                )
                preview_btn.pack(fill=tk.BOTH, expand=True)

                if preset.get("meta_path"):
                    tk.Button(
                        item,
                        text="Usuń",
                        command=lambda p=preset, c=category: delete_user_asset(p, c),
                        bg="#803333",
                        fg="white",
                        activebackground="#a94444",
                        activeforeground="white",
                        bd=1,
                    ).pack(fill=tk.X, padx=4, pady=(4, 4))

        def open_preset_library() -> None:
            nonlocal stamp_scale_label, stamp_scale_widget
            existing = state.get("preset_category_window")
            if existing and existing.winfo_exists():
                existing.deiconify()
                existing.lift()
                if stamp_scale_label is not None:
                    stamp_scale_label.config(text=f"Skala: {int(round(stamp_scale_var.get()))}%")
                return
            win = tk.Toplevel(editor)
            win.title("Biblioteka presetów")
            win.configure(bg="darkolivegreen")
            win.transient(editor)
            win.geometry("440x620")
            win.minsize(360, 520)
            win.resizable(True, True)
            state["preset_category_window"] = win

            def on_close() -> None:
                close_preset_window("preset_category_window")

            win.protocol("WM_DELETE_WINDOW", on_close)

            tk.Label(
                win,
                text="Wybierz kategorię",
                bg="darkolivegreen",
                fg="white",
                font=("Arial", 12, "bold")
            ).pack(fill=tk.X, pady=(12, 6))

            container = tk.Frame(win, bg="darkolivegreen")
            container.pack(fill=tk.BOTH, expand=True, padx=12, pady=(0, 12))

            for category in preset_categories:
                btn = tk.Button(
                    container,
                    text=f"{category['icon']}  {category['label']}",
                    anchor="w",
                    command=lambda c=category: open_presets_for_category(c),
                    bg="saddlebrown",
                    fg="white",
                    activebackground="saddlebrown",
                    activeforeground="white"
                )
                btn.pack(fill=tk.X, pady=4)

            def disable_preset_from_library() -> None:
                clear_stamp_mode()
                close_preset_window("preset_detail_window")

            controls = tk.Frame(win, bg="darkolivegreen")
            controls.pack(fill=tk.X, padx=12, pady=(0, 12))
            tk.Button(
                controls,
                text="Wyłącz preset",
                command=disable_preset_from_library,
                bg="#555555",
                fg="white",
                activebackground="#555555",
                activeforeground="white"
            ).pack(fill=tk.X)

            scale_frame = tk.LabelFrame(controls, text="Skala presetów", bg="darkolivegreen", fg="white")
            scale_frame.pack(fill=tk.X, pady=(12, 0))
            stamp_scale_label = tk.Label(scale_frame, text="Skala: 100%", bg="darkolivegreen", fg="#d4f2bf", anchor="w")
            stamp_scale_label.pack(fill=tk.X, padx=4, pady=(4, 0))
            stamp_scale_widget = tk.Scale(
                scale_frame,
                from_=10,
                to=100,
                resolution=5,
                orient=tk.HORIZONTAL,
                variable=stamp_scale_var,
                command=on_scale_change,
                length=220,
                bg="darkolivegreen",
                highlightthickness=0,
                troughcolor="#555555"
            )
            stamp_scale_widget.pack(fill=tk.X, padx=4, pady=(2, 4))
            on_scale_change(str(stamp_scale_var.get()))

        def set_current_color(color: str | None):
            if state.get("stamp_pixels") is not None:
                clear_stamp_mode()
            state["current_color"] = color
            state["eraser"] = False
            if color:
                current_color_preview.config(bg=color, text="", fg="white")
            else:
                current_color_preview.config(bg="#222222", text="Przezroczysty", fg="white")

        def pick_color_dialog():
            color_code = colorchooser.askcolor(title="Wybierz kolor", parent=editor)
            if color_code and color_code[1]:
                set_current_color(color_code[1])

        def toggle_eraser():
            if state.get("stamp_pixels") is not None:
                clear_stamp_mode()
            state["eraser"] = not state["eraser"]
            eraser_btn.config(relief="sunken" if state["eraser"] else "raised")

        def brush_label_for_radius(radius: int) -> str:
            diameter = radius * 2 + 1
            if radius <= 0:
                return "Promień: 0 (1×1)"
            return f"Promień: {radius} (do {diameter}×{diameter})"

        def bleed_depth_label_for_value(depth: int) -> str:
            if depth <= 0:
                return "Przenikanie: 0 (wyłączone)"
            if depth == 1:
                return "Przenikanie: 1 komórka"
            return f"Przenikanie: {depth} komórek"

        def on_brush_radius_change(value: str) -> None:
            try:
                radius = int(float(value))
            except (TypeError, ValueError):
                radius = state.get("brush_radius", BRUSH_RADIUS_DEFAULT)
            radius = max(BRUSH_RADIUS_MIN, min(BRUSH_RADIUS_MAX, radius))
            state["brush_radius"] = radius
            if brush_radius_value_label is not None:
                brush_radius_value_label.config(text=brush_label_for_radius(radius))

        def apply_color_to_cell(row: int, col: int) -> bool:
            if not (0 <= row < grid_size and 0 <= col < grid_size):
                return False
            if not state["mask"][row][col]:
                return False
            edge_entry = None
            if state.get("edge_mode_active"):
                edge_key = state.get("edge_current_key")
                if not edge_key:
                    return False
                edge_entry = state["edge_neighbors"].get(edge_key)
                if not edge_entry or not edge_entry.get("enabled"):
                    return False
                if not edge_entry["band_mask"][row][col]:
                    return False
            new_val = None if state["eraser"] else state["current_color"]
            pixel_changed = False
            if state["pixels"][row][col] != new_val:
                state["pixels"][row][col] = new_val
                fill = new_val if new_val else ""
                preview_canvas.itemconfig(f"cell_{row}_{col}", fill=fill)
                pixel_changed = True
            neighbor_changed = False
            if edge_entry:
                neighbor_changed = apply_color_to_neighbor(edge_entry, row, col, new_val)
            if pixel_changed or neighbor_changed:
                state["history_edit_dirty"] = True
            return neighbor_changed

        def paint_with_brush(center_row: int, center_col: int) -> None:
            radius = int(state.get("brush_radius", BRUSH_RADIUS_DEFAULT))
            if radius <= 0:
                neighbor_touched = apply_color_to_cell(center_row, center_col)
                if neighbor_touched:
                    refresh_edge_preview(refresh_background=True)
                return
            neighbor_touched = False
            for row in range(center_row - radius, center_row + radius + 1):
                if row < 0 or row >= grid_size:
                    continue
                row_offset = row - center_row
                for col in range(center_col - radius, center_col + radius + 1):
                    if col < 0 or col >= grid_size:
                        continue
                    if not state["mask"][row][col]:
                        continue
                    col_offset = col - center_col
                    if math.hypot(row_offset, col_offset) <= radius + 0.35:
                        if apply_color_to_cell(row, col):
                            neighbor_touched = True
            if neighbor_touched:
                refresh_edge_preview(refresh_background=True)

        def paint_neighbor_band(entry: dict, neighbor_center_row: int, neighbor_center_col: int) -> bool:
            if not entry or not entry.get("enabled"):
                return False
            neighbor_pixels = entry.get("neighbor_pixels")
            if neighbor_pixels is None:
                return False
            neighbor_mask = entry.get("neighbor_mask", hex_mask)
            neighbor_band_mask = entry.get("neighbor_band_mask")
            radius = int(state.get("brush_radius", BRUSH_RADIUS_DEFAULT))
            new_val = None if state.get("eraser") else state.get("current_color")
            changed = False
            for nr in range(neighbor_center_row - radius, neighbor_center_row + radius + 1):
                if nr < 0 or nr >= grid_size:
                    continue
                row_offset = nr - neighbor_center_row
                for nc in range(neighbor_center_col - radius, neighbor_center_col + radius + 1):
                    if nc < 0 or nc >= grid_size:
                        continue
                    if not neighbor_mask[nr][nc]:
                        continue
                    if neighbor_band_mask and not neighbor_band_mask[nr][nc]:
                        continue
                    col_offset = nc - neighbor_center_col
                    if radius > 0 and math.hypot(row_offset, col_offset) > radius + 0.35:
                        continue
                    if neighbor_pixels[nr][nc] == new_val:
                        continue
                    neighbor_pixels[nr][nc] = new_val
                    entry["dirty"] = True
                    changed = True
            if changed:
                state["history_edit_dirty"] = True
                refresh_edge_preview(refresh_background=True)
            return changed

        def canvas_paint(event):
            if state.get("precision_mode_active"):
                return
            if state.get("asset_mode_active"):
                return
            if state.get("stamp_pixels") is not None:
                pointer = get_pointer_position(event, clamp=False)
                if pointer is None:
                    return
                row_f, col_f = pointer
                apply_stamp_at(row_f, col_f)
                return
            
            # Sprawdź, czy kliknięto w obszar sąsiada (poza centralnym heksem)
            cell = get_cell_from_event(event, clamp=False)
            if cell is not None:
                row, col = cell
                # Jeśli kliknięto w obszar centralnego heksa, maluj normalnie
                if hex_mask[row][col]:
                    paint_with_brush(row, col)
                    return
            
            # Sprawdź kliknięcie w podgląd sąsiada - konwertuj współrzędne kanwy
            offset_x, offset_y = state.get("view_offset", (0, 0))
            canvas_x = event.x - grid_offset - offset_x
            canvas_y = event.y - grid_offset - offset_y
            
            # Pozycja w komórkach względem centrum
            col_center = canvas_x / cell_size
            row_center = canvas_y / cell_size
            
            # Sprawdź wszystkich sąsiadów w określonej kolejności
            for edge_key in ["E", "NE", "NW", "W", "SW", "SE"]:
                edge_entry = state["edge_neighbors"].get(edge_key)
                if not edge_entry or not edge_entry.get("enabled"):
                    continue
                
                neighbor_id = edge_entry["neighbor_id"]
                dx_cells = edge_entry.get("dx_cells", 0)
                dy_cells = edge_entry.get("dy_cells", 0)
                
                # Przelicz na współrzędne w przestrzeni sąsiada
                neighbor_col = int(col_center - dx_cells)
                neighbor_row = int(row_center - dy_cells)
                
                if not (0 <= neighbor_row < grid_size and 0 <= neighbor_col < grid_size):
                    continue
                
                neighbor_mask = edge_entry.get("neighbor_mask", hex_mask)
                if neighbor_mask[neighbor_row][neighbor_col]:
                    if (
                        state.get("edge_mode_active")
                        and state.get("edge_current_key")
                        and state.get("edge_current_key") == edge_key
                    ):
                        if paint_neighbor_band(edge_entry, neighbor_row, neighbor_col):
                            pass
                        return
                    # Kliknięto w obszar sąsiada - przełącz na tego sąsiada
                    switch_to_hex(neighbor_id)
                    return

        def canvas_pick_color(event):
            if state.get("precision_mode_active"):
                return
            if state.get("asset_mode_active"):
                return
            preview_canvas.focus_set()
            
            # Sprawdź, czy kliknięto w obszar centralnego heksa
            cell = get_cell_from_event(event, clamp=False)
            if cell is not None:
                row, col = cell
                if state["mask"][row][col]:
                    if state.get("edge_mode_active"):
                        edge_key = state.get("edge_current_key")
                        if edge_key:
                            edge_entry = state["edge_neighbors"].get(edge_key)
                            if edge_entry and edge_entry.get("enabled") and edge_entry["band_mask"][row][col]:
                                color = state["pixels"][row][col]
                                if color:
                                    if state.get("stamp_pixels") is not None:
                                        clear_stamp_mode()
                                    set_current_color(color)
                                return
                    else:
                        color = state["pixels"][row][col]
                        if color:
                            if state.get("stamp_pixels") is not None:
                                clear_stamp_mode()
                            set_current_color(color)
                        return

        def handle_left_press(event):
            preview_canvas.focus_set()
            if state.get("precision_mode_active"):
                precision_add_point(event)
                return
            if state.get("asset_mode_active"):
                start_asset_selection(event)
                return
            begin_edit_action()
            canvas_paint(event)

        def handle_left_drag(event):
            if state.get("precision_mode_active"):
                update_precision_hover(get_cell_from_event(event, clamp=False))
                return
            if state.get("asset_mode_active"):
                update_asset_selection(event)
                return
            canvas_paint(event)

        def handle_left_release(event):
            if state.get("precision_mode_active"):
                update_precision_hover(get_cell_from_event(event, clamp=False))
                return "break"
            if state.get("asset_mode_active"):
                finalize_asset_selection(event)
                return "break"
            finish_edit_action(event)
            return None

        preview_canvas.bind("<ButtonPress-1>", handle_left_press)
        preview_canvas.bind("<B1-Motion>", handle_left_drag)
        preview_canvas.bind("<ButtonRelease-1>", handle_left_release)
        preview_canvas.bind("<Button-3>", canvas_pick_color)
        preview_canvas.bind("<Motion>", canvas_motion)
        preview_canvas.bind("<KeyPress-Left>", handle_pan_key)
        preview_canvas.bind("<KeyPress-Right>", handle_pan_key)
        preview_canvas.bind("<KeyPress-Up>", handle_pan_key)
        preview_canvas.bind("<KeyPress-Down>", handle_pan_key)
        preview_canvas.bind("<KeyPress-space>", reset_view_offset)
        preview_canvas.bind("<KeyPress-BackSpace>", precision_remove_last)
        preview_canvas.bind("<KeyPress-Escape>", precision_cancel)
        preview_canvas.bind("<KeyPress-Return>", precision_attempt_finish)
        preview_canvas.focus_set()

        toolbar = tk.Frame(editor, bg="darkolivegreen", width=360)
        toolbar.grid(row=0, column=1, sticky="ew", padx=(0, 12), pady=(12, 4))

        size_label_map = {size: f"{size}x{size}" for size in HEX_TEXTURE_GRID_OPTIONS}
        label_to_size = {label: size for size, label in size_label_map.items()}
        grid_size_var = tk.StringVar(value=size_label_map[grid_size])

        def handle_grid_size_change(event=None):
            label = grid_size_var.get()
            target = label_to_size.get(label)
            if target is None or target == state.get("grid_size", grid_size):
                return
            finish_edit_action()
            if state.get("history_edit_dirty") or state.get("undo_stack"):
                confirm = messagebox.askyesno(
                    "Zmiana rozdzielczości",
                    "Przełączyć siatkę na nową rozdzielczość? Aktualna edycja zostanie przeskalowana.",
                    parent=editor,
                )
                if not confirm:
                    grid_size_var.set(size_label_map[state.get("grid_size", grid_size)])
                    return
            converted = resample_pixel_grid(state["pixels"], state["grid_size"], target)

            def reopen() -> None:
                close_editor()
                self.open_hex_texture_editor(hex_id, grid_size=target, initial_pixels=converted)

            editor.after(10, reopen)

        grid_selector_frame = tk.Frame(toolbar, bg="darkolivegreen")
        grid_selector_frame.pack(side=tk.LEFT, padx=(0, 8))
        tk.Label(
            grid_selector_frame,
            text="Siatka",
            bg="darkolivegreen",
            fg="white",
            font=("Arial", 9, "bold")
        ).pack(anchor="w")
        grid_selector = ttk.Combobox(
            grid_selector_frame,
            textvariable=grid_size_var,
            values=[size_label_map[size] for size in HEX_TEXTURE_GRID_OPTIONS],
            state="readonly",
            width=10
        )
        grid_selector.pack(anchor="w", pady=(2, 0))
        grid_selector.bind("<<ComboboxSelected>>", handle_grid_size_change)

        tk.Button(
            toolbar,
            text="Wyśrodkuj podgląd",
            command=reset_view_offset,
            bg="#444444",
            fg="white"
        ).pack(side=tk.LEFT, padx=(0, 8))

        asset_mode_btn = tk.Button(
            toolbar,
            text="Tworzenie assetu",
            command=toggle_asset_mode,
            bg="#556b2f",
            fg="white"
        )
        asset_mode_btn.pack(side=tk.LEFT, padx=(0, 8))

        precision_mode_btn = tk.Button(
            toolbar,
            text="Obrys assetu",
            command=toggle_precision_mode,
            bg="#6b8e23",
            fg="white"
        )
        precision_mode_btn.pack(side=tk.LEFT, padx=(0, 8))

        precision_undo_btn = tk.Button(
            toolbar,
            text="Cofnij punkt obrysu",
            command=precision_remove_last,
            bg="#444444",
            fg="white",
            state=tk.DISABLED
        )
        precision_undo_btn.pack(side=tk.LEFT, padx=(0, 8))
        update_precision_controls()

        tools_container = tk.Frame(editor, bg="darkolivegreen", width=360)
        tools_container.grid(row=1, column=1, sticky="nsew", padx=(0, 12), pady=(0, 12))

        tools_canvas = tk.Canvas(
            tools_container,
            bg="darkolivegreen",
            highlightthickness=0,
        )
        tools_scrollbar = tk.Scrollbar(tools_container, orient=tk.VERTICAL, command=tools_canvas.yview)
        tools_canvas.configure(yscrollcommand=tools_scrollbar.set)

        tools_canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        tools_scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

        tools_inner = tk.Frame(tools_canvas, bg="darkolivegreen")
        tools_window_id = tools_canvas.create_window((0, 0), window=tools_inner, anchor="nw")

        def _sync_tools_scrollregion(event=None) -> None:
            tools_canvas.configure(scrollregion=tools_canvas.bbox("all"))
            tools_canvas.itemconfig(tools_window_id, width=tools_canvas.winfo_width())

        def _tools_mousewheel(event) -> None:
            tools_canvas.yview_scroll(int(-1 * (event.delta / 120)), "units")

        tools_inner.bind("<Configure>", _sync_tools_scrollregion)
        tools_canvas.bind("<Configure>", _sync_tools_scrollregion)
        tools_canvas.bind("<MouseWheel>", _tools_mousewheel)
        tools_inner.bind("<MouseWheel>", _tools_mousewheel)

        tools = tools_inner

        tk.Label(tools, text="Aktualny kolor", bg="darkolivegreen", fg="white", font=("Arial", 10, "bold")).pack(anchor="w")
        current_color_preview = tk.Label(tools, bg=state["current_color"], width=10, height=2, relief=tk.SUNKEN, bd=2)
        current_color_preview.pack(pady=(2, 8), fill=tk.X)

        tk.Button(tools, text="Wybierz kolor…", command=pick_color_dialog, bg="saddlebrown", fg="white").pack(fill=tk.X, pady=2)

        palette_frame = tk.LabelFrame(tools, text="Paleta", bg="darkolivegreen", fg="white")
        palette_frame.pack(fill=tk.X, pady=(8, 4))

        default_palette = [
            "#1f3b17", "#274a1c", "#315a22", "#3c6b28",
            "#48802f", "#579637", "#69ac41", "#7ccf4d",
            "#2b1a10", "#3a2313", "#4a2e17", "#5b3a1d",
            "#6e4724", "#82552c", "#986236", "#b37445",
            "#c1864f", "#d39a56", "#e5af5e", "#f3c56a",
            "#152f49", "#1f4261", "#29567a", "#336b93",
            "#4181ac", "#4f99c5", "#5fb1df", "#72c9f6",
            "#2c2c2c", "#393939", "#4b4b4b", "#5e5e5e",
            "#757575", "#909090", "#b0b0b0", "#d0d0d0",
            "#7f301f", "#9b3e26", "#ba4d2e", "#da5e37",
            "#f27440", "#f58d4f", "#f7a75f", "#f9c27b",
            "#a4d87a", "#c0e99b", "#e8f2ff", "#fefefe",
        ]
        palette_columns = 8
        for col in range(palette_columns):
            palette_frame.grid_columnconfigure(col, weight=1)

        for idx, pal_color in enumerate(default_palette):
            btn = tk.Button(
                palette_frame,
                bg=pal_color,
                width=3,
                command=lambda c=pal_color: set_current_color(c)
            )
            btn.grid(row=idx // palette_columns, column=idx % palette_columns, padx=2, pady=2, sticky="nsew")

        transparent_row = (len(default_palette) + (palette_columns - 1)) // palette_columns
        transparent_btn = tk.Button(
            palette_frame,
            text="Przezroczysty",
            command=lambda: set_current_color(None),
            bg="#222222",
            fg="white"
        )
        transparent_btn.grid(row=transparent_row, column=0, columnspan=palette_columns, padx=2, pady=(4, 2), sticky="nsew")

        eraser_btn = tk.Button(tools, text="Gumka", command=toggle_eraser, bg="#444", fg="white")
        eraser_btn.pack(fill=tk.X, pady=(8, 2))

        brush_frame = tk.LabelFrame(tools, text="Pędzel", bg="darkolivegreen", fg="white")
        brush_frame.pack(fill=tk.X, pady=(6, 4))
        brush_radius_value_label = tk.Label(
            brush_frame,
            text=brush_label_for_radius(state["brush_radius"]),
            bg="darkolivegreen",
            fg="#d4f2bf",
            anchor="w"
        )
        brush_radius_value_label.pack(fill=tk.X, padx=4, pady=(2, 0))
        brush_scale = tk.Scale(
            brush_frame,
            from_=BRUSH_RADIUS_MIN,
            to=BRUSH_RADIUS_MAX,
            orient=tk.HORIZONTAL,
            resolution=1,
            variable=brush_radius_var,
            command=on_brush_radius_change,
            length=200,
            bg="darkolivegreen",
            highlightthickness=0,
            troughcolor="#555555"
        )
        brush_scale.pack(fill=tk.X, padx=4, pady=(2, 4))
        on_brush_radius_change(str(state["brush_radius"]))

        tk.Button(
            tools,
            text="Biblioteka presetów…",
            command=open_preset_library,
            bg="saddlebrown",
            fg="white"
        ).pack(fill=tk.X, pady=(10, 4))

        stamp_status_label = tk.Label(tools, text="Preset: brak", bg="darkolivegreen", fg="#d4f2bf", anchor="w", wraplength=220, justify="left")
        stamp_status_label.pack(fill=tk.X, padx=2, pady=(0, 6))

        edge_frame = tk.LabelFrame(tools, text="Pas styku", bg="darkolivegreen", fg="white")
        edge_frame.pack(fill=tk.X, pady=(12, 6))
        tk.Label(
            edge_frame,
            text="Wybierz krawędź, aby malować styki dwóch heksów lub wygładzać je między heksami.",
            bg="darkolivegreen",
            fg="#d4f2bf",
            wraplength=200,
            justify="left"
        ).pack(fill=tk.X, padx=4, pady=(2, 4))

        band_controls = tk.Frame(edge_frame, bg="darkolivegreen")
        band_controls.pack(fill=tk.X, padx=4, pady=(0, 6))
        edge_band_width_value_label = tk.Label(
            band_controls,
            text=f"Szerokość: {state['edge_band_cells']} komórek",
            bg="darkolivegreen",
            fg="#d4f2bf",
            anchor="w"
        )
        edge_band_width_value_label.pack(fill=tk.X, pady=(0, 2))
        edge_band_scale = tk.Scale(
            band_controls,
            from_=EDGE_BAND_CELLS_MIN,
            to=EDGE_BAND_CELLS_MAX,
            orient=tk.HORIZONTAL,
            resolution=1,
            variable=edge_band_width_var,
            command=on_edge_band_width_change,
            length=200,
            bg="darkolivegreen",
            highlightthickness=0,
            troughcolor="#555555"
        )
        edge_band_scale.pack(fill=tk.X)

        edges_list_frame = tk.Frame(edge_frame, bg="darkolivegreen")
        edges_list_frame.pack(fill=tk.X, padx=4, pady=(4, 4))
        for edge_entry in edge_definitions:
            edge_info = edge_mode_data[edge_entry["key"]]
            label_text = f"{edge_entry['label']} → {edge_info['neighbor_id']}"
            btn = tk.Radiobutton(
                edges_list_frame,
                text=label_text,
                variable=selected_edge_var,
                value=edge_entry["key"],
                command=lambda key=edge_entry["key"]: enter_edge_mode(key),
                bg="darkolivegreen",
                fg="white",
                selectcolor="darkolivegreen",
                anchor="w"
            )
            if not edge_info.get("enabled"):
                btn.config(state=tk.DISABLED, fg="#555555")
            btn.pack(fill=tk.X, pady=1)
            edge_button_widgets[edge_entry["key"]] = btn

        blend_frame = tk.LabelFrame(edge_frame, text="Wygładzanie", bg="darkolivegreen", fg="white")
        blend_frame.pack(fill=tk.X, padx=4, pady=(4, 6))
        edge_blend_strength_value_label = tk.Label(
            blend_frame,
            text=f"Moc: {int(state['edge_blend_strength'])}%",
            bg="darkolivegreen",
            fg="#d4f2bf",
            anchor="w"
        )
        edge_blend_strength_value_label.pack(fill=tk.X, pady=(2, 0))
        blend_strength_scale = tk.Scale(
            blend_frame,
            from_=0,
            to=100,
            orient=tk.HORIZONTAL,
            resolution=1,
            variable=edge_blend_strength_var,
            command=on_edge_blend_strength_change,
            length=200,
            bg="darkolivegreen",
            highlightthickness=0,
            troughcolor="#555555"
        )
        blend_strength_scale.pack(fill=tk.X, pady=(0, 4))

        edge_bleed_depth_value_label = tk.Label(
            blend_frame,
            text=bleed_depth_label_for_value(state["edge_bleed_depth"]),
            bg="darkolivegreen",
            fg="#d4f2bf",
            anchor="w"
        )
        edge_bleed_depth_value_label.pack(fill=tk.X, pady=(2, 0))
        edge_bleed_depth_scale = tk.Scale(
            blend_frame,
            from_=0,
            to=state["edge_band_cells"],
            orient=tk.HORIZONTAL,
            resolution=1,
            variable=edge_bleed_depth_var,
            command=on_edge_bleed_depth_change,
            length=200,
            bg="darkolivegreen",
            highlightthickness=0,
            troughcolor="#555555"
        )
        edge_bleed_depth_scale.pack(fill=tk.X, pady=(0, 4))

        tk.Label(
            blend_frame,
            text="Profil wygładzania",
            bg="darkolivegreen",
            fg="#d4f2bf",
            anchor="w"
        ).pack(fill=tk.X, pady=(2, 0))
        blend_profile_combo = ttk.Combobox(
            blend_frame,
            textvariable=edge_blend_profile_display_var,
            values=[meta["label"] for meta in EDGE_BLEND_PROFILES.values()],
            state="readonly"
        )
        blend_profile_combo.pack(fill=tk.X, pady=(0, 4))
        try:
            current_index = [meta["label"] for meta in EDGE_BLEND_PROFILES.values()].index(
                edge_blend_profile_display_var.get()
            )
            blend_profile_combo.current(current_index)
        except ValueError:
            default_label = EDGE_BLEND_PROFILES[EDGE_BLEND_PROFILE_DEFAULT]["label"]
            edge_blend_profile_display_var.set(default_label)
            blend_profile_combo.current(0)
            on_edge_blend_profile_change()
        blend_profile_combo.bind("<<ComboboxSelected>>", on_edge_blend_profile_change)

        tk.Button(
            blend_frame,
            text="Wygładź aktywny pas",
            command=blend_active_edge,
            bg="#4c7035",
            fg="white"
        ).pack(fill=tk.X, pady=(2, 4))

        tk.Button(
            edge_frame,
            text="Wyłącz pas styku",
            command=exit_edge_mode,
            bg="#555555",
            fg="white"
        ).pack(fill=tk.X, padx=4, pady=(6, 2))
        edge_status_label = tk.Label(edge_frame, text="Aktywny: brak", bg="darkolivegreen", fg="#d4f2bf", anchor="w", wraplength=200, justify="left")
        edge_status_label.pack(fill=tk.X, padx=4, pady=(0, 2))
        edge_sync_status_label = tk.Label(
            edge_frame,
            text="Podgląd sąsiada: wyłączony",
            bg="darkolivegreen",
            fg="#d4f2bf",
            anchor="w",
            wraplength=200,
            justify="left",
        )
        edge_sync_status_label.pack(fill=tk.X, padx=4, pady=(0, 4))
        refresh_edge_button_states()
        on_edge_bleed_depth_change(str(state["edge_bleed_depth"]))
        on_edge_blend_strength_change(str(state["edge_blend_strength"]))
        on_edge_blend_profile_change()

        # Panel nawigacji między heksami
        hex_nav_frame = tk.LabelFrame(tools, text="Nawigacja", bg="darkolivegreen", fg="white")
        hex_nav_frame.pack(fill=tk.X, pady=(12, 6))
        
        current_hex_label = tk.Label(
            hex_nav_frame,
            text=f"Edytujesz: {state['current_hex_id']}",
            bg="darkolivegreen",
            fg="#ffcc66",
            font=("Arial", 9, "bold"),
            anchor="w"
        )
        current_hex_label.pack(fill=tk.X, padx=4, pady=(4, 2))
        
        tk.Label(
            hex_nav_frame,
            text="Kliknij w podgląd sąsiada, aby przełączyć edycję na ten heks",
            bg="darkolivegreen",
            fg="#d4f2bf",
            wraplength=200,
            justify="left",
            font=("Arial", 8)
        ).pack(fill=tk.X, padx=4, pady=(0, 4))

        def switch_to_hex(target_hex_id: str) -> None:
            nonlocal edge_mode_data, q, r, current_hex_id
            
            if target_hex_id == state.get("current_hex_id"):
                return
            if target_hex_id not in centers:
                return
            
            # Zapisz obecny stan
            current_id = current_hex_id
            finish_edit_action()
            existing_entry = state["neighbor_hex_data"].get(current_id)
            dirty_flag = state.get("history_edit_dirty", False) or (existing_entry.get("dirty") if existing_entry else False)
            state["neighbor_hex_data"][current_id] = {
                "pixels": clone_pixels(state["pixels"]),
                "dirty": dirty_flag,
            }
            cached_snapshot = state["neighbor_hex_data"][current_id]
            debug_cache(f"switch_to_hex {current_id} -> {target_hex_id}: storing snapshot; dirty={dirty_flag}")
            for edge_key, edge_entry in state["edge_neighbors"].items():
                if edge_entry.get("neighbor_id") == current_id:
                    edge_entry["neighbor_pixels"] = clone_pixels(cached_snapshot["pixels"])
                    edge_entry["dirty"] = cached_snapshot.get("dirty", False)
                    debug_cache(
                        f"switch_to_hex {current_id}: mirrored pixels into edge {edge_key}; "
                        f"dirty={edge_entry['dirty']}"
                    )
            state["history_edit_dirty"] = False
            
            # Załaduj dane nowego heksa
            if target_hex_id in state["neighbor_hex_data"]:
                target_data = state["neighbor_hex_data"][target_hex_id]
                state["pixels"] = clone_pixels(target_data["pixels"])
                debug_cache(f"switch_to_hex {current_id} -> {target_hex_id}: loaded pixels from cache")
            else:
                # Wczytaj z bazy
                target_terrain = self.hex_data.get(target_hex_id, {})
                target_texture_rel = target_terrain.get("texture")
                target_pixels = self._load_hex_texture_pixels(target_texture_rel, grid_size)
                if target_pixels is None:
                    target_pixels = blank_pixel_grid()
                state["pixels"] = target_pixels
                debug_cache(
                    f"switch_to_hex {current_id} -> {target_hex_id}: loaded from storage "
                    f"texture_rel={target_texture_rel}"
                )
            
            current_hex_id = target_hex_id
            state["current_hex_id"] = current_hex_id
            state["undo_stack"].clear()
            state["redo_stack"].clear()
            update_history_buttons()
            
            # Zaktualizuj współrzędne centralnego heksa
            q, r = map(int, current_hex_id.split(","))

            # Przebuduj obrysy sąsiadów
            rebuild_neighbor_outlines()
            
            # Przebuduj dane krawędzi dla nowego heksa
            previous_edge_state = state.get("edge_neighbors")
            edge_mode_data = build_edge_mode_data(
                state["edge_band_cells"],
                previous_edge_state,
                state.get("neighbor_hex_data"),
            )
            state["edge_neighbors"] = edge_mode_data
            debug_cache(
                f"switch_to_hex {current_hex_id}: rebuilt edge_mode_data "
                f"with {len(edge_mode_data)} entries"
            )
            
            # Odśwież interfejs
            current_hex_label.config(text=f"Edytujesz: {current_hex_id}")
            if state.get("edge_mode_active"):
                exit_edge_mode()
            state["view_offset"] = (0, 0)
            refresh_edge_button_states()
            draw_grid()
            refresh_edge_preview(refresh_background=True)

        def save_and_close():
            deactivate_asset_mode(update_button=False)
            clear_stamp_mode(update_label=False)
            close_preset_window("preset_detail_window")
            close_preset_window("preset_category_window")
            grid_size_local = state.get("grid_size", grid_size)
            
            # Zapisz główny edytowany heks
            current_hex = state.get("current_hex_id", hex_id)
            texture_rel = self._save_hex_texture(current_hex, state["pixels"], grid_size_local)
            self.hex_data.setdefault(current_hex, {}).update({
                "texture": texture_rel,
                "texture_grid": grid_size_local,
            })
            textures_to_drop = {texture_rel}
            
            # Zapisz dane sąsiednich heksów, jeśli były edytowane
            for neighbor_id, neighbor_data in state.get("neighbor_hex_data", {}).items():
                neighbor_pixels = neighbor_data.get("pixels")
                if neighbor_pixels is not None and neighbor_data.get("dirty", False):
                    neighbor_texture_rel = self._save_hex_texture(neighbor_id, neighbor_pixels, grid_size_local)
                    neighbor_record = self.hex_data.get(neighbor_id)
                    if neighbor_record is None:
                        neighbor_record = {
                            "terrain_key": "teren_płaski",
                            "move_mod": 0,
                            "defense_mod": 0,
                        }
                        self.hex_data[neighbor_id] = neighbor_record
                    neighbor_record["texture"] = neighbor_texture_rel
                    neighbor_record["texture_grid"] = grid_size_local
                    textures_to_drop.add(neighbor_texture_rel)
            
            neighbor_updates: list[str] = []
            for edge_entry in state["edge_neighbors"].values():
                if not edge_entry.get("enabled") or not edge_entry.get("dirty"):
                    continue
                neighbor_pixels = edge_entry.get("neighbor_pixels")
                if neighbor_pixels is None:
                    continue
                neighbor_id = edge_entry["neighbor_id"]
                neighbor_texture_rel = self._save_hex_texture(neighbor_id, neighbor_pixels, grid_size_local)
                neighbor_record = self.hex_data.get(neighbor_id)
                if neighbor_record is None:
                    neighbor_record = {
                        "terrain_key": "teren_płaski",
                        "move_mod": 0,
                        "defense_mod": 0,
                    }
                    self.hex_data[neighbor_id] = neighbor_record
                neighbor_record["texture"] = neighbor_texture_rel
                neighbor_record["texture_grid"] = grid_size_local
                edge_entry["neighbor_texture_rel"] = neighbor_texture_rel
                edge_entry["dirty"] = False
                textures_to_drop.add(neighbor_texture_rel)
                neighbor_updates.append(neighbor_id)
                if getattr(self, "selected_hex", None) == neighbor_id:
                    self.update_hex_info_display(neighbor_id)
            if textures_to_drop:
                self.hex_texture_cache = {k: v for k, v in self.hex_texture_cache.items() if k[0] not in textures_to_drop}
            if neighbor_updates:
                print(f"Zapisano pas styku dla sąsiadów: {', '.join(neighbor_updates)}")
            editor.grab_release()
            editor.destroy()
            self._texture_editor_window = None
            self.update_hex_info_display(current_hex)
            self.draw_grid()
            self.auto_save_and_export("zapisano teksturę heksa")

        def close_editor():
            deactivate_asset_mode(update_button=False)
            clear_stamp_mode(update_label=False)
            close_preset_window("preset_detail_window")
            close_preset_window("preset_category_window")
            editor.grab_release()
            editor.destroy()
            self._texture_editor_window = None

        undo_btn = tk.Button(toolbar, text="Cofnij (Ctrl+Z)", command=undo_action, bg="saddlebrown", fg="white", width=14, state=tk.DISABLED)
        undo_btn.pack(side=tk.LEFT, padx=4)
        redo_btn = tk.Button(toolbar, text="Ponów (Ctrl+Y)", command=redo_action, bg="saddlebrown", fg="white", width=14, state=tk.DISABLED)
        redo_btn.pack(side=tk.LEFT, padx=4)
        tk.Button(toolbar, text="Zapisz", command=save_and_close, bg="forestgreen", fg="white", width=12).pack(side=tk.LEFT, padx=4)
        tk.Button(toolbar, text="Anuluj", command=close_editor, bg="saddlebrown", fg="white", width=12).pack(side=tk.LEFT, padx=4)
        update_history_buttons()

        editor.bind("<Control-z>", undo_action)
        editor.bind("<Control-Z>", undo_action)
        editor.bind("<Control-y>", redo_action)
        editor.bind("<Control-Y>", redo_action)

        draw_grid()

        texture_rel = terrain.get("texture")
        if texture_rel:
            try:
                img_path = fix_image_path(texture_rel)
                if img_path.exists():
                    tk.Label(tools, text=f"Plik: {to_rel(str(img_path))}", bg="darkolivegreen", fg="white", wraplength=180, justify="left").pack(fill=tk.X, pady=(10, 0))
            except Exception:
                pass

        editor.protocol("WM_DELETE_WINDOW", close_editor)

    def _clear_flat_texture_from_record(self, record: dict) -> None:
        record.pop("texture", None)
        record.pop("texture_grid", None)
        record.pop("flat_texture_preset", None)

    def _apply_flat_texture_preset_to_record(self, record: dict, preset_key: str, grid_size: int | None = None) -> None:
        preset_meta = FLAT_TERRAIN_PRESET_LOOKUP.get(preset_key)
        if not preset_meta or preset_meta.get("type") == "clear":
            self._clear_flat_texture_from_record(record)
            return
        grid = grid_size or DEFAULT_HEX_TEXTURE_GRID_SIZE
        texture_rel = self._ensure_flat_texture_asset(preset_key, grid)
        record["texture"] = texture_rel
        record["texture_grid"] = grid
        record["flat_texture_preset"] = preset_key

    def _ensure_flat_texture_asset(self, preset_key: str, grid_size: int) -> str:
        output_name = f"flat_{preset_key}_{grid_size}.png"
        output_path = HEX_TEXTURE_DIR / output_name
        if not output_path.exists():
            pixels = self._generate_flat_texture_pixels(preset_key, grid_size)
            img = self._pixel_grid_to_image(pixels)
            export_size = HEX_TEXTURE_EXPORT_SIZES.get(grid_size, grid_size)
            export_img = img.resize((export_size, export_size), Image.NEAREST)
            output_path.parent.mkdir(parents=True, exist_ok=True)
            export_img.save(output_path)
        return to_rel(str(output_path))

    def _pixel_grid_to_image(self, pixel_grid: list[list[str | None]]) -> Image.Image:
        size = len(pixel_grid)
        img = Image.new("RGBA", (size, size), (0, 0, 0, 0))
        for row in range(size):
            for col in range(size):
                color = pixel_grid[row][col]
                if color:
                    r, g, b = hex_to_rgb(color)
                    img.putpixel((col, row), (r, g, b, 255))
        return img

    def _generate_flat_texture_pixels(self, preset_key: str, grid_size: int) -> list[list[str | None]]:
        preset_meta = FLAT_TERRAIN_PRESET_LOOKUP.get(preset_key)
        if not preset_meta or preset_meta.get("type") != "builtin":
            raise ValueError(f"Brak wzoru typu 'builtin' dla klucza: {preset_key}")

        mask = self._precompute_hex_mask(grid_size)
        pixels: list[list[str | None]] = [[None for _ in range(grid_size)] for _ in range(grid_size)]
        rng = random.Random(f"{preset_key}-{grid_size}")

        base_rgb = hex_to_rgb(preset_meta["base_color"])
        noise = int(preset_meta.get("noise", 0))
        accent_color = preset_meta.get("accent_color")
        accent_chance = float(preset_meta.get("accent_chance", 0.0))
        highlight_color = preset_meta.get("highlight_color")
        highlight_chance = float(preset_meta.get("highlight_chance", 0.0))
        pattern = preset_meta.get("pattern", "noise")

        secondary_color = preset_meta.get("secondary_color")
        secondary_rgb = hex_to_rgb(secondary_color) if secondary_color else base_rgb

        if pattern == "noise":
            for row in range(grid_size):
                for col in range(grid_size):
                    if not mask[row][col]:
                        continue
                    delta = (
                        rng.randint(-noise, noise) if noise else 0,
                        rng.randint(-noise, noise) if noise else 0,
                        rng.randint(-noise, noise) if noise else 0,
                    )
                    pixel_rgb = adjust_rgb(base_rgb, delta)
                    if accent_color and rng.random() < accent_chance:
                        pixel_rgb = hex_to_rgb(accent_color)
                    elif highlight_color and rng.random() < highlight_chance:
                        pixel_rgb = hex_to_rgb(highlight_color)
                    pixels[row][col] = rgb_to_hex(pixel_rgb)

        elif pattern == "stripes":
            band_width = max(2, int(preset_meta.get("band_width", 6)))
            band_strength = float(preset_meta.get("band_strength", 0.5))
            for row in range(grid_size):
                for col in range(grid_size):
                    if not mask[row][col]:
                        continue
                    delta = (
                        rng.randint(-noise, noise) if noise else 0,
                        rng.randint(-noise, noise) if noise else 0,
                        rng.randint(-noise, noise) if noise else 0,
                    )
                    pixel_rgb = adjust_rgb(base_rgb, delta)
                    stripe_index = ((row + int(col * 0.4)) // band_width) % 2
                    if stripe_index == 1 and secondary_color:
                        pixel_rgb = blend_rgb(pixel_rgb, secondary_rgb, band_strength)
                    if accent_color and rng.random() < accent_chance:
                        pixel_rgb = hex_to_rgb(accent_color)
                    pixels[row][col] = rgb_to_hex(pixel_rgb)

        elif pattern == "patches":
            patch_size = max(3, int(preset_meta.get("patch_size", 6)))
            patch_jitter = float(preset_meta.get("patch_jitter", 0.3))
            patch_cache: dict[tuple[int, int], float] = {}
            for row in range(grid_size):
                for col in range(grid_size):
                    if not mask[row][col]:
                        continue
                    delta = (
                        rng.randint(-noise, noise) if noise else 0,
                        rng.randint(-noise, noise) if noise else 0,
                        rng.randint(-noise, noise) if noise else 0,
                    )
                    pixel_rgb = adjust_rgb(base_rgb, delta)
                    patch_key = (row // patch_size, col // patch_size)
                    base_value = patch_cache.setdefault(patch_key, rng.random())
                    threshold = 0.6 + rng.uniform(-patch_jitter, patch_jitter)
                    if secondary_color and base_value > threshold:
                        pixel_rgb = secondary_rgb
                    if accent_color and rng.random() < accent_chance:
                        pixel_rgb = hex_to_rgb(accent_color)
                    pixels[row][col] = rgb_to_hex(pixel_rgb)

        else:
            # domyślnie fallback do podstawowego szumu
            for row in range(grid_size):
                for col in range(grid_size):
                    if not mask[row][col]:
                        continue
                    delta = (
                        rng.randint(-noise, noise) if noise else 0,
                        rng.randint(-noise, noise) if noise else 0,
                        rng.randint(-noise, noise) if noise else 0,
                    )
                    pixel_rgb = adjust_rgb(base_rgb, delta)
                    pixels[row][col] = rgb_to_hex(pixel_rgb)

        return pixels

    def _build_clear_texture_preview(self) -> Image.Image:
        size = DEFAULT_HEX_TEXTURE_GRID_SIZE
        mask = self._precompute_hex_mask(size)
        base_color = hex_to_rgb(TERRAIN_PREVIEW_COLORS.get("teren_płaski", "#91a86b"))
        img = Image.new("RGBA", (size, size), (0, 0, 0, 0))
        for row in range(size):
            for col in range(size):
                if not mask[row][col]:
                    continue
                img.putpixel((col, row), (*base_color, 110))
        draw = ImageDraw.Draw(img)
        draw.line((0, 0, size, size), fill=(255, 255, 255, 180), width=4)
        draw.line((0, size, size, 0), fill=(255, 255, 255, 180), width=4)
        return img

    def _get_flat_texture_preview(self, preset_key: str) -> ImageTk.PhotoImage:
        cached = self.flat_texture_preview_cache.get(preset_key)
        if cached is not None:
            return cached

        if preset_key == "none":
            img = self._build_clear_texture_preview()
        else:
            pixels = self._generate_flat_texture_pixels(preset_key, DEFAULT_HEX_TEXTURE_GRID_SIZE)
            img = self._pixel_grid_to_image(pixels)

        preview_size = 104
        preview_img = img.resize((preview_size, preview_size), Image.NEAREST)
        photo = ImageTk.PhotoImage(preview_img)
        self.flat_texture_preview_cache[preset_key] = photo
        return photo

    def _load_hex_texture_pixels(self, texture_rel: str | None, grid_size: int) -> list[list[str | None]]:
        mask = self._precompute_hex_mask(grid_size)
        pixels: list[list[str | None]] = [[None for _ in range(grid_size)] for _ in range(grid_size)]
        if not texture_rel:
            return pixels
        img_path = fix_image_path(texture_rel)
        if not img_path.exists():
            return pixels
        try:
            img = Image.open(img_path).convert("RGBA")
            if img.width != grid_size or img.height != grid_size:
                img = img.resize((grid_size, grid_size), Image.NEAREST)
            for row in range(grid_size):
                for col in range(grid_size):
                    if not mask[row][col]:
                        continue
                    r, g, b, a = img.getpixel((col, row))
                    if a == 0:
                        pixels[row][col] = None
                    else:
                        pixels[row][col] = f"#{r:02x}{g:02x}{b:02x}"
        except Exception as exc:
            print(f"Nie udało się wczytać tekstury heksa: {exc}")
        return pixels

    def _save_hex_texture(self, hex_id: str, pixels: list[list[str | None]], grid_size: int) -> str:
        mask = self._precompute_hex_mask(grid_size)
        base_img = Image.new("RGBA", (grid_size, grid_size), (0, 0, 0, 0))
        for row in range(grid_size):
            for col in range(grid_size):
                if not mask[row][col]:
                    continue
                color = pixels[row][col]
                if color:
                    r = int(color[1:3], 16)
                    g = int(color[3:5], 16)
                    b = int(color[5:7], 16)
                    base_img.putpixel((col, row), (r, g, b, 255))
        export_size = HEX_TEXTURE_EXPORT_SIZES.get(grid_size, grid_size)
        export_img = base_img.resize((export_size, export_size), Image.NEAREST)
        filename = f"hex_{hex_id.replace(',', '_')}.png"
        output_path = HEX_TEXTURE_DIR / filename
        export_img.save(output_path)
        rel_path = to_rel(str(output_path))
        print(f"Zapisano teksturę heksa do {output_path}")
        return rel_path

    def _get_hex_texture_image(self, texture_rel: str) -> ImageTk.PhotoImage | None:
        cache_key = (texture_rel, self.hex_size)
        if cache_key in self.hex_texture_cache:
            return self.hex_texture_cache[cache_key]
        img_path = fix_image_path(texture_rel)
        if not img_path.exists():
            return None
        try:
            img = Image.open(img_path).convert("RGBA")
            target_size = (int(self.hex_size * 2), int(self.hex_size * 2))
            img = img.resize(target_size, Image.NEAREST)
            photo = ImageTk.PhotoImage(img)
            self.hex_texture_cache[cache_key] = photo
            return photo
        except Exception as exc:
            print(f"Nie udało się wczytać obrazu tekstury: {exc}")
            return None

    def _precompute_hex_mask(self, grid_size: int) -> list[list[bool]]:
        cache = getattr(self, "_hex_texture_masks", None)
        if cache and grid_size in cache:
            return cache[grid_size]

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

        if cache is None:
            self._hex_texture_masks = {}
        if not hasattr(self, "_hex_texture_vertices"):
            self._hex_texture_vertices = {}
        self._hex_texture_masks[grid_size] = mask
        self._hex_texture_vertices[grid_size] = vertices
        return mask

    def update_hex_info_display(self, hex_id):
        """Aktualizuje wyświetlane informacje o heksie"""
        terrain = self.hex_data.get(hex_id, self.hex_defaults)
        
        # Podstawowe info
        self.hex_info_label.config(text=f"Heks: {hex_id}")
        
        # Teren
        terrain_key = terrain.get('terrain_key', 'teren_płaski')
        move_mod = terrain.get('move_mod', 0)
        defense_mod = terrain.get('defense_mod', 0)
        self.terrain_info_label.config(text=f"Teren: {terrain_key} (M:{move_mod} D:{defense_mod})")
        
        # Żeton
        token = terrain.get("token")
        if token:
            token_info = f"Żeton: {token.get('unit', 'nieznany')}"
        else:
            token_info = "Żeton: brak"
        self.token_info_label.config(text=token_info)

        texture_rel = terrain.get("texture")
        grid_info = terrain.get("texture_grid") or DEFAULT_HEX_TEXTURE_GRID_SIZE
        try:
            grid_info = int(grid_info)
        except (TypeError, ValueError):
            grid_info = DEFAULT_HEX_TEXTURE_GRID_SIZE
        if texture_rel:
            self.texture_info_label.config(text=f"Tekstura: {texture_rel} ({grid_info}x{grid_info})")
        else:
            self.texture_info_label.config(text=f"Tekstura: domyślna ({grid_info}x{grid_info})")
        self.edit_texture_button.config(state=tk.NORMAL)

        preset_key = terrain.get("flat_texture_preset")
        if hasattr(self, "flat_texture_info_label"):
            if preset_key:
                preset_meta = FLAT_TERRAIN_PRESET_LOOKUP.get(preset_key)
                preset_label = preset_meta.get("name", preset_key) if preset_meta else preset_key
                self.flat_texture_info_label.config(text=f"Wzór płaski: {preset_label}")
            else:
                self.flat_texture_info_label.config(text="Wzór płaski: brak")
        
        # Sprawdź czy to Key Point
        key_point_info = ""
        if hex_id in self.key_points:
            key_data = self.key_points[hex_id]
            key_type = key_data.get('type', 'nieznany')
            key_value = key_data.get('value', 0)
            key_point_info = f"🔑 Key Point: {key_type} (wartość: {key_value})"
        
        # Sprawdź czy to Spawn Point
        spawn_point_info = ""
        for nation, spawn_list in self.spawn_points.items():
            if hex_id in spawn_list:
                spawn_point_info = f"🚀 Spawn Point: {nation}"
                break
        
        # Aktualizuj etykiety - dodaj nowe jeśli nie istnieją
        if not hasattr(self, 'key_point_info_label'):
            # Dodaj nowe etykiety do basic_info_frame
            basic_info_frame = self.hex_info_label.master
            self.key_point_info_label = tk.Label(basic_info_frame, text="", bg="darkolivegreen", fg="yellow", font=("Arial", 9))
            self.key_point_info_label.pack(anchor="w", pady=1)
            
            self.spawn_point_info_label = tk.Label(basic_info_frame, text="", bg="darkolivegreen", fg="lightblue", font=("Arial", 9))
            self.spawn_point_info_label.pack(anchor="w", pady=1)
        
        # Zaktualizuj informacje o key point i spawn point
        self.key_point_info_label.config(text=key_point_info)
        self.spawn_point_info_label.config(text=spawn_point_info)
        
        # Zaktualizuj przyciski modyfikacji drogi
        if hasattr(self, "_update_road_modify_buttons"):
            self._update_road_modify_buttons()

    def auto_save_and_export(self, reason):
        """Automatyczny zapis danych mapy i eksport żetonów z debounce"""
        # Sprawdź czy auto-save jest włączony
        if not self.auto_save_enabled:
            return
            
        # Natychmiastowy zapis map_data.json
        try:
            self.save_data()
        except Exception as e:
            print(f"Błąd zapisu danych: {e}")
            
        # Debounce eksportu start_tokens.json
        if self._auto_save_after:
            self.root.after_cancel(self._auto_save_after)
        self._auto_save_after = self.root.after(500, self.export_start_tokens_delayed)
        
        print(f"Auto-save: {reason}")

    def export_start_tokens_delayed(self):
        """Opóźniony eksport start_tokens.json"""
        try:
            count = self.export_start_tokens(show_message=False)
            print(f"Auto-export start_tokens.json ({count} żetonów)")
        except Exception as e:
            print(f"Błąd eksportu żetonów: {e}")

    def highlight_hex(self, hex_id):
        'Oznacza wybrany heks żółtą obwódką.'
        self.canvas.delete("highlight")
        if hex_id in self.hex_centers:
            cx, cy = self.hex_centers[hex_id]
            s = self.hex_size
            self.canvas.create_oval(cx - s, cy - s, cx + s, cy + s,
                                    outline="yellow", width=3, tags="highlight")

    # --- STATUS / AUTO SAVE ---
    def set_status(self, msg: str):
        if hasattr(self, 'status_label'):
            self.status_label.config(text=msg)
        # opcjonalnie print
        # print('[STATUS]', msg)

    def auto_save(self, reason: str):
        if not getattr(self, 'auto_save_enabled', True):
            return
        # debounce
        if hasattr(self, '_auto_save_after') and self._auto_save_after:
            self.root.after_cancel(self._auto_save_after)
        self._auto_save_after = self.root.after(500, lambda: self._perform_auto_save(reason))

    def _perform_auto_save(self, reason: str):
        try:
            self.save_data()
            self.set_status(f'Auto-save: {reason}')
        except Exception as e:
            self.set_status(f'Auto-save błąd: {e}')

    def on_canvas_hover(self, event):
        """Obsługuje hover nad canvasem - ghost preview i zoom żetonów"""
        x = self.canvas.canvasx(event.x)
        y = self.canvas.canvasy(event.y)
        hex_id = self.get_clicked_hex(x, y)
        self.canvas.delete("hover_zoom")
        
        if not hex_id:
            if hasattr(self, '_hover_zoom_images'):
                self._hover_zoom_images.clear()
            return
            
        terrain = self.hex_data.get(hex_id, self.hex_defaults)
        token_existing = terrain.get('token')
        
        # 1. Ghost preview dla nowego systemu żetonów
        if self.selected_token and not token_existing and hex_id in self.hex_centers:
            cx, cy = self.hex_centers[hex_id]
            s_zoom = int(self.hex_size * 1.2)
            
            # Sprawdź czy można postawić żeton (unikalność)
            can_place = True
            color = "#00ffaa"  # zielony
            
            if self.uniqueness_mode:
                for terrain_check in self.hex_data.values():
                    existing_token = terrain_check.get("token")
                    if existing_token and existing_token.get("unit") == self.selected_token["id"]:
                        can_place = False
                        color = "#ff0000"  # czerwony
                        break
            
            # Rysuj obwódkę
            points = get_hex_vertices(cx, cy, s_zoom)
            self.canvas.create_polygon(points, outline=color, width=2, dash=(4,2), fill="", tags="hover_zoom")
            
            # Rysuj ghost image
            img_path = fix_image_path(self.selected_token["image"])
            
            if img_path.exists():
                key_cache = (img_path, s_zoom)
                tk_img = self._ghost_cache.get(key_cache)
                if tk_img is None:
                    try:
                        base = Image.open(img_path).convert('RGBA').resize((s_zoom, s_zoom))
                        r,g,b,a = base.split()
                        # Przezroczystość w zależności od możliwości postawienia
                        alpha = 0.55 if can_place else 0.3
                        a = a.point(lambda v: int(v*alpha))
                        base = Image.merge('RGBA', (r,g,b,a))
                        tk_img = ImageTk.PhotoImage(base)
                        self._ghost_cache[key_cache] = tk_img
                    except Exception:
                        tk_img = None
                        
                if tk_img:
                    self.canvas.create_image(cx, cy, image=tk_img, tags='hover_zoom')
                    if not hasattr(self, '_hover_zoom_images'):
                        self._hover_zoom_images = []
                    self._hover_zoom_images.append(tk_img)
                    
            # Czerwony X jeśli nie można postawić
            if not can_place:
                self.canvas.create_text(cx, cy, text="✗", fill="red", font=("Arial", 20, "bold"), tags="hover_zoom")
            
            return
            
        # 2. Kompatybilność ze starym systemem
        if hasattr(self, 'selected_token_for_deployment') and self.selected_token_for_deployment and not token_existing and hex_id in self.hex_centers:
            cx, cy = self.hex_centers[hex_id]
            s_zoom = int(self.hex_size * 1.2)
            points = get_hex_vertices(cx, cy, s_zoom)
            self.canvas.create_polygon(points, outline="#00ffaa", width=2, dash=(4,2), fill="", tags="hover_zoom")
            img_path = None
            sel = self.selected_token_for_deployment
            if sel:
                if sel.get('image_path'):
                    img_path = Path(sel['image_path'])
                elif sel.get('image'):
                    img_path = fix_image_path(sel['image'])
            if img_path and img_path.exists():
                key_cache = (img_path, s_zoom)
                tk_img = self._ghost_cache.get(key_cache)
                if tk_img is None:
                    try:
                        base = Image.open(img_path).convert('RGBA').resize((s_zoom, s_zoom))
                        r,g,b,a = base.split()
                        a = a.point(lambda v: int(v*0.55))
                        base = Image.merge('RGBA', (r,g,b,a))
                        tk_img = ImageTk.PhotoImage(base)
                        self._ghost_cache[key_cache] = tk_img
                    except Exception:
                        tk_img = None
                if tk_img:
                    self.canvas.create_image(cx, cy, image=tk_img, tags='hover_zoom')
                    if not hasattr(self, '_hover_zoom_images'):
                        self._hover_zoom_images = []
                    self._hover_zoom_images.append(tk_img)
            return
            
        # 3. Powiększenie istniejącego żetonu
        if token_existing and 'image' in token_existing and hex_id in self.hex_centers:
            cx, cy = self.hex_centers[hex_id]
            move_mod = terrain.get('move_mod',0)
            defense_mod = terrain.get('defense_mod',0)
            s_zoom = int(self.hex_size * 1.5)
            points = get_hex_vertices(cx, cy, s_zoom)
            self.canvas.create_polygon(points, outline='orange', fill='#ffffcc', width=3, tags='hover_zoom')
            label = f"M:{move_mod} D:{defense_mod}"
            if token_existing.get('unit'):
                label += f"\n{token_existing['unit']}"
            self.canvas.create_text(cx, cy, text=label, fill='black', font=('Arial', 14, 'bold'), tags='hover_zoom')
            img_path = fix_image_path(token_existing['image'])
            
            if img_path.exists():
                try:
                    img = Image.open(img_path).resize((s_zoom, s_zoom))
                    tk_img = ImageTk.PhotoImage(img)
                    self.canvas.create_image(cx, cy, image=tk_img, tags='hover_zoom')
                    if not hasattr(self, '_hover_zoom_images'):
                        self._hover_zoom_images = []
                    self._hover_zoom_images.append(tk_img)
                except Exception:
                    pass

    def save_data(self):
        'Zapisuje aktualne dane (teren, kluczowe punkty, spawn_points) do pliku JSON.'
        # --- USUWANIE MARTWYCH ŻETONÓW ---
        for hex_id, terrain in list(self.hex_data.items()):
            token = terrain.get("token")
            if token and "image" in token:
                img_path = fix_image_path(token["image"])
                if not img_path.exists():
                    terrain.pop("token", None)
        # --- KONIEC USUWANIA ---
        # ZAPISZ CAŁĄ SIATKĘ HEKSÓW (nie tylko zmienione)
        map_data = {
            "meta": {
                "hex_size": self.hex_size,
                "cols": self.config.get("grid_cols"),
                "rows": self.config.get("grid_rows"),
                "coord_system": "axial",
                "orientation": "pointy",
                "background": self._serialize_background_info()
            },
            "terrain": self.hex_data,
            "key_points": self.key_points,
            "spawn_points": self.spawn_points
        }
        self.current_working_file = self.get_working_data_path()
        print(f"Zapisywanie danych do: {self.current_working_file}")
        with open(self.current_working_file, "w", encoding="utf-8") as f:
            import json
            json.dump(map_data, f, indent=2, ensure_ascii=False)
        # messagebox.showinfo("Zapisano", f"Dane mapy zostały zapisane w:\n{self.current_working_file}\n"
        #                                 f"Liczba kluczowych punktów: {len(self.key_points)}\n"
        #                                 f"Liczba punktów wystawienia: {sum(len(v) for v in self.spawn_points.values())}")

    def load_data(self):
        'Wczytuje dane z pliku roboczego (teren, kluczowe i spawn).'
        self.current_working_file = self.get_working_data_path()
        print(f"Wczytywanie danych z: {self.current_working_file}")
        loaded_data = wczytaj_dane_hex(self.current_working_file)
        if loaded_data:
            meta = loaded_data.get("meta", {})
            if meta:
                self.hex_size = meta.get("hex_size", self.hex_size)
                self.config["grid_cols"] = meta.get("cols", self.config.get("grid_cols"))
                self.config["grid_rows"] = meta.get("rows", self.config.get("grid_rows"))
                self._update_map_info_label()
                self._apply_background_metadata(meta.get("background"))
            else:
                self._apply_background_metadata(None)
            orientation = loaded_data.get("meta", {}).get("orientation", "pointy")
            self.orientation = orientation  # przechowaj w obiekcie, przyda się GUI
            if "meta" not in loaded_data:          # plik starego formatu
                self.hex_data = loaded_data
                self.key_points = {}
                self.spawn_points = {}
            else:
                self.hex_data   = loaded_data.get("terrain", {})
                self.key_points = loaded_data.get("key_points", {})
                self.spawn_points = loaded_data.get("spawn_points", {})
            if self._ensure_city_marker_textures():
                # aktualizuj zapis, aby nowa tekstura była dostępna w pliku
                self.save_data()
            self.hex_tokens = {
                hex_id: terrain["image"]
                for hex_id, terrain in self.hex_data.items()
                if "image" in terrain and os.path.exists(terrain["image"])
            }
            # MIGRACJA starej struktury tokenów
            for hid, hinfo in list(self.hex_data.items()):
                # 1) absolutna ścieżka w korzeniu heksu -> token + rel
                if "image" in hinfo:
                    img = hinfo.pop("image")
                    hinfo["token"] = {"unit": Path(img).stem, "image": to_rel(img)}

                # 2) przenieś png_file do image, jeśli jeszcze nie przeniesione
                if "token" in hinfo and "png_file" in hinfo["token"]:
                    pf = hinfo["token"].pop("png_file")
                    if "image" not in hinfo["token"]:
                        hinfo["token"]["image"] = to_rel(pf)

                # 3) upewnij się, że image jest relatywne
                if "token" in hinfo and "image" in hinfo["token"]:
                    hinfo["token"]["image"] = to_rel(hinfo["token"]["image"])
            # zawsze upewnij się, że tło jest załadowane
            self.load_map_image()

            # i dopiero potem rysuj grid
            self.draw_grid()
            
            # Odśwież paletę żetonów
            self.update_filtered_tokens()
            
            # Nie pokazuj popup przy starcie - tylko loguj do konsoli
            print(f"✅ Wczytano dane mapy z: {self.current_working_file}")
            print(f"📍 Kluczowe punkty: {len(self.key_points)}")
            print(f"🚀 Punkty wystawienia: {sum(len(v) for v in self.spawn_points.values())}")
        else:
            self._apply_background_metadata(None)
            self.load_map_image()
            print("⚠️  Brak danych do wczytania lub plik nie istnieje")
        self._update_map_info_label()

    def clear_variables(self):
        'Kasuje wszystkie niestandardowe ustawienia mapy (reset do płaskiego terenu).'
        answer = messagebox.askyesno("Potwierdzenie", "Czy na pewno chcesz zresetować mapę do domyślnego terenu płaskiego?")
        if answer:
            self.hex_data = {}
            self.key_points = {}
            self.spawn_points = {}
            zapisz_dane_hex({"terrain": {}, "key_points": {}, "spawn_points": {}}, self.current_working_file)
            self.draw_grid()
            messagebox.showinfo("Zresetowano", "Mapa została zresetowana do domyślnego terenu płaskiego.")
        self._update_map_info_label()

    def save_map_and_data(self):
        """Zapisuje dane JSON mapy i eksportuje żetony."""
        try:
            self.save_data()  # Zapisuje dane JSON
            count = self.export_start_tokens(show_message=False)  # Eksportuje żetony
            messagebox.showinfo("Sukces", f"Dane mapy zostały zapisane pomyślnie.\nWyeksportowano {count} żetonów.")
        except Exception as e:
            messagebox.showerror("Błąd", f"Nie udało się zapisać danych mapy: {e}")

    def toggle_auto_save(self):
        """Zmienia stan auto-save"""
        self.auto_save_enabled = self.auto_save_var.get()
        status = "włączony" if self.auto_save_enabled else "wyłączony"
        print(f"Auto-save {status}")

    def open_map_and_data(self):
        """Otwiera mapę i wczytuje dane."""
        try:
            # Domyślna ścieżka do mapy
            map_path = filedialog.askopenfilename(
                initialdir=DEFAULT_MAP_DIR,
                title="Wybierz mapę",
                filetypes=[("Obrazy", "*.jpg *.png *.bmp"), ("Wszystkie pliki", "*.*")]
            )
            if map_path:
                self.map_image_path = map_path
                self.load_map_image()
                self.load_data()
                messagebox.showinfo("Sukces", "Mapa i dane zostały pomyślnie wczytane.")
            else:
                messagebox.showinfo("Anulowano", "Nie wybrano mapy.")
        except Exception as e:
            messagebox.showerror("Błąd", f"Nie udało się otworzyć mapy i danych: {e}")

    def add_key_point_dialog(self):
        'Okno dialogowe do dodawania kluczowego punktu na wybranym heksie.'
        if self.selected_hex is None:
            messagebox.showinfo("Informacja", "Najpierw wybierz heks klikając na niego.")
            return
        dialog = tk.Toplevel(self.root)
        dialog.title("Dodaj kluczowy punkt")
        dialog.geometry("300x150")
        dialog.transient(self.root)
        dialog.grab_set()
        tk.Label(dialog, text="Wybierz typ punktu:", font=("Arial", 10)).pack(pady=10)
        point_types = list(self.available_key_point_types.keys())
        selected_type = tk.StringVar(value=point_types[0])
        tk.OptionMenu(dialog, selected_type, *point_types).pack()
        def save_key_point():
            ptype = selected_type.get()
            value = self.available_key_point_types[ptype]
            self.key_points[self.selected_hex] = {"type": ptype, "value": value}
            self.save_data()
            self.draw_key_point(self.selected_hex, ptype, value)
            messagebox.showinfo("Sukces", f"Dodano kluczowy punkt '{ptype}' o wartości {value} na heksie {self.selected_hex}.")
            dialog.destroy()
        tk.Button(dialog, text="Zapisz", command=save_key_point, bg="green", fg="white").pack(pady=10)
        tk.Button(dialog, text="Anuluj", command=dialog.destroy, bg="red", fg="white").pack(pady=5)
        # po sukcesie dodania key point
        self.auto_save('key point')

    def add_spawn_point_dialog(self):
        'Okno dialogowe do dodawania punktu wystawienia dla nacji.'
        if self.selected_hex is None:
            messagebox.showinfo("Informacja", "Najpierw wybierz heks klikając na niego.")
            return
        dialog = tk.Toplevel(self.root)
        dialog.title("Dodaj punkt wystawienia")
        dialog.geometry("300x150")
        dialog.transient(self.root)
        dialog.grab_set()
        tk.Label(dialog, text="Wybierz nację:", font=("Arial", 10)).pack(pady=10)
        selected_nation = tk.StringVar(value=self.available_nations[0])
        tk.OptionMenu(dialog, selected_nation, *self.available_nations).pack()
        def save_spawn_point():
            nation = selected_nation.get()
            self.spawn_points.setdefault(nation, []).append(self.selected_hex)
            self.save_data()
            self.draw_grid()  # Odśwież rysunek mapy, aby zobaczyć mgiełkę
            messagebox.showinfo("Sukces", f"Dodano punkt wystawienia dla nacji '{nation}' na heksie {self.selected_hex}.")
            dialog.destroy()
        tk.Button(dialog, text="Zapisz", command=save_spawn_point, bg="green", fg="white").pack(pady=10)
        tk.Button(dialog, text="Anuluj", command=dialog.destroy, bg="red", fg="white").pack(pady=5)
        # po sukcesie dodania spawn
        self.auto_save('spawn point')

    def draw_key_point(self, hex_id, point_type, value):
        'Rysuje na canvasie etykietę kluczowego punktu.'
        if hex_id in self.hex_centers:
            cx, cy = self.hex_centers[hex_id]
            self.canvas.create_text(cx, cy, text=f"{point_type}\n({value})", fill="yellow",
                                    font=("Arial", 10, "bold"), tags=f"key_point_{hex_id}")

    def apply_terrain(self, terrain_key):
        'Przypisuje wybrany typ terenu do aktualnie zaznaczonego heksu.'
        if self.selected_hex is None:
            messagebox.showinfo("Informacja", "Najpierw wybierz heks klikając na niego.")
            return
        terrain = TERRAIN_TYPES.get(terrain_key)
        if terrain:
            current_record = self.hex_data.get(self.selected_hex, {})
            updated_record = current_record.copy()
            previous_texture = current_record.get("texture")
            updated_record["terrain_key"] = terrain_key
            updated_record["move_mod"] = terrain["move_mod"]
            updated_record["defense_mod"] = terrain["defense_mod"]

            is_default_flat = (
                terrain_key == "teren_płaski"
                and terrain["move_mod"] == self.hex_defaults.get("move_mod", 0)
                and terrain["defense_mod"] == self.hex_defaults.get("defense_mod", 0)
            )
            extra_keys = {k for k in updated_record.keys() if k not in {"terrain_key", "move_mod", "defense_mod"}}

            if is_default_flat and not extra_keys:
                updated_record = {
                    "terrain_key": terrain_key,
                    "move_mod": terrain["move_mod"],
                    "defense_mod": terrain["defense_mod"]
                }

            if terrain_key == "teren_płaski":
                brush_preset = self.selected_flat_texture_preset
                if brush_preset == "none":
                    self._clear_flat_texture_from_record(updated_record)
                elif brush_preset:
                    self._apply_flat_texture_preset_to_record(updated_record, brush_preset)
                elif "flat_texture_preset" in updated_record and updated_record.get("texture") is None:
                    self._clear_flat_texture_from_record(updated_record)
            elif terrain_key == "miasto":
                self._apply_flat_texture_preset_to_record(updated_record, "city_marker")
            else:
                self._clear_flat_texture_from_record(updated_record)

            self.hex_data[self.selected_hex] = updated_record
            terrain_for_draw = updated_record
            # Zapisz dane i odrysuj heks
            self.save_data()
            new_texture = updated_record.get("texture")
            needs_full_redraw = previous_texture != new_texture
            if needs_full_redraw:
                self.draw_grid()
            else:
                cx, cy = self.hex_centers[self.selected_hex]
                self.draw_hex(self.selected_hex, cx, cy, self.hex_size, terrain_for_draw)
            self.update_hex_info_display(self.selected_hex)
            messagebox.showinfo("Zapisano", f"Dla heksu {self.selected_hex} ustawiono teren: {terrain_key}")
            self.auto_save('malowanie terenu')
        else:
            messagebox.showerror("Błąd", "Niepoprawny rodzaj terenu.")

    def _ensure_city_marker_textures(self) -> bool:
        """Upewnia się, że wszystkie heksy oznaczone jako miasta mają teksturę orientacyjną."""
        changed = False
        for record in self.hex_data.values():
            if record.get("terrain_key") == "miasto":
                texture = record.get("texture")
                preset = record.get("flat_texture_preset")
                if not texture or preset != "city_marker":
                    self._apply_flat_texture_preset_to_record(record, "city_marker")
                    changed = True
        return changed

    def toggle_flat_texture_window(self, event=None):
        if self.flat_texture_window and self.flat_texture_window.winfo_exists():
            self.close_flat_texture_window()
        else:
            self.open_flat_texture_window()
        return "break"

    def open_flat_texture_window(self, event=None):
        if self.flat_texture_window and self.flat_texture_window.winfo_exists():
            try:
                self.flat_texture_window.deiconify()
                self.flat_texture_window.lift()
                self.flat_texture_window.focus_set()
            except Exception:
                pass
            return

        window = tk.Toplevel(self.root)
        window.title("Tekstury terenu płaskiego")
        window.configure(bg="darkolivegreen")
        window.geometry("420x560")
        window.minsize(360, 440)
        window.transient(self.root)

        container = tk.Frame(window, bg="darkolivegreen")
        container.pack(fill=tk.BOTH, expand=True, padx=8, pady=6)

        canvas = tk.Canvas(container, bg="darkolivegreen", highlightthickness=0)
        canvas.configure(width=300)
        canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

        scrollbar = tk.Scrollbar(container, orient=tk.VERTICAL, command=canvas.yview)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        canvas.configure(yscrollcommand=scrollbar.set)

        inner = tk.Frame(canvas, bg="darkolivegreen")
        canvas.create_window((0, 0), window=inner, anchor="nw")
        inner.bind(
            "<Configure>",
            lambda event, canv=canvas: canv.configure(scrollregion=canv.bbox("all"))
        )

        for preset in FLAT_TERRAIN_TEXTURE_PRESETS:
            self._build_flat_texture_entry(inner, preset)

        tips_frame = tk.Frame(inner, bg="darkolivegreen")
        tips_frame.pack(fill=tk.X, padx=10, pady=(6, 10))
        tk.Label(
            tips_frame,
            text="Wskazówka: wybierz wzór jako aktywny, aby malować nim teren płaski.",
            wraplength=300,
            justify="left",
            bg="darkolivegreen",
            fg="white",
            font=("Arial", 8, "italic")
        ).pack(anchor="w")

        window.bind("<Control-Shift-F>", self.toggle_flat_texture_window)
        window.bind("<Escape>", self.close_flat_texture_window)
        window.protocol("WM_DELETE_WINDOW", self.close_flat_texture_window)
        self.flat_texture_window = window

    def close_flat_texture_window(self, event=None):
        if self.flat_texture_window and self.flat_texture_window.winfo_exists():
            try:
                self.flat_texture_window.destroy()
            except Exception:
                pass
        self.flat_texture_window = None
        return "break"

    def _build_flat_texture_entry(self, parent, preset_meta: dict) -> None:
        entry_frame = tk.Frame(parent, bg="darkolivegreen", bd=1, relief=tk.GROOVE, padx=6, pady=6)
        entry_frame.pack(fill=tk.X, padx=8, pady=4)

        preview_label = tk.Label(entry_frame, bg="darkolivegreen")
        preview_label.pack(side=tk.LEFT, padx=(0, 8))

        preview_image = self._get_flat_texture_preview(preset_meta["key"])
        preview_label.configure(image=preview_image)
        preview_label.image = preview_image

        text_frame = tk.Frame(entry_frame, bg="darkolivegreen")
        text_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

        tk.Label(
            text_frame,
            text=preset_meta.get("name", preset_meta["key"]),
            bg="darkolivegreen",
            fg="white",
            font=("Arial", 10, "bold"),
            anchor="w"
        ).pack(anchor="w")

        description = preset_meta.get("description")
        if description:
            tk.Label(
                text_frame,
                text=description,
                wraplength=220,
                justify="left",
                bg="darkolivegreen",
                fg="white",
                font=("Arial", 8)
            ).pack(anchor="w", pady=(2, 6))

        buttons_frame = tk.Frame(text_frame, bg="darkolivegreen")
        buttons_frame.pack(fill=tk.X)

        tk.Button(
            buttons_frame,
            text="Aktywny pędzel",
            command=lambda key=preset_meta["key"]: self.set_flat_texture_brush(key),
            bg="saddlebrown",
            fg="white",
            activebackground="saddlebrown",
            activeforeground="white"
        ).pack(side=tk.LEFT, expand=True, fill=tk.X, padx=(0, 4))

        tk.Button(
            buttons_frame,
            text="Zastosuj na heksie",
            command=lambda key=preset_meta["key"]: self.apply_flat_texture_preset(key),
            bg="forestgreen",
            fg="white",
            activebackground="forestgreen",
            activeforeground="white"
        ).pack(side=tk.LEFT, expand=True, fill=tk.X)

    def set_flat_texture_brush(self, preset_key: str) -> None:
        preset_meta = FLAT_TERRAIN_PRESET_LOOKUP.get(preset_key)
        if not preset_meta:
            messagebox.showerror("Błąd", f"Nieznany wzór terenu: {preset_key}")
            return
        if preset_meta.get("type") == "clear":
            self.selected_flat_texture_preset = "none"
        else:
            self.selected_flat_texture_preset = preset_key
        self.update_flat_texture_status()
        self.set_status(f"Aktywny wzór terenu płaskiego: {preset_meta.get('name', preset_key)}")

    def update_flat_texture_status(self) -> None:
        if not hasattr(self, "flat_texture_status_var"):
            return
        if not self.selected_flat_texture_preset or self.selected_flat_texture_preset == "none":
            self.flat_texture_status_var.set("Aktywny wzór: brak")
        else:
            preset_meta = FLAT_TERRAIN_PRESET_LOOKUP.get(self.selected_flat_texture_preset, {})
            preset_name = preset_meta.get("name", self.selected_flat_texture_preset)
            self.flat_texture_status_var.set(f"Aktywny wzór: {preset_name}")

    def apply_flat_texture_preset(self, preset_key: str, target_hex: str | None = None) -> None:
        preset_meta = FLAT_TERRAIN_PRESET_LOOKUP.get(preset_key)
        if not preset_meta:
            messagebox.showerror("Błąd", f"Nieznany wzór terenu: {preset_key}")
            return

        if target_hex is None:
            if self.selected_hex is None:
                messagebox.showinfo("Informacja", "Najpierw wybierz heks do zastosowania wzoru.")
                return
            target_hex = self.selected_hex

        if target_hex not in self.hex_centers:
            messagebox.showerror("Błąd", f"Heks {target_hex} nie istnieje na mapie.")
            return

        record = self.hex_data.get(target_hex, {}).copy()
        base_flat = TERRAIN_TYPES["teren_płaski"]
        record["terrain_key"] = "teren_płaski"
        record["move_mod"] = base_flat["move_mod"]
        record["defense_mod"] = base_flat["defense_mod"]

        previous_texture = record.get("texture")
        if preset_meta.get("type") == "clear":
            self._clear_flat_texture_from_record(record)
            preset_name = preset_meta.get("name", "Brak tekstury")
        else:
            self._apply_flat_texture_preset_to_record(record, preset_key)
            preset_name = preset_meta.get("name", preset_key)

        self.hex_data[target_hex] = record
        self.save_data()

        new_texture = record.get("texture")
        if previous_texture != new_texture:
            self.draw_grid()
        else:
            cx, cy = self.hex_centers[target_hex]
            self.draw_hex(target_hex, cx, cy, self.hex_size, record)

        if self.selected_hex == target_hex:
            self.update_hex_info_display(target_hex)

        self.auto_save('tekstura płaska')
        self.set_status(f"Zastosowano wzór '{preset_name}' na heksie {target_hex}")

    def clear_token_selection(self):
        """Czyści aktualnie wybrany żeton do wystawienia."""
        if self.selected_token_button:
            try:
                # Sprawdź czy przycisk nadal istnieje (dialog może być zamknięty)
                self.selected_token_button.config(relief="raised", bg="saddlebrown")
            except tk.TclError:
                # Przycisk został zniszczony (dialog zamknięty) - ignoruj błąd
                pass
        self.selected_token_for_deployment = None
        self.selected_token_button = None

    def _delete_hex_texture_if_unused(self, texture_rel: str | None) -> None:
        """Usuwa wygenerowaną teksturę, gdy żaden heks z niej nie korzysta."""
        if not texture_rel:
            return

        # Jeśli jakiś inny heks nadal korzysta z tej tekstury, nie usuwamy plików.
        if any(
            terrain.get("texture") == texture_rel
            for terrain in self.hex_data.values()
        ):
            return

        texture_path = fix_image_path(texture_rel)
        try:
            texture_path.relative_to(HEX_TEXTURE_DIR)
        except ValueError:
            # Tekstura znajduje się poza katalogiem generowanych plików – pozostawiamy ją.
            return

        try:
            texture_path.unlink(missing_ok=True)
            print(f"🗑️ Usunięto teksturę heksa: {texture_path.name}")
        except Exception as exc:  # noqa: BLE001
            print(f"⚠️ Nie udało się usunąć tekstury {texture_path}: {exc}")

        # Usuń plik metadanych wygenerowanych rzek, jeśli istnieje.
        try:
            metadata_path = texture_path.with_suffix(".json")
            metadata_path.relative_to(RIVER_OUTPUT_DIR)
        except ValueError:
            metadata_path = None

        if metadata_path and metadata_path.exists():
            try:
                metadata_path.unlink(missing_ok=True)
                print(f"🗑️ Usunięto metadane rzeki: {metadata_path.name}")
            except Exception as exc:  # noqa: BLE001
                print(f"⚠️ Nie udało się usunąć metadanych rzeki {metadata_path}: {exc}")

        # Wyczyść cache tekstur odnoszące się do usuniętego pliku.
        self.hex_texture_cache = {
            key: value for key, value in self.hex_texture_cache.items() if key[0] != texture_rel
        }

    def continue_river_from_selected_hex(self) -> None:
        """Przygotowuje narzędzie rzeki do kontynuacji istniejącego nurtu."""
        if self.selected_hex is None:
            messagebox.showinfo("Kontynuacja rzeki", "Najpierw wybierz heks z istniejącą rzeką.", parent=self.root)
            return

        record = self.hex_data.get(self.selected_hex)
        if not record:
            messagebox.showwarning(
                "Kontynuacja rzeki",
                "Wybrany heks nie ma zapisanych danych terenu.",
                parent=self.root,
            )
            return

        texture_rel = record.get("texture")
        if not texture_rel:
            messagebox.showwarning(
                "Kontynuacja rzeki",
                "Heks nie posiada wygenerowanej tekstury rzeki.",
                parent=self.root,
            )
            return

        texture_path = fix_image_path(texture_rel)
        metadata_rel = record.get("river_metadata_path")
        metadata_path = fix_image_path(metadata_rel) if metadata_rel else None

        texture_from_generator = False
        try:
            texture_path.relative_to(RIVER_OUTPUT_DIR)
            texture_from_generator = True
        except ValueError:
            texture_from_generator = False

        if not texture_from_generator and metadata_path is None:
            messagebox.showwarning(
                "Kontynuacja rzeki",
                "Tekstura nie pochodzi z generatora rzek – nie można jej kontynuować automatycznie.",
                parent=self.root,
            )
            return

        if metadata_path is None and texture_from_generator:
            metadata_path = texture_path.with_suffix(".json")
            if metadata_path.exists():
                record["river_metadata_path"] = to_rel(str(metadata_path))

        if metadata_path is None or not metadata_path.exists():
            messagebox.showwarning(
                "Kontynuacja rzeki",
                "Brak pliku metadanych rzeki dla wybranego heksu.",
                parent=self.root,
            )
            return

        try:
            with metadata_path.open("r", encoding="utf-8") as handle:
                metadata = json.load(handle)
        except Exception as exc:  # noqa: BLE001
            messagebox.showerror(
                "Kontynuacja rzeki",
                f"Nie udało się wczytać metadanych rzeki: {exc}",
                parent=self.root,
            )
            return

        tributary_meta = metadata.get("tributary") if metadata.get("tributary_present") else None
        branch_choice = "main"
        if tributary_meta:
            response = messagebox.askyesnocancel(
                "Kontynuacja rzeki",
                (
                    "Wybrany heks zawiera dopływ.\n"
                    "Wybierz, co chcesz kontynuować:\n"
                    "TAK – główny nurt\n"
                    "NIE – dopływ\n"
                    "ANULUJ – przerwij kontynuację"
                ),
                parent=self.root,
            )
            if response is None:
                return
            branch_choice = "main" if response else "tributary"
        self._river_resume_branch = branch_choice

        grid_value = metadata.get("grid", self._current_river_params.get("grid_size", DEFAULT_HEX_TEXTURE_GRID_SIZE))
        try:
            grid_size = int(grid_value)
        except (TypeError, ValueError):
            grid_size = DEFAULT_HEX_TEXTURE_GRID_SIZE

        shape_key = metadata.get("shape") or "auto"
        if shape_key not in {"auto", "straight", "curve", "turn"}:
            shape_key = "auto"
        shape_label = RIVER_SHAPE_LABELS.get(shape_key, RIVER_SHAPE_LABELS["auto"])

        try:
            shape_strength = float(metadata.get("shape_strength", self._current_river_params.get("shape_strength", 0.5)))
        except (TypeError, ValueError):
            shape_strength = float(self._current_river_params.get("shape_strength", 0.5))

        try:
            noise_amplitude = float(metadata.get("noise_amplitude", self._current_river_params.get("noise_amplitude", 0.0)))
        except (TypeError, ValueError):
            noise_amplitude = float(self._current_river_params.get("noise_amplitude", 0.0))

        try:
            noise_frequency = float(metadata.get("noise_frequency", self._current_river_params.get("noise_frequency", 2.0)))
        except (TypeError, ValueError):
            noise_frequency = float(self._current_river_params.get("noise_frequency", 2.0))

        try:
            bank_offset = float(metadata.get("bank_offset", self._current_river_params.get("bank_offset", DEFAULT_BANK_OFFSET)))
        except (TypeError, ValueError):
            bank_offset = float(self._current_river_params.get("bank_offset", DEFAULT_BANK_OFFSET))

        try:
            bank_variation = float(metadata.get("bank_variation", self._current_river_params.get("bank_variation", DEFAULT_BANK_VARIATION)))
        except (TypeError, ValueError):
            bank_variation = float(self._current_river_params.get("bank_variation", DEFAULT_BANK_VARIATION))

        self.river_size_profile_var.set(CUSTOM_PROFILE_LABEL)
        self.river_curvature_profile_var.set(CUSTOM_PROFILE_LABEL)
        self.river_bank_profile_var.set(CUSTOM_PROFILE_LABEL)
        self.river_grid_var.set(str(grid_size))
        self.river_shape_var.set(shape_label)
        self.river_strength_var.set(shape_strength)
        self.river_noise_var.set(noise_amplitude)
        self.river_frequency_var.set(noise_frequency)
        self.river_bank_offset_var.set(bank_offset)
        self.river_bank_variation_var.set(bank_variation)

        try:
            self.river_seed_var.set(int(metadata.get("seed", self.river_seed_var.get())))
        except (TypeError, ValueError):
            pass
        self._update_river_seed_label()

        self._current_river_params.update(
            grid_size=grid_size,
            shape_preference=shape_key,
            shape_strength=shape_strength,
            noise_amplitude=noise_amplitude,
            noise_frequency=noise_frequency,
            base_bank_offset=bank_offset,
            base_bank_variation=bank_variation,
            bank_offset=bank_offset,
            bank_variation=bank_variation,
        )
        self._apply_river_profiles()

        self.river_tributary_enabled_var.set(bool(tributary_meta))
        if tributary_meta:
            entry_side = tributary_meta.get("entry_side")
            entry_label = TRIBUTARY_ENTRY_SIDE_TO_LABEL.get(entry_side, self.river_tributary_entry_var.get())
            if entry_label:
                self.tributary_entry_profile_var.set(entry_label)
                self.river_tributary_entry_var.set(entry_label)

            join_ratio = tributary_meta.get("join_ratio")
            if join_ratio is None:
                try:
                    join_ratio = float(tributary_meta.get("join_ratio_percent", 55.0)) / 100.0
                except (TypeError, ValueError):
                    join_ratio = 0.55
            join_ratio = max(MIN_TRIBUTARY_JOIN, min(MAX_TRIBUTARY_JOIN, float(join_ratio)))
            self.river_tributary_join_var.set(int(round(join_ratio * 100.0)))

            trib_shape_key = tributary_meta.get("shape", self._current_tributary_params.get("shape", "curve"))
            trib_shape_label = TRIBUTARY_SHAPE_LABELS.get(trib_shape_key, TRIBUTARY_SHAPE_LABELS["curve"])
            self.river_tributary_shape_var.set(trib_shape_label)

            try:
                trib_strength = float(tributary_meta.get("shape_strength", self._current_tributary_params.get("shape_strength", 0.6)))
            except (TypeError, ValueError):
                trib_strength = float(self._current_tributary_params.get("shape_strength", 0.6))
            self.river_tributary_strength_var.set(trib_strength)

            try:
                trib_noise = float(tributary_meta.get("noise_amplitude", self._current_tributary_params.get("noise_amplitude", 0.0)))
            except (TypeError, ValueError):
                trib_noise = float(self._current_tributary_params.get("noise_amplitude", 0.0))
            self.river_tributary_noise_var.set(trib_noise)

            try:
                trib_frequency = float(tributary_meta.get("noise_frequency", self._current_tributary_params.get("noise_frequency", 2.5)))
            except (TypeError, ValueError):
                trib_frequency = float(self._current_tributary_params.get("noise_frequency", 2.5))
            self.river_tributary_frequency_var.set(trib_frequency)

            direction_mode = tributary_meta.get(
                "shape_direction_mode",
                self._current_tributary_params.get("shape_direction_mode", "auto"),
            )
            if direction_mode not in TRIBUTARY_DIRECTION_LABELS:
                direction_mode = "auto"
            self.river_tributary_direction_var.set(TRIBUTARY_DIRECTION_LABELS[direction_mode])

            try:
                tributary_seed = int(tributary_meta.get("seed"))
                base_seed = int(metadata.get("seed", 0))
                offset_value = max(0, tributary_seed - base_seed)
            except (TypeError, ValueError):
                offset_value = self.river_tributary_seed_offset_var.get()
            self.river_tributary_seed_offset_var.set(offset_value)

            try:
                main_bank_offset = float(self.river_bank_offset_var.get())
            except (tk.TclError, TypeError, ValueError):
                main_bank_offset = bank_offset
            try:
                trib_bank_offset = float(tributary_meta.get("bank_offset", main_bank_offset))
            except (TypeError, ValueError):
                trib_bank_offset = main_bank_offset
            bank_offset_scale = trib_bank_offset / main_bank_offset if main_bank_offset else 1.0

            try:
                main_bank_variation = float(self.river_bank_variation_var.get())
            except (tk.TclError, TypeError, ValueError):
                main_bank_variation = bank_variation
            try:
                trib_bank_variation = float(tributary_meta.get("bank_variation", main_bank_variation))
            except (TypeError, ValueError):
                trib_bank_variation = main_bank_variation
            variation_scale = trib_bank_variation / main_bank_variation if main_bank_variation else 1.0

            self.tributary_size_profile_var.set(CUSTOM_PROFILE_LABEL)
            self.tributary_character_profile_var.set(CUSTOM_PROFILE_LABEL)

            self._current_tributary_params.update(
                bank_offset_scale=bank_offset_scale,
                variation_scale=variation_scale,
                shape=trib_shape_key,
                shape_strength=trib_strength,
                noise_amplitude=trib_noise,
                noise_frequency=trib_frequency,
                shape_direction_mode=direction_mode,
                entry_side=entry_side,
            )
            self._apply_tributary_profiles()
        else:
            self.tributary_size_profile_var.set("Średni dopływ")
            self.tributary_character_profile_var.set("Łagodny dopływ")
            default_entry = next(iter(TRIBUTARY_ENTRY_OPTIONS))
            self.tributary_entry_profile_var.set(default_entry)
            self.river_tributary_entry_var.set(default_entry)
            self.river_tributary_join_var.set(int(round(TRIBUTARY_ENTRY_OPTIONS[default_entry]["default_join"] * 100)))
            default_size_cfg = TRIBUTARY_SIZE_OPTIONS.get("Średni dopływ", {})
            default_char_cfg = TRIBUTARY_CHARACTER_OPTIONS.get("Łagodny dopływ", {})
            self._current_tributary_params.update(
                bank_offset_scale=default_size_cfg.get("bank_offset_scale", 0.8),
                variation_scale=default_size_cfg.get("variation_scale", 1.0),
                shape=default_char_cfg.get("shape", "curve"),
                shape_strength=default_char_cfg.get("shape_strength", 0.6),
                noise_amplitude=default_char_cfg.get("noise_amplitude", 0.0),
                noise_frequency=default_char_cfg.get("noise_frequency", 2.5),
                shape_direction_mode=default_char_cfg.get("shape_direction_mode", "auto"),
                entry_side=None,
            )
            self._apply_tributary_profiles()
            self._on_tributary_entry_change()

        if not self.river_mode_active:
            self._skip_river_mode_popup = True
            self._set_river_mode(True)
        else:
            self._river_resume_expected_exit = None

        self._update_tributary_controls_state()

        if self._river_resume_branch == "tributary" and tributary_meta:
            entry_side = tributary_meta.get("entry_side")
            if entry_side in SIDE_TO_AXIAL_DIRECTION:
                self._river_resume_expected_exit = entry_side
            else:
                self._river_resume_branch = "main"
                self._river_resume_expected_exit = metadata.get("exit_side")
        else:
            self._river_resume_expected_exit = metadata.get("exit_side")

        self.river_path = [self.selected_hex]
        self._river_update_status()
        self.draw_grid()
        self.update_hex_info_display(self.selected_hex)
        exit_label = None
        if self._river_resume_expected_exit:
            exit_label = HEX_SIDE_LABELS_PL.get(self._river_resume_expected_exit, self._river_resume_expected_exit)
            branch_label = "dopływu" if self._river_resume_branch == "tributary" else "rzeki"
            self.set_status(
                f"Kontynuacja {branch_label} z heksu {self.selected_hex}. Dodaj sąsiada po stronie: {exit_label}."
            )
        else:
            branch_label = "dopływu" if self._river_resume_branch == "tributary" else "rzeki"
            self.set_status(f"Kontynuacja {branch_label} z heksu {self.selected_hex}. Dodaj kolejny heks ścieżki.")

        action_label = "dopływ" if self._river_resume_branch == "tributary" else "nurt"
        message = (
            f"Dodaj nowe heksy LPM, aby przedłużyć {action_label}. "
            "Zakończ przyciskiem 'Generuj rzekę'."
        )
        if exit_label:
            message += f"\nPierwszy sąsiad powinien leżeć po stronie: {exit_label}."
        messagebox.showinfo("Kontynuacja rzeki", message, parent=self.root)

    def reset_selected_hex(self):
        """Czyści wszystkie dane przypisane do wybranego heksu i aktualizuje plik start_tokens.json."""
        if self.selected_hex is None:
            messagebox.showinfo("Informacja", "Najpierw wybierz heks klikając na niego.")
            return
        self._reset_hex_data_by_id(self.selected_hex)
        self._cleanup_dead_tokens()
        self.save_data()
        self.draw_grid()
        self.export_start_tokens()
        messagebox.showinfo("Sukces", f"Dane dla heksu {self.selected_hex} zostały zresetowane.")

    def _cleanup_dead_tokens(self) -> None:
        # --- USUWANIE MARTWYCH WPISÓW ŻETONÓW Z CAŁEJ MAPY ---
        for hex_id, terrain in list(self.hex_data.items()):
            token = terrain.get("token")
            if token and "image" in token:
                img_path = fix_image_path(token["image"])
                if not img_path.exists():
                    terrain.pop("token", None)

    def _reset_hex_data_by_id(self, hex_id: str) -> None:
        record = self.hex_data.pop(hex_id, None)
        texture_rel = record.get("texture") if record else None

        # Usuwanie danych przypisanych do heksu
        self.key_points.pop(hex_id, None)
        for nation, hexes in self.spawn_points.items():
            if hex_id in hexes:
                hexes.remove(hex_id)
        # Usuwanie żetonu z hex_tokens
        self.hex_tokens.pop(hex_id, None)

        # Usuń tekstury generowane dla tego heksu, jeśli nie są już nigdzie używane.
        self._delete_hex_texture_if_unused(texture_rel)

    def _lake_cluster_signature(self, record: dict) -> tuple | None:
        if not isinstance(record, dict):
            return None
        mode = record.get("lake_mode")
        cluster_seed = record.get("lake_cluster_seed")
        cluster_neighbors = record.get("lake_cluster_neighbors")
        cluster_shape = record.get("lake_cluster_shape")
        if mode not in ("lake_cluster7", "lake_y") and cluster_seed is None and not cluster_neighbors:
            return None
        neighbors_tuple = tuple(cluster_neighbors) if cluster_neighbors else ()
        return (mode, cluster_seed, neighbors_tuple, cluster_shape)

    def _collect_lake_cluster_hexes(self, start_hex: str) -> list[str]:
        record = self.hex_data.get(start_hex)
        signature = self._lake_cluster_signature(record or {})
        if signature is None:
            return [start_hex]

        visited: set[str] = set()
        queue: list[str] = [start_hex]
        while queue:
            current = queue.pop(0)
            if current in visited:
                continue
            visited.add(current)
            current_record = self.hex_data.get(current)
            if self._lake_cluster_signature(current_record or {}) != signature:
                continue
            for delta in AXIAL_DIRECTION_TO_SIDE:
                neighbor_id = f"{int(current.split(',')[0]) + delta[0]},{int(current.split(',')[1]) + delta[1]}"
                if neighbor_id in self.hex_data and neighbor_id not in visited:
                    neighbor_record = self.hex_data.get(neighbor_id)
                    if self._lake_cluster_signature(neighbor_record or {}) == signature:
                        queue.append(neighbor_id)

        return sorted(visited)

    def clear_selected_hex_smart(self) -> None:
        """Czyści wybrany heks z uwzględnieniem spójnych obiektów (np. całe jezioro 1+6/Y)."""
        if self.selected_hex is None:
            messagebox.showinfo("Informacja", "Najpierw wybierz heks klikając na niego.")
            return

        hexes_to_clear = self._collect_lake_cluster_hexes(self.selected_hex)
        for hex_id in hexes_to_clear:
            self._reset_hex_data_by_id(hex_id)

        self._cleanup_dead_tokens()
        self.save_data()
        self.draw_grid()
        self.export_start_tokens()

        if len(hexes_to_clear) > 1:
            messagebox.showinfo(
                "Czyszczenie heksa",
                f"Wyczyszczono spójny obiekt (jezioro): {len(hexes_to_clear)} heksów.",
                parent=self.root,
            )
        else:
            messagebox.showinfo(
                "Czyszczenie heksa",
                f"Wyczyszczono heks: {self.selected_hex}.",
                parent=self.root,
            )

    def do_pan(self, event):
        'Przesuwa mapę myszką.'
        self.canvas.scan_dragto(event.x, event.y, gain=1)

    def start_pan(self, event):
        'Rozpoczyna przesuwanie mapy myszką.'
        self.canvas.scan_mark(event.x, event.y)

    def on_close(self):
        'Obsługuje zamknięcie aplikacji - daje możliwość zapisu mapy.'
        answer = messagebox.askyesno("Zamykanie programu", "Czy chcesz zapisać dane mapy przed zamknięciem?")
        if answer:
            self.save_map_and_data()
        self.root.destroy()

    def print_extreme_hexes(self):
        'Wypisuje w konsoli współrzędne skrajnych heksów (debug).'
        if not self.hex_centers:
            print("Brak heksów do analizy.")
            return
        xs = [coord[0] for coord in self.hex_centers.values()]
        ys = [coord[1] for coord in self.hex_centers.values()]
        print("Skrajne heksy:")
        print("Lewy skrajny (x) =", min(xs))
        print("Prawy skrajny (x) =", max(xs))
        print("Górny skrajny (y) =", min(ys))
        print("Dolny skrajny (y) =", max(ys))

    def get_working_data_path(self):
        # Zawsze zwracaj ścieżkę do data/map_data.json
        data_dir = Path(__file__).parent.parent / "data"
        data_dir.mkdir(exist_ok=True)
        return str(data_dir / "map_data.json")

    def load_tokens_from_folders(self, folders):
        """Wczytuje listę żetonów z podanych folderów (zgodnie z nową strukturą: token.json + token.png)."""
        tokens = []
        for folder in folders:
            if os.path.exists(folder):
                for subfolder in os.listdir(folder):
                    token_folder = os.path.join(folder, subfolder)
                    if os.path.isdir(token_folder):
                        json_path = os.path.join(token_folder, "token.json")   # poprawka: nowa nazwa pliku
                        png_path = os.path.join(token_folder, "token.png")     # poprawka: nowa nazwa pliku
                        if os.path.exists(json_path) and os.path.exists(png_path):
                            tokens.append({
                                "name": subfolder,
                                "json_path": json_path,
                                "image_path": png_path
                            })
        return tokens

    def deploy_token_dialog(self):
        """PRZESTARZAŁA METODA - używa nowej palety żetonów"""
        print("Metoda deploy_token_dialog jest przestarzała. Używaj nowej palety żetonów.")
        # Stara implementacja została zastąpiona przez paletę żetonów w panelu bocznym
        """Wyświetla okno dialogowe z wszystkimi dostępnymi żetonami w folderze tokeny (unikalność: żeton znika po wystawieniu)."""
        dialog = tk.Toplevel(self.root)
        dialog.title("Wybierz żeton")
        dialog.geometry("300x300")  # Ustawienie rozmiaru okna
        dialog.transient(self.root)
        dialog.grab_set()

        # Konfiguracja siatki w oknie dialogowym
        dialog.rowconfigure(0, weight=1)
        dialog.columnconfigure(0, weight=1)

        # Ramka przewijana dla żetonów
        frame_container = tk.Frame(dialog, bg="darkolivegreen")
        frame_container.grid(row=0, column=0, sticky="nsew")

        frame_container.rowconfigure(0, weight=1)
        frame_container.columnconfigure(0, weight=1)

        canvas = tk.Canvas(frame_container, bg="darkolivegreen")
        canvas.grid(row=0, column=0, sticky="nsew")

        scroll_y = tk.Scrollbar(frame_container, orient="vertical", command=canvas.yview)
        scroll_y.grid(row=0, column=1, sticky="ns")

        scroll_x = tk.Scrollbar(frame_container, orient="horizontal", command=canvas.xview)
        scroll_x.grid(row=1, column=0, sticky="ew")

        frame = tk.Frame(canvas, bg="darkolivegreen")

        # Konfiguracja przewijania
        canvas.create_window((0, 0), window=frame, anchor="nw")
        canvas.configure(yscrollcommand=scroll_y.set, xscrollcommand=scroll_x.set)

        # Wczytaj żetony z folderów
        token_base = str(ASSET_ROOT / "tokens")
        token_folders = [os.path.join(token_base, d)
                         for d in os.listdir(token_base)
                         if os.path.isdir(os.path.join(token_base, d))]
        tokens = self.load_tokens_from_folders(token_folders)

        # Filtruj żetony, które już są na mapie (unikalność)
        used_token_ids = set()
        for terrain in self.hex_data.values():
            token = terrain.get("token")
            if token and "unit" in token:
                used_token_ids.add(token["unit"])
        available_tokens = [t for t in tokens if self._get_token_id_from_json(t["json_path"]) not in used_token_ids]
        
        # Wyświetlanie żetonów
        for token in available_tokens:
            if os.path.exists(token["image_path"]):
                img = Image.open(token["image_path"]).resize((50, 50))
                img = ImageTk.PhotoImage(img)
                btn = tk.Button(
                    frame, image=img, text=token["name"], compound="top",
                    bg="saddlebrown", fg="white", relief="raised",
                    command=lambda t=token, b=None, d=dialog: self.select_token_for_deployment(t, b, d)
                )
                btn.image = img  # Przechowuj referencję do obrazu
                btn.pack(pady=5, padx=5, side="left")
                  # Zaktualizuj lambda, aby przekazać referencję do przycisku i dialoga
                btn.config(command=lambda t=token, b=btn, d=dialog: self.select_token_for_deployment(t, b, d))

        # Ustawienie scrollregion po dodaniu widgetów
        frame.update_idletasks()
        canvas.configure(scrollregion=canvas.bbox("all"))

    def select_token_for_deployment(self, token, button, dialog=None):
        """Wybiera żeton do wystawienia (system click-and-click)."""
        # Wyczyść poprzedni wybór
        self.clear_token_selection()

        # Ustaw nowy wybór
        self.selected_token_for_deployment = token
        self.selected_token_button = button

        # Podświetl wybrany przycisk
        if button is not None:
            button.config(relief="sunken", bg="orange")

        # Zamknij dialog po wyborze żetonu
        if dialog is not None:
            try:
                dialog.destroy()
            except Exception:
                pass

        # Informuj użytkownika
        self.set_status(f"Wybrano żeton: {token['name']} (kliknij heks aby postawić)")

    def _get_token_id_from_json(self, json_path):
        try:
            with open(json_path, "r", encoding="utf-8") as f:
                token_json = json.load(f)
            return token_json.get("id")
        except Exception:
            return None

    def place_token_on_hex(self, token, clicked_hex):
        """Umieszcza wybrany żeton na wskazanym heksie (string 'q,r')."""
        if not token or not clicked_hex:
            return

        try:
            q, r = map(int, clicked_hex.split(","))
        except ValueError:
            return
        hex_id = f"{q},{r}"

        # Jeśli brak wpisu – utwórz z domyślnym terenem
        if hex_id not in self.hex_data:
            self.hex_data[hex_id] = {
                "terrain_key": "płaski",
                "move_mod": 0,
                "defense_mod": 0
            }

        # Wczytaj prawdziwe ID żetonu z token.json
        try:
            with open(token["json_path"], "r", encoding="utf-8") as f:
                token_json = json.load(f)
            token_id = token_json.get("id", Path(token["json_path"]).stem)
        except Exception:
            token_id = Path(token.get("json_path", "UNKNOWN.json")).stem

        rel_path = to_rel(token["image_path"]).replace("\\", "/")
        self.hex_data[hex_id]["token"] = {"unit": token_id, "image": rel_path}

        # Odśwież mapę i zapisz
        self.draw_grid()
        self.set_status(f"Postawiono żeton '{token['name']}' na {hex_id}")
        self.auto_save('postawiono żeton')

    def toggle_brush(self, key):
        if self.current_brush == key:           # drugi klik → wyłącz
            self.terrain_buttons[key].config(relief="raised")
            self.current_brush = None
            return
        # przełącz pędzel
        for k,b in self.terrain_buttons.items():
            b.config(relief="raised")
        self.terrain_buttons[key].config(relief="sunken")
        self.current_brush = key
        
        # Automatycznie zwiń sekcję po wyborze terenu
        if self._terrain_expanded:
            self._toggle_terrain_section()

    def paint_hex(self, clicked_hex, terrain_key):
        'Maluje heks wybranym typem terenu.'
        q, r = clicked_hex
        hex_id = f"{q},{r}"
        terrain = TERRAIN_TYPES.get(terrain_key)
        if terrain:
            current_record = self.hex_data.get(hex_id, {})
            updated_record = current_record.copy()
            previous_texture = current_record.get("texture")
            updated_record["terrain_key"] = terrain_key
            updated_record["move_mod"] = terrain["move_mod"]
            updated_record["defense_mod"] = terrain["defense_mod"]

            is_default_flat = (
                terrain_key == "teren_płaski"
                and terrain["move_mod"] == self.hex_defaults.get("move_mod", 0)
                and terrain["defense_mod"] == self.hex_defaults.get("defense_mod", 0)
            )
            extra_keys = {k for k in updated_record.keys() if k not in {"terrain_key", "move_mod", "defense_mod"}}

            if is_default_flat and not extra_keys:
                updated_record = {
                    "terrain_key": terrain_key,
                    "move_mod": terrain["move_mod"],
                    "defense_mod": terrain["defense_mod"]
                }

            if terrain_key == "teren_płaski":
                brush_preset = self.selected_flat_texture_preset
                if brush_preset == "none":
                    self._clear_flat_texture_from_record(updated_record)
                elif brush_preset:
                    self._apply_flat_texture_preset_to_record(updated_record, brush_preset)
                elif "flat_texture_preset" in updated_record and updated_record.get("texture") is None:
                    self._clear_flat_texture_from_record(updated_record)
            else:
                self._clear_flat_texture_from_record(updated_record)

            self.hex_data[hex_id] = updated_record
            terrain_for_draw = updated_record
            self.save_data()
            new_texture = updated_record.get("texture")
            needs_full_redraw = previous_texture != new_texture
            if needs_full_redraw:
                self.draw_grid()
            else:
                cx, cy = self.hex_centers[hex_id]
                self.draw_hex(hex_id, cx, cy, self.hex_size, terrain_for_draw)
            if self.selected_hex == hex_id:
                self.update_hex_info_display(hex_id)
        else:
            messagebox.showerror("Błąd", "Niepoprawny rodzaj terenu.")
        self.auto_save('malowanie terenu')

    def export_start_tokens(self, path=None, show_message=True):
        """Eksportuje rozmieszczenie wszystkich żetonów na mapie do assets/start_tokens.json."""
        if path is None:
            path = str(ASSET_ROOT / "start_tokens.json")
        tokens = []
        for hex_id, terrain in self.hex_data.items():
            token = terrain.get("token")
            if token and "unit" in token:
                try:
                    q, r = map(int, hex_id.split(","))
                except Exception:
                    continue
                tokens.append({
                    "id": token["unit"],
                    "q": q,
                    "r": r
                })
        with open(path, "w", encoding="utf-8") as f:
            json.dump(tokens, f, indent=2, ensure_ascii=False)
        
        if show_message:
            messagebox.showinfo("Sukces", f"Wyeksportowano rozmieszczenie żetonów do:\n{path}")
        return len(tokens)

    def on_commander_selected(self, event):
        """Obsługuje wybór dowódcy z dropdown"""
        selected_commander = self.commander_var.get()
        print(f"⚔️  Wybrano dowódcę z dropdown: {selected_commander}")
        
        if selected_commander == "Wszyscy dowódcy":
            self.commander_filter = None
        else:
            self.commander_filter = selected_commander
        
        self.update_filtered_tokens()

if __name__ == '__main__':
    import sys
    try:
        cfg = CONFIG  # użyj lokalnej stałej CONFIG
        root = tk.Tk()
        root.title('Map Editor')
        app = MapEditor(root, cfg)
        root.mainloop()
    except Exception as e:
        print('Błąd startu:', e, file=sys.stderr)
        raise
