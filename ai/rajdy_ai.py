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


def optimize_fuel_for_raids(unit: Dict[str, Any], game_engine, commander_ref) -> bool:
    """Dotankuj jednostkę do MP+1 przed rajdem jeśli opłacalne i możliwe.
    
    Args:
        unit: Słownik z danymi jednostki
        game_engine: GameEngine
        commander_ref: Referencja do AI Commandera
    
    Returns:
        bool: True jeśli udało się dotankować lub nie było potrzeby, False jeśli nie udało się
    """
    try:
        current_fuel = unit.get('fuel', 0)
        target_fuel = unit.get('mp', 0) + 1  # MP + 1 dla bufora bezpieczeństwa
        fuel_needed = max(0, target_fuel - current_fuel)
        
        if fuel_needed <= 0:
            # Już ma wystarczająco paliwa
            return True
            
        # Sprawdź czy stać na dotankowanie (szybka heurystyka)
        if not can_afford_fuel(game_engine, fuel_needed):
            debug_print(f"[RAID FUEL] {unit.get('id', 'UNKNOWN')}: Nie stać na {fuel_needed} paliwa", "FULL", "INFO")
            return False
            
        # Próba dotankowania
        if commander_ref and hasattr(commander_ref, 'tactical_resupply'):
            if commander_ref.tactical_resupply(game_engine, "PRE_RAID_OPTIMIZATION"):
                # Aktualizuj fuel w unit dict na podstawie tokena
                token = unit.get('token')
                if token:
                    unit['fuel'] = getattr(token, 'currentFuel', current_fuel)
                    debug_print(f"[RAID FUEL] ✅ {unit.get('id', 'UNKNOWN')}: {current_fuel}→{unit['fuel']} paliwa", "FULL", "INFO")
                    return True
        
        debug_print(f"[RAID FUEL] ❌ {unit.get('id', 'UNKNOWN')}: Nie udało się dotankować", "FULL", "INFO")
        return False
        
    except Exception as e:
        debug_print(f"[RAID FUEL] Błąd optymalizacji paliwa: {e}", "BASIC", "ERROR")
        return False


def can_afford_fuel(game_engine, fuel_needed: int) -> bool:
    """Sprawdź czy AI stać na dotankowanie (szybka heurystyka)."""
    try:
        current_player = getattr(game_engine, 'current_player_obj', None)
        if not current_player:
            return False
            
        # Sprawdź punkty ekonomiczne
        punkty = 0
        if hasattr(current_player, 'economy') and current_player.economy is not None:
            punkty = getattr(current_player.economy, 'economic_points', 0)
        if punkty <= 0:
            punkty = getattr(current_player, 'punkty_ekonomiczne', 0)
            
        # Heurystyka: potrzeba co najmniej 2x więcej punktów niż fuel (zabezpieczenie)
        min_required = fuel_needed * 2
        return punkty >= min_required
        
    except Exception:
        return False


def evaluate_movement_mode_for_raid(unit, target_pos, game_engine):
    """Ocenia optymalny tryb ruchu dla rajdu przed jego wykonaniem"""
    try:
        from ai.ruch_jednostek import choose_movement_mode
        
        # Sprawdź aktualny tryb
        current_mode = None
        token = unit.get('token')
        if token and hasattr(token, 'movement_mode'):
            current_mode = token.movement_mode
        
        # Wybierz optymalny tryb dla tego celu
        optimal_mode = choose_movement_mode(unit, target_pos, game_engine)
        
        # Symuluj zmianę MP dla różnych trybów
        base_mp = unit.get('base_mp', unit.get('mp', 0))
        
        # Przybliżone MP dla różnych trybów (na podstawie typowych wartości)
        mode_mp_multipliers = {
            'march': 1.5,     # szybki marsz
            'combat': 1.0,    # podstawowy tryb
            'recon': 0.8      # ostrożny rekonesans
        }
        
        optimal_mp = int(base_mp * mode_mp_multipliers.get(optimal_mode, 1.0))
        current_mp = unit.get('mp', 0)
        
        debug_print(f"[RAID MODE] {unit.get('id', 'UNKNOWN')}: Aktualny={current_mode}({current_mp}MP), Optymalny={optimal_mode}({optimal_mp}MP)", "FULL", "INFO")
        
        return optimal_mode, optimal_mp
        
    except Exception as e:
        debug_print(f"[RAID MODE] Błąd oceny trybu: {e}", "BASIC", "ERROR")
        return None, unit.get('mp', 0)


def opportunistic_capture_phase(game_engine, my_units: List[Dict[str, Any]], player_id):
    """Szybka próba zajęcia wolnych keypointów osiągalnych w tej turze LUB w planach wieloturowych.
    Kryterium solo-rajdu: (value / distance) >= FREE_KEYPOINT_VALUE_DISTANCE_FACTOR
    NOWE: Obsługuje cele osiągalne w 2-3 turach z uzupełnianiem paliwa.
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
                
            # PRIORYTET 1: Sprawdź czy jednostka ma już assigned_target z poprzedniej tury (plan wieloturowy)
            assigned_target = unit.get('assigned_target')
            if assigned_target:
                # Sprawdź czy cel nadal istnieje i jest wolny
                target_q, target_r = assigned_target
                target_key = f"{target_q},{target_r}"
                target_kp = kp_state.get(target_key)
                
                if target_kp and target_kp.get('current_value', 0) > 0:
                    # Cel nadal jest dostępny - sprawdź czy można go osiągnąć w tej turze
                    pos = (unit['q'], unit['r'])
                    try:
                        dist = board.hex_distance(pos, assigned_target) if board else 999
                        
                        # Sprawdź czy można osiągnąć z obecnym paliwem/MP
                        optimal_mode, optimal_mp = evaluate_movement_mode_for_raid(unit, assigned_target, game_engine)
                        optimal_range = min(optimal_mp, unit['fuel'])
                        
                        if dist <= optimal_range:
                            # Można osiągnąć cel - wykonaj rajd!
                            debug_print(f"[MULTI-TURN RAID] {unit.get('id', 'UNKNOWN')}: Kontynuuję plan wieloturowy do {assigned_target}", "BASIC", "INFO")
                            
                            # Ustaw optymalny tryb ruchu
                            token = unit.get('token')
                            if token and optimal_mode and hasattr(token, 'movement_mode'):
                                if token.movement_mode != optimal_mode:
                                    token.movement_mode = optimal_mode
                                    if hasattr(token, 'apply_movement_mode'):
                                        token.apply_movement_mode()
                                    unit['mp'] = getattr(token, 'currentMovePoints', optimal_mp)
                                    debug_print(f"[MULTI-TURN] ✅ {unit.get('id', 'UNKNOWN')}: Tryb {optimal_mode}, MP: {unit['mp']}", "BASIC", "INFO")
                            
                            try:
                                from ai.ruch_jednostek import move_towards
                                if move_towards(unit, assigned_target, game_engine):
                                    unit['moved_capture'] = True
                                    # ✅ POPRAWKA: Zamiast usuwać assigned_target, ustaw garrison_kp dla ciągłości
                                    unit['garrison_kp'] = assigned_target
                                    unit['garrison_established_turn'] = getattr(game_engine, 'turn_number', getattr(game_engine, 'current_turn', 1))
                                    unit.pop('assigned_target', None)  # Cel osiągnięty, usuń plan
                                    captured.append(target_key)
                                    debug_print(f"[MULTI-TURN SUCCESS] ✅ Zrealizowano plan wieloturowy: {target_key}, garnizon ustanowiony", "BASIC", "INFO")
                                    continue  # Przejdź do następnej jednostki
                            except Exception as e:
                                debug_print(f"[MULTI-TURN ERROR] Błąd ruchu: {e}", "BASIC", "ERROR")
                        else:
                            # Nadal za daleko - spróbuj uzupełnić paliwo i przybliż się
                            debug_print(f"[MULTI-TURN] {unit.get('id', 'UNKNOWN')}: Kontynuuję drogę do {assigned_target} (dystans {dist} > zasięg {optimal_range})", "FULL", "INFO")
                            
                            # Najpierw spróbuj uzupełnić paliwo
                            current_player = getattr(game_engine, 'current_player_obj', None)
                            commander_ref = getattr(game_engine, 'current_player_commander', None)
                            if commander_ref and hasattr(commander_ref, 'tactical_resupply'):
                                if commander_ref.tactical_resupply(game_engine, "MULTI_TURN_RAID", unit.get('id')):
                                    token = unit.get('token')
                                    if token:
                                        unit['fuel'] = getattr(token, 'currentFuel', unit['fuel'])
                                        optimal_range = min(optimal_mp, unit['fuel'])
                            
                            # Teraz spróbuj się przybliżyć do celu
                            try:
                                from ai.ruch_jednostek import move_towards
                                if move_towards(unit, assigned_target, game_engine):
                                    unit['moved_capture'] = True
                                    debug_print(f"[MULTI-TURN PROGRESS] {unit.get('id', 'UNKNOWN')}: Przybliżam się do celu {assigned_target}", "FULL", "INFO")
                                    continue  # Przejdź do następnej jednostki - zachowaj assigned_target
                            except Exception as e:
                                debug_print(f"[MULTI-TURN PROGRESS ERROR] Błąd ruchu: {e}", "BASIC", "ERROR")
                    except Exception as e:
                        debug_print(f"[MULTI-TURN] Błąd obliczania dystansu: {e}", "BASIC", "ERROR")
                else:
                    # Cel już niedostępny - wyczyść assigned_target
                    unit.pop('assigned_target', None)
                    debug_print(f"[MULTI-TURN] {unit.get('id', 'UNKNOWN')}: Cel {assigned_target} już niedostępny, czyszczę plan", "FULL", "INFO")
            
            # PRIORYTET 2: Jeśli nie ma planu wieloturowego, szukaj nowych celów (logika jednoorazowa + wieloturowa)
            if unit.get('moved_capture'):
                continue  # Jednostka już wykonała ruch w ramach planu wieloturowego
                
            # NOWA LOGIKA: Optymalizacja paliwa przed rajdem
            current_player = getattr(game_engine, 'current_player_obj', None)
            commander_ref = getattr(game_engine, 'current_player_commander', None)
            
            # Zawsze próbuj zoptymalizować paliwo do MP+1
            if commander_ref:
                optimize_fuel_for_raids(unit, game_engine, commander_ref)
            
            # Jeśli nadal brak paliwa, spróbuj podstawowego uzupełnienia
            if unit.get('fuel', 0) <= 0:
                if current_player and hasattr(current_player, 'is_ai_commander'):
                    if commander_ref and hasattr(commander_ref, 'tactical_resupply'):
                        try:
                            if commander_ref.tactical_resupply(game_engine, "LOW_FUEL", unit.get('id')):
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
            current_range = min(unit['mp'], unit['fuel'])
            debug_print(f"[RAID RANGE] {unit.get('id', 'UNKNOWN')}: MP={unit.get('mp', 0)}, Fuel={unit.get('fuel', 0)}, Zasięg={current_range}", "FULL", "INFO")
            
            best_target = None
            best_score = 0.0
            best_optimal_mode = None
            best_optimal_mp = current_range
            best_is_multiturn = False  # Czy to plan wieloturowy
            
            # Przeszukaj cele i dla każdego oceń optymalny tryb ruchu + możliwość wieloturową
            for hex_id, q, r, kp in free_kps:
                try:
                    dist = board.hex_distance(pos, (q, r)) if board else 999
                except Exception:
                    continue
                if dist <= 0:
                    continue
                    
                # Oceń optymalny tryb ruchu dla tego celu
                optimal_mode, optimal_mp = evaluate_movement_mode_for_raid(unit, (q, r), game_engine)
                optimal_range = min(optimal_mp, unit['fuel'])  # Paliwo nie zmienia się, tylko MP
                
                # LOGIKA JEDNOTUROWA (jak wcześniej)
                if dist <= optimal_range:
                    value = kp.get('current_value', 0)
                    if value <= 0:
                        continue
                        
                    score = value / dist
                    if score >= FREE_KEYPOINT_VALUE_DISTANCE_FACTOR and score > best_score:
                        best_score = score
                        best_target = (hex_id, q, r)
                        best_optimal_mode = optimal_mode
                        best_optimal_mp = optimal_mp
                        best_is_multiturn = False
                        debug_print(f"[RAID MODE] {unit.get('id', 'UNKNOWN')}: Nowy najlepszy cel jednoturowy {hex_id} (score {score:.2f}) z trybem {optimal_mode}", "FULL", "INFO")
                
                # NOWA LOGIKA WIELOTUROWA: Sprawdź cele osiągalne w 2-3 turach z uzupełnianiem paliwa
                elif not best_target or best_is_multiturn:  # Tylko jeśli nie ma lepszego celu jednoturowego
                    # Symuluj uzupełnienie paliwa do MP+3 (realistyczne założenie)
                    max_fuel_after_resupply = min(unit.get('base_mp', 6) + 4, 20)  # Max paliwo po uzupełnieniu
                    multiturn_range = min(optimal_mp, max_fuel_after_resupply)
                    
                    # KLUCZOWE: Sprawdź pathfinding z POTENCJALNYMI zasobami, nie obecnymi
                    try:
                        from engine.board import Board
                        board = getattr(game_engine, 'board', None)
                        if board and hasattr(board, 'find_path'):
                            # Test z zwiększonymi zasobami - czy w ogóle da się dotrzeć?
                            potential_path = board.find_path(pos, (q, r), max_mp=optimal_mp, max_fuel=max_fuel_after_resupply)
                            
                            if potential_path and len(potential_path) > 1:
                                # Ścieżka istnieje! Oszacuj ile tur potrzeba
                                path_length = len(potential_path) - 1
                                turns_needed = max(1, (path_length - 1) // (multiturn_range // 2) + 1)
                                
                                if turns_needed <= 3:  # Maksymalnie 3 tury
                                    value = kp.get('current_value', 0)
                                    if value <= 0:
                                        continue
                                        
                                    # Obniżony score dla celów wieloturowych (penalty za czas)
                                    multiturn_penalty = 0.8 ** (turns_needed - 1)  # 0.8 za każdą dodatkową turę
                                    score = (value / dist) * multiturn_penalty
                                    
                                    # Niższy próg dla celów wieloturowych
                                    if score >= (FREE_KEYPOINT_VALUE_DISTANCE_FACTOR * 0.6) and (not best_target or (best_is_multiturn and score > best_score)):
                                        best_score = score
                                        best_target = (hex_id, q, r)
                                        best_optimal_mode = optimal_mode
                                        best_optimal_mp = optimal_mp
                                        best_is_multiturn = True
                                        debug_print(f"[MULTI-TURN PLAN] {unit.get('id', 'UNKNOWN')}: Nowy cel wieloturowy {hex_id} (score {score:.2f}, {turns_needed} tury, path_len={path_length}) z trybem {optimal_mode}", "FULL", "INFO")
                                else:
                                    debug_print(f"[MULTI-TURN SKIP] {unit.get('id', 'UNKNOWN')}: Cel {hex_id} wymaga {turns_needed} tur (za długo)", "FULL", "INFO")
                            else:
                                debug_print(f"[MULTI-TURN PATH] {unit.get('id', 'UNKNOWN')}: Brak ścieżki do {hex_id} nawet z pełnymi zasobami", "FULL", "INFO")
                    except Exception as e:
                        debug_print(f"[MULTI-TURN ERROR] Błąd testowania ścieżki: {e}", "FULL", "ERROR")
                        # Fallback do starej logiki
                        if dist <= multiturn_range * 1.5:  # Możliwy w 2-3 turach
                            value = kp.get('current_value', 0)
                            if value <= 0:
                                continue
                                
                            # Obniżony score dla celów wieloturowych (penalty za czas)
                            turns_needed = max(1, (dist - 1) // (multiturn_range // 2) + 1)
                            multiturn_penalty = 0.7 ** (turns_needed - 1)  # 0.7 za każdą dodatkową turę
                            score = (value / dist) * multiturn_penalty
                            
                            # Niższy próg dla celów wieloturowych
                            if score >= (FREE_KEYPOINT_VALUE_DISTANCE_FACTOR * 0.8) and (not best_target or (best_is_multiturn and score > best_score)):
                                best_score = score
                                best_target = (hex_id, q, r)
                                best_optimal_mode = optimal_mode
                                best_optimal_mp = optimal_mp
                                best_is_multiturn = True
                                debug_print(f"[MULTI-TURN PLAN] {unit.get('id', 'UNKNOWN')}: Nowy cel wieloturowy {hex_id} (score {score:.2f}, {turns_needed} tury, fallback) z trybem {optimal_mode}", "FULL", "INFO")
                else:
                    debug_print(f"[RAID MODE] {unit.get('id', 'UNKNOWN')}: Cel {hex_id} za daleko - dystans {dist} > zasięg {optimal_range} ({optimal_mode})", "FULL", "INFO")
                    
            if best_target:
                hex_id, tq, tr = best_target
                
                if best_is_multiturn:
                    # PLAN WIELOTUROWY: Zapisz cel jako assigned_target i rozpocznij realizację
                    unit['assigned_target'] = (tq, tr)
                    debug_print(f"[MULTI-TURN START] {unit.get('id', 'UNKNOWN')}: Rozpoczynam plan wieloturowy do {best_target} (score {best_score:.2f})", "BASIC", "INFO")
                    
                    # Najpierw spróbuj uzupełnić paliwo
                    if commander_ref and hasattr(commander_ref, 'tactical_resupply'):
                        if commander_ref.tactical_resupply(game_engine, "MULTI_TURN_START", unit.get('id')):
                            token = unit.get('token')
                            if token:
                                unit['fuel'] = getattr(token, 'currentFuel', unit['fuel'])
                    
                    # Ustaw optymalny tryb ruchu
                    token = unit.get('token')
                    if token and best_optimal_mode and hasattr(token, 'movement_mode'):
                        if token.movement_mode != best_optimal_mode:
                            token.movement_mode = best_optimal_mode
                            if hasattr(token, 'apply_movement_mode'):
                                token.apply_movement_mode()
                            unit['mp'] = getattr(token, 'currentMovePoints', best_optimal_mp)
                            debug_print(f"[MULTI-TURN] ✅ {unit.get('id', 'UNKNOWN')}: Tryb {best_optimal_mode}, MP: {unit['mp']}", "BASIC", "INFO")
                    
                    # Rozpocznij ruch w kierunku celu (pierwszy etap)
                    try:
                        from ai.ruch_jednostek import move_towards
                        if move_towards(unit, (tq, tr), game_engine):
                            unit['moved_capture'] = True
                            debug_print(f"[MULTI-TURN PROGRESS] {unit.get('id', 'UNKNOWN')}: Pierwszy etap ruchu do {best_target}", "BASIC", "INFO")
                    except Exception as e:
                        debug_print(f"[MULTI-TURN START ERROR] Błąd pierwszego ruchu: {e}", "BASIC", "ERROR")
                
                else:
                    # RAJD JEDNOTUROWY: Wykonaj natychmiast (logika jak wcześniej)
                    debug_print(f"[RAID SUCCESS] {unit.get('id', 'UNKNOWN')}: Rajd do {best_target} (score {best_score:.2f}) z trybem {best_optimal_mode}", "BASIC", "INFO")
                    
                    # Ustaw optymalny tryb ruchu PRZED ruchem
                    token = unit.get('token')
                    if token and best_optimal_mode and hasattr(token, 'movement_mode'):
                        if token.movement_mode != best_optimal_mode:
                            token.movement_mode = best_optimal_mode
                            if hasattr(token, 'apply_movement_mode'):
                                token.apply_movement_mode()
                            # Aktualizuj MP w unit dict
                            unit['mp'] = getattr(token, 'currentMovePoints', best_optimal_mp)
                            debug_print(f"[RAID MODE] ✅ {unit.get('id', 'UNKNOWN')}: Zmiana trybu na {best_optimal_mode}, MP: {unit['mp']}", "BASIC", "INFO")
                    
                    try:
                        from ai.ruch_jednostek import move_towards  # local import to avoid cycles
                        if move_towards(unit, (tq, tr), game_engine):
                            unit['moved_capture'] = True
                            # ✅ POPRAWKA: Ustaw garrison_kp dla explicit garnizonu po pojedynczym rajdzie
                            unit['garrison_kp'] = (tq, tr)
                            unit['garrison_established_turn'] = getattr(game_engine, 'turn_number', getattr(game_engine, 'current_turn', 1))
                            captured.append(hex_id)
                            debug_print(f"[RAID SUCCESS] ✅ {unit.get('id', 'UNKNOWN')}: Rajd do {hex_id} sukces, garnizon ustanowiony", "BASIC", "INFO")
                    except Exception as e:
                        debug_print(f"[RAID] Move error {e}", "BASIC", "ERROR")
            else:
                debug_print(f"[RAID NO TARGET] {unit.get('id', 'UNKNOWN')}: Brak odpowiednich celów w zasięgu (sprawdzono wszystkie tryby ruchu)", "FULL", "INFO")
    except Exception as e:
        debug_print(f"[RAID] Błąd fazy opportunistycznej: {e}", "BASIC", "ERROR")
    return captured
