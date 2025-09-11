"""Advanced Logistics AI - Phase 4 Implementation
Commander-General Communication System for Request-Based Resource Allocation

Implementuje:
- Force requirement analysis (Commander side)
- Reinforcement request generation (Commander → General)
- Request collection & prioritization (General side)
- Adaptive purchasing based on field needs
"""
from __future__ import annotations
from typing import Dict, List, Any, Tuple, Optional
from pathlib import Path
import json
from datetime import datetime
import csv

try:
    from main_ai import debug_print
except Exception:
    def debug_print(msg, level="BASIC", category="INFO"):
        print(f"[COMM_AI] {msg}")

# Logging categories
COMM_LOG = "COMMUNICATION"
FORCE_LOG = "FORCE_ANALYSIS"
REQUEST_LOG = "REQUEST"

# Communication storage
REQUESTS_DIR = Path("data/requests")
REQUESTS_DIR.mkdir(parents=True, exist_ok=True)

def get_current_turn(game_engine) -> int:
    """Bezpieczne pobieranie numeru tury."""
    return getattr(game_engine, 'turn_number', None) or getattr(game_engine, 'current_turn', 1)

def get_player_nation(game_engine) -> str:
    """Bezpieczne pobieranie nazwy narodu aktywnego gracza."""
    current_player = getattr(game_engine, 'current_player_obj', None)
    return getattr(current_player, 'nation', 'Unknown') if current_player else 'Unknown'

# =============================================================================
# MODULE 5.1: FORCE REQUIREMENTS ANALYSIS (Commander Side)
# =============================================================================

def analyze_force_requirements(my_units: List[Dict[str, Any]], 
                              game_engine, 
                              planned_operations: Optional[Dict] = None) -> Dict[str, Any]:
    """Analizuj potrzeby siłowe na podstawie aktualnej sytuacji terenowej.
    
    Args:
        my_units: Lista jednostek dowódcy
        game_engine: Dostęp do board i enemy situation
        planned_operations: Planned operations from Victory AI (optional)
        
    Returns:
        Dictionary z force requirements i priorities
    """
    if not my_units:
        debug_print("[FORCE ANALYSIS] Brak jednostek do analizy", "BASIC", FORCE_LOG)
        return {
            'status': 'NO_UNITS',
            'requirements': {},
            'priorities': {},
            'urgency': 'NONE',
            'analysis_timestamp': datetime.now().isoformat()
        }
    
    debug_print(f"[FORCE ANALYSIS] Analizuję {len(my_units)} jednostek", "FULL", FORCE_LOG)
    
    # 1. Analiza obecnej kompozycji sił
    current_composition = _analyze_current_composition(my_units)
    
    # 2. Analiza zagrożeń terenowych
    threat_analysis = _analyze_tactical_threats(my_units, game_engine)
    
    # 3. Analiza potrzeb operacyjnych
    operational_needs = _analyze_operational_needs(my_units, game_engine, planned_operations)
    
    # 4. Analiza stanu logistycznego
    logistics_status = _analyze_logistics_status(my_units)
    
    # 5. Wyliczenie konkretnych potrzeb
    requirements = _calculate_force_requirements(
        current_composition, threat_analysis, operational_needs, logistics_status
    )
    
    # 6. Priorytetyzacja potrzeb
    priorities = _prioritize_requirements(requirements, threat_analysis, operational_needs)
    
    # 7. Określenie poziomu pilności
    urgency_level = _determine_urgency_level(threat_analysis, logistics_status, operational_needs)
    
    analysis_result = {
        'status': 'ANALYZED',
        'current_composition': current_composition,
        'threat_analysis': threat_analysis,
        'operational_needs': operational_needs,
        'logistics_status': logistics_status,
        'requirements': requirements,
        'priorities': priorities,
        'urgency': urgency_level,
        'analysis_timestamp': datetime.now().isoformat(),
        'turn': get_current_turn(game_engine),
        'nation': get_player_nation(game_engine)
    }
    
    debug_print(f"[FORCE ANALYSIS] Analiza kompletna - urgency: {urgency_level}, requirements: {len(requirements)}", "BASIC", FORCE_LOG)
    
    # CSV Logging
    _log_force_analysis_csv(analysis_result)
    
    return analysis_result

def _analyze_current_composition(units: List[Dict[str, Any]]) -> Dict[str, Any]:
    """Analiza aktualnego składu sił."""
    composition = {
        'total_units': len(units),
        'by_type': {},
        'combat_strength': 0,
        'mobility': {'high': 0, 'medium': 0, 'low': 0},
        'fuel_status': {'critical': 0, 'low': 0, 'good': 0},
        'combat_value_total': 0,  # HP total dla kompatybilności
        'combat_strength_total': 0  # Rzeczywista siła bojowa
    }
    
    for unit in units:
        # Typ jednostki
        unit_type = unit.get('unit_type', 'Unknown')
        composition['by_type'][unit_type] = composition['by_type'].get(unit_type, 0) + 1
        
        # Combat value (HP) i combat strength (attack+defense)
        cv = unit.get('combat_value', 0)  # HP
        attack_val = unit.get('attack_val', 0)
        defense_val = unit.get('defense_val', 0)
        combat_strength = attack_val + defense_val
        
        composition['combat_value_total'] += cv  # HP total
        composition['combat_strength_total'] += combat_strength  # Siła bojowa
        
        # Status paliwa
        fuel_ratio = unit.get('fuel', 0) / max(1, unit.get('max_fuel', 1))
        if fuel_ratio < 0.3:
            composition['fuel_status']['critical'] += 1
        elif fuel_ratio < 0.6:
            composition['fuel_status']['low'] += 1
        else:
            composition['fuel_status']['good'] += 1
        
        # Mobilność (na podstawie MP)
        mp = unit.get('mp', 0)
        if mp >= 3:
            composition['mobility']['high'] += 1
        elif mp >= 2:
            composition['mobility']['medium'] += 1
        else:
            composition['mobility']['low'] += 1
    
    composition['avg_combat_value'] = composition['combat_value_total'] / max(1, len(units))  # Avg HP
    composition['avg_combat_strength'] = composition['combat_strength_total'] / max(1, len(units))  # Avg siła bojowa
    
    return composition

def _analyze_tactical_threats(units: List[Dict[str, Any]], game_engine) -> Dict[str, Any]:
    """Analiza zagrożeń terenowych w obszarze operacji."""
    threats = {
        'enemy_clusters': [],
        'total_enemy_cv': 0,
        'threat_level': 'LOW',
        'force_ratio': 0.0,
        'contested_areas': 0,
        'immediate_threats': 0
    }
    
    try:
        # Pobierz widocznych wrogów
        all_tokens = getattr(game_engine, 'tokens', [])
        current_player = getattr(game_engine, 'current_player_obj', None)
        my_nation = getattr(current_player, 'nation', '') if current_player else ''
        
        if not my_nation:
            return threats
        
        visible_enemies = []
        for token in all_tokens[:200]:  # Limit dla wydajności
            token_nation = getattr(token, 'nation', '')
            if token_nation and token_nation != my_nation:
                enemy_pos = (getattr(token, 'q', 0), getattr(token, 'r', 0))
                # Używamy combat_strength zamiast HP dla analizy siły
                enemy_attack = getattr(token, 'attack', None)
                enemy_attack_val = enemy_attack.value if enemy_attack else 0
                enemy_defense_val = getattr(token, 'defense_value', 0)
                enemy_combat_strength = enemy_attack_val + enemy_defense_val
                enemy_hp = getattr(token, 'combat_value', 0)  # HP dla statusu
                
                visible_enemies.append({
                    'position': enemy_pos,
                    'combat_value': enemy_hp,  # HP dla kompatybilności
                    'combat_strength': enemy_combat_strength,  # Rzeczywista siła
                    'attack_val': enemy_attack_val,
                    'defense_val': enemy_defense_val,
                    'type': getattr(token, 'type', 'Unknown')
                })
                threats['total_enemy_cv'] += enemy_combat_strength  # Używamy siły, nie HP
        
        # Oblicz force ratio na podstawie combat_strength
        my_total_strength = 0
        for unit in units:
            unit_attack = unit.get('attack_val', 0)
            unit_defense = unit.get('defense_val', 0) 
            my_total_strength += unit_attack + unit_defense
            
        if threats['total_enemy_cv'] > 0:
            threats['force_ratio'] = my_total_strength / threats['total_enemy_cv']
        else:
            threats['force_ratio'] = float('inf')
        
        # Określ threat level
        if threats['force_ratio'] < 0.5:
            threats['threat_level'] = 'CRITICAL'
        elif threats['force_ratio'] < 0.8:
            threats['threat_level'] = 'HIGH'
        elif threats['force_ratio'] < 1.2:
            threats['threat_level'] = 'MEDIUM'
        else:
            threats['threat_level'] = 'LOW'
        
        # Analiza immediate threats (wrogowie w zasięgu 3 hex)
        for unit in units:
            unit_pos = unit.get('position', (0, 0))
            for enemy in visible_enemies:
                distance = _hex_distance(unit_pos, enemy['position'])
                if distance <= 3:
                    threats['immediate_threats'] += 1
                    break  # Jeden threat per unit
        
        debug_print(f"[THREAT ANALYSIS] {len(visible_enemies)} wrogów, ratio {threats['force_ratio']:.2f}, level {threats['threat_level']}", "FULL", FORCE_LOG)
        
    except Exception as e:
        debug_print(f"[THREAT ANALYSIS] Błąd analizy: {e}", "BASIC", FORCE_LOG)
    
    return threats

def _analyze_operational_needs(units: List[Dict[str, Any]], 
                              game_engine, 
                              planned_operations: Optional[Dict] = None) -> Dict[str, Any]:
    """Analiza potrzeb operacyjnych na podstawie celów strategicznych."""
    needs = {
        'offensive_capability': 'SUFFICIENT',
        'defensive_capability': 'SUFFICIENT', 
        'reconnaissance_capability': 'SUFFICIENT',
        'logistics_capability': 'SUFFICIENT',
        'key_point_coverage': 0,
        'planned_operations_support': 'NONE'
    }
    
    # Sprawdź key points w obszarze
    key_points = getattr(game_engine, 'key_points_state', {})
    accessible_kp = 0
    
    for hex_id, kp_data in key_points.items():
        kp_value = kp_data.get('current_value', 0)
        if kp_value > 0:  # Dostępny key point
            accessible_kp += 1
    
    needs['key_point_coverage'] = accessible_kp
    
    # Analiza capabilities
    unit_types = [unit.get('unit_type', '') for unit in units]
    
    # Reconnaissance (K, Z_Aufkl)
    scouts = sum(1 for utype in unit_types if 'K' in utype or 'Z_Aufkl' in utype)
    if scouts == 0:
        needs['reconnaissance_capability'] = 'INSUFFICIENT'
    elif scouts < 2:
        needs['reconnaissance_capability'] = 'LIMITED'
    
    # Logistics (Z units)
    supply_units = sum(1 for utype in unit_types if 'Z' in utype)
    if supply_units == 0:
        needs['logistics_capability'] = 'CRITICAL'
    elif supply_units < 2:
        needs['logistics_capability'] = 'LIMITED'
    
    # Offensive (high CV units)
    high_cv_units = sum(1 for unit in units if unit.get('combat_value', 0) >= 4)
    if high_cv_units < 3:
        needs['offensive_capability'] = 'LIMITED'
    elif high_cv_units < 2:
        needs['offensive_capability'] = 'INSUFFICIENT'
    
    # Defensive (total units for area control)
    if len(units) < accessible_kp:
        needs['defensive_capability'] = 'INSUFFICIENT'
    elif len(units) < accessible_kp * 1.5:
        needs['defensive_capability'] = 'LIMITED'
    
    # Support dla planned operations
    if planned_operations:
        active_plans = planned_operations.get('active_attack_plans', [])
        if active_plans:
            needs['planned_operations_support'] = 'REQUIRED'
        
        defense_allocation = planned_operations.get('defense_allocation', {})
        if defense_allocation.get('defenders_needed', 0) > len(units):
            needs['defensive_capability'] = 'CRITICAL'
    
    return needs

def _analyze_logistics_status(units: List[Dict[str, Any]]) -> Dict[str, Any]:
    """Analiza stanu logistycznego jednostek."""
    status = {
        'fuel_critical_count': 0,
        'fuel_low_count': 0,
        'avg_fuel_level': 0.0,
        'supply_units_available': 0,
        'resupply_needed': False,
        'mobility_degraded': 0
    }
    
    fuel_levels = []
    
    for unit in units:
        fuel = unit.get('fuel', 0)
        max_fuel = unit.get('max_fuel', 1)
        fuel_ratio = fuel / max(1, max_fuel)
        fuel_levels.append(fuel_ratio)
        
        if fuel_ratio < 0.2:
            status['fuel_critical_count'] += 1
            status['mobility_degraded'] += 1
        elif fuel_ratio < 0.5:
            status['fuel_low_count'] += 1
        
        # Supply units
        unit_type = unit.get('unit_type', '')
        if 'Z' in unit_type:
            status['supply_units_available'] += 1
    
    if fuel_levels:
        status['avg_fuel_level'] = sum(fuel_levels) / len(fuel_levels)
    
    # Czy potrzebne resupply?
    critical_ratio = status['fuel_critical_count'] / max(1, len(units))
    low_ratio = (status['fuel_critical_count'] + status['fuel_low_count']) / max(1, len(units))
    
    status['resupply_needed'] = critical_ratio > 0.2 or low_ratio > 0.4
    
    return status

def _calculate_force_requirements(composition: Dict, threats: Dict, operations: Dict, logistics: Dict) -> Dict[str, Any]:
    """Oblicz konkretne potrzeby siłowe na podstawie analiz."""
    requirements = {
        'infantry_needed': 0,
        'armor_needed': 0,
        'artillery_needed': 0,
        'reconnaissance_needed': 0,
        'supply_needed': 0,
        'total_cv_needed': 0,
        'priority_types': []
    }
    
    # Potrzeby na podstawie threat level
    if threats['threat_level'] in ['HIGH', 'CRITICAL']:
        # Potrzeba wzmocnień bojowych - porównujemy siłę bojową, nie HP
        cv_deficit = max(0, threats['total_enemy_cv'] * 1.2 - composition['combat_strength_total'])
        requirements['total_cv_needed'] = int(cv_deficit)
        
        if cv_deficit > 0:
            # Priorytet dla jednostek o wysokim CV
            requirements['armor_needed'] = max(1, int(cv_deficit / 6))  # Assume armor ~6 CV
            requirements['infantry_needed'] = max(2, int(cv_deficit / 3))  # Assume infantry ~3 CV
            requirements['priority_types'].append('COMBAT_UNITS')
    
    # Potrzeby recon
    if operations['reconnaissance_capability'] in ['INSUFFICIENT', 'LIMITED']:
        requirements['reconnaissance_needed'] = 2 if operations['reconnaissance_capability'] == 'INSUFFICIENT' else 1
        requirements['priority_types'].append('RECONNAISSANCE')
    
    # Potrzeby supply
    if logistics['resupply_needed'] or operations['logistics_capability'] in ['CRITICAL', 'LIMITED']:
        requirements['supply_needed'] = 2 if operations['logistics_capability'] == 'CRITICAL' else 1
        requirements['priority_types'].append('LOGISTICS')
    
    # Artillery dla wsparcia
    if operations['offensive_capability'] == 'LIMITED' and len(requirements['priority_types']) > 0:
        requirements['artillery_needed'] = 1
        requirements['priority_types'].append('ARTILLERY_SUPPORT')
    
    return requirements

def _prioritize_requirements(requirements: Dict, threats: Dict, operations: Dict) -> Dict[str, int]:
    """Ustaw priorytety potrzeb (1-10, gdzie 10 = najwyższy)."""
    priorities = {}
    
    # Базовые priorytety
    if requirements['supply_needed'] > 0:
        priorities['LOGISTICS'] = 8 if operations['logistics_capability'] == 'CRITICAL' else 6
    
    if requirements['reconnaissance_needed'] > 0:
        priorities['RECONNAISSANCE'] = 7
    
    if requirements['total_cv_needed'] > 0:
        if threats['threat_level'] == 'CRITICAL':
            priorities['COMBAT_REINFORCEMENT'] = 10
        elif threats['threat_level'] == 'HIGH':
            priorities['COMBAT_REINFORCEMENT'] = 8
        else:
            priorities['COMBAT_REINFORCEMENT'] = 5
    
    if requirements['artillery_needed'] > 0:
        priorities['ARTILLERY_SUPPORT'] = 4
    
    return priorities

def _determine_urgency_level(threats: Dict, logistics: Dict, operations: Dict) -> str:
    """Określ poziom pilności (LOW/MEDIUM/HIGH/CRITICAL)."""
    if threats['threat_level'] == 'CRITICAL':
        return 'CRITICAL'
    
    if logistics['fuel_critical_count'] > 2 or operations['logistics_capability'] == 'CRITICAL':
        return 'HIGH'
    
    if threats['threat_level'] == 'HIGH' or logistics['resupply_needed']:
        return 'MEDIUM'
    
    return 'LOW'

def _hex_distance(pos1: Tuple[int, int], pos2: Tuple[int, int]) -> int:
    """Oblicz odległość hex między dwoma pozycjami."""
    q1, r1 = pos1
    q2, r2 = pos2
    return max(abs(q1 - q2), abs(r1 - r2), abs((q1 + r1) - (q2 + r2)))

def _log_force_analysis_csv(analysis: Dict[str, Any]):
    """Log force analysis do CSV."""
    try:
        csv_file = Path("logs/ai_commander/force_analysis.csv")
        csv_file.parent.mkdir(parents=True, exist_ok=True)
        
        file_exists = csv_file.exists()
        
        with open(csv_file, 'a', newline='', encoding='utf-8') as f:
            writer = csv.writer(f)
            
            if not file_exists:
                # Nagłówki
                writer.writerow([
                    'timestamp', 'turn', 'nation', 'urgency_level', 'total_units',
                    'combat_value_total', 'threat_level', 'force_ratio', 'immediate_threats',
                    'fuel_critical', 'fuel_low', 'avg_fuel', 'supply_units',
                    'infantry_needed', 'armor_needed', 'artillery_needed', 'recon_needed', 'supply_needed',
                    'priority_combat', 'priority_logistics', 'priority_recon'
                ])
            
            # Dane
            comp = analysis.get('current_composition', {})
            threats = analysis.get('threat_analysis', {})
            logistics = analysis.get('logistics_status', {})
            req = analysis.get('requirements', {})
            priorities = analysis.get('priorities', {})
            
            writer.writerow([
                analysis.get('analysis_timestamp'),
                analysis.get('turn'),
                analysis.get('nation'),
                analysis.get('urgency'),
                comp.get('total_units', 0),
                comp.get('combat_value_total', 0),
                threats.get('threat_level'),
                round(threats.get('force_ratio', 0), 2),
                threats.get('immediate_threats', 0),
                logistics.get('fuel_critical_count', 0),
                logistics.get('fuel_low_count', 0),
                round(logistics.get('avg_fuel_level', 0), 2),
                logistics.get('supply_units_available', 0),
                req.get('infantry_needed', 0),
                req.get('armor_needed', 0),
                req.get('artillery_needed', 0),
                req.get('reconnaissance_needed', 0),
                req.get('supply_needed', 0),
                priorities.get('COMBAT_REINFORCEMENT', 0),
                priorities.get('LOGISTICS', 0),
                priorities.get('RECONNAISSANCE', 0)
            ])
            
    except Exception as e:
        debug_print(f"[CSV LOG] Błąd zapisu force analysis: {e}", "BASIC", FORCE_LOG)

# =============================================================================
# MODULE 5.2: REINFORCEMENT REQUEST GENERATION (Commander Side)
# =============================================================================

def generate_reinforcement_request(force_requirements: Dict[str, Any], 
                                 urgency_level: str,
                                 commander_id: int,
                                 game_engine) -> Dict[str, Any]:
    """Stwórz structured request o posiłki dla Generała.
    
    Args:
        force_requirements: Output z analyze_force_requirements()
        urgency_level: LOW/MEDIUM/HIGH/CRITICAL
        commander_id: ID dowódcy wysyłającego request
        game_engine: Dla context (turn, nation, etc.)
        
    Returns:
        Structured reinforcement request
    """
    request = {
        'request_id': _generate_request_id(commander_id, game_engine),
        'commander_id': commander_id,
        'nation': get_player_nation(game_engine),
        'turn_created': get_current_turn(game_engine),
        'urgency': urgency_level,
        'status': 'PENDING',
        'created_timestamp': datetime.now().isoformat(),
        
        # Request details
        'force_requirements': force_requirements.get('requirements', {}),
        'priorities': force_requirements.get('priorities', {}),
        'justification': _generate_justification(force_requirements),
        
        # Operational context
        'current_situation': {
            'total_units': force_requirements.get('current_composition', {}).get('total_units', 0),
            'combat_value': force_requirements.get('current_composition', {}).get('combat_value_total', 0),
            'threat_level': force_requirements.get('threat_analysis', {}).get('threat_level', 'UNKNOWN'),
            'force_ratio': force_requirements.get('threat_analysis', {}).get('force_ratio', 0),
            'fuel_status': force_requirements.get('logistics_status', {}).get('avg_fuel_level', 0)
        },
        
        # Specific requests
        'unit_requests': _formulate_unit_requests(force_requirements),
        
        # Processing metadata
        'processed': False,
        'general_response': None,
        'fulfillment_turn': None
    }
    
    debug_print(f"[REQUEST GEN] Utworzono request {request['request_id']} urgency={urgency_level}", "BASIC", REQUEST_LOG)
    
    # Log do CSV
    _log_request_generation_csv(request)
    
    return request

def _generate_request_id(commander_id: int, game_engine) -> str:
    """Generuj unikalny request ID."""
    turn = get_current_turn(game_engine)
    timestamp = int(datetime.now().timestamp())
    return f"REQ_{commander_id}_{turn}_{timestamp % 10000}"

def _generate_justification(force_requirements: Dict[str, Any]) -> str:
    """Generuj tekstową justyfikację dla requestu."""
    justifications = []
    
    threats = force_requirements.get('threat_analysis', {})
    logistics = force_requirements.get('logistics_status', {})
    operations = force_requirements.get('operational_needs', {})
    
    # Threat-based justification
    threat_level = threats.get('threat_level', 'LOW')
    if threat_level in ['HIGH', 'CRITICAL']:
        force_ratio = threats.get('force_ratio', 0)
        justifications.append(f"Zagrożenie {threat_level.lower()}: ratio sił {force_ratio:.2f}")
    
    # Logistics justification
    if logistics.get('resupply_needed'):
        fuel_critical = logistics.get('fuel_critical_count', 0)
        justifications.append(f"Krytyczny stan paliwa: {fuel_critical} jednostek")
    
    # Operational justification
    insufficient_caps = [k for k, v in operations.items() if v in ['INSUFFICIENT', 'CRITICAL']]
    if insufficient_caps:
        justifications.append(f"Niewystarczające: {', '.join(insufficient_caps)}")
    
    return "; ".join(justifications) if justifications else "Wzmocnienie potencjału operacyjnego"

def _formulate_unit_requests(force_requirements: Dict[str, Any]) -> List[Dict[str, Any]]:
    """Sformułuj konkretne requests na jednostki."""
    requests = []
    req = force_requirements.get('requirements', {})
    priorities = force_requirements.get('priorities', {})
    
    # Infantry requests
    if req.get('infantry_needed', 0) > 0:
        requests.append({
            'unit_category': 'INFANTRY',
            'quantity': req['infantry_needed'],
            'preferred_types': ['I', 'IM', 'IR'],
            'priority': priorities.get('COMBAT_REINFORCEMENT', 5),
            'justification': 'Wzmocnienie potencjału bojowego'
        })
    
    # Armor requests  
    if req.get('armor_needed', 0) > 0:
        requests.append({
            'unit_category': 'ARMOR',
            'quantity': req['armor_needed'],
            'preferred_types': ['P', 'PC', 'PT'],
            'priority': priorities.get('COMBAT_REINFORCEMENT', 5),
            'justification': 'Wsparcie pancerne dla operacji'
        })
    
    # Artillery requests
    if req.get('artillery_needed', 0) > 0:
        requests.append({
            'unit_category': 'ARTILLERY',
            'quantity': req['artillery_needed'],
            'preferred_types': ['AL', 'AC', 'AP'],
            'priority': priorities.get('ARTILLERY_SUPPORT', 4),
            'justification': 'Wsparcie artyleryjskie'
        })
    
    # Reconnaissance requests
    if req.get('reconnaissance_needed', 0) > 0:
        requests.append({
            'unit_category': 'RECONNAISSANCE',
            'quantity': req['reconnaissance_needed'],
            'preferred_types': ['K', 'Z_Aufkl'],
            'priority': priorities.get('RECONNAISSANCE', 7),
            'justification': 'Zwiększenie capabilities rozpoznawczych'
        })
    
    # Supply requests
    if req.get('supply_needed', 0) > 0:
        requests.append({
            'unit_category': 'LOGISTICS',
            'quantity': req['supply_needed'],
            'preferred_types': ['Z'],
            'priority': priorities.get('LOGISTICS', 6),
            'justification': 'Wsparcie logistyczne i resupply'
        })
    
    return requests

def _log_request_generation_csv(request: Dict[str, Any]):
    """Log request generation do CSV."""
    try:
        csv_file = Path("logs/ai_commander/reinforcement_requests.csv")
        csv_file.parent.mkdir(parents=True, exist_ok=True)
        
        file_exists = csv_file.exists()
        
        with open(csv_file, 'a', newline='', encoding='utf-8') as f:
            writer = csv.writer(f)
            
            if not file_exists:
                writer.writerow([
                    'timestamp', 'request_id', 'commander_id', 'nation', 'turn',
                    'urgency', 'threat_level', 'force_ratio', 'current_units', 'current_cv',
                    'infantry_req', 'armor_req', 'artillery_req', 'recon_req', 'supply_req',
                    'total_requests', 'justification'
                ])
            
            # Zlicz requests
            unit_reqs = request.get('unit_requests', [])
            infantry_req = sum(r['quantity'] for r in unit_reqs if r['unit_category'] == 'INFANTRY')
            armor_req = sum(r['quantity'] for r in unit_reqs if r['unit_category'] == 'ARMOR')
            artillery_req = sum(r['quantity'] for r in unit_reqs if r['unit_category'] == 'ARTILLERY')
            recon_req = sum(r['quantity'] for r in unit_reqs if r['unit_category'] == 'RECONNAISSANCE')
            supply_req = sum(r['quantity'] for r in unit_reqs if r['unit_category'] == 'LOGISTICS')
            
            situation = request.get('current_situation', {})
            
            writer.writerow([
                request['created_timestamp'],
                request['request_id'],
                request['commander_id'],
                request['nation'],
                request['turn_created'],
                request['urgency'],
                situation.get('threat_level'),
                round(situation.get('force_ratio', 0), 2),
                situation.get('total_units', 0),
                situation.get('combat_value', 0),
                infantry_req, armor_req, artillery_req, recon_req, supply_req,
                len(unit_reqs),
                request['justification']
            ])
            
    except Exception as e:
        debug_print(f"[CSV LOG] Błąd zapisu request: {e}", "BASIC", REQUEST_LOG)

# =============================================================================
# MODULE 5.3: COMMUNICATION CHANNEL (Commander → General)
# =============================================================================

def send_request_to_general(request: Dict[str, Any], game_engine) -> bool:
    """Wyślij request do Generała przez communication channel.
    
    Args:
        request: Reinforcement request dict
        game_engine: For context and data access
        
    Returns:
        True jeśli wysłano, False jeśli błąd
    """
    try:
        # Zapisz request do pliku JSON (komunikacja przez filesystem)
        nation = request['nation'].lower().replace(' ', '_')
        turn = request['turn_created']
        
        requests_file = REQUESTS_DIR / f"commander_requests_{nation}_turn_{turn}.json"
        
        # Wczytaj istniejące requests lub stwórz nową listę
        existing_requests = []
        if requests_file.exists():
            try:
                with open(requests_file, 'r', encoding='utf-8') as f:
                    existing_requests = json.load(f)
            except json.JSONDecodeError:
                existing_requests = []
        
        # Dodaj nowy request
        existing_requests.append(request)
        
        # Zapisz zaktualizowaną listę
        with open(requests_file, 'w', encoding='utf-8') as f:
            json.dump(existing_requests, f, ensure_ascii=False, indent=2)
        
        debug_print(f"[COMM SEND] Wysłano request {request['request_id']} do pliku {requests_file.name}", "BASIC", COMM_LOG)
        
        # Log communication event
        _log_communication_event_csv("REQUEST_SENT", request['commander_id'], request['request_id'], game_engine)
        
        return True
        
    except Exception as e:
        debug_print(f"[COMM SEND] Błąd wysyłania request: {e}", "BASIC", COMM_LOG)
        return False

def _log_communication_event_csv(event_type: str, commander_id: int, request_id: str, game_engine):
    """Log communication events do CSV."""
    try:
        csv_file = Path("logs/ai_general/communication_log.csv")
        csv_file.parent.mkdir(parents=True, exist_ok=True)
        
        file_exists = csv_file.exists()
        
        with open(csv_file, 'a', newline='', encoding='utf-8') as f:
            writer = csv.writer(f)
            
            if not file_exists:
                writer.writerow([
                    'timestamp', 'turn', 'nation', 'event_type', 'commander_id', 
                    'request_id', 'details'
                ])
            
            writer.writerow([
                datetime.now().isoformat(),
                get_current_turn(game_engine),
                get_player_nation(game_engine),
                event_type,
                commander_id,
                request_id,
                f"{event_type} for commander {commander_id}"
            ])
            
    except Exception as e:
        debug_print(f"[CSV LOG] Błąd communication event: {e}", "BASIC", COMM_LOG)

# =============================================================================
# INTEGRATION FUNCTIONS FOR PHASE 4
# =============================================================================

def commander_logistics_analysis(my_units: List[Dict[str, Any]], 
                               game_engine, 
                               commander_id: int,
                               victory_ai_data: Optional[Dict] = None) -> Dict[str, Any]:
    """Main function dla Phase 4 integration w AI Commander.
    
    Args:
        my_units: Lista jednostek dowódcy
        game_engine: Game engine
        commander_id: ID dowódcy
        victory_ai_data: Optional data from Victory AI phases 1-3
        
    Returns:
        Dictionary z analysis results i generated requests
    """
    debug_print(f"[PHASE 4] Commander {commander_id} - rozpoczynam logistics analysis", "BASIC", COMM_LOG)
    
    # 1. Analyze force requirements
    force_analysis = analyze_force_requirements(my_units, game_engine, victory_ai_data)
    
    # 2. Determine if request needed
    urgency = force_analysis.get('urgency', 'LOW')
    requirements = force_analysis.get('requirements', {})
    
    # Generate request tylko jeśli są concrete needs
    request_generated = False
    request_data = None
    
    needs_reinforcement = (
        urgency in ['HIGH', 'CRITICAL'] or
        any(requirements.get(key, 0) > 0 for key in ['infantry_needed', 'armor_needed', 'supply_needed', 'reconnaissance_needed'])
    )
    
    if needs_reinforcement:
        # 3. Generate reinforcement request
        request_data = generate_reinforcement_request(force_analysis, urgency, commander_id, game_engine)
        
        # 4. Send request to General
        if send_request_to_general(request_data, game_engine):
            request_generated = True
            debug_print(f"[PHASE 4] Request {request_data['request_id']} wysłany dla commander {commander_id}", "BASIC", COMM_LOG)
        else:
            debug_print(f"[PHASE 4] Błąd wysyłania request dla commander {commander_id}", "BASIC", COMM_LOG)
    else:
        debug_print(f"[PHASE 4] Commander {commander_id} - brak potrzeby requestów (urgency: {urgency})", "FULL", COMM_LOG)
    
    return {
        'phase': 'LOGISTICS_ANALYSIS_COMPLETE',
        'commander_id': commander_id,
        'force_analysis': force_analysis,
        'request_generated': request_generated,
        'request_data': request_data,
        'needs_reinforcement': needs_reinforcement,
        'analysis_summary': {
            'urgency': urgency,
            'total_requirements': sum(requirements.get(key, 0) for key in ['infantry_needed', 'armor_needed', 'supply_needed', 'reconnaissance_needed', 'artillery_needed']),
            'priority_areas': list(force_analysis.get('priorities', {}).keys())
        }
    }

# Export functions for external use
__all__ = [
    'analyze_force_requirements',
    'generate_reinforcement_request', 
    'send_request_to_general',
    'commander_logistics_analysis'
]
