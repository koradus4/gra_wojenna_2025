"""AI Commander - PROSTA IMPLEMENTACJA (Sonnet 3.5 Safe)

ZASADY:
- NIE używaj klas - tylko funkcje
- ZAWSZE sprawdzaj atrybuty z getattr()
- LIMIT wszystkiego - max 100 iteracji
- BEZ rekurencji - tylko proste pętle
- KAŻDA funkcja max 25 linii
"""

from __future__ import annotations
from typing import Any
import csv
import datetime
import json
import os
from pathlib import Path


def log_commander_action(unit_id, action_type, from_pos, to_pos, reason, player_nation="Unknown"):
    """Loguj akcję AI Commander do CSV w dedykowanym folderze"""
    try:
        # Utwórz katalog logs/ai_commander/ jeśli nie istnieje
        log_dir = "logs/ai_commander"
        if not os.path.exists(log_dir):
            os.makedirs(log_dir)
        
        # Nazwa pliku z datą w folderze ai_commander
        today = datetime.date.today()
        log_file = f"{log_dir}/actions_{today:%Y%m%d}.csv"
        
        # Sprawdź czy plik istnieje, jeśli nie - dodaj nagłówek
        file_exists = os.path.exists(log_file)
        
        with open(log_file, 'a', newline='', encoding='utf-8') as f:
            writer = csv.writer(f)
            
            # Dodaj nagłówek jeśli nowy plik
            if not file_exists:
                writer.writerow([
                    'timestamp', 'nation', 'unit_id', 'action_type', 
                    'from_q', 'from_r', 'to_q', 'to_r', 'reason'
                ])
            
            # Dodaj wpis
            timestamp = datetime.datetime.now().isoformat()
            from_q, from_r = from_pos if from_pos else (None, None)
            to_q, to_r = to_pos if to_pos else (None, None)
            
            writer.writerow([
                timestamp, player_nation, unit_id, action_type,
                from_q, from_r, to_q, to_r, reason
            ])
            
    except Exception as e:
        print(f"[AI] Błąd logowania: {e}")


def get_my_units(game_engine, player_id=None):
    """Zwróć listę moich jednostek z potrzebnymi danymi
    
    Args:
        game_engine: GameEngine
        player_id: ID gracza (2, 3, 5, 6) lub None (auto-detect)
    """
    units = []
    
    # Bezpieczne pobieranie tokenów
    all_tokens = getattr(game_engine, 'tokens', [])
    
    # Określ ID gracza
    if player_id is None:
        current_player = getattr(game_engine, 'current_player_obj', None)
        if current_player:
            player_id = getattr(current_player, 'id', None)
    
    if not player_id:
        return units
    
    for token in all_tokens[:200]:  # MAX 200 tokenów
        # Sprawdź owner - może być "2 (Polska)" lub "2"
        owner = str(getattr(token, 'owner', ''))
        if str(player_id) in owner or owner.startswith(str(player_id)):
            mp = getattr(token, 'currentMovePoints', 0)
            fuel = getattr(token, 'currentFuel', 0)
            
            units.append({
                'id': getattr(token, 'id', None),
                'q': getattr(token, 'q', 0),
                'r': getattr(token, 'r', 0),
                'mp': mp,
                'fuel': fuel,
                'cv': getattr(token, 'combat_value', 0),
                'token': token  # Referencja do obiektu
            })
    
    return units


def ai_attempt_combat(unit, game_engine, player_id, player_nation="Unknown"):
    """Sprawdź czy jednostka może zaatakować wroga i wykonaj atak"""
    try:
        # Znajdź wrogów w zasięgu
        enemies = find_enemies_in_range(unit, game_engine, player_id)
        if not enemies:
            return False
        
        # Wybierz najlepszy cel (najwyższy combat ratio)
        best_enemy = None
        best_ratio = 0
        
        for enemy in enemies:
            ratio = evaluate_combat_ratio(unit, enemy)
            if ratio > best_ratio and ratio >= 1.3:  # Minimalne ratio dla ataku
                best_ratio = ratio
                best_enemy = enemy
        
        if best_enemy:
            print(f"🎯 [COMBAT] {unit.get('id')} atakuje {best_enemy.get('id')} (ratio: {best_ratio:.2f})")
            return execute_ai_combat(unit, best_enemy, game_engine, player_nation)
        
        return False
    except Exception as e:
        print(f"❌ [COMBAT] Błąd podczas sprawdzania ataku: {e}")
        return False


def find_enemies_in_range(unit, game_engine, player_id):
    """Znajdź wszystkich wrogów w zasięgu ataku jednostki"""
    try:
        enemies = []
        my_owner = f"{player_id} ({get_player_nation(game_engine, player_id)})"
        
        # Pobierz zasięg ataku
        unit_token = unit.get('token')
        if not unit_token:
            return enemies
            
        attack_range = unit_token.stats.get('attack', {}).get('range', 1)
        unit_pos = (unit['q'], unit['r'])
        
        # Sprawdź wszystkie żetony
        all_tokens = getattr(game_engine, 'tokens', [])
        for token in all_tokens:
            # Pomiń własne żetony
            if getattr(token, 'owner', '') == my_owner:
                continue
            
            # Sprawdź dystans
            enemy_pos = (getattr(token, 'q', 0), getattr(token, 'r', 0))
            board = getattr(game_engine, 'board', None)
            if board:
                distance = board.hex_distance(unit_pos, enemy_pos)
                if distance <= attack_range:
                    enemies.append({
                        'token': token,
                        'id': getattr(token, 'id', 'unknown'),
                        'q': enemy_pos[0],
                        'r': enemy_pos[1],
                        'cv': getattr(token, 'combat_value', 0),
                        'distance': distance
                    })
        
        return enemies
    except Exception as e:
        print(f"❌ [COMBAT] Błąd wyszukiwania wrogów: {e}")
        return []


def evaluate_combat_ratio(unit, enemy):
    """Oblicz stosunek sił ataku vs obrony"""
    try:
        unit_token = unit.get('token')
        enemy_token = enemy.get('token')
        
        if not unit_token or not enemy_token:
            return 0
        
        # Siła ataku
        attack_value = unit_token.stats.get('attack', {}).get('value', 0)
        
        # Siła obrony wroga (defense + terrain)
        defense_value = enemy_token.stats.get('defense_value', 0)
        
        # Modyfikator terenu (uproszczony)
        board = getattr(unit_token, 'board', None)
        terrain_mod = 0
        if hasattr(board, 'get_tile'):
            tile = board.get_tile(enemy['q'], enemy['r'])
            terrain_mod = getattr(tile, 'defense_mod', 0) if tile else 0
        
        total_defense = defense_value + terrain_mod
        
        # Ratio: atak / obrona
        if total_defense <= 0:
            return 999  # Wróg bez obrony
        
        ratio = attack_value / total_defense
        return ratio
        
    except Exception as e:
        print(f"❌ [COMBAT] Błąd obliczania ratio: {e}")
        return 0


def execute_ai_combat(unit, enemy, game_engine, player_nation="Unknown"):
    """Wykonaj atak używając CombatAction"""
    try:
        unit_token = unit.get('token')
        enemy_token = enemy.get('token')
        
        if not unit_token or not enemy_token:
            return False
        
        # Import CombatAction
        from engine.action_refactored_clean import CombatAction
        
        # Wykonaj atak
        action = CombatAction(unit_token.id, enemy_token.id)
        result = game_engine.execute_action(action)
        
        if result.success:
            print(f"⚔️ [COMBAT] Sukces: {result.message}")
            
            # Loguj atak
            log_commander_action(
                unit_id=unit.get('id', 'unknown'),
                action_type="combat",
                from_pos=(unit['q'], unit['r']),
                to_pos=(enemy['q'], enemy['r']),
                reason=f"Attack enemy {enemy.get('id', 'unknown')}",
                player_nation=player_nation
            )
            return True
        else:
            print(f"❌ [COMBAT] Błąd: {result.message}")
            return False
            
    except Exception as e:
        print(f"❌ [COMBAT] Błąd wykonania ataku: {e}")
        return False


def get_player_nation(game_engine, player_id):
    """Pobierz nazwę narodu gracza"""
    try:
        current_player = getattr(game_engine, 'current_player_obj', None)
        if current_player and getattr(current_player, 'id', None) == player_id:
            return getattr(current_player, 'nation', 'Unknown')
        return 'Unknown'
    except:
        return 'Unknown'


def can_move(unit):
    """Sprawdź czy jednostka może się ruszyć"""
    mp = unit.get('mp', 0)
    fuel = unit.get('fuel', 0)
    return mp > 0 and fuel > 0


def find_target(unit, game_engine):
    """Znajdź najbliższy osiągalny cel (key point lub centrum mapy)"""
    
    # Pobierz key points
    key_points = getattr(game_engine, 'key_points_state', {})
    board = getattr(game_engine, 'board', None)
    
    if not board:
        return None
    
    unit_pos = (unit['q'], unit['r'])
    best_target = None
    best_distance = 999
    
    # Sprawdź key points (max 20)
    kp_count = 0
    for hex_id, kp_data in key_points.items():
        if kp_count >= 20:
            break
        kp_count += 1
        
        # Parsuj hex_id do współrzędnych
        try:
            parts = hex_id.split('_')
            if len(parts) >= 2:
                kp_q = int(parts[0])
                kp_r = int(parts[1])
                kp_pos = (kp_q, kp_r)
                
                # POPRAWKA: Sprawdź rzeczywisty pathfinding z limitami MP
                path = board.find_path(
                    unit_pos, kp_pos,
                    max_mp=unit['mp'],
                    max_fuel=unit['fuel']
                )
                
                if path and len(path) > 1:  # Cel osiągalny w ramach MP/Fuel
                    actual_distance = len(path) - 1
                    if actual_distance < best_distance:
                        best_target = kp_pos
                        best_distance = actual_distance
        except (ValueError, IndexError):
            continue
    
    # Jeśli brak key points - znajdź NAJDALSZY dostępny hex w zasięgu MP
    if not best_target:
        max_mp = unit.get('mp', 1)
        best_distance = 0
        
        # Wypróbuj cele od najdalszych do najbliższych
        for distance in range(min(max_mp, 5), 0, -1):  # Od max do 1
            candidates_found = []
            
            for direction in [(1,0), (0,1), (-1,1), (-1,0), (0,-1), (1,-1)]:
                candidate = (unit_pos[0] + direction[0] * distance, 
                           unit_pos[1] + direction[1] * distance)
                
                # Sprawdź czy można tam dotrzeć Z LIMITAMI MP i FUEL
                test_path = board.find_path(
                    unit_pos, candidate, 
                    max_mp=max_mp, 
                    max_fuel=unit.get('fuel', 99)
                )
                if test_path and len(test_path) > 1:
                    candidates_found.append(candidate)
            
            if candidates_found:
                # Wybierz pierwszy z najdalszych celów
                best_target = candidates_found[0]
                best_distance = distance
                break
        
        # Fallback - znajdź najbliższy osiągalny hex w kierunku centrum
        if not best_target:
            center = (10, 10)
            # Sprawdź czy centrum osiągalne
            center_path = board.find_path(
                unit_pos, center,
                max_mp=unit.get('mp', 1),
                max_fuel=unit.get('fuel', 99)
            )
            
            if center_path and len(center_path) > 1:
                best_target = center
            else:
                # Jeśli centrum nieosiągalne, znajdź najbliższy hex w kierunku centrum
                for dist in range(1, min(unit.get('mp', 1) + 1, 6)):
                    # Kierunek do centrum
                    dx = 1 if center[0] > unit_pos[0] else (-1 if center[0] < unit_pos[0] else 0)
                    dy = 1 if center[1] > unit_pos[1] else (-1 if center[1] < unit_pos[1] else 0)
                    
                    candidate = (unit_pos[0] + dx * dist, unit_pos[1] + dy * dist)
                    fallback_path = board.find_path(
                        unit_pos, candidate,
                        max_mp=unit.get('mp', 1),
                        max_fuel=unit.get('fuel', 99)
                    )
                    
                    if fallback_path and len(fallback_path) > 1:
                        best_target = candidate
                        break
    
    return best_target


def find_alternative_target_around(unit, base_target, game_engine, search_radius=3):
    """Znajdź alternatywny cel wokół base_target jeśli ten jest zajęty"""
    board = getattr(game_engine, 'board', None)
    if not board:
        return base_target
    
    unit_pos = (unit['q'], unit['r'])
    base_q, base_r = base_target[0], base_target[1]
    
    # Sprawdź czy base_target jest wolny
    if not board.is_occupied(base_q, base_r):
        return base_target
    
    # Znajdź najbliższy wolny hex w promieniu
    best_alternative = None
    best_distance = 999
    
    for radius in range(1, search_radius + 1):
        # Sprawdź heksy w kolejnych pierścieniach
        for dq in range(-radius, radius + 1):
            for dr in range(-radius, radius + 1):
                if abs(dq + dr) > radius:
                    continue
                
                candidate = (base_q + dq, base_r + dr)
                
                # Sprawdź czy hex jest wolny
                if board.is_occupied(candidate[0], candidate[1]):
                    continue
                
                # Sprawdź czy hex jest osiągalny
                path = board.find_path(unit_pos, candidate, max_mp=unit.get('mp', 1), max_fuel=unit.get('fuel', 1))
                if not path or len(path) < 2:
                    continue
                
                # Oblicz dystans od base_target
                distance = abs(candidate[0] - base_q) + abs(candidate[1] - base_r)
                if distance < best_distance:
                    best_alternative = candidate
                    best_distance = distance
        
        # Jeśli znaleziono w tym promieniu - użyj (najbliżej base_target)
        if best_alternative:
            break
    
    if best_alternative:
        print(f"[FORMATION] {unit.get('id')}: Cel {base_target} zajęty -> alternatywa {best_alternative}")
        return best_alternative
    else:
        print(f"[FORMATION] {unit.get('id')}: Brak wolnych miejsc wokół {base_target}")
        return base_target


def execute_mission_tactics(unit, base_target, mission_type, game_engine, unit_index, total_units):
    """
    Wykonuje różne taktyki w zależności od typu misji z ulepszoną formation coordination.
    
    Args:
        unit: Słownik z danymi jednostki
        base_target: Bazowy cel z rozkazu [q, r]
        mission_type: Typ misji (SECURE_KEYPOINT, INTEL_GATHERING, etc.)
        game_engine: GameEngine
        unit_index: Indeks jednostki w liście (0, 1, 2...)
        total_units: Całkowita liczba jednostek dowódcy
    
    Returns:
        tuple: Docelowe współrzędne (q, r) lub None
    """
    if not base_target or len(base_target) < 2:
        return base_target
    
    base_q, base_r = base_target[0], base_target[1]
    unit_pos = (unit['q'], unit['r'])
    
    # Pobierz board dla pathfinding
    board = getattr(game_engine, 'board', None)
    if not board:
        return base_target
    
    try:
        if mission_type == "INTEL_GATHERING":
            # ROZPOZNANIE: Rozproszone jednostki, różne kierunki
            spread_directions = [
                (1, 0), (0, 1), (-1, 1), (-1, 0), (0, -1), (1, -1)  # 6 kierunków hex
            ]
            direction = spread_directions[unit_index % len(spread_directions)]
            spread_distance = 3 + (unit_index % 3)  # 3-5 hexów oddalenia
            
            spread_target = (
                base_q + direction[0] * spread_distance,
                base_r + direction[1] * spread_distance
            )
            
            # Znajdź alternatywę jeśli cel zajęty
            final_target = find_alternative_target_around(unit, spread_target, game_engine)
            print(f"[TACTIC] INTEL: Jednostka {unit.get('id')} -> rozproszenie {final_target}")
            return final_target
                
        elif mission_type == "DEFEND_KEYPOINTS":
            # OBRONA: Pozycje obronne wokół celu - lepsze rozprowadzenie
            defense_radius = [2, 3, 2, 3, 2, 3]  # Zmienny promień
            defense_angles = [0, 60, 120, 180, 240, 300]  # Kąty w stopniach
            
            if unit_index < len(defense_angles):
                radius = defense_radius[unit_index % len(defense_radius)]
                angle = defense_angles[unit_index]
                
                # Konwersja kąt -> hex offset (uproszczona)
                import math
                rad = math.radians(angle)
                offset_q = int(round(radius * math.cos(rad)))
                offset_r = int(round(radius * math.sin(rad)))
                
                defense_target = (base_q + offset_q, base_r + offset_r)
                
                # Znajdź alternatywę jeśli zajęty
                final_target = find_alternative_target_around(unit, defense_target, game_engine)
                print(f"[TACTIC] DEFEND: Jednostka {unit.get('id')} -> pozycja obronna {final_target}")
                return final_target
            
            return find_alternative_target_around(unit, base_target, game_engine)
            
        elif mission_type == "ATTACK_ENEMY_VP":
            # ATAK: Skoordynowane natarcie - formacja bojowa
            unit_speed = unit.get('mp', 1)
            unit_fuel = unit.get('fuel', 1)
            mobility = unit_speed + unit_fuel
            
            # Fast units tworzą spearhead, slow units wspierają
            if mobility > 8:
                # Fast units - 2 pierwsze idą do celu, reszta na flanki
                if unit_index < 2:
                    final_target = find_alternative_target_around(unit, base_target, game_engine, search_radius=2)
                    print(f"[TACTIC] ATTACK: Fast spearhead {unit.get('id')} -> {final_target}")
                    return final_target
                else:
                    # Fast flankers
                    flank_offsets = [(-2, 1), (2, 1), (-1, 2), (1, 2)]
                    offset_idx = (unit_index - 2) % len(flank_offsets)
                    offset = flank_offsets[offset_idx]
                    flank_target = (base_q + offset[0], base_r + offset[1])
                    
                    final_target = find_alternative_target_around(unit, flank_target, game_engine)
                    print(f"[TACTIC] ATTACK: Fast flanker {unit.get('id')} -> {final_target}")
                    return final_target
            else:
                # Slow units - wsparcie z tyłu
                support_offsets = [(-3, 0), (-2, -1), (-3, 1), (-2, 1)]
                offset_idx = unit_index % len(support_offsets)
                offset = support_offsets[offset_idx]
                support_target = (base_q + offset[0], base_r + offset[1])
                
                final_target = find_alternative_target_around(unit, support_target, game_engine)
                print(f"[TACTIC] ATTACK: Slow support {unit.get('id')} -> {final_target}")
                return final_target
                    
        elif mission_type == "SECURE_KEYPOINT":
            # ZABEZPIECZENIE: Ulepszona formacja pierścieniowa
            if total_units == 1:
                # Pojedyncza jednostka - bezpośrednio do celu
                final_target = find_alternative_target_around(unit, base_target, game_engine)
                print(f"[TACTIC] SECURE: Solo unit {unit.get('id')} -> {final_target}")
                return final_target
            
            # Formacja pierścieniowa - lepsze rozprowadzenie
            formation_patterns = [
                # Pierścień 1 (blisko celu)
                [(0, 0), (-1, 0), (1, 0), (0, -1), (0, 1), (-1, 1), (1, -1)],
                # Pierścień 2 (dalej od celu)
                [(-2, 0), (2, 0), (-1, -1), (1, 1), (-2, 1), (2, -1), (0, -2), (0, 2)]
            ]
            
            # Wybierz pierścień na podstawie liczby jednostek
            if total_units <= 7:
                pattern = formation_patterns[0]
            else:
                # Większe siły - użyj obu pierścieni
                if unit_index < 7:
                    pattern = formation_patterns[0]
                else:
                    pattern = formation_patterns[1]
                    unit_index -= 7  # Przesun indeks dla drugiego pierścienia
            
            if unit_index < len(pattern):
                offset = pattern[unit_index]
                formation_target = (base_q + offset[0], base_r + offset[1])
                
                # Znajdź alternatywę jeśli zajęty
                final_target = find_alternative_target_around(unit, formation_target, game_engine)
                print(f"[TACTIC] SECURE: Formation unit {unit.get('id')} -> {final_target}")
                return final_target
            
            # Overflow - znajdź dowolne miejsce wokół celu
            final_target = find_alternative_target_around(unit, base_target, game_engine, search_radius=4)
            print(f"[TACTIC] SECURE: Overflow unit {unit.get('id')} -> {final_target}")
            return final_target
        else:
            # UNKNOWN mission type - fallback z alternatywą
            final_target = find_alternative_target_around(unit, base_target, game_engine)
            print(f"[TACTIC] UNKNOWN: {mission_type} -> {final_target}")
            return final_target
            
    except Exception as e:
        print(f"[TACTIC] ERROR: {e} -> fallback {base_target}")
        return base_target


def calculate_progressive_target(unit, final_target, game_engine):
    """
    Oblicz optymalny cel pośredni dla jednostki która nie może dotrzeć do końcowego celu w jednej turze.
    
    Args:
        unit: Słownik z danymi jednostki
        final_target: Końcowy cel [q, r]  
        game_engine: GameEngine
        
    Returns:
        tuple: Najlepszy cel pośredni (q, r)
    """
    board = getattr(game_engine, 'board', None)
    if not board:
        return final_target
    
    unit_pos = (unit['q'], unit['r'])
    final_pos = tuple(final_target) if isinstance(final_target, list) else final_target
    max_reach = min(unit['mp'], unit['fuel'])
    
    # Oblicz kierunek do celu
    direction_q = 1 if final_pos[0] > unit_pos[0] else (-1 if final_pos[0] < unit_pos[0] else 0)
    direction_r = 1 if final_pos[1] > unit_pos[1] else (-1 if final_pos[1] < unit_pos[1] else 0)
    
    # Sprawdź różne dystanse - od maksymalnego do minimalnego
    for distance in range(max_reach, max(1, max_reach // 2), -1):
        # Wypróbuj różne wariacje kierunku
        candidates = [
            # Bezpośredni kierunek
            (unit_pos[0] + direction_q * distance, unit_pos[1] + direction_r * distance),
            # Lekkie odchylenia dla uniknięcia przeszkód
            (unit_pos[0] + direction_q * distance + 1, unit_pos[1] + direction_r * distance),
            (unit_pos[0] + direction_q * distance - 1, unit_pos[1] + direction_r * distance),
            (unit_pos[0] + direction_q * distance, unit_pos[1] + direction_r * distance + 1),
            (unit_pos[0] + direction_q * distance, unit_pos[1] + direction_r * distance - 1),
            # Alternatywne kierunki (45 stopni odchylenie)
            (unit_pos[0] + distance, unit_pos[1]),
            (unit_pos[0], unit_pos[1] + distance),
            (unit_pos[0] - distance, unit_pos[1]),
            (unit_pos[0], unit_pos[1] - distance),
        ]
        
        best_candidate = None
        best_progress = 0
        
        for candidate in candidates:
            # Sprawdź czy możemy dotrzeć do kandydata
            path = board.find_path(unit_pos, candidate, max_mp=max_reach, max_fuel=max_reach)
            if not path or len(path) < 2:
                continue
            
            # Oblicz postęp w kierunku końcowego celu
            old_distance = board.hex_distance(unit_pos, final_pos)
            new_distance = board.hex_distance(candidate, final_pos)
            progress = old_distance - new_distance
            
            if progress > best_progress:
                best_candidate = candidate
                best_progress = progress
        
        if best_candidate:
            print(f"[PROGRESSIVE] {unit.get('id')}: Postęp {best_progress} hexów w kierunku {final_pos}")
            return best_candidate
    
    # Fallback - znajdź najbliższy osiągalny hex
    for radius in range(1, max_reach + 1):
        for dq in range(-radius, radius + 1):
            for dr in range(-radius, radius + 1):
                if abs(dq + dr) > radius:
                    continue
                
                candidate = (unit_pos[0] + dq, unit_pos[1] + dr)
                path = board.find_path(unit_pos, candidate, max_mp=max_reach, max_fuel=max_reach)
                if path and len(path) > 1:
                    print(f"[PROGRESSIVE] {unit.get('id')}: Fallback movement {candidate}")
                    return candidate
    
    print(f"[PROGRESSIVE] {unit.get('id')}: Brak możliwości ruchu")
    return unit_pos


def group_units_by_proximity(units, max_group_distance=8):
    """
    Grupuj jednostki według bliskości geograficznej dla lepszego zarządzania formacjami.
    
    Args:
        units: Lista jednostek
        max_group_distance: Maksymalny dystans dla grupy
        
    Returns:
        list: Lista grup jednostek
    """
    if not units:
        return []
    
    groups = []
    ungrouped = units.copy()
    
    while ungrouped:
        # Rozpocznij nową grupę od pierwszej jednostki
        leader = ungrouped.pop(0)
        group = [leader]
        leader_pos = (leader['q'], leader['r'])
        
        # Znajdź jednostki w pobliżu
        remaining = []
        for unit in ungrouped:
            unit_pos = (unit['q'], unit['r'])
            # Uproszczony hex distance
            distance = abs(unit_pos[0] - leader_pos[0]) + abs(unit_pos[1] - leader_pos[1]) + abs((unit_pos[0] + unit_pos[1]) - (leader_pos[0] + leader_pos[1]))
            distance = distance // 2
            
            if distance <= max_group_distance:
                group.append(unit)
            else:
                remaining.append(unit)
        
        ungrouped = remaining
        groups.append(group)
        
        print(f"[GROUPING] Grupa {len(groups)}: {len(group)} jednostek wokół {leader_pos}")
    
    return groups


def move_towards(unit, target, game_engine):
    """Wykonaj ruch w kierunku celu - ULEPSZONA WERSJA z progressive movement"""
    
    print(f"[AI] Szukam ścieżki {unit['id']}: ({unit['q']},{unit['r']}) -> {target}")
    
    board = getattr(game_engine, 'board', None)
    if not board:
        print(f"[AI] Brak board w game_engine")
        return False

    unit_pos = (unit['q'], unit['r'])
    token = unit.get('token', None)
    
    # DEBUG: sprawdź token
    if token is None:
        print(f"[AI] Brak tokenu w unit dict")
        return False
    
    if isinstance(token, str):
        print(f"[AI] Token jest stringiem: {token} - próbuję znaleźć obiekt")
        all_tokens = getattr(game_engine, 'tokens', [])
        for t in all_tokens:
            if getattr(t, 'id', None) == token:
                token = t
                print(f"[AI] Znaleziono obiekt tokenu: {type(token)}")
                break
        else:
            print(f"[AI] Nie znaleziono obiektu tokenu dla id: {token}")
            return False

    # KONWERSJA TARGET
    target_tuple = tuple(target) if isinstance(target, list) else target
    print(f"[AI Pathfinding] Konwersja: {target} -> {target_tuple}")
    
    # SPRAWDZENIE REALNOŚCI CELU - hex distance calculation
    hex_distance = board.hex_distance(unit_pos, target_tuple)
    max_reach = min(unit['mp'], unit['fuel'])
    
    # PROGRESSIVE MOVEMENT - jeśli cel za daleko
    if hex_distance > max_reach:
        print(f"[AI Pathfinding] ⚠️ Cel za daleko! Dystans: {hex_distance}, Zasięg: {max_reach}")
        print(f"[AI Pathfinding] Obliczam cel pośredni...")
        
        # Użyj progressive targeting
        progressive_target = calculate_progressive_target(unit, target_tuple, game_engine)
        if progressive_target != unit_pos:
            target_tuple = progressive_target
            print(f"[AI Pathfinding] ✅ Cel pośredni: {target_tuple}")
        else:
            print(f"[AI Pathfinding] ❌ Brak możliwości ruchu")
            return False

    # PATHFINDING
    try:
        from engine.action_refactored_clean import PathfindingService
        path = PathfindingService.find_movement_path(
            game_engine, token, unit_pos, target_tuple, 
            game_engine.current_player_obj
        )
        print(f"[AI Pathfinding] Bazowa ścieżka: {path}")
        
        if not path or len(path) < 2:
            print(f"[AI Pathfinding] ❌ Brak ścieżki!")
            return False
        
        # Sprawdź zasoby vs długość ścieżki
        full_distance = len(path) - 1
        max_steps = min(unit['mp'], unit['fuel'], full_distance)
        
        if max_steps <= 0:
            print(f"[AI Pathfinding] ❌ Brak zasobów (MP={unit['mp']}, Fuel={unit['fuel']})")
            return False
        
        # Przytnij ścieżkę do dostępnych kroków
        if max_steps < full_distance:
            path = path[:max_steps + 1]
            print(f"[AI Pathfinding] ⚠️ Częściowo ({max_steps}/{full_distance}): {path}")
        else:
            print(f"[AI Pathfinding] ✅ Pełna ścieżka ({full_distance}): {path}")
        
        target_hex = path[-1]
        is_partial_path = (max_steps < full_distance)
        
        # COLLISION AVOIDANCE na końcowym hexie
        if board.is_occupied(target_hex[0], target_hex[1]):
            print(f"[AI Pathfinding] ⚠️ Końcowy hex {target_hex} zajęty - szukam sąsiedniego")
            neighbors = board.neighbors(target_hex[0], target_hex[1])
            
            for neighbor in neighbors:
                if not board.is_occupied(neighbor[0], neighbor[1]):
                    neighbor_distance = len(path) - 1 + 1
                    if neighbor_distance <= max_steps:
                        target_hex = neighbor
                        print(f"[AI Pathfinding] ✅ Używam sąsiedniego hexu: {target_hex}")
                        break
            else:
                print(f"[AI Pathfinding] ⚠️ Wszyscy sąsiedzi zajęci - próbuję oryginalny cel")
        
        # WYKONAJ RUCH
        if path and len(path) > 1:
            from engine.action_refactored_clean import MoveAction
            
            if hasattr(token, 'id'):
                token_id = token.id
                print(f"[AI Move] Wykonuję ruch {token_id}: {unit_pos} -> {target_hex}")
                
                action = MoveAction(token_id, target_hex[0], target_hex[1])
                result = game_engine.execute_action(action)
                
                success = getattr(result, 'success', False) if result else False
                if success:
                    print(f"[AI Move] ✅ Sukces: {getattr(result, 'message', 'OK')}")
                    
                    # LOGOWANIE
                    player_nation = getattr(game_engine.current_player_obj, 'nation', 'Unknown')
                    move_type = "progressive_move" if hex_distance > max_reach else ("partial_move" if is_partial_path else "full_move")
                    reason = f"Strategic move to {target}"
                    
                    log_commander_action(
                        unit_id=unit['id'],
                        action_type=move_type,
                        from_pos=unit_pos,
                        to_pos=target_hex,
                        reason=reason,
                        player_nation=player_nation
                    )
                else:
                    print(f"[AI Move] ❌ Błąd: {getattr(result, 'message', 'Nieznany błąd')}")
                    
                return success
            else:
                print(f"[AI Move] Brak ID tokenu dla {unit['id']}")
                return False
            
    except Exception as e:
        print(f"[AI] Błąd ruchu: {e}")
        
    return False


def make_tactical_turn(game_engine, player_id=None):
    """Główna funkcja AI Commandera - ULEPSZONA z progressive movement i grouping
    
    Args:
        game_engine: GameEngine
        player_id: ID gracza (2, 3, 5, 6) lub None (auto-detect)
    """
    try:
        # Określ ID gracza
        if player_id is None:
            current_player = getattr(game_engine, 'current_player_obj', None)
            if current_player:
                player_id = getattr(current_player, 'id', None)
        
        print(f"[AICommander] Tura dla gracza (id={player_id})")
        
        # Pobierz nazwę narodu dla logów
        player_nation = "Unknown"
        current_player = getattr(game_engine, 'current_player_obj', None)
        if current_player:
            player_nation = getattr(current_player, 'nation', 'Unknown')
        
        # LOGUJ POCZĄTEK TURY
        log_commander_action(
            unit_id="TURN_START",
            action_type="turn_begin",
            from_pos=None,
            to_pos=None,
            reason=f"AI Commander turn started for player {player_id}",
            player_nation=player_nation
        )
        
        # STRATEGICZNE ROZKAZY od General
        strategic_order = None
        try:
            if current_player:
                temp_commander = type('obj', (), {'player': current_player})()
                current_turn = getattr(game_engine, 'turn_number', getattr(game_engine, 'current_turn', 1))
                strategic_order = AICommander.receive_orders(temp_commander, current_turn=current_turn)
                
                if strategic_order:
                    print(f"📋 [AI] Otrzymano strategiczny rozkaz: {strategic_order['mission_type']} -> {strategic_order['target_hex']}")
                else:
                    print(f"🔄 [AI] Brak rozkazów strategicznych - tryb autonomiczny")
        except Exception as e:
            print(f"⚠️ [AI] Błąd odczytu rozkazów strategicznych: {e}")
        
        # 1. Zbierz dane
        my_units = get_my_units(game_engine, player_id)
        print(f"[AI] Znaleziono {len(my_units)} jednostek dla gracza {player_id}")
        if not my_units:
            print(f"[AI] Brak jednostek dla gracza {player_id}")
            return
        
        # 2. GRUPOWANIE JEDNOSTEK według bliskości
        unit_groups = group_units_by_proximity(my_units, max_group_distance=8)
        print(f"[AI] Utworzono {len(unit_groups)} grup jednostek")
        
        # 3. COMBAT PHASE - dla każdej jednostki sprawdź możliwe ataki
        combat_count = 0
        for i, unit in enumerate(my_units):
            unit_name = unit.get('id', f'unit_{i}')
            can_move_result = can_move(unit)
            
            if can_move_result:
                combat_attempted = ai_attempt_combat(unit, game_engine, player_id, player_nation)
                if combat_attempted:
                    combat_count += 1
        
        # 4. MOVEMENT PHASE - grupowe zarządzanie ruchem
        moved_count = 0
        total_processed = 0
        
        for group_idx, group in enumerate(unit_groups):
            print(f"[AI] Przetwarzam grupę {group_idx + 1}/{len(unit_groups)} ({len(group)} jednostek)")
            
            # Oblicz średnią pozycję grupy dla lepszego target selection
            if strategic_order and strategic_order.get('target_hex'):
                # Wszystkie grupy mają ten sam strategiczny cel
                base_target = strategic_order['target_hex']
                mission_type = strategic_order.get('mission_type', 'UNKNOWN')
            else:
                # Autonomiczny cel dla grupy - wybierz na podstawie pozycji lidera
                leader = group[0]
                base_target = find_target(leader, game_engine)
                mission_type = 'AUTONOMOUS'
            
            # Przetwórz jednostki w grupie
            for unit_idx, unit in enumerate(group):
                total_processed += 1
                unit_name = unit.get('id', f'unit_{total_processed}')
                can_move_result = can_move(unit)
                print(f"[AI] {unit_name}: MP={unit.get('mp', 0)}, Fuel={unit.get('fuel', 0)}, Can move: {can_move_result}")
                
                if can_move_result:
                    # Wybierz cel i taktykę
                    if base_target:
                        if mission_type != 'AUTONOMOUS':
                            # TAKTYKA STRATEGICZNA
                            target = execute_mission_tactics(unit, base_target, mission_type, game_engine, unit_idx, len(group))
                            print(f"[AI] {unit_name}: {mission_type} -> {target} (taktyka)")
                        else:
                            # AUTONOMOUS MOVEMENT
                            target = base_target
                            print(f"[AI] {unit_name}: Cel autonomiczny {target}")
                    else:
                        print(f"[AI] {unit_name}: Brak celu")
                        continue
                    
                    if target:
                        success = move_towards(unit, target, game_engine)
                        if success:
                            moved_count += 1
                            # Log taktyki
                            log_commander_action(
                                unit_id=unit_name,
                                action_type="tactical_move",
                                from_pos=(unit['q'], unit['r']),
                                to_pos=target,
                                reason=f"{mission_type} mission (group {group_idx + 1})",
                                player_nation=player_nation
                            )
                        else:
                            print(f"[AI] {unit_name}: Ruch nieudany")
                    else:
                        print(f"[AI] {unit_name}: Brak celu")
                else:
                    print(f"[AI] {unit_name}: Nie może się ruszyć")
        
        print(f"[AI] Ruszono {moved_count} jednostek z {len(my_units)} (sukces: {moved_count/len(my_units)*100:.1f}%)")
        
        # LOGUJ KONIEC TURY
        log_commander_action(
            unit_id="TURN_END",
            action_type="turn_summary",
            from_pos=None,
            to_pos=None,
            reason=f"Turn completed: {moved_count}/{len(my_units)} units moved, {len(unit_groups)} groups",
            player_nation=player_nation
        )
        
    except Exception as e:
        print(f"[AI] Błąd tury: {e}")
        # NIE CRASHUJ - po prostu zakończ turę


class AICommander:
    """Wrapper klasa dla kompatybilności z istniejącym kodem"""
    def __init__(self, player: Any):
        self.player = player

    def pre_resupply(self, game_engine: Any) -> None:
        """Automatyczne uzupełnianie paliwa i siły bojowej AI"""
        print(f"🔧 [DEBUG Resupply] START dla {self.player.nation} (id={self.player.id})")
        
        # POPRAWKA: Pobierz punkty z economy system + synchronizuj
        punkty = 0
        
        # Spróbuj economy.economic_points (AI General zapisuje tutaj)
        if hasattr(self.player, 'economy') and self.player.economy is not None:
            punkty = self.player.economy.economic_points
            print(f"[AI Resupply] {self.player.nation}: Znaleziono {punkty} pkt w economy.economic_points")
        
        # Fallback do punkty_ekonomiczne
        if punkty <= 0:
            punkty = getattr(self.player, 'punkty_ekonomiczne', 0)
            print(f"[AI Resupply] {self.player.nation}: Fallback - {punkty} pkt w punkty_ekonomiczne")
        
        # Jeśli nadal zero - sprawdź get_points()
        if punkty <= 0 and hasattr(self.player, 'economy') and hasattr(self.player.economy, 'get_points'):
            points_data = self.player.economy.get_points()
            punkty = points_data.get('economic_points', 0)
            print(f"[AI Resupply] {self.player.nation}: Fallback2 - {punkty} pkt z get_points()")
        
        if punkty <= 0:
            print(f"[AI Resupply] {self.player.nation}: ❌ BRAK PUNKTÓW - wszystkie źródła puste!")
            print(f"  - player.economy: {getattr(self.player, 'economy', None)}")
            print(f"  - player.punkty_ekonomiczne: {getattr(self.player, 'punkty_ekonomiczne', None)}")
            return
            
        print(f"[AI Resupply] {self.player.nation}: ✅ Rozpoczynam z {punkty} punktami")
        
        # DEBUG: Sprawdź strukturę game_engine
        print(f"🔧 [DEBUG] game_engine type: {type(game_engine)}")
        print(f"🔧 [DEBUG] game_engine.board: {hasattr(game_engine, 'board')}")
        print(f"🔧 [DEBUG] game_engine.tokens: {hasattr(game_engine, 'tokens')}")
        
        # Znajdź wszystkie moje żetony - SPRAWDŹ OBA MIEJSCA
        my_tokens = []
        expected_owner = f"{self.player.id} ({self.player.nation})"
        print(f"🔧 [DEBUG] Szukam tokenów dla owner: '{expected_owner}'")
        
        # Opcja 1: game_engine.board.tokens
        tokens_found_board = 0
        if hasattr(game_engine, 'board') and hasattr(game_engine.board, 'tokens'):
            tokens_found_board = len(game_engine.board.tokens)
            print(f"🔧 [DEBUG] game_engine.board.tokens count: {tokens_found_board}")
            for i, token in enumerate(game_engine.board.tokens):
                token_owner = getattr(token, 'owner', 'NO_OWNER')
                print(f"🔧 [DEBUG] Token[{i}]: owner='{token_owner}', id={getattr(token, 'id', 'NO_ID')}")
                if token_owner == expected_owner:
                    my_tokens.append(token)
        
        # Opcja 2: game_engine.tokens (fallback)
        tokens_found_engine = 0
        if not my_tokens and hasattr(game_engine, 'tokens'):
            tokens_found_engine = len(game_engine.tokens)
            print(f"🔧 [DEBUG] game_engine.tokens count: {tokens_found_engine}")
            for i, token in enumerate(game_engine.tokens):
                token_owner = getattr(token, 'owner', 'NO_OWNER')
                print(f"🔧 [DEBUG] EngineToken[{i}]: owner='{token_owner}', id={getattr(token, 'id', 'NO_ID')}")
                if token_owner == expected_owner:
                    my_tokens.append(token)
        
        print(f"🔧 [DEBUG] Znaleziono {len(my_tokens)} moich tokenów")
        
        if not my_tokens:
            print(f"[AI Resupply] {self.player.nation}: ❌ BRAK ŻETONÓW DO UZUPEŁNIENIA")
            print(f"🔧 [DEBUG] Expected owner: '{expected_owner}'")
            print(f"🔧 [DEBUG] Board tokens: {tokens_found_board}, Engine tokens: {tokens_found_engine}")
            return
        
        # Sortuj według priorytetu: najpierw niskie paliwo, potem niska siła bojowa
        def get_priority(token):
            current_fuel = getattr(token, 'currentFuel', 0)
            max_fuel = getattr(token, 'maxFuel', token.stats.get('maintenance', 0))
            fuel_pct = current_fuel / max(max_fuel, 1)
            
            current_combat = getattr(token, 'combat_value', token.stats.get('combat_value', 0))
            max_combat = token.stats.get('combat_value', 0)
            combat_pct = current_combat / max(max_combat, 1)
            
            # Priorytet: im niższy procent, tym wyższy priorytet (sortuj rosnąco)
            return min(fuel_pct, combat_pct)
        
        my_tokens.sort(key=get_priority)
        
        # Uzupełniaj jednostki
        resupplied_count = 0
        for token in my_tokens:
            if punkty <= 0:
                break
                
            # Oblicz ile potrzebuje uzupełnienia
            current_fuel = getattr(token, 'currentFuel', 0)
            max_fuel = getattr(token, 'maxFuel', token.stats.get('maintenance', 0))
            fuel_needed = max(0, max_fuel - current_fuel)
            
            current_combat = getattr(token, 'combat_value', token.stats.get('combat_value', 0))
            max_combat = token.stats.get('combat_value', 0)
            combat_needed = max(0, max_combat - current_combat)
            
            total_needed = fuel_needed + combat_needed
            
            print(f"🔧 [DEBUG] Token {token.id}: fuel={current_fuel}/{max_fuel} (need {fuel_needed}), combat={current_combat}/{max_combat} (need {combat_needed})")
            
            if total_needed <= 0:
                print(f"🔧 [DEBUG] Token {token.id}: PEŁNY - pomijam")
                continue  # Jednostka pełna
            
            # Ograniczenie do dostępnych punktów
            can_spend = min(total_needed, punkty)
            
            # Priorytetyzacja: paliwo < 50% to najpierw paliwo
            fuel_pct = current_fuel / max(max_fuel, 1)
            if fuel_pct < 0.5 and fuel_needed > 0:
                # Najpierw paliwo
                fuel_add = min(fuel_needed, can_spend)
                combat_add = min(combat_needed, can_spend - fuel_add)
                print(f"🔧 [DEBUG] Token {token.id}: PRIORYTET PALIWO (fuel_pct={fuel_pct:.2f})")
            else:
                # Równomierne dzielenie
                fuel_add = min(fuel_needed, can_spend // 2)
                combat_add = min(combat_needed, can_spend - fuel_add)
                print(f"🔧 [DEBUG] Token {token.id}: RÓWNOMIERNE DZIELENIE")
            
            print(f"🔧 [DEBUG] Token {token.id}: Planowane +{fuel_add} fuel, +{combat_add} combat (budżet: {can_spend})")
            
            # Uzupełnij
            if fuel_add > 0:
                old_fuel = token.currentFuel
                token.currentFuel += fuel_add
                if token.currentFuel > max_fuel:
                    token.currentFuel = max_fuel
                print(f"🔧 [DEBUG] Token {token.id}: Fuel {old_fuel} -> {token.currentFuel}")
            
            if combat_add > 0:
                old_combat = getattr(token, 'combat_value', 0)
                if hasattr(token, 'combat_value'):
                    token.combat_value += combat_add
                else:
                    token.combat_value = combat_add
                if token.combat_value > max_combat:
                    token.combat_value = max_combat
                print(f"🔧 [DEBUG] Token {token.id}: Combat {old_combat} -> {token.combat_value}")
            
            # Odejmij punkty
            spent = fuel_add + combat_add
            punkty -= spent
            self.player.punkty_ekonomiczne = punkty
            
            # Synchronizuj z economy jeśli istnieje
            if hasattr(self.player, 'economy') and self.player.economy is not None:
                self.player.economy.economic_points = punkty
            
            if spent > 0:
                resupplied_count += 1
                print(f"[AI Resupply] {self.player.nation}: {token.stats.get('label', token.id)[:15]} -> fuel+{fuel_add}, combat+{combat_add} (koszt: {spent})")
        
        print(f"[AI Resupply] {self.player.nation}: ✅ Zakończono, uzupełniono {resupplied_count} jednostek, pozostało {punkty} punktów")

    def make_tactical_turn(self, game_engine: Any) -> None:
        """Wykonaj turę taktyczną - używa prostych funkcji"""
        player_id = getattr(self.player, 'id', None)
        print(f"[AICommander] Tura dla {self.player.nation} (id={player_id})")
        make_tactical_turn(game_engine, player_id)

    def receive_orders(self, orders_file_path=None, current_turn=1):
        """
        Odbiera strategiczne rozkazy z pliku wydanego przez AI General.
        
        Args:
            orders_file_path: Ścieżka do pliku z rozkazami (domyślnie data/strategic_orders.json)
            current_turn: Aktualny numer tury do sprawdzenia ważności rozkazów
            
        Returns:
            dict: Rozkaz dla tego dowódcy lub None jeśli brak/wygasł
        """
        import json
        from pathlib import Path
        
        # Domyślna ścieżka do pliku rozkazów
        if orders_file_path is None:
            orders_file_path = Path("data/strategic_orders.json")
        else:
            orders_file_path = Path(orders_file_path)
        
        # Sprawdź czy plik istnieje
        if not orders_file_path.exists():
            return None
        
        try:
            # Wczytaj rozkazy z pliku
            with open(orders_file_path, 'r', encoding='utf-8') as f:
                orders_data = json.load(f)
            
            # Sprawdź czy są rozkazy dla tego dowódcy
            # Najpierw spróbuj po ID dowódcy (nowy system)
            my_nation = self.player.nation.lower()
            commander_id = f"{my_nation}_commander_{self.player.id}"
            
            my_order = None
            
            # Nowy system - indywidualne rozkazy per dowódca
            if "orders" in orders_data and commander_id in orders_data["orders"]:
                my_order = orders_data["orders"][commander_id]
            # Fallback - stary system per nacja (dla kompatybilności)
            elif "orders" in orders_data and my_nation in orders_data["orders"]:
                my_order = orders_data["orders"][my_nation]
            
            if not my_order:
                return None
            
            # Sprawdź czy rozkaz nie wygasł
            expires_turn = my_order.get("expires_turn", 0)
            if current_turn > expires_turn:
                return None  # Rozkaz wygasł
            
            # Sprawdź czy rozkaz jest aktywny
            if my_order.get("status") != "ACTIVE":
                return None
            
            # Zwróć rozkaz
            return my_order
            
        except Exception as e:
            print(f"❌ Błąd odczytu rozkazów: {e}")
            return None


def test_basic_safety():
    """Test że AI nie crashuje"""
    # Stwórz mock engine
    mock_engine = type('obj', (), {
        'tokens': [],
        'key_points_state': {},
        'board': None,
        'current_player_obj': type('obj', (), {'nation': 'Test'})()
    })()
    
    # Powinno nie crashować
    try:
        make_tactical_turn(mock_engine)
        print("TEST: Brak crashu przy pustych danych ✓")
        return True
    except Exception as e:
        print(f"TEST: Błąd - {e}")
        return False

if __name__ == "__main__":
    # Uruchom test bezpieczeństwa
    test_basic_safety()

