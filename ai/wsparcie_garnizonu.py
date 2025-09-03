"""Moduł wsparcia garnizonu - automatyczne przydzielanie jednostek do ochrony punktów kluczowych.
Bazuje na jakości punktu i zagrożeniu wrogami w pobliżu.
"""
from __future__ import annotations
from typing import List, Dict, Any, Tuple

try:
    from main_ai import debug_print  # type: ignore
except Exception:  # fallback
    def debug_print(msg, level="BASIC", category="INFO"):
        print(f"[AI_GARRISON_SUPPORT] {msg}")


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
    
    debug_print(f"[SUPPORT CALC] KP wartość={kp_value} (quality={quality_factor}), wrogów={len(enemies_nearby)} (threat={threat_factor})", "FULL", "GARRISON")
    debug_print(f"[SUPPORT CALC] Priorytet={total_priority} → potrzeba={support_needed}, dostępne={available_units} → finalne={final_support}", "FULL", "GARRISON")
    
    return final_support


def find_closest_units(target_unit: dict, candidate_units: List[dict], max_count: int, game_engine) -> List[dict]:
    """Znajdź najbliższe jednostki do celu.
    
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
    
    # Oblicz dystanse
    units_with_distance = []
    for unit in candidate_units:
        unit_pos = (unit['q'], unit['r'])
        if board and hasattr(board, 'hex_distance'):
            distance = board.hex_distance(target_pos, unit_pos)
        else:
            # Fallback: Manhattan distance
            distance = abs(target_pos[0] - unit_pos[0]) + abs(target_pos[1] - unit_pos[1])
        
        units_with_distance.append((unit, distance))
    
    # Sortuj po dystansie i zwróć najbliższe
    units_with_distance.sort(key=lambda x: x[1])
    closest = [unit for unit, _ in units_with_distance[:max_count]]
    
    debug_print(f"[CLOSEST] Znaleziono {len(closest)}/{max_count} najbliższych jednostek do {target_unit.get('id', 'UNKNOWN')}", "FULL", "GARRISON")
    
    return closest


def assign_garrison_support(my_units: List[dict], game_engine) -> int:
    """Główna funkcja przydzielania wsparcia garnizonom.
    
    Args:
        my_units: Lista wszystkich jednostek gracza
        game_engine: GameEngine
        
    Returns:
        int: Liczba przydzielonych jednostek wsparcia
    """
    try:
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
        
        if not garrison_units or not idle_units:
            debug_print(f"[GARRISON SUPPORT] Brak garnizonów ({len(garrison_units)}) lub idle jednostek ({len(idle_units)})", "FULL", "GARRISON")
            return 0
        
        debug_print(f"[GARRISON SUPPORT] Sprawdzanie wsparcia dla {len(garrison_units)} garnizonów z {len(idle_units)} dostępnych jednostek", "BASIC", "GARRISON")
        
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
                            debug_print(f"[ENEMY DETECT] Wróg {getattr(token, 'id', 'UNKNOWN')} ({token_nation}) w dystansie {dist} od {hex_id}", "FULL", "GARRISON")
            
            # Oblicz potrzebne wsparcie
            support_needed = calculate_garrison_support(kp_data, enemies_nearby, len(idle_units))
            
            if support_needed > 0:
                # Znajdź najbliższe jednostki
                closest_units = find_closest_units(garrison_unit, idle_units, support_needed, game_engine)
                
                # Przydziel jednostki do wsparcia
                for support_unit in closest_units:
                    support_unit['assigned_target'] = garrison_pos
                    support_unit['support_role'] = 'garrison_defense'
                    support_unit['support_for'] = garrison_unit.get('id', 'unknown')
                    idle_units.remove(support_unit)  # Usuń z listy dostępnych
                    total_assigned += 1
                    
                    debug_print(f"[GARRISON SUPPORT] {support_unit.get('id', 'UNKNOWN')} przydzielony do obrony {hex_id} (garnizon: {garrison_unit.get('id', 'UNKNOWN')})", "BASIC", "GARRISON")
                
                debug_print(f"[GARRISON SUPPORT] Punkt {hex_id}: wartość={kp_data.get('current_value', 0)}, wrogów={len(enemies_nearby)} → przydzielono {len(closest_units)}/{support_needed} wsparcia", "BASIC", "GARRISON")
        
        if total_assigned > 0:
            debug_print(f"[GARRISON SUPPORT] ✅ Łącznie przydzielono {total_assigned} jednostek wsparcia garnizonów", "BASIC", "GARRISON")
        
        return total_assigned
        
    except Exception as e:
        debug_print(f"[GARRISON SUPPORT] ❌ Błąd przydzielania wsparcia: {e}", "BASIC", "ERROR")
        return 0


def clear_obsolete_garrison_support(my_units: List[dict], game_engine) -> int:
    """Usuwa przestarzałe przydzielenia wsparcia (garnizon zwolniony, punkt wyczerpany).
    
    Args:
        my_units: Lista wszystkich jednostek gracza
        game_engine: GameEngine
        
    Returns:
        int: Liczba zwolnionych jednostek wsparcia
    """
    try:
        kp_state = getattr(game_engine, 'key_points_state', {})
        cleared_count = 0
        
        for unit in my_units:
            if unit.get('support_role') == 'garrison_defense':
                target_pos = unit.get('assigned_target')
                if not target_pos:
                    continue
                
                hex_id = f"{target_pos[0]},{target_pos[1]}"
                kp_data = kp_state.get(hex_id, {})
                
                # Sprawdź czy punkt nadal istnieje i ma wartość
                should_clear = False
                reason = ""
                
                if not kp_data or kp_data.get('current_value', 0) <= 0:
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
                    unit.pop('assigned_target', None)
                    unit.pop('support_role', None)
                    unit.pop('support_for', None)
                    cleared_count += 1
                    
                    debug_print(f"[GARRISON SUPPORT] {unit.get('id', 'UNKNOWN')} zwolniony z wsparcia {hex_id}: {reason}", "BASIC", "GARRISON")
        
        if cleared_count > 0:
            debug_print(f"[GARRISON SUPPORT] 🔄 Zwolniono {cleared_count} jednostek z przestarzałego wsparcia", "BASIC", "GARRISON")
        
        return cleared_count
        
    except Exception as e:
        debug_print(f"[GARRISON SUPPORT] ❌ Błąd czyszczenia wsparcia: {e}", "BASIC", "ERROR")
        return 0
