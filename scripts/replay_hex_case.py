#!/usr/bin/env python3
"""Replay zapisanych przypadków heksów/klastrów.

Cel: szybka pętla "repro -> poprawka w generatorze -> repro" bez klikania w GUI.

Obsługuje dwa formaty wejścia:
- eksport z Hex Inspectora: hex_config.json (single albo cluster7)
- paczka faila fuzzera: case.json (single)

Wynik zapisuje do edytory/_hex_inspector_output/replay_YYYYMMDD_HHMMSS/.
"""

from __future__ import annotations

import argparse
import json
import math
import os
import sys
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, Optional, Tuple

from PIL import Image


PROJEKT_ROOT = Path(__file__).resolve().parent.parent
EDYTORY_DIR = PROJEKT_ROOT / "edytory"
BACKGROUNDS_DIR = PROJEKT_ROOT / "assets" / "terrain" / "hex_painted"
OUT_ROOT = EDYTORY_DIR / "_hex_inspector_output"

# importy generatorów z edytory/
sys.path.insert(0, str(EDYTORY_DIR))

import generate_road_hex_tile as road_gen  # noqa: E402
import generate_railway_hex_tile as rail_gen  # noqa: E402
import generate_river_hex_tile as river_gen  # noqa: E402
import generate_lake_hex_tile as lake_gen  # noqa: E402


def _ensure_dir(p: Path) -> None:
    p.mkdir(parents=True, exist_ok=True)


def _open_path(path: Path) -> None:
    if sys.platform.startswith("win"):
        os.startfile(str(path))  # type: ignore[attr-defined]
        return
    if sys.platform == "darwin":
        import subprocess

        subprocess.run(["open", str(path)], check=False)
        return
    import subprocess

    subprocess.run(["xdg-open", str(path)], check=False)


def _read_json(path: Path) -> Dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def _coerce_background(v: Any) -> Optional[Path]:
    if not v:
        return None
    # Inspector zapisuje tylko nazwę pliku tła
    p = BACKGROUNDS_DIR / str(v)
    return p if p.exists() else None


def _overlay_hex_outline(img: Image.Image, color=(0, 255, 255, 220), width: int = 2) -> Image.Image:
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
    draw.line(poly + [poly[0]], fill=color, width=width, joint="curve")
    return out


def _cluster7_layout(tile_size: int = 512) -> Dict[str, Tuple[int, int]]:
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

    layout: Dict[str, Tuple[int, int]] = {}
    for name, (cx, cy) in centers.items():
        x = int(round(cx - half + shift_x))
        y = int(round(cy - half + shift_y))
        layout[name] = (x, y)

    layout["__canvas_size__"] = (
        int(round((max_x - min_x) + 2 * margin)),
        int(round((max_y - min_y) + 2 * margin)),
    )
    return layout


def _blank_tile(background_name: Optional[str], add_outline: bool) -> Image.Image:
    if background_name:
        bg = BACKGROUNDS_DIR / background_name
        if bg.exists():
            img = Image.open(bg).convert("RGBA")
            if img.size != (512, 512):
                img = img.resize((512, 512), Image.NEAREST)
            return _overlay_hex_outline(img) if add_outline else img
    img = Image.new("RGBA", (512, 512), (0, 0, 0, 0))
    return _overlay_hex_outline(img) if add_outline else img


def _render_single_from_inspector(cfg: Dict[str, Any], out_dir: Path, add_outline: bool) -> Path:
    category = cfg.get("category")
    tmp = out_dir / "_tmp"
    _ensure_dir(tmp)

    bg_path = _coerce_background(cfg.get("background"))

    if category == "road":
        opts = road_gen.RoadOptions(
            grid_size=64,
            background=bg_path,
            road_type=cfg["road_type"],
            entry_side=cfg["entry_side"],
            exit_side=cfg.get("exit_side"),
            width=cfg["width"],
            noise_amplitude=float(cfg.get("noise_amplitude", 0.3)),
            crossroads=(cfg.get("crossroads") or None),
            endcap_preset=(Path(cfg["endcap_preset"]) if cfg.get("endcap_preset") else None),
            seed=int(cfg.get("seed", 1)),
        )
        out_png = out_dir / "replay_road.png"
        road_gen.generate_road(opts, out_png)

    elif category == "railway":
        opts = rail_gen.RailwayOptions(
            grid_size=64,
            background=bg_path,
            railway_type=cfg["railway_type"],
            entry_side=cfg["entry_side"],
            exit_side=cfg.get("exit_side"),
            junctions=list(cfg.get("junctions") or []),
            junction_double_track=bool(cfg.get("junction_double_track", False)),
            seed=int(cfg.get("seed", 1)),
        )
        out_png = out_dir / "replay_railway.png"
        rail_gen.generate_railway(opts, out_png)

    elif category == "river":
        def _coerce_side(value: Any) -> str | None:
            if value is None:
                return None
            if isinstance(value, str) and value.strip().lower() in {"none", "null"}:
                return None
            return str(value)

        def _coerce_side(value: Any) -> str | None:
            if value is None:
                return None
            if isinstance(value, str) and value.strip().lower() in {"none", "null"}:
                return None
            return str(value)

        trib = None
        if cfg.get("tributary"):
            t = cfg["tributary"]
            trib = river_gen.TributaryOptions(
                entry_side=_coerce_side(t.get("entry_side")),
                join_ratio=float(t["join_ratio"]),
                shape=t["shape"],
                shape_strength=float(t["shape_strength"]),
                noise_amplitude=float(t["noise_amplitude"]),
                noise_frequency=float(t["noise_frequency"]),
                shape_direction_mode=str(t.get("shape_direction_mode", "auto")),
            )
        opts = river_gen.RiverCenterlineOptions(
            grid_size=64,
            background=bg_path,
            entry_side=_coerce_side(cfg.get("entry_side")),
            exit_side=_coerce_side(cfg.get("exit_side")),
            shape=cfg["shape"],
            shape_strength=float(cfg["shape_strength"]),
            shape_direction=cfg.get("shape_direction"),
            noise_amplitude=float(cfg["noise_amplitude"]),
            noise_frequency=float(cfg["noise_frequency"]),
            seed=int(cfg.get("seed", 1)),
            tributary=trib,
        )
        out_png = out_dir / "replay_river.png"
        river_gen.generate_centerline(opts, out_png)

    elif category == "lake":
        opts = lake_gen.LakeOptions(
            grid_size=64,
            background=bg_path,
            seed=int(cfg.get("seed", 1)),
            lake_radius=float(cfg.get("lake_radius", 0.34)),
            shore_width=int(cfg.get("shore_width", 2)),
            outflow_side=(cfg.get("outflow_side") or None),
            outflow_width=float(cfg.get("outflow_width", 2.2)),
            cluster_seed=(int(cfg["cluster_seed"]) if cfg.get("cluster_seed") is not None else None),
            cluster_neighbors=(
                tuple(cfg.get("cluster_neighbors"))  # type: ignore[arg-type]
                if cfg.get("cluster_neighbors")
                else None
            ),
            cluster_tile=str(cfg.get("cluster_tile")) if cfg.get("cluster_tile") else None,
        )
        out_png = out_dir / "replay_lake.png"
        lake_gen.generate_lake(opts, out_png)

    else:
        raise ValueError(f"Nieznana kategoria: {category!r}")

    if add_outline:
        img = Image.open(out_png).convert("RGBA")
        img = _overlay_hex_outline(img)
        img.save(out_dir / "preview.png")
    return out_png


def _render_single_from_fuzzer_case(case: Dict[str, Any], out_dir: Path, add_outline: bool) -> Path:
    category = case.get("category")
    opts_d = dict(case.get("options") or {})

    if category == "road":
        opts = road_gen.RoadOptions(**opts_d)
        out_png = out_dir / "replay_road.png"
        road_gen.generate_road(opts, out_png)

    elif category == "railway":
        opts = rail_gen.RailwayOptions(**opts_d)
        out_png = out_dir / "replay_railway.png"
        rail_gen.generate_railway(opts, out_png)

    elif category == "river":
        # tributary w asdict() jest dict albo None
        if isinstance(opts_d.get("tributary"), dict):
            opts_d["tributary"] = river_gen.TributaryOptions(**opts_d["tributary"])
        opts = river_gen.RiverCenterlineOptions(**opts_d)
        out_png = out_dir / "replay_river.png"
        river_gen.generate_centerline(opts, out_png)

    elif category == "lake":
        opts = lake_gen.LakeOptions(**opts_d)
        out_png = out_dir / "replay_lake.png"
        lake_gen.generate_lake(opts, out_png)

    else:
        raise ValueError(f"Nieznana kategoria: {category!r}")

    if add_outline:
        img = Image.open(out_png).convert("RGBA")
        img = _overlay_hex_outline(img)
        img.save(out_dir / "preview.png")
    return out_png


def _render_cluster7(plan: Dict[str, Any], out_dir: Path, add_outline: bool) -> Path:
    layout = _cluster7_layout(tile_size=512)
    canvas_w, canvas_h = layout["__canvas_size__"]
    mosaic = Image.new("RGBA", (canvas_w, canvas_h), (0, 0, 0, 0))

    tiles_dir = out_dir / "tiles"
    tmp_dir = out_dir / "_tmp"
    _ensure_dir(tiles_dir)
    _ensure_dir(tmp_dir)

    bg_name = plan.get("background")

    def _coerce_side(value: Any) -> str | None:
        if value is None:
            return None
        if isinstance(value, str) and value.strip().lower() in {"none", "null"}:
            return None
        return str(value)

    for name, cfg in (plan.get("tiles") or {}).items():
        if cfg.get("blank"):
            tile = _blank_tile(bg_name, add_outline)
        else:
            category = cfg["category"]
            bg_path = _coerce_background(cfg.get("background"))
            temp_path = tmp_dir / f"{category}_{name}.png"

            if category == "road":
                opts = road_gen.RoadOptions(
                    grid_size=64,
                    background=bg_path,
                    road_type=cfg["road_type"],
                    entry_side=cfg["entry_side"],
                    exit_side=cfg["exit_side"],
                    width=cfg["width"],
                    noise_amplitude=float(cfg.get("noise_amplitude", 0.3)),
                    crossroads=(cfg.get("crossroads") or None),
                    seed=int(cfg.get("seed", 1)),
                )
                road_gen.generate_road(opts, temp_path)
            elif category == "railway":
                opts = rail_gen.RailwayOptions(
                    grid_size=64,
                    background=bg_path,
                    railway_type=cfg["railway_type"],
                    entry_side=cfg["entry_side"],
                    exit_side=cfg["exit_side"],
                    junctions=list(cfg.get("junctions") or []),
                    junction_double_track=bool(cfg.get("junction_double_track", False)),
                    seed=int(cfg.get("seed", 1)),
                )
                rail_gen.generate_railway(opts, temp_path)
            elif category == "river":
                trib = None
                if cfg.get("tributary"):
                    t = cfg["tributary"]
                    trib = river_gen.TributaryOptions(
                        entry_side=_coerce_side(t.get("entry_side")),
                        join_ratio=float(t["join_ratio"]),
                        shape=t["shape"],
                        shape_strength=float(t["shape_strength"]),
                        noise_amplitude=float(t["noise_amplitude"]),
                        noise_frequency=float(t["noise_frequency"]),
                        shape_direction_mode=str(t.get("shape_direction_mode", "auto")),
                    )
                opts = river_gen.RiverCenterlineOptions(
                    grid_size=64,
                    background=bg_path,
                    entry_side=_coerce_side(cfg.get("entry_side")),
                    exit_side=_coerce_side(cfg.get("exit_side")),
                    shape=cfg["shape"],
                    shape_strength=float(cfg["shape_strength"]),
                    shape_direction=cfg.get("shape_direction"),
                    noise_amplitude=float(cfg["noise_amplitude"]),
                    noise_frequency=float(cfg["noise_frequency"]),
                    seed=int(cfg.get("seed", 1)),
                    tributary=trib,
                    bank_offset=float(cfg.get("bank_offset", river_gen.DEFAULT_BANK_OFFSET)),
                    bank_variation=float(cfg.get("bank_variation", river_gen.DEFAULT_BANK_VARIATION)),
                    bank_prune_radius=int(cfg.get("bank_prune_radius", 0)),
                )
                river_gen.generate_centerline(opts, temp_path)
            elif category == "lake":
                opts = lake_gen.LakeOptions(
                    grid_size=64,
                    background=bg_path,
                    seed=int(cfg.get("seed", 1)),
                    lake_radius=float(cfg.get("lake_radius", 0.34)),
                    shore_width=int(cfg.get("shore_width", 2)),
                    outflow_side=(cfg.get("outflow_side") or None),
                    outflow_width=float(cfg.get("outflow_width", 2.2)),
                    cluster_seed=(int(cfg["cluster_seed"]) if cfg.get("cluster_seed") is not None else None),
                    cluster_neighbors=(
                        tuple(cfg.get("cluster_neighbors"))  # type: ignore[arg-type]
                        if cfg.get("cluster_neighbors")
                        else None
                    ),
                    cluster_tile=str(cfg.get("cluster_tile")) if cfg.get("cluster_tile") else None,
                )
                lake_gen.generate_lake(opts, temp_path)
            else:
                raise ValueError(f"Nieznana kategoria w klastrze: {category!r}")

            tile = Image.open(temp_path).convert("RGBA")
            if tile.size != (512, 512):
                tile = tile.resize((512, 512), Image.NEAREST)
            if add_outline:
                tile = _overlay_hex_outline(tile)

        tile.save(tiles_dir / f"{name}.png")
        x, y = layout[name]
        mosaic.alpha_composite(tile, (x, y))

    mosaic_path = out_dir / "cluster_preview.png"
    mosaic.save(mosaic_path)
    if add_outline:
        _overlay_hex_outline(mosaic).save(out_dir / "preview.png")
    return mosaic_path


def main(argv: Optional[list[str]] = None) -> int:
    p = argparse.ArgumentParser(description="Replay zapisanych przypadków heksów/klastrów (Hex Inspector / fuzzer).")
    p.add_argument("--config", type=str, help="Ścieżka do hex_config.json z eksportu Hex Inspectora")
    p.add_argument("--case", type=str, help="Ścieżka do case.json z paczki faila fuzzera")
    p.add_argument("--out", type=str, default=None, help="Folder wyjściowy (domyślnie replay_YYYYMMDD_HHMMSS)")
    p.add_argument("--open", action="store_true", help="Otwórz folder wynikowy po zakończeniu")
    p.add_argument("--no-outline", action="store_true", help="Nie rysuj obrysu heksa w preview")
    args = p.parse_args(argv)

    if bool(args.config) == bool(args.case):
        p.error("Podaj dokładnie jedno: --config albo --case")

    ts = datetime.now().strftime("%Y%m%d_%H%M%S")
    out_dir = Path(args.out) if args.out else (OUT_ROOT / f"replay_{ts}")
    _ensure_dir(out_dir)

    add_outline = not args.no_outline

    if args.config:
        cfg_path = Path(args.config)
        data = _read_json(cfg_path)
        (out_dir / "input_hex_config.json").write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")

        if data.get("mode") == "cluster7":
            _render_cluster7(data, out_dir, add_outline)
        else:
            _render_single_from_inspector(data, out_dir, add_outline)

    else:
        case_path = Path(args.case)
        data = _read_json(case_path)
        (out_dir / "input_case.json").write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")
        _render_single_from_fuzzer_case(data, out_dir, add_outline)

    if args.open:
        try:
            _open_path(out_dir)
        except Exception:
            pass

    print(f"OK: {out_dir}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
