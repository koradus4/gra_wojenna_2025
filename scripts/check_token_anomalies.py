"""Validate TokenAI log entries for economic invariants."""
from __future__ import annotations

import re
from pathlib import Path
from typing import Iterable, List, Tuple

END_RE = re.compile(
    r"\\[(?P<time>\\d{2}:\\d{2}:\\d{2})].*\\[TOKEN] (?P<token>[^:]+): koniec tury"
)
ALLOC_RE = re.compile(r"allocated_pe=(\\d+)")
SPENT_RE = re.compile(r"spent_pe=(\\d+)")
RES_RE = re.compile(r"reserved_pe=(\\d+)")


def find_anomalies(lines: Iterable[str]) -> List[Tuple[str, str, str, int, int, int]]:
    anomalies: List[Tuple[str, str, str, int, int, int]] = []
    for line in lines:
        if "koniec tury" not in line:
            continue
        end_match = END_RE.search(line)
        alloc_match = ALLOC_RE.search(line)
        spent_match = SPENT_RE.search(line)
        res_match = RES_RE.search(line)
        if not (end_match and alloc_match and spent_match and res_match):
            continue
        time = end_match.group("time")
        token = end_match.group("token")
        alloc = int(alloc_match.group(1))
        spent = int(spent_match.group(1))
        reserved = int(res_match.group(1))

        if spent > alloc:
            anomalies.append((time, token, "spent>allocated", alloc, spent, reserved))
        if reserved > alloc:
            anomalies.append((time, token, "reserved>allocated", alloc, spent, reserved))
        if alloc > 0 and spent + reserved > alloc:
            anomalies.append((time, token, "spent+reserved>allocated", alloc, spent, reserved))
    return anomalies


def main(path: str = "ai/logs/tokens/text/2025-10-02.log") -> None:
    log_path = Path(path)
    if not log_path.exists():
        raise SystemExit(f"Log file {path} not found")
    with log_path.open("r", encoding="utf-8") as fh:
        anomalies = find_anomalies(fh)
    print(f"Total anomalies: {len(anomalies)}")
    for item in anomalies[:20]:
        print(item)
    if len(anomalies) > 20:
        print("...")


if __name__ == "__main__":
    main()
