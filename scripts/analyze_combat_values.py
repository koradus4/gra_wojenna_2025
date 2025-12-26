"""Quick helper to inspect combat value ranges after balance adjustments."""
from __future__ import annotations

from pathlib import Path
import sys

# ensure repository root is on path when script executed directly
ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from balance import model

SIZES = ["Pluton", "Kompania", "Batalion"]
QUALITIES = ["low", "standard", "elite"]
# Wzięliśmy zarówno brak doktryny (None), jak i dwie zdefiniowane nacje.
NATIONS = [None, "Polska", "Niemcy"]


def analyze_combat_value_ranges():
    rows = []
    for unit_code in model.BASE_STATS:
        entries = []
        for size in SIZES:
            for quality in QUALITIES:
                for nation in NATIONS:
                    stats = model.compute_base_stats(unit_code, size, quality, nation=nation)
                    entries.append(
                        {
                            "cv": stats["combat_value"],
                            "size": size,
                            "quality": quality,
                            "nation": nation or "brak doktryny",
                        }
                    )
        low = min(entries, key=lambda entry: entry["cv"])
        high = max(entries, key=lambda entry: entry["cv"])
        rows.append(
            (
                unit_code,
                model.UNIT_TYPE_FULL.get(unit_code, unit_code),
                low,
                high,
            )
        )
    return rows


def print_report():
    print("Combat value ranges:")
    for code, name, low, high in analyze_combat_value_ranges():
        print(
            f"{code:>2} ({name:<16}) | min {low['cv']:>3} "
            f"({low['size']}, {low['quality']}, {low['nation']}) | "
            f"max {high['cv']:>3} ({high['size']}, {high['quality']}, {high['nation']})"
        )


if __name__ == "__main__":
    print_report()
