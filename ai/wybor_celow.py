"""Moduł wyboru i oceny celów (wydzielony z ai_commander).
Przeniesione: find_target, find_alternative_target, find_alternative_target_around, get_keypoint_value.
"""
from __future__ import annotations
from typing import Any, Dict, Tuple

__all__ = [
    'find_target','find_alternative_target','find_alternative_target_around',
    'get_keypoint_value'
]

def find_target(unit, game_engine):
    token = unit.get('token')
    if token and hasattr(token, 'ai_target_memory'):
        saved_target = getattr(token, 'ai_target_memory', None)
        if saved_target:
            key_points = getattr(game_engine, 'key_points_state', {})
            hex_id = f"{saved_target[0]},{saved_target[1]}"
            if hex_id in key_points and key_points[hex_id].get('current_value', 0) > 0:
                unit_pos = (unit['q'], unit['r'])
                if saved_target != unit_pos:
                    print(f"[AI MEMORY] {unit.get('id')} kontynuuje do zapisanego celu {saved_target}")
                    return saved_target
                else:
                    print(f"[AI MEMORY] {unit.get('id')} dotarł do celu {saved_target} - czyszczę pamięć")
                    delattr(token, 'ai_target_memory')

    key_points = getattr(game_engine, 'key_points_state', {})
    board = getattr(game_engine, 'board', None)
    if not board:
        return None

    unit_pos = (unit['q'], unit['r'])
    best_target = None
    best_distance = 999
    best_score = -1
    econ_weight = 1.0
    vp_weight = 0.5
    try:
        commander_obj = getattr(game_engine, 'current_player_commander', None)
        if commander_obj and hasattr(commander_obj, 'econ_weight'):
            econ_weight = commander_obj.econ_weight
            vp_weight = commander_obj.vp_weight
    except Exception:
        pass

    def kp_score(kp_dict: dict) -> float:
        ktype = kp_dict.get('type', 'unknown')
        base_val = kp_dict.get('current_value', kp_dict.get('value', 0))
        if ktype == 'economy':
            return base_val * econ_weight
        if ktype == 'victory':
            return base_val * vp_weight
        if ktype == 'mixed':
            return base_val * (0.5*econ_weight + 0.5*vp_weight)
        return base_val * 0.3

    kp_count = 0
    for hex_id, kp_data in key_points.items():
        if kp_count >= 20:
            break
        kp_count += 1
        if kp_data.get('current_value', 0) <= 0:
            continue
        try:
            if ',' in hex_id:
                parts = hex_id.split(',')
            else:
                parts = hex_id.split('_')
            if len(parts) >= 2:
                kp_q = int(parts[0]); kp_r = int(parts[1])
                kp_pos = (kp_q, kp_r)
                path = board.find_path(unit_pos, kp_pos, max_mp=unit['mp'], max_fuel=unit['fuel'])
                if path and len(path) > 1:
                    actual_distance = len(path) - 1
                    score = kp_score(kp_data)
                    if score > best_score or (score == best_score and actual_distance < best_distance):
                        best_target = kp_pos; best_distance = actual_distance; best_score = score
        except (ValueError, IndexError):
            continue

    if not best_target:
        max_mp = unit.get('mp', 1)
        for distance in range(min(max_mp, 5), 0, -1):
            candidates_found = []
            for direction in [(1,0),(0,1),(-1,1),(-1,0),(0,-1),(1,-1)]:
                candidate = (unit_pos[0]+direction[0]*distance, unit_pos[1]+direction[1]*distance)
                test_path = board.find_path(unit_pos, candidate, max_mp=max_mp, max_fuel=unit.get('fuel', 99))
                if test_path and len(test_path) > 1:
                    candidates_found.append(candidate)
            if candidates_found:
                best_target = candidates_found[0]
                break
        if not best_target:
            center = (10, 10)
            center_path = board.find_path(unit_pos, center, max_mp=unit.get('mp',1), max_fuel=unit.get('fuel',99))
            if center_path and len(center_path) > 1:
                best_target = center
            else:
                for dist in range(1, min(unit.get('mp',1)+1,6)):
                    dx = 1 if center[0] > unit_pos[0] else (-1 if center[0] < unit_pos[0] else 0)
                    dy = 1 if center[1] > unit_pos[1] else (-1 if center[1] < unit_pos[1] else 0)
                    candidate = (unit_pos[0]+dx*dist, unit_pos[1]+dy*dist)
                    fallback_path = board.find_path(unit_pos, candidate, max_mp=unit.get('mp',1), max_fuel=unit.get('fuel',99))
                    if fallback_path and len(fallback_path) > 1:
                        best_target = candidate
                        break

    if best_target and token:
        key_points = getattr(game_engine, 'key_points_state', {})
        hex_id = f"{best_target[0]},{best_target[1]}"
        if hex_id in key_points:
            try:
                setattr(token, 'ai_target_memory', best_target)
                print(f"[AI MEMORY] {unit.get('id')} zapisuje cel {best_target} do pamięci")
            except Exception:
                pass
    return best_target


def find_alternative_target_around(unit, base_target, game_engine, search_radius=3):
    board = getattr(game_engine, 'board', None)
    if not board:
        return base_target
    unit_pos = (unit['q'], unit['r'])
    base_q, base_r = base_target[0], base_target[1]
    if not board.is_occupied(base_q, base_r):
        return base_target
    best_alternative = None; best_distance = 999
    for radius in range(1, search_radius+1):
        for dq in range(-radius, radius+1):
            for dr in range(-radius, radius+1):
                if abs(dq+dr) > radius:
                    continue
                candidate = (base_q + dq, base_r + dr)
                if board.is_occupied(candidate[0], candidate[1]):
                    continue
                path = board.find_path(unit_pos, candidate, max_mp=unit.get('mp',1), max_fuel=unit.get('fuel',1))
                if not path or len(path) < 2:
                    continue
                distance = abs(candidate[0]-base_q) + abs(candidate[1]-base_r)
                if distance < best_distance:
                    best_alternative = candidate; best_distance = distance
        if best_alternative:
            break
    if best_alternative:
        print(f"[FORMATION] {unit.get('id')}: Cel {base_target} zajęty -> alternatywa {best_alternative}")
        return best_alternative
    else:
        print(f"[FORMATION] {unit.get('id')}: Brak wolnych miejsc wokół {base_target}")
        return base_target


def get_keypoint_value(target_pos, game_engine):
    key_points = getattr(game_engine, 'key_points_state', {})
    for hex_id, kp_data in key_points.items():
        try:
            if ',' in hex_id:
                q, r = map(int, hex_id.split(','))
            else:
                q, r = map(int, hex_id.split('_'))
            if (q, r) == target_pos:
                return kp_data.get('current_value', 0)
        except (ValueError, IndexError):
            continue
    return 0


def find_alternative_target(leader, key_points, reserved_targets):
    board = getattr(leader.get('token', None), 'board', None)
    if not board:
        return None
    leader_pos = (leader['q'], leader['r'])
    best_alternative = None; best_distance = 999
    for hex_id, kp_data in key_points.items():
        try:
            if ',' in hex_id:
                q, r = map(int, hex_id.split(','))
            else:
                q, r = map(int, hex_id.split('_'))
            target_pos = (q, r); target_key = f"{q},{r}"
            if target_key in reserved_targets:
                continue
            if kp_data.get('current_value', 0) <= 0:
                continue
            distance = abs(leader_pos[0]-q) + abs(leader_pos[1]-r)
            if distance < best_distance:
                best_alternative = target_pos; best_distance = distance
        except (ValueError, IndexError):
            continue
    return best_alternative
