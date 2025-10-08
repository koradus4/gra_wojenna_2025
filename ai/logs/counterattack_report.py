"""Analiza kontrataków w logach ludzkiego gracza."""
from __future__ import annotations

import argparse
import csv
import json
from dataclasses import dataclass
from pathlib import Path
from statistics import mean
from typing import Iterable, Sequence


@dataclass
class CounterattackEvent:
    csv_path: Path
    timestamp: str
    attacker: str
    defender: str
    distance: float
    defense_range: float
    attack_result: float | None
    defense_result: float | None

@dataclass
class FileStats:
    path: Path
    attacks: int
    counterattacks: int
    events: list[CounterattackEvent]

    @property
    def ratio(self) -> float:
        return (self.counterattacks / self.attacks * 100) if self.attacks else 0.0


LOG_ROOT = Path(__file__).resolve().parent
LOG_DIR = LOG_ROOT / "human" / "csv"
DEFAULT_REPORT_DIR = LOG_ROOT / "human" / "raporty"


def find_csv_files(custom_dir: Path | None) -> list[Path]:
    directory = custom_dir or LOG_DIR
    if not directory.exists():
        raise FileNotFoundError(
            f"Katalog z logami {directory} nie istnieje. Upewnij się, że ścieżka jest poprawna."
        )
    files = sorted(p for p in directory.glob("*.csv") if p.is_file())
    if not files:
        raise FileNotFoundError(
            f"Nie znaleziono plików CSV z logami w katalogu {directory}."
        )
    return files


def parse_context(raw: str, csv_name: str, row_number: int) -> dict:
    try:
        return json.loads(raw)
    except json.JSONDecodeError as exc:  # pragma: no cover - raportujemy i kończymy
        raise ValueError(
            f"Nie można sparsować pola context w pliku {csv_name}, wiersz {row_number}: {exc}"
        ) from exc


def analyze_file(csv_path: Path) -> FileStats:
    events: list[CounterattackEvent] = []
    total_attacks = 0

    with csv_path.open("r", encoding="utf-8", newline="") as handle:
        reader = csv.DictReader(handle)
        for row_number, row in enumerate(reader, start=2):
            if row.get("action_type") != "attack":
                continue
            total_attacks += 1

            context_raw = row.get("context", "")
            if not context_raw:
                continue

            context = parse_context(context_raw, csv_path.name, row_number)
            if context.get("counterattack") is not True:
                continue

            detail = context.get("combat_detail") or {}
            distance = detail.get("distance")
            defense_range = detail.get("defense_range")
            attack_result = detail.get("attack_result")
            defense_result = detail.get("defense_result")

            if distance is None or defense_range is None:
                raise ValueError(
                    f"Brak informacji o dystansie/zasięgu w pliku {csv_path.name}, "
                    f"wiersz {row_number} ({row.get('summary', '').strip()})."
                )

            events.append(
                CounterattackEvent(
                    csv_path=csv_path,
                    timestamp=row.get("timestamp", ""),
                    attacker=context.get("token_id", ""),
                    defender=context.get("target_token_id", ""),
                    distance=float(distance),
                    defense_range=float(defense_range),
                    attack_result=float(attack_result) if attack_result is not None else None,
                    defense_result=float(defense_result) if defense_result is not None else None,
                )
            )
    return FileStats(path=csv_path, attacks=total_attacks, counterattacks=len(events), events=events)


def aggregate(events: Iterable[CounterattackEvent]) -> dict:
    per_defender: dict[str, int] = {}
    per_attacker: dict[str, int] = {}
    distance_samples: list[float] = []
    defense_samples: list[float] = []
    defense_damage_samples: list[float] = []

    for event in events:
        per_defender[event.defender] = per_defender.get(event.defender, 0) + 1
        per_attacker[event.attacker] = per_attacker.get(event.attacker, 0) + 1
        distance_samples.append(event.distance)
        defense_samples.append(event.defense_range)
        if event.defense_result is not None:
            defense_damage_samples.append(event.defense_result)

    return {
        "per_defender": per_defender,
        "per_attacker": per_attacker,
        "distance_avg": mean(distance_samples) if distance_samples else 0.0,
        "distance_max": max(distance_samples) if distance_samples else 0.0,
        "defense_range_avg": mean(defense_samples) if defense_samples else 0.0,
        "defense_damage_avg": mean(defense_damage_samples) if defense_damage_samples else 0.0,
    }


def _format_counter(counter: dict[str, int], *, limit: int = 5) -> list[str]:
    entries = sorted(counter.items(), key=lambda item: item[1], reverse=True)
    return [f"  • {key or '<brak id>'}: {value}" for key, value in entries[:limit]]


def render_report(files: Sequence[FileStats], overall: dict) -> str:
    lines: list[str] = []

    lines.append("=== Raport kontrataków ludzkiego gracza ===")
    lines.append("")

    lines.append("--- Podsumowanie plików ---")
    for stats in files:
        lines.append(
            f"• {stats.path.name}: kontrataki {stats.counterattacks} / ataki {stats.attacks} "
            f"({stats.ratio:.1f}%)."
        )
    lines.append("")

    lines.append("--- Statystyki zbiorcze ---")
    total_counterattacks = sum(stats.counterattacks for stats in files)
    total_attacks = sum(stats.attacks for stats in files)
    ratio = (total_counterattacks / total_attacks * 100) if total_attacks else 0.0
    lines.append(f"Łączna liczba kontrataków: {total_counterattacks}")
    lines.append(f"Łączna liczba ataków: {total_attacks}")
    lines.append(f"Skuteczność kontrataków: {ratio:.1f}%")
    lines.append(
        f"Średni dystans kontrataku: {overall['distance_avg']:.2f} (max {overall['distance_max']:.2f})"
    )
    lines.append(f"Średni zasięg obrony: {overall['defense_range_avg']:.2f}")
    lines.append(f"Średnie obrażenia kontrataku: {overall['defense_damage_avg']:.2f}")
    lines.append("")

    defenders = _format_counter(overall["per_defender"])
    if defenders:
        lines.append("Najaktywniejsi obrońcy:")
        lines.extend(defenders)
        lines.append("")

    attackers = _format_counter(overall["per_attacker"])
    if attackers:
        lines.append("Jednostki najczęściej obrywane kontratakiem:")
        lines.extend(attackers)
        lines.append("")

    lines.append("Notatka: raport obejmuje wyłącznie odnotowane kontrataki (counterattack=True).")

    return "\n".join(lines)


def write_report(text: str, *, target: Path | None, files: Sequence[FileStats]) -> Path:
    if target is None:
        DEFAULT_REPORT_DIR.mkdir(parents=True, exist_ok=True)
        if len(files) == 1:
            filename = f"{files[0].path.stem}_kontrataki.txt"
        else:
            filename = "kontrataki_zbiorczo.txt"
        target = DEFAULT_REPORT_DIR / filename
    else:
        target.parent.mkdir(parents=True, exist_ok=True)

    target.write_text(text, encoding="utf-8")
    return target


def build_json_payload(files: Sequence[FileStats]) -> dict:
    return {
        "files": {
            stats.path.name: {
                "attacks": stats.attacks,
                "counterattacks": stats.counterattacks,
                "events": [event.__dict__ for event in stats.events],
            }
            for stats in files
        }
    }


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--logs",
        type=Path,
        default=None,
        help="Opcjonalna ścieżka do katalogu z logami CSV (domyślnie ai/logs/human/csv).",
    )
    parser.add_argument(
        "--save",
        type=Path,
        default=None,
        help="Zapisz surowe dane kontrataków do wskazanego pliku JSON.",
    )
    parser.add_argument(
        "--report",
        type=Path,
        default=None,
        help="Ręcznie wskaż plik wyjściowy raportu tekstowego (domyślnie zapisz obok logów).",
    )
    parser.add_argument(
        "--no-report",
        action="store_true",
        help="Nie zapisuj raportu na dysk (tylko wypisz w konsoli).",
    )
    args = parser.parse_args()

    file_paths = find_csv_files(args.logs)
    file_stats = [analyze_file(path) for path in file_paths]
    all_events = [event for stats in file_stats for event in stats.events]
    overall = aggregate(all_events)
    report_text = render_report(file_stats, overall)

    print(report_text)

    if not args.no_report:
        output_path = write_report(report_text, target=args.report, files=file_stats)
        print(f"\nRaport zapisano do pliku: {output_path}")

    if args.save:
        payload = build_json_payload(file_stats)
        args.save.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
        print(f"\nDane JSON zapisano do {args.save}")


if __name__ == "__main__":  # pragma: no cover - entrypoint skryptu
    main()
