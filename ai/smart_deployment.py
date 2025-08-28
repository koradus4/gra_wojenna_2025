"""INTELIGENTNY SYSTEM SPAWNOWANIA JEDNOSTEK

FUNKCJE:
- Analiza potrzeb taktycznych
- Wybór najlepszego spawnu na podstawie sytuacji
- Adaptacja do zmian mapy
- Elastyczność dla różnych konfiguracji spawn pointów
"""

import math
import json
import os
from typing import List, Tuple, Dict, Any, Optional


def calculate_hex_distance(pos1: Tuple[int, int], pos2: Tuple[int, int]) -> int:
    """Oblicza odległość między dwoma hex positions (axial coordinates)"""
    q1, r1 = pos1
    q2, r2 = pos2
    return (abs(q1 - q2) + abs(q1 + r1 - q2 - r2) + abs(r1 - r2)) // 2


def analyze_tactical_situation(game_engine, player_id):
    """Analizuje sytuację taktyczną na mapie"""
    analysis = {
        'threatened_areas': [],
        'key_points_undefended': [],
        'friendly_clusters': [],
        'enemy_threats': [],
        'strategic_priorities': []
    }
    
    # Pobierz jednostki gracza
    my_units = get_my_units(game_engine, player_id)
    
    # Pobierz punkty kluczowe
    key_points = get_all_key_points(game_engine)
    
    # Znajdź wrogów
    all_tokens = getattr(game_engine, 'tokens', [])
    current_player = getattr(game_engine, 'current_player_obj', None)
    my_nation = getattr(current_player, 'nation', '') if current_player else ''
    
    enemy_units = []
    for token in all_tokens[:100]:  # Limit dla wydajności
        token_owner = getattr(token, 'owner', '')
        if token_owner and token_owner != player_id:
            enemy_units.append({
                'q': getattr(token, 'q', 0),
                'r': getattr(token, 'r', 0),
                'strength': getattr(token, 'current_strength', 1)
            })
    
    # 1. ZNAJDŹ ZAGROŻONE OBSZARY
    for unit in my_units:
        unit_pos = (unit['q'], unit['r'])
        nearest_enemy_distance = float('inf')
        
        for enemy in enemy_units:
            enemy_pos = (enemy['q'], enemy['r'])
            distance = calculate_hex_distance(unit_pos, enemy_pos)
            nearest_enemy_distance = min(nearest_enemy_distance, distance)
        
        if nearest_enemy_distance <= 3:  # Bliskie zagrożenie
            analysis['threatened_areas'].append({
                'position': unit_pos,
                'threat_level': 4 - nearest_enemy_distance,
                'unit_strength': unit.get('strength', 1)
            })
    
    # 2. PUNKTY KLUCZOWE BEZ OBRONY
    for kp_pos, kp_data in key_points.items():
        closest_friendly = float('inf')
        closest_enemy = float('inf')
        
        for unit in my_units:
            unit_pos = (unit['q'], unit['r'])
            distance = calculate_hex_distance(kp_pos, unit_pos)
            closest_friendly = min(closest_friendly, distance)
        
        for enemy in enemy_units:
            enemy_pos = (enemy['q'], enemy['r'])
            distance = calculate_hex_distance(kp_pos, enemy_pos)
            closest_enemy = min(closest_enemy, distance)
        
        if closest_enemy < closest_friendly or closest_friendly > 4:
            analysis['key_points_undefended'].append({
                'position': kp_pos,
                'value': kp_data.get('value', 0),
                'threat_level': max(0, 5 - closest_enemy)
            })
    
    # 3. KLASTRY PRZYJACIÓŁ (do wsparcia)
    processed_units = set()
    for i, unit in enumerate(my_units):
        if i in processed_units:
            continue
            
        cluster = [unit]
        unit_pos = (unit['q'], unit['r'])
        
        for j, other_unit in enumerate(my_units[i+1:], i+1):
            if j in processed_units:
                continue
            other_pos = (other_unit['q'], other_unit['r'])
            if calculate_hex_distance(unit_pos, other_pos) <= 2:
                cluster.append(other_unit)
                processed_units.add(j)
        
        if len(cluster) >= 2:
            # Znajdź środek klastra
            avg_q = sum(u['q'] for u in cluster) // len(cluster)
            avg_r = sum(u['r'] for u in cluster) // len(cluster)
            analysis['friendly_clusters'].append({
                'center': (avg_q, avg_r),
                'size': len(cluster),
                'total_strength': sum(u.get('strength', 1) for u in cluster)
            })
    
    return analysis


def evaluate_spawn_position(spawn_pos: Tuple[int, int], tactical_analysis: Dict, 
                           game_engine, nation: str) -> float:
    """Ocenia jakość pozycji spawn według sytuacji taktycznej"""
    score = 100.0  # Bazowy wynik
    
    # 1. BONUS ZA REAGOWANIE NA ZAGROŻENIA (WYSOKIE PRIORYTETY)
    threat_bonus = 0
    for threat in tactical_analysis['threatened_areas']:
        threat_pos = threat['position']
        distance = calculate_hex_distance(spawn_pos, threat_pos)
        
        if distance <= 2:
            # Bardzo blisko zagrożenia - duży bonus
            threat_bonus += (3 - distance) * threat['threat_level'] * 50
        elif distance <= 4:
            # Średnio blisko - średni bonus
            threat_bonus += (5 - distance) * threat['threat_level'] * 20
    
    score += threat_bonus
    
    # 2. BONUS ZA OCHRONĘ PUNKTÓW KLUCZOWYCH
    kp_bonus = 0
    for kp in tactical_analysis['key_points_undefended']:
        kp_pos = kp['position']
        distance = calculate_hex_distance(spawn_pos, kp_pos)
        
        if distance <= 3:
            # Bonus proporcjonalny do wartości punktu i odwrotnie do odległości
            kp_bonus += (kp['value'] / 10) * (4 - distance) * (kp['threat_level'] + 1)
        elif distance <= 6:
            # Słabszy bonus dla dalszych punktów
            kp_bonus += (kp['value'] / 20) * (7 - distance) * kp['threat_level']
    
    score += kp_bonus
    
    # 3. BONUS ZA WSPARCIE KLASTRÓW
    cluster_bonus = 0
    for cluster in tactical_analysis['friendly_clusters']:
        cluster_pos = cluster['center']
        distance = calculate_hex_distance(spawn_pos, cluster_pos)
        
        if distance <= 2:
            # Bardzo blisko klastra - wsparcie
            cluster_bonus += cluster['size'] * (3 - distance) * 15
        elif distance <= 4:
            # Średnio blisko - koordynacja
            cluster_bonus += cluster['size'] * (5 - distance) * 8
    
    score += cluster_bonus
    
    # 4. MALUS ZA NIEBEZPIECZEŃSTWO (KRYTYCZNY CZYNNIK)
    danger_malus = 0
    all_tokens = getattr(game_engine, 'tokens', [])
    current_player = getattr(game_engine, 'current_player_obj', None)
    player_id = getattr(current_player, 'player_id', '') if current_player else ''
    
    for token in all_tokens[:50]:  # Limit dla wydajności
        token_owner = getattr(token, 'owner', '')
        if token_owner and token_owner != player_id:
            enemy_pos = (getattr(token, 'q', 0), getattr(token, 'r', 0))
            distance = calculate_hex_distance(spawn_pos, enemy_pos)
            enemy_strength = getattr(token, 'current_strength', 1)
            
            if distance <= 1:
                danger_malus += 300 + (enemy_strength * 10)  # Bardzo niebezpieczne
            elif distance <= 2:
                danger_malus += 150 + (enemy_strength * 5)   # Niebezpieczne
            elif distance <= 3:
                danger_malus += 50 + enemy_strength          # Ryzykowne
    
    score -= danger_malus
    
    # 5. STRATEGICZNE POZYCJONOWANIE
    # Różnicuj spawny według ich charakteru strategicznego
    strategic_bonus = get_strategic_spawn_bonus(spawn_pos, nation)
    score += strategic_bonus
    
    # 6. UNIKAJ PRZELUDNIENIA
    # Malus jeśli zbyt wiele jednostek już w okolicy
    overcrowding_malus = 0
    friendly_count = 0
    for token in all_tokens[:50]:
        token_owner = getattr(token, 'owner', '')
        if token_owner == player_id:
            friendly_pos = (getattr(token, 'q', 0), getattr(token, 'r', 0))
            distance = calculate_hex_distance(spawn_pos, friendly_pos)
            if distance <= 3:
                friendly_count += 1
    
    if friendly_count >= 4:
        overcrowding_malus = friendly_count * 30  # Malus za przeludnienie
    
    score -= overcrowding_malus
    
    return score


def get_strategic_spawn_bonus(spawn_pos: Tuple[int, int], nation: str) -> float:
    """Nadaje bonus strategiczny różnym spawn pointom według ich charakteru"""
    
    # Definicje strategiczne dla różnych spawn points
    strategic_roles = {
        'Polska': {
            (6, -3): {'role': 'main_base', 'bonus': 10},      # Główna baza
            (0, 2): {'role': 'western_front', 'bonus': 15},   # Front zachodni
            (0, 13): {'role': 'city_defense', 'bonus': 20},   # Obrona miasta
            (0, 14): {'role': 'city_support', 'bonus': 15},   # Wsparcie miasta
            (18, 24): {'role': 'southern_flank', 'bonus': 25}, # Flanka południowa
            (24, -12): {'role': 'eastern_advance', 'bonus': 30}, # Ofensywa wschodnia
            (25, 20): {'role': 'central_reserve', 'bonus': 12}  # Rezerwa centralna
        },
        'Niemcy': {
            (52, -26): {'role': 'main_base', 'bonus': 10},
            (55, -23): {'role': 'northern_flank', 'bonus': 25},
            (55, -20): {'role': 'advance_position', 'bonus': 30},
            (49, 8): {'role': 'southern_thrust', 'bonus': 35},
            (40, -20): {'role': 'central_axis', 'bonus': 20}
        }
    }
    
    spawn_info = strategic_roles.get(nation, {}).get(spawn_pos, {'bonus': 0})
    return spawn_info['bonus']


def find_optimal_spawn_position(unit_data, game_engine, player_id) -> Optional[Tuple[int, int]]:
    """Znajduje optymalną pozycję spawn na podstawie analizy taktycznej"""
    board = getattr(game_engine, 'board', None)
    if not board:
        return None
    
    current_player = getattr(game_engine, 'current_player_obj', None)
    nation = getattr(current_player, 'nation', 'Unknown')
    
    # Pobierz spawn points dla tej nacji - ładuj bezpośrednio z pliku
    try:
        map_data_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'data', 'map_data.json')
        with open(map_data_path, 'r', encoding='utf-8') as f:
            map_data = json.load(f)
    except Exception as e:
        print(f"[SMART_DEPLOY] Błąd ładowania map_data.json: {e}")
        return None
    
    spawn_points = map_data.get('spawn_points', {}).get(nation, [])
    
    if not spawn_points:
        print(f"[SMART_DEPLOY] Brak spawn points dla nacji {nation}")
        return None
    
    print(f"[SMART_DEPLOY] Analiza {len(spawn_points)} spawn points dla {nation}")
    
    # Przeprowadź analizę taktyczną
    tactical_analysis = analyze_tactical_situation(game_engine, player_id)
    
    # Oceń wszystkie dostępne spawn points
    spawn_candidates = []
    
    for spawn_str in spawn_points:
        try:
            spawn_pos = tuple(map(int, spawn_str.split(',')))
            
            # Sprawdź czy pozycja jest wolna
            if not board.is_occupied(spawn_pos[0], spawn_pos[1]):
                score = evaluate_spawn_position(spawn_pos, tactical_analysis, game_engine, nation)
                spawn_candidates.append({
                    'position': spawn_pos,
                    'score': score,
                    'reason': f"Wynik: {score:.1f}"
                })
        except (ValueError, IndexError):
            continue
    
    # Jeśli wszystkie spawn points zajęte, sprawdź sąsiednie pozycje
    if not spawn_candidates:
        print(f"[SMART_DEPLOY] Wszystkie spawn points zajęte, sprawdzam sąsiednie...")
        
        for spawn_str in spawn_points:
            try:
                spawn_pos = tuple(map(int, spawn_str.split(',')))
                neighbors = board.neighbors(spawn_pos[0], spawn_pos[1])
                
                for neighbor in neighbors:
                    if not board.is_occupied(neighbor[0], neighbor[1]):
                        score = evaluate_spawn_position(neighbor, tactical_analysis, game_engine, nation)
                        # Malus za nie bycie dokładnie na spawn point
                        score -= 20
                        spawn_candidates.append({
                            'position': neighbor,
                            'score': score,
                            'reason': f"Sąsiad spawnu, wynik: {score:.1f}"
                        })
            except (ValueError, IndexError):
                continue
    
    if not spawn_candidates:
        print(f"[SMART_DEPLOY] Brak dostępnych pozycji do spawnu!")
        return None
    
    # Wybierz najlepszy spawn
    best_spawn = max(spawn_candidates, key=lambda x: x['score'])
    
    print(f"[SMART_DEPLOY] Wybrano spawn: {best_spawn['position']}")
    print(f"[SMART_DEPLOY] Powód: {best_spawn['reason']}")
    
    return best_spawn['position']


def get_my_units(game_engine, player_id):
    """Pobiera jednostki gracza"""
    my_units = []
    all_tokens = getattr(game_engine, 'tokens', [])
    
    for token in all_tokens:
        token_owner = getattr(token, 'owner', '')
        if token_owner == player_id:
            my_units.append({
                'q': getattr(token, 'q', 0),
                'r': getattr(token, 'r', 0),
                'strength': getattr(token, 'current_strength', 1),
                'name': getattr(token, 'name', 'Unknown')
            })
    
    return my_units


def get_all_key_points(game_engine):
    """Pobiera wszystkie punkty kluczowe z mapy"""
    key_points = {}
    map_data = getattr(game_engine, 'map_data', {})
    
    # Sprawdź punkty kluczowe z map_data
    kp_data = map_data.get('key_points', {})
    for hex_id, kp_info in kp_data.items():
        try:
            if ',' in hex_id:
                q, r = map(int, hex_id.split(','))
            else:
                q, r = map(int, hex_id.split('_'))
            key_points[(q, r)] = kp_info
        except (ValueError, IndexError):
            continue
    
    return key_points
