"""Moduł rajdów opportunistycznych: szybkie przechwytywanie wolnych punktów kluczowych.
Wydzielone z ai_commander.opportunistic_capture_phase
"""
from __future__ import annotations
from typing import List, Dict, Any

# Stałe / progi – mogą być w przyszłości scentralizowane
FREE_KEYPOINT_VALUE_DISTANCE_FACTOR = 1.2

try:
    from main_ai import debug_print  # type: ignore
except Exception:  # fallback
    def debug_print(msg, level="BASIC", category="INFO"):
        print(f"[AI_RAID] {msg}")


def opportunistic_capture_phase(game_engine, my_units: List[Dict[str, Any]], player_id):
    """Szybka próba zajęcia wolnych keypointów osiągalnych w tej turze.
    Kryterium solo-rajdu: (value / distance) >= FREE_KEYPOINT_VALUE_DISTANCE_FACTOR
    Zwraca listę hex_id przejętych punktów.
    """
    captured: List[str] = []
    try:
        board = getattr(game_engine, 'board', None)
        kp_state = getattr(game_engine, 'key_points_state', {}) or {}
        if not board or not kp_state:
            return captured

        # Lista wolnych punktów
        free_kps = []
        for hex_id, kp in kp_state.items():
            if kp.get('current_value', 0) <= 0:
                continue
            try:
                q, r = map(int, hex_id.split(','))
            except Exception:
                continue
            occupied = False
            for t in getattr(game_engine, 'tokens', [])[:400]:
                if getattr(t, 'q', None) == q and getattr(t, 'r', None) == r:
                    occupied = True
                    break
            if not occupied:
                free_kps.append((hex_id, q, r, kp))
        if not free_kps:
            return captured

        for unit in my_units:
            if unit.get('mp', 0) <= 0:
                continue
            if unit.get('fuel', 0) <= 0:
                # Spróbuj uzupełnić
                current_player = getattr(game_engine, 'current_player_obj', None)
                if current_player and hasattr(current_player, 'is_ai_commander'):
                    commander_ref = getattr(game_engine, 'current_player_commander', None)
                    if commander_ref and hasattr(commander_ref, 'tactical_resupply'):
                        try:
                            if commander_ref.tactical_resupply(game_engine, "LOW_FUEL"):
                                unit['fuel'] = getattr(unit.get('token'), 'currentFuel', 0)
                                if unit.get('fuel', 0) <= 0:
                                    continue
                            else:
                                continue
                        except Exception:
                            continue
                    else:
                        continue
                else:
                    continue

            pos = (unit['q'], unit['r'])
            best_target = None
            best_score = 0.0
            for hex_id, q, r, kp in free_kps:
                try:
                    dist = board.hex_distance(pos, (q, r)) if board else 999
                except Exception:
                    continue
                if dist <= 0 or dist > min(unit['mp'], unit['fuel']):
                    continue
                value = kp.get('current_value', 0)
                if value <= 0:
                    continue
                score = value / dist
                if score >= FREE_KEYPOINT_VALUE_DISTANCE_FACTOR and score > best_score:
                    best_score = score
                    best_target = (hex_id, q, r)
            if best_target:
                hex_id, tq, tr = best_target
                try:
                    from ai.ruch_jednostek import move_towards  # local import to avoid cycles
                    if move_towards(unit, (tq, tr), game_engine):
                        unit['moved_capture'] = True
                        captured.append(hex_id)
                except Exception as e:
                    debug_print(f"[RAID] Move error {e}", "BASIC", "ERROR")
    except Exception as e:
        debug_print(f"[RAID] Błąd fazy opportunistycznej: {e}", "BASIC", "ERROR")
    return captured
