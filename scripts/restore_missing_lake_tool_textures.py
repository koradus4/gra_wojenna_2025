"""Odtwarza brakujące PNG w assets/terrain/hex_painted/lake_tool na podstawie wpisów w data/map_data.json.

Po czyszczeniu katalogów może się zdarzyć, że map_data.json nadal wskazuje na pliki lake_tool.
Ten skrypt regeneruje brakujące obrazy pod TE SAME nazwy plików, żeby nie psuć mapy.

Uruchom:
  python scripts/restore_missing_lake_tool_textures.py
"""

from __future__ import annotations

import json
import sys
from pathlib import Path


def _repo_root() -> Path:
    return Path(__file__).resolve().parents[1]


def main() -> int:
    repo_root = _repo_root()
    map_path = repo_root / "data" / "map_data.json"
    if not map_path.exists():
        print(f"Brak pliku: {map_path}")
        return 2

    # Import generatora z edytory/
    sys.path.insert(0, str(repo_root / "edytory"))
    from generate_lake_hex_tile import LakeOptions, render_lake  # type: ignore

    data = json.loads(map_path.read_text(encoding="utf-8"))

    created = 0
    already = 0
    skipped = 0

    if not isinstance(data, dict):
        print("Nieoczekiwany format map_data.json (nie jest dict).")
        return 2

    # Aktualny format: { meta: ..., terrain: { hex_id: {...} }, ... }
    terrain_map = data.get("terrain") if isinstance(data.get("terrain"), dict) else data

    if not isinstance(terrain_map, dict):
        print("Nieoczekiwany format map_data.json (brak dict w polu 'terrain').")
        return 2

    for hex_id, terrain in terrain_map.items():
        if not isinstance(terrain, dict):
            continue
        texture = terrain.get("texture")
        if not texture or not isinstance(texture, str):
            continue
        if "lake_tool" not in texture:
            continue
        if not texture.lower().endswith(".png"):
            continue

        rel = Path(texture.replace("\\", "/"))
        out_path = repo_root / "assets" / rel
        out_path.parent.mkdir(parents=True, exist_ok=True)

        if out_path.exists():
            already += 1
            continue

        # Ustal parametry.
        lake_mode = terrain.get("lake_mode")
        lake_seed = terrain.get("lake_seed")
        cluster_seed = terrain.get("lake_cluster_seed")
        cluster_tile = terrain.get("lake_cluster_tile")
        cluster_neighbors = terrain.get("lake_cluster_neighbors")

        outflow_side = terrain.get("lake_outflow_side")
        outflow_width = terrain.get("lake_outflow_width")

        is_cluster = bool(cluster_seed is not None and cluster_tile and cluster_neighbors)

        try:
            seed_int = int(lake_seed) if lake_seed is not None else int(cluster_seed) if cluster_seed is not None else 1
        except Exception:
            seed_int = 1

        opts_kwargs = {
            "grid_size": 64,
            "background": None,
            "seed": seed_int,
            "shore_width": 2,
        }

        if is_cluster:
            try:
                neighbors_tuple = tuple(str(x) for x in cluster_neighbors)
            except Exception:
                skipped += 1
                continue

            opts_kwargs.update(
                {
                    "cluster_seed": int(cluster_seed),
                    "cluster_neighbors": neighbors_tuple,
                    "cluster_tile": str(cluster_tile),
                    # bezpieczny domyślny mnożnik dla klastrów
                    "lake_radius": 1.0,
                }
            )

            # outflow tylko sensownie na center
            if str(cluster_tile) == "center" and outflow_side:
                opts_kwargs["outflow_side"] = str(outflow_side)
                if outflow_width is not None:
                    try:
                        opts_kwargs["outflow_width"] = float(outflow_width)
                    except Exception:
                        pass
        else:
            # single
            opts_kwargs["lake_radius"] = 0.34
            if outflow_side:
                opts_kwargs["outflow_side"] = str(outflow_side)
                if outflow_width is not None:
                    try:
                        opts_kwargs["outflow_width"] = float(outflow_width)
                    except Exception:
                        pass

        try:
            img, _meta = render_lake(LakeOptions(**opts_kwargs))
            img.save(out_path)
            created += 1
        except Exception as e:
            print(f"FAIL {hex_id} -> {out_path.name}: {e}")
            skipped += 1

    print(f"restore_missing_lake_tool_textures: created={created} already={already} skipped={skipped}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
