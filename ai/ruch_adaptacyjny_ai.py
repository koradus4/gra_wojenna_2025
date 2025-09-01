"""Moduł adaptacyjnych taktyk ruchu AI.

Przeniesione z klasy AdaptiveAICommander:
 - _adaptive_movement_tactics
 - _find_defensive_position_near
 - _is_position_safe

Cel: uproszczenie ai_commander.py i separacja logiki taktycznej.
"""
from __future__ import annotations

from typing import Any, Dict, Tuple


HEX_DIRECTIONS = [(1,0), (0,1), (-1,1), (-1,0), (0,-1), (1,-1)]


def _adaptive_movement_tactics(ai, unit: Dict[str, Any], base_target: Tuple[int, int], strategic_plan: Dict[str, Any], game_engine):
    """Adaptacyjne taktyki ruchu na podstawie planu strategicznego (przeniesione)."""
    try:
        aggression_level = strategic_plan.get('aggression_level', 0.5)
        strategic_state = strategic_plan.get('state', 'TIED')

        final_target = base_target

        if strategic_state == "LOSING" and aggression_level > 0.7:
            print(f"⚔️ [ADAPTIVE] {unit['id']}: Agresywny atak na {base_target}")
            final_target = base_target
        elif strategic_state == "WINNING" and aggression_level < 0.4:
            defensive_pos = _find_defensive_position_near(ai, base_target, unit, game_engine)
            if defensive_pos != base_target:
                print(f"🛡️ [ADAPTIVE] {unit['id']}: Pozycja defensywna {defensive_pos} zamiast {base_target}")
                final_target = defensive_pos
        else:
            print(f"⚖️ [ADAPTIVE] {unit['id']}: Zbalansowany ruch do {base_target}")
            final_target = base_target

        return final_target
    except Exception as e:
        print(f"❌ [ADAPTIVE] Błąd taktyki ruchu: {e}")
        return base_target


def _find_defensive_position_near(ai, target: Tuple[int, int], unit: Dict[str, Any], game_engine):
    try:
        board = getattr(game_engine, 'board', None)
        if not board:
            return target
        for distance in [1, 2]:
            for direction in HEX_DIRECTIONS:
                candidate = (target[0] + direction[0]*distance, target[1] + direction[1]*distance)
                if not board.is_occupied(candidate[0], candidate[1]):
                    if _is_position_safe(ai, candidate, game_engine):
                        return candidate
        return target
    except Exception:
        return target


def _is_position_safe(ai, position: Tuple[int, int], game_engine) -> bool:
    try:
        recon_data = ai.reconnaissance_data
        if not recon_data or 'visible_enemies' not in recon_data:
            return True
        for enemy in recon_data['visible_enemies']:
            enemy_pos = enemy['position']
            # prosta metryka axial distance (import z obrona_ai możliwy, ale unikamy zależności)
            distance = (abs(position[0]-enemy_pos[0]) + abs(position[0]+position[1]-enemy_pos[0]-enemy_pos[1]) + abs(position[1]-enemy_pos[1])) // 2
            if distance <= 3:
                return False
        return True
    except Exception:
        return True
