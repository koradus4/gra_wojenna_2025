"""Headless smoke test: czy MapEditor generuje lake3 jako klaster (center + 2 sąsiadów).

Uruchom:
  python scripts/smoke_map_editor_lake3.py

Oczekiwane:
- w stdout pojawią się 3 ścieżki texture zaczynające się od lake_cluster_
- cluster_tile dla sąsiadów to konkretne nazwy (np. bottom, bottom_left)
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

    # Import edytora jako moduł (plik nie jest paczką, więc dodajemy edytory/ do sys.path)
    import map_editor_prototyp as me

    root = tk.Tk()
    root.withdraw()  # bez okna

    app = me.MapEditor(root, me.CONFIG)

    # Żeby to był smoke „bez UI”, odpinamy kosztowne rzeczy.
    app.draw_grid = lambda: None
    app.auto_save_and_export = lambda *args, **kwargs: None
    app.set_status = lambda *args, **kwargs: None

    # Stabilne wejście: cluster7 z center=0,0 i dwoma sąsiadami: bottom i bottom_left.
    center = "0,0"
    neighbor_bottom = "0,1"      # delta (0,1) => bottom
    neighbor_bottom_left = "-1,1"  # delta (-1,1) => bottom_left

    app.hex_data = {}  # czysto
    app.lake_auto_connect_var.set(False)
    app.lake_seed_var.set(63015)
    app.lake_grid_var.set("64")
    app.lake_cluster = [center, neighbor_bottom, neighbor_bottom_left]

    # Wywołujemy bezpośrednio lake3, żeby nie mieszać w autosave/clear.
    app._generate_lake_cluster_3hex(grid_size=64)

    # Zbieramy wyniki
    results = {}
    for hid in (center, neighbor_bottom, neighbor_bottom_left):
        terrain = app.hex_data.get(hid, {})
        results[hid] = {
            "texture": terrain.get("texture"),
            "lake_mode": terrain.get("lake_mode"),
            "lake_cluster_tile": terrain.get("lake_cluster_tile"),
            "lake_cluster_neighbors": terrain.get("lake_cluster_neighbors"),
            "lake_cluster_seed": terrain.get("lake_cluster_seed"),
        }

    print("[SMOKE] lake3 results:")
    for hid, info in results.items():
        print(f"  {hid}: mode={info['lake_mode']} tile={info['lake_cluster_tile']} texture={info['texture']}")

    # Prosta walidacja
    ok = True
    for hid, info in results.items():
        if info["lake_mode"] != "lake3":
            ok = False
        if not (info["texture"] and "lake_cluster_" in str(info["texture"])):
            ok = False

    # Dodatkowo: sąsiedzi muszą mieć tile != 'center'
    if results[neighbor_bottom]["lake_cluster_tile"] != "bottom":
        ok = False
    if results[neighbor_bottom_left]["lake_cluster_tile"] != "bottom_left":
        ok = False

    try:
        root.destroy()
    except Exception:
        pass

    if not ok:
        print("[SMOKE] FAIL: lake3 nie wygląda na klaster (sprawdź logikę cluster_tile/texture).")
        return 2

    print("[SMOKE] OK")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
