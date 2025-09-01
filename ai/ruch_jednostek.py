"""Moduł ruchu AI (wydzielony z ai_commander).
Zawiera logikę wyboru trybu ruchu oraz funkcję move_towards z progressive movement.
"""
from __future__ import annotations
from typing import Any, Tuple

__all__ = ["choose_movement_mode", "move_towards"]

# Uwaga: funkcje zakładają istnienie pomocniczych funkcji scan_for_enemies, calculate_progressive_target,
# logowania oraz stałych typu HEX_MISSING_LOG_PREFIX w środowisku wywołującym (ai_commander).

def choose_movement_mode(unit: dict, target: Tuple[int,int], game_engine: Any) -> str:
    print(f"🧠 [AI TEST] CHOOSE_MOVEMENT_MODE wywołane dla {unit.get('id', 'UNKNOWN')}")
    unit_pos = (unit['q'], unit['r'])
    board = getattr(game_engine, 'board', None)
    if not board:
        print(f"🧠 [AI TEST] BRAK BOARD - zwracam combat")
        return 'combat'
    enemies_nearby = scan_for_enemies(unit_pos, game_engine, range=6)  # type: ignore[name-defined]
    print(f"🧠 [AI TEST] Wrogów w pobliżu: {len(enemies_nearby)}")
    if enemies_nearby:
        closest_enemy_distance = min(enemy[1] for enemy in enemies_nearby)
        print(f"🧠 [AI TEST] Najbliższy wróg: {closest_enemy_distance} pól")
        if closest_enemy_distance > 6:
            print(f"🧠 [AI TEST] Daleki wróg -> MARCH")
            return 'march'
        elif closest_enemy_distance > 3:
            print(f"🧠 [AI TEST] Średni dystans -> COMBAT")
            return 'combat'
        else:
            print(f"🧠 [AI TEST] Blisko wroga -> RECON")
            return 'recon'
    else:
        distance_to_target = board.hex_distance(unit_pos, target)
        print(f"🧠 [AI TEST] Brak wrogów, dystans do celu: {distance_to_target}")
        if distance_to_target > 10:
            print(f"🧠 [AI TEST] Daleki cel -> MARCH")
            return 'march'
        elif distance_to_target > 5:
            print(f"🧠 [AI TEST] Średni cel -> MARCH (ryzykownie)")
            return 'march'
        else:
            print(f"🧠 [AI TEST] Blisko celu -> COMBAT")
            return 'combat'


def move_towards(unit: dict, target: Tuple[int,int], game_engine: Any) -> bool:
    print(f"🚀 [AI TEST] MOVE_TOWARDS WYWOŁANE! {unit['id']}: ({unit['q']},{unit['r']}) -> {target}")
    from ai.ai_commander import HEX_MISSING_LOG_PREFIX  # lokalny import aby uniknąć cykli przy starcie
    import os
    os.makedirs('logs', exist_ok=True)
    with open("logs/movement_test.log", "a", encoding="utf-8") as f:
        f.write(f"MOVE_TOWARDS START: {unit['id']} -> {target}\n")
    board = getattr(game_engine, 'board', None)
    if not board:
        print(f"[AI] Brak board w game_engine")
        return False
    unit_pos = (unit['q'], unit['r'])
    token = unit.get('token', None)
    if token is None:
        print(f"[AI] Brak tokenu w unit dict")
        return False
    if isinstance(token, str):
        all_tokens = getattr(game_engine, 'tokens', [])
        for t in all_tokens:
            if getattr(t, 'id', None) == token:
                token = t
                break
        else:
            print(f"[AI] Nie znaleziono obiektu tokenu dla id: {token}")
            return False
    target_tuple = tuple(target) if isinstance(target, list) else target
    print(f"[AI Pathfinding] Konwersja: {target} -> {target_tuple}")
    print(f"🔍 [AI TEST] Sprawdzam token: {type(token)}, hasattr movement_mode: {hasattr(token, 'movement_mode')}")
    with open("logs/movement_test.log", "a", encoding="utf-8") as f:
        f.write(f"WYBOR TRYBU START: {unit['id']}, token_type: {type(token)}\n")
    optimal_mode = choose_movement_mode(unit, target_tuple, game_engine)
    print(f"🎯 [AI TEST] Wybrany tryb: {optimal_mode}")
    with open("logs/movement_test.log", "a", encoding="utf-8") as f:
        f.write(f"WYBRANY TRYB: {optimal_mode}\n")
    if hasattr(token, 'movement_mode') and not getattr(token, 'movement_mode_locked', False):
        if token.movement_mode != optimal_mode:
            token.movement_mode = optimal_mode
            token.apply_movement_mode()
            print(f"✅ [AI Movement] Zmieniono tryb ruchu na: {optimal_mode}")
            unit['mp'] = getattr(token, 'currentMovePoints', getattr(token, 'maxMovePoints', unit.get('mp',0)))
        else:
            print(f"🔄 [AI Movement] Tryb ruchu już ustawiony: {optimal_mode}")
    else:
        print(f"❌ [AI TEST] NIE MOGĘ ZMIENIĆ TRYBU - hasattr: {hasattr(token, 'movement_mode')}, locked: {getattr(token, 'movement_mode_locked', 'BRAK')}")
    if hasattr(board, 'get_tile') and board.get_tile(target_tuple[0], target_tuple[1]) is None:
        print(f"{HEX_MISSING_LOG_PREFIX} target {target_tuple}")
    hex_distance = board.hex_distance(unit_pos, target_tuple)
    max_reach = min(unit['mp'], unit['fuel'])
    if hex_distance > max_reach:
        print(f"[AI Pathfinding] ⚠️ Cel za daleko! Dystans: {hex_distance}, Zasięg: {max_reach}")
        progressive = calculate_progressive_target(unit, target_tuple, game_engine)  # type: ignore[name-defined]
        if progressive and progressive != unit_pos:
            target_tuple = progressive
            hex_distance = board.hex_distance(unit_pos, target_tuple)
    # Próba ścieżki
    base_path = board.find_path(unit_pos, target_tuple, max_mp=max_reach, max_fuel=max_reach)
    print(f"[AI Pathfinding] Bazowa ścieżka: {base_path}")
    if not base_path or len(base_path) < 2:
        # Adaptacja: skrócony ruch w promieniu
        print(f"[AI Pathfinding][DIAG] Brak ścieżki bazowej do {target_tuple} | terrain={getattr(board.get_tile(target_tuple[0], target_tuple[1]), 'terrain', None) if hasattr(board,'get_tile') else None} occupied=False neighbors={ [str(n) for n in getattr(board,'get_neighbors', lambda *_:[]) (target_tuple[0], target_tuple[1])] if hasattr(board,'get_neighbors') else []}")
        if hex_distance > max_reach:
            fallback = calculate_progressive_target(unit, target_tuple, game_engine)  # type: ignore[name-defined]
            if fallback and fallback != unit_pos:
                print(f"[AI Pathfinding][ADAPT] Brak ścieżki do {target_tuple}, używam krótszego {fallback} (frac={(max_reach/hex_distance if hex_distance else 1):.2f})")
                base_path = board.find_path(unit_pos, fallback, max_mp=max_reach, max_fuel=max_reach)
        if not base_path or len(base_path) < 2:
            print(f"[AI Pathfinding] ❌ Brak ścieżki po adaptacji!")
            return False
    # Wykonanie ruchu
    try:
        if hasattr(board, 'move_token'):
            success = board.move_token(token, target_tuple[0], target_tuple[1])
        else:
            success = False
    except Exception as e:
        print(f"[AI Move] ❌ Błąd: {e}")
        success = False
    if success:
        print(f"[AI Pathfinding] ✅ Pełna ścieżka ({len(base_path)-1}): {base_path}")
        unit['q'], unit['r'] = target_tuple
        if hasattr(token, 'currentMovePoints'):
            token.currentMovePoints = max(0, getattr(token, 'currentMovePoints', 0) - 1)
    else:
        print(f"[AI Move] ❌ Błąd: Brak ścieżki do celu.")
    return success
