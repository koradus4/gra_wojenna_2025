"""Inspect TokenAI log for potential behavior anomalies."""
from __future__ import annotations

import re
from pathlib import Path
from typing import Dict, Optional, Tuple

START_RE = re.compile(
    r"\[\d{2}:\d{2}:\d{2}\] \[INFO] \[TOKEN] (?P<token>[^:]+): start tury \(budżet PE=(?P<budget>\d+)\) \| (?P<fields>.+)"
)
END_RE = re.compile(
    r"\[\d{2}:\d{2}:\d{2}\] \[INFO] \[TOKEN] (?P<token>[^:]+): koniec tury \(wydane PE=(?P<spent>\d+)\) \| (?P<fields>.+)"
)
FIELD_RE = re.compile(r"(\w+)=([^,]+)")
PLANNED_RE = re.compile(r"planned_actions=\[(.*?)\]")


def parse_fields(blob: str) -> Dict[str, str]:
    fields = {key: value.strip() for key, value in FIELD_RE.findall(blob)}
    planned_match = PLANNED_RE.search(blob)
    if planned_match:
        fields["planned_actions"] = planned_match.group(1)
    return fields


def main(path: str = "ai/logs/tokens/text/2025-10-02.log") -> None:
    log_path = Path(path)
    if not log_path.exists():
        raise SystemExit(f"Log file {path} not found")

    pending: Dict[str, Dict[str, str]] = {}
    anomalies = []

    with log_path.open("r", encoding="utf-8") as fh:
        for line in fh:
            start_match = START_RE.match(line)
            if start_match:
                token = start_match.group("token")
                fields = parse_fields(start_match.group("fields"))
                pending[token] = fields
                continue
            end_match = END_RE.match(line)
            if end_match:
                token = end_match.group("token")
                summary_fields = parse_fields(end_match.group("fields"))
                start_fields = pending.pop(token, {})
                move_success = summary_fields.get("movement_success", "False") == "True"
                attack_attempted = summary_fields.get("attack_attempted", "False") == "True"

                try:
                    start_mp = int(start_fields.get("move_points", "0"))
                    start_fuel = int(start_fields.get("fuel", "0"))
                except ValueError:
                    start_mp = start_fuel = 0
                planned = start_fields.get("planned_actions", "")

                if move_success and start_mp <= 0:
                    anomalies.append((token, "movement_without_mp", start_mp, planned))
                if move_success and start_fuel <= 0 and "refuel_minimum" not in planned:
                    anomalies.append((token, "movement_without_fuel", start_fuel, planned))
                if attack_attempted and "attack" not in planned:
                    anomalies.append((token, "attack_without_plan", 0, planned))

    print(f"Potential anomalies detected: {len(anomalies)}")
    for entry in anomalies[:20]:
        print(entry)
    if len(anomalies) > 20:
        print("...")


if __name__ == "__main__":
    main()
