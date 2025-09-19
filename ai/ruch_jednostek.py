"""Moduł ruchu AI (wydzielony z ai_commander).
Zawiera logikę wyboru trybu ruchu oraz funkcję move_towards z progressive movement.
"""
from __future__ import annotations
from typing import Any, Tuple
from ai.ai_config import get_param
from utils.turn_context import set_correlation_id, clear_correlation_id

__all__ = ["choose_movement_mode", "move_towards"]

# Uwaga: funkcje zakładają istnienie pomocniczych funkcji scan_for_enemies, calculate_progressive_target,
# logowania oraz stałych typu HEX_MISSING_LOG_PREFIX w środowisku wywołującym (ai_commander).
# Aby uniknąć NameError po refaktoryzacji stosujemy leniwe importy / fallback.

def _lazy_scan_for_enemies(unit_pos, game_engine, range=6):  # fallback prosty
    try:
        from ai.ai_commander import scan_for_enemies as _sfe
        return _sfe(unit_pos, game_engine, range=range)
    except Exception:
        return []

def _lazy_calculate_progressive_target(unit, final_target, game_engine):
    try:
        from ai.ai_commander import calculate_progressive_target as _cpt
        return _cpt(unit, final_target, game_engine)
    except Exception:
        return final_target

def choose_movement_mode(unit: dict, target: Tuple[int,int], game_engine: Any) -> str:
    # ZABEZPIECZENIE: sprawdź czy nie jesteśmy w nieskończonej pętli
    if not hasattr(choose_movement_mode, '_call_counter'):
        choose_movement_mode._call_counter = {}
    
    unit_id = unit.get('id', 'UNKNOWN')
    if unit_id not in choose_movement_mode._call_counter:
        choose_movement_mode._call_counter[unit_id] = 0
    
    choose_movement_mode._call_counter[unit_id] += 1
    
    if choose_movement_mode._call_counter[unit_id] > 2:
        print(f"⚠️ [AI LOOP PROTECTION] {unit_id} wywołano {choose_movement_mode._call_counter[unit_id]} razy - STOP! Zwracam combat")
        choose_movement_mode._call_counter[unit_id] = 0  # reset
        return 'combat'
    
    print(f"🧠 [AI TEST] CHOOSE_MOVEMENT_MODE wywołane dla {unit_id} (#{choose_movement_mode._call_counter[unit_id]})")
    unit_pos = (unit['q'], unit['r'])
    board = getattr(game_engine, 'board', None)
    if not board:
        print(f"🧠 [AI TEST] BRAK BOARD - zwracam combat")
        choose_movement_mode._call_counter[unit_id] = 0  # reset
        return 'combat'
    try:
        enemies_nearby = scan_for_enemies(unit_pos, game_engine, range=6)  # type: ignore[name-defined]
    except Exception:
        enemies_nearby = _lazy_scan_for_enemies(unit_pos, game_engine, range=6)
    print(f"🧠 [AI TEST] Wrogów w pobliżu: {len(enemies_nearby)}")
    
    result = 'combat'  # domyślnie
    if enemies_nearby:
        closest_enemy_distance = min(enemy[1] for enemy in enemies_nearby)
        print(f"🧠 [AI TEST] Najbliższy wróg: {closest_enemy_distance} pól")
        if closest_enemy_distance > 6:
            print(f"🧠 [AI TEST] Daleki wróg -> MARCH")
            result = 'march'
        elif closest_enemy_distance > 3:
            print(f"🧠 [AI TEST] Średni dystans -> COMBAT")
            result = 'combat'
        else:
            print(f"🧠 [AI TEST] Blisko wroga -> RECON")
            result = 'recon'
    else:
        distance_to_target = board.hex_distance(unit_pos, target)
        print(f"🧠 [AI TEST] Brak wrogów, dystans do celu: {distance_to_target}")
        if distance_to_target > 10:
            print(f"🧠 [AI TEST] Daleki cel -> MARCH")
            result = 'march'
        elif distance_to_target > 5:
            print(f"🧠 [AI TEST] Średni cel -> MARCH (ryzykownie)")
            result = 'march'
        else:
            print(f"🧠 [AI TEST] Blisko celu -> COMBAT")
            result = 'combat'
    
    # Reset licznika po pomyślnym wywołaniu
    choose_movement_mode._call_counter[unit_id] = 0
    return result


def move_towards(unit: dict, target: Tuple[int,int], game_engine: Any) -> bool:
    print(f"🚀 [AI TEST] MOVE_TOWARDS WYWOŁANE! {unit['id']}: ({unit['q']},{unit['r']}) -> {target}")
    from ai.logowanie_ai import log_move_aborted, log_path_planned
    from ai.ai_commander import HEX_MISSING_LOG_PREFIX  # lokalny import aby uniknąć cykli przy starcie
    import os
    os.makedirs('logs', exist_ok=True)
    with open("logs/movement_test.log", "a", encoding="utf-8") as f:
        f.write(f"MOVE_TOWARDS START: {unit['id']} -> {target}\n")
    board = getattr(game_engine, 'board', None)
    if not board:
        print(f"[AI] Brak board w game_engine")
        try:
            log_move_aborted(unit.get('id','UNKNOWN'), getattr(game_engine,'current_player_nation','Unknown'), (unit['q'], unit['r']), tuple(target) if isinstance(target, list) else target, 'fail', 'NO_BOARD', 'Brak planszy')
        except Exception:
            pass
        return False
    unit_pos = (unit['q'], unit['r'])
    token = unit.get('token', None)
    if token is None:
        print(f"[AI] Brak tokenu w unit dict")
        try:
            log_move_aborted(unit.get('id','UNKNOWN'), getattr(game_engine,'current_player_nation','Unknown'), (unit['q'], unit['r']), tuple(target) if isinstance(target, list) else target, 'fail', 'NO_TOKEN', 'Brak tokenu')
        except Exception:
            pass
        return False
    if isinstance(token, str):
        all_tokens = getattr(game_engine, 'tokens', [])
        for t in all_tokens:
            if getattr(t, 'id', None) == token:
                token = t
                break
        else:
            print(f"[AI] Nie znaleziono obiektu tokenu dla id: {token}")
            try:
                log_move_aborted(unit.get('id','UNKNOWN'), getattr(game_engine,'current_player_nation','Unknown'), (unit['q'], unit['r']), tuple(target) if isinstance(target, list) else target, 'fail', 'TOKEN_NOT_FOUND', 'Nie znaleziono instancji tokenu')
            except Exception:
                pass
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
        try:
            progressive = calculate_progressive_target(unit, target_tuple, game_engine)  # type: ignore[name-defined]
        except Exception:
            progressive = _lazy_calculate_progressive_target(unit, target_tuple, game_engine)
        if progressive and progressive != unit_pos:
            target_tuple = progressive
            hex_distance = board.hex_distance(unit_pos, target_tuple)
    # Próba ścieżki - używamy wartości odpowiednich do trybu ruchu po optymalizacji paliwa
    # Jeśli jednostka ma march mode i została zoptymalizowana, użyj większych limitów
    effective_mp = unit['mp']
    effective_fuel = unit['fuel']
    
    # Sprawdź czy jednostka ma march mode (zwiększone MP)
    if hasattr(token, 'movement_mode') and token.movement_mode == 'march':
        # March mode daje +50% MP, sprawdź czy to zostało już uwzględnione
        base_mp = getattr(token, 'maxMovePoints', unit.get('mp', 3))
        march_mp = int(base_mp * 1.5)
        if unit['mp'] < march_mp:
            effective_mp = march_mp
            print(f"[AI Pathfinding] Zwiększam MP dla march mode: {unit['mp']} -> {effective_mp}")
    
    # Dla wieloturowych planów, używaj wyższych limitów do znalezienia ścieżki
    if hasattr(unit, 'assigned_target') and unit.get('assigned_target'):
        effective_mp = max(effective_mp, 15)  # Wystarczająco wysokie dla pathfindingu
        effective_fuel = max(effective_fuel, 15)
        print(f"[AI Pathfinding] Plan wieloturowy: używam MP={effective_mp}, Fuel={effective_fuel}")
    
    # Nawet w combat mode, jednostka powinna móc znaleźć ścieżkę w promieniu 5-10 hexów
    # Ustaw minimalne limity dla pathfindingu - zwiększone dla przypadków ekstremalnych
    effective_mp = max(effective_mp, 20)   # zwiększone z 10 na 20
    effective_fuel = max(effective_fuel, 20)  # zwiększone z 10 na 20
    
    # Specjalne przypadki dla bardzo niskich zasobów
    if unit.get('fuel', 0) <= 1:
        effective_fuel = 25  # jeszcze wyższe minimum dla krytycznego braku paliwa
    if unit.get('mp', 0) <= 3:
        effective_mp = 25   # jeszcze wyższe minimum dla krytycznego braku MP
    
    base_path = board.find_path(unit_pos, target_tuple, max_mp=effective_mp, max_fuel=effective_fuel)
    print(f"[AI Pathfinding] Bazowa ścieżka (MP={effective_mp}, Fuel={effective_fuel}): {base_path}")
    try:
        if base_path:
            from ai.logowanie_ai import log_path_planned as _lpp
            _lpp(unit.get('id','UNKNOWN'), getattr(game_engine,'current_player_nation','Unknown'), unit_pos, target_tuple, len(base_path), effective_mp, effective_fuel)
    except Exception:
        pass
    if not base_path or len(base_path) < 2:
        # Adaptacja: skrócony ruch w promieniu
        print(f"[AI Pathfinding][DIAG] Brak ścieżki bazowej do {target_tuple} | terrain={getattr(board.get_tile(target_tuple[0], target_tuple[1]), 'terrain', None) if hasattr(board,'get_tile') else None} occupied=False neighbors={ [str(n) for n in getattr(board,'neighbors', lambda *_:[]) (target_tuple[0], target_tuple[1])] if hasattr(board,'neighbors') else []}")
        if hex_distance > max_reach:
            try:
                fallback = calculate_progressive_target(unit, target_tuple, game_engine)  # type: ignore[name-defined]
            except Exception:
                fallback = _lazy_calculate_progressive_target(unit, target_tuple, game_engine)
            if fallback and fallback != unit_pos:
                print(f"[AI Pathfinding][ADAPT] Brak ścieżki do {target_tuple}, używam krótszego {fallback} (frac={(max_reach/hex_distance if hex_distance else 1):.2f})")
                base_path = board.find_path(unit_pos, fallback, max_mp=effective_mp, max_fuel=effective_fuel)
        # Nowe: jeśli nadal brak ścieżki, spróbuj znaleźć najbliższy osiągalny heks wokół celu (pierścienie)
        nearest_reachable = None
        nearest_dist = None
        obstacle_hint = None
        if (not base_path or len(base_path) < 2) and hasattr(board, 'neighbors') and hasattr(board, 'find_path'):
            # przeszukaj pierścienie do 4 pól od celu
            try:
                max_ring = 4
                visited = set()
                frontier = [(target_tuple, 0)]
                while frontier:
                    (hq, hr), d = frontier.pop(0)
                    if (hq, hr) in visited or d > max_ring:
                        continue
                    visited.add((hq, hr))
                    path_try = board.find_path(unit_pos, (hq, hr), max_mp=effective_mp, max_fuel=effective_fuel)
                    if path_try and len(path_try) >= 2:
                        nearest_reachable = (hq, hr)
                        nearest_dist = d
                        break
                    # rozszerz sąsiedztwo
                    for n in board.neighbors(hq, hr):
                        frontier.append((n, d+1))
            except Exception:
                pass
            # podpowiedź przeszkody
            try:
                tile = board.get_tile(target_tuple[0], target_tuple[1]) if hasattr(board, 'get_tile') else None
                if tile and getattr(tile, 'occupied', False):
                    obstacle_hint = 'occupied'
                elif tile and getattr(tile, 'terrain', '') in ('water', 'mountain'):
                    obstacle_hint = f"terrain:{getattr(tile,'terrain','')}"
                else:
                    obstacle_hint = 'unknown'
            except Exception:
                obstacle_hint = None
        # Nowe: jeśli mamy najbliższy osiągalny heks, potraktuj jako waypoint i spróbuj ponownie
        if (not base_path or len(base_path) < 2) and nearest_reachable:
            print(f"[AI Pathfinding][WAYPOINT] Próbuję waypoint {nearest_reachable} (dist_ring={nearest_dist})")
            base_path = board.find_path(unit_pos, nearest_reachable, max_mp=effective_mp, max_fuel=effective_fuel)
        # Nowe: jeśli nadal brak, spróbuj side-step na sąsiednie dostępne heksy zbliżające do celu
        if not base_path or len(base_path) < 2:
            try:
                candidates = []
                for nq, nr in (board.neighbors(unit_pos[0], unit_pos[1]) if hasattr(board, 'neighbors') else []):
                    if board.hex_distance((nq, nr), target_tuple) < board.hex_distance(unit_pos, target_tuple):
                        p = board.find_path((nq, nr), target_tuple, max_mp=effective_mp, max_fuel=effective_fuel)
                        if p and len(p) >= 1:
                            candidates.append(((nq, nr), len(p)))
                if candidates:
                    candidates.sort(key=lambda x: x[1])
                    side_step = candidates[0][0]
                    print(f"[AI Pathfinding][SIDESTEP] Próba obejścia przez {side_step}")
                    base_path = [unit_pos, side_step]
                    target_tuple = side_step
            except Exception:
                pass
        if not base_path or len(base_path) < 2:
            print(f"[AI Pathfinding] ❌ Brak ścieżki po adaptacji!")
            try:
                # logowanie rozszerzone o najbliższy osiągalny i wskazówkę przeszkody
                nrd_q = nearest_reachable[0] if nearest_reachable else None
                nrd_r = nearest_reachable[1] if nearest_reachable else None
                log_move_aborted(unit.get('id','UNKNOWN'), getattr(game_engine,'current_player_nation','Unknown'), unit_pos, target_tuple, 'fail', 'NO_PATH', 'Brak ścieżki',
                                 nearest_reachable_dist=nearest_dist,
                                 nearest_reachable_hex_q=nrd_q,
                                 nearest_reachable_hex_r=nrd_r,
                                 obstacle_hint=obstacle_hint)
            except Exception:
                pass
            return False
    # Wykonanie ruchu - używamy token.set_position() jak w głównym silniku
    try:
        # Sprawdź czy mamy wystarczające zasoby
        if getattr(token, 'currentMovePoints', 0) <= 0:
            print(f"[AI Move] ❌ Brak punktów ruchu: {getattr(token, 'currentMovePoints', 0)}")
            try:
                log_move_aborted(unit.get('id','UNKNOWN'), getattr(game_engine,'current_player_nation','Unknown'), unit_pos, target_tuple, 'blocked', 'NO_MP', 'Brak punktów ruchu')
            except Exception:
                pass
            return False
        if getattr(token, 'currentFuel', 0) <= 0:
            print(f"[AI Move] ❌ Brak paliwa: {getattr(token, 'currentFuel', 0)}")
            try:
                log_move_aborted(unit.get('id','UNKNOWN'), getattr(game_engine,'current_player_nation','Unknown'), unit_pos, target_tuple, 'blocked', 'NO_FUEL', 'Brak paliwa')
            except Exception:
                pass
            return False
        
        # Wykonaj ruch używając tej samej metody co główny silnik
        if hasattr(token, 'set_position'):
            token.set_position(target_tuple[0], target_tuple[1])
            # Zmniejsz zasoby ruchu
            if hasattr(token, 'currentMovePoints'):
                token.currentMovePoints = max(0, getattr(token, 'currentMovePoints', 0) - 1)
            if hasattr(token, 'currentFuel'):
                token.currentFuel = max(0, getattr(token, 'currentFuel', 0) - 1)
            success = True
        else:
            print(f"[AI Move] ❌ Token nie ma metody set_position")
            success = False
    except Exception as e:
        print(f"[AI Move] ❌ Błąd: {e}")
        success = False
    
    if success:
        print(f"[AI Pathfinding] ✅ Pełna ścieżka ({len(base_path)-1}): {base_path}")
        print(f"[AI Move] ✅ Przesunięto {unit['id']} na ({target_tuple[0]}, {target_tuple[1]})")
        # Zaktualizuj pozycję w unit dict dla spójności
        unit['q'], unit['r'] = target_tuple
        
        # 🔥 NOWE: Sprawdź czy żeton dotarł na punkt kluczowy i ustaw garnizon
        _check_and_set_keypoint_garrison(unit, target_tuple, game_engine, token)
    else:
        print(f"[AI Move] ❌ Błąd: Nie udało się wykonać ruchu.")
    return success


def _check_and_set_keypoint_garrison(unit: dict, position: Tuple[int,int], game_engine: Any, token: Any) -> None:
    """Sprawdza czy żeton dotarł na punkt kluczowy i ustawia garnizon.
    
    Args:
        unit: Słownik z danymi jednostki
        position: Pozycja (q, r) na którą dotarł żeton
        game_engine: GameEngine
        token: Obiekt tokenu
    """
    try:
        kp_state = getattr(game_engine, 'key_points_state', {})
        if not kp_state:
            return
            
        hex_id = f"{position[0]},{position[1]}"
        kp_data = kp_state.get(hex_id)
        
        if kp_data and kp_data.get('current_value', 0) > 0:
            # Żeton dotarł na aktywny punkt kluczowy - ustaw garnizon
            setattr(token, 'hold_position', True)
            
            # Zainicjalizuj tracker garnizonu jeśli nie istnieje
            if not hasattr(game_engine, 'garrison_tracker'):
                game_engine.garrison_tracker = {}
            
            garrison_tracker = game_engine.garrison_tracker
            if hex_id not in garrison_tracker:
                garrison_tracker[hex_id] = {}
                
            current_turn = getattr(game_engine, 'turn_number', getattr(game_engine, 'current_turn', 1))
            token_id = getattr(token, 'id', 'unknown')
            garrison_tracker[hex_id][token_id] = current_turn
            
            print(f"🏰 [GARRISON SET] {unit.get('id', 'UNKNOWN')} rozpoczyna garnizon na punkcie {hex_id}")
            print(f"    📍 Wartość punktu: {kp_data.get('current_value', 0)}/{kp_data.get('initial_value', 0)}")
            print(f"    🛡️ Status: hold_position = True")
            
    except Exception as e:
        print(f"[GARRISON ERROR] Błąd ustawienia garnizonu: {e}")
