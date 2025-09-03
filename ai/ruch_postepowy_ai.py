"""Moduł obliczania progresywnego celu ruchu (wydzielony z ai_commander)."""
from __future__ import annotations
from typing import Tuple, Dict, Any

try:
    from main_ai import debug_print  # type: ignore
except Exception:
    def debug_print(msg, level="BASIC", category="INFO"):
        print(f"[AI_RUCH_POSTEPOWY] {msg}")

HEX_MISSING_LOG_PREFIX = "[AI HEX] HEX_MISSING"

def calculate_progressive_target(unit: Dict[str, Any], final_target, game_engine):
    """Wyznacz cel pośredni dla jednostki, jeśli nie dojdzie do final_target w tej turze."""
    board = getattr(game_engine, 'board', None)
    if not board:
        return final_target
    unit_pos = (unit['q'], unit['r'])
    final_pos = tuple(final_target) if isinstance(final_target, list) else final_target
    max_reach = min(unit.get('mp', 0), unit.get('fuel', 0))
    if max_reach <= 0:
        return unit_pos
    direction_q = 1 if final_pos[0] > unit_pos[0] else (-1 if final_pos[0] < unit_pos[0] else 0)
    direction_r = 1 if final_pos[1] > unit_pos[1] else (-1 if final_pos[1] < unit_pos[1] else 0)
    for distance in range(max_reach, max(1, max_reach // 2), -1):
        candidates = [
            (unit_pos[0] + direction_q * distance, unit_pos[1] + direction_r * distance),
            (unit_pos[0] + direction_q * distance + 1, unit_pos[1] + direction_r * distance),
            (unit_pos[0] + direction_q * distance - 1, unit_pos[1] + direction_r * distance),
            (unit_pos[0] + direction_q * distance, unit_pos[1] + direction_r * distance + 1),
            (unit_pos[0] + direction_q * distance, unit_pos[1] + direction_r * distance - 1),
            (unit_pos[0] + distance, unit_pos[1]),
            (unit_pos[0], unit_pos[1] + distance),
            (unit_pos[0] - distance, unit_pos[1]),
            (unit_pos[0], unit_pos[1] - distance),
        ]
        best_candidate = None
        best_progress = 0
        for candidate in candidates:
            if hasattr(board, 'get_tile') and board.get_tile(candidate[0], candidate[1]) is None:
                debug_print(f"{HEX_MISSING_LOG_PREFIX} progressive_target {candidate}", "FULL", "WARN")
                continue
            path = board.find_path(unit_pos, candidate, max_mp=unit.get('mp', 99), max_fuel=unit.get('fuel', 99))
            if not path or len(path) < 2:
                continue
            try:
                old_distance = board.hex_distance(unit_pos, final_pos)
                new_distance = board.hex_distance(candidate, final_pos)
            except Exception:
                continue
            progress = old_distance - new_distance
            if progress > best_progress:
                best_candidate = candidate
                best_progress = progress
        if best_candidate:
            debug_print(f"[PROGRESSIVE] {unit.get('id')}: Postęp {best_progress} hexów w kierunku {final_pos}", "FULL", "PROGRESSIVE")
            return best_candidate
    for radius in range(1, max_reach + 1):
        for dq in range(-radius, radius + 1):
            for dr in range(-radius, radius + 1):
                if abs(dq + dr) > radius:
                    continue
                candidate = (unit_pos[0] + dq, unit_pos[1] + dr)
                path = board.find_path(unit_pos, candidate, max_mp=unit.get('mp', 99), max_fuel=unit.get('fuel', 99))
                if path and len(path) > 1:
                    debug_print(f"[PROGRESSIVE] {unit.get('id')}: Fallback movement {candidate}", "FULL", "PROGRESSIVE")
                    return candidate
    debug_print(f"[PROGRESSIVE] {unit.get('id')}: Brak możliwości ruchu", "FULL", "PROGRESSIVE")
    return unit_pos
