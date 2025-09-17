"""Moduł ekonomii i zakupów AI.
Wydzielony z ai_commander: optimize_budget, adaptive_purchase_ai oraz funkcje pomocnicze.

NOWE: Priorytetyzacja jednostek Zaopatrzenia (Z) - jedynych zbierających PE.
"""
from __future__ import annotations
from typing import Any, List, Dict
from ai.logowanie_ai import log_commander_action
from ai.ai_config import get_param

# Import dla logowania ekonomicznego
try:
    from utils.session_manager import SessionManager
    from utils.ai_commander_logger_zaawansowany import ZaawansowanyLoggerAI
    ADVANCED_LOGGING_AVAILABLE = True
except ImportError:
    ADVANCED_LOGGING_AVAILABLE = False

__all__ = [
    'optimize_budget','adaptive_purchase_ai','get_unit_type_priority_multiplier', 'log_economic_decision'
]

def get_unit_type_priority_multiplier(unit_type):
    """Zwraca mnożnik priorytetu dla różnych typów jednostek.
    NOWE: Jednostki Z (Zaopatrzenie) mają zwiększony priorytet jako jedyne zbierające PE.
    """
    priorities = get_param('ECONOMY.UNIT_TYPE_PRIORITIES', {})
    return priorities.get(unit_type, 1.0)

def log_economic_decision(commander, decision_type: str, decision_data: Dict[str, Any]):
    """Loguje decyzje ekonomiczne AI"""
    if not ADVANCED_LOGGING_AVAILABLE:
        return
    
    try:
        session_manager = SessionManager()
        katalog_sesji = session_manager.get_current_session_dir()
        logger = ZaawansowanyLoggerAI(katalog_sesji)
        
        # Przygotowanie danych ekonomicznych
        economic_log_data = {
            'decision_type': decision_type,
            'nation': getattr(commander.player, 'nation', 'Unknown'),
            'available_budget': decision_data.get('available_budget', 0),
            'allocated_budget': decision_data.get('allocated_budget', 0),
            'expense_category': decision_data.get('expense_category', 'GENERAL'),
            'expected_return': decision_data.get('expected_return', 0),
            'opportunity_cost': decision_data.get('opportunity_cost', 0),
            'budget_pressure': decision_data.get('budget_pressure', 'MEDIUM'),
            'pe_efficiency': decision_data.get('pe_efficiency', 1.0),
            'resource_shortage': decision_data.get('resource_shortage', False),
            'emergency_expenses': decision_data.get('emergency_expenses', False),
            'investment_horizon': decision_data.get('investment_horizon', 'SHORT_TERM'),
            'cost_benefit_analysis': decision_data.get('cost_benefit_analysis', 'N/A'),
            'budget_deviation': decision_data.get('budget_deviation', 0),
            'economic_strategy_alignment': decision_data.get('economic_strategy_alignment', 'ALIGNED')
        }
        
        logger.loguj_decyzje_ekonomiczna(economic_log_data)
    except Exception as e:
        print(f"[LOG] Błąd logowania decyzji ekonomicznej: {e}")

def optimize_budget(commander, game_engine):
    try:
        if hasattr(commander.player, 'economy') and commander.player.economy:
            current_budget = commander.player.economy.economic_points
        else:
            current_budget = getattr(commander.player, 'punkty_ekonomiczne', 0)
        my_units = get_my_units(game_engine, commander.player.id)
        total_units = len(my_units)
        units_needing_resupply = 0
        total_resupply_cost = 0
        for unit in my_units:
            token = unit.get('token')
            if not token:
                continue
            current_fuel = getattr(token, 'currentFuel', 0)
            max_fuel = getattr(token, 'maxFuel', token.stats.get('maintenance', 0))
            fuel_needed = max(0, max_fuel - current_fuel)
            current_combat = getattr(token, 'combat_value', 0)
            max_combat = token.stats.get('combat_value', 0)
            combat_needed = max(0, max_combat - current_combat)
            unit_cost = fuel_needed + combat_needed
            if unit_cost > 0:
                units_needing_resupply += 1
                total_resupply_cost += unit_cost
        
        # Pobierz parametry konfiguracyjne
        thresholds = get_param('ECONOMY.ALLOCATION_THRESHOLDS', {})
        allocations = get_param('ECONOMY.BUDGET_ALLOCATIONS', {})
        
        small_army_size = thresholds.get('SMALL_ARMY_SIZE', 5)
        high_resupply_ratio = thresholds.get('HIGH_RESUPPLY_RATIO', 0.7)
        
        if total_units < small_army_size:
            allocation = allocations.get('SMALL_ARMY', {"allocate":0.3, "purchase":0.6, "reserve":0.1})
            reason = "Mała armia - priorytet nowe jednostki"
        elif units_needing_resupply > total_units * high_resupply_ratio:
            allocation = allocations.get('HIGH_RESUPPLY', {"allocate":0.8, "purchase":0.1, "reserve":0.1})
            reason = "Masowe potrzeby resupply"
        elif getattr(commander,'consecutive_losing_turns',0) >= 3:
            allocation = {"allocate":0.2, "purchase":0.7, "reserve":0.1}
            reason = "Desperacka sytuacja - wszystko w nowe jednostki"
        else:
            allocation = getattr(commander,'budget_allocation', allocations.get('BALANCED', {"allocate":0.5,"purchase":0.4,"reserve":0.1})).copy()
            reason = f"Strategia {getattr(commander,'strategic_state','TIED')}"
        allocate_amount = int(current_budget * allocation['allocate'])
        purchase_amount = int(current_budget * allocation['purchase'])
        reserve_amount = current_budget - allocate_amount - purchase_amount
        plan = {
            'total': current_budget,
            'allocate': allocate_amount,
            'purchase': purchase_amount,
            'reserve': reserve_amount,
            'allocation_ratios': allocation,
            'reason': reason,
            'units_count': total_units,
            'resupply_needed': units_needing_resupply,
            'estimated_resupply_cost': total_resupply_cost
        }
        
        # LOGOWANIE DECYZJI BUDŻETOWEJ
        budget_pressure = 'HIGH' if current_budget < total_resupply_cost else 'MEDIUM' if current_budget < total_resupply_cost * 2 else 'LOW'
        pe_efficiency = purchase_amount / current_budget if current_budget > 0 else 0
        
        log_economic_decision(commander, 'BUDGET_OPTIMIZATION', {
            'available_budget': current_budget,
            'allocated_budget': allocate_amount,
            'expense_category': 'MIXED_ALLOCATION',
            'expected_return': purchase_amount * 1.2,  # Przewidywany zwrot z nowych jednostek
            'opportunity_cost': reserve_amount,  # Koszt alternatywny to rezerwa
            'budget_pressure': budget_pressure,
            'pe_efficiency': pe_efficiency,
            'resource_shortage': total_resupply_cost > current_budget,
            'emergency_expenses': units_needing_resupply > total_units * 0.7,
            'investment_horizon': 'MEDIUM_TERM',
            'cost_benefit_analysis': f"Ratio: {allocation}",
            'budget_deviation': abs(allocate_amount - purchase_amount),
            'economic_strategy_alignment': 'ALIGNED' if reason != 'ERROR' else 'MISALIGNED'
        })
        
        print(f"💰 [BUDGET] {reason}: {allocate_amount}zł resupply, {purchase_amount}zł zakupy, {reserve_amount}zł rezerwa")
        return plan
    except Exception as e:
        print(f"❌ [BUDGET] Błąd optymalizacji: {e}")
        return {'total':0,'allocate':0,'purchase':0,'reserve':0,'reason':'ERROR'}

def adaptive_purchase_ai(commander, game_engine, budget_plan):
    try:
        purchase_budget = budget_plan.get('purchase',0)
        if purchase_budget <=0:
            return []
        my_units = get_my_units(game_engine, commander.player.id)
        unit_types = {}
        total_combat_value = 0
        for unit in my_units:
            token = unit.get('token')
            if not token:
                continue
            unit_type = getattr(token,'unit_type', getattr(token,'type','unknown'))
            unit_types[unit_type] = unit_types.get(unit_type,0)+1
            total_combat_value += unit.get('cv',0)
        purchase_priority = commander._determine_purchase_priority() if hasattr(commander,'_determine_purchase_priority') else {}
        available_units = commander._get_available_purchase_options(game_engine) if hasattr(commander,'_get_available_purchase_options') else []
        recommendations = []
        for unit_opt in available_units:
            cost = unit_opt.get('cost',0)
            if cost <=0 or cost > purchase_budget:
                continue
            utype = unit_opt.get('type','unknown')
            priority = purchase_priority.get(utype,1)
            # NOWE: Zastosuj mnożnik priorytetu dla typu jednostki
            type_multiplier = get_unit_type_priority_multiplier(utype)
            priority *= type_multiplier
            
            need = 1.0 / (1+unit_types.get(utype,0))
            score = priority * need
            recommendations.append({**unit_opt,'score':score, 'type_priority':type_multiplier})
        recommendations.sort(key=lambda x: x.get('score',0), reverse=True)
        selected = []
        remaining = purchase_budget
        for rec in recommendations:
            if rec['cost'] <= remaining:
                selected.append(rec)
                remaining -= rec['cost']
        print(f"🛒 [PURCHASE] Rekomendacje: {[r['type'] for r in selected]}")
        
        # LOGOWANIE DECYZJI ZAKUPOWYCH
        total_spent = sum(r['cost'] for r in selected)
        log_economic_decision(commander, 'UNIT_PURCHASE', {
            'available_budget': purchase_budget,
            'allocated_budget': total_spent,
            'expense_category': 'UNIT_PURCHASES',
            'expected_return': sum(r.get('score', 0) for r in selected),
            'opportunity_cost': remaining,  # Niewykorzsytany budżet
            'budget_pressure': 'LOW' if remaining > purchase_budget * 0.3 else 'MEDIUM',
            'pe_efficiency': total_spent / purchase_budget if purchase_budget > 0 else 0,
            'resource_shortage': len(selected) < len(recommendations),
            'emergency_expenses': False,
            'investment_horizon': 'SHORT_TERM',
            'cost_benefit_analysis': f"Selected {len(selected)}/{len(recommendations)} options",
            'budget_deviation': purchase_budget - total_spent,
            'economic_strategy_alignment': 'ALIGNED'
        })
        
        return selected
    except Exception as e:
        print(f"❌ [PURCHASE] Błąd zakupów: {e}")
        return []

# Wymagane funkcje pomocnicze importujemy lokalnie aby uniknąć cykli
try:
    from ai.ai_commander import get_my_units  # circular safe at runtime gdy moduł już załadowany
except Exception:
    def get_my_units(game_engine, player_id):
        return []
