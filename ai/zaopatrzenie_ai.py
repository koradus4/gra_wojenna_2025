"""Moduł zaopatrzenia / resupply AI.
Wydzielony z AICommander: pre_resupply, tactical_resupply oraz logika _perform_resupply.
"""
from __future__ import annotations
from typing import Any
import math
from .logowanie_ai import log_commander_action
from .wybor_celow import find_target
from .ruch_jednostek import move_towards

def _assess_tactical_situation(commander, game_engine):
    """
    Ocena sytuacji taktycznej dla dynamicznej alokacji budżetu.
    
    DEFINICJE STANÓW:
    - SPOKÓJ: force_ratio >= 1.5, brak immediate_threats, średnie paliwo > 70%
    - WOJNA: force_ratio 0.8-1.5, lub immediate_threats > 0, paliwo 40-70%
    - KRYZYS: force_ratio < 0.8, lub immediate_threats > 2, paliwo < 40%
    """
    try:
        from ai.communication_ai import _analyze_tactical_threats
        
        # Zbierz jednostki dowódcy
        player = getattr(commander, 'player', commander)
        expected_owner = f"{getattr(player,'id',0)} ({getattr(player,'nation','?')})"
        my_units = []
        
        if hasattr(game_engine, 'board') and hasattr(game_engine.board, 'tokens'):
            for token in game_engine.board.tokens:
                if getattr(token, 'owner', '') == expected_owner:
                    my_units.append({
                        'id': getattr(token, 'id', 'unknown'),
                        'position': (getattr(token, 'q', 0), getattr(token, 'r', 0)),
                        'attack_val': token.stats.get('attack', {}).get('value', 0),
                        'defense_val': token.stats.get('defense_value', 0),
                        'fuel_pct': getattr(token, 'currentFuel', 0) / max(getattr(token, 'maxFuel', 1), 1)
                    })
        
        if not my_units:
            return "SPOKÓJ"  # Brak jednostek = bezpieczna sytuacja
        
        # Analiza zagrożeń
        threats = _analyze_tactical_threats(my_units, game_engine)
        force_ratio = threats.get('force_ratio', float('inf'))
        immediate_threats = threats.get('immediate_threats', 0)
        
        # Średni poziom paliwa
        avg_fuel = sum(u['fuel_pct'] for u in my_units) / len(my_units) if my_units else 1.0
        
        # Klasyfikacja sytuacji
        if force_ratio >= 1.5 and immediate_threats == 0 and avg_fuel > 0.7:
            return "SPOKÓJ"
        elif force_ratio < 0.8 or immediate_threats > 2 or avg_fuel < 0.4:
            return "KRYZYS"
        else:
            return "WOJNA"
            
    except Exception as e:
        # W razie błędu zakładamy stan wojny (bezpieczna opcja)
        print(f"⚠️ [SITUATION ASSESSMENT] Błąd oceny: {e}")
        return "WOJNA"

# Stałe przeniesione z ai_commander - wszystkie wartości uaktualnione do 3
RESUPPLY_SECOND_MOVE_MIN_FUEL_GAIN = 2
RESUPPLY_TARGET_FUEL_THRESHOLD = 0.65
RESUPPLY_PER_UNIT_CAP_MID_TURN = 3  # Zwiększone z 1 do 3 aby pasować do LOW_FUEL systemu

__all__ = [
    'pre_resupply','tactical_resupply','_perform_resupply','_process_second_chance_moves',
    '_is_token_in_combat_zone','RESUPPLY_SECOND_MOVE_MIN_FUEL_GAIN','RESUPPLY_TARGET_FUEL_THRESHOLD',
    'RESUPPLY_PER_UNIT_CAP_MID_TURN'
]

def pre_resupply(commander, game_engine: Any) -> None:
    current_turn = getattr(game_engine, 'turn_number', getattr(game_engine, 'current_turn', None))
    if commander._did_pre_resupply_turn == current_turn:
        return
    player = commander.player
    try:
        print(f"🔧 [DEBUG Resupply] START dla {player.nation} (id={player.id})")
    except Exception:
        pass
    punkty = 0
    if hasattr(player, 'economy') and player.economy is not None:
        punkty = getattr(player.economy, 'economic_points', 0)
    if punkty <= 0:
        punkty = getattr(player, 'punkty_ekonomiczne', 0)
    if punkty <= 0 and hasattr(player, 'economy') and hasattr(player.economy, 'get_points'):
        try:
            punkty = player.economy.get_points().get('economic_points', 0)
        except Exception:
            pass
    if punkty <= 0:
        print(f"[AI Resupply] {getattr(player,'nation','?')}: ❌ BRAK PUNKTÓW")
        return
    print(f"[AI Resupply] {getattr(player,'nation','?')}: ✅ Rozpoczynam z {punkty} punktami")
    if _perform_resupply(commander, game_engine, punkty, "PRE_TURN"):
        commander._did_pre_resupply_turn = current_turn

def tactical_resupply(commander, game_engine: Any, trigger: str = "DAMAGE", unit_id: str = None) -> bool:
    try:
        current_turn = getattr(game_engine, 'turn_number', getattr(game_engine, 'current_turn', None))
        if current_turn is not None and getattr(commander, '_resupply_turn_cache', None) != current_turn:
            commander._resupply_turn_cache = current_turn
            commander._mid_turn_resupply_counts = {}
            commander._low_fuel_token_counts = {}  # Per-token LOW_FUEL counter
    except Exception:
        pass
    
    # LOW_FUEL limit per token (3 times per turn per token)
    if trigger == "LOW_FUEL" and unit_id:
        token_count = getattr(commander, '_low_fuel_token_counts', {}).get(unit_id, 0)
        if token_count >= 3:
            print(f"❌ [RESUPPLY BLOCK] {unit_id} osiągnął limit 3x LOW_FUEL na turę")
            return False
        # Increment counter for this token
        if not hasattr(commander, '_low_fuel_token_counts'):
            commander._low_fuel_token_counts = {}
        commander._low_fuel_token_counts[unit_id] = token_count + 1
        print(f"🔄 [LOW_FUEL COUNT] {unit_id}: {token_count + 1}/3 użyć w tej turze")
    
    player = commander.player
    punkty = 0
    if hasattr(player, 'economy') and player.economy is not None:
        punkty = getattr(player.economy, 'economic_points', 0)
    if punkty <= 0:
        punkty = getattr(player, 'punkty_ekonomiczne', 0)
    print(f"💰 [RESUPPLY CHECK] PE dostępne: {punkty}")
    if punkty <= 5:
        print(f"❌ [RESUPPLY BLOCK] Za mało PE: {punkty} <= 5")
        return False
    # szybka ocena sumy potrzeb
    try:
        total_need = 0
        expected_owner = f"{player.id} ({player.nation})"
        tokens_src = []
        if hasattr(game_engine,'board') and hasattr(game_engine.board,'tokens'):
            tokens_src = game_engine.board.tokens
        elif hasattr(game_engine,'tokens'):
            tokens_src = game_engine.tokens
        for tk in tokens_src[:150]:
            if getattr(tk,'owner','') != expected_owner:
                continue
            cf = getattr(tk,'currentFuel',0)
            mf = getattr(tk,'maxFuel', getattr(tk,'stats',{}).get('maintenance',0))
            cc = getattr(tk,'combat_value', getattr(tk,'stats',{}).get('combat_value',0))
            mc = getattr(tk,'stats',{}).get('combat_value',0)
            if mf and cf < mf:
                total_need += (mf-cf)
            if mc and cc < mc:
                total_need += (mc-cc)
            if total_need >= 1:  # Zmniejszone z 4 do 1 - pozwala na małe operacje LOW_FUEL
                break
        if total_need < 1:
            print(f"❌ [RESUPPLY BLOCK] Za mała potrzeba: {total_need} < 1")
            return False
    except Exception as e:
        print(f"⚠️ [RESUPPLY ERROR] Błąd oceny potrzeb: {e}")
        pass
    # ⚡ DYNAMICZNA ALOKACJA BUDŻETU - rozwiązanie problemu marnowania 30% PE na nieużywane zakupy
    try:
        # OCENA SYTUACJI TAKTYCZNEJ
        situation = _assess_tactical_situation(commander, game_engine)
        
        # DEFINICJE STANÓW:
        # SPOKÓJ: force_ratio >= 1.5, brak immediate_threats, fuel > 70%
        # WOJNA: force_ratio 0.8-1.5, lub immediate_threats > 0, fuel 40-70%  
        # KRYZYS: force_ratio < 0.8, lub immediate_threats > 2, fuel < 40%
        
        if situation == "SPOKÓJ":
            allocation = {"resupply": 0.5, "reserve": 0.5}  # 50% na paliwo, 50% rezerwa
            print(f"🟢 SYTUACJA: {situation} - alokacja 50% paliwo / 50% rezerwa")
        elif situation == "WOJNA":
            allocation = {"resupply": 0.8, "reserve": 0.2}  # 80% na paliwo, 20% rezerwa
            print(f"🟡 SYTUACJA: {situation} - alokacja 80% paliwo / 20% rezerwa") 
        else:  # KRYZYS
            allocation = {"resupply": 0.9, "reserve": 0.1}  # 90% na paliwo, 10% rezerwa
            print(f"🔴 SYTUACJA: {situation} - alokacja 90% paliwo / 10% rezerwa")
        
        resupply_ratio = allocation.get('resupply', 0.6)
        max_budget = max(5, int(punkty * resupply_ratio))
        print(f"💰 [DYNAMIC BUDGET] PE={punkty} × {resupply_ratio} = budżet {max_budget} (sytuacja: {situation})")
    except Exception as e:
        # Fallback do starego systemu w razie błędu
        print(f"⚠️ [BUDGET ERROR] Błąd oceny sytuacji: {e}, używam domyślnej alokacji")
        allocation = getattr(commander, 'budget_allocation', {"allocate": 0.6, "purchase": 0.3, "reserve": 0.1})
        allocate_ratio = allocation.get('allocate', 0.6)
        max_budget = max(5, int(punkty * allocate_ratio))
    # Zlicz próbę
    try:
        commander.resupply_attempts_this_turn = getattr(commander, 'resupply_attempts_this_turn', 0) + 1
    except Exception:
        pass
    result = _perform_resupply(commander, game_engine, max_budget, trigger)
    if result:
        try:
            commander.resupply_successes_this_turn = getattr(commander, 'resupply_successes_this_turn', 0) + 1
        except Exception:
            pass
    return result

def _perform_resupply(commander, game_engine: Any, punkty: int, context: str) -> bool:
    player = commander.player
    print(f"🔧 [Resupply {context}] {getattr(player,'nation','?')}: budżet={punkty}")
    # Upewnij się, że liczniki istnieją
    if not hasattr(commander, 'resupply_attempts_this_turn'):
        try:
            commander.resupply_attempts_this_turn = 0
            commander.resupply_successes_this_turn = 0
        except Exception:
            pass
    my_tokens = []
    expected_owner = f"{getattr(player,'id',0)} ({getattr(player,'nation','?')})"
    if hasattr(game_engine,'board') and hasattr(game_engine.board,'tokens'):
        for t in game_engine.board.tokens:
            if getattr(t,'owner','') == expected_owner:
                my_tokens.append(t)
    if not my_tokens and hasattr(game_engine,'tokens'):
        for t in game_engine.tokens:
            if getattr(t,'owner','') == expected_owner:
                my_tokens.append(t)
    if not my_tokens:
        return False
    if context == 'DAMAGE':
        def get_priority(token):
            mc = token.stats.get('combat_value',0)
            cc = getattr(token,'combat_value', mc)
            return cc / max(mc,1)
    elif context == 'PRE_ATTACK':
        def get_priority(token):
            mc = token.stats.get('combat_value',0)
            cc = getattr(token,'combat_value', mc)
            in_zone = _is_token_in_combat_zone(commander, token, game_engine)
            return (cc / max(mc,1)) - (0.5 if in_zone else 0)
    else:
        def get_priority(token):
            max_fuel = getattr(token,'maxFuel', token.stats.get('maintenance',0))
            cf = getattr(token,'currentFuel',0)
            fuel_pct = cf / max(max_fuel,1)
            mc = token.stats.get('combat_value',0)
            cc = getattr(token,'combat_value', mc)
            combat_pct = cc / max(mc,1)
            return min(fuel_pct, combat_pct)
    try:
        my_tokens.sort(key=get_priority)
    except Exception:
        pass
    tokens_needing_help = []
    total_needs = 0
    for tk in my_tokens:
        cf = getattr(tk,'currentFuel',0)
        mf = getattr(tk,'maxFuel', tk.stats.get('maintenance',0))
        fuel_needed = max(0, mf - cf)
        cc = getattr(tk,'combat_value', tk.stats.get('combat_value',0))
        mc = tk.stats.get('combat_value',0)
        combat_needed = max(0, mc - cc)
        tot = fuel_needed + combat_needed
        if tot>0:
            tokens_needing_help.append({'token': tk,'fuel_needed': fuel_needed,'combat_needed': combat_needed,'total_needed': tot})
            total_needs += tot
    if not tokens_needing_help:
        # Log że nie było potrzeby resupply
        try:
            log_commander_action(unit_id='NO_RESUPPLY_NEEDED', action_type='resupply_analysis', from_pos=None, to_pos=None, reason=f'ANALYSIS {context} | NO_UNITS_NEED_RESUPPLY | BUDGET_AVAILABLE: {punkty} PE', player_nation=getattr(player,'nation','?'))
        except Exception:
            pass
        return True
    
    print(f"🤝 [COLLECTIVE RESUPPLY] {len(tokens_needing_help)} units need {total_needs} pkt (budget {punkty})")
    
    # LOGOWANIE ANALIZY POTRZEB - szczegółowy breakdown
    try:
        total_fuel_needed = sum(d['fuel_needed'] for d in tokens_needing_help)
        total_combat_needed = sum(d['combat_needed'] for d in tokens_needing_help)
        analysis = f'NEEDS_ANALYSIS {context} | TOTAL_FUEL_NEEDED: {total_fuel_needed} | TOTAL_COMBAT_NEEDED: {total_combat_needed} | TOTAL_PE_NEEDED: {total_needs} | BUDGET_AVAILABLE: {punkty} | UNITS_REQUIRING_HELP: {len(tokens_needing_help)}'
        log_commander_action(unit_id='RESUPPLY_NEEDS', action_type='resupply_analysis', from_pos=None, to_pos=None, reason=analysis, player_nation=getattr(player,'nation','?'))
    except Exception:
        pass
    
    # Sprawdź czy budżet wystarczy na potrzeby
    if total_needs > punkty:
        print(f"⚠️ [BUDGET SHORTAGE] Potrzeba {total_needs} PE, dostępne {punkty} PE")
    
    # Zwiększona alokacja dla LOW_FUEL - minimum 3 punkty na jednostkę
    if context == "LOW_FUEL":
        base_alloc = max(3, punkty // max(1, len(tokens_needing_help)))
    else:
        base_alloc = max(1, punkty // (len(tokens_needing_help)+2))
    
    
    # NOWE: Sprawdź czy planowana alokacja nie przekracza budżetu
    planned_spending = base_alloc * len(tokens_needing_help)
    if planned_spending > punkty:
        print(f"⚠️ [OVERSPENDING] Planowano {planned_spending}, dostępne {punkty} - koryguje alokację")
        base_alloc = max(1, punkty // len(tokens_needing_help))
        planned_spending = base_alloc * len(tokens_needing_help)
    
    remaining = punkty - planned_spending
    resupplied = 0
    spent_total = 0
    for data in tokens_needing_help:
        tk = data['token']
        fuel_needed = data['fuel_needed']
        combat_needed = data['combat_needed']
        if context != 'PRE_TURN' and fuel_needed>0:
            try:
                target_cap = math.ceil(getattr(tk,'maxFuel', tk.stats.get('maintenance',0))*RESUPPLY_TARGET_FUEL_THRESHOLD)
                allowed_missing = max(0, target_cap - getattr(tk,'currentFuel',0))
                if allowed_missing < fuel_needed:
                    fuel_needed = allowed_missing
            except Exception:
                pass
        if context != 'PRE_TURN':
            uid = getattr(tk,'id',None)
            if uid and commander._mid_turn_resupply_counts.get(uid,0) >= RESUPPLY_PER_UNIT_CAP_MID_TURN:
                continue
        can_spend = min(base_alloc, fuel_needed+combat_needed)
        if fuel_needed>0 and combat_needed>0:
            fuel_add = min(fuel_needed, can_spend//2)
            combat_add = min(combat_needed, can_spend - fuel_add)
        elif fuel_needed>0:
            fuel_add = min(fuel_needed, can_spend); combat_add = 0
        else:
            fuel_add = 0; combat_add = min(combat_needed, can_spend)
        if fuel_add>0:
            tk.currentFuel = min(getattr(tk,'maxFuel', tk.stats.get('maintenance',0)), getattr(tk,'currentFuel',0)+fuel_add)
        if combat_add>0:
            tk.combat_value = min(tk.stats.get('combat_value',0), getattr(tk,'combat_value',0)+combat_add)
        spent = fuel_add + combat_add
        if spent>0:
            resupplied += 1; spent_total += spent
            if context != 'PRE_TURN':
                uid = getattr(tk,'id',None)
                if uid:
                    commander._mid_turn_resupply_counts[uid] = commander._mid_turn_resupply_counts.get(uid,0)+1
            try:
                # SZCZEGÓŁOWE LOGOWANIE: dokładnie co zostało uzupełnione
                details = f'phase1 {context} | PE_SPENT: fuel={fuel_add} combat={combat_add} total={spent} | BEFORE: fuel={getattr(tk,"currentFuel",0)-fuel_add} combat={getattr(tk,"combat_value",0)-combat_add} | AFTER: fuel={getattr(tk,"currentFuel",0)} combat={getattr(tk,"combat_value",0)}'
                log_commander_action(unit_id=getattr(tk,'id','unknown'), action_type='resupply_detailed', from_pos=(getattr(tk,'q',0),getattr(tk,'r',0)), to_pos=(getattr(tk,'q',0),getattr(tk,'r',0)), reason=details, player_nation=getattr(player,'nation','?'))
            except Exception:
                pass
    # Bonus faza uproszczona (opcjonalna)
    if remaining>0:
        bonus_each = max(1, remaining // len(tokens_needing_help))
        for data in tokens_needing_help:
            if remaining<=0: break
            tk = data['token']
            cf = getattr(tk,'currentFuel',0); mf = getattr(tk,'maxFuel', tk.stats.get('maintenance',0))
            cc = getattr(tk,'combat_value', tk.stats.get('combat_value',0)); mc = tk.stats.get('combat_value',0)
            fuel_need = max(0, mf-cf); combat_need = max(0, mc-cc)
            if fuel_need+combat_need<=0: continue
            spend = min(bonus_each, fuel_need+combat_need, remaining)
            f_add = min(fuel_need, spend//2); c_add = min(combat_need, spend-f_add)
            if f_add>0:
                tk.currentFuel = min(mf, getattr(tk,'currentFuel',0)+f_add)
            if c_add>0:
                tk.combat_value = min(mc, getattr(tk,'combat_value',0)+c_add)
            remaining -= (f_add+c_add); spent_total += (f_add+c_add)
            
            # SZCZEGÓŁOWE LOGOWANIE BONUS FAZY
            if f_add > 0 or c_add > 0:
                try:
                    bonus_details = f'bonus_phase {context} | PE_SPENT: fuel={f_add} combat={c_add} total={f_add+c_add} | BONUS_ALLOCATION: {bonus_each} PE available | REMAINING_BUDGET: {remaining} PE'
                    log_commander_action(unit_id=getattr(tk,'id','unknown'), action_type='resupply_bonus', from_pos=(getattr(tk,'q',0),getattr(tk,'r',0)), to_pos=(getattr(tk,'q',0),getattr(tk,'r',0)), reason=bonus_details, player_nation=getattr(player,'nation','?'))
                except Exception:
                    pass
    
    # WALIDACJA PE PRZED WYDANIEM - BLOKADA UJEMNYCH PE!
    current_pe = getattr(player, 'punkty_ekonomiczne', 0)
    if hasattr(player, 'economy') and player.economy is not None:
        current_pe = max(current_pe, getattr(player.economy, 'economic_points', 0))
    
    if spent_total > current_pe:
        print(f"🚫 [PE BLOCK] BLOKADA WYDANIA! Próba wydania {spent_total} PE, dostępne {current_pe} PE")
        print(f"🚫 [PE BLOCK] Koryguje wydatek do maksimum dostępnego: {current_pe} PE")
        spent_total = current_pe
        
        if spent_total <= 0:
            print(f"🚫 [PE BLOCK] Brak PE do wydania! Anuluje operację resupply")
            return False
    
    # Ostateczne wydanie środków - już zwalidowane
    print(f"💰 Wydaję {spent_total} PE na zaopatrzenie jednostek")
    
    # Odejmij zasoby ekonomiczne - bezpieczne odejmowanie
    try:
        old_pe = getattr(player, 'punkty_ekonomiczne', 0)
        new_pe = max(0, old_pe - spent_total)  # Nigdy nie pozwalaj na ujemne PE
        player.punkty_ekonomiczne = new_pe
        
        if hasattr(player, 'economy') and player.economy is not None:
            old_eco_pe = getattr(player.economy, 'economic_points', 0)
            new_eco_pe = max(0, old_eco_pe - spent_total)  # Nigdy nie pozwalaj na ujemne PE
            player.economy.economic_points = new_eco_pe
        
        print(f"💰 PE: {old_pe} → {new_pe} (wydano {spent_total})")
        
        # Dodatkowa kontrola bezpieczeństwa
        if getattr(player, 'punkty_ekonomiczne', 0) < 0:
            print(f"🚨 [EMERGENCY] WYKRYTO UJEMNE PE! Przywracam do 0")
            player.punkty_ekonomiczne = 0
        if hasattr(player, 'economy') and getattr(player.economy, 'economic_points', 0) < 0:
            print(f"🚨 [EMERGENCY] WYKRYTO UJEMNE ECONOMY PE! Przywracam do 0")
            player.economy.economic_points = 0
            
    except Exception as e:
        print(f"⚠️ Błąd przy aktualizacji ekonomii: {e}")
        pass
    
    # SUMMARY LOGOWANIE - CAŁOŚCIOWY RAPORT PE SPENDING
    try:
        summary = f'RESUPPLY_SUMMARY {context} | TOTAL_PE_SPENT: {spent_total} | UNITS_RESUPPLIED: {resupplied}/{len(tokens_needing_help)} | BUDGET_ALLOCATED: {punkty} | PE_REMAINING: {current_pe - spent_total}'
        log_commander_action(unit_id='RESUPPLY_OPERATION', action_type='resupply_summary', from_pos=None, to_pos=None, reason=summary, player_nation=getattr(player,'nation','?'))
    except Exception:
        pass
    if context != 'PRE_TURN':
        try:
            for d in tokens_needing_help:
                tk = d['token']
                if getattr(tk,'currentFuel',0)>0 and getattr(tk,'currentMovePoints',0)>0 \
                        and tk not in commander._second_chance_queue:
                    commander._second_chance_queue.append(tk)
        except Exception:
            pass
        if commander._second_chance_queue:
            _process_second_chance_moves(commander, game_engine, context)
    return resupplied>0

def _process_second_chance_moves(commander, game_engine, context: str):
    try:
        while commander._second_chance_queue:
            tk = commander._second_chance_queue.pop(0)
            if getattr(tk,'currentMovePoints',0)<=0 or getattr(tk,'currentFuel',0)<=0:
                continue
            unit_dict = {'id': getattr(tk,'id','unknown'),'q': getattr(tk,'q',0),'r': getattr(tk,'r',0),'mp': getattr(tk,'currentMovePoints',0),'fuel': getattr(tk,'currentFuel',0),'token': tk}
            try:
                target = find_target(unit_dict, game_engine)
            except Exception:
                target = None
            if target:
                move_towards(unit_dict, target, game_engine)
                try:
                    log_commander_action(unit_id=getattr(tk,'id','unknown'), action_type='second_move', from_pos=None, to_pos=(getattr(tk,'q',0),getattr(tk,'r',0)), reason=f'second_chance after {context}', player_nation=getattr(commander.player,'nation','?'))
                except Exception:
                    pass
    except Exception:
        pass

def _is_token_in_combat_zone(commander, token, game_engine) -> bool:
    try:
        token_pos = (token.q, token.r)
        sight_range = token.stats.get('sight', 1)
        for enemy_token in getattr(game_engine,'tokens', []):
            if not getattr(enemy_token,'owner', None) or not getattr(token,'owner', None):
                continue
            enemy_nation = enemy_token.owner.split('(')[-1].replace(')','').strip()
            token_nation = token.owner.split('(')[-1].replace(')','').strip()
            if enemy_nation != token_nation:
                board = getattr(game_engine,'board', None)
                if not board or not hasattr(board,'hex_distance'):
                    continue
                distance = board.hex_distance(token_pos, (enemy_token.q, enemy_token.r))
                if distance <= sight_range + 1:
                    return True
        return False
    except Exception:
        return False
