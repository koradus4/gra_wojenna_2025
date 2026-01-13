"""Headless smoke test: MapEditor generuje klaster cluster7 (7 heksów: center + 6 sąsiadów).

Uruchom:
  python scripts/smoke_map_editor_lake7.py

Oczekiwane:
- 7 wpisów w stdout, każdy z texture zaczynającym się od lake_cluster_
- lake_cluster_tile zgodny z pozycją (top/top_right/...)
"""

from __future__ import annotations

import sys
from pathlib import Path


def _repo_root() -> Path:
    return Path(__file__).resolve().parents[1]


def main() -> int:
    repo_root = _repo_root()
    sys.path.insert(0, str(repo_root))
    sys.path.insert(0, str(repo_root / "edytory"))

    import tkinter as tk
    import map_editor_prototyp as me

    root = tk.Tk()
    root.withdraw()

    app = me.MapEditor(root, me.CONFIG)

    # Odchudzamy: bez redrawów i autosave
    app.draw_grid = lambda: None
    app.auto_save_and_export = lambda *args, **kwargs: None
    app.set_status = lambda *args, **kwargs: None

    center = "0,0"
    neighbors = {
        "top": "0,-1",
        "top_right": "1,-1",
        "bottom_right": "1,0",
        "bottom": "0,1",
        "bottom_left": "-1,1",
        "top_left": "-1,0",
    }

    app.hex_data = {}
    app.lake_auto_connect_var.set(False)
    app.lake_seed_var.set(63015)
    app.lake_grid_var.set("64")
    app.lake_size_var.set("średnie")

    app.lake_cluster = [center, *neighbors.values()]
    app._generate_lake_cluster_cluster7(grid_size=64)

    expected_tiles = {"center", *neighbors.keys()}

    print("[SMOKE] lake7 results:")
    ok = True

    # Zbierz wyniki
    seen_tiles = set()
    for hid, terrain in app.hex_data.items():
        if hid not in app.lake_cluster:
            continue
        tile = terrain.get("lake_cluster_tile")
        tex = terrain.get("texture")
        mode = terrain.get("lake_mode")
        print(f"  {hid}: mode={mode} tile={tile} texture={tex}")
        if not tex or "lake_cluster_" not in str(tex):
            ok = False
        if tile:
            seen_tiles.add(tile)

    if seen_tiles != expected_tiles:
        ok = False

    try:
        root.destroy()
    except Exception:
        pass

    if not ok:
        print("[SMOKE] FAIL")
        return 2

    print("[SMOKE] OK")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
