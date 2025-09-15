"""Moduł wsparcia garnizonu - automatyczn        # NAPRAWIONE: używaj SessionManager dla polskich nazw folderów
        from utils.session_manager import get_current_session_dir
        specialized_dir = get_current_session_dir() / "specialized"rzydzielanie jednostek do ochrony punktów kluczowych.
Bazuje na jakości punktu i zagrożeniu wrogami w pobliżu.

NOWE: Długoterminowe wsparcie - jednostki przydzielane na cały czas garnizonu (MAX_GARRISON_TIME=3 tury).
"""
from __future__ import annotations
from typing import List, Dict, Any, Tuple
import csv
import os
from datetime import datetime

try:
    from main_ai import debug_print  # type: ignore
    from ai.log_kategorie_ai import GARRISON, ERROR  # type: ignore
except Exception:  # fallback
    def debug_print(msg, level="BASIC", category="INFO"):
        print(f"[AI_GARRISON_SUPPORT] {msg}")
    GARRISON = "GARRISON"
    ERROR = "ERROR"

# NOWE: Stałe dla długoterminowego wsparcia
MAX_GARRISON_TIME = 3  # Maksymalny czas garnizonu w turach

def get_current_turn(game_engine):
    """Pobiera aktualny numer tury z game_engine."""
    return getattr(game_engine, 'current_turn', 0)

def is_support_expired(unit, current_turn):
    """Sprawdza czy wsparcie garnizonu wygasło."""
    end_turn = unit.get('garrison_support_end_turn', 0)
    return current_turn >= end_turn

def has_priority_task(unit, game_engine):
    """FURTKA: sprawdza czy jednostka ma priorytetowe zadanie."""
    # TODO: Implementacja logiki priorytetowych zadań
    # Na razie false - można rozszerzyć w przyszłości
    return False

def log_garrison_issue_to_csv(issue_type: str, unit_id: str, garrison_hex: str, details: dict):
    """Loguje problemy z wsparciem garnizonu do CSV dla analizy."""
    try:
        # NAPRAWIONE: używaj SessionManager dla polskich nazw folderów
        from utils.session_manager import get_current_session_dir
        specialized_dir = get_current_session_dir() / "specialized"
        specialized_dir.mkdir(parents=True, exist_ok=True)
        
        # Create filename with current date
        today = datetime.now().strftime("%Y%m%d")
        csv_file = f"{specialized_dir}/garrison_problems_{today}.csv"
        
        # Check if file exists to determine if we need headers
        file_exists = os.path.exists(csv_file)
        
        with open(csv_file, 'a', newline='', encoding='utf-8') as f:
            writer = csv.writer(f)
            
            # Write headers if new file
            if not file_exists:
                writer.writerow([
                    'timestamp', 'issue_type', 'unit_id', 'garrison_hex',
                    'unit_mp', 'unit_fuel', 'unit_position', 'distance_to_garrison',
                    'pathfinding_failed', 'target_blocked', 'threat_level',
                    'kp_value', 'available_units', 'details'
                ])
            
            # Write the issue data
            writer.writerow([
                datetime.now().isoformat(),
                issue_type,
                unit_id,
                garrison_hex,
                details.get('mp', 'N/A'),
                details.get('fuel', 'N/A'), 
                details.get('position', 'N/A'),
                details.get('distance', 'N/A'),
                details.get('pathfinding_failed', 'N/A'),
                details.get('target_blocked', 'N/A'),
                details.get('threat_level', 'N/A'),
                details.get('kp_value', 'N/A'),
                details.get('available_units', 'N/A'),
                str(details.get('extra_info', ''))
            ])
            
    except Exception as e:
                debug_print(f"[CSV LOG ERROR] Nie można zapisać do CSV: {e}", "BASIC", ERROR)
def calculate_garrison_support(kp_data: dict, enemies_nearby: List, available_units: int) -> int:
    """Oblicza ile jednostek wsparcia potrzebuje garnizon.
    
    Args:
        kp_data: Dane punktu kluczowego
        enemies_nearby: Lista wrogich jednostek w pobliżu
        available_units: Liczba dostępnych jednostek bez celu
        
    Returns:
        int: Liczba jednostek wsparcia (0-4)
    """
    # Jakość punktu (0-4) - zwiększone progi
    kp_value = kp_data.get('current_value', 0)
    if kp_value >= 80:
        quality_factor = 4      # Mega cenny punkt
    elif kp_value >= 50:
        quality_factor = 3      # Cenny punkt
    elif kp_value >= 20:
        quality_factor = 2      # Średni punkt
    elif kp_value >= 10:
        quality_factor = 1      # Słaby punkt
    else:
        quality_factor = 0      # Bezwartościowy
    
    # Zagrożenie (0-3) - uproszczone
    threat_factor = min(3, len(enemies_nearby))
    
    # Łączny priorytet
    total_priority = quality_factor + threat_factor
    
    # Przelicz na jednostki wsparcia - bardziej agresywne przydzielanie
    if total_priority >= 6:      # Mega punkt + wrogowie
        support_needed = 3
    elif total_priority >= 4:    # Cenny punkt + wrogowie LUB mega punkt bez wrogów  
        support_needed = 2
    elif total_priority >= 2:    # Średni punkt LUB cenny punkt z wrogami
        support_needed = 1
    else:                        # Słabe punkty
        support_needed = 0
    
    # Ogranicz do dostępnych jednostek (max połowa dostępnych)
    max_available = max(0, available_units // 2)
    final_support = min(support_needed, max_available)
    
    debug_print(f"[SUPPORT CALC] KP wartość={kp_value} (quality={quality_factor}), wrogów={len(enemies_nearby)} (threat={threat_factor})", "FULL", GARRISON)
    debug_print(f"[SUPPORT CALC] Priorytet={total_priority} → potrzeba={support_needed}, dostępne={available_units} → finalne={final_support}", "FULL", GARRISON)
    
    return final_support


def find_closest_units(target_unit: dict, candidate_units: List[dict], max_count: int, game_engine) -> List[dict]:
    """Znajdź najbliższe jednostki do celu z diagnostyką problemów ruchu.
    
    Args:
        target_unit: Jednostka do której szukamy najbliższych
        candidate_units: Lista kandydatów
        max_count: Maksymalna liczba jednostek do zwrócenia
        game_engine: GameEngine dla obliczenia dystansu
        
    Returns:
        List[dict]: Lista najbliższych jednostek
    """
    if not candidate_units or max_count <= 0:
        return []
    
    target_pos = (target_unit['q'], target_unit['r'])
    board = getattr(game_engine, 'board', None)
    garrison_hex = f"{target_pos[0]},{target_pos[1]}"
    
    # Oblicz dystanse z diagnostyką
    units_with_distance = []
    units_with_problems = []
    
    for unit in candidate_units:
        unit_pos = (unit['q'], unit['r'])
        unit_token = unit.get('token')
        unit_id = unit.get('id', 'UNKNOWN')
        
        # Sprawdź podstawowe statystyki jednostki
        mp = getattr(unit_token, 'movement_points', 0) if unit_token else 0
        fuel = getattr(unit_token, 'fuel', 0) if unit_token else 0
        
        if board and hasattr(board, 'hex_distance'):
            distance = board.hex_distance(target_pos, unit_pos)
        else:
            # Fallback: Manhattan distance
            distance = abs(target_pos[0] - unit_pos[0]) + abs(target_pos[1] - unit_pos[1])
        
        # Diagnostyka problemów z ruchem
        problem_details = {
            'mp': mp,
            'fuel': fuel,
            'position': f"{unit_pos[0]},{unit_pos[1]}",
            'distance': distance,
            'pathfinding_failed': False,
            'target_blocked': False,
            'extra_info': {}
        }
        
        has_problems = False
        
        # Sprawdź brak punktów ruchu
        if mp <= 0:
            has_problems = True
            problem_details['extra_info']['no_mp'] = True
            log_garrison_issue_to_csv("NO_MOVEMENT_POINTS", unit_id, garrison_hex, problem_details)
            debug_print(f"[GARRISON ISSUE] {unit_id}: Brak punktów ruchu (MP={mp})", "BASIC", GARRISON)
        
        # Sprawdź brak paliwa  
        if fuel <= 0:
            has_problems = True
            problem_details['extra_info']['no_fuel'] = True
            log_garrison_issue_to_csv("NO_FUEL", unit_id, garrison_hex, problem_details)
            debug_print(f"[GARRISON ISSUE] {unit_id}: Brak paliwa (Fuel={fuel})", "BASIC", GARRISON)
        
        # Test pathfindingu (jeśli ma MP i fuel)
        if mp > 0 and fuel > 0:
            try:
                # Spróbuj znaleźć ścieżkę
                if board and hasattr(board, 'find_path'):
                    path = board.find_path(unit_pos, target_pos, mp, fuel)
                    if not path or len(path) <= 1:
                        has_problems = True
                        problem_details['pathfinding_failed'] = True
                        problem_details['extra_info']['pathfinding_error'] = 'no_path_found'
                        log_garrison_issue_to_csv("PATHFINDING_FAILED", unit_id, garrison_hex, problem_details)
                        debug_print(f"[GARRISON ISSUE] {unit_id}: Pathfinding failed - brak ścieżki do {garrison_hex}", "BASIC", GARRISON)
                
                # Sprawdź czy cel jest zablokowany (inną jednostką)
                if hasattr(game_engine, 'tokens'):
                    for token in game_engine.tokens:
                        token_pos = (getattr(token, 'q', 999), getattr(token, 'r', 999))
                        if token_pos == target_pos and token != unit_token:
                            has_problems = True
                            problem_details['target_blocked'] = True
                            problem_details['extra_info']['blocked_by'] = getattr(token, 'id', 'UNKNOWN')
                            log_garrison_issue_to_csv("TARGET_BLOCKED", unit_id, garrison_hex, problem_details)
                            debug_print(f"[GARRISON ISSUE] {unit_id}: Cel {garrison_hex} zablokowany przez {getattr(token, 'id', 'UNKNOWN')}", "BASIC", GARRISON)
                            break
                            
            except Exception as e:
                has_problems = True
                problem_details['pathfinding_failed'] = True
                problem_details['extra_info']['pathfinding_error'] = str(e)
                log_garrison_issue_to_csv("PATHFINDING_ERROR", unit_id, garrison_hex, problem_details)
                debug_print(f"[GARRISON ISSUE] {unit_id}: Błąd pathfindingu: {e}", "BASIC", GARRISON)
        
        # Dodaj do odpowiedniej listy
        if has_problems:
            units_with_problems.append((unit, distance, problem_details))
        else:
            units_with_distance.append((unit, distance))
    
    # Loguj podsumowanie problemów
    if units_with_problems:
        debug_print(f"[GARRISON PROBLEMS] {len(units_with_problems)}/{len(candidate_units)} jednostek ma problemy z ruchem", "BASIC", GARRISON)
        
        # Grupuj problemy według typu
        problem_counts = {}
        for _, _, details in units_with_problems:
            if details['extra_info'].get('no_mp'):
                problem_counts['no_mp'] = problem_counts.get('no_mp', 0) + 1
            if details['extra_info'].get('no_fuel'):
                problem_counts['no_fuel'] = problem_counts.get('no_fuel', 0) + 1
            if details['pathfinding_failed']:
                problem_counts['pathfinding'] = problem_counts.get('pathfinding', 0) + 1
            if details['target_blocked']:
                problem_counts['blocked'] = problem_counts.get('blocked', 0) + 1
        
        debug_print(f"[GARRISON PROBLEMS] Rozkład: {problem_counts}", "BASIC", GARRISON)
    
    # Sortuj po dystansie i zwróć najbliższe (tylko te bez problemów)
    units_with_distance.sort(key=lambda x: x[1])
    closest = [unit for unit, _ in units_with_distance[:max_count]]
    
    debug_print(f"[CLOSEST] Znaleziono {len(closest)}/{max_count} użytecznych jednostek (z {len(candidate_units)} kandydatów)", "FULL", GARRISON)
    
    return closest


def assign_garrison_support(my_units: List[dict], game_engine) -> int:
    """Główna funkcja przydzielania wsparcia garnizonom.
    NOWE: Długoterminowe wsparcie - jednostki przydzielane na cały czas garnizonu.
    
    Args:
        my_units: Lista wszystkich jednostek gracza
        game_engine: GameEngine
        
    Returns:
        int: Liczba przydzielonych jednostek wsparcia
    """
    try:
        current_turn = get_current_turn(game_engine)
        kp_state = getattr(game_engine, 'key_points_state', {})
        if not kp_state:
            return 0
        
        # Znajdź jednostki z garnizonem i bez celu
        garrison_units = []
        idle_units = []
        
        for unit in my_units:
            token = unit.get('token')
            if token and getattr(token, 'hold_position', False):
                # Jednostka ma garnizon
                garrison_units.append(unit)
            elif not unit.get('assigned_target') and not unit.get('support_role'):
                # Jednostka bez celu i bez roli wsparcia
                idle_units.append(unit)
            
        # NOWE: Usuń z dostępnych jednostki z długoterminowym wsparciem
        for unit in idle_units[:]:  # Kopia listy
            # Sprawdź czy jednostka ma długoterminowe wsparcie
            if unit.get('support_type') == 'long_term':
                if not is_support_expired(unit, current_turn):
                    debug_print(f"Jednostka {unit.get('id', 'unknown')} ma aktywne długoterminowe wsparcie do tury {unit.get('garrison_support_end_turn', 0)}", "BASIC", GARRISON)
                    idle_units.remove(unit)  # Usuń z dostępnych
                    continue
        
        if not garrison_units or not idle_units:
            debug_print(f"[GARRISON SUPPORT] Brak garnizonów ({len(garrison_units)}) lub idle jednostek ({len(idle_units)})", "FULL", GARRISON)
            return 0
        
        debug_print(f"[GARRISON SUPPORT] Sprawdzanie wsparcia dla {len(garrison_units)} garnizonów z {len(idle_units)} dostępnych jednostek", "BASIC", GARRISON)
        
        total_assigned = 0
        
        for garrison_unit in garrison_units:
            garrison_pos = (garrison_unit['q'], garrison_unit['r'])
            hex_id = f"{garrison_pos[0]},{garrison_pos[1]}"
            kp_data = kp_state.get(hex_id, {})
            
            if not kp_data or kp_data.get('current_value', 0) <= 0:
                continue  # Punkt wyczerpany lub nie istnieje
            
            # Sprawdź wrogów w pobliżu (zasięg 4 hexów)
            enemies_nearby = []
            try:
                from ai.ai_commander import scan_for_enemies
                enemies_nearby = scan_for_enemies(garrison_pos, game_engine, range=4)
            except Exception:
                # Fallback: sprawdź wszystkie wrogie tokeny
                all_tokens = getattr(game_engine, 'tokens', [])
                board = getattr(game_engine, 'board', None)
                
                # Ustal naszą nację z garnizonu
                garrison_token = garrison_unit.get('token')
                our_nation = None
                if garrison_token and hasattr(garrison_token, 'owner'):
                    our_nation = garrison_token.owner.split('(')[-1].replace(')', '').strip()
                
                for token in all_tokens:
                    if not hasattr(token, 'owner') or not token.owner:
                        continue
                    
                    # Sprawdź czy to wróg (inna nacja)
                    token_nation = token.owner.split('(')[-1].replace(')', '').strip()
                    
                    if our_nation and token_nation != our_nation:
                        token_pos = (getattr(token, 'q', 999), getattr(token, 'r', 999))
                        if board and hasattr(board, 'hex_distance'):
                            dist = board.hex_distance(garrison_pos, token_pos)
                        else:
                            dist = abs(garrison_pos[0] - token_pos[0]) + abs(garrison_pos[1] - token_pos[1])
                        
                        if dist <= 4:
                            enemies_nearby.append((token, dist))
                            debug_print(f"[ENEMY DETECT] Wróg {getattr(token, 'id', 'UNKNOWN')} ({token_nation}) w dystansie {dist} od {hex_id}", "FULL", GARRISON)
            
            # Oblicz potrzebne wsparcie
            support_needed = calculate_garrison_support(kp_data, enemies_nearby, len(idle_units))
            
            # Loguj sytuację garnizonu
            garrison_details = {
                'kp_value': kp_data.get('current_value', 0),
                'threat_level': len(enemies_nearby),
                'available_units': len(idle_units),
                'support_needed': support_needed,
                'extra_info': {
                    'enemies_list': [getattr(e[0], 'id', 'UNKNOWN') if isinstance(e, tuple) else str(e) for e in enemies_nearby[:3]]
                }
            }
            
            if support_needed > 0:
                # Znajdź najbliższe jednostki
                closest_units = find_closest_units(garrison_unit, idle_units, support_needed, game_engine)
                
                # Loguj jeśli nie znaleziono wystarczająco jednostek
                if len(closest_units) < support_needed:
                    shortage_details = garrison_details.copy()
                    shortage_details['extra_info']['units_found'] = len(closest_units)
                    shortage_details['extra_info']['units_needed'] = support_needed
                    shortage_details['extra_info']['shortage'] = support_needed - len(closest_units)
                    
                    log_garrison_issue_to_csv("INSUFFICIENT_SUPPORT", 
                                            garrison_unit.get('id', 'UNKNOWN'), 
                                            hex_id, 
                                            shortage_details)
                    
                    debug_print(f"[GARRISON SHORTAGE] {hex_id}: Potrzeba {support_needed}, znaleziono {len(closest_units)} jednostek", "BASIC", GARRISON)
                
                # Przydziel jednostki do wsparcia
                for support_unit in closest_units:
                    support_unit['assigned_target'] = garrison_pos
                    support_unit['support_role'] = 'garrison_defense'
                    support_unit['support_for'] = garrison_unit.get('id', 'unknown')
                    # NOWE: Długoterminowe wsparcie
                    support_unit['support_type'] = 'long_term'
                    support_unit['garrison_support_start_turn'] = current_turn
                    support_unit['garrison_support_end_turn'] = current_turn + MAX_GARRISON_TIME
                    support_unit['assigned_garrison_id'] = garrison_unit.get('id', 'unknown')
                    
                    idle_units.remove(support_unit)  # Usuń z listy dostępnych
                    total_assigned += 1
                    
                    debug_print(f"[GARRISON SUPPORT] {support_unit.get('id', 'UNKNOWN')} przydzielony do długoterminowej obrony {hex_id} (garnizon: {garrison_unit.get('id', 'UNKNOWN')}, tury: {current_turn}-{current_turn + MAX_GARRISON_TIME})", "BASIC", GARRISON)
                
                debug_print(f"[GARRISON SUPPORT] Punkt {hex_id}: wartość={kp_data.get('current_value', 0)}, wrogów={len(enemies_nearby)} → przydzielono {len(closest_units)}/{support_needed} wsparcia", "BASIC", GARRISON)
        
        if total_assigned > 0:
            debug_print(f"[GARRISON SUPPORT] ✅ Łącznie przydzielono {total_assigned} jednostek wsparcia garnizonów", "BASIC", GARRISON)
        
        return total_assigned
        
    except Exception as e:
        debug_print(f"[GARRISON SUPPORT] ❌ Błąd przydzielania wsparcia: {e}", "BASIC", "ERROR")
        return 0


def clear_obsolete_garrison_support(my_units: List[dict], game_engine) -> int:
    """Usuwa przestarzałe przydzielenia wsparcia (garnizon zwolniony, punkt wyczerpany).
    NOWE: Uwzględnia długoterminowe wsparcie i furtkę priorytetowych zadań.
    
    Args:
        my_units: Lista wszystkich jednostek gracza
        game_engine: GameEngine
        
    Returns:
        int: Liczba zwolnionych jednostek wsparcia
    """
    try:
        current_turn = get_current_turn(game_engine)
        kp_state = getattr(game_engine, 'key_points_state', {})
        cleared_count = 0
        
        for unit in my_units:
            if unit.get('support_role') == 'garrison_defense':
                target_pos = unit.get('assigned_target')
                if not target_pos:
                    continue
                
                hex_id = f"{target_pos[0]},{target_pos[1]}"
                kp_data = kp_state.get(hex_id, {})
                
                # Sprawdź powody zwolnienia wsparcia
                should_clear = False
                reason = ""
                
                # NOWE: Sprawdź czy wsparcie wygasło
                if is_support_expired(unit, current_turn):
                    should_clear = True
                    reason = "koniec okresu wsparcia"
                # NOWE: Sprawdź priorytetowe zadania (FURTKA)
                elif has_priority_task(unit, game_engine):
                    should_clear = True  
                    reason = "priorytetowe zadanie"
                # Istniejąca logika: punkt wyczerpany
                elif not kp_data or kp_data.get('current_value', 0) <= 0:
                    should_clear = True
                    reason = "punkt wyczerpany"
                else:
                    # Sprawdź czy garnizon nadal istnieje
                    garrison_exists = False
                    for other_unit in my_units:
                        other_pos = (other_unit['q'], other_unit['r'])
                        other_token = other_unit.get('token')
                        if (other_pos == target_pos and other_token and 
                            getattr(other_token, 'hold_position', False)):
                            garrison_exists = True
                            break
                    
                    if not garrison_exists:
                        should_clear = True
                        reason = "garnizon zwolniony"
                
                if should_clear:
                    # NOWE: Czyść dodatkowe pola długoterminowego wsparcia
                    unit.pop('assigned_target', None)
                    unit.pop('support_role', None)
                    unit.pop('support_for', None)
                    unit.pop('support_type', None)
                    unit.pop('garrison_support_start_turn', None)
                    unit.pop('garrison_support_end_turn', None)
                    unit.pop('assigned_garrison_id', None)
                    cleared_count += 1
                    
                    debug_print(f"[GARRISON SUPPORT] {unit.get('id', 'UNKNOWN')} zwolniony z długoterminowego wsparcia {hex_id}: {reason}", "BASIC", GARRISON)
        
        if cleared_count > 0:
            debug_print(f"[GARRISON SUPPORT] 🔄 Zwolniono {cleared_count} jednostek z przestarzałego wsparcia", "BASIC", GARRISON)
        
        return cleared_count
        
    except Exception as e:
        debug_print(f"[GARRISON SUPPORT] ❌ Błąd czyszczenia wsparcia: {e}", "BASIC", "ERROR")
        return 0
