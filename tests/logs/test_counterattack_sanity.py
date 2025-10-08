import csv
import json
from pathlib import Path

import pytest


PROJECT_ROOT = Path(__file__).resolve().parents[2]
LOG_DIR = PROJECT_ROOT / "ai" / "logs" / "human" / "csv"
CSV_FILES = sorted(LOG_DIR.glob("*.csv"))


if not CSV_FILES:
    pytest.skip("Brak plików logów CSV w ai/logs/human/csv", allow_module_level=True)


@pytest.mark.parametrize("csv_path", CSV_FILES)
def test_counterattack_distance_within_defense_range(csv_path: Path) -> None:
    """Sprawdza, że każdy kontratak następuje w zasięgu obrony."""
    with csv_path.open("r", encoding="utf-8", newline="") as handle:
        reader = csv.DictReader(handle)
        violations: list[str] = []
        missing_details: list[str] = []

        for row_index, row in enumerate(reader, start=2):
            context_raw = row.get("context")
            if not context_raw:
                continue

            try:
                context = json.loads(context_raw)
            except json.JSONDecodeError as exc:  # pragma: no cover - natychmiastowe zakończenie testu
                pytest.fail(
                    f"Niepoprawny JSON w kolumnie context w pliku {csv_path.name}, "
                    f"wiersz {row_index}: {exc}"
                )

            if context.get("counterattack") is not True:
                continue

            detail = context.get("combat_detail") or {}
            distance = detail.get("distance")
            defense_range = detail.get("defense_range")

            if distance is None or defense_range is None:
                missing_details.append(
                    f"{csv_path.name} wiersz {row_index} – brak distance/defense_range dla "
                    f"kontrataku ({row.get('summary', '').strip()})"
                )
                continue

            distance_value = float(distance)
            defense_range_value = float(defense_range)

            if distance_value > defense_range_value:
                violations.append(
                    f"{csv_path.name} wiersz {row_index} – kontratak poza zasięgiem: "
                    f"distance={distance_value} > defense_range={defense_range_value}; "
                    f"akcja {row.get('summary', '').strip()}"
                )

        if missing_details:
            pytest.fail("\n".join(missing_details))
        if violations:
            pytest.fail("\n".join(violations))
