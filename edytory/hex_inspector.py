
#!/usr/bin/env python3
"""Hex Inspector – szybki tester generatorów heksów.

To narzędzie jest używane często, więc trzymamy je w folderze edytory/.
Eksporty lądują w edytory/_hex_inspector_output/.
"""

import sys
import json
import random
import os
import subprocess
import tkinter as tk
from tkinter import scrolledtext, messagebox
from pathlib import Path
from datetime import datetime
from typing import Any, Dict, Optional
import math
import uuid

from PIL import Image, ImageTk


try:
    from PIL.Image import Resampling  # type: ignore

    RESAMPLE_NEAREST = Resampling.NEAREST
except Exception:
    # Fallback dla starszych Pillow / stubów typów: 0 == nearest
    RESAMPLE_NEAREST = 0


# Root projektu
PROJEKT_ROOT = Path(__file__).parent.parent

# Upewnij się, że generatorowe moduły z edytory/ są importowalne
sys.path.insert(0, str(PROJEKT_ROOT / "edytory"))

import generate_road_hex_tile as road_gen
import generate_river_hex_tile as river_gen
import generate_railway_hex_tile as rail_gen
import generate_lake_hex_tile as lake_gen

from generate_road_hex_tile import RoadOptions, generate_road
from generate_river_hex_tile import RiverCenterlineOptions, TributaryOptions, generate_centerline
from generate_railway_hex_tile import RailwayOptions, generate_railway, _is_valid_junction
from generate_lake_hex_tile import LakeOptions, generate_lake
from generate_forest_hex_tile import ForestOptions, generate_forest, generate_forest_cluster

try:
    from hex_feature_semantics import normalize_railway_options, normalize_road_options
except Exception:
    normalize_road_options = None
    normalize_railway_options = None

# ============================================================================
# OGRANICZENIA ZGODNE Z MAP EDITOREM (1:1)
# ============================================================================

# Jeziora: wartości zgodne z Map Editorem
MAP_EDITOR_LAKE_SINGLE_RADII = (0.26, 0.34, 0.42)
MAP_EDITOR_LAKE_CLUSTER_SCALES = (0.80, 1.00, 1.25)

# Rzeki: profile zgodne z Map Editorem
MAP_EDITOR_RIVER_SIZE_PRESETS = (
    {
        "label": "Duża rzeka",
        "bank_offset": float(river_gen.DEFAULT_BANK_OFFSET) * 1.55,
        "bank_variation": float(river_gen.DEFAULT_BANK_VARIATION) * 1.2,
    },
    {
        "label": "Mała rzeka",
        "bank_offset": float(river_gen.DEFAULT_BANK_OFFSET) * 1.05,
        "bank_variation": float(river_gen.DEFAULT_BANK_VARIATION),
    },
    {
        "label": "Strumień",
        "bank_offset": float(river_gen.DEFAULT_BANK_OFFSET) * 0.78,
        "bank_variation": float(river_gen.DEFAULT_BANK_VARIATION) * 0.85,
    },
)

MAP_EDITOR_RIVER_CURVATURE_PRESETS = (
    {
        "label": "Prosta",
        "shape_preference": "straight",
        "shape_strength": 0.25,
        "noise_amplitude": 0.05,
        "noise_frequency": 1.2,
    },
    {
        "label": "Łagodna",
        "shape_preference": "curve",
        "shape_strength": 0.45,
        "noise_amplitude": 0.18,
        "noise_frequency": 1.8,
    },
    {
        "label": "Meandrująca",
        "shape_preference": "curve",
        "shape_strength": 0.7,
        "noise_amplitude": 0.3,
        "noise_frequency": 2.4,
    },
    {
        "label": "Dynamiczna",
        "shape_preference": "turn",
        "shape_strength": 0.85,
        "noise_amplitude": 0.45,
        "noise_frequency": 3.0,
    },
)

MAP_EDITOR_RIVER_BANK_PRESETS = (
    {"label": "Stabilny brzeg", "offset_multiplier": 1.0, "variation_multiplier": 0.85, "variation_add": 0.0},
    {"label": "Erozyjny brzeg", "offset_multiplier": 1.15, "variation_multiplier": 1.25, "variation_add": 0.08},
    {"label": "Piaszczysty brzeg", "offset_multiplier": 1.25, "variation_multiplier": 0.95, "variation_add": -0.02},
    {"label": "Błotnisty brzeg", "offset_multiplier": 0.9, "variation_multiplier": 1.35, "variation_add": 0.1},
)

MAP_EDITOR_TRIBUTARY_SIZE_PRESETS = (
    {"label": "Mały dopływ", "bank_offset_scale": 0.65, "variation_scale": 0.9},
    {"label": "Średni dopływ", "bank_offset_scale": 0.8, "variation_scale": 1.0},
    {"label": "Duży dopływ", "bank_offset_scale": 1.0, "variation_scale": 1.15},
)

MAP_EDITOR_TRIBUTARY_CHARACTER_PRESETS = (
    {
        "label": "Łagodny dopływ",
        "shape": "curve",
        "shape_strength": 0.55,
        "noise_amplitude": 0.18,
        "noise_frequency": 2.2,
        "shape_direction_mode": "auto",
    },
    {
        "label": "Ostry dopływ",
        "shape": "turn",
        "shape_strength": 0.85,
        "noise_amplitude": 0.32,
        "noise_frequency": 2.9,
        "shape_direction_mode": "auto",
    },
    {
        "label": "Esowaty dopływ",
        "shape": "curve",
        "shape_strength": 0.75,
        "noise_amplitude": 0.28,
        "noise_frequency": 2.6,
        "shape_direction_mode": "auto",
    },
)


class HexInspector:
    def __init__(self, root: tk.Tk):
        self.root = root
        self.root.title("🔍 Hex Inspector - Tester Generatorów")
        self.root.geometry("700x950")
        self.root.resizable(True, True)
        self.root.minsize(700, 900)

        self.current_category = tk.StringVar(value="railway")
        self.current_mode = tk.StringVar(value="single")
        self.current_config: Optional[Dict[str, Any]] = None
        self.current_image: Optional[Image.Image] = None
        self.current_photo: Optional[ImageTk.PhotoImage] = None
        self.last_export_dir: Optional[Path] = None

        self.current_cluster: Optional[Dict[str, Any]] = None

        # Jedno pokrętło do strojenia szerokości połączenia jezioro↔rzeka.
        # Tryb zgodny z Map Editorem (realne parametry zamiast losowych ekstremów).
        self.use_map_editor_profiles = tk.BooleanVar(value=True)

        self.backgrounds_dir = PROJEKT_ROOT / "assets" / "terrain" / "hex_painted"
        self.output_dir = PROJEKT_ROOT / "edytory" / "_hex_inspector_output"
        self.output_dir.mkdir(exist_ok=True)
        self.fix_queue_path = self.output_dir / "fix_queue.jsonl"

        self._create_ui()
        self._generate_random()

    def _show_preview_window(self, image_path: Path) -> None:
        try:
            img = Image.open(image_path).convert("RGBA")
        except Exception as exc:
            messagebox.showerror("Podgląd", f"Nie udało się wczytać obrazu:\n{image_path}\n\n{exc}")
            return

        self.root.update_idletasks()
        box_w = int(self.preview_label.winfo_width() or 512)
        box_h = int(self.preview_label.winfo_height() or 512)
        w, h = img.size
        scale = min(1.0, box_w / float(w), box_h / float(h))
        if scale < 1.0:
            img = img.resize((int(round(w * scale)), int(round(h * scale))), RESAMPLE_NEAREST)

        photo = ImageTk.PhotoImage(img)
        self.current_photo = photo
        self.current_image = img
        self.preview_label.configure(image=photo)

    def _restore_state_from_export(self, export_dir: Path) -> None:
        config_path = export_dir / "hex_config.json"
        report_path = export_dir / "problem_report.txt"

        if config_path.exists():
            try:
                config = json.loads(config_path.read_text(encoding="utf-8"))
                category = str(config.get("category") or self.current_category.get())
                mode = str(config.get("mode") or "single")
                if category in {"road", "river", "railway", "lake"}:
                    self.current_category.set(category)
                if mode in {"single", "cluster7"}:
                    self.current_mode.set(mode)
                self.current_config = config
            except Exception as exc:
                messagebox.showwarning("Stan eksportu", f"Nie udało się wczytać hex_config.json:\n{exc}")

        if report_path.exists():
            try:
                content = report_path.read_text(encoding="utf-8")
                marker = "OPIS PROBLEMU:"
                if marker in content:
                    desc = content.split(marker, 1)[1].strip()
                else:
                    desc = content.strip()
                if hasattr(self, "description_text"):
                    self.description_text.delete("1.0", tk.END)
                    if desc:
                        self.description_text.insert(tk.END, desc)
            except Exception:
                pass

    def _append_fix_queue_entry(self, *, fix_id: str, export_dir: Path, config: Dict[str, Any], description: str) -> None:
        entry: Dict[str, Any] = {
            "fix_id": fix_id,
            "created_at": datetime.now().isoformat(timespec="seconds"),
            "status": "new",
            "export_dir": str(export_dir),
            "mode": str(config.get("mode") or self.current_mode.get()),
            "category": str(config.get("category") or self.current_category.get()),
            "pattern": config.get("pattern"),
            "description": description,
            "files": {
                "config": str(export_dir / "hex_config.json"),
                "report": str(export_dir / "problem_report.txt"),
            },
        }

        if entry["mode"] == "cluster7":
            entry["files"].update(
                {
                    "mosaic": str(export_dir / "cluster_preview.png"),
                    "tiles_dir": str(export_dir / "tiles"),
                }
            )
        else:
            entry["files"].update({"png": str(export_dir / "hex_problem.png")})

        try:
            with open(self.fix_queue_path, "a", encoding="utf-8") as f:
                f.write(json.dumps(entry, ensure_ascii=False) + "\n")
        except Exception as e:
            messagebox.showwarning(
                "Kolejka fixów",
                f"Pakiet zapisany, ale nie udało się dopisać do kolejki fixów:\n{self.fix_queue_path}\n\n{e}",
            )

    def _create_ui(self) -> None:
        header = tk.Frame(self.root, bg="#2d2d2d", height=60)
        header.pack(fill=tk.X, padx=0, pady=0)
        header.pack_propagate(False)

        title = tk.Label(
            header,
            text="🔍 Hex Inspector",
            font=("Segoe UI", 16, "bold"),
            bg="#2d2d2d",
            fg="#4fc3f7",
        )
        title.pack(pady=15)

        category_frame = tk.Frame(self.root, bg="#1e1e1e")
        category_frame.pack(fill=tk.X, padx=20, pady=(10, 5))

        tk.Label(
            category_frame,
            text="Kategoria:",
            font=("Segoe UI", 10),
            bg="#1e1e1e",
            fg="#ddd",
        ).pack(side=tk.LEFT, padx=(0, 10))

        for cat in ["road", "river", "railway", "lake", "forest"]:
            rb = tk.Radiobutton(
                category_frame,
                text=cat.capitalize(),
                variable=self.current_category,
                value=cat,
                bg="#1e1e1e",
                fg="#ddd",
                selectcolor="#363636",
                font=("Segoe UI", 10),
                activebackground="#1e1e1e",
                activeforeground="#4fc3f7",
            )
            rb.pack(side=tk.LEFT, padx=5)

        mode_frame = tk.Frame(self.root, bg="#1e1e1e")
        mode_frame.pack(fill=tk.X, padx=20, pady=(0, 10))

        tk.Label(
            mode_frame,
            text="Tryb:",
            font=("Segoe UI", 10),
            bg="#1e1e1e",
            fg="#ddd",
        ).pack(side=tk.LEFT, padx=(0, 10))

        for label, val in [("Pojedynczy", "single"), ("Klaster 7 (1+6)", "cluster7")]:
            rb = tk.Radiobutton(
                mode_frame,
                text=label,
                variable=self.current_mode,
                value=val,
                bg="#1e1e1e",
                fg="#ddd",
                selectcolor="#363636",
                font=("Segoe UI", 10),
                activebackground="#1e1e1e",
                activeforeground="#4fc3f7",
            )
            rb.pack(side=tk.LEFT, padx=5)

        profile_frame = tk.Frame(self.root, bg="#1e1e1e")
        profile_frame.pack(fill=tk.X, padx=20, pady=(0, 10))

        tk.Checkbutton(
            profile_frame,
            text="✅ Realne parametry jak w Map Editorze",
            variable=self.use_map_editor_profiles,
            bg="#1e1e1e",
            fg="#ddd",
            selectcolor="#363636",
            activebackground="#1e1e1e",
            activeforeground="#4fc3f7",
            font=("Segoe UI", 9),
        ).pack(side=tk.LEFT)

        preview_container = tk.Frame(self.root, bg="#1e1e1e")
        preview_container.pack(fill=tk.BOTH, expand=True, padx=20, pady=10)

        preview_frame = tk.Frame(preview_container, bg="#1a1a1a", bd=2, relief=tk.SUNKEN)
        preview_frame.pack()

        self.preview_label = tk.Label(preview_frame, bg="#1a1a1a", width=512, height=512)
        self.preview_label.pack(padx=5, pady=5)
        self.preview_label.bind("<Button-1>", self._on_preview_click)

        btn_regenerate = tk.Button(
            self.root,
            text="🔄 Generuj Losowo",
            font=("Segoe UI", 11, "bold"),
            bg="#4fc3f7",
            fg="#000",
            activebackground="#29b6f6",
            activeforeground="#000",
            cursor="hand2",
            command=self._generate_random,
            height=2,
        )
        btn_regenerate.pack(fill=tk.X, padx=20, pady=(5, 10))

        desc_label = tk.Label(
            self.root,
            text="Opis błędu:",
            font=("Segoe UI", 10, "bold"),
            bg="#1e1e1e",
            fg="#ddd",
        )
        desc_label.pack(anchor=tk.W, padx=20, pady=(10, 2))

        self.description_text = scrolledtext.ScrolledText(
            self.root,
            height=5,
            font=("Consolas", 10),
            bg="#2d2d2d",
            fg="#ddd",
            insertbackground="#4fc3f7",
            relief=tk.SUNKEN,
            bd=2,
            wrap=tk.WORD,
        )
        self.description_text.pack(fill=tk.BOTH, expand=False, padx=20, pady=(0, 10))

        buttons_frame = tk.Frame(self.root, bg="#1e1e1e")
        buttons_frame.pack(fill=tk.X, padx=20, pady=(0, 20))

        btn_export = tk.Button(
            buttons_frame,
            text="📦 Eksportuj Pakiet",
            font=("Segoe UI", 11, "bold"),
            bg="#66bb6a",
            fg="#000",
            activebackground="#4caf50",
            activeforeground="#000",
            cursor="hand2",
            command=self._export_package,
            height=2,
        )
        btn_export.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(0, 5))

        btn_open_last = tk.Button(
            buttons_frame,
            text="📂 Otwórz ostatni eksport",
            font=("Segoe UI", 11, "bold"),
            bg="#ffd54f",
            fg="#000",
            activebackground="#ffca28",
            activeforeground="#000",
            cursor="hand2",
            command=self._open_last_export,
            height=2,
        )
        btn_open_last.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=5)

        btn_clear = tk.Button(
            buttons_frame,
            text="🗑️ Wyczyść Eksporty",
            font=("Segoe UI", 11, "bold"),
            bg="#ef5350",
            fg="#000",
            activebackground="#e53935",
            activeforeground="#000",
            cursor="hand2",
            command=self._clear_exports,
            height=2,
        )
        btn_clear.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(5, 0))

        footer = tk.Label(
            self.root,
            text="Wygeneruj heks → Opisz błąd → Eksportuj → Wklej w czat",
            font=("Segoe UI", 9),
            bg="#1e1e1e",
            fg="#888",
        )
        footer.pack(side=tk.BOTTOM, pady=(5, 10))

    def _find_backgrounds(self):
        backgrounds = []
        flat_dir = self.backgrounds_dir / "flat"
        for base in (flat_dir, self.backgrounds_dir):
            if not base.exists():
                continue
            for bg in base.glob("flat_*.png"):
                backgrounds.append(bg)
        return backgrounds

    def _pick_background(self, rng: random.Random) -> Optional[str]:
        bgs = self._find_backgrounds()
        if not bgs:
            return None
        return rng.choice(bgs).name

    def _pick_entry_exit_with_coverage(self, rng: random.Random, prefer_horizontal: bool = False) -> tuple[str, str]:
        sides = list(rail_gen.HEX_SIDES)

        special_pairs = [
            ("top", "bottom"),
            ("top_left", "bottom_right"),
            ("top_right", "bottom_left"),
            ("bottom_right", "bottom_left"),
            ("top_left", "top_right"),
            ("bottom_left", "bottom_right"),
            ("top_right", "top"),
            ("top", "top_left"),
            ("bottom", "bottom_right"),
            ("bottom_left", "bottom"),
        ]

        if prefer_horizontal and rng.random() < 0.35:
            return ("bottom_right", "bottom_left")

        if rng.random() < 0.35:
            a, b = rng.choice(special_pairs)
            return (a, b) if rng.random() < 0.5 else (b, a)

        entry = rng.choice(sides)
        mode = rng.choices(["adjacent", "skip_one", "any"], weights=[0.45, 0.25, 0.30], k=1)[0]
        if mode == "any":
            return entry, rng.choice([s for s in sides if s != entry])

        entry_idx = sides.index(entry)
        if mode == "adjacent":
            exit_idx = (entry_idx + rng.choice([-1, 1])) % len(sides)
        else:
            exit_idx = (entry_idx + rng.choice([-2, 2])) % len(sides)
        return entry, sides[exit_idx]

    def _random_road_config(self, rng: random.Random) -> Dict[str, Any]:
        road_types = sorted(road_gen.ROAD_COLOR_PRESETS.keys())
        widths = sorted(road_gen.ROAD_WIDTH_PRESETS.keys())
        sides = list(road_gen.HEX_SIDES)

        entry, exit_side = self._pick_entry_exit_with_coverage(rng)

        crossroads_sides = []
        if rng.random() < 0.35:
            candidates = [s for s in sides if s not in (entry, exit_side)]
            rng.shuffle(candidates)
            crossroads_sides = candidates[: rng.choice([1, 2])]

        # Map Editor nie dodaje automatycznie tła pod drogami.
        bg = None

        road_type = rng.choice(road_types)
        width = rng.choice(widths)

        opposite = getattr(road_gen, "SIDE_OPPOSITE", {})
        is_straight = bool(opposite) and opposite.get(entry) == exit_side
        is_junction = bool(crossroads_sides)
        if road_type == "piaszczysta" and width == "bardzo_szeroka":
            width = "szeroka" if "szeroka" in widths else width
        if width == "bardzo_szeroka" and (is_junction or not is_straight):
            width = "szeroka" if "szeroka" in widths else width

        return {
            "category": "road",
            "road_type": road_type,
            "entry_side": entry,
            "exit_side": exit_side,
            "width": width,
            "crossroads": crossroads_sides,
            "noise_amplitude": round(rng.uniform(0.05, 0.45), 3),
            "seed": rng.randint(1000, 99999),
            "background": str(bg.name) if bg else None,
        }

    def _random_river_config(self, rng: random.Random) -> Dict[str, Any]:
        river_shapes = list(getattr(river_gen, "PATH_SHAPES", ("straight", "curve", "turn")))
        sides = list(getattr(river_gen, "HEX_SIDES", ("top", "top_right", "bottom_right", "bottom", "bottom_left", "top_left")))

        entry, exit_side = self._pick_entry_exit_with_coverage(rng)

        bg = None

        use_editor_profiles = bool(self.use_map_editor_profiles.get())

        if use_editor_profiles:
            size_preset = rng.choice(MAP_EDITOR_RIVER_SIZE_PRESETS)
            curvature_preset = rng.choice(MAP_EDITOR_RIVER_CURVATURE_PRESETS)
            bank_preset = rng.choice(MAP_EDITOR_RIVER_BANK_PRESETS)

            base_bank_offset = float(size_preset["bank_offset"])
            base_bank_variation = float(size_preset["bank_variation"])
            bank_offset = base_bank_offset * float(bank_preset["offset_multiplier"])
            bank_variation = max(
                0.0,
                base_bank_variation * float(bank_preset["variation_multiplier"])
                + float(bank_preset["variation_add"]),
            )

            shape = curvature_preset["shape_preference"]
            shape_strength = float(curvature_preset["shape_strength"])
            noise_amplitude = float(curvature_preset["noise_amplitude"])
            noise_frequency = float(curvature_preset["noise_frequency"])
        else:
            shape = rng.choice(river_shapes)
            shape_strength = round(rng.uniform(0.25, 0.85), 2)
            noise_amplitude = round(rng.uniform(0.05, 0.45), 3)
            noise_frequency = round(rng.uniform(0.15, 0.35), 3)
            bank_offset = round(rng.uniform(0.6, 3.2), 3)
            bank_variation = round(rng.uniform(0.0, 0.8), 3)

        tributary = None
        if rng.random() < 0.30:
            trib_entry = rng.choice([s for s in sides if s not in (entry, exit_side)])
            trib_size = rng.choice(MAP_EDITOR_TRIBUTARY_SIZE_PRESETS)
            trib_char = rng.choice(MAP_EDITOR_TRIBUTARY_CHARACTER_PRESETS)
            join_ratio = round(rng.uniform(river_gen.MIN_TRIBUTARY_JOIN, river_gen.MAX_TRIBUTARY_JOIN), 2)

            trib_bank_offset = max(0.0, bank_offset * float(trib_size["bank_offset_scale"]))
            trib_bank_variation = max(0.0, bank_variation * float(trib_size["variation_scale"]))

            tributary = {
                "entry_side": trib_entry,
                "join_ratio": join_ratio,
                "shape": trib_char["shape"],
                "shape_strength": float(trib_char["shape_strength"]),
                "noise_amplitude": float(trib_char["noise_amplitude"]),
                "noise_frequency": float(trib_char["noise_frequency"]),
                "shape_direction_mode": trib_char["shape_direction_mode"],
                "seed_offset": 1_000_000,
                "bank_offset": trib_bank_offset,
                "bank_variation": trib_bank_variation,
            }

        cfg: Dict[str, Any] = {
            "category": "river",
            "shape": shape,
            "entry_side": entry,
            "exit_side": exit_side,
            "shape_strength": shape_strength,
            "shape_direction": None,
            "noise_amplitude": noise_amplitude,
            "noise_frequency": noise_frequency,
            "tributary": tributary,
            "seed": rng.randint(1000, 99999),
            "background": str(bg.name) if bg else None,
            "bank_offset": float(bank_offset),
            "bank_variation": float(bank_variation),
        }

        return cfg

    def _random_railway_config(self, rng: random.Random) -> Dict[str, Any]:
        railway_types = sorted(rail_gen.RAILWAY_DIMENSIONS.keys())
        sides = list(rail_gen.HEX_SIDES)

        entry, exit_side = self._pick_entry_exit_with_coverage(rng, prefer_horizontal=True)

        bg = None

        junctions = []
        if rng.random() < 0.35:
            candidates = [s for s in sides if s not in (entry, exit_side)]
            rng.shuffle(candidates)
            for s in candidates:
                if _is_valid_junction(entry, exit_side, s):
                    junctions.append(s)
                if len(junctions) >= rng.choice([1, 2]):
                    break

        railway_type = rng.choice(railway_types)
        junction_double_track = rng.random() < 0.20

        if "jednot" in str(railway_type).lower():
            junction_double_track = False
            if len(junctions) > 1:
                junctions = junctions[:1]

        if len(junctions) > 1 and not junction_double_track:
            if rng.random() < 0.70:
                junctions = junctions[:1]
            else:
                junction_double_track = True

        return {
            "category": "railway",
            "railway_type": railway_type,
            "entry_side": entry,
            "exit_side": exit_side,
            "junctions": junctions,
            "junction_double_track": junction_double_track,
            "seed": rng.randint(1000, 99999),
            "background": str(bg.name) if bg else None,
        }

    def _random_forest_config(self, rng: random.Random) -> Dict[str, Any]:
        densities = ["rzadki", "średni", "gęsty"]
        tree_types = ["mixed", "iglaste", "lisciaste"]
        
        bg = self._pick_background(rng)
        
        return {
            "category": "forest",
            "density": rng.choice(densities),
            "tree_type": rng.choice(tree_types),
            "seed": rng.randint(1000, 99999),
            "background": str(bg.name) if bg else None,
        }

    def _generate_random_hex(self) -> None:
        category = self.current_category.get()
        rng = random.Random()

        if category == "road":
            config = self._random_road_config(rng)
        elif category == "river":
            config = self._random_river_config(rng)
        elif category == "forest":
            config = self._random_forest_config(rng)
        elif category == "lake":
            # Jezioro: wariant 1-heksowy, czasem z odpływem (źródło dopływu)
            bg = None
            use_editor_profiles = bool(self.use_map_editor_profiles.get())
            outflow = None
            if rng.random() < 0.45:
                outflow = rng.choice(list(lake_gen.HEX_SIDES))

            outflow_width = 2.2

            lake_radius = rng.choice(MAP_EDITOR_LAKE_SINGLE_RADII)
            shore_width = 2
            config = {
                "category": "lake",
                "seed": rng.randint(1000, 99999),
                "background": bg,
                "lake_radius": lake_radius,
                "shore_width": shore_width,
                "outflow_side": outflow,
                "outflow_width": outflow_width,
            }
        else:
            config = self._random_railway_config(rng)

        self.current_config = config
        temp_path = self.output_dir / "temp_hex.png"

        try:
            if category == "road":
                bg_path = self.backgrounds_dir / config["background"] if config["background"] else None
                opts = RoadOptions(
                    grid_size=64,
                    background=bg_path,
                    road_type=config["road_type"],
                    entry_side=config["entry_side"],
                    exit_side=config["exit_side"],
                    width=config["width"],
                    noise_amplitude=config.get("noise_amplitude", 0.3),
                    crossroads=(config["crossroads"] or None),
                    neighbor_road_types=config.get("neighbor_road_types"),
                    seed=config["seed"],
                )
                if normalize_road_options:
                    opts, _notes = normalize_road_options(opts)
                generate_road(opts, temp_path)

            elif category == "river":
                bg_path = self.backgrounds_dir / config["background"] if config["background"] else None

                trib = None
                if config.get("tributary"):
                    tcfg = config["tributary"]
                    trib = TributaryOptions(
                        entry_side=tcfg.get("entry_side"),
                        join_ratio=float(tcfg["join_ratio"]),
                        shape=tcfg["shape"],
                        shape_strength=float(tcfg["shape_strength"]),
                        noise_amplitude=float(tcfg["noise_amplitude"]),
                        noise_frequency=float(tcfg["noise_frequency"]),
                        shape_direction_mode=str(tcfg.get("shape_direction_mode") or "auto"),
                        seed_offset=int(tcfg.get("seed_offset", 1_000_000)),
                        bank_offset=tcfg.get("bank_offset"),
                        bank_variation=tcfg.get("bank_variation"),
                    )

                opts = RiverCenterlineOptions(
                    grid_size=64,
                    background=bg_path,
                    entry_side=config["entry_side"],
                    exit_side=config["exit_side"],
                    shape=config["shape"],
                    shape_strength=config["shape_strength"],
                    shape_direction=config["shape_direction"],
                    noise_amplitude=config["noise_amplitude"],
                    noise_frequency=config["noise_frequency"],
                    seed=config["seed"],
                    tributary=trib,
                    bank_offset=float(config.get("bank_offset", river_gen.DEFAULT_BANK_OFFSET)),
                    bank_variation=float(config.get("bank_variation", river_gen.DEFAULT_BANK_VARIATION)),
                )
                generate_centerline(opts, temp_path)

            elif category == "lake":
                bg_path = self.backgrounds_dir / config["background"] if config.get("background") else None
                opts = LakeOptions(
                    grid_size=64,
                    background=bg_path,
                    seed=int(config.get("seed", 1)),
                    lake_radius=float(config.get("lake_radius", 0.34)),
                    shore_width=int(config.get("shore_width", 2)),
                    outflow_side=config.get("outflow_side"),
                    outflow_width=float(config.get("outflow_width", 2.2)),
                )
                generate_lake(opts, temp_path)

            elif config["category"] == "forest":
                bg_path = self.backgrounds_dir / config["background"] if config["background"] else None
                if bg_path and not bg_path.exists():
                    bg_path = self.backgrounds_dir / "flat" / config["background"]
                    if not bg_path.exists():
                        bg_path = None
                
                opts = ForestOptions(
                    density=config["density"],
                    tree_type=config["tree_type"],
                    seed=config["seed"],
                    grid_size=64,
                    background_texture=bg_path,
                )
                generate_forest(opts, temp_path)

            else:
                bg_path = self.backgrounds_dir / config["background"] if config["background"] else None
                opts = RailwayOptions(
                    grid_size=64,
                    background=bg_path,
                    railway_type=config["railway_type"],
                    entry_side=config["entry_side"],
                    exit_side=config["exit_side"],
                    junctions=config["junctions"],
                    junction_double_track=config.get("junction_double_track", False),
                    seed=config["seed"],
                )
                if normalize_railway_options:
                    opts, _notes = normalize_railway_options(opts)
                generate_railway(opts, temp_path)

            img = Image.open(temp_path)
            img_512 = img.resize((512, 512), RESAMPLE_NEAREST)
            img_512 = self._overlay_hex_outline(img_512)
            self.current_image = img_512

            self.current_photo = ImageTk.PhotoImage(img_512)
            self.preview_label.configure(image=self.current_photo)

            self.description_text.delete("1.0", tk.END)

        except Exception as e:
            messagebox.showerror("Błąd generowania", f"Nie udało się wygenerować heksa:\n{e}")

    def _generate_random(self) -> None:
        mode = self.current_mode.get()
        if mode == "cluster7":
            self._generate_random_cluster7()
            return
        self._generate_random_hex()

    def _cluster7_layout(self, tile_size: int = 512) -> Dict[str, tuple[int, int]]:
        radius = tile_size / 2.0
        dx = 1.5 * radius
        dy = math.sqrt(3.0) * radius
        dy_half = dy / 2.0

        centers = {
            "center": (0.0, 0.0),
            "top": (0.0, -dy),
            "bottom": (0.0, dy),
            "top_right": (dx, -dy_half),
            "bottom_right": (dx, dy_half),
            "top_left": (-dx, -dy_half),
            "bottom_left": (-dx, dy_half),
        }

        half = tile_size / 2.0
        min_x = min(cx - half for cx, cy in centers.values())
        min_y = min(cy - half for cx, cy in centers.values())
        max_x = max(cx + half for cx, cy in centers.values())
        max_y = max(cy + half for cx, cy in centers.values())

        margin = 12
        shift_x = -min_x + margin
        shift_y = -min_y + margin

        layout: Dict[str, tuple[int, int]] = {}
        for name, (cx, cy) in centers.items():
            x = int(round(cx - half + shift_x))
            y = int(round(cy - half + shift_y))
            layout[name] = (x, y)

        layout["__canvas_size__"] = (
            int(round((max_x - min_x) + 2 * margin)),
            int(round((max_y - min_y) + 2 * margin)),
        )
        return layout

    def _cluster7_neighbor_map(self) -> Dict[str, Dict[str, str]]:
        coords = {
            "center": (0, 0),
            "top": (0, -1),
            "top_right": (1, -1),
            "bottom_right": (1, 0),
            "bottom": (0, 1),
            "bottom_left": (-1, 1),
            "top_left": (-1, 0),
        }
        directions = {
            "top": (0, -1),
            "top_right": (1, -1),
            "bottom_right": (1, 0),
            "bottom": (0, 1),
            "bottom_left": (-1, 1),
            "top_left": (-1, 0),
        }
        coord_to_name = {coord: name for name, coord in coords.items()}
        neighbor_map: Dict[str, Dict[str, str]] = {name: {} for name in coords}
        for name, (q, r) in coords.items():
            for side, (dq, dr) in directions.items():
                neighbor_name = coord_to_name.get((q + dq, r + dr))
                if neighbor_name:
                    neighbor_map[name][side] = neighbor_name
        return neighbor_map

    def _cluster7_axial_map(self) -> Dict[str, tuple[int, int]]:
        return {
            "center": (0, 0),
            "top": (0, -1),
            "top_right": (1, -1),
            "bottom_right": (1, 0),
            "bottom": (0, 1),
            "bottom_left": (-1, 1),
            "top_left": (-1, 0),
        }

    def _blank_tile(self, background_name: Optional[str]) -> Image.Image:
        if background_name:
            bg_path = self.backgrounds_dir / background_name
            if bg_path.exists():
                img = Image.open(bg_path).convert("RGBA")
                if img.size != (512, 512):
                    img = img.resize((512, 512), RESAMPLE_NEAREST)
                return self._overlay_hex_outline(img)
        return self._overlay_hex_outline(Image.new("RGBA", (512, 512), (0, 0, 0, 0)))

    def _overlay_hex_outline(self, img: Image.Image) -> Image.Image:
        from PIL import ImageDraw

        out = img.convert("RGBA").copy()
        w, h = out.size
        size = float(min(w, h))
        cx = size / 2.0
        cy = size / 2.0
        radius = (size / 2.0) - 0.5
        sqrt3 = math.sqrt(3.0)
        poly = [
            (cx - radius, cy),
            (cx - radius / 2.0, cy - (sqrt3 / 2.0) * radius),
            (cx + radius / 2.0, cy - (sqrt3 / 2.0) * radius),
            (cx + radius, cy),
            (cx + radius / 2.0, cy + (sqrt3 / 2.0) * radius),
            (cx - radius / 2.0, cy + (sqrt3 / 2.0) * radius),
        ]
        draw = ImageDraw.Draw(out)
        draw.line(poly + [poly[0]], fill=(0, 255, 255, 220), width=2, joint="curve")
        return out

    def _opposite_side(self, side: str) -> str:
        return rail_gen.SIDE_OPPOSITE[side]

    # ---- KLASTER 7: plan + render ----

    def _generate_cluster7_plan(self, rng: random.Random, category: str) -> Dict[str, Any]:
        sides = list(rail_gen.HEX_SIDES)
        use_editor_profiles = bool(self.use_map_editor_profiles.get())
        river_cluster_shape_strength: Optional[float] = None
        river_cluster_noise_amp: Optional[float] = None
        river_cluster_noise_freq: Optional[float] = None
        river_bank_offset: float = float(river_gen.DEFAULT_BANK_OFFSET)
        river_bank_variation: float = float(river_gen.DEFAULT_BANK_VARIATION)

        if category == "lake":
            # Układ: center + 2 sąsiady (trójka). Reszta blank.
            # Wersje: bez odpływu (wolne jezioro) / z odpływem (źródło dopływu).
            if use_editor_profiles:
                pattern = rng.choice(["lake3", "lake7", "lake3_source_river"])
            else:
                pattern = rng.choice(["lake3", "lake3_source", "lake3_source_river"])
            bg = self._pick_background(rng)
            base_seed = rng.randint(1000, 99999)

            lake_sides = list(lake_gen.HEX_SIDES)
            if pattern == "lake7":
                neighbors = tuple(lake_sides)
            else:
                # Wybierz 2 sąsiadów jako parę przyległych boków, żeby układ był spójny.
                a = rng.choice(lake_sides)
                ai = lake_sides.index(a)
                b = lake_sides[(ai + 1) % len(lake_sides)]
                neighbors = (a, b)

            tiles: Dict[str, Dict[str, Any]] = {}
            for name in ["center", "top", "top_right", "bottom_right", "bottom", "bottom_left", "top_left"]:
                tiles[name] = {"category": "lake", "background": bg, "seed": base_seed, "blank": True}

            if pattern == "lake7":
                active = ["center", *list(neighbors)]
            else:
                active = ["center", neighbors[0], neighbors[1]]
            outflow_side = None
            if pattern in ("lake3_source", "lake3_source_river"):
                # Odpływ: wybierz bok różny od 2 heksów jeziora, żeby wypływ nie szedł "w jezioro".
                outflow_candidates = [s for s in lake_sides if s not in neighbors]
                outflow_side = rng.choice(outflow_candidates) if outflow_candidates else rng.choice(lake_sides)

            # Dla wariantu z automatyczną rzeką, odpływ powinien mieć sensowną szerokość,
            # żeby łączył się ze standardową szerokością rzeki (bank_offset*GLOBAL_BANK_WIDTH_MULTIPLIER).
            # W pozostałych wariantach zachowujemy węższy, subtelny kanał.
            if pattern == "lake3_source_river":
                outflow_width = 2.2
                shore_width = 2
            else:
                outflow_width = 2.2
                shore_width = 2

            if use_editor_profiles:
                lake_radius = rng.choice(MAP_EDITOR_LAKE_CLUSTER_SCALES)
            else:
                lake_radius = rng.choice(MAP_EDITOR_LAKE_CLUSTER_SCALES)

            for tile_name in active:
                tiles[tile_name] = {
                    "category": "lake",
                    "background": bg,
                    "seed": base_seed,
                    "blank": False,
                    # parametry pola globalnego (spójność na stykach)
                    "cluster_seed": base_seed,
                    "cluster_neighbors": list(neighbors),
                    "cluster_tile": tile_name,
                    "cluster_shape": "y" if pattern != "lake7" else None,
                    # parametry jeziora
                    "lake_radius": lake_radius,
                    "shore_width": shore_width,
                    "outflow_side": outflow_side if tile_name == "center" else None,
                    "outflow_width": outflow_width,
                }

            # Gotowiec: jezioro jako źródło + automatyczna rzeka w sąsiadującym heksie.
            if pattern == "lake3_source_river" and outflow_side:
                river_tile = outflow_side
                entry_side = self._opposite_side(outflow_side)
                # Dopasuj przybliżoną szerokość rzeki do szerokości kanału odpływu.
                # Heurystyka: outflow_width to pełna szerokość kanału w komórkach,
                # a bank_offset w rzece jest mnożony przez GLOBAL_BANK_WIDTH_MULTIPLIER (~3.0).
                # Zakładamy: river_full_width ~ 2*effective_bank_offset.
                bank_offset = max(0.7, float(outflow_width) / 6.0)
                # Prosta kontynuacja na zewnątrz klastra.
                tiles[river_tile] = {
                    "category": "river",
                    "background": bg,
                    "seed": base_seed + 777,
                    "blank": False,
                    "shape": "straight",
                    "entry_side": entry_side,
                    "exit_side": outflow_side,
                    "shape_strength": 0.55,
                    "shape_direction": None,
                    "noise_amplitude": 0.08,
                    "noise_frequency": 0.22,
                    "tributary": None,
                    "bank_offset": bank_offset,
                    "bank_variation": 0.12,
                }

            return {
                "mode": "cluster7",
                "category": "lake",
                "pattern": pattern,
                "background": bg,
                "neighbors": list(neighbors),
                "cluster_seed": base_seed,
                "tiles": tiles,
            }

        if category == "road":
            patterns = ["straight3", "turn3", "horizontal3", "t_junction", "crossroads4"]
        elif category == "river":
            # *_tributary   -> dopływ w centrum + wymuszona kontynuacja w sąsiednim heksie
            # *_tributary_lake -> dopływ w centrum + jezioro w sąsiednim heksie dopływu
            patterns = [
                "straight3",
                "turn3",
                "horizontal3",
                "straight3_tributary",
                "straight3_tributary_lake",
            ]
        else:
            # branch4: dodatkowa odnoga od głównej linii
            patterns = ["straight3", "turn3", "horizontal3", "branch4"]

        pattern = rng.choice(patterns)
        bg = None

        axis_a: Optional[str] = None
        axis_b: Optional[str] = None
        branch_side: Optional[str] = None

        connected: Dict[str, list[str]] = {k: [] for k in ["center", "top", "top_right", "bottom_right", "bottom", "bottom_left", "top_left"]}

        def connect(a: str, side_from_a: str, b: str) -> None:
            connected[a].append(side_from_a)
            connected[b].append(self._opposite_side(side_from_a))

        if pattern == "straight3":
            axis = rng.choice([
                ("top", "bottom"),
                ("top_left", "bottom_right"),
                ("top_right", "bottom_left"),
            ])
            a, b = axis
            axis_a, axis_b = a, b
            connect("center", a, a)
            connect("center", b, b)

        elif pattern == "turn3":
            entry = rng.choice(sides)
            entry_idx = sides.index(entry)
            exit_side = sides[(entry_idx + rng.choice([-1, 1])) % len(sides)]
            axis_a, axis_b = entry, exit_side
            connect("center", entry, entry)
            connect("center", exit_side, exit_side)

        elif pattern == "horizontal3":
            if rng.random() < 0.5:
                left_name, right_name = "top_left", "top_right"
            else:
                left_name, right_name = "bottom_left", "bottom_right"
            axis_a, axis_b = left_name, right_name
            connect("center", left_name, left_name)
            connect("center", right_name, right_name)

        elif pattern in ("branch4", "branch4_buffer", "t_junction", "t_junction_house"):
            axis = rng.choice([
                ("top", "bottom"),
                ("top_left", "bottom_right"),
                ("top_right", "bottom_left"),
            ])
            a, b = axis
            branch = rng.choice([s for s in sides if s not in (a, b)])
            axis_a, axis_b, branch_side = a, b, branch
            connect("center", a, a)
            connect("center", b, b)
            connect("center", branch, branch)

        elif pattern in ("crossroads4",):
            axis = rng.choice([
                ("top", "bottom"),
                ("top_left", "bottom_right"),
                ("top_right", "bottom_left"),
            ])
            a, b = axis
            others = [s for s in sides if s not in (a, b)]
            extra1, extra2 = rng.sample(others, 2)
            axis_a, axis_b = a, b
            connect("center", a, a)
            connect("center", b, b)
            connect("center", extra1, extra1)
            connect("center", extra2, extra2)

        else:
            axis = rng.choice([
                ("top", "bottom"),
                ("top_left", "bottom_right"),
                ("top_right", "bottom_left"),
            ])
            a, b = axis
            axis_a, axis_b = a, b
            connect("center", a, a)
            connect("center", b, b)

        tiles: Dict[str, Dict[str, Any]] = {}
        base_seed = rng.randint(1000, 99999)

        road_cluster_type = None
        road_cluster_width = None
        river_cluster_shape = None
        railway_main_type: Optional[str] = None
        railway_branch_type: Optional[str] = None
        railway_junction_double: Optional[bool] = None

        if category == "road":
            road_cluster_type = rng.choice(sorted(road_gen.ROAD_COLOR_PRESETS.keys()))
            width_keys = sorted(road_gen.ROAD_WIDTH_PRESETS.keys())
            if road_cluster_type == "piaszczysta" and "bardzo_szeroka" in width_keys:
                width_keys = [w for w in width_keys if w != "bardzo_szeroka"]
            road_cluster_width = rng.choice(width_keys)
        elif category == "river":
            if use_editor_profiles:
                curvature_preset = rng.choice(MAP_EDITOR_RIVER_CURVATURE_PRESETS)
                river_cluster_shape = curvature_preset["shape_preference"]
                river_cluster_shape_strength = float(curvature_preset["shape_strength"])
                river_cluster_noise_amp = float(curvature_preset["noise_amplitude"])
                river_cluster_noise_freq = float(curvature_preset["noise_frequency"])
                
                # Losuj też bank parameters z Map Editor presets
                size_preset = rng.choice(MAP_EDITOR_RIVER_SIZE_PRESETS)
                bank_preset = rng.choice(MAP_EDITOR_RIVER_BANK_PRESETS)
                base_offset = size_preset["bank_offset"]
                base_variation = size_preset["bank_variation"]
                river_bank_offset = base_offset * bank_preset["offset_multiplier"]
                river_bank_variation = base_variation * bank_preset["variation_multiplier"] + bank_preset["variation_add"]
            else:
                river_cluster_shape = rng.choice(list(getattr(river_gen, "PATH_SHAPES", ("straight", "curve", "turn"))))
                river_cluster_shape_strength = None
                river_cluster_noise_amp = None
                river_cluster_noise_freq = None
                river_bank_offset = float(river_gen.DEFAULT_BANK_OFFSET) * rng.uniform(0.8, 1.5)
                river_bank_variation = float(river_gen.DEFAULT_BANK_VARIATION) * rng.uniform(0.85, 1.2)
        elif category == "forest":
            # Forest: spójny klaster (wspólna gęstość/typ drzew)
            forest_cluster_density = rng.choice(["rzadki", "średni", "gęsty"])
            forest_cluster_tree_type = rng.choice(["mixed", "iglaste", "lisciaste"])
        else:
            railway_types = sorted(rail_gen.RAILWAY_DIMENSIONS.keys())
            preferred_double = "dwutorowy" if "dwutorowy" in railway_types else None
            preferred_single = "jednotorowy" if "jednotorowy" in railway_types else None

            # Nie faworyzuj zawsze dwutorowego: w przykładach chcemy miks.
            if preferred_double and preferred_single:
                # 55/45 daje lekki bias na główną linię dwutorową, ale wciąż często trafia jednotor.
                railway_main_type = rng.choices([preferred_double, preferred_single], weights=[0.55, 0.45], k=1)[0]
            else:
                railway_main_type = preferred_double or preferred_single or rng.choice(railway_types)

            railway_branch_type = railway_main_type
            railway_junction_double = rng.random() < 0.20

            # Jednotorowy: brak sensu dla double-track rozjazdów.
            if railway_main_type and "jednot" in str(railway_main_type).lower():
                railway_junction_double = False

            # branch4: czasem zrób jednotorową odnogę od dwutorowej linii głównej.
            if pattern == "branch4" and preferred_single and preferred_double:
                if railway_main_type == preferred_double:
                    if rng.random() < 0.70:
                        railway_branch_type = preferred_single
                        railway_junction_double = False
                    else:
                        railway_branch_type = preferred_double
                        railway_junction_double = True

        # --- RIVER: dopływ w centrum musi wymusić sąsiada zanim zbudujemy kafle ---
        tributary_for_center: Optional[Dict[str, Any]] = None
        lake_tile_for_tributary: Optional[str] = None
        if category == "river":
            if use_editor_profiles:
                size_preset = rng.choice(MAP_EDITOR_RIVER_SIZE_PRESETS)
                bank_preset = rng.choice(MAP_EDITOR_RIVER_BANK_PRESETS)
                base_bank_offset = float(size_preset["bank_offset"])
                base_bank_variation = float(size_preset["bank_variation"])
                river_bank_offset = base_bank_offset * float(bank_preset["offset_multiplier"])
                river_bank_variation = max(
                    0.0,
                    base_bank_variation * float(bank_preset["variation_multiplier"])
                    + float(bank_preset["variation_add"]),
                )
            else:
                river_bank_offset = round(rng.uniform(0.6, 3.2), 3)
                river_bank_variation = round(rng.uniform(0.0, 0.8), 3)

            center_sides_used = connected.get("center") or []
            center_entry: Optional[str] = None
            center_exit: Optional[str] = None
            if len(center_sides_used) == 1:
                center_entry = center_sides_used[0]
                center_exit = self._opposite_side(center_entry)
            elif len(center_sides_used) >= 2:
                center_entry, center_exit = center_sides_used[0], center_sides_used[1]

            # Jeżeli pattern wymaga dopływu, musi on istnieć zawsze.
            force_tributary = pattern in ("straight3_tributary", "straight3_tributary_end", "straight3_tributary_lake")
            # W praktyce dopływ jest kluczowy dla testów/QA, więc dajemy mu większą szansę.
            if center_entry and center_exit and (force_tributary or rng.random() < 0.60):
                candidates = [s for s in sides if s not in (center_entry, center_exit)]
                if candidates:
                    trib_entry = rng.choice(candidates)
                    use_source = False
                    trib_size = rng.choice(MAP_EDITOR_TRIBUTARY_SIZE_PRESETS)
                    trib_char = rng.choice(MAP_EDITOR_TRIBUTARY_CHARACTER_PRESETS)
                    tributary_for_center = {
                        "entry_side": None if use_source else trib_entry,
                        # Semantyka: dopływ jako „źródło”/strumień dopływający raczej wcześnie.
                        "join_ratio": round(rng.uniform(river_gen.MIN_TRIBUTARY_JOIN, river_gen.MAX_TRIBUTARY_JOIN), 2),
                        "shape": trib_char["shape"],
                        "shape_strength": float(trib_char["shape_strength"]),
                        "noise_amplitude": float(trib_char["noise_amplitude"]),
                        "noise_frequency": float(trib_char["noise_frequency"]),
                        "shape_direction_mode": trib_char["shape_direction_mode"],
                        "seed_offset": 1_000_000,
                        "bank_offset": max(0.0, river_bank_offset * float(trib_size["bank_offset_scale"])),
                        "bank_variation": max(0.0, river_bank_variation * float(trib_size["variation_scale"])),
                    }

                    # W wariancie *_tributary dopływ ma kontynuację w sąsiadzie.
                    connect("center", trib_entry, trib_entry)

                    # Gotowiec: zamiast rzeki w kaflu dopływu daj jezioro z odpływem w stronę centrum.
                    if pattern == "straight3_tributary_lake" and not use_source:
                        lake_tile_for_tributary = trib_entry

        for name, sides_used in connected.items():
            tile_seed = (base_seed + hash((category, name)) % 100000) % 100000

            if category == "road":
                road_type = road_cluster_type
                width = road_cluster_width
                noise_amp = round(rng.uniform(0.05, 0.45), 3)

                if len(sides_used) == 0:
                    tiles[name] = {"category": "road", "background": bg, "seed": tile_seed, "blank": True}
                    continue
                if len(sides_used) == 1:
                    entry = sides_used[0]
                    # Domyślnie drogi "ciągną się" do krawędzi (łączą z mapą poza klastrem).
                    # Wyjątek: t_junction_house -> odnoga kończy się w heksie domem.
                    dead_end_house = bool(pattern == "t_junction_house" and branch_side and name == branch_side)
                    exit_side = None if dead_end_house else self._opposite_side(entry)
                    crossroads = []
                elif len(sides_used) == 2:
                    entry, exit_side = sides_used[0], sides_used[1]
                    crossroads = []
                else:
                    entry, exit_side = sides_used[0], sides_used[1]
                    crossroads = sides_used[2:]

                opposite = getattr(road_gen, "SIDE_OPPOSITE", {})
                is_straight = bool(opposite) and opposite.get(entry) == exit_side
                is_junction = bool(crossroads)
                if width == "bardzo_szeroka" and (is_junction or not is_straight):
                    width = "szeroka" if "szeroka" in road_gen.ROAD_WIDTH_PRESETS else width

                tiles[name] = {
                    "category": "road",
                    "road_type": road_type,
                    "entry_side": entry,
                    "exit_side": exit_side,
                    "width": width,
                    "noise_amplitude": noise_amp,
                    "crossroads": crossroads,
                    "seed": tile_seed,
                    "background": bg,
                    "endcap_preset": (
                        str((Path(__file__).resolve().parent.parent / "assets" / "terrain" / "presets" / "user_assets" / "settlement" / "dom_1.json"))
                        if (exit_side is None)
                        else None
                    ),
                }

            elif category == "railway":
                if pattern == "branch4" and branch_side and name == branch_side:
                    railway_type = railway_branch_type
                else:
                    railway_type = railway_main_type

                junction_double_track = bool(railway_junction_double)

                if len(sides_used) == 0:
                    tiles[name] = {"category": "railway", "background": bg, "seed": tile_seed, "blank": True}
                    continue
                if len(sides_used) == 1:
                    entry = sides_used[0]
                    # Domyślnie tory też ciągną się do krawędzi.
                    # Wyjątek: branch4_buffer -> odnoga (branch_side) kończy się buforem.
                    dead_end_buffer = bool(pattern == "branch4_buffer" and branch_side and name == branch_side)
                    exit_side = None if dead_end_buffer else self._opposite_side(entry)
                    junctions = []
                elif len(sides_used) == 2:
                    entry, exit_side = sides_used[0], sides_used[1]
                    junctions = []
                else:
                    entry, exit_side = sides_used[0], sides_used[1]
                    junctions = [s for s in sides_used[2:] if _is_valid_junction(entry, exit_side, s)]

                if len(junctions) > 1 and not junction_double_track:
                    if rng.random() < 0.70:
                        junctions = junctions[:1]
                    else:
                        junction_double_track = True

                if "jednot" in str(railway_type).lower():
                    junction_double_track = False
                    if len(junctions) > 1:
                        junctions = junctions[:1]

                tiles[name] = {
                    "category": "railway",
                    "railway_type": railway_type,
                    "entry_side": entry,
                    "exit_side": exit_side,
                    "junctions": junctions,
                    "junction_double_track": junction_double_track,
                    "seed": tile_seed,
                    "background": bg,
                }

            elif category == "forest":
                tiles[name] = {
                    "category": "forest",
                    "density": forest_cluster_density,
                    "tree_type": forest_cluster_tree_type,
                    "seed": tile_seed,
                    "background": bg,
                }

            else:
                shape = river_cluster_shape
                if use_editor_profiles and river_cluster_shape_strength is not None:
                    shape_strength = river_cluster_shape_strength
                    noise_amplitude = river_cluster_noise_amp
                    noise_frequency = river_cluster_noise_freq
                else:
                    shape_strength = round(rng.uniform(0.3, 0.8), 2)
                    noise_amplitude = round(rng.uniform(0.05, 0.15), 3)
                    noise_frequency = round(rng.uniform(0.15, 0.35), 3)

                if len(sides_used) == 0:
                    tiles[name] = {"category": "river", "background": bg, "seed": tile_seed, "blank": True}
                    continue
                if len(sides_used) == 1:
                    entry = sides_used[0]
                    exit_side = self._opposite_side(entry)
                else:
                    entry, exit_side = sides_used[0], sides_used[1]

                tributary = tributary_for_center if name == "center" else None

                tiles[name] = {
                    "category": "river",
                    "shape": shape,
                    "entry_side": entry,
                    "exit_side": exit_side,
                    "shape_strength": shape_strength,
                    "shape_direction": None,
                    "noise_amplitude": noise_amplitude,
                    "noise_frequency": noise_frequency,
                    "tributary": tributary,
                    "seed": tile_seed,
                    "background": bg,
                    "bank_offset": river_bank_offset if category == "river" else None,
                    "bank_variation": river_bank_variation if category == "river" else None,
                }

        # Podmień kafel dopływu na jezioro (jeśli wybrano preset).
        if category == "river" and lake_tile_for_tributary:
            lake_tile = lake_tile_for_tributary
            outflow_to_center = self._opposite_side(lake_tile)
            tiles[lake_tile] = {
                "category": "lake",
                "background": bg,
                "seed": base_seed + 4242,
                "blank": False,
                "lake_radius": round(rng.uniform(0.26, 0.42), 2),
                "shore_width": rng.choice([1, 2, 2, 3]),
                "outflow_side": outflow_to_center,
                "outflow_width": round(rng.uniform(1.8, 2.6), 2),
            }

        return {
            "mode": "cluster7",
            "category": category,
            "pattern": pattern,
            "background": bg,
            "axis": [axis_a, axis_b],
            "branch_side": branch_side,
            "tiles": tiles,
            "forest_density": forest_cluster_density if category == "forest" else None,
            "forest_tree_type": forest_cluster_tree_type if category == "forest" else None,
            "forest_seed": base_seed if category == "forest" else None,
        }

    def _render_cluster7(self, plan: Dict[str, Any]) -> Dict[str, Any]:
        layout = self._cluster7_layout(tile_size=512)
        canvas_w, canvas_h = layout["__canvas_size__"]
        mosaic = Image.new("RGBA", (canvas_w, canvas_h), (0, 0, 0, 0))

        tiles_out: Dict[str, Dict[str, Any]] = {}
        bg_name = plan.get("background")

        neighbor_map = self._cluster7_neighbor_map() if plan.get("category") == "road" else {}

        tmp_dir = self.output_dir / "_tmp"
        tmp_dir.mkdir(exist_ok=True)

        forest_cluster_outputs: Dict[str, Path] | None = None
        if plan.get("category") == "forest" and generate_forest_cluster:
            axial_map = self._cluster7_axial_map()
            hex_ids: list[str] = []
            output_paths: Dict[str, Path] = {}
            background_textures: Dict[str, Optional[Path]] = {}

            for name, cfg in plan["tiles"].items():
                if cfg.get("blank"):
                    continue
                q, r = axial_map.get(name, (0, 0))
                hex_id = f"{q},{r}"
                hex_ids.append(hex_id)
                bg_path = self.backgrounds_dir / cfg["background"] if cfg.get("background") else None
                background_textures[hex_id] = bg_path
                output_paths[hex_id] = tmp_dir / f"forest_{name}.png"

            if hex_ids:
                density = plan.get("forest_density") or "średni"
                tree_type = plan.get("forest_tree_type") or "mixed"
                seed = int(plan.get("forest_seed") or 1)
                generate_forest_cluster(
                    hex_ids,
                    grid_size=64,
                    density=str(density),
                    seed=seed,
                    tree_type=str(tree_type),
                    background_textures=background_textures,
                    output_paths=output_paths,
                )
                forest_cluster_outputs = {
                    name: output_paths[f"{axial_map[name][0]},{axial_map[name][1]}"]
                    for name in plan["tiles"].keys()
                    if name in axial_map and f"{axial_map[name][0]},{axial_map[name][1]}" in output_paths
                }

        for name, cfg in plan["tiles"].items():
            if cfg.get("blank"):
                tile_img = self._blank_tile(bg_name)
            else:
                category = cfg["category"]
                temp_path = tmp_dir / f"{category}_{name}.png"
                bg_path = self.backgrounds_dir / cfg["background"] if cfg.get("background") else None

                if category == "forest" and forest_cluster_outputs and name in forest_cluster_outputs:
                    tile_img = Image.open(forest_cluster_outputs[name]).convert("RGBA")
                    if tile_img.size != (512, 512):
                        tile_img = tile_img.resize((512, 512), RESAMPLE_NEAREST)
                    tile_img = self._overlay_hex_outline(tile_img)
                    x, y = layout[name]
                    mosaic.alpha_composite(tile_img, (x, y))
                    tiles_out[name] = {
                        "config": cfg,
                        "image": tile_img,
                        "pos": (x, y),
                    }
                    continue

                if category == "road":
                    neighbor_road_types: Optional[Dict[str, str]] = None
                    if neighbor_map:
                        neighbors_for_tile = neighbor_map.get(name, {})
                        if neighbors_for_tile:
                            neighbor_road_types = {}
                            for side, neighbor_name in neighbors_for_tile.items():
                                neighbor_cfg = plan["tiles"].get(neighbor_name, {})
                                if neighbor_cfg.get("category") == "road" and not neighbor_cfg.get("blank"):
                                    n_type = neighbor_cfg.get("road_type")
                                    if n_type:
                                        neighbor_road_types[side] = n_type
                            if not neighbor_road_types:
                                neighbor_road_types = None

                    opts = RoadOptions(
                        grid_size=64,
                        background=bg_path,
                        road_type=cfg["road_type"],
                        entry_side=cfg["entry_side"],
                        exit_side=cfg["exit_side"],
                        width=cfg["width"],
                        noise_amplitude=float(cfg.get("noise_amplitude", 0.3)),
                        crossroads=(cfg.get("crossroads") or None),
                        neighbor_road_types=neighbor_road_types,
                        endcap_preset=(Path(cfg["endcap_preset"]) if cfg.get("endcap_preset") else None),
                        seed=int(cfg["seed"]),
                    )
                    if normalize_road_options:
                        opts, _notes = normalize_road_options(opts)
                    generate_road(opts, temp_path)
                elif category == "railway":
                    opts = RailwayOptions(
                        grid_size=64,
                        background=bg_path,
                        railway_type=cfg["railway_type"],
                        entry_side=cfg["entry_side"],
                        exit_side=cfg["exit_side"],
                        junctions=cfg.get("junctions", []),
                        junction_double_track=bool(cfg.get("junction_double_track", False)),
                        seed=int(cfg["seed"]),
                    )
                    if normalize_railway_options:
                        opts, _notes = normalize_railway_options(opts)
                    generate_railway(opts, temp_path)
                elif category == "river":
                    trib = None
                    if cfg.get("tributary"):
                        tcfg = cfg["tributary"]
                        trib = TributaryOptions(
                            entry_side=tcfg.get("entry_side"),
                            join_ratio=float(tcfg["join_ratio"]),
                            shape=tcfg["shape"],
                            shape_strength=float(tcfg["shape_strength"]),
                            noise_amplitude=float(tcfg["noise_amplitude"]),
                            noise_frequency=float(tcfg["noise_frequency"]),
                            shape_direction_mode=str(tcfg.get("shape_direction_mode") or "auto"),
                            seed_offset=int(tcfg.get("seed_offset", 1_000_000)),
                            bank_offset=tcfg.get("bank_offset"),
                            bank_variation=tcfg.get("bank_variation"),
                        )
                    opts = RiverCenterlineOptions(
                        grid_size=64,
                        background=bg_path,
                        entry_side=cfg["entry_side"],
                        exit_side=cfg["exit_side"],
                        shape=cfg["shape"],
                        shape_strength=float(cfg["shape_strength"]),
                        shape_direction=None,
                        noise_amplitude=float(cfg["noise_amplitude"]),
                        noise_frequency=float(cfg["noise_frequency"]),
                        seed=int(cfg["seed"]),
                        tributary=trib,
                        bank_offset=float(cfg["bank_offset"]) if cfg.get("bank_offset") is not None else 1.5,
                        bank_variation=float(cfg["bank_variation"]) if cfg.get("bank_variation") is not None else 0.35,
                    )
                    generate_centerline(opts, temp_path)

                elif category == "lake":
                    opts = LakeOptions(
                        grid_size=64,
                        background=bg_path,
                        seed=int(cfg.get("seed", 1)),
                        lake_radius=float(cfg.get("lake_radius", 0.34)),
                        shore_width=int(cfg.get("shore_width", 2)),
                        outflow_side=cfg.get("outflow_side"),
                        outflow_width=float(cfg.get("outflow_width", 2.2)),
                        cluster_seed=(int(cfg["cluster_seed"]) if cfg.get("cluster_seed") is not None else None),
                        cluster_neighbors=(
                            tuple(cfg.get("cluster_neighbors"))  # type: ignore[arg-type]
                            if cfg.get("cluster_neighbors")
                            else None
                        ),
                        cluster_tile=str(cfg.get("cluster_tile")) if cfg.get("cluster_tile") else None,
                        cluster_shape=str(cfg.get("cluster_shape")) if cfg.get("cluster_shape") else None,
                    )
                    generate_lake(opts, temp_path)
                elif category == "forest":
                    opts = ForestOptions(
                        density=cfg["density"],
                        tree_type=cfg["tree_type"],
                        seed=int(cfg["seed"]),
                        grid_size=64,
                        background_texture=bg_path,
                    )
                    generate_forest(opts, temp_path)
                else:
                    raise ValueError(f"Nieznana kategoria: {category!r}")

                tile_img = Image.open(temp_path).convert("RGBA")
                if tile_img.size != (512, 512):
                    tile_img = tile_img.resize((512, 512), RESAMPLE_NEAREST)
                tile_img = self._overlay_hex_outline(tile_img)

            x, y = layout[name]
            mosaic.alpha_composite(tile_img, (x, y))

            tiles_out[name] = {
                "config": cfg,
                "image": tile_img,
                "pos": (x, y),
            }

        return {
            "plan": plan,
            "layout": layout,
            "mosaic": mosaic,
            "tiles": tiles_out,
        }

    def _generate_random_cluster7(self) -> None:
        category = self.current_category.get()
        rng = random.Random()
        plan = self._generate_cluster7_plan(rng, category)
        rendered = self._render_cluster7(plan)

        mosaic: Image.Image = rendered["mosaic"]
        self.current_cluster = rendered
        self.current_config = plan
        self.current_image = mosaic

        w, h = mosaic.size
        scale = 512 / max(w, h)
        preview = mosaic.resize((int(round(w * scale)), int(round(h * scale))), RESAMPLE_NEAREST)

        canvas = Image.new("RGBA", (512, 512), (0, 0, 0, 255))
        px = (512 - preview.size[0]) // 2
        py = (512 - preview.size[1]) // 2
        canvas.alpha_composite(preview, (px, py))

        self.current_photo = ImageTk.PhotoImage(canvas)
        self.preview_label.configure(image=self.current_photo)
        self.description_text.delete("1.0", tk.END)
        self.description_text.insert(
            tk.END,
            "Wylosowano klaster 7 (1+6).\n"
            f"Kategoria: {plan.get('category')}\n"
            f"Pattern: {plan.get('pattern')}\n"
            "Kliknij heks w mozaice, aby podejrzeć jego PNG i konfigurację.\n",
        )

    def _on_preview_click(self, event) -> None:
        if self.current_mode.get() != "cluster7" or not self.current_cluster:
            return

        mosaic: Image.Image = self.current_cluster["mosaic"]
        w, h = mosaic.size
        scale = 512 / max(w, h)
        preview_w = int(round(w * scale))
        preview_h = int(round(h * scale))
        offset_x = (512 - preview_w) // 2
        offset_y = (512 - preview_h) // 2

        mx = (event.x - offset_x) / scale
        my = (event.y - offset_y) / scale

        if mx < 0 or my < 0 or mx >= w or my >= h:
            return

        hit_name = None
        for name, tinfo in self.current_cluster["tiles"].items():
            x0, y0 = tinfo["pos"]
            lx = int(mx - x0)
            ly = int(my - y0)
            if 0 <= lx < 512 and 0 <= ly < 512:
                if tinfo["image"].getpixel((lx, ly))[3] > 0:
                    hit_name = name
                    break

        if not hit_name:
            return

        self._open_tile_detail(hit_name)

    def _open_tile_detail(self, tile_name: str) -> None:
        if not self.current_cluster:
            return
        tinfo = self.current_cluster["tiles"].get(tile_name)
        if not tinfo:
            return

        win = tk.Toplevel(self.root)
        win.title(f"Hex Detail: {tile_name}")
        win.configure(bg="#1e1e1e")

        img = tinfo["image"]
        photo = ImageTk.PhotoImage(img)
        lbl = tk.Label(win, image=photo, bg="#1e1e1e")
        lbl._photo = photo  # type: ignore[attr-defined]
        lbl.pack(padx=10, pady=10)

        txt = scrolledtext.ScrolledText(win, height=12, font=("Consolas", 9), bg="#2d2d2d", fg="#ddd")
        txt.pack(fill=tk.BOTH, expand=True, padx=10, pady=(0, 10))
        txt.insert(tk.END, json.dumps(tinfo["config"], indent=2, ensure_ascii=False))
        txt.configure(state=tk.DISABLED)

    def _export_package(self) -> None:
        if not self.current_config or not self.current_image:
            messagebox.showwarning("Brak danych", "Najpierw wygeneruj heks!")
            return

        description = self.description_text.get("1.0", tk.END).strip()
        if not description:
            if not messagebox.askyesno("Brak opisu", "Nie opisałeś błędu. Wyeksportować bez opisu?"):
                return

        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        fix_id = f"{timestamp}_{uuid.uuid4().hex[:8]}"
        save_path = self.output_dir / timestamp
        save_path.mkdir(exist_ok=True)
        self.last_export_dir = save_path

        if self.current_mode.get() == "cluster7" and self.current_cluster:
            mosaic_file = save_path / "cluster_preview.png"
            self.current_cluster["mosaic"].save(mosaic_file)

            tiles_dir = save_path / "tiles"
            tiles_dir.mkdir(exist_ok=True)
            for name, tinfo in self.current_cluster["tiles"].items():
                tinfo["image"].save(tiles_dir / f"{name}.png")
        else:
            png_file = save_path / "hex_problem.png"
            self.current_image.save(png_file)

        json_file = save_path / "hex_config.json"
        with open(json_file, "w", encoding="utf-8") as f:
            json.dump(self.current_config, f, indent=2, ensure_ascii=False)

        txt_file = save_path / "problem_report.txt"
        config = self.current_config

        if config.get("mode") == "cluster7":
            report_lines = [
                "=== PROBLEM (KLASTER 7) ===",
                "",
                f"Kategoria: {config.get('category')}",
                "Tryb: cluster7 (1+6)",
                f"Pattern: {config.get('pattern')}",
                f"Tło: {config.get('background') or 'brak'}",
                "",
                "KAFLE:",
            ]

            tiles = config.get("tiles", {})
            for name, tcfg in tiles.items():
                if tcfg.get("blank"):
                    report_lines.append(f"- {name}: blank")
                else:
                    cat = tcfg.get("category")
                    if cat == "road":
                        report_lines.append(
                            f"- {name}: road_type={tcfg.get('road_type')}, "
                            f"entry={tcfg.get('entry_side')} -> exit={tcfg.get('exit_side')}, "
                            f"width={tcfg.get('width')}, crossroads={tcfg.get('crossroads') or []}, seed={tcfg.get('seed')}"
                        )
                    elif cat == "river":
                        report_lines.append(
                            f"- {name}: shape={tcfg.get('shape')}, "
                            f"entry={tcfg.get('entry_side')} -> exit={tcfg.get('exit_side')}, "
                            f"tributary={'Tak' if tcfg.get('tributary') else 'Nie'}, seed={tcfg.get('seed')}"
                        )
                    else:
                        report_lines.append(
                            f"- {name}: railway_type={tcfg.get('railway_type')}, "
                            f"entry={tcfg.get('entry_side')} -> exit={tcfg.get('exit_side')}, "
                            f"junctions={tcfg.get('junctions') or []}, double={'Tak' if tcfg.get('junction_double_track') else 'Nie'}, seed={tcfg.get('seed')}"
                        )

            report_lines.extend(
                [
                    "",
                    "OPIS PROBLEMU:",
                    description if description else "(brak opisu)",
                    "",
                    "KONFIGURACJA JSON:",
                    json.dumps(config, indent=2, ensure_ascii=False),
                    "",
                    f"Wygenerowano: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
                ]
            )
        else:
            report_lines = [
                "=== PROBLEM Z HEKSEM ===",
                "",
                f"Kategoria: {config['category']}",
            ]

            if config["category"] == "road":
                report_lines.extend(
                    [
                        f"Typ drogi: {config['road_type']}",
                        f"Połączenie: {config['entry_side']} -> {config['exit_side']}",
                        f"Szerokość: {config['width']}",
                        f"Skrzyżowania (boki): {', '.join(config.get('crossroads') or []) or 'brak'}",
                    ]
                )
            elif config["category"] == "river":
                report_lines.extend(
                    [
                        f"Kształt: {config['shape']}",
                        f"Połączenie: {config['entry_side']} -> {config['exit_side']}",
                        f"Siła kształtu: {config['shape_strength']}",
                        f"Amplituda szumu: {config['noise_amplitude']}",
                        f"Częstotliwość szumu: {config['noise_frequency']}",
                        f"Dopływ: {'Tak' if config.get('tributary') else 'Nie'}",
                    ]
                )
            else:
                report_lines.extend(
                    [
                        f"Typ: {config['railway_type']}",
                        f"Połączenie: {config['entry_side']} -> {config['exit_side']}",
                        f"Rozjazdy: {len(config['junctions'])}",
                        f"Rozjazdy dwutorowe: {'Tak' if config.get('junction_double_track') else 'Nie'}",
                    ]
                )

            report_lines.extend(
                [
                    f"Seed: {config['seed']}",
                    f"Tło: {config['background'] or 'brak'}",
                    "",
                    "OPIS PROBLEMU:",
                    description if description else "(brak opisu)",
                    "",
                    "KONFIGURACJA JSON:",
                    json.dumps(config, indent=2, ensure_ascii=False),
                    "",
                    f"Wygenerowano: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
                ]
            )

        with open(txt_file, "w", encoding="utf-8") as f:
            f.write("\n".join(report_lines))

        self._append_fix_queue_entry(
            fix_id=fix_id,
            export_dir=save_path,
            config=self.current_config,
            description=description,
        )

        messagebox.showinfo(
            "Pakiet wyeksportowany",
            f"Zapisano w:\n{save_path}\n\n"
            f"Fix ID: {fix_id}\n"
            f"Kolejka fixów: {self.fix_queue_path}\n\n"
            f"📁 Pliki:\n"
            f"• {'cluster_preview.png + tiles/' if config.get('mode') == 'cluster7' else 'hex_problem.png'}\n"
            f"• problem_report.txt\n"
            f"• hex_config.json\n\n"
            f"Wklej problem_report.txt w czat i załącz {'cluster_preview.png' if config.get('mode') == 'cluster7' else 'hex_problem.png'}",
        )

    def _find_latest_export_dir(self) -> Optional[Path]:
        if not self.output_dir.exists():
            return None
        export_folders = [d for d in self.output_dir.iterdir() if d.is_dir()]
        if not export_folders:
            return None
        export_folders.sort(key=lambda p: p.stat().st_mtime, reverse=True)
        return export_folders[0]

    def _open_path(self, path: Path) -> None:
        if sys.platform.startswith("win"):
            os.startfile(str(path))  # type: ignore[attr-defined]
            return
        if sys.platform == "darwin":
            subprocess.run(["open", str(path)], check=False)
            return
        subprocess.run(["xdg-open", str(path)], check=False)

    def _open_last_export(self) -> None:
        export_dir = self.last_export_dir if self.last_export_dir and self.last_export_dir.exists() else self._find_latest_export_dir()
        if not export_dir:
            messagebox.showinfo("Brak eksportów", "Nie znaleziono żadnego folderu eksportu.")
            return
        try:
            preview_path = None
            for candidate in ["cluster_preview.png", "hex_problem.png"]:
                cand = export_dir / candidate
                if cand.exists():
                    preview_path = cand
                    break
            if preview_path is None:
                tiles_dir = export_dir / "tiles"
                if tiles_dir.exists():
                    for name in ["center.png", "top.png", "top_right.png", "bottom_right.png", "bottom.png", "bottom_left.png", "top_left.png"]:
                        cand = tiles_dir / name
                        if cand.exists():
                            preview_path = cand
                            break
                if preview_path is None:
                    pngs = sorted(export_dir.glob("*.png"), key=lambda p: p.stat().st_mtime, reverse=True)
                    if pngs:
                        preview_path = pngs[0]
            if preview_path is not None:
                self._show_preview_window(preview_path)
            self._restore_state_from_export(export_dir)
        except Exception as e:
            messagebox.showerror("Błąd", f"Nie udało się otworzyć folderu:\n{export_dir}\n\n{e}")

    def _clear_exports(self) -> None:
        if not self.output_dir.exists():
            messagebox.showinfo("Brak danych", "Folder eksportów jest pusty.")
            return

        export_folders = [d for d in self.output_dir.iterdir() if d.is_dir()]
        if not export_folders:
            messagebox.showinfo("Brak danych", "Folder eksportów jest pusty.")
            return

        if not messagebox.askyesno(
            "Potwierdzenie",
            f"Znaleziono {len(export_folders)} eksportów.\n\nCzy na pewno usunąć wszystkie?",
        ):
            return

        import shutil

        deleted = 0
        for folder in export_folders:
            try:
                shutil.rmtree(folder)
                deleted += 1
            except Exception as e:
                print(f"Błąd usuwania {folder}: {e}")

        messagebox.showinfo("Wyczyszczono", f"Usunięto {deleted} folderów z eksportami.")


def main() -> None:
    root = tk.Tk()
    root.configure(bg="#1e1e1e")
    HexInspector(root)
    root.mainloop()


if __name__ == "__main__":
    main()
