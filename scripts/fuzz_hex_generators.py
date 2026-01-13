from __future__ import annotations

import argparse
import json
import random
import shutil
from dataclasses import asdict
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, Iterable, List, Optional, Tuple

from PIL import Image


def _draw_hex_outline(img: Image.Image, color: Tuple[int, int, int, int] = (0, 255, 255, 220), width: int = 2) -> Image.Image:
    """Rysuje obrys heksa na obrazie (ułatwia ocenę PNG bez tła)."""
    from PIL import ImageDraw

    out = img.convert("RGBA").copy()
    w, h = out.size
    size = float(min(w, h))
    poly = _hex_vertices_pointy_top(size)
    draw = ImageDraw.Draw(out)
    draw.line(poly + [poly[0]], fill=color, width=width, joint="curve")
    return out


def _make_case_preview(img_path: Path, out_path: Path, prefer_size: int = 512) -> None:
    """Zapisuje preview z obrysem (i ewentualnym upscale) do paczki case."""
    img = Image.open(img_path).convert("RGBA")
    if prefer_size and img.size[0] < prefer_size:
        scale = prefer_size // img.size[0]
        if scale >= 2:
            img = img.resize((img.size[0] * scale, img.size[1] * scale), Image.NEAREST)
    preview = _draw_hex_outline(img)
    preview.save(out_path)


PROJEKT_ROOT = Path(__file__).resolve().parent.parent
EDYTORY_DIR = PROJEKT_ROOT / "edytory"

# importy generatorów z edytory/
import sys

sys.path.insert(0, str(EDYTORY_DIR))

import generate_road_hex_tile as road_gen
import generate_railway_hex_tile as rail_gen
import generate_river_hex_tile as river_gen


def _hex_vertices_pointy_top(size: float) -> List[Tuple[float, float]]:
    """Wierzchołki heksa (pointy-top) w układzie 0..size."""
    cx = size / 2.0
    cy = size / 2.0
    radius = (size / 2.0) - 0.5
    import math

    sqrt3 = math.sqrt(3.0)
    return [
        (cx - radius, cy),
        (cx - radius / 2.0, cy - (sqrt3 / 2.0) * radius),
        (cx + radius / 2.0, cy - (sqrt3 / 2.0) * radius),
        (cx + radius, cy),
        (cx + radius / 2.0, cy + (sqrt3 / 2.0) * radius),
        (cx - radius / 2.0, cy + (sqrt3 / 2.0) * radius),
    ]


def _point_in_polygon(x: float, y: float, polygon: List[Tuple[float, float]]) -> bool:
    inside = False
    j = len(polygon) - 1
    for i in range(len(polygon)):
        xi, yi = polygon[i]
        xj, yj = polygon[j]
        if ((yi > y) != (yj > y)) and (x < (xj - xi) * (y - yi) / ((yj - yi) + 1e-10) + xi):
            inside = not inside
        j = i
    return inside


def _alpha(img: Image.Image) -> Image.Image:
    if img.mode != "RGBA":
        img = img.convert("RGBA")
    return img.split()[-1]


def _has_ink_near(img: Image.Image, x: float, y: float, radius: int) -> bool:
    a = _alpha(img)
    w, h = img.size
    cx = int(round(x))
    cy = int(round(y))
    r2 = radius * radius
    px = a.load()
    for dy in range(-radius, radius + 1):
        yy = cy + dy
        if yy < 0 or yy >= h:
            continue
        for dx in range(-radius, radius + 1):
            if dx * dx + dy * dy > r2:
                continue
            xx = cx + dx
            if xx < 0 or xx >= w:
                continue
            if px[xx, yy] > 0:
                return True
    return False


def _leaks_outside_hex(img: Image.Image, samples: int = 3000) -> bool:
    """Heurystyka: losowo próbkowane punkty poza heksagonem nie powinny mieć alpha."""
    a = _alpha(img)
    w, h = img.size
    poly = _hex_vertices_pointy_top(float(w))
    px = a.load()

    rng = random.Random(1337)
    checked = 0
    hits = 0
    # próbkuj punkty aż zbierzesz wystarczająco poza heksagonem
    while checked < samples:
        x = rng.randrange(0, w)
        y = rng.randrange(0, h)
        if _point_in_polygon(x + 0.5, y + 0.5, poly):
            continue
        checked += 1
        if px[x, y] > 0:
            hits += 1
            if hits >= 3:
                return True
    return False


def _leaks_outside_mask(img: Image.Image, mask: Sequence[Sequence[bool]], max_hits: int = 3) -> bool:
    a = _alpha(img)
    w, h = img.size
    if h != len(mask) or w != len(mask[0]):
        # brak kompatybilności rozmiaru — nie sprawdzamy
        return False
    px = a.load()
    hits = 0
    for row in range(h):
        for col in range(w):
            if mask[row][col]:
                continue
            if px[col, row] > 0:
                hits += 1
                if hits >= max_hits:
                    return True
    return False


def _read_json_if_exists(path: Path) -> Optional[Dict[str, Any]]:
    try:
        if path.exists():
            return json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return None
    return None


def _ensure_dir(p: Path) -> None:
    p.mkdir(parents=True, exist_ok=True)


def _random_distinct_sides(rng: random.Random, sides: Iterable[str]) -> Tuple[str, str]:
    s = list(sides)
    a = rng.choice(s)
    b = rng.choice([x for x in s if x != a])
    return a, b


def fuzz_road(rng: random.Random, out_dir: Path, idx: int) -> Tuple[bool, Dict[str, Any]]:
    entry, exit_side = _random_distinct_sides(rng, road_gen.HEX_SIDES)
    road_type = rng.choice(sorted(road_gen.ROAD_COLOR_PRESETS.keys()))
    width = rng.choice(sorted(road_gen.ROAD_WIDTH_PRESETS.keys()))

    crossroads: List[str] = []
    if rng.random() < 0.40:
        candidates = [s for s in road_gen.HEX_SIDES if s not in (entry, exit_side)]
        rng.shuffle(candidates)
        crossroads = candidates[: rng.choice([1, 2])]

    opts = road_gen.RoadOptions(
        grid_size=64,
        background=None,
        entry_side=entry,
        exit_side=exit_side,
        road_type=road_type,
        width=width,
        noise_amplitude=rng.uniform(0.0, 1.0),
        seed=rng.randint(1, 9999999),
        crossroads=crossroads or None,
    )

    png = out_dir / f"road_{idx:05d}.png"
    result = road_gen.generate_road(opts, png)

    meta = _read_json_if_exists(result.metadata_path)

    img = Image.open(result.image_path).convert("RGBA")
    export_size = int(img.size[0])
    scale = export_size / float(opts.grid_size)

    problems: List[str] = []
    if _leaks_outside_hex(img):
        problems.append("alpha_outside_hex")

    # strony, które mają "wyjść" do krawędzi (po normalizacji)
    crossroads_final = None
    if isinstance(meta, dict):
        crossroads_final = meta.get("crossroads")
    if crossroads_final is None:
        crossroads_final = crossroads
    must_hit = [opts.entry_side, opts.exit_side] + (list(crossroads_final) if crossroads_final else [])
    for side in must_hit:
        pt = road_gen._side_to_edge_center(side, opts.grid_size)  # type: ignore[attr-defined]
        if not _has_ink_near(img, pt[0] * scale, pt[1] * scale, radius=int(3 * scale)):
            problems.append(f"no_ink_near_edge:{side}")

    return (len(problems) == 0), {
        "category": "road",
        "options": asdict(opts),
        "metadata": meta,
        "problems": problems,
        "image": str(result.image_path),
        "metadata_path": str(result.metadata_path),
    }


def fuzz_railway(rng: random.Random, out_dir: Path, idx: int) -> Tuple[bool, Dict[str, Any]]:
    entry, exit_side = _random_distinct_sides(rng, rail_gen.HEX_SIDES)
    railway_type = rng.choice(sorted(rail_gen.RAILWAY_DIMENSIONS.keys()))

    junctions: List[str] = []
    if rng.random() < 0.45:
        candidates = [s for s in rail_gen.HEX_SIDES if s not in (entry, exit_side)]
        rng.shuffle(candidates)
        # czasem specjalnie dajemy 2, żeby sprawdzić normalizację
        junctions = candidates[: rng.choice([1, 2])]

    opts = rail_gen.RailwayOptions(
        grid_size=64,
        background=None,
        entry_side=entry,
        exit_side=exit_side,
        railway_type=railway_type,
        seed=rng.randint(1, 9999999),
        junctions=junctions,
        junction_double_track=(rng.random() < 0.25),
    )

    png = out_dir / f"railway_{idx:05d}.png"
    result = rail_gen.generate_railway(opts, png)

    meta = _read_json_if_exists(result.metadata_path)

    img = Image.open(result.image_path).convert("RGBA")
    export_size = int(img.size[0])
    scale = export_size / float(opts.grid_size)

    problems: List[str] = []
    if _leaks_outside_hex(img):
        problems.append("alpha_outside_hex")

    junctions_final = None
    if isinstance(meta, dict):
        junctions_final = meta.get("junctions")
    if junctions_final is None:
        junctions_final = junctions
    must_hit = [opts.entry_side, opts.exit_side] + (list(junctions_final) if junctions_final else [])
    for side in must_hit:
        pt = rail_gen._side_to_edge_center(side, opts.grid_size)  # type: ignore[attr-defined]
        if not _has_ink_near(img, pt[0] * scale, pt[1] * scale, radius=int(3 * scale)):
            problems.append(f"no_ink_near_edge:{side}")

    return (len(problems) == 0), {
        "category": "railway",
        "options": asdict(opts),
        "metadata": meta,
        "problems": problems,
        "image": str(result.image_path),
        "metadata_path": str(result.metadata_path),
    }


def fuzz_river(rng: random.Random, out_dir: Path, idx: int) -> Tuple[bool, Dict[str, Any]]:
    entry, exit_side = _random_distinct_sides(rng, river_gen.HEX_SIDES)
    shape = rng.choice(list(river_gen.PATH_SHAPES))

    trib = None
    if rng.random() < 0.35:
        candidates = [s for s in river_gen.HEX_SIDES if s not in (entry, exit_side)]
        if candidates:
            trib = river_gen.TributaryOptions(
                entry_side=rng.choice(candidates),
                join_ratio=rng.uniform(0.0, 1.0),
                shape=rng.choice(list(river_gen.PATH_SHAPES)),
                shape_strength=rng.uniform(0.0, 1.0),
                noise_amplitude=rng.uniform(0.0, 1.0),
                noise_frequency=rng.uniform(0.0, 1.0),
            )

    opts = river_gen.RiverCenterlineOptions(
        grid_size=64,
        background=None,
        entry_side=entry,
        exit_side=exit_side,
        shape=shape,
        shape_strength=rng.uniform(0.0, 1.0),
        shape_direction=rng.choice([None, -1, 1]),
        noise_amplitude=rng.uniform(0.0, 1.0),
        noise_frequency=rng.uniform(0.0, 1.0),
        seed=rng.randint(1, 9999999),
        tributary=trib,
    )

    png = out_dir / f"river_{idx:05d}.png"
    result = river_gen.generate_centerline(opts, png)

    meta = _read_json_if_exists(result.metadata_path)

    img = Image.open(result.image_path).convert("RGBA")
    export_size = int(img.size[0])
    scale = export_size / float(opts.grid_size)

    problems: List[str] = []
    # Rzeka ma bardziej "konserwatywną" maskę (pixels intersecting polygon) — użyj tej samej.
    river_mask = river_gen.build_hex_mask(opts.grid_size)
    if _leaks_outside_mask(img, river_mask):
        problems.append("alpha_outside_hex")

    # start/end z geometrii rzeki
    start, end = river_gen.pick_flow_endpoints_by_side(opts.grid_size, opts.entry_side, opts.exit_side)
    if not _has_ink_near(img, start[0] * scale, start[1] * scale, radius=int(3 * scale)):
        problems.append("no_ink_near_edge:entry")
    if not _has_ink_near(img, end[0] * scale, end[1] * scale, radius=int(3 * scale)):
        problems.append("no_ink_near_edge:exit")

    return (len(problems) == 0), {
        "category": "river",
        "options": asdict(opts),
        "metadata": meta,
        "problems": problems,
        "image": str(result.image_path),
        "metadata_path": str(result.metadata_path),
    }


def main(argv: Optional[List[str]] = None) -> int:
    p = argparse.ArgumentParser(description="Fuzz test generatorów heksów (droga/rzeka/kolej).")
    p.add_argument("--category", choices=["road", "railway", "river", "all"], default="all")
    p.add_argument("--n", type=int, default=200)
    p.add_argument("--seed", type=int, default=12345)
    p.add_argument("--stop-on-first", action="store_true")
    p.add_argument(
        "--examples-per-problem",
        type=int,
        default=2,
        help="Ile przykładowych paczek skopiować na każdy typ problemu do examples/ (0 = wyłącz).",
    )
    args = p.parse_args(argv)

    rng = random.Random(args.seed)

    ts = datetime.now().strftime("%Y%m%d_%H%M%S")
    base_out = PROJEKT_ROOT / "edytory" / "_hex_inspector_output" / f"fuzz_{ts}"
    tmp_dir = base_out / "_tmp"
    fail_dir = base_out / "failures"
    _ensure_dir(tmp_dir)
    _ensure_dir(fail_dir)

    categories = [args.category] if args.category != "all" else ["road", "railway", "river"]

    total = 0
    failed = 0

    for cat in categories:
        for i in range(args.n):
            total += 1
            ok: bool
            report: Dict[str, Any]
            if cat == "road":
                ok, report = fuzz_road(rng, tmp_dir, i)
            elif cat == "railway":
                ok, report = fuzz_railway(rng, tmp_dir, i)
            else:
                ok, report = fuzz_river(rng, tmp_dir, i)

            if ok:
                continue

            failed += 1
            # przenieś pliki do failures
            img_path = Path(report["image"])
            meta_path = Path(report["metadata_path"])
            case_dir = fail_dir / f"{cat}_{i:05d}"
            _ensure_dir(case_dir)

            shutil.copy2(img_path, case_dir / img_path.name)
            if meta_path.exists():
                shutil.copy2(meta_path, case_dir / meta_path.name)

            # Podgląd dla człowieka (obrys heksa + ewentualny upscale)
            try:
                _make_case_preview(img_path, case_dir / "preview.png")
            except Exception:
                pass

            (case_dir / "case.json").write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")

            if args.stop_on_first:
                print(f"FAIL: {cat} #{i} -> {report['problems']}")
                print(f"Saved: {case_dir}")
                return 2

    # --- Podsumowanie wyników (ułatwia zgłaszanie) ---
    summary: Dict[str, Any] = {
        "total": total,
        "failed": failed,
        "base_out": str(base_out),
        "failures_dir": str(fail_dir),
        "by_category": {},
        "by_problem": {},
        "examples": {},
    }

    if fail_dir.exists():
        # zlicz problemy i kategorie
        case_files = sorted(fail_dir.glob("**/case.json"))
        by_problem: Dict[str, int] = {}
        by_category: Dict[str, int] = {}
        cases_by_problem: Dict[str, List[Path]] = {}

        for cf in case_files:
            try:
                data = json.loads(cf.read_text(encoding="utf-8"))
            except Exception:
                continue
            cat = str(data.get("category") or "unknown")
            by_category[cat] = by_category.get(cat, 0) + 1
            probs = data.get("problems") or []
            if not isinstance(probs, list):
                probs = [str(probs)]
            for pr in probs:
                pr_s = str(pr)
                by_problem[pr_s] = by_problem.get(pr_s, 0) + 1
                cases_by_problem.setdefault(pr_s, []).append(cf)

        summary["by_category"] = dict(sorted(by_category.items(), key=lambda kv: (-kv[1], kv[0])))
        summary["by_problem"] = dict(sorted(by_problem.items(), key=lambda kv: (-kv[1], kv[0])))

        # skopiuj przykłady do examples/
        examples_dir = base_out / "examples"
        if args.examples_per_problem and args.examples_per_problem > 0 and by_problem:
            _ensure_dir(examples_dir)
            examples: Dict[str, List[str]] = {}
            for pr, paths in sorted(cases_by_problem.items(), key=lambda kv: (-len(kv[1]), kv[0])):
                picked = paths[: int(args.examples_per_problem)]
                ex_list: List[str] = []
                safe_name = pr.replace(":", "_").replace("/", "_").replace("\\", "_")
                for idx, cf in enumerate(picked, start=1):
                    src_dir = cf.parent
                    dst_dir = examples_dir / f"{safe_name}_{idx:02d}"
                    if dst_dir.exists():
                        shutil.rmtree(dst_dir, ignore_errors=True)
                    shutil.copytree(src_dir, dst_dir)
                    ex_list.append(str(dst_dir))
                examples[pr] = ex_list
            summary["examples"] = examples

        # zapisz summary.json + summary.txt
        (base_out / "summary.json").write_text(
            json.dumps(summary, ensure_ascii=False, indent=2),
            encoding="utf-8",
        )

        lines: List[str] = []
        lines.append(f"TOTAL: {total}")
        lines.append(f"FAILED: {failed}")
        lines.append(f"OUTPUT: {base_out}")
        lines.append("")
        if by_category:
            lines.append("BY CATEGORY:")
            for k, v in summary["by_category"].items():
                lines.append(f"- {k}: {v}")
            lines.append("")
        if by_problem:
            lines.append("BY PROBLEM:")
            for k, v in list(summary["by_problem"].items())[:30]:
                lines.append(f"- {k}: {v}")
            lines.append("")
        if summary.get("examples"):
            lines.append("EXAMPLES (paths):")
            for pr, ex_paths in summary["examples"].items():
                if not ex_paths:
                    continue
                lines.append(f"- {pr}:")
                for pth in ex_paths:
                    lines.append(f"  * {pth}")
            lines.append("")
        (base_out / "summary.txt").write_text("\n".join(lines), encoding="utf-8")

    if failed:
        print(f"Done. total={total} failed={failed} output={base_out} (see summary.txt)")
    else:
        print(f"Done. total={total} failed={failed} output={base_out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
