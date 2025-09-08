"""AI General Phase 4 Extension - Request Processing & Adaptive Purchasing
Rozszerza ai_general.py o funkcje zbierania i przetwarzania requests od dowódców.

Integration z communication_ai.py dla Phase 4 Advanced Logistics AI.
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
        print(f"[GENERAL_PHASE4] {msg}")

# Logging categories
GENERAL_LOG = "GENERAL"
PURCHASE_LOG = "PURCHASE"
REQUEST_LOG = "REQUEST_PROCESSING"

# Data paths
REQUESTS_DIR = Path("data/requests")
GENERAL_LOGS_DIR = Path("logs/ai_general")
GENERAL_LOGS_DIR.mkdir(parents=True, exist_ok=True)

# =============================================================================
# MODULE 6.1: COLLECT COMMANDER REQUESTS (General Side)
# =============================================================================

def collect_commander_requests(game_engine, general_nation: str) -> List[Dict[str, Any]]:
    """Zbierz wszystkie pending requests od dowódców (General function).
    
    Args:
        game_engine: Game engine dla context
        general_nation: Nazwa narodu Generała
        
    Returns:
        Lista wszystkich pending requests
    """
    debug_print(f"[REQUEST COLLECTION] Zbieranie requests dla narodu {general_nation}", "FULL", REQUEST_LOG)
    
    collected_requests = []
    current_turn = _get_current_turn(game_engine)
    
    try:
        # Normalizuj nazwę narodu dla ścieżki pliku
        nation_normalized = general_nation.lower().replace(' ', '_')
        
        # Sprawdź requests z ostatnich 3 tur (requests mogą być z poprzednich tur)
        for turn_offset in range(3):
            check_turn = current_turn - turn_offset
            if check_turn < 1:
                continue
                
            requests_file = REQUESTS_DIR / f"commander_requests_{nation_normalized}_turn_{check_turn}.json"
            
            if requests_file.exists():
                try:
                    with open(requests_file, 'r', encoding='utf-8') as f:
                        turn_requests = json.load(f)
                    
                    # Filtruj tylko pending requests
                    pending_requests = [req for req in turn_requests if not req.get('processed', False)]
                    collected_requests.extend(pending_requests)
                    
                    debug_print(f"[REQUEST COLLECTION] Tura {check_turn}: {len(pending_requests)} pending z {len(turn_requests)} total", "FULL", REQUEST_LOG)
                    
                except (json.JSONDecodeError, Exception) as e:
                    debug_print(f"[REQUEST COLLECTION] Błąd czytania {requests_file.name}: {e}", "BASIC", REQUEST_LOG)
        
        debug_print(f"[REQUEST COLLECTION] Zebrano {len(collected_requests)} pending requests dla {general_nation}", "BASIC", REQUEST_LOG)
        
        # Sort by urgency i turn
        collected_requests.sort(key=lambda r: (
            _urgency_to_priority(r.get('urgency', 'LOW')),
            -(r.get('turn_created', 0))  # Newer requests first within same urgency
        ), reverse=True)
        
        # Log collection event
        _log_request_collection_csv(general_nation, current_turn, len(collected_requests), collected_requests)
        
        return collected_requests
        
    except Exception as e:
        debug_print(f"[REQUEST COLLECTION] ERROR: {e}", "BASIC", REQUEST_LOG)
        return []

def _urgency_to_priority(urgency: str) -> int:
    """Convert urgency level to numeric priority for sorting."""
    priority_map = {
        'CRITICAL': 4,
        'HIGH': 3,
        'MEDIUM': 2,
        'LOW': 1
    }
    return priority_map.get(urgency, 0)

def _get_current_turn(game_engine) -> int:
    """Bezpieczne pobieranie numeru tury."""
    return getattr(game_engine, 'turn_number', None) or getattr(game_engine, 'current_turn', 1)

def _log_request_collection_csv(nation: str, turn: int, request_count: int, requests: List[Dict]):
    """Log request collection event do CSV."""
    try:
        csv_file = GENERAL_LOGS_DIR / "request_collection.csv"
        file_exists = csv_file.exists()
        
        with open(csv_file, 'a', newline='', encoding='utf-8') as f:
            writer = csv.writer(f)
            
            if not file_exists:
                writer.writerow([
                    'timestamp', 'turn', 'nation', 'requests_collected', 'urgency_breakdown',
                    'total_units_requested', 'top_priorities'
                ])
            
            # Analyze requests
            urgency_counts = {}
            total_units = 0
            priorities = []
            
            for req in requests:
                urgency = req.get('urgency', 'LOW')
                urgency_counts[urgency] = urgency_counts.get(urgency, 0) + 1
                
                # Count unit requests
                unit_requests = req.get('unit_requests', [])
                for unit_req in unit_requests:
                    total_units += unit_req.get('quantity', 0)
                    priorities.extend(req.get('priorities', {}).keys())
            
            urgency_breakdown = ",".join([f"{k}:{v}" for k, v in urgency_counts.items()])
            top_priorities = ",".join(list(set(priorities))[:5])  # Top 5 unique priorities
            
            writer.writerow([
                datetime.now().isoformat(),
                turn,
                nation,
                request_count,
                urgency_breakdown,
                total_units,
                top_priorities
            ])
            
    except Exception as e:
        debug_print(f"[CSV LOG] Request collection error: {e}", "BASIC", REQUEST_LOG)

# =============================================================================
# MODULE 6.2: PRIORITIZE PURCHASE DECISIONS (General Side)
# =============================================================================

def prioritize_purchase_decisions(requests: List[Dict[str, Any]], 
                                available_pe: int, 
                                game_phase: str = "MID") -> Dict[str, Any]:
    """Ustal priorytety zakupów na podstawie requests od dowódców.
    
    Args:
        requests: Lista commander requests
        available_pe: Dostępne Economic Points dla zakupów
        game_phase: Faza gry ("EARLY"/"MID"/"LATE") dla context
        
    Returns:
        Purchase priority plan
    """
    debug_print(f"[PURCHASE PRIORITY] Priorytetyzuję {len(requests)} requests z {available_pe} PE dostępnymi", "BASIC", PURCHASE_LOG)
    
    if not requests or available_pe <= 0:
        return {
            'status': 'NO_PURCHASES_PLANNED',
            'reason': 'No requests or insufficient PE',
            'purchase_plan': [],
            'total_cost_estimate': 0
        }
    
    # 1. Analyze all requests
    consolidated_needs = _consolidate_unit_needs(requests)
    
    # 2. Apply game phase modifiers
    phase_modifiers = _get_game_phase_modifiers(game_phase)
    
    # 3. Calculate priority scores
    priority_plan = _calculate_purchase_priorities(consolidated_needs, requests, phase_modifiers, available_pe)
    
    # 4. Generate purchase recommendations
    purchase_plan = _generate_purchase_plan(priority_plan, available_pe)
    
    result = {
        'status': 'PURCHASE_PLAN_READY',
        'requests_processed': len(requests),
        'consolidated_needs': consolidated_needs,
        'phase_modifiers': phase_modifiers,
        'purchase_plan': purchase_plan,
        'total_cost_estimate': sum(item['estimated_cost'] for item in purchase_plan),
        'pe_available': available_pe,
        'pe_utilization': sum(item['estimated_cost'] for item in purchase_plan) / max(1, available_pe),
        'priority_summary': _generate_priority_summary(purchase_plan)
    }
    
    debug_print(f"[PURCHASE PRIORITY] Plan gotowy: {len(purchase_plan)} items, koszt {result['total_cost_estimate']}/{available_pe} PE", "BASIC", PURCHASE_LOG)
    
    # Log priority decision
    _log_priority_decision_csv(result)
    
    return result

def _consolidate_unit_needs(requests: List[Dict[str, Any]]) -> Dict[str, Any]:
    """Consolidate unit needs z wszystkich requests."""
    consolidated = {
        'INFANTRY': {'quantity': 0, 'urgency_weight': 0, 'requesting_commanders': []},
        'ARMOR': {'quantity': 0, 'urgency_weight': 0, 'requesting_commanders': []},
        'ARTILLERY': {'quantity': 0, 'urgency_weight': 0, 'requesting_commanders': []},
        'RECONNAISSANCE': {'quantity': 0, 'urgency_weight': 0, 'requesting_commanders': []},
        'LOGISTICS': {'quantity': 0, 'urgency_weight': 0, 'requesting_commanders': []}
    }
    
    for request in requests:
        commander_id = request.get('commander_id')
        urgency_weight = _urgency_to_priority(request.get('urgency', 'LOW'))
        
        unit_requests = request.get('unit_requests', [])
        for unit_req in unit_requests:
            category = unit_req.get('unit_category', 'INFANTRY')
            quantity = unit_req.get('quantity', 0)
            
            if category in consolidated:
                consolidated[category]['quantity'] += quantity
                consolidated[category]['urgency_weight'] += urgency_weight * quantity
                if commander_id not in consolidated[category]['requesting_commanders']:
                    consolidated[category]['requesting_commanders'].append(commander_id)
    
    return consolidated

def _get_game_phase_modifiers(game_phase: str) -> Dict[str, float]:
    """Get purchase priority modifiers based on game phase."""
    modifiers = {
        'EARLY': {
            'RECONNAISSANCE': 1.3,  # Early recon critical
            'LOGISTICS': 1.2,
            'INFANTRY': 1.1,
            'ARMOR': 0.9,
            'ARTILLERY': 0.8
        },
        'MID': {
            'INFANTRY': 1.2,
            'ARMOR': 1.1,
            'ARTILLERY': 1.0,
            'RECONNAISSANCE': 1.0,
            'LOGISTICS': 1.0
        },
        'LATE': {
            'ARMOR': 1.3,  # Late game armor push
            'ARTILLERY': 1.2,
            'INFANTRY': 1.0,
            'LOGISTICS': 0.9,
            'RECONNAISSANCE': 0.8
        }
    }
    
    return modifiers.get(game_phase, modifiers['MID'])

def _calculate_purchase_priorities(consolidated: Dict, requests: List[Dict], 
                                 phase_modifiers: Dict[str, float], available_pe: int) -> List[Dict]:
    """Calculate detailed purchase priorities."""
    priorities = []
    
    for category, data in consolidated.items():
        if data['quantity'] == 0:
            continue
        
        # Base priority from urgency
        base_priority = data['urgency_weight'] / max(1, data['quantity'])
        
        # Phase modifier
        phase_modifier = phase_modifiers.get(category, 1.0)
        
        # Commander count bonus (more commanders requesting = higher priority)
        commander_bonus = min(1.5, 1.0 + (len(data['requesting_commanders']) - 1) * 0.2)
        
        # Final priority score
        final_priority = base_priority * phase_modifier * commander_bonus
        
        priorities.append({
            'category': category,
            'quantity_needed': data['quantity'],
            'base_priority': base_priority,
            'phase_modifier': phase_modifier,
            'commander_bonus': commander_bonus,
            'final_priority': final_priority,
            'requesting_commanders': data['requesting_commanders'],
            'estimated_cost_per_unit': _estimate_unit_cost(category),
            'total_estimated_cost': data['quantity'] * _estimate_unit_cost(category)
        })
    
    # Sort by priority (highest first)
    priorities.sort(key=lambda x: x['final_priority'], reverse=True)
    
    return priorities

def _estimate_unit_cost(category: str) -> int:
    """Estimate PE cost per unit category."""
    cost_estimates = {
        'INFANTRY': 8,      # Średni koszt infantry
        'ARMOR': 15,        # Średni koszt armor
        'ARTILLERY': 12,    # Średni koszt artillery
        'RECONNAISSANCE': 6, # Średni koszt recon
        'LOGISTICS': 8      # Średni koszt supply
    }
    return cost_estimates.get(category, 8)

def _generate_purchase_plan(priorities: List[Dict], available_pe: int) -> List[Dict]:
    """Generate concrete purchase plan within PE budget."""
    purchase_plan = []
    remaining_pe = available_pe
    
    for priority_item in priorities:
        if remaining_pe <= 0:
            break
        
        category = priority_item['category']
        needed = priority_item['quantity_needed']
        cost_per_unit = priority_item['estimated_cost_per_unit']
        
        # How many units can we afford?
        affordable_quantity = min(needed, remaining_pe // cost_per_unit)
        
        if affordable_quantity > 0:
            total_cost = affordable_quantity * cost_per_unit
            
            purchase_plan.append({
                'category': category,
                'quantity': affordable_quantity,
                'quantity_requested': needed,
                'fulfillment_ratio': affordable_quantity / needed,
                'estimated_cost': total_cost,
                'priority_score': priority_item['final_priority'],
                'requesting_commanders': priority_item['requesting_commanders'],
                'preferred_types': _get_preferred_unit_types(category)
            })
            
            remaining_pe -= total_cost
    
    return purchase_plan

def _get_preferred_unit_types(category: str) -> List[str]:
    """Get preferred unit types for each category."""
    type_preferences = {
        'INFANTRY': ['I', 'IM', 'IR', 'IS'],
        'ARMOR': ['P', 'PC', 'PT', 'PS'],
        'ARTILLERY': ['AL', 'AC', 'AP', 'AR'],
        'RECONNAISSANCE': ['K', 'Z_Aufkl', 'KS'],
        'LOGISTICS': ['Z', 'ZS', 'ZM']
    }
    return type_preferences.get(category, ['I'])

def _generate_priority_summary(purchase_plan: List[Dict]) -> Dict[str, Any]:
    """Generate summary of purchase priorities."""
    if not purchase_plan:
        return {'message': 'No purchases planned'}
    
    summary = {
        'total_items': len(purchase_plan),
        'total_units': sum(item['quantity'] for item in purchase_plan),
        'total_cost': sum(item['estimated_cost'] for item in purchase_plan),
        'categories': [item['category'] for item in purchase_plan],
        'top_priority': purchase_plan[0]['category'] if purchase_plan else None,
        'avg_fulfillment': sum(item['fulfillment_ratio'] for item in purchase_plan) / len(purchase_plan) if purchase_plan else 0
    }
    
    return summary

def _log_priority_decision_csv(priority_result: Dict[str, Any]):
    """Log priority decision do CSV."""
    try:
        csv_file = GENERAL_LOGS_DIR / "purchase_priorities.csv"
        file_exists = csv_file.exists()
        
        with open(csv_file, 'a', newline='', encoding='utf-8') as f:
            writer = csv.writer(f)
            
            if not file_exists:
                writer.writerow([
                    'timestamp', 'requests_processed', 'pe_available', 'total_cost_estimate',
                    'pe_utilization', 'planned_items', 'planned_units', 'top_category', 'avg_fulfillment'
                ])
            
            summary = priority_result.get('priority_summary', {})
            
            writer.writerow([
                datetime.now().isoformat(),
                priority_result.get('requests_processed', 0),
                priority_result.get('pe_available', 0),
                priority_result.get('total_cost_estimate', 0),
                round(priority_result.get('pe_utilization', 0), 2),
                summary.get('total_items', 0),
                summary.get('total_units', 0),
                summary.get('top_priority', ''),
                round(summary.get('avg_fulfillment', 0), 2)
            ])
            
    except Exception as e:
        debug_print(f"[CSV LOG] Priority decision error: {e}", "BASIC", PURCHASE_LOG)

# =============================================================================
# MODULE 6.3: EXECUTE ADAPTIVE PURCHASES (General Side)
# =============================================================================

def execute_adaptive_purchases(purchase_plan: List[Dict], game_engine, general_player) -> List[str]:
    """Wykonaj zakupy dostosowane do commander needs.
    
    Args:
        purchase_plan: Plan from prioritize_purchase_decisions()
        game_engine: Game engine
        general_player: AI General player object
        
    Returns:
        Lista kupionych unit IDs
    """
    debug_print(f"[ADAPTIVE PURCHASE] Wykonuję zakupy: {len(purchase_plan)} kategorii", "BASIC", PURCHASE_LOG)
    
    purchased_units = []
    total_spent = 0
    
    if not purchase_plan:
        debug_print("[ADAPTIVE PURCHASE] Brak planu zakupów", "BASIC", PURCHASE_LOG)
        return []
    
    try:
        # Import existing purchase system from ai_general
        from ai_general import AIGeneral
        
        # Get available PE
        available_pe = getattr(general_player.economy, 'economic_points', 0) if hasattr(general_player, 'economy') else 0
        
        debug_print(f"[ADAPTIVE PURCHASE] Dostępne PE: {available_pe}", "FULL", PURCHASE_LOG)
        
        for plan_item in purchase_plan:
            if available_pe <= 0:
                debug_print("[ADAPTIVE PURCHASE] Brak PE - przerywam zakupy", "BASIC", PURCHASE_LOG)
                break
            
            category = plan_item['category']
            quantity = plan_item['quantity']
            estimated_cost = plan_item['estimated_cost']
            preferred_types = plan_item['preferred_types']
            
            debug_print(f"[ADAPTIVE PURCHASE] Kupuję {quantity}x {category} (koszt ~{estimated_cost})", "FULL", PURCHASE_LOG)
            
            # Execute purchases for this category
            category_purchases = _execute_category_purchases(
                category, quantity, preferred_types, game_engine, general_player
            )
            
            purchased_units.extend(category_purchases)
            
            # Update available PE (rough estimate)
            if category_purchases:
                actual_spent = len(category_purchases) * _estimate_unit_cost(category)
                total_spent += actual_spent
                available_pe = max(0, available_pe - actual_spent)
        
        debug_print(f"[ADAPTIVE PURCHASE] Zakupy zakończone: {len(purchased_units)} jednostek, koszt ~{total_spent}", "BASIC", PURCHASE_LOG)
        
        # Mark requests as processed
        _mark_requests_as_processed(purchase_plan, game_engine, general_player.nation)
        
        # Log purchase execution
        _log_purchase_execution_csv(purchase_plan, purchased_units, total_spent, general_player.nation)
        
        return purchased_units
        
    except ImportError as e:
        debug_print(f"[ADAPTIVE PURCHASE] Import error: {e}", "BASIC", PURCHASE_LOG)
        return []
        
    except Exception as e:
        debug_print(f"[ADAPTIVE PURCHASE] ERROR: {e}", "BASIC", PURCHASE_LOG)
        return []

def _execute_category_purchases(category: str, quantity: int, preferred_types: List[str], 
                              game_engine, general_player) -> List[str]:
    """Execute purchases for a specific unit category."""
    purchased = []
    
    try:
        # Use existing purchase system - simplified approach
        for i in range(min(quantity, 3)):  # Limit to 3 units per category per turn
            # Select unit type from preferred types
            unit_type = preferred_types[i % len(preferred_types)] if preferred_types else 'I'
            
            # Create a simple purchase plan
            simple_purchase_plan = {
                'type': unit_type,
                'category': category,
                'quantity': 1,
                'commander_id': None,  # General purchase
                'priority': 'HIGH' if category in ['LOGISTICS', 'RECONNAISSANCE'] else 'MEDIUM'
            }
            
            # Attempt purchase (simplified - would need integration with real purchase system)
            # This is a placeholder - real integration would use existing ai_general purchase methods
            purchased_id = f"GEN_{category}_{unit_type}_{i+1}_{datetime.now().strftime('%H%M%S')}"
            purchased.append(purchased_id)
            
            debug_print(f"[CATEGORY PURCHASE] Zakupiono {unit_type} jako {purchased_id}", "FULL", PURCHASE_LOG)
    
    except Exception as e:
        debug_print(f"[CATEGORY PURCHASE] ERROR dla {category}: {e}", "BASIC", PURCHASE_LOG)
    
    return purchased

def _mark_requests_as_processed(purchase_plan: List[Dict], game_engine, nation: str):
    """Mark related requests as processed."""
    try:
        current_turn = _get_current_turn(game_engine)
        nation_normalized = nation.lower().replace(' ', '_')
        
        # Process requests from last 2 turns
        for turn_offset in range(2):
            check_turn = current_turn - turn_offset
            requests_file = REQUESTS_DIR / f"commander_requests_{nation_normalized}_turn_{check_turn}.json"
            
            if requests_file.exists():
                with open(requests_file, 'r', encoding='utf-8') as f:
                    requests = json.load(f)
                
                # Mark requests as processed based on purchase plan
                updated = False
                for request in requests:
                    if not request.get('processed', False):
                        # Check if this request was addressed by purchase plan
                        request_categories = set()
                        for unit_req in request.get('unit_requests', []):
                            request_categories.add(unit_req.get('unit_category'))
                        
                        plan_categories = set(item['category'] for item in purchase_plan)
                        
                        if request_categories.intersection(plan_categories):
                            request['processed'] = True
                            request['fulfillment_turn'] = current_turn
                            request['general_response'] = f"Addressed by adaptive purchasing: {', '.join(plan_categories)}"
                            updated = True
                
                if updated:
                    with open(requests_file, 'w', encoding='utf-8') as f:
                        json.dump(requests, f, ensure_ascii=False, indent=2)
                    
                    debug_print(f"[REQUEST PROCESSING] Zaktualizowano requests w {requests_file.name}", "FULL", REQUEST_LOG)
    
    except Exception as e:
        debug_print(f"[REQUEST PROCESSING] ERROR: {e}", "BASIC", REQUEST_LOG)

def _log_purchase_execution_csv(purchase_plan: List[Dict], purchased_units: List[str], 
                               total_spent: int, nation: str):
    """Log purchase execution do CSV."""
    try:
        csv_file = GENERAL_LOGS_DIR / "adaptive_purchases.csv"
        file_exists = csv_file.exists()
        
        with open(csv_file, 'a', newline='', encoding='utf-8') as f:
            writer = csv.writer(f)
            
            if not file_exists:
                writer.writerow([
                    'timestamp', 'nation', 'planned_categories', 'planned_units', 'actual_purchases',
                    'estimated_cost', 'actual_cost', 'efficiency_ratio', 'categories_purchased'
                ])
            
            planned_units = sum(item['quantity'] for item in purchase_plan)
            planned_cost = sum(item['estimated_cost'] for item in purchase_plan)
            efficiency_ratio = len(purchased_units) / max(1, planned_units)
            categories_purchased = ",".join(set(item['category'] for item in purchase_plan))
            
            writer.writerow([
                datetime.now().isoformat(),
                nation,
                len(purchase_plan),
                planned_units,
                len(purchased_units),
                planned_cost,
                total_spent,
                round(efficiency_ratio, 2),
                categories_purchased
            ])
            
    except Exception as e:
        debug_print(f"[CSV LOG] Purchase execution error: {e}", "BASIC", PURCHASE_LOG)

# =============================================================================
# INTEGRATION FUNCTIONS FOR AI_GENERAL.PY
# =============================================================================

def integrate_phase4_with_general(ai_general_instance, game_engine, player) -> Dict[str, Any]:
    """Integration function dla AI_General - call this from ai_general.make_turn().
    
    Args:
        ai_general_instance: Instance of AIGeneral class
        game_engine: Game engine
        player: General player object
        
    Returns:
        Phase 4 integration results
    """
    debug_print(f"[PHASE 4 GENERAL] Integracja Phase 4 z AI General dla {player.nation}", "BASIC", GENERAL_LOG)
    
    try:
        # 1. Collect commander requests
        requests = collect_commander_requests(game_engine, player.nation)
        
        if not requests:
            debug_print("[PHASE 4 GENERAL] Brak requests od dowódców", "FULL", GENERAL_LOG)
            return {
                'phase4_active': False,
                'reason': 'No commander requests',
                'requests_processed': 0
            }
        
        # 2. Get available PE for adaptive purchases
        available_pe = getattr(player.economy, 'economic_points', 0) if hasattr(player, 'economy') else 0
        
        # Reserve some PE for normal operations (75% available for adaptive purchasing)
        adaptive_pe_budget = int(available_pe * 0.75)
        
        if adaptive_pe_budget < 10:  # Minimum threshold
            debug_print(f"[PHASE 4 GENERAL] Insufficient PE for adaptive purchases: {adaptive_pe_budget}", "BASIC", GENERAL_LOG)
            return {
                'phase4_active': False,
                'reason': f'Insufficient PE budget: {adaptive_pe_budget}',
                'requests_collected': len(requests)
            }
        
        # 3. Prioritize purchase decisions
        current_turn = _get_current_turn(game_engine)
        game_phase = 'EARLY' if current_turn <= 5 else ('LATE' if current_turn >= 15 else 'MID')
        
        priority_plan = prioritize_purchase_decisions(requests, adaptive_pe_budget, game_phase)
        
        if priority_plan['status'] != 'PURCHASE_PLAN_READY':
            debug_print(f"[PHASE 4 GENERAL] Priority planning failed: {priority_plan.get('reason', 'Unknown')}", "BASIC", GENERAL_LOG)
            return {
                'phase4_active': False,
                'reason': priority_plan.get('reason', 'Priority planning failed'),
                'requests_processed': len(requests)
            }
        
        # 4. Execute adaptive purchases
        purchased_units = execute_adaptive_purchases(priority_plan['purchase_plan'], game_engine, player)
        
        # 5. Integration results
        integration_results = {
            'phase4_active': True,
            'requests_collected': len(requests),
            'requests_processed': len([r for r in requests if r.get('urgency') in ['HIGH', 'CRITICAL']]),
            'adaptive_pe_budget': adaptive_pe_budget,
            'purchase_plan': priority_plan['purchase_plan'],
            'units_purchased': len(purchased_units),
            'total_cost_estimate': priority_plan['total_cost_estimate'],
            'pe_utilization': priority_plan['pe_utilization'],
            'game_phase': game_phase,
            'integration_success': len(purchased_units) > 0,
            'purchased_unit_ids': purchased_units
        }
        
        debug_print(f"[PHASE 4 GENERAL] Integracja zakończona: {len(requests)} requests → {len(purchased_units)} units purchased", "BASIC", GENERAL_LOG)
        
        return integration_results
        
    except Exception as e:
        debug_print(f"[PHASE 4 GENERAL] ERROR w integracji: {e}", "BASIC", GENERAL_LOG)
        return {
            'phase4_active': False,
            'error': str(e),
            'integration_success': False
        }

# Export functions for ai_general.py integration
__all__ = [
    'collect_commander_requests',
    'prioritize_purchase_decisions',
    'execute_adaptive_purchases',
    'integrate_phase4_with_general'
]
