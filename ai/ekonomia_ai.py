"""Moduł ekonomii i zakupów AI.
Wydzielony z ai_commander: optimize_budget, adaptive_purchase_ai oraz funkcje pomocnicze.
"""
from __future__ import annotations
from typing import Any, List, Dict
from ai.logowanie_ai import log_commander_action

__all__ = [
    'optimize_budget','adaptive_purchase_ai'
]

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
        if total_units < 5:
            allocation = {"allocate":0.3, "purchase":0.6, "reserve":0.1}
            reason = "Mała armia - priorytet nowe jednostki"
        elif units_needing_resupply > total_units * 0.7:
            allocation = {"allocate":0.8, "purchase":0.1, "reserve":0.1}
            reason = "Masowe potrzeby resupply"
        elif getattr(commander,'consecutive_losing_turns',0) >= 3:
            allocation = {"allocate":0.2, "purchase":0.7, "reserve":0.1}
            reason = "Desperacka sytuacja - wszystko w nowe jednostki"
        else:
            allocation = getattr(commander,'budget_allocation',{"allocate":0.5,"purchase":0.4,"reserve":0.1}).copy()
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
            need = 1.0 / (1+unit_types.get(utype,0))
            score = priority * need
            recommendations.append({**unit_opt,'score':score})
        recommendations.sort(key=lambda x: x.get('score',0), reverse=True)
        selected = []
        remaining = purchase_budget
        for rec in recommendations:
            if rec['cost'] <= remaining:
                selected.append(rec)
                remaining -= rec['cost']
        print(f"🛒 [PURCHASE] Rekomendacje: {[r['type'] for r in selected]}")
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
