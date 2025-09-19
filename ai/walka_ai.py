"""Moduł walki AI wydzielony z ai_commander.
Zawiera logikę wyszukiwania celów, oceny stosunku sił, flankowania, odwrotu i wykonania ataku.
"""
from __future__ import annotations
from typing import Any, Dict, List
from ai.ai_config import get_param
from utils.turn_context import set_correlation_id, clear_correlation_id

__all__ = [
    'ai_attempt_combat', 'find_enemies_in_range', 'evaluate_combat_ratio',
    'execute_ai_combat', 'attempt_retreat_low_cv', 'try_flank_before_attack'
]

def ai_attempt_combat(unit: Dict, game_engine: Any, player_id: int, player_nation: str = "Unknown") -> bool:
    from ai.logowanie_ai import log_commander_action, log_attack_opportunity_scan, log_combat_precheck, log_combat_decision
    from .walka_ai import find_enemies_in_range, evaluate_combat_ratio, execute_ai_combat, attempt_retreat_low_cv, try_flank_before_attack
    
    # DEBUG: Loguj rozpoczęcie analizy walki
    unit_name = unit.get('id', 'UNKNOWN')
    print(f"🔍 [COMBAT DEBUG] {unit_name} sprawdza możliwość ataku...")
    
    try:
        # correlation_id dla całego cyklu walki tej jednostki w tej turze
        corr_id = f"combat:{unit.get('id','UNKNOWN')}:{getattr(game_engine,'turn_number', getattr(game_engine,'current_turn', 'X'))}"
        set_correlation_id(corr_id)
        current_player = getattr(game_engine, 'current_player_obj', None)
        if current_player and hasattr(current_player, 'is_ai_commander'):
            commander_ref = getattr(game_engine, 'current_player_commander', None)
            if commander_ref and hasattr(commander_ref, 'tactical_resupply'):
                unit_token = unit.get('token')
                if unit_token:
                    current_cv = getattr(unit_token, 'combat_value', 0)
                    max_cv = unit_token.stats.get('combat_value', 0)
                    low_cv_threshold = get_param('COMBAT.LOW_CV_RESUPPLY_THRESHOLD', 0.8)
                    if max_cv > 0 and current_cv / max_cv < low_cv_threshold:
                        commander_ref.tactical_resupply(game_engine, "PRE_ATTACK")
        if attempt_retreat_low_cv(unit, game_engine):
            return False
        utok = unit.get('token')
        if utok and getattr(utok, 'currentMovePoints', 0) <= 0:
            return False
        enemies = find_enemies_in_range(unit, game_engine, player_id)
        print(f"🎯 [COMBAT DEBUG] {unit_name} znalazł {len(enemies)} wrogów w zasięgu")
        # Log skanu okazji do ataku
        try:
            preview = ",".join([e.get('id','?') for e in enemies[:5]])
            min_ratio = get_param('COMBAT.MINIMUM_ATTACK_RATIO', 1.2, player_id=player_id)
            log_attack_opportunity_scan(unit.get('id','UNKNOWN'), player_nation, len(enemies), min_ratio, preview)
        except Exception:
            pass
        
        if not enemies:
            print(f"❌ [COMBAT DEBUG] {unit_name}: Brak wrogów - koniec analizy")
            return False

        best_enemy = None; best_ratio = 0.0
        minimum_attack_ratio = get_param('COMBAT.MINIMUM_ATTACK_RATIO', 1.2, player_id=player_id)
        print(f"⚔️ [COMBAT DEBUG] {unit_name}: Próg ataku = {minimum_attack_ratio:.2f}")
        
        for i, enemy in enumerate(enemies):
            enemy_name = enemy.get('id', f'enemy_{i}')
            ratio = evaluate_combat_ratio(unit, enemy)
            print(f"🎲 [COMBAT DEBUG] {unit_name} vs {enemy_name}: ratio = {ratio:.2f}")
            # Precheck log
            try:
                threshold_tmp = get_param('COMBAT.MINIMUM_ATTACK_RATIO', 1.2, player_id=player_id)
                decision_tmp = 'consider' if ratio >= threshold_tmp else 'skip'
                log_combat_precheck(unit.get('id','UNKNOWN'), player_nation, enemy_name, ratio, threshold_tmp, decision_tmp)
            except Exception:
                pass
            
            # Adaptacyjny próg: jeśli ryzyko kontrataku niskie i teren nie wzmacnia obrony, pozwól na łagodniejszy próg
            threshold_local = minimum_attack_ratio
            try:
                enemy_token = enemy.get('token')
                unit_token = unit.get('token')
                board = getattr(game_engine, 'board', None)
                counter_range = enemy_token.stats.get('attack', {}).get('range', 1) if enemy_token else 1
                dist = board.hex_distance((unit.get('q'), unit.get('r')), (enemy.get('q'), enemy.get('r'))) if board else 99
                low_counter_risk = dist > counter_range
                terrain_penalty = 0
                if board and enemy_token and hasattr(board, 'get_tile'):
                    tile = board.get_tile(enemy.get('q'), enemy.get('r'))
                    terrain_penalty = getattr(tile, 'defense_mod', 0) if tile else 0
                if low_counter_risk and terrain_penalty <= 0:
                    threshold_local = min(threshold_local, 1.10)
            except Exception:
                pass
            if ratio > best_ratio and ratio >= threshold_local:
                old_best = best_enemy.get('id', 'none') if best_enemy else 'none'
                best_ratio = ratio; best_enemy = enemy
                print(f"⭐ [COMBAT DEBUG] {unit_name}: Nowy najlepszy cel {old_best} -> {enemy_name} (ratio: {ratio:.2f})")
                
        print(f"🏁 [COMBAT DEBUG] {unit_name}: Najlepszy wróg = {best_enemy.get('id', 'NONE') if best_enemy else 'NONE'} (ratio: {best_ratio:.2f})")
        if best_enemy:
            try_flank_before_attack(unit, best_enemy, game_engine)
            print(f"🎯 [COMBAT] {unit.get('id')} atakuje {best_enemy.get('id')} (ratio_adj: {best_ratio:.2f})")
            try:
                # Ustal czy próg był obniżony
                base_thr = get_param('COMBAT.MINIMUM_ATTACK_RATIO', 1.2, player_id=player_id)
                thr_adj = 1 if best_ratio < base_thr else 0
                log_combat_decision(unit.get('id','UNKNOWN'), player_nation, best_enemy.get('id','unknown'), best_ratio, base_thr, 'attack', reason=('low_counterattack_risk' if thr_adj else ''), extra=({'threshold_adjusted': True} if thr_adj else None))
            except Exception:
                pass
            return execute_ai_combat(unit, best_enemy, game_engine, player_nation)
        else:
            print(f"❌ [COMBAT DEBUG] {unit_name}: Żaden wróg nie spełnia progu {minimum_attack_ratio} (najlepszy: {best_ratio:.2f})")
            try:
                log_combat_decision(unit.get('id','UNKNOWN'), player_nation, 'NONE', best_ratio, minimum_attack_ratio, 'skip', reason='no_enemy_above_threshold')
            except Exception:
                pass
        return False
    except Exception as e:
        print(f"❌ [COMBAT] Błąd podczas sprawdzania ataku: {e}")
        return False
    finally:
        clear_correlation_id()

def find_enemies_in_range(unit: Dict, game_engine: Any, player_id: int) -> List[Dict]:
    enemies: List[Dict] = []
    try:
        from ai.ai_commander import get_player_nation
        my_owner = f"{player_id} ({get_player_nation(game_engine, player_id)})"
        unit_token = unit.get('token')
        if not unit_token:
            return enemies
        board = getattr(game_engine, 'board', None)
        attack_range = unit_token.stats.get('attack', {}).get('range', 1)
        sight = unit_token.stats.get('sight', 0)
        unit_pos = (unit['q'], unit['r'])
        visible_hexes = set()
        if board and sight > 0:
            try:
                from engine.action_refactored_clean import VisionService
                visible_hexes = VisionService.calculate_visible_hexes(board, unit_pos, sight)
                print(f"🔍 [VISION DEBUG] {unit.get('id', 'UNKNOWN')}: sight={sight}, visible_hexes={len(visible_hexes)}")
            except Exception as e:
                print(f"❌ [VISION DEBUG] VisionService error: {e}")
                visible_hexes = set()
        all_tokens = getattr(game_engine, 'tokens', [])
        current_player = getattr(game_engine, 'current_player_obj', None)
        for token in all_tokens:
            # POPRAWKA: Porównuj tylko część numeryczną owner (np. "2" z "2 (Polska)")
            token_owner_id = getattr(token, 'owner', '').split(' ')[0]
            if token_owner_id == str(player_id):
                continue  # Pomiń własne jednostki
            enemy_pos = (getattr(token, 'q', 0), getattr(token, 'r', 0))
            if visible_hexes and enemy_pos not in visible_hexes:
                continue
            if board:
                distance = board.hex_distance(unit_pos, enemy_pos)
                if distance <= attack_range:
                    detection_level = 1.0
                    if current_player and hasattr(current_player, 'visible_token_data'):
                        token_detection = current_player.visible_token_data.get(token.id, {})
                        detection_level = token_detection.get('detection_level', 1.0)
                    
                    # POPRAWKA: Używaj attack/defense zamiast combat_value do oceny siły
                    enemy_attack = token.stats.get('attack', {}).get('value', 0)
                    enemy_defense = token.stats.get('defense_value', 0)
                    enemy_hp = getattr(token, 'combat_value', 0)
                    
                    # Jeśli ograniczona detekcja, użyj przybliżonych wartości
                    high_detection = get_param('COMBAT.HIGH_DETECTION_THRESHOLD', 0.8)
                    medium_detection = get_param('COMBAT.MEDIUM_DETECTION_THRESHOLD', 0.5)
                    
                    if detection_level < high_detection:
                        try:
                            from engine.detection_filter import apply_detection_filter
                            enemy_info = apply_detection_filter(token, detection_level)
                            # Szacuj attack/defense na podstawie poziomu detekcji
                            if detection_level >= medium_detection:
                                enemy_attack = max(1, int(enemy_attack * 0.8))  # Przybliżona wartość
                                enemy_defense = max(1, int(enemy_defense * 0.8))
                            else:
                                enemy_attack = 5  # Domyślne założenie przy słabej detekcji
                                enemy_defense = 5
                        except Exception:
                            pass
                    
                    enemies.append({'token': token,'id': getattr(token, 'id', 'unknown'),'q': enemy_pos[0],'r': enemy_pos[1],'attack_val': enemy_attack,'defense_val': enemy_defense,'hp': enemy_hp,'detection_level': detection_level,'distance': distance})
        return enemies
    except Exception as e:
        print(f"❌ [COMBAT] Błąd wyszukiwania wrogów: {e}")
        return enemies

def evaluate_combat_ratio(unit: Dict, enemy: Dict) -> float:
    try:
        unit_token = unit.get('token'); enemy_token = enemy.get('token')
        if not unit_token or not enemy_token: return 0.0
        attack_value = unit_token.stats.get('attack', {}).get('value', 0)
        defense_value = enemy_token.stats.get('defense_value', 0)
        board = getattr(unit_token, 'board', None)
        terrain_mod = 0
        if hasattr(board, 'get_tile'):
            tile = board.get_tile(enemy['q'], enemy['r'])
            terrain_mod = getattr(tile, 'defense_mod', 0) if tile else 0
        total_defense = max(1, defense_value + terrain_mod)
        base_ratio = attack_value / total_defense
        defender_attack_val = enemy_token.stats.get('attack', {}).get('value', 0)
        defender_range = enemy_token.stats.get('attack', {}).get('range', 1)
        attacker_defense = unit_token.stats.get('defense_value', 0)
        attacker_pos = (unit.get('q'), unit.get('r'))
        enemy_pos = (enemy.get('q'), enemy.get('r'))
        distance = board.hex_distance(attacker_pos, enemy_pos) if board else 99
        if distance <= defender_range and attacker_defense > 0:
            counter_factor = (defender_attack_val / max(1, attacker_defense))
            penalty = min(0.6, 0.25 * counter_factor)
            return base_ratio * (1 - penalty)
        return base_ratio
    except Exception as e:
        print(f"❌ [COMBAT] Błąd obliczania ratio: {e}")
        return 0.0

def attempt_retreat_low_cv(unit: Dict, game_engine: Any) -> bool:
    try:
        utok = unit.get('token')
        if not utok: return False
        cv = getattr(utok, 'combat_value', 0)
        base_cv = utok.stats.get('combat_value', 1)
        if base_cv <= 0 or cv / base_cv >= get_param('COMBAT.MINIMUM_CV_RETREAT_RATIO', 0.25): return False
        board = getattr(game_engine, 'board', None)
        if not board: return False
        closest = None; closest_d = 999
        for t in getattr(game_engine, 'tokens', [])[:120]:
            if t is utok or getattr(t,'owner','') == getattr(utok,'owner',''): continue
            d = board.hex_distance((utok.q, utok.r), (t.q, t.r))
            if d < closest_d: closest_d = d; closest = t
        if not closest or closest_d > 3: return False
        best_hex = None; best_gain = 0
        for nq, nr in board.neighbors(utok.q, utok.r):
            tile = board.get_tile(nq, nr)
            if not tile or board.is_occupied(nq, nr): continue
            dist_new = board.hex_distance((nq, nr), (closest.q, closest.r))
            gain = dist_new - closest_d
            if gain > best_gain: best_gain = gain; best_hex = (nq, nr)
        if best_hex and best_gain > 0:
            try:
                from engine.action_refactored_clean import MoveAction
                action = MoveAction(utok.id, best_hex[0], best_hex[1])
                game_engine.execute_action(action, player=getattr(game_engine, 'current_player_obj', None))
                print(f"[RETREAT] {utok.id} wycofuje się na {best_hex} (cv {cv}/{base_cv})")
                return True
            except Exception:
                return False
        return False
    except Exception:
        return False

def try_flank_before_attack(unit: Dict, enemy: Dict, game_engine: Any) -> None:
    try:
        utok = unit.get('token'); etok = enemy.get('token')
        if not utok or not etok: return
        board = getattr(game_engine, 'board', None)
        if not board: return
        atk_range = utok.stats.get('attack', {}).get('range', 1)
        def_range = etok.stats.get('attack', {}).get('range', 1)
        if board.hex_distance((utok.q, utok.r), (etok.q, etok.r)) > def_range: return
        candidates = []
        for dq in range(-atk_range, atk_range+1):
            for dr in range(-atk_range, atk_range+1):
                tq = etok.q + dq; tr = etok.r + dr
                if board.hex_distance((etok.q, etok.r), (tq, tr)) > atk_range: continue
                if board.get_tile(tq, tr) is None: continue
                if board.is_occupied(tq, tr): continue
                if board.hex_distance((etok.q, etok.r), (tq, tr)) <= def_range: continue
                candidates.append((tq, tr))
        if not candidates: return
        best = None; best_len = 999
        for cand in candidates[:80]:
            path = board.find_path((utok.q, utok.r), cand, max_mp=getattr(utok,'currentMovePoints',0), max_fuel=getattr(utok,'currentFuel',0))
            if path and len(path) < best_len:
                best_len = len(path); best = (cand, path)
        if best:
            from engine.action_refactored_clean import MoveAction
            mv = MoveAction(utok.id, best[0][0], best[0][1])
            res = game_engine.execute_action(mv, player=getattr(game_engine,'current_player_obj',None))
            if getattr(res,'success',False):
                print(f"[FLANK] {utok.id} manewr na {best[0]} przed atakiem")
    except Exception:
        return

def execute_ai_combat(unit: Dict, enemy: Dict, game_engine: Any, player_nation: str = "Unknown") -> bool:
    try:
        from ai.logowanie_ai import log_commander_action
        unit_token = unit.get('token'); enemy_token = enemy.get('token')
        if not unit_token or not enemy_token: return False
        from engine.action_refactored_clean import CombatAction
        current_player = getattr(game_engine, 'current_player_obj', None)
        action = CombatAction(unit_token.id, enemy_token.id)
        # Zmierz CV przed
        atk_cv_before = getattr(unit_token, 'combat_value', unit_token.stats.get('combat_value', 0))
        def_cv_before = getattr(enemy_token, 'combat_value', enemy_token.stats.get('combat_value', 0))
        result = game_engine.execute_action(action, player=current_player)
        if getattr(result,'success',False):
            print(f"⚔️ [COMBAT] Sukces: {getattr(result,'message','OK')}")
            try:
                log_commander_action(
                    unit_id=unit.get('id','unknown'), action_type='combat',
                    from_pos=(unit['q'], unit['r']), to_pos=(enemy['q'], enemy['r']),
                    reason=f"Attack enemy {enemy.get('id','unknown')}", player_nation=player_nation
                )
            except Exception:
                pass
            # LOGER WALKI (CV przed/po)
            try:
                atk_cv_after = getattr(unit_token, 'combat_value', unit_token.stats.get('combat_value', 0))
                def_cv_after = getattr(enemy_token, 'combat_value', enemy_token.stats.get('combat_value', 0))
                # Nacje atakującego/obrońcy
                def_owner = getattr(enemy_token, 'owner', '')
                def_nation = def_owner.split('(')[-1].replace(')','').strip() if '(' in def_owner else 'Unknown'
                # Spróbuj użyć aliasu zaawansowanego loggera
                commander_ref = getattr(game_engine, 'current_player_commander', None)
                adv = getattr(commander_ref, 'zaawansowany_logger', None)
                if adv:
                    adv.loguj_walke({
                        'nation': player_nation,
                        'attacker_nation': player_nation,
                        'defender_nation': def_nation,
                        'attacker_id': unit.get('id','unknown'),
                        'defender_id': enemy.get('id','unknown'),
                        'attacker_cv_before': atk_cv_before,
                        'attacker_cv_after': atk_cv_after,
                        'defender_cv_before': def_cv_before,
                        'defender_cv_after': def_cv_after,
                        'outcome': 'success',
                        'hex_q': enemy.get('q'),
                        'hex_r': enemy.get('r'),
                        'notes': getattr(result, 'message', '')
                    })
            except Exception:
                pass
            return True
        else:
            print(f"❌ [COMBAT] Błąd: {getattr(result,'message','Brak danych')}")
            # Nawet przy niepowodzeniu zaloguj zdarzenie walki, jeśli możliwe
            try:
                commander_ref = getattr(game_engine, 'current_player_commander', None)
                adv = getattr(commander_ref, 'zaawansowany_logger', None)
                if adv:
                    def_owner = getattr(enemy_token, 'owner', '')
                    def_nation = def_owner.split('(')[-1].replace(')','').strip() if '(' in def_owner else 'Unknown'
                    adv.loguj_walke({
                        'nation': player_nation,
                        'attacker_nation': player_nation,
                        'defender_nation': def_nation,
                        'attacker_id': unit.get('id','unknown'),
                        'defender_id': enemy.get('id','unknown'),
                        'attacker_cv_before': atk_cv_before,
                        'attacker_cv_after': getattr(unit_token, 'combat_value', unit_token.stats.get('combat_value', 0)),
                        'defender_cv_before': def_cv_before,
                        'defender_cv_after': getattr(enemy_token, 'combat_value', enemy_token.stats.get('combat_value', 0)),
                        'outcome': 'fail',
                        'hex_q': enemy.get('q'),
                        'hex_r': enemy.get('r'),
                        'notes': getattr(result, 'message', '')
                    })
            except Exception:
                pass
            return False
    except Exception as e:
        print(f"❌ [COMBAT] Błąd wykonania ataku: {e}")
        return False
