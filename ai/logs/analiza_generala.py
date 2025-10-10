"""Szybki raport z logów generała AI.

Skrypt wyszukuje najnowszy plik CSV w katalogu `ai/logs/general/csv`,
wczytuje wpisy i wyciąga podsumowanie decyzji budżetowych Generała.
Rezultat drukowany jest na ekran oraz zapisywany do pliku
`ai/logs/general/raporty/<nazwa>_raport.txt`.
"""
from __future__ import annotations

import argparse
import csv
import json
from collections import Counter, defaultdict
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, Iterable, List, Optional

GENERAL_LOG_DIR = Path("ai/logs/general")
COMMANDER_LOG_DIR = Path("ai/logs/commander")
CSV_DIR = GENERAL_LOG_DIR / "csv"
COMMANDER_CSV_DIR = COMMANDER_LOG_DIR / "csv"
RAPORT_DIR = GENERAL_LOG_DIR / "raporty"


@dataclass
class TurnSummary:
    count: int = 0
    total_pe: int = 0
    reserve_effective: int = 0
    commander_spent: int = 0
    purchase_effective: int = 0
    support_fuel: int = 0
    support_repair: int = 0


def _find_latest_csv(path: Path) -> Optional[Path]:
    if path.is_file():
        return path
    if not path.exists():
        return None
    candidates = sorted(path.glob("*.csv"))
    return candidates[-1] if candidates else None


def _load_entries(csv_path: Path) -> Iterable[Dict[str, str]]:
    with csv_path.open("r", encoding="utf-8") as handle:
        reader = csv.DictReader(handle)
        for row in reader:
            yield row


def _load_commander_deployments(csv_dir: Path = COMMANDER_CSV_DIR) -> Dict[str, Dict[str, object]]:
    csv_path = _find_latest_csv(csv_dir)
    if not csv_path or not csv_path.exists():
        return {}

    deployments: Dict[str, Dict[str, object]] = {}
    for entry in _load_entries(csv_path):
        if entry.get("message") != "Wystawiono wzmocnienie":
            continue
        context = _parse_context(entry.get("context", ""))
        token_id = context.get("token_id")
        if not token_id:
            continue
        deployments[str(token_id)] = {
            "timestamp": entry.get("timestamp"),
            "commander_id": context.get("commander_id"),
            "spawn_q": context.get("spawn_q"),
            "spawn_r": context.get("spawn_r"),
            "cost": context.get("cost"),
        }
    return deployments


def _parse_context(context_raw: str) -> Dict[str, object]:
    if not context_raw:
        return {}
    try:
        data = json.loads(context_raw)
    except json.JSONDecodeError:
        return {}
    if isinstance(data, dict):
        return data
    return {}


def _aggregate(entries: Iterable[Dict[str, str]]):
    totals = TurnSummary()
    war_state_counter: Counter[str] = Counter()
    vp_diffs: List[int] = []
    token_diffs: List[int] = []
    purchase_focus: Counter[str] = Counter()
    commander_allocations: Dict[int, int] = defaultdict(int)
    allocations_total = 0
    purchases: List[Dict[str, object]] = []

    for entry in entries:
        message = entry.get("message")
        context = _parse_context(entry.get("context", ""))

        if message == "Podsumowanie decyzji Generała":
            totals.count += 1
            totals.total_pe += int(context.get("total_pe_available", 0) or 0)
            totals.reserve_effective += int(context.get("reserve_effective", 0) or 0)
            totals.commander_spent += int(context.get("commander_pool_spent", 0) or 0)
            totals.purchase_effective += int(context.get("purchase_effective", 0) or 0)
            totals.support_fuel += int(context.get("support_fuel_total", 0) or 0)
            totals.support_repair += int(context.get("support_repair_total", 0) or 0)

            war_state = str(context.get("war_state") or "UNKNOWN")
            war_state_counter[war_state] += 1

            vp_diff = context.get("vp_diff")
            token_diff = context.get("token_diff")
            if isinstance(vp_diff, (int, float)):
                vp_diffs.append(int(vp_diff))
            if isinstance(token_diff, (int, float)):
                token_diffs.append(int(token_diff))

            for purchase in context.get("purchase_plan", []) or []:
                if isinstance(purchase, dict):
                    focus = str(purchase.get("focus") or purchase.get("category") or "unknown")
                    purchase_focus[focus] += int(purchase.get("allocated", 0) or 0)

            for commander_entry in context.get("commander_allocations", []) or []:
                if not isinstance(commander_entry, dict):
                    continue
                commander_id = commander_entry.get("id")
                allocated = commander_entry.get("allocated", 0)
                if commander_id is None:
                    continue
                commander_allocations[int(commander_id)] += int(allocated or 0)
                allocations_total += int(allocated or 0)

        elif message == "Zakupiono jednostkę":
            if context:
                purchases.append(
                    {
                        "timestamp": entry.get("timestamp"),
                        "turn": context.get("turn"),
                        "commander_id": context.get("commander_id"),
                        "token_id": context.get("token_id"),
                        "unit_type": context.get("unit_type"),
                        "unit_size": context.get("unit_size"),
                        "category": context.get("category"),
                        "focus": context.get("focus"),
                        "cost": context.get("cost"),
                        "folder": context.get("folder"),
                    }
                )

    return {
        "totals": totals,
        "war_state_counter": war_state_counter,
        "vp_diffs": vp_diffs,
        "token_diffs": token_diffs,
        "purchase_focus": purchase_focus,
        "commander_allocations": commander_allocations,
        "allocations_total": allocations_total,
        "purchases": purchases,
    }


def _format_report(data: Dict[str, object]) -> str:
    totals: TurnSummary = data["totals"]
    war_state_counter: Counter[str] = data["war_state_counter"]
    vp_diffs: List[int] = data["vp_diffs"]
    token_diffs: List[int] = data["token_diffs"]
    purchase_focus: Counter[str] = data["purchase_focus"]
    commander_allocations: Dict[int, int] = data["commander_allocations"]
    allocations_total: int = data["allocations_total"]
    purchases: List[Dict[str, object]] = data.get("purchases", [])  # type: ignore[arg-type]

    lines: List[str] = []
    lines.append("=== Raport Generała AI ===")
    lines.append("")

    lines.append("--- TURY ---")
    lines.append(f"• Zliczone tury: {totals.count}")
    if totals.count:
        avg_total = totals.total_pe / totals.count
        avg_commander = totals.commander_spent / totals.count
        avg_reserve = totals.reserve_effective / totals.count
        avg_purchase = totals.purchase_effective / totals.count
        lines.append(f"• Średni budżet całkowity: {avg_total:.2f} PE")
        lines.append(f"• Średni przydział dla dowódców: {avg_commander:.2f} PE")
        lines.append(f"• Średnia rezerwa: {avg_reserve:.2f} PE")
        lines.append(f"• Średnie zakupy: {avg_purchase:.2f} PE")

    if war_state_counter:
        lines.append("")
        lines.append("--- STAN WOJNY ---")
        for state, count in war_state_counter.most_common():
            lines.append(f"• {state}: {count} tur")

    if vp_diffs:
        avg_vp = sum(vp_diffs) / len(vp_diffs)
        lines.append("")
        lines.append(f"Średnia różnica VP: {avg_vp:.2f}")
    if token_diffs:
        avg_token = sum(token_diffs) / len(token_diffs)
        lines.append(f"Średnia różnica liczby żetonów: {avg_token:.2f}")

    lines.append("")
    lines.append("--- WSPARCIE ---")
    lines.append(f"• Łączny deficyt paliwa: {totals.support_fuel}")
    lines.append(f"• Łączne potrzeby napraw: {totals.support_repair}")

    if purchase_focus:
        lines.append("")
        lines.append("--- PRIORYTETY ZAKUPÓW (sumaryczny PE) ---")
        for focus, amount in purchase_focus.most_common():
            lines.append(f"• {focus}: {amount}")

    if commander_allocations:
        lines.append("")
        lines.append("--- PRZYDZIAŁY DLA DOWÓDCÓW (łącznie) ---")
        for commander_id, amount in sorted(commander_allocations.items()):
            share = (amount / allocations_total * 100) if allocations_total else 0.0
            lines.append(f"• Dowódca {commander_id}: {amount} PE ({share:.1f}% puli)")

    if purchases:
        deployments = _load_commander_deployments()
        lines.append("")
        lines.append("<details>")
        lines.append(f"<summary>Zakupione żetony ({len(purchases)})</summary>")
        for purchase in purchases:
            token_id = purchase.get("token_id") or "(brak id)"
            commander_id = purchase.get("commander_id")
            cost = purchase.get("cost")
            category = purchase.get("category") or purchase.get("focus")
            focus = purchase.get("focus")
            unit_desc = ", ".join(
                part for part in [purchase.get("unit_type"), purchase.get("unit_size")] if part
            )
            turn = purchase.get("turn")
            folder = purchase.get("folder")

            deployment = deployments.get(str(token_id))
            if deployment:
                status = (
                    f"wystawiono przez Dowódca {deployment.get('commander_id')} na heksie "
                    f"({deployment.get('spawn_q')},{deployment.get('spawn_r')})"
                )
            else:
                status = "oczekuje na wystawienie"

            details = [f"token {token_id}"]
            if unit_desc:
                details.append(unit_desc)
            if category:
                label = category if category != focus else category
                details.append(f"kategoria: {label}")
            if focus and focus != category:
                details.append(f"focus: {focus}")
            if cost is not None:
                details.append(f"koszt: {cost} PE")
            if commander_id is not None:
                details.append(f"dla dowódcy {commander_id}")
            if turn is not None:
                details.append(f"tura: {turn}")
            if folder:
                details.append(f"folder: {folder}")

            lines.append(f"• {' | '.join(details)} → {status}")

        lines.append("</details>")

    return "\n".join(lines)


def main() -> None:
    parser = argparse.ArgumentParser(description="Analiza logów generała AI")
    parser.add_argument(
        "sciezka",
        nargs="?",
        default=str(CSV_DIR),
        help="Ścieżka do pliku CSV lub katalogu z logami generała",
    )
    args = parser.parse_args()

    csv_candidate = _find_latest_csv(Path(args.sciezka))
    if not csv_candidate or not csv_candidate.exists():
        raise SystemExit("Brak pliku CSV logów generała do analizy.")

    data = _aggregate(_load_entries(csv_candidate))
    raport = _format_report(data)
    print(raport)

    RAPORT_DIR.mkdir(parents=True, exist_ok=True)
    raport_path = RAPORT_DIR / f"{csv_candidate.stem}_raport.txt"
    raport_path.write_text(raport, encoding="utf-8")
    print(f"\nRaport zapisany do pliku: {raport_path}")


if __name__ == "__main__":
    main()
