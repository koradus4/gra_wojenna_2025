"""Summarize autonomous token log output for quick diagnostics."""
from __future__ import annotations

import argparse
import re
from collections import Counter
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, Iterable, Optional


START_RE = re.compile(r"status=([^,]+).+planned_actions=\[(.*)\]")
SUMMARY_RE = re.compile(
    r"movement_success=(True|False).*movement_attempts=(\d+).+resupply_spent=(\d+).+reserved_pe=(\d+)"
)
ATTACK_RE = re.compile(r"atak na .+success=(True|False).+damage_dealt=([\d-]+).+damage_taken=([\d-]+)")
FUEL_RE = re.compile(r"uzupełnia paliwo o (\d+)")
CV_RE = re.compile(r"uzupełnia CV o (\d+)")
HOLD_RE = re.compile(r"hold_position=(True|False)")
STATUS_RE = re.compile(r"status=([^,|]+)")
MODE_RE = re.compile(r"movement_mode=([a-zA-Z_]+)")
ATTEMPT_RE = re.compile(r"attack_attempted=(True|False)")
DISTANCE_TOTAL_RE = re.compile(r"movement_distance_total=([\d-]+)")
MP_SPENT_RE = re.compile(r"movement_mp_spent=([\d-]+)")


@dataclass
class Totals:
    entries: int = 0
    movement_success: int = 0
    movement_attempts: int = 0
    resupply_spent: int = 0
    reserved_pe: int = 0
    fuel_added: int = 0
    cv_added: int = 0
    hold_position_true: int = 0
    planned_attacks: int = 0
    attacks_attempted: int = 0
    movement_distance_total: int = 0
    movement_mp_spent_total: int = 0


def analyze_lines(lines: Iterable[str]) -> Dict[str, object]:
    actions = Counter()
    statuses = Counter()
    attacks = Counter()
    movement_modes = Counter()
    totals = Totals()

    for line in lines:
        if "start tury" in line:
            totals.entries += 1
            match = START_RE.search(line)
            if match:
                status, actions_raw = match.groups()
                statuses[status.strip()] += 1
                planned_attack = False
                if actions_raw.strip():
                    for item in actions_raw.split(','):
                        item = item.strip().strip("'\"")
                        if item:
                            actions[item] += 1
                            if item == "attack":
                                planned_attack = True
                if planned_attack:
                    totals.planned_attacks += 1
            mode_match = MODE_RE.search(line)
            if mode_match:
                movement_modes[mode_match.group(1).strip()] += 1
        elif "koniec tury" in line:
            match = SUMMARY_RE.search(line)
            if match:
                success_flag, attempts, spent, reserved = match.groups()
                if success_flag == "True":
                    totals.movement_success += 1
                totals.movement_attempts += int(attempts)
                totals.resupply_spent += int(spent)
                totals.reserved_pe += int(reserved)
            attempt_match = ATTEMPT_RE.search(line)
            if attempt_match and attempt_match.group(1) == "True":
                totals.attacks_attempted += 1
            distance_match = DISTANCE_TOTAL_RE.search(line)
            if distance_match:
                totals.movement_distance_total += int(distance_match.group(1))
            mp_match = MP_SPENT_RE.search(line)
            if mp_match:
                totals.movement_mp_spent_total += int(mp_match.group(1))
            hold_match = HOLD_RE.search(line)
            if hold_match and hold_match.group(1) == "True":
                totals.hold_position_true += 1
            status_match = STATUS_RE.search(line)
            if status_match:
                statuses.setdefault(status_match.group(1), 0)
        elif "uzupełnia paliwo" in line:
            match = FUEL_RE.search(line)
            if match:
                totals.fuel_added += int(match.group(1))
        elif "uzupełnia CV" in line:
            match = CV_RE.search(line)
            if match:
                totals.cv_added += int(match.group(1))
        elif "atak na" in line and "damage_dealt" in line:
            match = ATTACK_RE.search(line)
            if match:
                success_flag, dealt, taken = match.groups()
                key = "success" if success_flag == "True" else "fail"
                attacks[key] += 1
                if success_flag == "True":
                    attacks["damage_dealt_total"] += int(dealt)
                    attacks["damage_taken_total"] += int(taken)

    return {
        "totals": totals,
        "actions": actions,
        "statuses": statuses,
        "attacks": attacks,
        "movement_modes": movement_modes,
    }


def format_report(results: Dict[str, object]) -> str:
    totals: Totals = results["totals"]
    actions: Counter = results["actions"]
    statuses: Counter = results["statuses"]
    attacks: Counter = results["attacks"]
    movement_modes: Counter = results.get("movement_modes", Counter())

    lines = []
    lines.append("=== Token Autonomy Summary ===")
    lines.append(f"Entries logged: {totals.entries}")
    if totals.entries:
        move_rate = totals.movement_success / max(1, totals.entries)
        lines.append(
            f"Movement success: {totals.movement_success}/{totals.entries} attempts (avg attempts {totals.movement_attempts / max(1, totals.entries):.2f}, success rate {move_rate:.1%})"
        )
    lines.append(f"Resupply spent PE: {totals.resupply_spent}")
    lines.append(f"Reserved PE returned: {totals.reserved_pe}")
    lines.append(f"Fuel restored: {totals.fuel_added}")
    lines.append(f"Combat value restored: {totals.cv_added}")
    lines.append(f"Hold position triggers: {totals.hold_position_true}")
    avg_distance_entry = totals.movement_distance_total / max(1, totals.entries)
    avg_distance_success = totals.movement_distance_total / max(1, totals.movement_success)
    avg_mp_success = totals.movement_mp_spent_total / max(1, totals.movement_success)
    lines.append(
        f"Movement distance total: {totals.movement_distance_total} (avg per entry {avg_distance_entry:.2f}, avg per successful mover {avg_distance_success:.2f})"
    )
    lines.append(
        f"Movement MP spent total: {totals.movement_mp_spent_total} (avg per successful mover {avg_mp_success:.2f})"
    )

    if totals.planned_attacks or totals.attacks_attempted:
        ratio = totals.attacks_attempted / max(1, totals.planned_attacks)
        lines.append(
            f"Planned vs executed attacks: {totals.planned_attacks} planned / {totals.attacks_attempted} executed ({ratio:.1%})"
        )

    if statuses:
        lines.append("\nStatus distribution:")
        for status, count in statuses.most_common():
            lines.append(f"  - {status}: {count}")

    if movement_modes:
        lines.append("\nMovement modes usage:")
        for mode, count in movement_modes.most_common():
            lines.append(f"  - {mode}: {count}")

    if actions:
        lines.append("\nPlanned actions frequency:")
        for action, count in actions.most_common():
            lines.append(f"  - {action}: {count}")

    if attacks:
        success = attacks.get("success", 0)
        fail = attacks.get("fail", 0)
        lines.append("\nCombat summary:")
        lines.append(f"  Success: {success}, Fail: {fail}")
        if success:
            lines.append(f"  Damage dealt (sum): {attacks.get('damage_dealt_total', 0)}")
            lines.append(f"  Damage taken (sum): {attacks.get('damage_taken_total', 0)}")

    return "\n".join(lines)


def pick_latest(path: Path) -> Optional[Path]:
    if path.is_file():
        return path
    candidates = sorted(path.glob("*.log"))
    return candidates[-1] if candidates else None


def main() -> None:
    parser = argparse.ArgumentParser(description="Analyze TokenAI autonomy logs")
    parser.add_argument(
        "log_path",
        nargs="?",
        default="ai/logs/tokens/text",
        help="Path to log file or directory (default: latest token text log)",
    )
    args = parser.parse_args()

    candidate = pick_latest(Path(args.log_path))
    if not candidate or not candidate.exists():
        raise SystemExit(f"No log file found under {args.log_path!r}")

    with candidate.open("r", encoding="utf-8") as fh:
        results = analyze_lines(fh)

    print(format_report(results))


if __name__ == "__main__":
    main()
