"""Moduł logowania AI Commandera (wydzielony z ai_commander).
Zachowuje te same nazwy: LOG_COLUMNS, log_commander_action.
"""
from __future__ import annotations
import csv
from datetime import datetime
from pathlib import Path
from typing import Any, Dict

LOG_COLUMNS = [
    'timestamp','turn','phase','nation','unit_id','unit_type','action_type',
    'from_q','from_r','to_q','to_r',
    'target_q','target_r','target_type','target_value_before','target_value_after',
    'movement_mode','path_len','path_used','progressive_used','adaptive_frac',
    'mp_before','mp_after','fuel_before','fuel_after',
    'combat_dmg_dealt','combat_dmg_taken','enemy_adj_before','enemy_adj_after',
    'threat_level','decision_reason','extra_tags','reason',
    # NOWA KOLUMNA (placeholder) – przy przyszłych logach stagnacji
    'skip_reason'
]

LOG_DIR = Path('logs/ai_commander')
LOG_DIR.mkdir(parents=True, exist_ok=True)
LOG_FILE = LOG_DIR / f"actions_{datetime.now().strftime('%Y%m%d')}.csv"

# Dodatkowy plik zbiorczy podsumowań tur dowódców (łatwa analiza AI vs AI)
TURN_LOG_COLUMNS = [
    'timestamp','turn','nation','mode','groups','units_total','units_moved','moved_pct',
    'opportunistic_captures','combats','retreats','deployments',
    'resupply_attempts','resupply_successes',
    'threatened_units','low_income_streak','econ_weight','vp_weight',
    'artillery_units','artillery_shots','artillery_reaction_used','artillery_avg_shots',
    # NOWE METRYKI – dodane na końcu (additive only)
    'casualties_turn','new_units_turn',
    'notes'
]
TURN_LOG_FILE = LOG_DIR / f"turns_{datetime.now().strftime('%Y%m%d')}.csv"


def log_commander_action(unit_id: str, action_type: str, from_pos, to_pos, reason: str,
                         player_nation: str = "Unknown", extra: Dict[str, Any] | None = None):
    """Loguj akcję AI Commander do CSV.
    extra: dict z dodatkowymi polami zgodnymi z LOG_COLUMNS.
    """
    try:
        turn = None
        phase = None
        unit_type = None
        timestamp = datetime.now().isoformat()
        row_dict = {k: None for k in LOG_COLUMNS}
        row_dict.update({
            'timestamp': timestamp,
            'turn': turn,
            'phase': phase,
            'nation': player_nation,
            'unit_id': unit_id,
            'unit_type': unit_type,
            'action_type': action_type,
            'from_q': from_pos[0] if from_pos else None,
            'from_r': from_pos[1] if from_pos else None,
            'to_q': to_pos[0] if to_pos else None,
            'to_r': to_pos[1] if to_pos else None,
            'reason': reason
        })
        if extra:
            for k, v in extra.items():
                if k in row_dict:
                    row_dict[k] = v
        file_exists = LOG_FILE.exists()
        with open(LOG_FILE, 'a', newline='', encoding='utf-8') as f:
            writer = csv.writer(f)
            if not file_exists:
                writer.writerow(LOG_COLUMNS)
            values = [row_dict[k] for k in LOG_COLUMNS]
            writer.writerow(values)
    except Exception:
        # Ciche pominięcie w razie błędu logowania aby nie blokować AI
        pass

__all__ = ["LOG_COLUMNS", "log_commander_action"]


def log_commander_turn(data: Dict[str, Any]):
    """Loguje zagregowane metryki tury dowódcy do osobnego pliku CSV.

    Oczekiwane klucze w data (brakujące zostaną uzupełnione None): TURN_LOG_COLUMNS.
    Bezpieczne – w razie błędu pomija zapis.
    """
    try:
        file_exists = TURN_LOG_FILE.exists()
        row = {k: None for k in TURN_LOG_COLUMNS}
        row.update(data)
        # timestamp jeśli nie podano
        if not row.get('timestamp'):
            row['timestamp'] = datetime.now().isoformat()
        with open(TURN_LOG_FILE, 'a', newline='', encoding='utf-8') as f:
            w = csv.writer(f)
            if not file_exists:
                w.writerow(TURN_LOG_COLUMNS)
            w.writerow([row[k] for k in TURN_LOG_COLUMNS])
    except Exception:
        pass

__all__.append("log_commander_turn")
