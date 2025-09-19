"""Moduł okupacji i garnizonów punktów kluczowych (wydzielony z ai_commander).
Zawiera limit garnizonów, rotację oraz funkcję enforce_garrison_limits.
"""
from __future__ import annotations
from typing import Any, Dict
from ai.logowanie_ai import log_kp_vacate_attempt, log_kp_vacate_blocked

__all__ = ["GARRISON_LIMITS", "enforce_garrison_limits"]

GARRISON_LIMITS: Dict[str, int] = {
    'default': 1,
    'miasto': 2,
    'fortyfikacja': 3,
    'most': 1,
    'węzeł komunikacyjny': 2
}

def enforce_garrison_limits(game_engine: Any, hex_id: str, kp_data: dict, token: Any, current_ratio: float) -> None:
    """Wymusza limity garnizonu i rotuje jednostki gdy punkt traci wartość lub stoi zbyt długo.
    Parametry pozostawione kompatybilne z poprzednim wywołaniem.
    """
    try:
        EARLY_ROTATION_THRESHOLD = 0.7
        MAX_GARRISON_TIME = 3
        garrison_tracker = getattr(game_engine, 'garrison_tracker', {})
        if not hasattr(game_engine, 'garrison_tracker'):
            game_engine.garrison_tracker = {}
            garrison_tracker = game_engine.garrison_tracker
        current_turn = getattr(game_engine, 'turn_number', getattr(game_engine, 'current_turn', 1))
        token_id = getattr(token, 'id', 'unknown')
        if hex_id not in garrison_tracker:
            garrison_tracker[hex_id] = {}
        if token_id not in garrison_tracker[hex_id]:
            garrison_tracker[hex_id][token_id] = current_turn
        turns_stationed = current_turn - garrison_tracker[hex_id][token_id]

        should_rotate = False
        reason = ""
        if current_ratio < EARLY_ROTATION_THRESHOLD:
            should_rotate = True
            reason = f"punkt wyczerpany ({current_ratio:.1%})"
        elif turns_stationed >= MAX_GARRISON_TIME:
            should_rotate = True
            reason = f"długi garnizon ({turns_stationed} tur)"

        # Nowe: presja logistyczna – jeśli paliwo/MP są bardzo niskie przez >=2 tury i w pobliżu jest Z, rozważ zwolnienie
        if not should_rotate:
            try:
                low_fuel = getattr(token, 'currentFuel', 0) <= 1
                low_mp = getattr(token, 'currentMovePoints', 0) <= 0
                # pamięć niskich zasobów per token
                if not hasattr(game_engine, 'garrison_low_supply_mem'):
                    game_engine.garrison_low_supply_mem = {}
                mem = game_engine.garrison_low_supply_mem
                cnt = mem.get(token_id, 0)
                if low_fuel or low_mp:
                    cnt += 1
                else:
                    cnt = 0
                mem[token_id] = cnt
                # Szukaj jednostki zaopatrzeniowej w zasięgu 2
                nearby_supply = False
                board = getattr(game_engine, 'board', None)
                if board and hasattr(board, 'hex_distance'):
                    for t in getattr(game_engine, 'tokens', [])[:200]:
                        # Tylko własna nacja
                        if getattr(t, 'owner', '').split(' ')[0] != getattr(token, 'owner', '').split(' ')[0]:
                            continue
                        if getattr(t, 'stats', {}).get('unitType', '') == 'Z':
                            d = board.hex_distance((getattr(t, 'q', 0), getattr(t, 'r', 0)), (int(hex_id.split(',')[0]), int(hex_id.split(',')[1])))
                            if d <= 2:
                                nearby_supply = True
                                break
                if cnt >= 2 and nearby_supply:
                    should_rotate = True
                    reason = 'logistics_pressure'
            except Exception:
                pass

        if should_rotate:
            setattr(token, 'hold_position', False)
            if token_id in garrison_tracker[hex_id]:
                del garrison_tracker[hex_id][token_id]
            print(f"[ROTATION] {token_id} zwolniony z {hex_id}: {reason}")
            try:
                log_kp_vacate_attempt(token_id, getattr(game_engine,'current_player_nation','Unknown'), hex_id, current_ratio, turns_stationed, reason)
            except Exception:
                pass
        else:
            print(f"[GARRISON] {token_id} pozostaje na {hex_id} (tura {turns_stationed+1}, wartość {current_ratio:.1%})")
            try:
                log_kp_vacate_blocked(token_id, getattr(game_engine,'current_player_nation','Unknown'), hex_id, current_ratio, turns_stationed, 'wartość wysoka lub limit czasu nieprzekroczony')
            except Exception:
                pass
    except Exception as e:
        print(f"[GARRISON] Błąd rotacji: {e}")
