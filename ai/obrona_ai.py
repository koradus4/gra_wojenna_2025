"""Moduł obrony AI wyodrębniony z ai_commander.
Obejmuje ocenę zagrożeń, planowanie odwrotu, koordynację grup defensywnych i pomocnicze funkcje dystansu.
"""
from __future__ import annotations
from typing import Any, Dict, List, Tuple

__all__ = [
    'calculate_hex_distance','get_all_key_points','assess_defensive_threats','plan_defensive_retreat',
    'find_safe_retreat_position','find_safe_fallback_position','evaluate_position_safety',
    'defensive_coordination','plan_group_defense'
]

Position = Tuple[int,int]

def calculate_hex_distance(pos1: Position, pos2: Position) -> int:
    q1, r1 = pos1; q2, r2 = pos2
    return max(abs(q1-q2), abs(r1-r2), abs((q1+r1)-(q2+r2)))

def get_all_key_points(game_engine: Any) -> Dict[Position, Dict]:
    key_points: Dict[Position, Dict] = {}
    map_data = getattr(game_engine, 'map_data', {})
    if 'key_points' in map_data:
        for pos_str, kp_data in map_data['key_points'].items():
            q, r = map(int, pos_str.split(',')); key_points[(q,r)] = kp_data
    if not key_points and hasattr(game_engine, 'key_points_state'):
        kp_state = getattr(game_engine, 'key_points_state', {})
        for pos_str, state_data in kp_state.items():
            q, r = map(int, pos_str.split(','))
            key_points[(q,r)] = {'type': state_data.get('type','unknown'),'value': state_data.get('value',50)}
    return key_points

def assess_defensive_threats(my_units: List[Dict], game_engine: Any) -> Dict[str, Dict]:
    threat_assessment: Dict[str, Dict] = {}
    enemy_positions: List[Dict] = []
    all_tokens = getattr(game_engine, 'tokens', [])
    if hasattr(game_engine, 'board') and hasattr(game_engine.board, 'tokens'):
        all_tokens = game_engine.board.tokens
    current_player_obj = getattr(game_engine, 'current_player_obj', None)
    current_player_id = getattr(current_player_obj, 'id', None)
    current_nation = getattr(current_player_obj, 'nation', 'Unknown')
    expected_owner = f"{current_player_id} ({current_nation})"
    for token in all_tokens:
        token_owner = getattr(token, 'owner', 'NO_OWNER')
        if token_owner != expected_owner and token_owner != 'NO_OWNER':
            # POPRAWKA: Użyj prawdziwych statystyk bojowych zamiast tylko HP
            attack_val = token.stats.get('attack', {}).get('value', 0)
            defense_val = token.stats.get('defense_value', 0)
            combat_strength = max(1, (attack_val + defense_val) // 2)  # Średnia sił bojowych
            enemy_positions.append({'id': getattr(token,'id','unknown'),'pos': (getattr(token,'q',0), getattr(token,'r',0)),'combat': combat_strength})
    key_points = get_all_key_points(game_engine)
    for unit in my_units:
        unit_pos = (unit['q'], unit['r'])
        threatening_enemies = []
        for enemy in enemy_positions:
            distance = calculate_hex_distance(unit_pos, enemy['pos'])
            if distance <= 6:
                threat_score = max(1, enemy['combat'] - distance)
                threatening_enemies.append({'id': enemy['id'],'pos': enemy['pos'],'distance': distance,'threat_score': threat_score})
        threat_level = sum(e['threat_score'] for e in threatening_enemies)
        nearest_safe_point = None; min_distance = float('inf')
        for kp_pos in key_points.keys():
            kp_distance = calculate_hex_distance(unit_pos, kp_pos)
            if kp_distance < min_distance:
                min_distance = kp_distance; nearest_safe_point = kp_pos
        threat_assessment[unit['id']] = {'threat_level': threat_level,'threatening_enemies': threatening_enemies,'nearest_safe_point': nearest_safe_point,'safe_point_distance': min_distance}
        if threat_level > 0:
            print(f"[DEFENSE] {unit['id']}: Threat level {threat_level}, {len(threatening_enemies)} enemies nearby")
    return threat_assessment

def plan_defensive_retreat(threatened_units: List[Dict], threat_assessment: Dict[str,Dict], game_engine: Any) -> Dict[str, Position]:
    retreat_plan: Dict[str, Position] = {}
    for unit in threatened_units:
        unit_id = unit['id']; unit_pos = (unit['q'], unit['r'])
        assessment = threat_assessment.get(unit_id, {})
        safe_point = assessment.get('nearest_safe_point')
        safe_distance = assessment.get('safe_point_distance', float('inf'))
        if safe_distance <= 2:
            retreat_plan[unit_id] = unit_pos
            print(f"[RETREAT] {unit_id}: Zostaje przy punkcie kluczowym {safe_point}")
        elif safe_point:
            retreat_pos = find_safe_retreat_position(unit, safe_point, assessment.get('threatening_enemies', []), game_engine)
            retreat_plan[unit_id] = retreat_pos
            print(f"[RETREAT] {unit_id}: Odwrót do {retreat_pos} (kierunek: {safe_point})")
        else:
            retreat_pos = find_safe_fallback_position(unit, assessment.get('threatening_enemies', []), game_engine)
            retreat_plan[unit_id] = retreat_pos
            print(f"[RETREAT] {unit_id}: Odwrót awaryjny do {retreat_pos}")
    return retreat_plan

def find_safe_retreat_position(unit: Dict, target_point: Position, threatening_enemies: List[Dict], game_engine: Any) -> Position:
    unit_pos = (unit['q'], unit['r']); board = getattr(game_engine, 'board', None)
    if not board: return unit_pos
    max_range = min(unit['mp'], unit['fuel'], 4)
    best_position = unit_pos; best_score = -10**9
    for distance in range(1, max_range+1):
        direction_q = target_point[0] - unit_pos[0]; direction_r = target_point[1] - unit_pos[1]
        if direction_q != 0 or direction_r != 0:
            length = max(abs(direction_q), abs(direction_r), abs(direction_q + direction_r))
            step_q = direction_q // max(length,1) if length>0 else 0
            step_r = direction_r // max(length,1) if length>0 else 0
            candidate_pos = (unit_pos[0] + step_q * distance, unit_pos[1] + step_r * distance)
            if not board.is_occupied(candidate_pos[0], candidate_pos[1]):
                safety_score = evaluate_position_safety(candidate_pos, threatening_enemies, target_point)
                if safety_score > best_score:
                    best_score = safety_score; best_position = candidate_pos
    return best_position

def find_safe_fallback_position(unit: Dict, threatening_enemies: List[Dict], game_engine: Any) -> Position:
    unit_pos = (unit['q'], unit['r']); board = getattr(game_engine, 'board', None)
    if not board: return unit_pos
    max_range = min(unit['mp'], unit['fuel'], 3)
    best_position = unit_pos; best_safety = -10**9
    for q_offset in range(-max_range, max_range+1):
        for r_offset in range(-max_range, max_range+1):
            if abs(q_offset) + abs(r_offset) + abs(q_offset + r_offset) <= max_range * 2:
                candidate_pos = (unit_pos[0] + q_offset, unit_pos[1] + r_offset)
                if not board.is_occupied(candidate_pos[0], candidate_pos[1]):
                    min_enemy_distance = float('inf')
                    for enemy in threatening_enemies:
                        enemy_distance = calculate_hex_distance(candidate_pos, enemy['pos'])
                        min_enemy_distance = min(min_enemy_distance, enemy_distance)
                    if min_enemy_distance > best_safety:
                        best_safety = min_enemy_distance; best_position = candidate_pos
    return best_position

def evaluate_position_safety(position: Position, threatening_enemies: List[Dict], target_point: Position | None = None) -> int:
    safety_score = 0
    for enemy in threatening_enemies:
        enemy_distance = calculate_hex_distance(position, enemy['pos'])
        safety_score += enemy_distance * 10
    if target_point:
        target_distance = calculate_hex_distance(position, target_point)
        safety_score -= target_distance * 5
    return safety_score

def defensive_coordination(my_units: List[Dict], threat_assessment: Dict[str,Dict], game_engine: Any) -> Dict[Position, List[Dict]]:
    key_points = get_all_key_points(game_engine)
    defensive_groups: Dict[Position, List[Dict]] = {}
    for unit in my_units:
        unit_pos = (unit['q'], unit['r']); closest_kp = None; min_distance = float('inf')
        for kp_pos in key_points.keys():
            distance = calculate_hex_distance(unit_pos, kp_pos)
            if distance < min_distance:
                min_distance = distance; closest_kp = kp_pos
        if closest_kp:
            defensive_groups.setdefault(closest_kp, []).append(unit)
    for kp_pos, group in defensive_groups.items():
        if len(group) >= 2:
            plan_group_defense(kp_pos, group, game_engine)
    return defensive_groups

def plan_group_defense(key_point: Position, defending_units: List[Dict], game_engine: Any):
    print(f"[GROUP_DEFENSE] Planowanie obrony punktu {key_point} przez {len(defending_units)} jednostek")
    # Sortuj jednostki obronne po sile bojowej (combat_strength), nie HP
    defending_units.sort(key=lambda u: u.get('combat_strength', 
                                           u.get('attack_val', 0) + u.get('defense_val', 0)), reverse=True)
    board = getattr(game_engine, 'board', None)
    if not board: return {}
    assigned_positions = {}
    if not board.is_occupied(key_point[0], key_point[1]) and defending_units:
        strongest_unit = defending_units[0]
        assigned_positions[strongest_unit['id']] = key_point
        print(f"[GROUP_DEFENSE] {strongest_unit['id']} przydzielony do obrony {key_point}")
    if len(defending_units) > 1:
        neighbors = board.neighbors(key_point[0], key_point[1])
        neighbor_idx = 0
        for unit in defending_units[1:]:
            if neighbor_idx < len(neighbors):
                neighbor_pos = neighbors[neighbor_idx]
                if not board.is_occupied(neighbor_pos[0], neighbor_pos[1]):
                    assigned_positions[unit['id']] = neighbor_pos
                    print(f"[GROUP_DEFENSE] {unit['id']} przydzielony do wsparcia na {neighbor_pos}")
                neighbor_idx += 1
    return assigned_positions
