"""Victory AI System - Uczciwy i adaptacyjny system zdobywania Victory Points.
PHASE 1: Scouting + Threat Assessment ✅ COMPLETE
PHASE 2: Multi-turn Attack Planning 🚧 IN PROGRESS

Implementuje:
- Intelligent scouting (K, Z_Aufkl units) ✅
- Patrol zone assignment (centrum, dalekie KP, bufory) ✅
- Fair enemy detection (tylko widoczni wrogowie!) ✅
- Combat opportunity evaluation z adaptive risk assessment ✅
- Multi-turn attack planning (3-5 tur) 🚧
- Attack phase execution system 🚧
- Plan validation and adaptation 🚧
"""
from __future__ import annotations
from typing import List, Dict, Any, Tuple, Optional
import math

try:
    from main_ai import debug_print
except Exception:
    def debug_print(msg, level="BASIC", category="INFO"):
        print(f"[VICTORY_AI] {msg}")

# CSV Logging dla analizy
import csv
from datetime import datetime

def log_victory_ai_csv(action, player_id, turn, **kwargs):
    """Log Victory AI actions do CSV dla analizy."""
    try:
        import os
        os.makedirs("logs", exist_ok=True)
        
        csv_file = f"logs/victory_ai_phase1_{datetime.now().strftime('%Y%m%d')}.csv"
        file_exists = os.path.exists(csv_file)
        
        with open(csv_file, 'a', newline='', encoding='utf-8') as f:
            writer = csv.writer(f)
            
            if not file_exists:
                # Header
                writer.writerow(['timestamp', 'turn', 'player_id', 'action', 'details'])
            
            # Data
            details = "|".join([f"{k}={v}" for k, v in kwargs.items()])
            writer.writerow([
                datetime.now().strftime('%H:%M:%S'),
                turn,
                player_id,
                action,
                details
            ])
    except Exception as e:
        debug_print(f"CSV LOG ERROR: {e}", "BASIC", "ERROR")

# Logging categories
VICTORY_LOG = "VICTORY"
SCOUT_LOG = "SCOUT"
THREAT_LOG = "THREAT"

def identify_scout_units(my_units: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """Znajdź jednostki zwiadu (K = Kawaleria, Z_Aufkl = rozpoznanie).
    
    Args:
        my_units: Lista wszystkich jednostek gracza
        
    Returns:
        Lista scout units z capabilities metadata
    """
    scouts = []
    total_units = len(my_units)
    
    for unit in my_units:
        if unit.get('mp', 0) <= 0 or unit.get('fuel', 0) <= 0:
            continue  # Skip units bez ruchu
            
        token = unit.get('token')
        if not token or not hasattr(token, 'stats'):
            continue
            
        unit_type = token.stats.get('unitType', '')
        unit_id = unit.get('id', 'UNKNOWN')
        
        # Scout criteria: Kawaleria lub jednostki rozpoznawcze
        is_scout = (
            unit_type == 'K' or  # Kawaleria
            'Aufkl' in unit_id or  # Aufklärungs units  
            'Rozpoznaw' in unit_id  # Polish reconnaissance
        )
        
        if is_scout:
            # Kalkuluj scout capabilities
            max_mp = getattr(token, 'maxMovePoints', unit.get('mp', 0))
            max_fuel = getattr(token, 'maxFuel', unit.get('fuel', 0))
            
            scout_data = {
                'unit': unit,
                'unit_id': unit_id,
                'unit_type': unit_type,
                'position': (unit.get('q', 0), unit.get('r', 0)),
                'mp': unit.get('mp', 0),
                'fuel': unit.get('fuel', 0),
                'max_range': min(max_mp, max_fuel),
                'sight_range': getattr(token, 'sightRange', 3),  # Default sight
                'assigned_patrol_zone': unit.get('assigned_patrol_zone'),  # Previous assignment
                'patrol_turns_active': unit.get('patrol_turns_active', 0)
            }
            scouts.append(scout_data)
    
    debug_print(f"[SCOUT IDENTIFICATION] Znaleziono {len(scouts)} jednostek zwiadu z {total_units} dostępnych", "BASIC", SCOUT_LOG)
    
    # CSV Log
    log_victory_ai_csv("SCOUT_IDENTIFICATION", "UNKNOWN", "UNKNOWN", 
                      total_units=total_units, scouts_found=len(scouts),
                      scout_ids=",".join([s['unit_id'] for s in scouts]))
    
    for scout in scouts:
        debug_print(f"[SCOUT] {scout['unit_id']} ({scout['unit_type']}) na {scout['position']}, zasięg: {scout['max_range']}", "FULL", SCOUT_LOG)
    
    return scouts

def assign_patrol_zones(scouts: List[Dict[str, Any]], game_engine) -> Dict[str, Tuple[int, int]]:
    """Przypisz każdemu scoutowi designated patrol zone.
    
    Args:
        scouts: Lista scout units
        game_engine: Dostęp do board i key points
        
    Returns:
        Dict {scout_id: (target_hex_q, target_hex_r)}
    """
    assignments = {}
    used_zones = set()
    
    board = getattr(game_engine, 'board', None)
    key_points = getattr(game_engine, 'key_points_state', {})
    
    if not board or not key_points:
        debug_print("[PATROL ASSIGNMENT] Brak board lub key_points - fallback assignment", "BASIC", SCOUT_LOG)
        # Fallback: assign centrum mapy
        for i, scout in enumerate(scouts):
            center_variations = [(25, 0), (24, 1), (26, -1), (23, 2), (27, -2)]
            zone = center_variations[i % len(center_variations)]
            assignments[scout['unit_id']] = zone
        return assignments
    
    # PRIORYTET 1: Centrum mapy (25,0) i okolice - główny obszar aktywności
    center_zones = [(25, 0), (24, 1), (26, -1), (25, 1), (25, -1), (23, 0), (27, 0)]
    
    # PRIORYTET 2: Dalekie KP o wysokiej wartości (>70)
    high_value_kps = []
    for hex_id, kp_data in key_points.items():
        if kp_data.get('current_value', 0) > 70:
            try:
                q, r = map(int, hex_id.split(','))
                high_value_kps.append((q, r))
            except:
                continue
    
    # PRIORYTET 3: Strefy buforowe wokół własnych KP (przemień 8 hex)
    buffer_zones = []
    current_player = getattr(game_engine, 'current_player_obj', None)
    my_nation = getattr(current_player, 'nation', '') if current_player else ''
    
    if my_nation:
        all_tokens = getattr(game_engine, 'tokens', [])
        for token in all_tokens[:100]:  # Limit dla performance
            owner = getattr(token, 'owner', '')
            if my_nation in owner:
                token_pos = (getattr(token, 'q', 0), getattr(token, 'r', 0))
                hex_id = f"{token_pos[0]},{token_pos[1]}"
                if hex_id in key_points:
                    # Dodaj buffer zones wokół naszych KP
                    for dq in [-8, -4, 0, 4, 8]:
                        for dr in [-8, -4, 0, 4, 8]:
                            if abs(dq) + abs(dr) <= 8:  # hex distance constraint
                                buffer_pos = (token_pos[0] + dq, token_pos[1] + dr)
                                if board.get_tile(buffer_pos[0], buffer_pos[1]) is not None:
                                    buffer_zones.append(buffer_pos)
    
    # Kombinuj wszystkie priority zones
    all_priority_zones = center_zones + high_value_kps + buffer_zones[:20]  # Limit buffer zones
    
    # Assign zones do scouts (jeden scout per zone)
    for scout in scouts:
        scout_id = scout['unit_id']
        scout_pos = scout['position']
        
        # Check if scout has previous assignment that's still valid
        prev_zone = scout.get('assigned_patrol_zone')
        if prev_zone and prev_zone not in used_zones:
            # Continue previous patrol if not too long
            patrol_turns = scout.get('patrol_turns_active', 0)
            if patrol_turns < 5:  # Max 5 turns per zone
                assignments[scout_id] = prev_zone
                used_zones.add(prev_zone)
                debug_print(f"[PATROL CONTINUE] {scout_id} kontynuuje patrol {prev_zone} (tura {patrol_turns + 1})", "FULL", SCOUT_LOG)
                continue
        
        # Find best available zone
        best_zone = None
        best_distance = float('inf')
        
        for zone in all_priority_zones:
            if zone in used_zones:
                continue
                
            # Sprawdź czy zone jest dostępna (valid hex)
            if board.get_tile(zone[0], zone[1]) is None:
                continue
                
            # Kalkuluj dystans od scout do zone
            try:
                distance = board.hex_distance(scout_pos, zone)
                if distance < best_distance:
                    best_distance = distance
                    best_zone = zone
            except:
                continue
        
        if best_zone:
            assignments[scout_id] = best_zone
            used_zones.add(best_zone)
            debug_print(f"[PATROL ASSIGN] {scout_id} → zona {best_zone} (dystans: {best_distance})", "BASIC", SCOUT_LOG)
        else:
            # Fallback: centrum mapy
            fallback_zone = (25, 0)
            assignments[scout_id] = fallback_zone
            debug_print(f"[PATROL FALLBACK] {scout_id} → centrum {fallback_zone} (brak wolnych stref)", "BASIC", SCOUT_LOG)
    
    debug_print(f"[PATROL SUMMARY] Przypisano {len(assignments)} patrol zones", "BASIC", SCOUT_LOG)
    
    # CSV Log patrol assignments
    log_victory_ai_csv("PATROL_ASSIGNMENT", "UNKNOWN", "UNKNOWN",
                      scouts_count=len(scouts), assignments_made=len(assignments),
                      center_zones=len(center_zones), high_value_kps=len(high_value_kps),
                      buffer_zones_available=len(buffer_zones))
    
    return assignments

def execute_intelligent_patrol(scout: Dict[str, Any], patrol_zone: Tuple[int, int], game_engine) -> bool:
    """Wykonaj patrol w assigned zone (nie krążenie bez celu!).
    
    Args:
        scout: Scout unit data
        patrol_zone: Target (q, r) coordinates  
        game_engine: Dostęp do movement systems
        
    Returns:
        True jeśli ruch wykonany, False jeśli blocked
    """
    board = getattr(game_engine, 'board', None)
    if not board:
        return False
        
    scout_pos = scout['position']
    unit = scout['unit']
    unit_id = scout['unit_id']
    
    try:
        # Kalkuluj dystans do patrol zone
        distance_to_zone = board.hex_distance(scout_pos, patrol_zone)
        
        # LOGIKA 1: Jeśli daleko od zone, idź w jej kierunku
        if distance_to_zone > 3:
            debug_print(f"[PATROL MOVE] {unit_id} ruszam do zony {patrol_zone} (dystans: {distance_to_zone})", "FULL", SCOUT_LOG)
            target = patrol_zone
            
        # LOGIKA 2: Jeśli w zone, wykonaj local patrol
        else:
            # Random patrol w promieniu 2-3 hex (obszar coverage)
            import random
            patrol_offsets = [
                (-2, 0), (2, 0), (0, -2), (0, 2),
                (-1, -1), (1, 1), (-1, 1), (1, -1),
                (-3, 0), (3, 0), (0, -3), (0, 3)
            ]
            
            # Wybierz valid patrol point
            valid_targets = []
            for dq, dr in patrol_offsets:
                candidate = (patrol_zone[0] + dq, patrol_zone[1] + dr)
                if board.get_tile(candidate[0], candidate[1]) is not None:
                    valid_targets.append(candidate)
            
            if valid_targets:
                target = random.choice(valid_targets)
                debug_print(f"[PATROL LOCAL] {unit_id} patrol lokalny w zonie, cel: {target}", "FULL", SCOUT_LOG)
            else:
                target = patrol_zone  # Fallback
                debug_print(f"[PATROL STAY] {unit_id} pozostaje w centrum zony {patrol_zone}", "FULL", SCOUT_LOG)
        
        # WYKONAJ RUCH z optimal movement mode (recon dla sight)
        token = unit.get('token')
        if token and hasattr(token, 'movement_mode'):
            # Set recon mode dla zwiększonego sight range
            if hasattr(token, 'apply_movement_mode'):
                token.movement_mode = 'recon'
                token.apply_movement_mode()
                unit['mp'] = getattr(token, 'currentMovePoints', unit.get('mp', 0))
                debug_print(f"[PATROL MODE] {unit_id} ustawiono tryb recon dla zwiększonego sight", "FULL", SCOUT_LOG)
        
        # Deleguj do existing movement system
        try:
            from ai.ruch_jednostek import move_towards
            success = move_towards(unit, target, game_engine)
            
            if success:
                # Update patrol metadata
                unit['assigned_patrol_zone'] = patrol_zone
                unit['patrol_turns_active'] = unit.get('patrol_turns_active', 0) + 1
                debug_print(f"[PATROL SUCCESS] {unit_id} wykonał patrol do {target}", "BASIC", SCOUT_LOG)
                return True
            else:
                debug_print(f"[PATROL BLOCKED] {unit_id} nie może ruszyć do {target}", "BASIC", SCOUT_LOG)
                return False
                
        except Exception as e:
            debug_print(f"[PATROL ERROR] {unit_id} błąd ruchu: {e}", "BASIC", SCOUT_LOG)
            return False
            
    except Exception as e:
        debug_print(f"[PATROL CRITICAL] {unit_id} krytyczny błąd patrol: {e}", "BASIC", SCOUT_LOG)
        return False

def scan_visible_enemies(my_units: List[Dict[str, Any]], game_engine) -> List[Dict[str, Any]]:
    """Zbierz dane o wszystkich widocznych wrogach (UCZCIWIE!).
    
    Args:
        my_units: Moje jednostki (dla vision calculation)
        game_engine: Dostęp do all tokens
        
    Returns:
        Lista wrogich units z metadata
    """
    visible_enemies = []
    
    all_tokens = getattr(game_engine, 'tokens', [])
    current_player = getattr(game_engine, 'current_player_obj', None)
    my_nation = getattr(current_player, 'nation', '') if current_player else ''
    
    if not my_nation:
        debug_print("[ENEMY SCAN] Brak identyfikacji własnej nacji", "BASIC", THREAT_LOG)
        return visible_enemies
    
    # Zbierz pozycje moich jednostek dla vision calculation
    my_positions = []
    for unit in my_units:
        pos = (unit.get('q', 0), unit.get('r', 0))
        token = unit.get('token')
        sight_range = getattr(token, 'sightRange', 3) if token else 3
        my_positions.append((pos, sight_range))
    
    debug_print(f"[ENEMY SCAN] Skanowanie z {len(my_positions)} pozycji obserwacyjnych", "FULL", THREAT_LOG)
    
    # Sprawdź każdy token pod kątem visibility
    board = getattr(game_engine, 'board', None)
    
    for token in all_tokens[:200]:  # Performance limit
        owner = getattr(token, 'owner', '')
        if not owner or my_nation in owner:
            continue  # Skip own units
            
        enemy_pos = (getattr(token, 'q', 0), getattr(token, 'r', 0))
        
        # UCZCIWY CHECK: Czy enemy jest widoczny z którejś mojej pozycji?
        is_visible = False
        for my_pos, sight_range in my_positions:
            try:
                if board:
                    distance = board.hex_distance(my_pos, enemy_pos)
                    if distance <= sight_range:
                        is_visible = True
                        break
                else:
                    # Fallback: simple distance
                    dx = abs(my_pos[0] - enemy_pos[0])
                    dy = abs(my_pos[1] - enemy_pos[1])
                    if dx + dy <= sight_range * 2:  # Approximate hex distance
                        is_visible = True
                        break
            except:
                continue
        
        if is_visible:
            # Zbierz enemy metadata
            unit_type = getattr(token, 'stats', {}).get('unitType', 'UNKNOWN') if hasattr(token, 'stats') else 'UNKNOWN'
            combat_value = getattr(token, 'combat_value', 0)
            max_mp = getattr(token, 'maxMovePoints', 0)
            
            enemy_data = {
                'token': token,
                'unit_id': getattr(token, 'id', 'UNKNOWN'),
                'owner': owner,
                'position': enemy_pos,
                'unit_type': unit_type,
                'combat_value': combat_value,
                'estimated_mp': max_mp,  # Conservative estimate
                'detection_turn': getattr(game_engine, 'current_turn', 1),
                'threat_level': 'UNKNOWN'  # Will be calculated later
            }
            
            visible_enemies.append(enemy_data)
    
    debug_print(f"[ENEMY SCAN] Wykryto {len(visible_enemies)} wrogich jednostek", "BASIC", THREAT_LOG)
    
    # CSV Log enemy detection
    log_victory_ai_csv("ENEMY_DETECTION", "UNKNOWN", "UNKNOWN",
                      vision_positions=len(my_positions), total_tokens_checked=min(len(all_tokens), 200),
                      enemies_detected=len(visible_enemies),
                      enemy_nations=",".join(set(e['owner'].split('_')[0] for e in visible_enemies if '_' in e['owner'])))
    
    for enemy in visible_enemies[:5]:  # Log first 5
        debug_print(f"[ENEMY DETECTED] {enemy['unit_id']} ({enemy['unit_type']}) na {enemy['position']}, HP: {enemy.get('combat_value', 'N/A')}, Combat: {enemy.get('combat_strength', 'N/A')}", "FULL", THREAT_LOG)
    
    return visible_enemies

def cluster_enemies(enemies: List[Dict[str, Any]], cluster_radius: int = 5) -> List[List[Dict[str, Any]]]:
    """Grupuj wrogów w klastry (promień 5 hex = jeden cluster).
    
    Args:
        enemies: Lista detected enemies
        cluster_radius: Max distance for clustering
        
    Returns:
        Lista clusterów (każdy cluster to lista enemies)
    """
    if not enemies:
        return []
    
    clusters = []
    unassigned = enemies.copy()
    
    while unassigned:
        # Start new cluster with first unassigned enemy
        cluster_seed = unassigned.pop(0)
        current_cluster = [cluster_seed]
        
        # Find all enemies within cluster_radius
        remaining = []
        for enemy in unassigned:
            # Simple distance calculation (hex distance approximation)
            seed_pos = cluster_seed['position']
            enemy_pos = enemy['position']
            
            dx = abs(seed_pos[0] - enemy_pos[0])
            dy = abs(seed_pos[1] - enemy_pos[1])
            distance = max(dx, dy)  # Hex distance approximation
            
            if distance <= cluster_radius:
                current_cluster.append(enemy)
            else:
                remaining.append(enemy)
        
        clusters.append(current_cluster)
        unassigned = remaining
    
    debug_print(f"[ENEMY CLUSTERING] {len(enemies)} wrogów → {len(clusters)} clusterów", "BASIC", THREAT_LOG)
    for i, cluster in enumerate(clusters):
        total_combat_strength = sum(e.get('combat_strength', 
                                        e.get('attack_val', 0) + e.get('defense_val', 0)) for e in cluster)
        total_hp = sum(e.get('combat_value', 0) for e in cluster)  # HP dla info
        center_pos = cluster[0]['position'] if cluster else (0, 0)
        debug_print(f"[CLUSTER {i+1}] {len(cluster)} jednostek przy {center_pos}, siła: {total_combat_strength}, HP: {total_hp}", "FULL", THREAT_LOG)
    
    return clusters

def evaluate_combat_opportunity(enemy_cluster: List[Dict[str, Any]], my_available_forces: List[Dict[str, Any]], 
                               current_vp_situation: str = "TIED") -> Dict[str, Any]:
    """Oceń czy warto atakować dany cluster wrogów.
    
    Args:
        enemy_cluster: Cluster wrogów do oceny
        my_available_forces: Dostępne siły (nie wszystkie!)
        current_vp_situation: "WINNING"/"LOSING"/"TIED" dla adaptive assessment
        
    Returns:
        Combat assessment z decision recommendation
    """
    if not enemy_cluster or not my_available_forces:
        return {
            'recommendation': 'NO_ATTACK',
            'reason': 'Brak danych do oceny',
            'confidence': 0.0,
            'force_ratio': 0.0,
            'required_ratio': 0.0,
            'my_total_cv': 0,
            'enemy_total_cv': 0,
            'vp_potential': 0,
            'estimated_cost': 0
        }
    
    try:
        # Kalkuluj force ratios z bezpieczną obsługą błędów
        enemy_total_cv = 0
        for e in enemy_cluster:
            # Bezpieczne pobieranie combat_value
            cv = 0
            if hasattr(e, 'combat_value'):
                cv = getattr(e, 'combat_value', 0)
            elif isinstance(e, dict):
                cv = e.get('combat_value', 0)
                # Jeśli nie ma bezpośrednio, spróbuj z token
                if cv == 0 and 'token' in e:
                    token = e['token']
                    if hasattr(token, 'combat_value'):
                        cv = getattr(token, 'combat_value', 0)
            enemy_total_cv += cv
        
        my_total_cv = 0
        for u in my_available_forces:
            cv = 0
            if hasattr(u, 'combat_value'):
                cv = getattr(u, 'combat_value', 0)
            elif isinstance(u, dict):
                cv = u.get('combat_value', 0)
                # Jeśli nie ma bezpośrednio, spróbuj z token
                if cv == 0 and 'token' in u:
                    token = u['token']
                    if hasattr(token, 'combat_value'):
                        cv = getattr(token, 'combat_value', 0)
            my_total_cv += cv
        
        # ADAPTIVE force ratio requirements - ZMNIEJSZONE dla więcej opportunities
        if current_vp_situation == "LOSING":
            required_ratio = 1.1  # Bardzo agresywne gdy przegrywamy
            risk_tolerance = "HIGH"
        elif current_vp_situation == "WINNING": 
            required_ratio = 1.4  # Zachowawcze gdy wygrywamy
            risk_tolerance = "LOW"
        else:  # TIED
            required_ratio = 1.2  # Umiarkowanie agresywne - OBNIŻONE z 1.5
            risk_tolerance = "MEDIUM"
        
        # Bezpieczne dzielenie
        if enemy_total_cv <= 0:
            force_ratio = 999.0  # Przytłaczająca przewaga
        else:
            force_ratio = my_total_cv / enemy_total_cv
    
    except Exception as e:
        # Log błędy szczegółowo
        debug_print(f"[COMBAT ASSESSMENT ERROR] {e}", "BASIC", "ERROR")
        log_victory_ai_csv("PHASE1_ERROR", "UNKNOWN", "UNKNOWN", error=f"force_ratio: {e}")
        return {
            'recommendation': 'ERROR',
            'reason': f'Error in combat assessment: {e}',
            'confidence': 0.0,
            'force_ratio': 0.0,
            'required_ratio': 0.0,
            'my_total_cv': 0,
            'enemy_total_cv': 0,
            'vp_potential': 0,
            'estimated_cost': 0
        }
    
    # Estimate VP potential
    vp_potential = calculate_vp_potential(enemy_cluster, None)  # Placeholder for now
    
    # Simple cost estimation (movement + combat losses)
    estimated_pe_cost = len(my_available_forces) * 2  # Rough estimate
    
    # Decision logic - ZMIĘKCZONE kryteria
    if force_ratio >= required_ratio:
        if vp_potential > estimated_pe_cost * 0.3:  # OBNIŻONE z 0.5 - łatwiejsze VP/PE efficiency
            recommendation = 'ATTACK'
            confidence = min(force_ratio / required_ratio, 2.0)  # Cap at 2.0
        else:
            recommendation = 'MONITOR'
            confidence = 0.5
    elif force_ratio >= (required_ratio * 0.8):  # NOWE: "marginal opportunities"
        recommendation = 'CONSIDER'  # Nowa kategoria - niemal wystarczające siły
        confidence = 0.4
    else:
        recommendation = 'AVOID'
        confidence = 1.0 - (force_ratio / required_ratio)
    
    assessment = {
        'recommendation': recommendation,
        'reason': f"Force ratio: {force_ratio:.2f} vs required {required_ratio:.2f}",
        'confidence': confidence,
        'force_ratio': force_ratio,
        'required_ratio': required_ratio,
        'my_total_cv': my_total_cv,
        'enemy_total_cv': enemy_total_cv,
        'vp_potential': vp_potential,
        'estimated_cost': estimated_pe_cost,
        'risk_tolerance': risk_tolerance,
        'cluster_size': len(enemy_cluster),
        'available_forces': len(my_available_forces)
    }
    
    debug_print(f"[COMBAT ASSESSMENT] {recommendation} - Ratio: {force_ratio:.2f}/{required_ratio:.2f}, "
               f"VP: {vp_potential}, Cost: {estimated_pe_cost}, Confidence: {confidence:.2f}", "BASIC", THREAT_LOG)
    
    # CSV Log combat assessment
    log_victory_ai_csv("COMBAT_ASSESSMENT", "UNKNOWN", "UNKNOWN",
                      recommendation=recommendation, force_ratio=f"{force_ratio:.2f}",
                      required_ratio=f"{required_ratio:.2f}", my_cv=my_total_cv, 
                      enemy_cv=enemy_total_cv, vp_potential=vp_potential,
                      confidence=f"{confidence:.2f}",
                      cluster_size=len(enemy_cluster), available_forces=len(my_available_forces))
    
    return assessment

def calculate_vp_potential(target_list: List[Dict[str, Any]], game_engine) -> int:
    """Oszacuj potencjalne VP z niszczenia danych celów.
    
    Args:
        target_list: Lista target units
        game_engine: Dla VP rules (currently placeholder)
        
    Returns:
        Estimated VP gain
    """
    if not target_list:
        return 0
    
    # PLACEHOLDER - będzie rozwinięte z proper VP rules
    total_vp = 0
    
    for target in target_list:
        unit_type = target.get('unit_type', 'UNKNOWN')
        combat_value = target.get('combat_value', 0)  # HP
        combat_strength = target.get('combat_strength', 
                                   target.get('attack_val', 0) + target.get('defense_val', 0))
        
        # Simple VP estimation based on unit type and strength
        if unit_type == 'G':  # Generał
            vp_value = 10
        elif unit_type in ['TL', 'TS']:  # Tanks
            vp_value = 3
        elif unit_type in ['P', 'K']:  # Infantry, Cavalry
            vp_value = 2
        elif unit_type in ['AL', 'AC']:  # Artillery
            vp_value = 4
        else:
            vp_value = 1  # Default
        
        # Bonus dla stronger units based on combat strength, not HP
        if combat_strength > 10:
            vp_value += 1
        
        total_vp += vp_value
    
    debug_print(f"[VP CALCULATION] {len(target_list)} celów = szacowane {total_vp} VP", "FULL", THREAT_LOG)
    return total_vp

# MAIN CONTROLLER FUNCTION - PHASE 1
def victory_ai_phase1_controller(game_engine, my_units: List[Dict[str, Any]], player_id: int) -> Dict[str, Any]:
    """Phase 1 controller: Scouting + Threat Assessment.
    
    Args:
        game_engine: Standard game engine
        my_units: Lista wszystkich jednostek gracza
        player_id: ID gracza
        
    Returns:
        Action summary report
    """
    debug_print(f"[VICTORY AI] PHASE 1 START - Player {player_id}", "BASIC", VICTORY_LOG)
    
    # Pobierz current turn z game_engine
    current_turn = getattr(game_engine, 'current_turn', 1)
    
    report = {
        'phase': 'SCOUTING_AND_THREAT_ASSESSMENT',
        'scouts_deployed': 0,
        'enemies_detected': 0,
        'combat_opportunities': 0,
        'recommended_actions': [],
        'patrol_assignments': {},
        'threat_clusters': []
    }
    
    try:
        # STEP 1: Identify and deploy scouts
        scouts = identify_scout_units(my_units)
        if scouts:
            patrol_assignments = assign_patrol_zones(scouts, game_engine)
            report['patrol_assignments'] = patrol_assignments
            
            # Execute patrol movements
            scouts_moved = 0
            for scout in scouts:
                scout_id = scout['unit_id']
                if scout_id in patrol_assignments:
                    patrol_zone = patrol_assignments[scout_id]
                    if execute_intelligent_patrol(scout, patrol_zone, game_engine):
                        scouts_moved += 1
                        # CSV Log successful scout movement
                        log_victory_ai_csv("SCOUT_MOVEMENT", player_id, current_turn,
                                         scout_id=scout_id, from_pos=f"{scout['position'][0]},{scout['position'][1]}",
                                         to_zone=f"{patrol_zone[0]},{patrol_zone[1]}", success=True)
                    else:
                        # CSV Log failed scout movement
                        log_victory_ai_csv("SCOUT_MOVEMENT", player_id, current_turn,
                                         scout_id=scout_id, from_pos=f"{scout['position'][0]},{scout['position'][1]}",
                                         to_zone=f"{patrol_zone[0]},{patrol_zone[1]}", success=False)
            
            report['scouts_deployed'] = scouts_moved
            debug_print(f"[VICTORY AI] Wysłano {scouts_moved}/{len(scouts)} scouts na patrol", "BASIC", VICTORY_LOG)
        
        # STEP 2: Scan for visible enemies
        visible_enemies = scan_visible_enemies(my_units, game_engine)
        report['enemies_detected'] = len(visible_enemies)
        
        if visible_enemies:
            # STEP 3: Cluster enemies and assess threats
            enemy_clusters = cluster_enemies(visible_enemies)
            report['threat_clusters'] = enemy_clusters
            
            # STEP 4: Evaluate combat opportunities
            current_vp_status = "TIED"  # Placeholder - will be determined from game state
            
            combat_opportunities = 0
            for i, cluster in enumerate(enemy_clusters):
                # Use subset of forces for assessment (not all units)
                combat_units = [u for u in my_units if u.get('mp', 0) > 0 and 
                               not u.get('moved_capture', False)][:8]  # Limit to 8 units max
                
                assessment = evaluate_combat_opportunity(cluster, combat_units, current_vp_status)
                
                # CSV Log each cluster assessment
                cluster_center = cluster[0]['position'] if cluster else (0, 0)
                log_victory_ai_csv("CLUSTER_ASSESSMENT", player_id, current_turn,
                                 cluster_id=i, cluster_size=len(cluster),
                                 cluster_center=f"{cluster_center[0]},{cluster_center[1]}",
                                 recommendation=assessment['recommendation'],
                                 force_ratio=f"{assessment['force_ratio']:.2f}",
                                 confidence=f"{assessment['confidence']:.2f}")
                
                if assessment['recommendation'] == 'ATTACK':
                    combat_opportunities += 1
                    report['recommended_actions'].append({
                        'action': 'PLAN_ATTACK',
                        'target_cluster': i,
                        'confidence': assessment['confidence'],
                        'force_ratio': assessment['force_ratio']
                    })
                    debug_print(f"[VICTORY AI] Opportunity: Atak na cluster {i}, confidence: {assessment['confidence']:.2f}", "BASIC", VICTORY_LOG)
            
            report['combat_opportunities'] = combat_opportunities
        
        # Final summary CSV log
        log_victory_ai_csv("PHASE1_SUMMARY", player_id, current_turn,
                          total_units=len(my_units), scouts_identified=len(scouts) if scouts else 0,
                          scouts_deployed=report['scouts_deployed'], enemies_detected=report['enemies_detected'],
                          combat_opportunities=report['combat_opportunities'],
                          threat_clusters=len(report['threat_clusters']))
        
        debug_print(f"[VICTORY AI] PHASE 1 COMPLETE - {report['scouts_deployed']} scouts, "
                   f"{report['enemies_detected']} enemies, {report['combat_opportunities']} opportunities", "BASIC", VICTORY_LOG)
        
    except Exception as e:
        debug_print(f"[VICTORY AI] PHASE 1 ERROR: {e}", "BASIC", VICTORY_LOG)
        log_victory_ai_csv("PHASE1_ERROR", player_id, current_turn, error=str(e))
        report['error'] = str(e)
    
    return report

# Integration hook dla existing AI pipeline
def integrate_victory_ai_phase1(game_engine, my_units: List[Dict[str, Any]], player_id: int) -> Dict[str, Any]:
    """Integration point dla existing AI systems.
    
    Wywołaj to w ai_commander.py przed standard tactical operations.
    """
    return victory_ai_phase1_controller(game_engine, my_units, player_id)

# ===== PHASE 5 VP INTELLIGENCE INTEGRATION =====

def integrate_vp_intelligence_system(game_engine, my_units: List[Dict[str, Any]], player_id: int) -> Dict[str, Any]:
    """Integrates VP Intelligence System with existing Victory AI.
    
    Args:
        game_engine: Standard game engine with VP data access
        my_units: Lista wszystkich jednostek gracza
        player_id: ID gracza
        
    Returns:
        VP strategic assessment with recommendations
    """
    try:
        # Import VP Intelligence System
        from ai.vp_intelligence import VPIntelligenceSystem
        
        # Get current player info
        current_player = getattr(game_engine, 'current_player_obj', None)
        nation = getattr(current_player, 'nation', 'Unknown') if current_player else 'Unknown'
        current_turn = getattr(game_engine, 'current_turn', 1)
        
        # Initialize VP system with game engine
        vp_system = VPIntelligenceSystem(game_engine, nation)
        
        # Perform comprehensive VP analysis
        vp_analysis = vp_system.analyze_vp_situation(current_turn)
        
        if vp_analysis:
            debug_print(f"[VP INTELLIGENCE] Status: {vp_analysis.get('current_status', 'UNKNOWN')}, "
                       f"Trend: {vp_analysis.get('trend_direction', 'STABLE')}, "
                       f"Opportunities: {len(vp_analysis.get('opportunities', []))}", "BASIC", VICTORY_LOG)
            
            # CSV Log VP intelligence integration
            log_victory_ai_csv("VP_INTELLIGENCE", player_id, getattr(game_engine, 'current_turn', 1),
                             vp_status=vp_analysis.get('current_status', 'UNKNOWN'),
                             trend_direction=vp_analysis.get('trend_direction', 'STABLE'),
                             threat_level=vp_analysis.get('primary_threat_level', 'LOW'),
                             opportunities_count=len(vp_analysis.get('opportunities', [])),
                             recommendations_count=len(vp_analysis.get('strategic_recommendations', [])))
            
            return vp_analysis
        else:
            debug_print("[VP INTELLIGENCE] No analysis data available", "BASIC", VICTORY_LOG)
            return {}
            
    except ImportError as e:
        debug_print(f"[VP INTELLIGENCE] Import error: {e}", "BASIC", "ERROR")
        return {}
    except Exception as e:
        debug_print(f"[VP INTELLIGENCE] Error: {e}", "BASIC", "ERROR")
        log_victory_ai_csv("VP_INTELLIGENCE_ERROR", player_id, getattr(game_engine, 'current_turn', 1), error=str(e))
        return {}


# ===== PHASE 2: MULTI-TURN ATTACK PLANNING =====

# Persistent attack plan storage
ATTACK_PLAN_CACHE = {}

def create_attack_plan(target_cluster: List[Dict[str, Any]], available_forces: List[Dict[str, Any]], 
                      game_engine, player_id: int, current_turn: int) -> Dict[str, Any]:
    """Stwórz stabilny plan ataku na 3-5 tur.
    
    Args:
        target_cluster: Cluster wrogów do ataku
        available_forces: Siły dostępne do ataku
        game_engine: Game engine dla board access
        player_id: ID gracza
        current_turn: Aktualny numer tury
        
    Returns:
        Detailed attack plan z fazami
    """
    import uuid
    import time
    
    plan_id = str(uuid.uuid4())[:8]  # Krótki unique ID
    
    if not target_cluster or not available_forces:
        debug_print("[ATTACK PLANNING] Brak danych do stworzenia planu", "BASIC", "PLANNING")
        return {'plan_id': plan_id, 'status': 'INVALID', 'reason': 'No targets or forces'}
    
    # Określ target cluster center
    cluster_positions = [enemy.get('position', (0, 0)) for enemy in target_cluster]
    if cluster_positions:
        center_q = sum(pos[0] for pos in cluster_positions) // len(cluster_positions)
        center_r = sum(pos[1] for pos in cluster_positions) // len(cluster_positions)
        target_center = (center_q, center_r)
    else:
        target_center = (25, 0)  # Default centrum mapy
    
    # Kalkuluj assembly area (2-3 hex od target center)
    assembly_area = (target_center[0] - 3, target_center[1] - 2)
    
    # 5-fazowy plan ataku
    attack_plan = {
        'plan_id': plan_id,
        'player_id': player_id,
        'created_turn': current_turn,
        'status': 'PLANNING',
        'target_cluster': target_cluster,
        'target_center': target_center,
        'assembly_area': assembly_area,
        'assigned_forces': available_forces[:8],  # Maksymalnie 8 jednostek
        'current_phase': 'POSITIONING',
        'phases': {
            'POSITIONING': {
                'turn_range': (current_turn + 1, current_turn + 1),
                'objective': 'Move units toward assembly area',
                'status': 'PENDING'
            },
            'CONCENTRATION': {
                'turn_range': (current_turn + 2, current_turn + 2),
                'objective': 'Concentrate forces, final scouting',
                'status': 'PENDING'
            },
            'ATTACK': {
                'turn_range': (current_turn + 3, current_turn + 3),
                'objective': 'Execute coordinated attack',
                'status': 'PENDING'
            },
            'EXPLOITATION': {
                'turn_range': (current_turn + 4, current_turn + 5),
                'objective': 'Pursue enemies or secure gains',
                'status': 'PENDING'
            }
        },
        'contingencies': {
            'enemy_retreat': 'PURSUE',
            'heavy_losses': 'WITHDRAW',
            'new_threat': 'REASSESS'
        },
        'success_metrics': {
            'min_enemies_destroyed': len(target_cluster) // 2,
            'max_acceptable_losses': len(available_forces) // 3,
            'min_vp_gain': len(target_cluster) * 2
        }
    }
    
    # Zapisz plan w cache
    ATTACK_PLAN_CACHE[plan_id] = attack_plan
    
    # CSV Log plan creation
    log_victory_ai_csv("ATTACK_PLAN_CREATED", player_id, current_turn,
                      plan_id=plan_id, target_center=f"{target_center[0]},{target_center[1]}",
                      assigned_forces=len(available_forces), target_cluster_size=len(target_cluster),
                      estimated_duration="4-5_turns")
    
    debug_print(f"[ATTACK PLANNING] Created plan {plan_id} for cluster at {target_center}, "
               f"{len(available_forces)} forces assigned", "BASIC", "PLANNING")
    
    return attack_plan


def execute_attack_phase(plan_id: str, current_turn: int, game_engine, my_units: List[Dict[str, Any]], 
                        player_id: int) -> str:
    """Wykonaj odpowiednią fazę ataku według planu.
    
    Args:
        plan_id: ID planu do wykonania
        current_turn: Aktualny numer tury
        game_engine: Game engine
        my_units: Aktualne jednostki gracza
        player_id: ID gracza
        
    Returns:
        Status execution ("POSITIONING", "ATTACKING", "COMPLETED", "ABORTED")
    """
    if plan_id not in ATTACK_PLAN_CACHE:
        debug_print(f"[ATTACK EXECUTION] Plan {plan_id} not found in cache", "BASIC", "PLANNING")
        return "ABORTED"
    
    plan = ATTACK_PLAN_CACHE[plan_id]
    
    # Validate plan continuation
    if not validate_plan_continuation(plan, my_units, game_engine):
        plan['status'] = 'ABORTED'
        log_victory_ai_csv("ATTACK_PLAN_ABORTED", player_id, current_turn,
                          plan_id=plan_id, reason="validation_failed")
        debug_print(f"[ATTACK EXECUTION] Plan {plan_id} aborted - validation failed", "BASIC", "PLANNING")
        return "ABORTED"
    
    # Determine current phase
    current_phase = None
    for phase_name, phase_data in plan['phases'].items():
        turn_start, turn_end = phase_data['turn_range']
        if turn_start <= current_turn <= turn_end and phase_data['status'] == 'PENDING':
            current_phase = phase_name
            break
    
    if not current_phase:
        # Plan completed or no active phase
        plan['status'] = 'COMPLETED'
        debug_print(f"[ATTACK EXECUTION] Plan {plan_id} completed", "BASIC", "PLANNING")
        return "COMPLETED"
    
    # Execute specific phase
    execution_result = None
    
    if current_phase == 'POSITIONING':
        execution_result = execute_positioning_phase(plan, my_units, game_engine)
    elif current_phase == 'CONCENTRATION':
        execution_result = execute_concentration_phase(plan, my_units, game_engine)
    elif current_phase == 'ATTACK':
        execution_result = execute_attack_phase_action(plan, my_units, game_engine)
    elif current_phase == 'EXPLOITATION':
        execution_result = execute_exploitation_phase(plan, my_units, game_engine)
    
    # Update phase status
    if execution_result:
        plan['phases'][current_phase]['status'] = 'COMPLETED'
        plan['current_phase'] = current_phase
        
        # CSV Log phase completion
        log_victory_ai_csv("ATTACK_PHASE_COMPLETED", player_id, current_turn,
                          plan_id=plan_id, phase=current_phase, result=execution_result)
        
        debug_print(f"[ATTACK EXECUTION] Phase {current_phase} completed for plan {plan_id}: {execution_result}", 
                   "BASIC", "PLANNING")
    
    return current_phase


def validate_plan_continuation(plan: Dict[str, Any], my_units: List[Dict[str, Any]], game_engine) -> bool:
    """Sprawdź czy plan nadal ma sens (czy kontynuować?).
    
    Args:
        plan: Attack plan do walidacji
        my_units: Aktualne jednostki gracza
        game_engine: Game engine dla battlefield state
        
    Returns:
        True = kontynuuj, False = abort plan
    """
    try:
        # Check 1: Czy nasze siły nadal istnieją?
        assigned_force_ids = [u.get('unit_id', '') for u in plan.get('assigned_forces', [])]
        current_force_ids = [u.get('unit_id', '') for u in my_units]
        
        surviving_forces = [f_id for f_id in assigned_force_ids if f_id in current_force_ids]
        
        if len(surviving_forces) < len(assigned_force_ids) * 0.6:  # 40%+ strat = abort
            debug_print(f"[PLAN VALIDATION] Too many losses: {len(surviving_forces)}/{len(assigned_force_ids)}", 
                       "BASIC", "PLANNING")
            return False
        
        # Check 2: Czy target cluster nadal istnieje?
        target_center = plan['target_center']
        visible_enemies = scan_visible_enemies(my_units, game_engine)
        
        enemies_near_target = []
        for enemy in visible_enemies:
            enemy_pos = enemy.get('position', (0, 0))
            distance = abs(enemy_pos[0] - target_center[0]) + abs(enemy_pos[1] - target_center[1])
            if distance <= 5:  # W obrębie 5 hex od original target
                enemies_near_target.append(enemy)
        
        if len(enemies_near_target) < len(plan['target_cluster']) * 0.3:  # 70%+ wrogów zniknęło
            debug_print(f"[PLAN VALIDATION] Target cluster dispersed: {len(enemies_near_target)} enemies remain", 
                       "BASIC", "PLANNING")
            return False
        
        # Check 3: Force ratio validation - nadal mamy szanse?
        assessment = evaluate_combat_opportunity(enemies_near_target, 
                                               [u for u in my_units if u.get('unit_id') in surviving_forces])
        
        if assessment['recommendation'] == 'AVOID':
            debug_print(f"[PLAN VALIDATION] Force ratio too poor: {assessment['force_ratio']:.2f}", 
                       "BASIC", "PLANNING")
            return False
        
        debug_print(f"[PLAN VALIDATION] Plan {plan['plan_id']} validated successfully", "BASIC", "PLANNING")
        return True
        
    except Exception as e:
        debug_print(f"[PLAN VALIDATION] Error during validation: {e}", "BASIC", "ERROR")
        return False


# ===== PHASE EXECUTION FUNCTIONS =====

def execute_positioning_phase(plan: Dict[str, Any], my_units: List[Dict[str, Any]], game_engine) -> str:
    """Execute positioning phase - move units toward assembly area."""
    assembly_area = plan['assembly_area']
    assigned_force_ids = [u.get('unit_id', '') for u in plan.get('assigned_forces', [])]
    
    units_moved = 0
    for unit in my_units:
        if unit.get('unit_id') in assigned_force_ids and unit.get('mp', 0) > 0:
            current_pos = unit.get('position', (0, 0))
            distance_to_assembly = abs(current_pos[0] - assembly_area[0]) + abs(current_pos[1] - assembly_area[1])
            
            if distance_to_assembly > 2:  # Jeśli daleko od assembly area
                # Move toward assembly area (simplified - actual pathfinding needed)
                if move_unit_toward_target(unit, assembly_area, game_engine):
                    units_moved += 1
    
    return f"POSITIONING: {units_moved} units moved toward assembly area"


def execute_concentration_phase(plan: Dict[str, Any], my_units: List[Dict[str, Any]], game_engine) -> str:
    """Execute concentration phase - concentrate forces, final scouting."""
    assembly_area = plan['assembly_area']
    assigned_force_ids = [u.get('unit_id', '') for u in plan.get('assigned_forces', [])]
    
    concentrated_units = 0
    for unit in my_units:
        if unit.get('unit_id') in assigned_force_ids:
            current_pos = unit.get('position', (0, 0))
            distance_to_assembly = abs(current_pos[0] - assembly_area[0]) + abs(current_pos[1] - assembly_area[1])
            
            if distance_to_assembly <= 3:  # W obrębie assembly area
                concentrated_units += 1
    
    # Final scouting of target area
    target_center = plan['target_center']
    scout_coverage = perform_target_scouting(target_center, my_units, game_engine)
    
    return f"CONCENTRATION: {concentrated_units} units concentrated, scouting: {scout_coverage}"


def execute_attack_phase_action(plan: Dict[str, Any], my_units: List[Dict[str, Any]], game_engine) -> str:
    """Execute attack phase - coordinated attack on targets."""
    target_center = plan['target_center']
    assigned_force_ids = [u.get('unit_id', '') for u in plan.get('assigned_forces', [])]
    
    attacking_units = []
    for unit in my_units:
        if unit.get('unit_id') in assigned_force_ids and unit.get('mp', 0) > 0:
            attacking_units.append(unit)
    
    # Find enemies near target center
    visible_enemies = scan_visible_enemies(my_units, game_engine)
    target_enemies = []
    
    for enemy in visible_enemies:
        enemy_pos = enemy.get('position', (0, 0))
        distance = abs(enemy_pos[0] - target_center[0]) + abs(enemy_pos[1] - target_center[1])
        if distance <= 4:  # Enemies near target
            target_enemies.append(enemy)
    
    if not target_enemies:
        return "ATTACK: No enemies found in target area"
    
    # Execute coordinated attacks
    attacks_executed = 0
    for attacker in attacking_units[:len(target_enemies)]:  # Max 1 attacker per target
        if target_enemies:
            target = target_enemies.pop(0)
            if execute_unit_attack(attacker, target, game_engine):
                attacks_executed += 1
    
    return f"ATTACK: {attacks_executed} coordinated attacks executed"


def execute_exploitation_phase(plan: Dict[str, Any], my_units: List[Dict[str, Any]], game_engine) -> str:
    """Execute exploitation phase - pursue enemies or secure gains."""
    target_center = plan['target_center']
    assigned_force_ids = [u.get('unit_id', '') for u in plan.get('assigned_forces', [])]
    
    exploitation_units = []
    for unit in my_units:
        if unit.get('unit_id') in assigned_force_ids and unit.get('mp', 0) > 0:
            exploitation_units.append(unit)
    
    # Check for fleeing enemies or secure key points
    visible_enemies = scan_visible_enemies(my_units, game_engine)
    nearby_enemies = []
    
    for enemy in visible_enemies:
        enemy_pos = enemy.get('position', (0, 0))
        distance = abs(enemy_pos[0] - target_center[0]) + abs(enemy_pos[1] - target_center[1])
        if distance <= 6:  # Expanding search radius
            nearby_enemies.append(enemy)
    
    if nearby_enemies:
        # Pursue fleeing enemies
        pursuit_moves = 0
        for unit in exploitation_units:
            if nearby_enemies:
                target_enemy = nearby_enemies[0]
                target_pos = target_enemy.get('position', (0, 0))
                if move_unit_toward_target(unit, target_pos, game_engine):
                    pursuit_moves += 1
        return f"EXPLOITATION: {pursuit_moves} units pursuing enemies"
    else:
        # Secure key points near target area
        secured_positions = 0
        for unit in exploitation_units:
            # Move to defensive positions around target center
            defensive_pos = (target_center[0] + 1, target_center[1] + 1)  # Simplified
            if move_unit_toward_target(unit, defensive_pos, game_engine):
                secured_positions += 1
        return f"EXPLOITATION: {secured_positions} units securing positions"


# ===== HELPER FUNCTIONS FOR PHASE EXECUTION =====

def move_unit_toward_target(unit: Dict[str, Any], target_pos: Tuple[int, int], game_engine) -> bool:
    """Simplified unit movement toward target. Returns True if moved."""
    # Placeholder - actual implementation would use pathfinding
    current_pos = unit.get('position', (0, 0))
    
    # Simple direction calculation
    if current_pos[0] < target_pos[0]:
        new_pos = (current_pos[0] + 1, current_pos[1])
    elif current_pos[0] > target_pos[0]:
        new_pos = (current_pos[0] - 1, current_pos[1])
    elif current_pos[1] < target_pos[1]:
        new_pos = (current_pos[0], current_pos[1] + 1)
    elif current_pos[1] > target_pos[1]:
        new_pos = (current_pos[0], current_pos[1] - 1)
    else:
        return False  # Already at target
    
    # Placeholder for actual movement validation
    debug_print(f"[MOVEMENT] Unit {unit.get('unit_id', 'UNKNOWN')} moving from {current_pos} toward {target_pos}", 
               "FULL", "PLANNING")
    return True


def perform_target_scouting(target_pos: Tuple[int, int], my_units: List[Dict[str, Any]], game_engine) -> str:
    """Perform scouting of target area."""
    scouts_in_area = 0
    
    for unit in my_units:
        if unit.get('unitType') in ['K', 'Z_Aufkl']:  # Scout units
            unit_pos = unit.get('position', (0, 0))
            distance = abs(unit_pos[0] - target_pos[0]) + abs(unit_pos[1] - target_pos[1])
            if distance <= 4:  # Scout coverage radius
                scouts_in_area += 1
    
    if scouts_in_area >= 2:
        return "EXCELLENT"
    elif scouts_in_area >= 1:
        return "GOOD"
    else:
        return "POOR"


def execute_unit_attack(attacker: Dict[str, Any], target: Dict[str, Any], game_engine) -> bool:
    """Execute attack by one unit on target. Returns True if attack executed."""
    # Placeholder for actual combat execution
    attacker_pos = attacker.get('position', (0, 0))
    target_pos = target.get('position', (0, 0))
    
    distance = abs(attacker_pos[0] - target_pos[0]) + abs(attacker_pos[1] - target_pos[1])
    
    if distance <= 2:  # Within attack range
        debug_print(f"[COMBAT] Unit {attacker.get('unit_id', 'UNKNOWN')} attacking target at {target_pos}", 
                   "BASIC", "PLANNING")
        return True
    else:
        debug_print(f"[COMBAT] Unit {attacker.get('unit_id', 'UNKNOWN')} too far from target ({distance} hex)", 
                   "BASIC", "PLANNING")
        return False


# ===== PHASE 2 MAIN CONTROLLER =====

def victory_ai_phase2_controller(game_engine, my_units: List[Dict[str, Any]], player_id: int) -> Dict[str, Any]:
    """Phase 2 controller: Multi-turn Attack Planning.
    
    Args:
        game_engine: Standard game engine
        my_units: Lista wszystkich jednostek gracza
        player_id: ID gracza
        
    Returns:
        Action summary report
    """
    debug_print(f"[VICTORY AI] PHASE 2 START - Player {player_id}", "BASIC", VICTORY_LOG)
    
    current_turn = getattr(game_engine, 'current_turn', 1)
    
    report = {
        'phase': 'MULTI_TURN_ATTACK_PLANNING',
        'active_plans': 0,
        'new_plans_created': 0,
        'plans_executed': 0,
        'plans_aborted': 0,
        'phase_actions': []
    }
    
    try:
        # STEP 1: Execute existing attack plans
        active_plan_ids = [plan_id for plan_id, plan in ATTACK_PLAN_CACHE.items() 
                          if plan['status'] in ['PLANNING', 'EXECUTING'] and plan['player_id'] == player_id]
        
        report['active_plans'] = len(active_plan_ids)
        
        for plan_id in active_plan_ids:
            execution_status = execute_attack_phase(plan_id, current_turn, game_engine, my_units, player_id)
            
            if execution_status == "ABORTED":
                report['plans_aborted'] += 1
            elif execution_status == "COMPLETED":
                report['plans_executed'] += 1
            
            report['phase_actions'].append({
                'plan_id': plan_id,
                'status': execution_status
            })
        
        # STEP 2: Check for new attack opportunities (from Phase 1 results)
        phase1_results = victory_ai_phase1_controller(game_engine, my_units, player_id)
        
        new_opportunities = [action for action in phase1_results.get('recommended_actions', []) 
                           if action['action'] == 'PLAN_ATTACK']
        
        # STEP 3: Create new attack plans for high-confidence opportunities
        for opportunity in new_opportunities:
            if opportunity['confidence'] >= 0.7:  # High confidence threshold
                cluster_id = opportunity['target_cluster']
                threat_clusters = phase1_results.get('threat_clusters', [])
                
                if cluster_id < len(threat_clusters):
                    target_cluster = threat_clusters[cluster_id]
                    
                    # Select forces for attack (not all units)
                    available_forces = [u for u in my_units 
                                      if u.get('mp', 0) > 0 and not u.get('moved_capture', False)]
                    
                    # Reserve 40% of forces for defense/PE collection
                    attack_force_limit = max(len(available_forces) * 6 // 10, 3)  # Min 3 units
                    selected_forces = available_forces[:attack_force_limit]
                    
                    if len(selected_forces) >= 3:  # Minimum viable attack force
                        new_plan = create_attack_plan(target_cluster, selected_forces, 
                                                    game_engine, player_id, current_turn)
                        
                        if new_plan['status'] != 'INVALID':
                            report['new_plans_created'] += 1
                            report['phase_actions'].append({
                                'action': 'NEW_PLAN_CREATED',
                                'plan_id': new_plan['plan_id'],
                                'target_cluster_size': len(target_cluster),
                                'assigned_forces': len(selected_forces)
                            })
                            
                            debug_print(f"[VICTORY AI PHASE 2] Created new attack plan {new_plan['plan_id']}", 
                                       "BASIC", VICTORY_LOG)
        
        # STEP 4: Plan maintenance - cleanup completed/old plans
        cleanup_old_plans(player_id, current_turn)
        
        # CSV Log Phase 2 summary
        log_victory_ai_csv("PHASE2_SUMMARY", player_id, current_turn,
                          active_plans=report['active_plans'], new_plans=report['new_plans_created'],
                          executed_plans=report['plans_executed'], aborted_plans=report['plans_aborted'])
        
        debug_print(f"[VICTORY AI] PHASE 2 COMPLETE - {report['active_plans']} active, "
                   f"{report['new_plans_created']} new, {report['plans_executed']} executed", "BASIC", VICTORY_LOG)
        
    except Exception as e:
        debug_print(f"[VICTORY AI] PHASE 2 ERROR: {e}", "BASIC", VICTORY_LOG)
        log_victory_ai_csv("PHASE2_ERROR", player_id, current_turn, error=str(e))
        report['error'] = str(e)
    
    return report


def cleanup_old_plans(player_id: int, current_turn: int):
    """Clean up completed or very old attack plans."""
    plans_to_remove = []
    
    for plan_id, plan in ATTACK_PLAN_CACHE.items():
        if plan['player_id'] == player_id:
            # Remove completed plans after 2 turns
            if plan['status'] == 'COMPLETED' and current_turn - plan['created_turn'] > 2:
                plans_to_remove.append(plan_id)
            # Remove very old plans (8+ turns old)
            elif current_turn - plan['created_turn'] > 8:
                plans_to_remove.append(plan_id)
    
    for plan_id in plans_to_remove:
        del ATTACK_PLAN_CACHE[plan_id]
        debug_print(f"[PLAN CLEANUP] Removed old plan {plan_id}", "FULL", VICTORY_LOG)


# ===== UPDATED INTEGRATION FUNCTIONS =====

def integrate_victory_ai_full(game_engine, my_units: List[Dict[str, Any]], player_id: int) -> Dict[str, Any]:
    """Full Victory AI integration - Phase 1 + Phase 2.
    
    Wywołaj to w ai_commander.py jako replacement dla integrate_victory_ai_phase1.
    """
    # Execute Phase 1 (scouting + threat assessment)
    phase1_results = victory_ai_phase1_controller(game_engine, my_units, player_id)
    
    # Execute Phase 2 (multi-turn attack planning)  
    phase2_results = victory_ai_phase2_controller(game_engine, my_units, player_id)
    
    # Combined results
    combined_results = {
        'victory_ai_active': True,
        'phase1': phase1_results,
        'phase2': phase2_results,
        'total_opportunities': phase1_results.get('combat_opportunities', 0),
        'active_attack_plans': phase2_results.get('active_plans', 0),
        'recommended_actions': phase1_results.get('recommended_actions', []) + 
                             phase2_results.get('phase_actions', [])
    }
    
    return combined_results


# =============================================================================
# PHASE 3: BALANCED DEFENSE & KP SECURITY
# =============================================================================

def calculate_defense_allocation(total_forces: List[Dict[str, Any]], 
                               active_attack_plans: List[Dict], 
                               game_engine) -> Dict[str, Any]:
    """Określ ile sił zostaje przy obronie KP vs. ide na atak.
    
    Args:
        total_forces: Lista wszystkich dostępnych jednostek
        active_attack_plans: Plany ataku z Phase 2
        game_engine: Dostęp do game state
        
    Returns:
        Dict zawierający alokację sił
    """
    try:
        # Filter out units without MP/Fuel
        available_forces = []
        for unit in total_forces:
            mp = unit.get('MP', 0)
            fuel = unit.get('Fuel', 0) 
            
            if mp > 0 and fuel > 0:
                available_forces.append(unit)
        
        total_available = len(available_forces)
        
        if total_available == 0:
            debug_print(f"[PHASE3] Brak dostępnych jednostek do alokacji", "BASIC", VICTORY_LOG)
            return {
                'defensive_units': [],
                'attack_units': [],
                'reserve_units': [],
                'allocation_ratios': {'defense_percent': 0, 'attack_percent': 0, 'reserve_percent': 0}
            }
        
        # Bazowa alokacja: 60% obrona, 30% atak, 10% rezerwa
        base_defense_ratio = 0.6
        base_attack_ratio = 0.3
        base_reserve_ratio = 0.1
        
        # Modyfikatory na podstawie threat level
        current_turn = getattr(game_engine, 'current_turn', 1)
        threat_modifier = assess_overall_threat_level(game_engine, total_forces)
        
        # Modyfikator na podstawie aktywnych planów ataku
        active_plans_count = len(active_attack_plans)
        plan_modifier = min(0.2, active_plans_count * 0.1)  # Maks +20% na atak
        
        # Finalne ratio
        if threat_modifier > 0.7:  # Wysokie zagrożenie
            defense_ratio = min(0.8, base_defense_ratio + 0.2)
            attack_ratio = max(0.1, base_attack_ratio - 0.1)
        elif threat_modifier < 0.3:  # Niskie zagrożenie  
            defense_ratio = max(0.4, base_defense_ratio - 0.1)
            attack_ratio = min(0.5, base_attack_ratio + plan_modifier)
        else:  # Średnie zagrożenie
            defense_ratio = base_defense_ratio
            attack_ratio = base_attack_ratio + (plan_modifier * 0.5)
        
        reserve_ratio = max(0.05, 1.0 - defense_ratio - attack_ratio)
        
        # Normalizuj ratio, żeby suma była dokładnie 1.0
        total_ratio = defense_ratio + attack_ratio + reserve_ratio
        if total_ratio > 0:
            defense_ratio = defense_ratio / total_ratio
            attack_ratio = attack_ratio / total_ratio
            reserve_ratio = reserve_ratio / total_ratio
        
        # Alokacja jednostek
        defense_count = int(total_available * defense_ratio)
        attack_count = int(total_available * attack_ratio)
        reserve_count = total_available - defense_count - attack_count
        
        # Sortuj jednostki według przydatności do obrony (defensywne stats)
        sorted_for_defense = sorted(available_forces, 
                                  key=lambda u: (u.get('defense', 0), u.get('attack', 0)), 
                                  reverse=True)
        
        # Przydziel jednostki
        defensive_units = sorted_for_defense[:defense_count]
        attack_units = sorted_for_defense[defense_count:defense_count + attack_count]
        reserve_units = sorted_for_defense[defense_count + attack_count:]
        
        allocation_result = {
            'defensive_units': defensive_units,
            'attack_units': attack_units,
            'reserve_units': reserve_units,
            'allocation_ratios': {
                'defense_percent': round(defense_ratio * 100, 1),
                'attack_percent': round(attack_ratio * 100, 1),
                'reserve_percent': round(reserve_ratio * 100, 1)
            },
            'total_available': total_available,
            'threat_level': threat_modifier,
            'active_plans': active_plans_count
        }
        
        debug_print(f"[PHASE3] Defense allocation: {defense_count}D/{attack_count}A/{reserve_count}R (threat: {threat_modifier:.2f})", "BASIC", VICTORY_LOG)
        
        return allocation_result
        
    except Exception as e:
        debug_print(f"[PHASE3] ERROR w calculate_defense_allocation: {e}", "BASIC", VICTORY_LOG)
        return {
            'defensive_units': total_forces[:len(total_forces)//2], 
            'attack_units': total_forces[len(total_forces)//2:],
            'reserve_units': [],
            'allocation_ratios': {'defense_percent': 50, 'attack_percent': 50, 'reserve_percent': 0}
        }


def assess_overall_threat_level(game_engine, my_units: List[Dict[str, Any]]) -> float:
    """Ocenia ogólny poziom zagrożenia dla gracza.
    
    Returns:
        float: 0.0 (brak zagrożenia) do 1.0 (krytyczne zagrożenie)
    """
    try:
        total_threat = 0.0
        threat_count = 0
        
        # Sprawdź zagrożenie dla każdej naszej jednostki
        for unit in my_units:
            unit_pos = (unit.get('q', 0), unit.get('r', 0))
            nearby_enemies = []
            
            # Znajdź wrogów w pobliżu (zasięg 4)
            board = getattr(game_engine, 'board', None)
            if board and hasattr(board, 'tokens'):
                for pos, token in board.tokens.items():
                    if hasattr(token, 'owner') and token.owner:
                        token_owner = token.owner.split('(')[-1].replace(')', '').strip()
                        our_owner = my_units[0].get('owner', '').split('(')[-1].replace(')', '').strip() if my_units else ''
                        
                        if token_owner != our_owner:  # Wróg
                            distance = abs(pos[0] - unit_pos[0]) + abs(pos[1] - unit_pos[1])
                            if distance <= 4:
                                enemy_strength = getattr(token, 'attack', 10)
                                nearby_enemies.append((distance, enemy_strength))
            
            # Oblicz threat level dla tej jednostki
            if nearby_enemies:
                # Threat jest większy gdy wrogowie są blżej i silniejsi
                unit_threat = 0.0
                for distance, strength in nearby_enemies:
                    proximity_factor = max(0.1, (5 - distance) / 5)  # Bliżej = większe zagrożenie
                    unit_threat += strength * proximity_factor / 100  # Normalize
                
                total_threat += min(1.0, unit_threat)
                threat_count += 1
        
        # Średni threat level
        if threat_count > 0:
            avg_threat = total_threat / threat_count
        else:
            avg_threat = 0.0
        
        return min(1.0, avg_threat)
        
    except Exception as e:
        debug_print(f"[PHASE3] ERROR w assess_overall_threat_level: {e}", "BASIC", VICTORY_LOG)
        return 0.5  # Default moderate threat


def assign_kp_defenders(available_defenders: List[Dict[str, Any]], 
                       key_points: List[Tuple[int, int]], 
                       threat_level: float,
                       game_engine) -> Dict[str, Any]:
    """Przypisz konkretne jednostki do obrony konkretnych KP.
    
    Args:
        available_defenders: Jednostki dostępne do obrony
        key_points: Lista współrzędnych key points  
        threat_level: Ogólny poziom zagrożenia (0.0-1.0)
        game_engine: Game state access
        
    Returns:
        Dict z przypisaniami i priorytetami
    """
    try:
        # Pobierz dane o key points
        kp_data = {}
        board = getattr(game_engine, 'board', None)
        
        if board and hasattr(board, 'key_points_state'):
            kp_state = board.key_points_state
            for kp_pos in key_points:
                hex_id = f"{kp_pos[0]},{kp_pos[1]}"
                kp_info = kp_state.get(hex_id, {})
                kp_data[kp_pos] = {
                    'current_value': kp_info.get('current_value', 0),
                    'initial_value': kp_info.get('initial_value', 1),
                    'controlled_by': kp_info.get('controlled_by', None)
                }
        
        # Priorytetyzuj KP według wartości PE + strategic value
        prioritized_kps = []
        for kp_pos in key_points:
            kp_info = kp_data.get(kp_pos, {})
            current_value = kp_info.get('current_value', 0)
            
            # Strategic value calculation
            strategic_value = current_value
            
            # Bonus dla centrally located KP
            distance_from_center = abs(kp_pos[0] - 25) + abs(kp_pos[1])
            if distance_from_center < 10:
                strategic_value *= 1.2
            
            # Penalty dla exhausted KP  
            if current_value <= 0:
                strategic_value = 0
            
            prioritized_kps.append((kp_pos, strategic_value, kp_info))
        
        # Sortuj według strategic value
        prioritized_kps.sort(key=lambda x: x[1], reverse=True)
        
        # Przydziel defenders
        kp_assignments = {}
        unassigned_defenders = available_defenders.copy()
        
        for kp_pos, strategic_value, kp_info in prioritized_kps:
            if strategic_value <= 0 or not unassigned_defenders:
                continue
                
            # Calculate needed defenders based on value and threat
            base_defenders = 1 if strategic_value > 20 else 0
            
            if strategic_value > 80:
                needed_defenders = 3
            elif strategic_value > 50:
                needed_defenders = 2  
            elif strategic_value > 20:
                needed_defenders = 1
            else:
                needed_defenders = 0
            
            # Threat modifier
            if threat_level > 0.7:
                needed_defenders += 1
            elif threat_level < 0.3:
                needed_defenders = max(0, needed_defenders - 1)
            
            needed_defenders = min(needed_defenders, len(unassigned_defenders))
            
            if needed_defenders > 0:
                # Wybierz najbliższych defenders
                closest_defenders = sorted(unassigned_defenders, 
                                         key=lambda u: abs(u.get('q', 0) - kp_pos[0]) + abs(u.get('r', 0) - kp_pos[1]))
                
                assigned_defenders = closest_defenders[:needed_defenders]
                support_units = []  # Support units from existing garrison system
                
                kp_assignments[kp_pos] = {
                    'defenders': assigned_defenders,
                    'support_units': support_units,
                    'priority_level': int(strategic_value / 25),  # 0-4 scale
                    'strategic_value': strategic_value,
                    'needed_defenders': needed_defenders
                }
                
                # Remove assigned defenders
                for defender in assigned_defenders:
                    if defender in unassigned_defenders:
                        unassigned_defenders.remove(defender)
        
        result = {
            'kp_assignments': kp_assignments,
            'unassigned_defenders': unassigned_defenders,
            'total_kps_covered': len(kp_assignments),
            'total_defenders_assigned': len(available_defenders) - len(unassigned_defenders)
        }
        
        debug_print(f"[PHASE3] KP Assignments: {len(kp_assignments)} KPs covered, {result['total_defenders_assigned']} defenders assigned", "BASIC", VICTORY_LOG)
        
        return result
        
    except Exception as e:
        debug_print(f"[PHASE3] ERROR w assign_kp_defenders: {e}", "BASIC", VICTORY_LOG)
        return {
            'kp_assignments': {},
            'unassigned_defenders': available_defenders,
            'total_kps_covered': 0,
            'total_defenders_assigned': 0
        }


def maintain_pe_collection_capability(defense_plan: Dict[str, Any], game_engine) -> Dict[str, Any]:
    """Upewnij się że PE collection nie jest zagrożone.
    
    Args:
        defense_plan: Plan obrony z assign_kp_defenders()
        game_engine: Game state
        
    Returns:
        Dict z ocean PE security i rekomendacjami
    """
    try:
        pe_security_status = {
            'pe_secure': True,
            'critical_pe_points': [],
            'unprotected_pe_points': [],
            'recommendations': []
        }
        
        board = getattr(game_engine, 'board', None)
        if not board or not hasattr(board, 'key_points_state'):
            return pe_security_status
        
        kp_state = board.key_points_state
        kp_assignments = defense_plan.get('kp_assignments', {})
        
        # Sprawdź wszystkie PE-generating KP
        for hex_id, kp_data in kp_state.items():
            try:
                q, r = map(int, hex_id.split(','))
                kp_pos = (q, r)
            except:
                continue
                
            current_value = kp_data.get('current_value', 0)
            controlled_by = kp_data.get('controlled_by', None)
            
            # Skip wyczerpane lub wrogie KP
            if current_value <= 0 or not controlled_by:
                continue
            
            # Check if this KP generates PE (wysokowartościowe)
            is_pe_generating = current_value > 30  # Threshold dla PE generation
            
            if is_pe_generating:
                kp_assignment = kp_assignments.get(kp_pos, {})
                defenders = kp_assignment.get('defenders', [])
                
                # Sprawdź czy KP jest chroniony
                is_protected = len(defenders) > 0
                
                # Sprawdź czy są jednostki Z (Zaopatrzenie) w pobliżu
                has_supply_units = False
                if board and hasattr(board, 'tokens'):
                    for pos, token in board.tokens.items():
                        if hasattr(token, 'unit_type') and 'Z' in str(token.unit_type):
                            distance = abs(pos[0] - kp_pos[0]) + abs(pos[1] - kp_pos[1])
                            if distance <= 2:  # Supply units w zasięgu 2
                                has_supply_units = True
                                break
                
                # Assess threat level dla tego KP
                nearby_threats = 0
                if board and hasattr(board, 'tokens'):
                    for pos, token in board.tokens.items():
                        if hasattr(token, 'owner') and token.owner:
                            # Check if enemy token
                            if controlled_by not in token.owner:  # Simplified enemy check
                                distance = abs(pos[0] - kp_pos[0]) + abs(pos[1] - kp_pos[1])
                                if distance <= 3:  # Enemy within striking distance
                                    nearby_threats += 1
                
                # Evaluate PE point security
                pe_point_info = {
                    'position': kp_pos,
                    'value': current_value,
                    'protected': is_protected,
                    'has_supply': has_supply_units,
                    'threat_level': nearby_threats,
                    'defenders_count': len(defenders)
                }
                
                # Determine if critical/unprotected
                if nearby_threats > 0 and not is_protected:
                    pe_security_status['unprotected_pe_points'].append(pe_point_info)
                    pe_security_status['pe_secure'] = False
                    pe_security_status['recommendations'].append(
                        f"URGENT: Assign defenders to PE point {kp_pos} (value: {current_value}, threats: {nearby_threats})"
                    )
                
                if current_value > 80 and (not is_protected or nearby_threats > 1):
                    pe_security_status['critical_pe_points'].append(pe_point_info)
                    if nearby_threats > 1:
                        pe_security_status['pe_secure'] = False
                        pe_security_status['recommendations'].append(
                            f"CRITICAL: Reinforce high-value PE point {kp_pos} (value: {current_value}, threats: {nearby_threats})"
                        )
                
                if not has_supply_units:
                    pe_security_status['recommendations'].append(
                        f"INFO: Consider positioning supply units near PE point {kp_pos} for collection"
                    )
        
        # Summary assessment
        critical_count = len(pe_security_status['critical_pe_points'])
        unprotected_count = len(pe_security_status['unprotected_pe_points'])
        
        if critical_count > 0 or unprotected_count > 0:
            pe_security_status['pe_secure'] = False
            
        debug_print(f"[PHASE3] PE Security: {critical_count} critical, {unprotected_count} unprotected PE points", "BASIC", VICTORY_LOG)
        
        return pe_security_status
        
    except Exception as e:
        debug_print(f"[PHASE3] ERROR w maintain_pe_collection_capability: {e}", "BASIC", VICTORY_LOG)
        return {
            'pe_secure': False,
            'critical_pe_points': [],
            'unprotected_pe_points': [],
            'recommendations': [f"ERROR in PE security check: {e}"]
        }


def victory_ai_phase3_controller(game_engine, my_units: List[Dict[str, Any]], player_id: int) -> Dict[str, Any]:
    """Main controller dla Phase 3 - Balanced Defense & KP Security.
    
    Args:
        game_engine: Game engine instance
        my_units: Lista jednostek gracza
        player_id: ID gracza
        
    Returns:
        Dict z rezultatami Phase 3
    """
    try:
        current_turn = getattr(game_engine, 'current_turn', 1)
        
        # Log Phase 3 start
        player_nation = "Niemcy" if player_id in [4, 5, 6] else "Polska"  # Simple mapping
        log_victory_ai_csv("TURN_START", player_id, current_turn, 
                          player_nation=player_nation, 
                          total_units=len(my_units), 
                          available_units=len([u for u in my_units if u.get('MP', 0) > 0]))
        
        # 1. Pobierz active attack plans
        active_plans = []
        our_plans = [plan for plan in ATTACK_PLAN_CACHE.values() if plan.get('player_id') == player_id]
        active_plans = [plan for plan in our_plans if plan.get('status') in ['PLANNING', 'POSITIONING', 'CONCENTRATION', 'ATTACK', 'EXPLOITATION']]
        
        # 2. Calculate defense allocation
        allocation = calculate_defense_allocation(my_units, active_plans, game_engine)
        
        # 3. Get strategic key points
        board = getattr(game_engine, 'board', None)
        key_points = []
        if board and hasattr(board, 'key_points_state'):
            for hex_id in board.key_points_state.keys():
                try:
                    q, r = map(int, hex_id.split(','))
                    key_points.append((q, r))
                except:
                    continue
        
        # 4. Assess overall threat
        threat_level = assess_overall_threat_level(game_engine, my_units)
        
        # 5. Assign KP defenders
        kp_defense = assign_kp_defenders(
            allocation['defensive_units'], 
            key_points, 
            threat_level, 
            game_engine
        )
        
        # 6. Validate PE security
        pe_security = maintain_pe_collection_capability(kp_defense, game_engine)
        
        # 7. Integration with existing garrison system
        garrison_integration = integrate_with_garrison_support(kp_defense, my_units, game_engine)
        
        # 8. Generate recommendations
        recommendations = generate_defense_recommendations(allocation, kp_defense, pe_security, threat_level)
        
        # 9. Log Phase 3 summary
        log_victory_ai_csv("PHASE3_SUMMARY", player_id, current_turn,
                          defenders_assigned=kp_defense['total_defenders_assigned'],
                          kps_covered=kp_defense['total_kps_covered'],
                          pe_secure=pe_security['pe_secure'],
                          threat_level=round(threat_level, 2),
                          active_plans=len(active_plans))
        
        phase3_results = {
            'phase3_active': True,
            'allocation': allocation,
            'kp_assignments': kp_defense,
            'pe_security': pe_security,
            'garrison_integration': garrison_integration,
            'threat_level': threat_level,
            'active_attack_plans': len(active_plans),
            'recommendations': recommendations,
            'phase3_actions': [
                f"DEFENSE_ALLOCATION: {allocation['allocation_ratios']['defense_percent']}% defense",
                f"KP_COVERAGE: {kp_defense['total_kps_covered']} key points covered",
                f"PE_SECURITY: {'SECURE' if pe_security['pe_secure'] else 'AT_RISK'}"
            ]
        }
        
        return phase3_results
        
    except Exception as e:
        debug_print(f"[PHASE3] ERROR w victory_ai_phase3_controller: {e}", "BASIC", VICTORY_LOG)
        log_victory_ai_csv("PHASE3_ERROR", player_id, getattr(game_engine, 'current_turn', 1),
                          error=str(e))
        
        return {
            'phase3_active': False,
            'allocation': {'defensive_units': my_units, 'attack_units': [], 'reserve_units': []},
            'kp_assignments': {'kp_assignments': {}, 'unassigned_defenders': my_units},
            'pe_security': {'pe_secure': False, 'recommendations': [f"Phase 3 error: {e}"]},
            'threat_level': 0.5,
            'recommendations': [f"Phase 3 failed: {e}"]
        }


def integrate_with_garrison_support(kp_defense: Dict[str, Any], 
                                   my_units: List[Dict[str, Any]], 
                                   game_engine) -> Dict[str, Any]:
    """Integracja z istniejącym systemem garrison support.
    
    Args:
        kp_defense: Plan obrony KP
        my_units: Wszystkie jednostki gracza
        game_engine: Game engine
        
    Returns:
        Dict z rezultatem integracji
    """
    try:
        integration_result = {
            'garrison_assignments': 0,
            'support_assignments': 0,
            'integration_success': True,
            'issues': []
        }
        
        kp_assignments = kp_defense.get('kp_assignments', {})
        
        # Set garrison roles for assigned defenders
        for kp_pos, assignment in kp_assignments.items():
            defenders = assignment.get('defenders', [])
            
            for defender in defenders:
                # Mark as garrison unit
                defender['assigned_target'] = kp_pos
                defender['support_role'] = 'victory_ai_defender'
                defender['priority_task'] = 'kp_defense'
                defender['victory_ai_assignment'] = True
                
                integration_result['garrison_assignments'] += 1
        
        # Try to integrate with existing wsparcie_garnizonu system
        try:
            from ai.wsparcie_garnizonu import assign_garrison_support
            
            # Run existing garrison support system for remaining units
            unassigned_units = [u for u in my_units if not u.get('victory_ai_assignment', False)]
            support_count = assign_garrison_support(unassigned_units, game_engine)
            integration_result['support_assignments'] = support_count
            
        except Exception as e:
            integration_result['issues'].append(f"Garrison support integration failed: {e}")
            debug_print(f"[PHASE3] Garrison support integration error: {e}", "BASIC", VICTORY_LOG)
        
        debug_print(f"[PHASE3] Garrison integration: {integration_result['garrison_assignments']} Victory AI assignments, {integration_result['support_assignments']} traditional support", "BASIC", VICTORY_LOG)
        
        return integration_result
        
    except Exception as e:
        debug_print(f"[PHASE3] ERROR w integrate_with_garrison_support: {e}", "BASIC", VICTORY_LOG)
        return {
            'garrison_assignments': 0,
            'support_assignments': 0,
            'integration_success': False,
            'issues': [f"Integration error: {e}"]
        }


def generate_defense_recommendations(allocation: Dict[str, Any], 
                                   kp_defense: Dict[str, Any], 
                                   pe_security: Dict[str, Any], 
                                   threat_level: float) -> List[str]:
    """Generuj rekomendacje defensywne dla gracza.
    
    Returns:
        Lista rekomendacji tekstowych
    """
    recommendations = []
    
    try:
        # Allocation recommendations
        defense_percent = allocation.get('allocation_ratios', {}).get('defense_percent', 0)
        if defense_percent > 80:
            recommendations.append("DEFENSIVE: Very high defense allocation - consider more aggressive stance")
        elif defense_percent < 40:
            recommendations.append("AGGRESSIVE: Low defense allocation - ensure key points are secure")
        
        # KP coverage recommendations
        total_covered = kp_defense.get('total_kps_covered', 0)
        if total_covered < 3:
            recommendations.append("EXPAND: Cover more key points for better PE generation")
        elif total_covered > 8:
            recommendations.append("CONSOLIDATE: Too many KP covered - focus on high-value points")
        
        # PE security recommendations
        if not pe_security.get('pe_secure', True):
            critical_count = len(pe_security.get('critical_pe_points', []))
            if critical_count > 0:
                recommendations.append(f"URGENT: {critical_count} critical PE points need immediate protection")
            
            unprotected_count = len(pe_security.get('unprotected_pe_points', []))
            if unprotected_count > 0:
                recommendations.append(f"SECURE: {unprotected_count} PE points lack adequate defense")
        
        # Threat level recommendations
        if threat_level > 0.8:
            recommendations.append("ALERT: High threat level detected - prioritize defensive measures")
        elif threat_level < 0.2:
            recommendations.append("OPPORTUNITY: Low threat environment - consider aggressive expansion")
        
        # Include PE security specific recommendations
        pe_recommendations = pe_security.get('recommendations', [])
        recommendations.extend(pe_recommendations[:3])  # Max 3 PE recommendations
        
        return recommendations[:6]  # Limit to 6 recommendations total
        
    except Exception as e:
        debug_print(f"[PHASE3] ERROR w generate_defense_recommendations: {e}", "BASIC", VICTORY_LOG)
        return [f"Recommendation system error: {e}"]


# Updated full integration function to include Phase 3
def integrate_victory_ai_full_with_phase3(game_engine, my_units: List[Dict[str, Any]], player_id: int) -> Dict[str, Any]:
    """Complete Victory AI integration - Phase 1 + Phase 2 + Phase 3.
    
    This is the ultimate Victory AI function to call from ai_commander.py
    """
    try:
        # Execute Phase 1 (scouting + threat assessment)
        phase1_results = victory_ai_phase1_controller(game_engine, my_units, player_id)
        
        # Execute Phase 2 (multi-turn attack planning)  
        phase2_results = victory_ai_phase2_controller(game_engine, my_units, player_id)
        
        # Execute Phase 3 (balanced defense + KP security)
        phase3_results = victory_ai_phase3_controller(game_engine, my_units, player_id)
        
        # Combined results
        combined_results = {
            'victory_ai_active': True,
            'phase1': phase1_results,
            'phase2': phase2_results,
            'phase3': phase3_results,
            'total_opportunities': phase1_results.get('combat_opportunities', 0),
            'active_attack_plans': phase2_results.get('active_plans', 0),
            'kps_secured': phase3_results.get('kp_assignments', {}).get('total_kps_covered', 0),
            'pe_secure': phase3_results.get('pe_security', {}).get('pe_secure', False),
            'threat_level': phase3_results.get('threat_level', 0.5),
            'recommended_actions': (
                phase1_results.get('recommended_actions', []) + 
                phase2_results.get('phase_actions', []) +
                phase3_results.get('phase3_actions', [])
            ),
            'all_recommendations': (
                phase1_results.get('recommendations', []) +
                phase2_results.get('recommendations', []) +
                phase3_results.get('recommendations', [])
            )
        }
        
        debug_print(f"[VICTORY AI] Full system active: {phase1_results.get('combat_opportunities', 0)} combat ops, {phase2_results.get('active_plans', 0)} attack plans, {phase3_results.get('kp_assignments', {}).get('total_kps_covered', 0)} KPs secured", "BASIC", VICTORY_LOG)
        
        return combined_results
        
    except Exception as e:
        debug_print(f"[VICTORY AI] ERROR w integrate_victory_ai_full_with_phase3: {e}", "BASIC", VICTORY_LOG)
        # Fallback to Phase 1+2 only
        return integrate_victory_ai_full(game_engine, my_units, player_id)

# =============================================================================
# PHASE 4: ADVANCED LOGISTICS AI - VICTORY INTEGRATION
# =============================================================================

def victory_ai_phase4_controller(game_engine, my_units: List[Dict[str, Any]], player_id: int) -> Dict[str, Any]:
    """Phase 4 Controller - Advanced Logistics AI with Commander-General Communication.
    
    Integrates with communication_ai.py for force requirements analysis and 
    reinforcement request generation.
    
    Args:
        game_engine: Game engine
        my_units: Lista jednostek dowódcy
        player_id: ID gracza/dowódcy
        
    Returns:
        Phase 4 results dictionary
    """
    debug_print(f"[VICTORY AI PHASE 4] Starting Advanced Logistics AI for player {player_id}", "BASIC", VICTORY_LOG)
    
    try:
        # Import communication functions
        from ai.communication_ai import commander_logistics_analysis
        
        # Gather Victory AI context from previous phases
        victory_context = {
            'has_victory_ai': True,
            'phase4_active': True
        }
        
        try:
            # Get Phase 1-3 data for context
            phase1_data = victory_ai_phase1_controller(game_engine, my_units, player_id)
            phase2_data = victory_ai_phase2_controller(game_engine, my_units, player_id)
            phase3_data = victory_ai_phase3_controller(game_engine, my_units, player_id)
            
            victory_context.update({
                'active_attack_plans': phase2_data.get('active_plans', 0),
                'threat_level': phase3_data.get('threat_level', 0.5),
                'kp_security': phase3_data.get('pe_security', {}).get('pe_secure', False),
                'combat_opportunities': phase1_data.get('combat_opportunities', 0)
            })
            
        except Exception as e:
            debug_print(f"[PHASE 4] Warning: Could not gather Phase 1-3 context: {e}", "BASIC", VICTORY_LOG)
        
        # Execute Phase 4 logistics analysis
        logistics_result = commander_logistics_analysis(
            my_units=my_units,
            game_engine=game_engine,
            commander_id=player_id,
            victory_ai_data=victory_context
        )
        
        # Generate Phase 4 recommendations
        phase4_recommendations = _generate_phase4_recommendations(logistics_result, victory_context)
        
        # Phase 4 results
        phase4_results = {
            'phase': 'PHASE_4_COMPLETE',
            'logistics_analysis': logistics_result.get('force_analysis', {}),
            'request_generated': logistics_result.get('request_generated', False),
            'request_id': logistics_result.get('request_data', {}).get('request_id') if logistics_result.get('request_data') else None,
            'urgency_level': logistics_result.get('analysis_summary', {}).get('urgency', 'LOW'),
            'total_requirements': logistics_result.get('analysis_summary', {}).get('total_requirements', 0),
            'priority_areas': logistics_result.get('analysis_summary', {}).get('priority_areas', []),
            'needs_reinforcement': logistics_result.get('needs_reinforcement', False),
            'victory_ai_context': victory_context,
            'phase4_recommendations': phase4_recommendations,
            'logistics_integration_success': True
        }
        
        debug_print(f"[VICTORY AI PHASE 4] Complete - Request: {phase4_results['request_generated']}, Urgency: {phase4_results['urgency_level']}, Requirements: {phase4_results['total_requirements']}", "BASIC", VICTORY_LOG)
        
        # CSV Logging
        log_victory_ai_csv("PHASE_4_COMPLETE", player_id, "UNKNOWN",
                          request_generated=phase4_results['request_generated'],
                          urgency=phase4_results['urgency_level'],
                          requirements=phase4_results['total_requirements'],
                          priority_areas=",".join(phase4_results['priority_areas']))
        
        return phase4_results
        
    except ImportError as e:
        debug_print(f"[VICTORY AI PHASE 4] Import error: {e} - communication_ai.py not available", "BASIC", VICTORY_LOG)
        return {
            'phase': 'PHASE_4_ERROR',
            'error': 'communication_ai module not available',
            'logistics_integration_success': False
        }
        
    except Exception as e:
        debug_print(f"[VICTORY AI PHASE 4] ERROR: {e}", "BASIC", VICTORY_LOG)
        return {
            'phase': 'PHASE_4_ERROR', 
            'error': str(e),
            'logistics_integration_success': False
        }

def _generate_phase4_recommendations(logistics_result: Dict[str, Any], victory_context: Dict[str, Any]) -> List[str]:
    """Generate tactical recommendations based on Phase 4 logistics analysis."""
    recommendations = []
    
    if not logistics_result.get('force_analysis'):
        return ["Phase 4: Brak danych logistics analysis"]
    
    force_analysis = logistics_result['force_analysis']
    urgency = force_analysis.get('urgency', 'LOW')
    requirements = force_analysis.get('requirements', {})
    
    # Urgency-based recommendations
    if urgency == 'CRITICAL':
        recommendations.append("🚨 CRITICAL: Immediate reinforcement required - defensive posture recommended")
    elif urgency == 'HIGH':
        recommendations.append("⚠️ HIGH: Priority reinforcement needed - limit offensive operations")
    elif urgency == 'MEDIUM':
        recommendations.append("🔶 MEDIUM: Reinforcement beneficial - maintain current operations")
    
    # Specific requirements
    if requirements.get('supply_needed', 0) > 0:
        recommendations.append(f"🛠️ LOGISTICS: Request {requirements['supply_needed']} supply units for resupply operations")
    
    if requirements.get('reconnaissance_needed', 0) > 0:
        recommendations.append(f"👁️ RECON: Request {requirements['reconnaissance_needed']} reconnaissance units for improved intel")
    
    combat_needed = requirements.get('infantry_needed', 0) + requirements.get('armor_needed', 0)
    if combat_needed > 0:
        recommendations.append(f"⚔️ COMBAT: Request {combat_needed} combat units for force multiplication")
    
    # Victory AI integration recommendations
    if victory_context.get('active_attack_plans', 0) > 0 and urgency in ['LOW', 'MEDIUM']:
        recommendations.append("🎯 COORDINATION: Continue planned operations with logistics support")
    elif victory_context.get('threat_level', 0) > 0.7:
        recommendations.append("🛡️ DEFENSE: Prioritize defensive posture until reinforcements arrive")
    
    return recommendations if recommendations else ["Phase 4: Current force composition adequate"]

# =============================================================================
# COMPLETE VICTORY AI INTEGRATION - ALL PHASES
# =============================================================================

def integrate_victory_ai_complete_system(game_engine, my_units: List[Dict[str, Any]], player_id: int) -> Dict[str, Any]:
    """Complete Victory AI System - Phase 1 + Phase 2 + Phase 3 + Phase 4.
    
    This is the ULTIMATE Victory AI function with full Advanced Logistics AI.
    Call this from ai_commander.py for complete Victory AI integration.
    """
    try:
        # Execute all phases sequentially
        phase1_results = victory_ai_phase1_controller(game_engine, my_units, player_id)
        phase2_results = victory_ai_phase2_controller(game_engine, my_units, player_id)
        phase3_results = victory_ai_phase3_controller(game_engine, my_units, player_id)
        phase4_results = victory_ai_phase4_controller(game_engine, my_units, player_id)
        
        # Ultimate combined results
        ultimate_results = {
            'victory_ai_system': 'COMPLETE_ALL_PHASES',
            'phase1': phase1_results,
            'phase2': phase2_results,
            'phase3': phase3_results,
            'phase4': phase4_results,
            
            # Aggregated metrics
            'total_opportunities': phase1_results.get('combat_opportunities', 0),
            'active_attack_plans': phase2_results.get('active_plans', 0),
            'kps_secured': phase3_results.get('kp_assignments', {}).get('total_kps_covered', 0),
            'pe_secure': phase3_results.get('pe_security', {}).get('pe_secure', False),
            'threat_level': phase3_results.get('threat_level', 0.5),
            'logistics_active': phase4_results.get('logistics_integration_success', False),
            'reinforcement_requested': phase4_results.get('request_generated', False),
            'urgency_level': phase4_results.get('urgency_level', 'LOW'),
            
            # All recommendations from all phases
            'all_recommendations': (
                phase1_results.get('recommendations', []) +
                phase2_results.get('recommendations', []) +
                phase3_results.get('recommendations', []) +
                phase4_results.get('phase4_recommendations', [])
            ),
            
            # System status
            'system_status': 'FULLY_OPERATIONAL' if phase4_results.get('logistics_integration_success', False) else 'LOGISTICS_LIMITED'
        }
        
        debug_print(f"[VICTORY AI COMPLETE] All phases active: Combat({phase1_results.get('combat_opportunities', 0)}) Attack Plans({phase2_results.get('active_plans', 0)}) KPs({phase3_results.get('kp_assignments', {}).get('total_kps_covered', 0)}) Logistics({phase4_results.get('request_generated', False)})", "BASIC", VICTORY_LOG)
        
        return ultimate_results
        
    except Exception as e:
        debug_print(f"[VICTORY AI COMPLETE] ERROR: {e} - falling back to Phase 1-3", "BASIC", VICTORY_LOG)
        # Fallback to Phase 1-3 only
        return integrate_victory_ai_full_with_phase3(game_engine, my_units, player_id)
