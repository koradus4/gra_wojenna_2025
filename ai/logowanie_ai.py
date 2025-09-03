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
    'skip_reason',
    # === NOWE KOLUMNY DIAGNOSTYCZNE AI (FAZA 1) ===
    'target_search_candidates','target_search_best_score','target_search_best_distance',
    'group_id','group_size','group_leader_pos','group_assignment_score',
    'strategic_state','aggression_level','priority_level','target_is_free',
    'fallback_used','enemy_distance','threat_assessment','coordination_mode',
    'ai_memory_target','reassignment_count','tactical_mode',
    # === DODATKOWE KOLUMNY FAZA 2 ===
    'pathfinding_failures','valid_candidates','total_candidates','unit_mp_available','unit_fuel_available'
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
    'casualties_turn','new_units_turn',
    # === NOWE KOLUMNY DIAGNOSTYCZNE TURA (FAZA 1) ===
    'total_targets_analyzed','avg_target_score','targets_with_fallback',
    'groups_without_targets','dynamic_reassignments','strategic_state',
    'aggression_level','high_priority_targets','free_targets_captured',
    'coordination_failures','memory_targets_used','tactical_resupply_calls',
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

__all__ = ["LOG_COLUMNS", "log_commander_action", "log_commander_turn", "log_target_analysis", "log_group_formation", "log_strategic_decision"]


def log_target_analysis(unit_id: str, candidates: int, best_score: float, best_distance: int, 
                       fallback_used: bool, player_nation: str = "Unknown", extra: Dict[str, Any] = None):
    """Loguje szczegółową analizę wyboru celu do CSV diagnostycznego."""
    diagnostic_data = {
        'action_type': 'target_analysis',
        'target_search_candidates': candidates,
        'target_search_best_score': best_score,
        'target_search_best_distance': best_distance,
        'fallback_used': fallback_used,
        'phase': 'target_selection',
        # Nowe kolumny FAZA 2
        'pathfinding_failures': extra.get('failed_paths', 0) if extra else 0,
        'valid_candidates': extra.get('valid_kp_count', 0) if extra else 0,
        'total_candidates': extra.get('kp_count', 0) if extra else 0,
        'unit_mp_available': extra.get('unit_mp', 0) if extra else 0,
        'unit_fuel_available': extra.get('unit_fuel', 0) if extra else 0
    }
    if extra:
        diagnostic_data.update(extra)
    
    log_commander_action(
        unit_id=unit_id,
        action_type='target_analysis',
        from_pos=None,
        to_pos=None,
        reason=f"Target analysis: {candidates} candidates, score {best_score:.2f}",
        player_nation=player_nation,
        extra=diagnostic_data
    )


def log_group_formation(group_id: int, group_size: int, leader_pos: tuple, assignment_score: float,
                       target_pos: tuple = None, player_nation: str = "Unknown", extra: Dict[str, Any] = None):
    """Loguje informacje o formowaniu grup do CSV diagnostycznego."""
    diagnostic_data = {
        'action_type': 'group_formation',
        'group_id': group_id,
        'group_size': group_size,
        'group_leader_pos': f"{leader_pos[0]},{leader_pos[1]}" if leader_pos else None,
        'group_assignment_score': assignment_score,
        'phase': 'grouping'
    }
    if target_pos:
        diagnostic_data.update({
            'target_q': target_pos[0],
            'target_r': target_pos[1]
        })
    if extra:
        diagnostic_data.update(extra)
    
    log_commander_action(
        unit_id=f"GROUP_{group_id}",
        action_type='group_formation',
        from_pos=leader_pos,
        to_pos=target_pos,
        reason=f"Group {group_id}: {group_size} units, score {assignment_score:.2f}",
        player_nation=player_nation,
        extra=diagnostic_data
    )


def log_strategic_decision(strategic_state: str, aggression_level: float, total_groups: int,
                         reassignments: int, player_nation: str = "Unknown", extra: Dict[str, Any] = None):
    """Loguje kluczowe decyzje strategiczne do CSV diagnostycznego."""
    diagnostic_data = {
        'action_type': 'strategic_decision',
        'strategic_state': strategic_state,
        'aggression_level': aggression_level,
        'reassignment_count': reassignments,
        'phase': 'strategy'
    }
    if extra:
        diagnostic_data.update(extra)
    
    log_commander_action(
        unit_id="STRATEGY",
        action_type='strategic_decision',
        from_pos=None,
        to_pos=None,
        reason=f"Strategy: {strategic_state}, aggression {aggression_level:.2f}, {total_groups} groups, {reassignments} reassignments",
        player_nation=player_nation,
        extra=diagnostic_data
    )


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
