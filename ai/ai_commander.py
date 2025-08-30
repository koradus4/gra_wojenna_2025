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
import shutil
import os
import math
import os
import shutil
from pathlib import Path

# --- KONFIGURACJA NOWYCH HEURYSTYK ---
GARRISON_LIMITS = {
    'miasto': 1,
    'węzeł komunikacyjny': 1,
    'wez\u0142 komunikacyjny': 1,  # fallback jezykowy
    'fortyfikacja': 2,
    'default': 1,
}

EARLY_ROTATION_THRESHOLD_RATIO = 0.25  # zwolnij nadwy\u017ckowe jednostki gdy warto\u015b\u0107 spadnie poni\u017cej 25%
FREE_KEYPOINT_VALUE_DISTANCE_FACTOR = 1.2  # minimalny wsp\u00f3\u0142czynnik (value/distance) dla samotnego rajdu
FREE_HIGH_VALUE_BONUS_MULTIPLIER = 2.5  # dodatkowy mno\u017cnik do priorytetu wolnego punktu
FREE_MED_VALUE_BONUS_MULTIPLIER = 1.6
HEX_MISSING_LOG_PREFIX = "[AI HEX] HEX_MISSING"

def enforce_garrison_limits(game_engine, hex_id, kp, newly_arrived_token, ratio):
    """Pilnuj limitu garnizonu i wczesnej rotacji.
    - ratio < EARLY_ROTATION_THRESHOLD_RATIO: utrzymuj max 1 jednostkę
    - po przekroczeniu limitu: zdejmij hold_position z nadwyżek (poza najstarszą / najsilniejszą)
    """
    try:
        tokens = getattr(game_engine, 'tokens', [])
        # Parse coords
        try:
            q, r = map(int, hex_id.split(','))
        except Exception:
            return
        kp_type = kp.get('type', 'default')
        limit = GARRISON_LIMITS.get(kp_type, GARRISON_LIMITS['default'])
        if ratio < EARLY_ROTATION_THRESHOLD_RATIO:
            limit = max(1, limit - 1)
        # Zbierz tokeny stojące na punkcie
        stationed = []
        for t in tokens:
            if getattr(t, 'q', None) == q and getattr(t, 'r', None) == r and getattr(t, 'hold_position', False):
                stationed.append(t)
        if len(stationed) <= limit:
            return
        # Sortuj: trzymaj ten z najwyższą wartością bojową (attack+defense) i/lub ten który właśnie przyszedł
        def score(t):
            attack = getattr(t, 'attack', 0)
            defense = getattr(t, 'defense', 0)
            freshness = 1 if t is newly_arrived_token else 0
            return attack + defense + freshness * 1000
        stationed.sort(key=score, reverse=True)
        # Zachowaj pierwsze 'limit'
        keep = set(stationed[:limit])
        for t in stationed[limit:]:
            if getattr(t, 'hold_position', False):
                setattr(t, 'hold_position', False)
                print(f"[AI GARRISON] ROTATE {getattr(t,'id','?')} z {hex_id} (limit {limit})")
    except Exception as e:
        print(f"[AI GARRISON] Błąd limitu: {e}")

def opportunistic_capture_phase(game_engine, my_units, player_id):
    """Spróbuj natychmiast zająć wolne key pointy w zasięgu MP.
    Kryterium solo-rajdu: (value / distance) >= FREE_KEYPOINT_VALUE_DISTANCE_FACTOR.
    """
    captured = []
    try:
        board = getattr(game_engine, 'board', None)
        kp_state = getattr(game_engine, 'key_points_state', {}) or {}
        if not board or not kp_state:
            return captured
        # Map token id -> unit dict for quick access
        unit_by_id = {u['id']: u for u in my_units if 'id' in u}
        # Build lookup of free keypoints
        free_kps = []
        for hex_id, kp in kp_state.items():
            if kp.get('current_value', 0) <= 0:
                continue
            try:
                q, r = map(int, hex_id.split(','))
            except Exception:
                continue
            occupied = False
            for t in getattr(game_engine, 'tokens', [])[:400]:
                if getattr(t, 'q', None) == q and getattr(t, 'r', None) == r:
                    occupied = True
                    break
            if not occupied:
                free_kps.append((hex_id, q, r, kp))
        if not free_kps:
            return captured
        # Dla każdej jednostki zobacz czy może dotrzeć w 1 turze
        for unit in my_units:
            if unit.get('mp', 0) <= 0 or unit.get('fuel', 0) <= 0:
                continue
            pos = (unit['q'], unit['r'])
            best_target = None
            best_score = 0
            for hex_id, q, r, kp in free_kps:
                dist = board.hex_distance(pos, (q, r)) if board else 999
                if dist <= 0:
                    continue
                if dist > min(unit['mp'], unit['fuel']):
                    continue
                value = kp.get('current_value', 0)
                score = value / dist
                if score >= FREE_KEYPOINT_VALUE_DISTANCE_FACTOR and score > best_score:
                    best_score = score
                    best_target = (hex_id, q, r, kp)
            if best_target:
                hex_id, tq, tr, kp = best_target
                # Bez pathfindingu – spróbuj ruchu sekwencyjnego w kierunku (fallback prosty)
                # Użyj istniejącego move_towards aby zachować spójność
                success = move_towards(unit, (tq, tr), game_engine)
                if success:
                    unit['moved_capture'] = True
                    captured.append(hex_id)
    except Exception as e:
        print(f"[OPPORTUNISTIC] Błąd: {e}")
    return captured

# Importujemy debug_print z głównego modułu
try:
    from main_ai import debug_print
except ImportError:
    # Fallback gdyby nie udało się zaimportować
    def debug_print(message, level="BASIC", category="INFO"):
        print(f"[AI_COMMANDER] {message}")


def prioritize_targets(key_points, game_engine):
    """Priorytetyzuj cele: wolne wysokowartościowe premiowane mocniej."""
    priorities = []
    board = getattr(game_engine, 'board', None)
    all_tokens = getattr(game_engine, 'tokens', [])
    current_player = getattr(game_engine, 'current_player_obj', None)
    my_nation = getattr(current_player, 'nation', '') if current_player else ''

    for hex_id, kp_data in key_points.items():
        value = kp_data.get('current_value', 0)
        if value <= 0:
            continue
        try:
            if ',' in hex_id:
                q, r = map(int, hex_id.split(','))
            else:
                q, r = map(int, hex_id.split('_'))
            target_pos = (q, r)
        except (ValueError, IndexError):
            continue

        # Czy hex istnieje na planszy
        if board and hasattr(board, 'get_tile'):
            tile = board.get_tile(q, r)
            if tile is None:
                print(f"{HEX_MISSING_LOG_PREFIX} priorytetyzacja {hex_id}")
                continue

        # Sprawdzenie czy punkt jest już okupowany przez nas
        occupied_by_me = False
        occupied_any = False
        for t in all_tokens[:200]:  # limit
            tq, tr = getattr(t, 'q', None), getattr(t, 'r', None)
            if tq == q and tr == r:
                occupied_any = True
                owner = getattr(t, 'owner', '')
                if my_nation and my_nation in owner:
                    occupied_by_me = True
                break

        enemy_distance = 10
        if board:
            for token in all_tokens[:80]:
                token_owner = getattr(token, 'owner', '')
                if my_nation and my_nation in token_owner:
                    continue
                enemy_pos = (getattr(token, 'q', 0), getattr(token, 'r', 0))
                dist = board.hex_distance(target_pos, enemy_pos)
                enemy_distance = min(enemy_distance, dist)

        # Bazowy wynik
        priority_score = (value * 10) / max(enemy_distance, 1)

        # Bonus za wolny (nieokupowany) i wysoka wartość
        if not occupied_any:
            if value >= 120:
                priority_score *= FREE_HIGH_VALUE_BONUS_MULTIPLIER
            elif value >= 70:
                priority_score *= FREE_MED_VALUE_BONUS_MULTIPLIER
        # Lekka redukcja gdy już okupowany przez nas (unikanie prze-garnizonowania)
        if occupied_by_me:
            priority_score *= 0.65

        priorities.append({
            'target': target_pos,
            'hex_id': hex_id,
            'value': value,
            'enemy_distance': enemy_distance,
            'priority': priority_score,
            'free': not occupied_any
        })

    return sorted(priorities, key=lambda x: x['priority'], reverse=True)


def adaptive_grouping(my_units, game_engine):
    """Grupowanie adaptacyjne - rozmiar grup zależy od sytuacji"""
    key_points = getattr(game_engine, 'key_points_state', {})
    key_points_count = len([kp for kp in key_points.values() 
                           if kp.get('current_value', 0) > 0])
    
    # Adaptacyjny rozmiar grup
    if key_points_count <= 3:
        group_size = 3  # Małe grupy dla kilku celów
    elif key_points_count <= 6:
        group_size = 4  # Średnie grupy
    else:
        group_size = 5  # Duże grupy dla wielu celów
    
    print(f"🎯 [ADAPTIVE] {key_points_count} celów -> grupy po {group_size}")
    
    # Stwórz zbalansowane grupy
    groups = []
    for i in range(0, len(my_units), group_size):
        group = my_units[i:i+group_size]
        groups.append(group)
    
    return groups


def assign_targets_with_coordination(groups, prioritized_targets, game_engine):
    """Przypisz cele grupom z koordynacją - bez duplikatów"""
    reserved_targets = set()
    group_assignments = []
    
    for group_idx, group in enumerate(groups):
        print(f"\n🎯 [COORD] Grupa {group_idx+1}: {len(group)} żetonów")
        
        # Znajdź lidera grupy (najbliższy najbardziej wartościowemu celowi)
        best_leader = None
        best_target = None
        best_distance = 999
        best_priority_idx = 999
        
        for unit in group:
            unit_pos = (unit['q'], unit['r'])
            
            # Sprawdź każdy cel według priorytetu
            for priority_idx, target_data in enumerate(prioritized_targets):
                target_pos = target_data['target']
                target_key = f"{target_pos[0]},{target_pos[1]}"
                
                # Pomiń już zarezerwowane cele
                if target_key in reserved_targets:
                    continue
                
                # Oblicz odległość
                board = getattr(game_engine, 'board', None)
                if board:
                    distance = board.hex_distance(unit_pos, target_pos)
                    
                    # Preferuj wyższy priorytet, potem mniejszą odległość
                    if (priority_idx < best_priority_idx or 
                        (priority_idx == best_priority_idx and distance < best_distance)):
                        best_leader = unit
                        best_target = target_pos
                        best_distance = distance
                        best_priority_idx = priority_idx
        
        # Jeśli znaleziono lidera i cel
        if best_leader and best_target:
            target_key = f"{best_target[0]},{best_target[1]}"
            reserved_targets.add(target_key)
            
            group_assignments.append({
                'group': group,
                'leader': best_leader,
                'target': best_target,
                'distance': best_distance,
                'priority': best_priority_idx
            })
            
            target_value = prioritized_targets[best_priority_idx]['value']
            print(f"✅ [COORD] Lider: {best_leader['id']}, Cel: {best_target}, Wartość: {target_value}, Dystans: {best_distance}")
        else:
            print(f"❌ [COORD] Nie można przypisać celu - wszystkie zajęte")
    
    return group_assignments


LOG_COLUMNS = [
    'timestamp','turn','phase','nation','unit_id','unit_type','action_type',
    'from_q','from_r','to_q','to_r',
    'target_q','target_r','target_type','target_value_before','target_value_after',
    'movement_mode','path_len','path_used','progressive_used','adaptive_frac',
    'mp_before','mp_after','fuel_before','fuel_after',
    'combat_dmg_dealt','combat_dmg_taken','enemy_adj_before','enemy_adj_after',
    'threat_level','decision_reason','extra_tags','reason'
]

def log_commander_action(unit_id, action_type, from_pos, to_pos, reason, player_nation="Unknown", extra=None):
    """Loguj akcję AI Commander do CSV (rozszerzony zestaw kolumn).
    extra: dict z dodatkowymi polami zgodnymi z LOG_COLUMNS (poza bazowymi).
    Nieznane pola są ignorowane.
    """
    try:
        log_dir = "logs/ai_commander"
        if not os.path.exists(log_dir):
            os.makedirs(log_dir)

        today = datetime.date.today()
        log_file = f"{log_dir}/actions_{today:%Y%m%d}.csv"
        file_exists = os.path.exists(log_file)

        # Przygotuj wiersz jako słownik
        row_dict = {k: None for k in LOG_COLUMNS}
        row_dict['timestamp'] = datetime.datetime.now().isoformat()
        row_dict['nation'] = player_nation
        row_dict['unit_id'] = unit_id
        row_dict['action_type'] = action_type
        row_dict['reason'] = reason
        if from_pos:
            row_dict['from_q'], row_dict['from_r'] = from_pos
        if to_pos:
            row_dict['to_q'], row_dict['to_r'] = to_pos
        # Merge extra
        if extra:
            for k, v in extra.items():
                if k in row_dict:
                    row_dict[k] = v

        # Kolejność kolumn
        values = [row_dict[k] for k in LOG_COLUMNS]

        with open(log_file, 'a', newline='', encoding='utf-8') as f:
            writer = csv.writer(f)
            if not file_exists:
                writer.writerow(LOG_COLUMNS)
            writer.writerow(values)
    except Exception as e:
        print(f"[AI] Błąd logowania: {e}")


def is_unit_holding(unit_dict: dict) -> bool:
    """Pomocniczo sprawdza czy jednostka ma atrybut token.hold_position == True"""
    try:
        token = unit_dict.get('token')
        if not token:
            return False
        return bool(getattr(token, 'hold_position', False))
    except Exception:
        return False


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
        # 1. Jeśli jednostka ma krytycznie niskie CV spróbuj odwrotu zanim rozważysz atak
        if _attempt_retreat_low_cv(unit, game_engine):
            return False
        # 2. Blokada: brak punktów ruchu => nie inicjuj nowego ataku
        utok = unit.get('token')
        if utok and getattr(utok, 'currentMovePoints', 0) <= 0:
            return False
        # Znajdź wrogów w zasięgu
        enemies = find_enemies_in_range(unit, game_engine, player_id)
        if not enemies:
            return False
        
        # Wybierz najlepszy cel (najwyższy combat ratio)
        best_enemy = None
        best_ratio = 0
        
        for enemy in enemies:
            ratio = evaluate_combat_ratio(unit, enemy)
            if ratio > best_ratio and ratio >= 1.2:  # lekko niższy próg po uwzględnieniu kar kontrataku
                best_ratio = ratio
                best_enemy = enemy
        
        if best_enemy:
            # 3. Spróbuj manewru flankującego aby uniknąć kontrataku
            _try_flank_before_attack(unit, best_enemy, game_engine)
            print(f"🎯 [COMBAT] {unit.get('id')} atakuje {best_enemy.get('id')} (ratio_adj: {best_ratio:.2f})")
            return execute_ai_combat(unit, best_enemy, game_engine, player_nation)
        
        return False
    except Exception as e:
        print(f"❌ [COMBAT] Błąd podczas sprawdzania ataku: {e}")
        return False


def find_enemies_in_range(unit, game_engine, player_id):
    """Znajdź wrogów w zasięgu ataku I WIDOCZNYCH (fog-of-war dla AI)."""
    try:
        enemies = []
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
            except Exception:
                visible_hexes = set()
        all_tokens = getattr(game_engine, 'tokens', [])
        current_player = getattr(game_engine, 'current_player_obj', None)
        
        for token in all_tokens:
            if getattr(token, 'owner', '') == my_owner:
                continue
            enemy_pos = (getattr(token, 'q', 0), getattr(token, 'r', 0))
            if visible_hexes and enemy_pos not in visible_hexes:
                continue  # niewidoczny -> ignoruj
            if board:
                distance = board.hex_distance(unit_pos, enemy_pos)
                if distance <= attack_range:
                    # NOWE: Sprawdź detection level jeśli dostępny
                    detection_level = 1.0  # Default dla backward compatibility
                    if current_player and hasattr(current_player, 'visible_token_data'):
                        token_detection = current_player.visible_token_data.get(token.id, {})
                        detection_level = token_detection.get('detection_level', 1.0)
                    
                    # Filtruj informacje na podstawie poziomu detekcji
                    try:
                        from engine.detection_filter import apply_detection_filter
                        enemy_info = apply_detection_filter(token, detection_level)
                        cv_value = enemy_info.get('combat_value', 0)
                        if isinstance(cv_value, str):  # "~3-7" -> użyj średnią
                            cv_value = 5  # Konserwatywne szacowanie
                    except:
                        cv_value = getattr(token, 'combat_value', 0)
                    
                    enemies.append({
                        'token': token,
                        'id': getattr(token, 'id', 'unknown'),
                        'q': enemy_pos[0],
                        'r': enemy_pos[1],
                        'cv': cv_value,
                        'detection_level': detection_level,
                        'distance': distance
                    })
        return enemies
    except Exception as e:
        print(f"❌ [COMBAT] Błąd wyszukiwania wrogów: {e}")
        return []


def evaluate_combat_ratio(unit, enemy):
    """Atak/obrona + penalizacja za spodziewany kontratak (jeśli wróg ma zasięg)."""
    try:
        unit_token = unit.get('token')
        enemy_token = enemy.get('token')
        if not unit_token or not enemy_token:
            return 0.0
        attack_value = unit_token.stats.get('attack', {}).get('value', 0)
        defense_value = enemy_token.stats.get('defense_value', 0)
        board = getattr(unit_token, 'board', None)
        terrain_mod = 0
        if hasattr(board, 'get_tile'):
            tile = board.get_tile(enemy['q'], enemy['r'])
            terrain_mod = getattr(tile, 'defense_mod', 0) if tile else 0
        total_defense = max(1, defense_value + terrain_mod)
        base_ratio = attack_value / total_defense
        # Ryzyko kontrataku
        defender_attack_val = enemy_token.stats.get('attack', {}).get('value', 0)
        defender_range = enemy_token.stats.get('attack', {}).get('range', 1)
        attacker_defense = unit_token.stats.get('defense_value', 0)
        attacker_pos = (unit.get('q'), unit.get('r'))
        enemy_pos = (enemy.get('q'), enemy.get('r'))
        distance = board.hex_distance(attacker_pos, enemy_pos) if board else 99
        if distance <= defender_range and attacker_defense > 0:
            counter_factor = (defender_attack_val / max(1, attacker_defense))
            # Skala tłumienia: im wyższy potencjalny counter tym mocniej obniż wynik (logistycznie ograniczone)
            penalty = min(0.6, 0.25 * counter_factor)
            return base_ratio * (1 - penalty)
        return base_ratio
    except Exception as e:
        print(f"❌ [COMBAT] Błąd obliczania ratio: {e}")
        return 0.0

def _attempt_retreat_low_cv(unit, game_engine):
    """Prosta ucieczka gdy combat_value bardzo niskie (<25% startowej) i wróg blisko."""
    try:
        utok = unit.get('token')
        if not utok:
            return False
        cv = getattr(utok, 'combat_value', 0)
        base_cv = utok.stats.get('combat_value', 1)
        if base_cv <= 0 or cv / base_cv >= 0.25:
            return False
        board = getattr(game_engine, 'board', None)
        if not board:
            return False
        # znajdź najbliższego wroga
        closest = None; closest_d = 999
        for t in getattr(game_engine, 'tokens', [])[:120]:
            if t is utok: continue
            if getattr(t, 'owner', '') == getattr(utok, 'owner', ''): continue
            d = board.hex_distance((utok.q, utok.r), (t.q, t.r))
            if d < closest_d:
                closest_d = d; closest = t
        if not closest or closest_d > 3:
            return False
        # spróbuj znaleźć sąsiada dalej od wroga
        best_hex = None; best_gain = 0
        for nq, nr in board.neighbors(utok.q, utok.r):
            tile = board.get_tile(nq, nr)
            if not tile or board.is_occupied(nq, nr):
                continue
            dist_new = board.hex_distance((nq, nr), (closest.q, closest.r))
            gain = dist_new - closest_d
            if gain > best_gain:
                best_gain = gain; best_hex = (nq, nr)
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

def _try_flank_before_attack(unit, enemy, game_engine):
    """Spróbuj ustawić się tak, by być w zasięgu ataku i poza zasięgiem kontrataku."""
    try:
        utok = unit.get('token'); etok = enemy.get('token')
        if not utok or not etok: return
        board = getattr(game_engine, 'board', None)
        if not board: return
        atk_range = utok.stats.get('attack', {}).get('range', 1)
        def_range = etok.stats.get('attack', {}).get('range', 1)
        # już poza kontratakiem?
        if board.hex_distance((utok.q, utok.r), (etok.q, etok.r)) > def_range:
            return
        # wygeneruj potencjalne heksy
        candidates = []
        for dq in range(-atk_range, atk_range+1):
            for dr in range(-atk_range, atk_range+1):
                tq = etok.q + dq; tr = etok.r + dr
                if board.hex_distance((etok.q, etok.r), (tq, tr)) > atk_range:
                    continue
                if board.get_tile(tq, tr) is None: continue
                if board.is_occupied(tq, tr): continue
                if board.hex_distance((etok.q, etok.r), (tq, tr)) <= def_range:
                    continue
                candidates.append((tq, tr))
        if not candidates: return
        # ocena: minimalny dystans ruchu od obecnej pozycji
        best = None; best_len = 999
        for cand in candidates[:80]:
            path = board.find_path((utok.q, utok.r), cand, max_mp=getattr(utok,'currentMovePoints',0), max_fuel=getattr(utok,'currentFuel',0))
            if path and len(path) < best_len:
                best_len = len(path)
                best = (cand, path)
        if best:
            from engine.action_refactored_clean import MoveAction
            mv = MoveAction(utok.id, best[0][0], best[0][1])
            res = game_engine.execute_action(mv, player=getattr(game_engine,'current_player_obj',None))
            if res.success:
                print(f"[FLANK] {utok.id} manewr na {best[0]} przed atakiem")
    except Exception:
        return


def execute_ai_combat(unit, enemy, game_engine, player_nation="Unknown"):
    """Wykonaj atak używając CombatAction"""
    try:
        unit_token = unit.get('token')
        enemy_token = enemy.get('token')
        
        if not unit_token or not enemy_token:
            return False
        
        # Import CombatAction
        from engine.action_refactored_clean import CombatAction
        
        # Pobierz obiekt gracza dla weryfikacji właściciela żetonu
        current_player = getattr(game_engine, 'current_player_obj', None)
        
        # Wykonaj atak z weryfikacją właściciela (tak jak człowiek)
        action = CombatAction(unit_token.id, enemy_token.id)
        result = game_engine.execute_action(action, player=current_player)
        
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


def check_ai_reaction_attacks(moved_token, game_engine, ai_player_nation="Unknown"):
    """Sprawdź czy AI units mogą wykonać ataki reakcyjne po ruchu przeciwnika - IDENTYCZNA LOGIKA JAK GUI"""
    try:
        if not moved_token or not game_engine:
            return
        
        moved_owner = getattr(moved_token, 'owner', '')
        moved_nation = moved_owner.split('(')[-1].replace(')', '').strip() if '(' in moved_owner else ''
        
        # IDENTYCZNA logika jak w gui/panel_mapa.py linie 695-750
        for enemy in getattr(game_engine, 'tokens', []):
            if enemy.id == moved_token.id or enemy.owner == moved_token.owner:
                continue
            
            # Blokada: nie atakuje własnych żetonów (identyczna jak GUI)
            nation_enemy = enemy.owner.split('(')[-1].replace(')', '').strip()
            nation_moved = moved_token.owner.split('(')[-1].replace(')', '').strip()
            if nation_enemy == nation_moved:
                continue
            
            # Sprawdź sight i attack_range (IDENTYCZNE obliczenia jak GUI)
            sight = enemy.stats.get('sight', 0)
            dist = game_engine.board.hex_distance((enemy.q, enemy.r), (moved_token.q, moved_token.r)) if hasattr(game_engine, 'board') else 999
            in_sight = dist <= sight
            attack_range = enemy.stats.get('attack', {}).get('range', 1)
            in_range = dist <= attack_range
            
            if in_sight and in_range:
                print(f"🎯 [AI_REACTION] {enemy.id} ({enemy.owner}) atakuje {moved_token.id} ({moved_owner})!")
                setattr(moved_token, 'wykryty_do_konca_tury', True)
                
                # Execute reaction attack using IDENTICAL CombatAction as GUI
                from engine.action_refactored_clean import CombatAction
                action = CombatAction(enemy.id, moved_token.id, is_reaction=True)
                result = game_engine.execute_action(action)
                success2, msg2 = result.success, result.message
                
                if success2:
                    print(f"⚔️ [AI_REACTION] Sukces: {msg2}")
                else:
                    print(f"❌ [AI_REACTION] Błąd: {msg2}")
                    
                # Log reaction attack (simplified version of GUI logging)
                try:
                    log_commander_action(
                        unit_id=enemy.id,
                        action_type="reaction_combat", 
                        from_pos=(enemy.q, enemy.r),
                        to_pos=(moved_token.q, moved_token.r),
                        reason=f"Reaction attack on {moved_token.id}",
                        player_nation=nation_enemy
                    )
                except Exception:
                    pass
                    
    except Exception as e:
        print(f"❌ [AI_REACTION] Błąd sprawdzania reakcji: {e}")


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
    best_score = -1

    # Pobierz dynamiczne wagi jeśli istnieje instancja AICommander (current_player_obj może ją mieć jako commander)
    econ_weight = 1.0
    vp_weight = 0.5
    try:
        commander_obj = getattr(game_engine, 'current_player_commander', None)
        if commander_obj and hasattr(commander_obj, 'econ_weight'):
            econ_weight = commander_obj.econ_weight
            vp_weight = commander_obj.vp_weight
    except Exception:
        pass

    def kp_score(kp_dict: dict) -> float:
        # typ może być 'economy','victory','mixed'
        ktype = kp_dict.get('type', 'unknown')
        base_val = kp_dict.get('current_value', kp_dict.get('value', 0))
        if ktype == 'economy':
            return base_val * econ_weight
        if ktype == 'victory':
            return base_val * vp_weight
        if ktype == 'mixed':
            return base_val * (0.5*econ_weight + 0.5*vp_weight)
        return base_val * 0.3  # niskie jeśli nieznany
    
    # Sprawdź key points (max 20) - TYLKO z wartością > 0
    kp_count = 0
    for hex_id, kp_data in key_points.items():
        if kp_count >= 20:
            break
        kp_count += 1
        
        # NOWE: Pomiń wyczerpane key pointy
        if kp_data.get('current_value', 0) <= 0:
            continue
        
        # Parsuj hex_id do współrzędnych (obsługa formatów "q,r" i "q_r")
        try:
            if ',' in hex_id:
                parts = hex_id.split(',')
            else:
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
                    score = kp_score(kp_data)
                    # Preferuj wyższy score, przy równym score krótszy dystans
                    if score > best_score or (score == best_score and actual_distance < best_distance):
                        best_target = kp_pos
                        best_distance = actual_distance
                        best_score = score
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
            if hasattr(board, 'get_tile') and board.get_tile(candidate[0], candidate[1]) is None:
                print(f"{HEX_MISSING_LOG_PREFIX} progressive_target {candidate}")
                continue
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


def advanced_autonomous_mode(my_units, game_engine):
    """
    ZAAWANSOWANY TRYB AUTONOMICZNY z TARGET RESERVATION:
    - Adaptacyjne grupowanie
    - Priorytetyzacja celów 
    - Koordynacja bez duplikatów
    - Inteligentna alokacja sił
    """
    print(f"🎯 [ADVANCED AUTO] Rozpoczynam z {len(my_units)} żetonami")
    
    # Filtruj tylko dostępne key pointy (current_value > 0)
    key_points = getattr(game_engine, 'key_points_state', {})
    available_keypoints = {}
    
    for hex_id, kp_data in key_points.items():
        if kp_data.get('current_value', 0) > 0:
            available_keypoints[hex_id] = kp_data
    
    print(f"🎯 [ADVANCED AUTO] Dostępne key pointy: {len(available_keypoints)}")
    if not available_keypoints:
        print("❌ [ADVANCED AUTO] Brak dostępnych key pointów!")
        return []
    
    # NOWY: Priorytetyzacja celów
    prioritized_targets = prioritize_targets(available_keypoints, game_engine)
    print(f"🎯 [TARGETS] Priorytetyzowano {len(prioritized_targets)} celów")
    
    # NOWY: Adaptacyjne grupowanie
    groups = adaptive_grouping(my_units, game_engine)
    print(f"🎯 [GROUPING] Utworzono {len(groups)} adaptacyjnych grup")
    
    # NOWY: Koordynacja celów - bez duplikatów
    group_assignments = assign_targets_with_coordination(groups, prioritized_targets, game_engine)
    
    print(f"🎯 [FINAL] Przypisano cele dla {len(group_assignments)} grup")
    return group_assignments


def dynamic_reassignment(group_assignments, game_engine):
    """Dynamicznie przemieszczaj siły między celami"""
    for assignment_idx, assignment in enumerate(group_assignments):
        group_size = len(assignment['group'])
        target = assignment['target']
        
        # Znajdź wartość celu
        target_value = get_keypoint_value(target, game_engine)
        
        print(f"🔄 [REASSIGN] Grupa {assignment_idx+1}: {group_size} jednostek -> cel wartość {target_value}")
        
        # Jeśli grupa za duża dla małego celu - podziel
        if group_size > 3 and target_value < 5:
            print(f"🔄 [REASSIGN] Grupa {assignment_idx+1}: Za duża dla małego celu - można podzielić")
            # TODO: Implementacja podziału grup (wymagałaby refaktoryzacji struktur)
        
        # Jeśli grupa za mała dla cennego celu - zaznacz do wzmocnienia
        elif group_size < 4 and target_value > 15:
            print(f"🔄 [REASSIGN] Grupa {assignment_idx+1}: Za mała dla cennego celu - potrzebuje wzmocnienia")
            assignment['needs_reinforcement'] = True
    
    return group_assignments


def get_keypoint_value(target_pos, game_engine):
    """Pobierz wartość key pointu dla danej pozycji"""
    key_points = getattr(game_engine, 'key_points_state', {})
    
    # Szukaj key pointu o podanych współrzędnych
    for hex_id, kp_data in key_points.items():
        try:
            if ',' in hex_id:
                q, r = map(int, hex_id.split(','))
            else:
                q, r = map(int, hex_id.split('_'))
            
            if (q, r) == target_pos:
                return kp_data.get('current_value', 0)
        except (ValueError, IndexError):
            continue
    
    return 0  # Nie znaleziono


def find_alternative_target(leader, key_points, reserved_targets):
    """Znajdź alternatywny cel dla lidera gdy główny jest zajęty"""
    board = getattr(leader.get('token', None), 'board', None)
    if not board:
        return None
    
    leader_pos = (leader['q'], leader['r'])
    best_alternative = None
    best_distance = 999
    
    # Sprawdź wszystkie dostępne key pointy
    for hex_id, kp_data in key_points.items():
        try:
            if ',' in hex_id:
                q, r = map(int, hex_id.split(','))
            else:
                q, r = map(int, hex_id.split('_'))
            
            target_pos = (q, r)
            target_key = f"{q},{r}"
            
            # Pomiń już zarezerwowane
            if target_key in reserved_targets:
                continue
            
            # Sprawdź czy cel ma wartość
            if kp_data.get('current_value', 0) <= 0:
                continue
            
            # Oblicz odległość
            distance = abs(leader_pos[0] - q) + abs(leader_pos[1] - r)
            if distance < best_distance:
                best_alternative = target_pos
                best_distance = distance
                
        except (ValueError, IndexError):
            continue
    
    return best_alternative


def group_units_by_proximity(units, max_group_distance=8):
    """
    NOWA WERSJA: Preferuje grupowanie po 5 żetonów dla zaawansowanego trybu autonomicznego
    """
    if not units:
        return []
    
    # W trybie zaawansowanym - po prostu dziel po 5
    if len(units) >= 5:
        print(f"[GROUPING] ADVANCED MODE: Dzielę {len(units)} żetonów na grupy po 5")
        groups = []
        for i in range(0, len(units), 5):
            group = units[i:i+5]
            groups.append(group)
            avg_pos = (
                sum(u['q'] for u in group) // len(group),
                sum(u['r'] for u in group) // len(group)
            )
            print(f"[GROUPING] Grupa {len(groups)}: {len(group)} żetonów wokół {avg_pos}")
        return groups
    
    # Fallback - stary sposób dla małych liczb
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


def scan_for_enemies(unit_pos, game_engine, range=3):
    """Sprawdź czy są widoczni wrogowie w pobliżu"""
    current_player = getattr(game_engine, 'current_player_obj', None)
    if not current_player:
        return []
    
    my_nation = getattr(current_player, 'nation', '')
    board = getattr(game_engine, 'board', None)
    if not board:
        return []
    
    # Sprawdź tylko widoczne żetony dla tego gracza
    visible_tokens = getattr(current_player, 'visible_tokens', set())
    enemies = []
    
    for token in visible_tokens:
        token_owner = getattr(token, 'owner', '')
        if my_nation not in token_owner:  # To wróg
            enemy_pos = (getattr(token, 'q', 0), getattr(token, 'r', 0))
            distance = board.hex_distance(unit_pos, enemy_pos)
            if distance <= range:
                enemies.append((token, distance))
    
    return enemies


def choose_movement_mode(unit, target, game_engine):
    """RYZYKOWNY wybór trybu ruchu dla AI"""
    print(f"🧠 [AI TEST] CHOOSE_MOVEMENT_MODE wywołane dla {unit.get('id', 'UNKNOWN')}")
    unit_pos = (unit['q'], unit['r'])
    board = getattr(game_engine, 'board', None)
    if not board:
        print(f"🧠 [AI TEST] BRAK BOARD - zwracam combat")
        return 'combat'
    
    # Sprawdź wrogów w pobliżu
    enemies_nearby = scan_for_enemies(unit_pos, game_engine, range=6)
    print(f"🧠 [AI TEST] Wrogów w pobliżu: {len(enemies_nearby)}")
    
    if enemies_nearby:
        # SCENARIUSZ 2: AI podąża do WIDOCZNEGO WROGA
        closest_enemy_distance = min(enemy[1] for enemy in enemies_nearby)
        print(f"🧠 [AI TEST] Najbliższy wróg: {closest_enemy_distance} pól")
        
        if closest_enemy_distance > 6:
            print(f"🧠 [AI TEST] Daleki wróg -> MARCH")
            return 'march'    # Szybko do kontaktu! (agresywnie)
        elif closest_enemy_distance > 3:
            print(f"🧠 [AI TEST] Średni dystans -> COMBAT")
            return 'combat'   # Normalny tryb przy średnim dystansie
        else:
            print(f"🧠 [AI TEST] Blisko wroga -> RECON")
            return 'recon'    # Ostrożnie przy bezpośrednim kontakcie (+25% obrony)
    else:
        # SCENARIUSZ 1: AI podąża do KEY POINTU (bez wrogów)
        distance_to_target = board.hex_distance(unit_pos, target)
        print(f"🧠 [AI TEST] Brak wrogów, dystans do celu: {distance_to_target}")
        
        if distance_to_target > 10:
            print(f"🧠 [AI TEST] Daleki cel -> MARCH")
            return 'march'    # Szybko do celu (+50% ruchu, -50% obrony)
        elif distance_to_target > 5:
            print(f"🧠 [AI TEST] Średni cel -> MARCH (ryzykownie)")
            return 'march'    # NADAL march! (ryzykownie ale szybko)
        else:
            print(f"🧠 [AI TEST] Blisko celu -> COMBAT")
            return 'combat'   # Tylko przy samym celu bezpiecznie


def move_towards(unit, target, game_engine):
    """Wykonaj ruch w kierunku celu - ULEPSZONA WERSJA z progressive movement"""
    
    print(f"🚀 [AI TEST] MOVE_TOWARDS WYWOŁANE! {unit['id']}: ({unit['q']},{unit['r']}) -> {target}")
    
    # DODATKOWY TEST - sprawdź czy dojdziemy do kodu trybów ruchu
    with open("logs/movement_test.log", "a", encoding="utf-8") as f:
        f.write(f"MOVE_TOWARDS START: {unit['id']} -> {target}\n")
    
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
    
    # NOWE: RYZYKOWNY WYBÓR TRYBU RUCHU
    print(f"🔍 [AI TEST] Sprawdzam token: {type(token)}, hasattr movement_mode: {hasattr(token, 'movement_mode')}")
    
    # DODATKOWY LOG DO PLIKU
    with open("logs/movement_test.log", "a", encoding="utf-8") as f:
        f.write(f"WYBOR TRYBU START: {unit['id']}, token_type: {type(token)}\n")
    
    optimal_mode = choose_movement_mode(unit, target_tuple, game_engine)
    print(f"🎯 [AI TEST] Wybrany tryb: {optimal_mode}")
    
    with open("logs/movement_test.log", "a", encoding="utf-8") as f:
        f.write(f"WYBRANY TRYB: {optimal_mode}\n")
    
    if hasattr(token, 'movement_mode') and not getattr(token, 'movement_mode_locked', False):
        if token.movement_mode != optimal_mode:
            token.movement_mode = optimal_mode
            token.apply_movement_mode()  # Przelicz statystyki
            print(f"✅ [AI Movement] Zmieniono tryb ruchu na: {optimal_mode}")
            with open("logs/movement_test.log", "a", encoding="utf-8") as f:
                f.write(f"ZMIENIONO TRYB: {token.movement_mode} -> {optimal_mode}\n")
            # Aktualizuj unit stats po zmianie trybu
            unit['mp'] = getattr(token, 'currentMovePoints', token.maxMovePoints)
        else:
            print(f"🔄 [AI Movement] Tryb ruchu już ustawiony: {optimal_mode}")
            with open("logs/movement_test.log", "a", encoding="utf-8") as f:
                f.write(f"TRYB JUZ USTAWIONY: {optimal_mode}\n")
    else:
        print(f"❌ [AI TEST] NIE MOGĘ ZMIENIĆ TRYBU - hasattr: {hasattr(token, 'movement_mode')}, locked: {getattr(token, 'movement_mode_locked', 'BRAK')}")
        with open("logs/movement_test.log", "a", encoding="utf-8") as f:
            f.write(f"NIE MOZNA ZMIENIC TRYBU: hasattr={hasattr(token, 'movement_mode')}\n")
    # SPRAWDZENIE REALNOŚCI CELU - hex distance calculation
    # SANITY: istnieje hex docelowy?
    if hasattr(board, 'get_tile') and board.get_tile(target_tuple[0], target_tuple[1]) is None:
        print(f"{HEX_MISSING_LOG_PREFIX} target {target_tuple}")
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

    # PATHFINDING + ADAPTIVE RETRY
    try:
        from engine.action_refactored_clean import PathfindingService
        # Wstępny sanity check listy prób kiedy brak ścieżki
        path = PathfindingService.find_movement_path(
            game_engine, token, unit_pos, target_tuple,
            game_engine.current_player_obj
        )
        print(f"[AI Pathfinding] Bazowa ścieżka: {path}")
        if (not path or len(path) < 2) and unit_pos != target_tuple:
            # DIAGNOSTYKA – zbierz info o terenie, zajętości i sąsiadach celu
            try:
                terrain = None
                if hasattr(board, 'get_tile'):
                    tile = board.get_tile(target_tuple[0], target_tuple[1])
                    if tile:
                        terrain = getattr(tile, 'terrain', getattr(tile, 'type', 'unknown'))
                occupied = board.is_occupied(target_tuple[0], target_tuple[1]) if hasattr(board, 'is_occupied') else 'NO_METHOD'
                neighbors_info = []
                if hasattr(board, 'neighbors'):
                    for n in board.neighbors(target_tuple[0], target_tuple[1]):
                        occ = board.is_occupied(n[0], n[1]) if hasattr(board, 'is_occupied') else '?'
                        neighbors_info.append(f"{n}{'*' if occ else ''}")
                print(f"[AI Pathfinding][DIAG] Brak ścieżki bazowej do {target_tuple} | terrain={terrain} occupied={occupied} neighbors={neighbors_info}")
            except Exception as _e:
                print(f"[AI Pathfinding][DIAG] Błąd diagnostyki: {_e}")
        # Jeśli brak ścieżki – adaptacyjnie skracaj wektor celu
        if (not path or len(path) < 2) and unit_pos != target_tuple:
            dq = target_tuple[0] - unit_pos[0]
            dr = target_tuple[1] - unit_pos[1]
            original = target_tuple
            for frac in (0.75, 0.5, 0.33, 0.25):
                test_q = unit_pos[0] + int(round(dq * frac))
                test_r = unit_pos[1] + int(round(dr * frac))
                test_target = (test_q, test_r)
                if test_target == unit_pos:
                    continue
                if hasattr(board, 'get_tile') and board.get_tile(test_q, test_r) is None:
                    print(f"{HEX_MISSING_LOG_PREFIX} adapt {test_target}")
                    continue
                test_path = PathfindingService.find_movement_path(
                    game_engine, token, unit_pos, test_target, game_engine.current_player_obj
                )
                if test_path and len(test_path) > 1:
                    print(f"[AI Pathfinding][ADAPT] Brak ścieżki do {original}, używam krótszego {test_target} (frac={frac})")
                    path = test_path
                    target_tuple = test_target
                    break
        if not path or len(path) < 2:
            print(f"[AI Pathfinding] ❌ Brak ścieżki po adaptacji!")
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
                
                # Pobierz obiekt gracza dla weryfikacji właściciela żetonu
                current_player = getattr(game_engine, 'current_player_obj', None)
                
                action = MoveAction(token_id, target_hex[0], target_hex[1])
                result = game_engine.execute_action(action, player=current_player)
                
                success = getattr(result, 'success', False) if result else False
                if success:
                    print(f"[AI Move] ✅ Sukces: {getattr(result, 'message', 'OK')}")
                    # Jeśli weszliśmy na key point – natychmiastowy log okupacji
                    kp_state = getattr(game_engine, 'key_points_state', {}) or {}
                    hex_id = f"{target_hex[0]},{target_hex[1]}"
                    if hex_id in kp_state:
                        kp = kp_state[hex_id]
                        print(f"[AI OCCUPY] {unit['id']} OBJĄŁ KEY POINT {hex_id} ({kp.get('type','?')}) wart {kp['current_value']}/{kp['initial_value']}")
                        # Ustaw znacznik hold_position aby jednostka została na punkcie (MVP)
                        try:
                            setattr(token, 'hold_position', True)
                        except Exception:
                            pass
                        # ROTACJA: jeśli punkt już wyczerpany (current_value <=0) nie trzymaj jednostki
                        try:
                            if kp.get('current_value', 0) <= 0:
                                if getattr(token, 'hold_position', False):
                                    print(f"[AI ROTATE] Punkt {hex_id} wyczerpany -> zwalniam {unit['id']}")
                                setattr(token, 'hold_position', False)
                            else:
                                # EARLY ROTATION / LIMIT GARRISON
                                initial = kp.get('initial_value', kp.get('value', 0)) or kp.get('value', 0)
                                ratio = kp.get('current_value', 0) / max(initial, 1)
                                enforce_garrison_limits(game_engine, hex_id, kp, token, ratio)
                        except Exception:
                            pass
                    
                    # LOGOWANIE
                    player_nation = getattr(game_engine.current_player_obj, 'nation', 'Unknown')
                    move_type = "progressive_move" if hex_distance > max_reach else ("partial_move" if is_partial_path else "full_move")
                    reason = f"Strategic move to {target}"
                    
                    # Przygotuj dane rozszerzone
                    extra_log = {
                        'turn': getattr(game_engine, 'turn_number', getattr(game_engine, 'current_turn', None)),
                        'phase': 'movement',
                        'unit_type': getattr(token, 'unit_type', getattr(token, 'type', None)),
                        'target_q': target[0] if isinstance(target, (list, tuple)) else None,
                        'target_r': target[1] if isinstance(target, (list, tuple)) else None,
                        'movement_mode': getattr(token, 'movement_mode', None),
                        'path_len': len(path) if path else 0,
                        'path_used': len(path) - 1 if path else 0,
                        'progressive_used': hex_distance > max_reach,
                        'adaptive_frac': None,
                        'mp_before': unit.get('mp'),
                        'fuel_before': unit.get('fuel'),
                        'mp_after': getattr(token, 'currentMovePoints', None),
                        'fuel_after': getattr(token, 'fuel', None),
                        'decision_reason': reason,
                        'extra_tags': 'garrison' if getattr(token, 'hold_position', False) else None
                    }
                    log_commander_action(
                        unit_id=unit['id'],
                        action_type=move_type,
                        from_pos=unit_pos,
                        to_pos=target_hex,
                        reason=reason,
                        player_nation=player_nation,
                        extra=extra_log
                    )
                    
                    # SPRAWDŹ ATAKI REAKCYJNE PRZECIWNIKÓW - IDENTYCZNA LOGIKA JAK GUI!
                    # Po każdym ruchu AI sprawdź czy ktokolwiek może wykonać reakcję
                    check_ai_reaction_attacks(token, game_engine)
                else:
                    print(f"[AI Move] ❌ Błąd: {getattr(result, 'message', 'Nieznany błąd')}")
                    
                return success
            else:
                print(f"[AI Move] Brak ID tokenu dla {unit['id']}")
                return False
            
    except Exception as e:
        print(f"[AI] Błąd ruchu: {e}")
        
    return False


# ========== ADAPTACYJNY SYSTEM AI COMMANDER ==========

class AdaptiveAICommander:
    """Kompletny adaptacyjny system AI Commander z VP-based strategic switching"""
    
    def __init__(self, ai_commander_instance):
        self.commander = ai_commander_instance
        self.player = ai_commander_instance.player
        self.strategic_state = "TIED"  # WINNING, LOSING, TIED
        self.last_vp_check = 0
        self.consecutive_losing_turns = 0
        self.budget_allocation = {"allocate": 0.6, "purchase": 0.3, "reserve": 0.1}
        self.keypoint_priorities = {}
        self.reconnaissance_data = {}
        self.adaptive_purchase_queue = []
        self.aggression_level = 0.5  # 0.0 = defensive, 1.0 = full aggression
        
        print(f"🧠 [ADAPTIVE AI] Zainicjalizowano dla {self.player.nation}")

    def analyze_strategic_state(self, game_engine):
        """STRATEGIC_STATE_ANALYZER - Ocena sytuacji VP i strategiczna adaptacja"""
        try:
            # Pobierz dane VP wszystkich graczy
            all_players = getattr(game_engine, 'players', [])
            current_player_id = self.player.id
            
            vp_data = {}
            for player in all_players:
                player_id = getattr(player, 'id', None)
                if player_id is not None:
                    vp_points = getattr(player, 'victory_points', 0)
                    vp_data[player_id] = vp_points
            
            my_vp = vp_data.get(current_player_id, 0)
            other_vps = [vp for pid, vp in vp_data.items() if pid != current_player_id]
            
            if not other_vps:
                self.strategic_state = "TIED"
                return self.strategic_state
            
            max_enemy_vp = max(other_vps)
            avg_enemy_vp = sum(other_vps) / len(other_vps)
            
            # Logika strategicznej adaptacji
            vp_difference = my_vp - max_enemy_vp
            
            if vp_difference >= 10:
                new_state = "WINNING"
            elif vp_difference <= -10:
                new_state = "LOSING"
                self.consecutive_losing_turns += 1
            else:
                new_state = "TIED"
                self.consecutive_losing_turns = 0
            
            # Adaptacja strategii na podstawie stanu
            if new_state != self.strategic_state:
                print(f"🎯 [STRATEGIC] Zmiana stanu: {self.strategic_state} -> {new_state} (VP: {my_vp} vs max {max_enemy_vp})")
                self.strategic_state = new_state
                self._adapt_strategy_to_state()
            
            return self.strategic_state
            
        except Exception as e:
            print(f"❌ [STRATEGIC] Błąd analizy: {e}")
            return "TIED"

    def _adapt_strategy_to_state(self):
        """Adaptuje strategię na podstawie aktualnego stanu gry"""
        if self.strategic_state == "WINNING":
            # Tryb defensywny - broń przewagi
            self.aggression_level = 0.3
            self.budget_allocation = {"allocate": 0.7, "purchase": 0.2, "reserve": 0.1}
            print(f"🛡️ [STRATEGY] WINNING MODE: Defensywnie, focus na utrzymanie pozycji")
            
        elif self.strategic_state == "LOSING":
            # Tryb agresywny - wszystko albo nic
            self.aggression_level = 0.9
            self.budget_allocation = {"allocate": 0.4, "purchase": 0.5, "reserve": 0.1}
            print(f"⚔️ [STRATEGY] LOSING MODE: Agresywnie, focus na nowe jednostki")
            
        else:  # TIED
            # Tryb zbalansowany
            self.aggression_level = 0.6
            self.budget_allocation = {"allocate": 0.5, "purchase": 0.4, "reserve": 0.1}
            print(f"⚖️ [STRATEGY] TIED MODE: Zbalansowany approach")

    def optimize_budget(self, game_engine):
        """BUDGET_OPTIMIZER - Dynamiczna alokacja budżetu na podstawie sytuacji"""
        try:
            # Pobierz dostępne punkty ekonomiczne
            if hasattr(self.player, 'economy') and self.player.economy:
                current_budget = self.player.economy.economic_points
            else:
                current_budget = getattr(self.player, 'punkty_ekonomiczne', 0)
            
            # Analiza sytuacji jednostek
            my_units = get_my_units(game_engine, self.player.id)
            total_units = len(my_units)
            
            # Sprawdź stan jednostek (ile potrzebuje resupply)
            units_needing_resupply = 0
            total_resupply_cost = 0
            
            for unit in my_units:
                token = unit.get('token')
                if token:
                    # Fuel check
                    current_fuel = getattr(token, 'currentFuel', 0)
                    max_fuel = getattr(token, 'maxFuel', token.stats.get('maintenance', 0))
                    fuel_needed = max(0, max_fuel - current_fuel)
                    
                    # Combat value check
                    current_combat = getattr(token, 'combat_value', 0)
                    max_combat = token.stats.get('combat_value', 0)
                    combat_needed = max(0, max_combat - current_combat)
                    
                    unit_cost = fuel_needed + combat_needed
                    if unit_cost > 0:
                        units_needing_resupply += 1
                        total_resupply_cost += unit_cost
            
            # Dynamiczna alokacja budżetu
            if total_units < 5:  # Mało jednostek - priorytet zakupy
                allocation = {"allocate": 0.3, "purchase": 0.6, "reserve": 0.1}
                reason = "Mała armia - priorytet nowe jednostki"
            elif units_needing_resupply > total_units * 0.7:  # Większość potrzebuje resupply
                allocation = {"allocate": 0.8, "purchase": 0.1, "reserve": 0.1}
                reason = "Masowe potrzeby resupply"
            elif self.consecutive_losing_turns >= 3:  # Długo przegrywa
                allocation = {"allocate": 0.2, "purchase": 0.7, "reserve": 0.1}
                reason = "Desperacka sytuacja - wszystko w nowe jednostki"
            else:
                # Użyj alokacji z strategic state
                allocation = self.budget_allocation.copy()
                reason = f"Strategia {self.strategic_state}"
            
            # Oblicz konkretne kwoty
            allocate_amount = int(current_budget * allocation["allocate"])
            purchase_amount = int(current_budget * allocation["purchase"])
            reserve_amount = current_budget - allocate_amount - purchase_amount
            
            budget_plan = {
                "total": current_budget,
                "allocate": allocate_amount,
                "purchase": purchase_amount,
                "reserve": reserve_amount,
                "allocation_ratios": allocation,
                "reason": reason,
                "units_count": total_units,
                "resupply_needed": units_needing_resupply,
                "estimated_resupply_cost": total_resupply_cost
            }
            
            print(f"💰 [BUDGET] {reason}: {allocate_amount}zł resupply, {purchase_amount}zł zakupy, {reserve_amount}zł rezerwa")
            return budget_plan
            
        except Exception as e:
            print(f"❌ [BUDGET] Błąd optymalizacji: {e}")
            return {"total": 0, "allocate": 0, "purchase": 0, "reserve": 0, "reason": "ERROR"}

    def prioritize_keypoints(self, game_engine):
        """KEYPOINT_PRIORITIZER - Inteligentne priorytetyzowanie celów"""
        try:
            key_points = getattr(game_engine, 'key_points_state', {})
            my_units = get_my_units(game_engine, self.player.id)
            
            # Resetuj priorytety
            self.keypoint_priorities = {}
            
            for hex_id, kp_data in key_points.items():
                if kp_data.get('current_value', 0) <= 0:
                    continue  # Pomiń wyczerpane
                
                try:
                    q, r = map(int, hex_id.split(','))
                    kp_pos = (q, r)
                except:
                    continue
                
                # Podstawowe dane punktu
                current_value = kp_data.get('current_value', 0)
                kp_type = kp_data.get('type', 'unknown')
                
                # Oblicz bazowy priorytet
                base_priority = current_value
                
                # Modyfikatory strategiczne
                if self.strategic_state == "LOSING":
                    if kp_type == 'victory':
                        base_priority *= 2.0  # Desperacko potrzebujemy VP
                    elif kp_type == 'economy':
                        base_priority *= 1.2  # Również ważne dla recovery
                elif self.strategic_state == "WINNING":
                    if kp_type == 'economy':
                        base_priority *= 1.5  # Utrzymuj ekonomię
                    elif kp_type == 'victory':
                        base_priority *= 0.8  # Mniej ważne gdy już wygrywamy
                else:  # TIED
                    if kp_type == 'economy':
                        base_priority *= 1.3  # Zbalansowany focus na ekonomię
                
                # Modyfikator odległości od moich jednostek
                if my_units:
                    min_distance = float('inf')
                    for unit in my_units:
                        unit_pos = (unit['q'], unit['r'])
                        distance = calculate_hex_distance(kp_pos, unit_pos)
                        min_distance = min(min_distance, distance)
                    
                    # Im bliżej, tym wyższy priorytet
                    distance_modifier = 1.0 / max(1, min_distance * 0.1)
                    base_priority *= distance_modifier
                
                # Sprawdź czy punkt jest okupowany
                board = getattr(game_engine, 'board', None)
                occupied_by_enemy = False
                if board and hasattr(board, 'is_occupied'):
                    if board.is_occupied(q, r):
                        # Sprawdź przez kogo
                        for token in getattr(game_engine, 'tokens', []):
                            if getattr(token, 'q', -1) == q and getattr(token, 'r', -1) == r:
                                token_owner = getattr(token, 'owner', '')
                                my_owner = f"{self.player.id} ({self.player.nation})"
                                if token_owner != my_owner:
                                    occupied_by_enemy = True
                                    base_priority *= 1.5  # Wyższy priorytet dla wrogich punktów
                                break
                
                final_priority = base_priority
                
                self.keypoint_priorities[hex_id] = {
                    'position': kp_pos,
                    'priority': final_priority,
                    'value': current_value,
                    'type': kp_type,
                    'occupied_by_enemy': occupied_by_enemy,
                    'strategic_modifier': self.strategic_state
                }
            
            # Sortuj według priorytetu
            sorted_priorities = sorted(
                self.keypoint_priorities.items(),
                key=lambda x: x[1]['priority'],
                reverse=True
            )
            
            print(f"🎯 [PRIORITIES] Top 3 cele dla {self.strategic_state}:")
            for i, (hex_id, data) in enumerate(sorted_priorities[:3]):
                print(f"  {i+1}. {hex_id} ({data['type']}) - priorytet {data['priority']:.1f}, wartość {data['value']}")
            
            return sorted_priorities
            
        except Exception as e:
            print(f"❌ [PRIORITIES] Błąd priorytetyzacji: {e}")
            return []

    def gather_reconnaissance(self, game_engine):
        """RECONNAISSANCE_SYSTEM - Zbieranie danych zwiadowczych"""
        try:
            current_player = getattr(game_engine, 'current_player_obj', None)
            if not current_player:
                return {}
            
            # Zbierz dane o widocznych wrogach
            visible_enemies = []
            if hasattr(current_player, 'visible_tokens'):
                for token in current_player.visible_tokens:
                    token_owner = getattr(token, 'owner', '')
                    my_owner = f"{self.player.id} ({self.player.nation})"
                    
                    if token_owner != my_owner and token_owner:
                        enemy_pos = (getattr(token, 'q', 0), getattr(token, 'r', 0))
                        combat_value = getattr(token, 'combat_value', 0)
                        
                        # Sprawdź detection level jeśli dostępny
                        detection_level = 1.0
                        if hasattr(current_player, 'visible_token_data'):
                            token_data = current_player.visible_token_data.get(token.id, {})
                            detection_level = token_data.get('detection_level', 1.0)
                        
                        visible_enemies.append({
                            'id': getattr(token, 'id', 'unknown'),
                            'position': enemy_pos,
                            'combat_value': combat_value,
                            'detection_level': detection_level,
                            'owner': token_owner
                        })
            
            # Analiza rozmieszczenia wrogów
            enemy_clusters = self._analyze_enemy_clusters(visible_enemies)
            
            # Sprawdź zagrożenia dla kluczowych punktów
            keypoint_threats = self._assess_keypoint_threats(visible_enemies, game_engine)
            
            self.reconnaissance_data = {
                'visible_enemies': visible_enemies,
                'enemy_count': len(visible_enemies),
                'enemy_clusters': enemy_clusters,
                'keypoint_threats': keypoint_threats,
                'last_update': getattr(game_engine, 'turn_number', 1)
            }
            
            print(f"🔍 [RECON] Wykryto {len(visible_enemies)} wrogów w {len(enemy_clusters)} klastrach")
            if keypoint_threats:
                print(f"🚨 [RECON] {len(keypoint_threats)} punktów kluczowych zagrożonych")
            
            return self.reconnaissance_data
            
        except Exception as e:
            print(f"❌ [RECON] Błąd rozpoznania: {e}")
            return {}

    def _analyze_enemy_clusters(self, enemies):
        """Analizuje klastry wrogów dla lepszego planowania"""
        if not enemies:
            return []
        
        clusters = []
        processed = set()
        
        for i, enemy in enumerate(enemies):
            if i in processed:
                continue
                
            cluster = [enemy]
            processed.add(i)
            
            # Znajdź pobliskich wrogów (w promieniu 4 hexów)
            for j, other_enemy in enumerate(enemies):
                if j in processed:
                    continue
                    
                distance = calculate_hex_distance(enemy['position'], other_enemy['position'])
                if distance <= 4:
                    cluster.append(other_enemy)
                    processed.add(j)
            
            clusters.append({
                'size': len(cluster),
                'enemies': cluster,
                'center': self._calculate_cluster_center(cluster),
                'threat_level': sum(e['combat_value'] for e in cluster)
            })
        
        return clusters

    def _calculate_cluster_center(self, cluster):
        """Oblicza środek klastra wrogów"""
        if not cluster:
            return (0, 0)
        
        avg_q = sum(e['position'][0] for e in cluster) // len(cluster)
        avg_r = sum(e['position'][1] for e in cluster) // len(cluster)
        return (avg_q, avg_r)

    def _assess_keypoint_threats(self, enemies, game_engine):
        """Ocenia zagrożenia dla punktów kluczowych"""
        key_points = getattr(game_engine, 'key_points_state', {})
        threats = {}
        
        for hex_id, kp_data in key_points.items():
            if kp_data.get('current_value', 0) <= 0:
                continue
                
            try:
                q, r = map(int, hex_id.split(','))
                kp_pos = (q, r)
            except:
                continue
            
            # Znajdź wrogów w promieniu 6 hexów od punktu
            nearby_enemies = []
            for enemy in enemies:
                distance = calculate_hex_distance(kp_pos, enemy['position'])
                if distance <= 6:
                    nearby_enemies.append({
                        'enemy': enemy,
                        'distance': distance,
                        'threat_score': enemy['combat_value'] / max(1, distance)
                    })
            
            if nearby_enemies:
                total_threat = sum(e['threat_score'] for e in nearby_enemies)
                threats[hex_id] = {
                    'position': kp_pos,
                    'threat_level': total_threat,
                    'enemy_count': len(nearby_enemies),
                    'closest_enemy_distance': min(e['distance'] for e in nearby_enemies)
                }
        
        return threats

    def adaptive_purchase_ai(self, game_engine, budget_plan):
        """ADAPTIVE_PURCHASE_AI - Inteligentne zakupy jednostek"""
        try:
            purchase_budget = budget_plan.get('purchase', 0)
            if purchase_budget <= 0:
                print(f"💸 [PURCHASE] Brak budżetu na zakupy")
                return []
            
            # Analiza potrzeb
            my_units = get_my_units(game_engine, self.player.id)
            current_army_size = len(my_units)
            
            # Analiza składu armii
            unit_types = {}
            total_combat_value = 0
            for unit in my_units:
                token = unit.get('token')
                if token:
                    unit_type = getattr(token, 'unit_type', getattr(token, 'type', 'unknown'))
                    unit_types[unit_type] = unit_types.get(unit_type, 0) + 1
                    total_combat_value += unit.get('cv', 0)
            
            # Strategiczna analiza zakupów
            purchase_priority = self._determine_purchase_priority()
            
            # Symuluj dostępne opcje zakupu
            available_units = self._get_available_purchase_options(game_engine)
            
            # Wybierz optymalne jednostki
            selected_purchases = self._select_optimal_purchases(
                available_units, purchase_budget, purchase_priority, current_army_size
            )
            
            print(f"🛒 [PURCHASE] Strategia {self.strategic_state}: {len(selected_purchases)} jednostek za {sum(u['cost'] for u in selected_purchases)}zł")
            
            return selected_purchases
            
        except Exception as e:
            print(f"❌ [PURCHASE] Błąd adaptacyjnych zakupów: {e}")
            return []

    def _determine_purchase_priority(self):
        """Określa priorytety zakupów na podstawie sytuacji strategicznej"""
        if self.strategic_state == "LOSING":
            return {
                'fast_attack': 0.4,  # Szybkie jednostki atakujące
                'heavy_combat': 0.3,  # Ciężkie jednostki bojowe
                'support': 0.2,      # Wsparcie
                'economic': 0.1      # Jednostki ekonomiczne
            }
        elif self.strategic_state == "WINNING":
            return {
                'heavy_combat': 0.4,  # Ciężkie jednostki do obrony
                'support': 0.3,       # Wsparcie i utrzymanie
                'economic': 0.2,      # Jednostki ekonomiczne
                'fast_attack': 0.1    # Mniej ataku
            }
        else:  # TIED
            return {
                'heavy_combat': 0.3,
                'fast_attack': 0.3,
                'support': 0.2,
                'economic': 0.2
            }

    def _get_available_purchase_options(self, game_engine):
        """Pobiera dostępne opcje zakupu jednostek"""
        # Symulacja dostępnych jednostek (w rzeczywistej grze to by było z tokenshopa)
        available_units = [
            {'type': 'infantry', 'category': 'heavy_combat', 'cost': 15, 'combat_value': 8, 'mobility': 2},
            {'type': 'tank', 'category': 'heavy_combat', 'cost': 25, 'combat_value': 12, 'mobility': 3},
            {'type': 'recon', 'category': 'fast_attack', 'cost': 12, 'combat_value': 5, 'mobility': 4},
            {'type': 'artillery', 'category': 'support', 'cost': 20, 'combat_value': 10, 'mobility': 1},
            {'type': 'engineer', 'category': 'support', 'cost': 18, 'combat_value': 6, 'mobility': 2},
            {'type': 'supply', 'category': 'economic', 'cost': 10, 'combat_value': 2, 'mobility': 2}
        ]
        
        return available_units

    def _select_optimal_purchases(self, available_units, budget, priorities, current_army_size):
        """Wybiera optymalne jednostki do zakupu"""
        selected = []
        remaining_budget = budget
        
        # Sortuj według priorytetu strategicznego
        weighted_units = []
        for unit in available_units:
            category = unit['category']
            priority_weight = priorities.get(category, 0.1)
            efficiency = unit['combat_value'] / max(1, unit['cost'])  # Combat value per cost
            
            score = priority_weight * efficiency
            weighted_units.append((score, unit))
        
        weighted_units.sort(key=lambda x: x[0], reverse=True)
        
        # Wybierz jednostki dopóki starczy budżetu
        for score, unit in weighted_units:
            if remaining_budget >= unit['cost'] and len(selected) < 5:  # Max 5 jednostek na raz
                selected.append(unit)
                remaining_budget -= unit['cost']
                print(f"  🎯 Wybrano {unit['type']} ({unit['category']}) za {unit['cost']}zł, score: {score:.2f}")
        
        return selected

    def adaptive_strategic_behavior(self, game_engine):
        """GŁÓWNA FUNKCJA - Koordynuje wszystkie adaptacyjne systemy"""
        try:
            print(f"\n🧠 [ADAPTIVE AI] === ANALIZA STRATEGICZNA ===")
            
            # 1. Analiza stanu strategicznego
            strategic_state = self.analyze_strategic_state(game_engine)
            
            # 2. Optymalizacja budżetu
            budget_plan = self.optimize_budget(game_engine)
            
            # 3. Priorytetyzacja celów
            prioritized_keypoints = self.prioritize_keypoints(game_engine)
            
            # 4. Rozpoznanie
            recon_data = self.gather_reconnaissance(game_engine)
            
            # 5. Adaptacyjne zakupy
            purchase_recommendations = self.adaptive_purchase_ai(game_engine, budget_plan)
            
            # 6. Kompilacja strategii
            strategic_plan = {
                'state': strategic_state,
                'aggression_level': self.aggression_level,
                'budget': budget_plan,
                'target_priorities': prioritized_keypoints[:5],  # Top 5 celów
                'reconnaissance': recon_data,
                'purchase_plan': purchase_recommendations,
                'recommended_actions': self._generate_action_recommendations()
            }
            
            print(f"📋 [ADAPTIVE AI] Strategia gotowa: {strategic_state}, agresja {self.aggression_level:.1f}")
            
            # 7. Wykonaj automatyczne akcje jeśli włączone
            if getattr(self.commander, 'auto_execute', True):
                self._execute_strategic_plan(strategic_plan, game_engine)
            
            return strategic_plan
            
        except Exception as e:
            print(f"❌ [ADAPTIVE AI] Błąd systemu adaptacyjnego: {e}")
            return None

    def _generate_action_recommendations(self):
        """Generuje rekomendacje działań na podstawie analizy"""
        recommendations = []
        
        if self.strategic_state == "LOSING":
            recommendations.extend([
                "PRIORYTET: Skupić wszystkie siły na wysokowartościowych VP",
                "TAKTYKA: Agresywne ataki na słabe punkty wroga",
                "ZAKUPY: Szybkie jednostki atakujące",
                "BUDŻET: Maksymalnie w nowe jednostki"
            ])
        elif self.strategic_state == "WINNING":
            recommendations.extend([
                "PRIORYTET: Utrzymać kontrolę nad ekonomicznymi punktami",
                "TAKTYKA: Defensywne pozycje, unikać ryzyka",
                "ZAKUPY: Ciężkie jednostki obronne",
                "BUDŻET: Focus na resupply istniejących sił"
            ])
        else:  # TIED
            recommendations.extend([
                "PRIORYTET: Zbalansowany rozwój ekonomiczny i militarny",
                "TAKTYKA: Oportunistyczne zajmowanie wolnych punktów",
                "ZAKUPY: Uniwersalne jednostki",
                "BUDŻET: Zrównoważona alokacja"
            ])
        
        # Dodaj rekomendacje na podstawie rozpoznania
        if self.reconnaissance_data.get('enemy_count', 0) > len(get_my_units(None, self.player.id)):
            recommendations.append("UWAGA: Wróg ma przewagę liczebną - unikaj otwartej walki")
        
        return recommendations

    def _execute_strategic_plan(self, strategic_plan, game_engine):
        """Wykonuje automatyczne akcje strategiczne (opcjonalne)"""
        try:
            print(f"🤖 [AUTO EXEC] Wykonuję strategiczny plan...")
            
            # Tutaj można dodać automatyczną egzekucję:
            # - Automatyczne zakupy jednostek
            # - Automatyczne deployment
            # - Automatyczne ustawienie priorytetów
            
            # Na razie tylko logowanie
            print(f"📋 [AUTO EXEC] Plan przygotowany do manualnej egzekucji")
            
        except Exception as e:
            print(f"❌ [AUTO EXEC] Błąd wykonania planu: {e}")

    def _adaptive_movement_tactics(self, unit, base_target, strategic_plan, game_engine):
        """Adaptacyjne taktyki ruchu na podstawie planu strategicznego"""
        try:
            aggression_level = strategic_plan.get('aggression_level', 0.5)
            strategic_state = strategic_plan.get('state', 'TIED')
            
            # Podstawowy cel
            final_target = base_target
            
            # Modyfikacje na podstawie strategii
            if strategic_state == "LOSING" and aggression_level > 0.7:
                # Agresywny mode - cel bezpośrednio na punkt
                print(f"⚔️ [ADAPTIVE] {unit['id']}: Agresywny atak na {base_target}")
                final_target = base_target
                
            elif strategic_state == "WINNING" and aggression_level < 0.4:
                # Defensywny mode - pozycje defensywne wokół celu
                defensive_pos = self._find_defensive_position_near(base_target, unit, game_engine)
                if defensive_pos != base_target:
                    print(f"🛡️ [ADAPTIVE] {unit['id']}: Pozycja defensywna {defensive_pos} zamiast {base_target}")
                    final_target = defensive_pos
                    
            else:
                # Zbalansowany mode - standardowy ruch
                print(f"⚖️ [ADAPTIVE] {unit['id']}: Zbalansowany ruch do {base_target}")
                final_target = base_target
            
            return final_target
            
        except Exception as e:
            print(f"❌ [ADAPTIVE] Błąd taktyki ruchu: {e}")
            return base_target

    def _find_defensive_position_near(self, target, unit, game_engine):
        """Znajduje defensywną pozycję w pobliżu celu"""
        try:
            board = getattr(game_engine, 'board', None)
            if not board:
                return target
            
            # Sprawdź pozycje w promieniu 2 hexów od celu
            for distance in [1, 2]:
                for direction in [(1,0), (0,1), (-1,1), (-1,0), (0,-1), (1,-1)]:
                    candidate = (
                        target[0] + direction[0] * distance,
                        target[1] + direction[1] * distance
                    )
                    
                    # Sprawdź czy pozycja jest dostępna i bezpieczna
                    if not board.is_occupied(candidate[0], candidate[1]):
                        # Dodatkowa logika oceny bezpieczeństwa
                        if self._is_position_safe(candidate, game_engine):
                            return candidate
            
            return target  # Fallback
            
        except Exception:
            return target

    def _is_position_safe(self, position, game_engine):
        """Sprawdza czy pozycja jest bezpieczna (brak wrogów w pobliżu)"""
        try:
            recon_data = self.reconnaissance_data
            if not recon_data or 'visible_enemies' not in recon_data:
                return True  # Brak danych = zakładamy bezpieczeństwo
            
            for enemy in recon_data['visible_enemies']:
                enemy_pos = enemy['position']
                distance = calculate_hex_distance(position, enemy_pos)
                if distance <= 3:  # Wróg w promieniu 3 hexów
                    return False
            
            return True
            
        except Exception:
            return True  # Default safe


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

        # --- AUTO INIT KEY POINTS (jeśli brak current_value) ---
        try:
            kp_state = getattr(game_engine, 'key_points_state', None)
            map_data = getattr(game_engine, 'map_data', {}) or {}
            map_kp = map_data.get('key_points', {})
            if kp_state is None:
                game_engine.key_points_state = {}
                kp_state = game_engine.key_points_state
            changed = False
            # Dodaj brakujące z mapy
            for pos_str, kp in map_kp.items():
                if pos_str not in kp_state:
                    val = kp.get('value', 0)
                    kp_state[pos_str] = {
                        'type': kp.get('type', 'unknown'),
                        'value': kp.get('value', val),
                        'current_value': kp.get('current_value', val)
                    }
                    changed = True
                else:
                    # Uzupełnij current_value jeśli brak
                    if 'current_value' not in kp_state[pos_str]:
                        kp_state[pos_str]['current_value'] = kp_state[pos_str].get('value', 0)
                        changed = True
            if changed:
                print(f"[AI KP INIT] Zainicjalizowano/uzupełniono key pointy: {len(kp_state)}")
        except Exception as _e:
            print(f"[AI KP INIT] Błąd inicjalizacji key pointów: {_e}")
        
        # STRATEGICZNE ROZKAZY od General
        strategic_order = None
        try:
            if current_player:
                # Zarejestruj referencję do commander aby find_target mógł pobrać wagi
                if not hasattr(game_engine, 'current_player_commander'):
                    game_engine.current_player_commander = None
                temp_commander = type('obj', (), {'player': current_player})()
                current_turn = getattr(game_engine, 'turn_number', getattr(game_engine, 'current_turn', 1))
                strategic_order = AICommander.receive_orders(temp_commander, current_turn=current_turn)
                
                if strategic_order:
                    print(f"📋 [AI] Otrzymano strategiczny rozkaz: {strategic_order['mission_type']} -> {strategic_order['target_hex']}")
                else:
                    print(f"🔄 [AI] Brak rozkazów strategicznych - tryb autonomiczny")
        except Exception as e:
            print(f"⚠️ [AI] Błąd odczytu rozkazów strategicznych: {e}")

        # ===== NOWY: ADAPTACYJNY SYSTEM AI =====
        adaptive_ai = None
        strategic_plan = None
        try:
            # Stwórz tymczasową instancję AICommander dla AdaptiveAI
            temp_ai_commander = AICommander(current_player)
            adaptive_ai = AdaptiveAICommander(temp_ai_commander)
            
            # Wykonaj pełną analizę strategiczną
            strategic_plan = adaptive_ai.adaptive_strategic_behavior(game_engine)
            
            if strategic_plan:
                print(f"🧠 [ADAPTIVE] Plan strategiczny gotowy: {strategic_plan['state']}")
                # Ustaw priorytetyzację dla reszty tury
                if hasattr(game_engine, 'current_player_commander'):
                    game_engine.current_player_commander = temp_ai_commander
                    # Przekaż dane adaptacyjne
                    temp_ai_commander.adaptive_plan = strategic_plan
                    temp_ai_commander.adaptive_ai = adaptive_ai
            
        except Exception as e:
            print(f"⚠️ [ADAPTIVE] Błąd systemu adaptacyjnego: {e}")
            strategic_plan = None
        
        # 1. Zbierz dane
        my_units = get_my_units(game_engine, player_id)
        print(f"[AI] Znaleziono {len(my_units)} jednostek dla gracza {player_id}")
        if not my_units:
            print(f"[AI] Brak jednostek dla gracza {player_id}")
            return

        # DYNAMICZNA ADAPTACJA WAG (MVP): jeśli przychód ekonomiczny niski przez kilka tur zwiększ wagę ekonomii
        try:
            commander_ref = getattr(game_engine, 'current_player_commander', None)
            if commander_ref is not None and hasattr(current_player, 'economy'):
                income = 0
                econ_obj = current_player.economy
                if hasattr(econ_obj, 'get_points'):
                    pts = econ_obj.get_points()
                    income = pts.get('last_turn_income', 0)
                else:
                    income = getattr(econ_obj, 'last_turn_income', 0)
                if income < 5:
                    commander_ref.turns_on_low_income += 1
                else:
                    commander_ref.turns_on_low_income = 0
                if commander_ref.turns_on_low_income >= 2:
                    # Podbij wagę ekonomii do max 2.0 i lekko zmniejsz vp
                    commander_ref.econ_weight = min(2.0, commander_ref.econ_weight + 0.2)
                    commander_ref.vp_weight = max(0.3, commander_ref.vp_weight - 0.05)
                    print(f"[AI WEIGHTS] Low income streak={commander_ref.turns_on_low_income}: econ_weight={commander_ref.econ_weight:.2f}, vp_weight={commander_ref.vp_weight:.2f}")
        except Exception as _e:
            print(f"[AI WEIGHTS] Błąd adaptacji wag: {_e}")
        
        # 2. Faza OPPORTUNISTIC CAPTURE (przed grupowaniem / walką)
        opportunistic_captured = opportunistic_capture_phase(game_engine, my_units, player_id)
        if opportunistic_captured:
            print(f"[OPPORTUNISTIC] Zajęto błyskawicznie {len(opportunistic_captured)} wolnych punktów")
        # Odfiltruj jednostki które już ruszyły
        my_units = [u for u in my_units if not u.get('moved_capture')]

        # 2b. GRUPOWANIE JEDNOSTEK według bliskości lub zaawansowany autonomiczny
        if strategic_order:
            # Standardowe grupowanie dla rozkazów strategicznych
            unit_groups = group_units_by_proximity(my_units, max_group_distance=8)
            print(f"[AI] Utworzono {len(unit_groups)} grup jednostek (tryb strategiczny)")
            advanced_mode = False
        else:
            # ZAAWANSOWANY TRYB AUTONOMICZNY
            print(f"🎯 [AI] ZAAWANSOWANY TRYB AUTONOMICZNY AKTYWOWANY!")
            group_assignments = advanced_autonomous_mode(my_units, game_engine)
            
            # NOWY: Dynamiczne przeprzydzielanie sił
            group_assignments = dynamic_reassignment(group_assignments, game_engine)
            
            advanced_mode = True
            print(f"[AI] Utworzono {len(group_assignments)} zorganizowanych grup")
        
        # 3. COMBAT PHASE - dla każdej jednostki sprawdź możliwe ataki
        combat_count = 0
        for i, unit in enumerate(my_units):
            unit_name = unit.get('id', f'unit_{i}')
            can_move_result = can_move(unit)

            if can_move_result:
                combat_attempted = ai_attempt_combat(unit, game_engine, player_id, player_nation)
                if combat_attempted:
                    combat_count += 1
        print(f"[AI] COMBAT PHASE: {combat_count} ataków wykonanych")

        # 3.5. NOWA FAZA DEFENSYWNA - ocena zagrożeń i planowanie obrony
        print(f"🛡️ [AI] === FAZA DEFENSYWNA ===")

        # Oceń zagrożenia defensywne
        threat_assessment = assess_defensive_threats(my_units, game_engine)

        # Znajdź jednostki wymagające odwrotu
        threatened_units = []
        for unit in my_units:
            assessment = threat_assessment.get(unit['id'], {})
            threat_level = assessment.get('threat_level', 0)
            if threat_level > 5:  # Próg zagrożenia
                threatened_units.append(unit)

        if threatened_units:
            print(f"[DEFENSE] Znaleziono {len(threatened_units)} zagrożonych jednostek")

            # Planuj kontrolowany odwrót
            retreat_plan = plan_defensive_retreat(threatened_units, threat_assessment, game_engine)

            # Wykonaj ruchy defensywne
            retreat_count = 0
            for unit in threatened_units:
                if unit['id'] in retreat_plan:
                    target_pos = retreat_plan[unit['id']]
                    current_pos = (unit['q'], unit['r'])

                    if target_pos != current_pos:  # Tylko jeśli ruch jest potrzebny
                        success = move_towards(unit, target_pos, game_engine)
                        if success:
                            retreat_count += 1
                            print(f"[DEFENSE] {unit['id']}: Udany odwrót do {target_pos}")

            print(f"[DEFENSE] Wykonano {retreat_count} ruchów defensywnych")

        # Koordynacja obrony wokół punktów kluczowych
        defensive_groups = defensive_coordination(my_units, threat_assessment, game_engine)
        debug_print(f"🛡️  Utworzono {len(defensive_groups)} grup defensywnych", "FULL", "DEFENSE")

        # 3.6. DEPLOYMENT NOWYCH JEDNOSTEK
        debug_print(f"🚀 === FAZA DEPLOYMENT ===", "BASIC", "DEPLOY")
        deployed_count = deploy_purchased_units(game_engine, player_id)

        if deployed_count > 0:
            debug_print(f"✅ Wdrożono {deployed_count} nowych jednostek", "BASIC", "DEPLOY")
            # Po deployment, odśwież listę jednostek
            my_units = get_my_units(game_engine, player_id)

        # 4. MOVEMENT PHASE - różne logiki dla różnych trybów
        moved_count = 0
        total_processed = 0

        if advanced_mode:
            # ZAAWANSOWANY RUCH - każda grupa ma przypisany cel
            for assignment_idx, assignment in enumerate(group_assignments):
                group = assignment['group']
                leader = assignment['leader']
                target = assignment['target']

                print(f"🎯 [ADVANCED MOVE] Grupa {assignment_idx + 1}: {len(group)} żetonów -> cel {target}")
                print(f"🎯 [ADVANCED MOVE] Lider: {leader['id']} (dystans: {assignment['distance']})")

                # NOWE: Użyj priorytetów z adaptacyjnego systemu jeśli dostępne
                if strategic_plan and 'target_priorities' in strategic_plan:
                    # Sprawdź czy cel grupy pasuje do top priorytetów
                    target_str = f"{target[0]},{target[1]}"
                    for priority_hex, priority_data in strategic_plan['target_priorities']:
                        if priority_hex == target_str:
                            priority_level = priority_data['priority']
                            print(f"🎯 [ADAPTIVE] Cel {target} ma priorytet {priority_level:.1f} ({priority_data['type']})")
                            break

                # Przetwórz wszystkie jednostki w grupie
                for unit_idx, unit in enumerate(group):
                    total_processed += 1
                    unit_name = unit.get('id', f'unit_{total_processed}')
                    can_move_result = can_move(unit)
                    # NOWE: jeśli jednostka utrzymuje pozycję (garnizon) pomijamy ruch
                    if is_unit_holding(unit):
                        print(f"🛡️ [ADVANCED MOVE] {unit_name}: UTRZYMUJE POZYCJĘ (garnizon)")
                        continue

                    if can_move_result:
                        # NOWE: Adaptacyjna taktyka na podstawie stanu strategicznego
                        final_target = target
                        if strategic_plan:
                            final_target = adaptive_ai._adaptive_movement_tactics(
                                unit, target, strategic_plan, game_engine
                            ) if adaptive_ai else target

                        print(f"🚨 [URGENT TEST] ZARAZ WYWOŁUJĘ MOVE_TOWARDS DLA {unit_name}!")
                        success = move_towards(unit, final_target, game_engine)
                        if success:
                            moved_count += 1
                            # Log zaawansowanego ruchu z adaptacyjnymi danymi
                            move_reason = f"Advanced auto mode: group {assignment_idx + 1}"
                            if strategic_plan:
                                move_reason += f" (strategy: {strategic_plan['state']}, aggr: {strategic_plan['aggression_level']:.1f})"
                            
                            log_commander_action(
                                unit_id=unit_name,
                                action_type="adaptive_autonomous",
                                from_pos=(unit['q'], unit['r']),
                                to_pos=final_target,
                                reason=move_reason,
                                player_nation=player_nation
                            )
                            print(f"✅ [ADVANCED MOVE] {unit_name}: Ruch do {final_target}")
                        else:
                            print(f"❌ [ADVANCED MOVE] {unit_name}: Ruch nieudany")
                    else:
                        print(f"⚠️ [ADVANCED MOVE] {unit_name}: Nie może się ruszyć (MP={unit.get('mp', 0)}, Fuel={unit.get('fuel', 0)})")

        else:
            # STANDARDOWA LOGIKA - dla rozkazów strategicznych
            for group_idx, group in enumerate(unit_groups):
                print(f"[AI] Przetwarzam grupę {group_idx + 1}/{len(unit_groups)} ({len(group)} jednostek)")

                # Oblicz średnią pozycję grupy dla lepszego target selection
                if strategic_order and strategic_order.get('target_hex'):
                    # Wszystkie grupy mają ten sam strategiczny cel
                    base_target = strategic_order['target_hex']
                    mission_type = strategic_order.get('mission_type', 'UNKNOWN')
                else:
                    # Autonomiczny cel dla grupy - wybierz na podstawie pozycji lidera (stara logika)
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
                                # AUTONOMOUS MOVEMENT (stara logika)
                                target = base_target
                                print(f"[AI] {unit_name}: Cel autonomiczny {target}")
                        else:
                            print(f"[AI] {unit_name}: Brak celu")
                            continue

                        # NOWE: pomiń ruch jeśli jednostka jest w trybie hold_position
                        if is_unit_holding(unit):
                            print(f"🛡️ [MOVE] {unit_name}: UTRZYMUJE POZYCJĘ (garnizon)")
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
        group_count = len(group_assignments) if advanced_mode else len(unit_groups)
        mode_type = "advanced" if advanced_mode else "standard"
        log_commander_action(
            unit_id="TURN_END",
            action_type="turn_summary",
            from_pos=None,
            to_pos=None,
            reason=f"Turn completed: {moved_count}/{len(my_units)} units moved, {group_count} groups ({mode_type})",
            player_nation=player_nation
        )
        
    except Exception as e:
        print(f"[AI] Błąd tury: {e}")
        # NIE CRASHUJ - po prostu zakończ turę


class AICommander:
    """Wrapper klasa dla kompatybilności z istniejącym kodem"""
    def __init__(self, player: Any):
        # Poprawne wcięcia naprawiające wcześniejszy błąd składni
        self.player = player
        # GARRISONS: hex_id -> {'tokens': set(ids), 'since_turn': int}
        self.garrisons: dict[str, dict] = {}
        # Konfiguracja wag strategicznych (docelowo dynamiczne)
        self.econ_weight: float = 1.0
        self.vp_weight: float = 0.5
        self.min_garrison_size: int = 1  # minimalny garnizon na punkt
        self.max_garrison_fraction: float = 0.3  # max 30% jednostek w garnizonach
        # Bufor: liczba jednostek trzymanych na każdym zajętym key point
        self.default_garrison_size: int = 1
        # Licznik tur do adaptacyjnej zmiany wag
        self.turns_on_low_income: int = 0
        self.low_income_threshold: int = 5  # jeśli tura daje < X pkt ekonomicznych

    def should_hold_position(self, unit_dict: dict) -> bool:
        """Zwraca True jeśli jednostka ma pozostać na zajętym key poincie.
        Używa atrybutu token.hold_position ustawianego przy wejściu na punkt.
        """
        token = unit_dict.get('token')
        if not token:
            return False
        return bool(getattr(token, 'hold_position', False))

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


# ========== STRATEGIA DEFENSYWNA ==========

def calculate_hex_distance(pos1, pos2):
    """Oblicza dystans hex między dwoma pozycjami"""
    q1, r1 = pos1
    q2, r2 = pos2
    return max(abs(q1 - q2), abs(r1 - r2), abs((q1 + r1) - (q2 + r2)))


def get_all_key_points(game_engine):
    """Pobiera wszystkie punkty kluczowe z mapy"""
    key_points = {}
    
    # Sprawdź czy mamy dane mapy
    map_data = getattr(game_engine, 'map_data', {})
    if 'key_points' in map_data:
        for pos_str, kp_data in map_data['key_points'].items():
            # Konwertuj string pozycji na tuple
            q, r = map(int, pos_str.split(','))
            key_points[(q, r)] = kp_data
    
    # Fallback - sprawdź stan punktów kluczowych w grze
    if not key_points and hasattr(game_engine, 'key_points_state'):
        kp_state = getattr(game_engine, 'key_points_state', {})
        for pos_str, state_data in kp_state.items():
            q, r = map(int, pos_str.split(','))
            key_points[(q, r)] = {
                'type': state_data.get('type', 'unknown'),
                'value': state_data.get('value', 50)
            }
    
    return key_points


def assess_defensive_threats(my_units, game_engine):
    """Ocenia zagrożenia defensywne dla każdej jednostki
    
    Returns:
        dict: {unit_id: {'threat_level': int, 'threatening_enemies': list, 'nearest_safe_point': tuple}}
    """
    threat_assessment = {}
    
    # Pobierz pozycje wrogów
    enemy_positions = []
    all_tokens = getattr(game_engine, 'tokens', [])
    if hasattr(game_engine, 'board') and hasattr(game_engine.board, 'tokens'):
        all_tokens = game_engine.board.tokens
    
    current_player_id = getattr(game_engine.current_player_obj, 'id', None)
    current_nation = getattr(game_engine.current_player_obj, 'nation', 'Unknown')
    expected_owner = f"{current_player_id} ({current_nation})"
    
    for token in all_tokens:
        token_owner = getattr(token, 'owner', 'NO_OWNER')
        if token_owner != expected_owner and token_owner != 'NO_OWNER':
            enemy_positions.append({
                'id': getattr(token, 'id', 'unknown'),
                'pos': (getattr(token, 'q', 0), getattr(token, 'r', 0)),
                'combat': getattr(token, 'combat_value', 0)
            })
    
    # Znajdź punkty kluczowe dla defensywnych pozycji
    key_points = get_all_key_points(game_engine)
    
    for unit in my_units:
        unit_pos = (unit['q'], unit['r'])
        threatening_enemies = []
        
        # Sprawdź wrogów w zasięgu 6 hexów
        for enemy in enemy_positions:
            distance = calculate_hex_distance(unit_pos, enemy['pos'])
            if distance <= 6:  # Zasięg zagrożenia
                threat_score = max(1, enemy['combat'] - distance)
                threatening_enemies.append({
                    'id': enemy['id'],
                    'pos': enemy['pos'],
                    'distance': distance,
                    'threat_score': threat_score
                })
        
        # Oblicz całkowity poziom zagrożenia
        threat_level = sum(enemy['threat_score'] for enemy in threatening_enemies)
        
        # Znajdź najbliższy bezpieczny punkt kluczowy
        nearest_safe_point = None
        min_distance = float('inf')
        for kp_pos, kp_data in key_points.items():
            kp_distance = calculate_hex_distance(unit_pos, kp_pos)
            if kp_distance < min_distance:
                min_distance = kp_distance
                nearest_safe_point = kp_pos
        
        threat_assessment[unit['id']] = {
            'threat_level': threat_level,
            'threatening_enemies': threatening_enemies,
            'nearest_safe_point': nearest_safe_point,
            'safe_point_distance': min_distance
        }
        
        if threat_level > 0:
            print(f"[DEFENSE] {unit['id']}: Threat level {threat_level}, {len(threatening_enemies)} enemies nearby")
    
    return threat_assessment


def plan_defensive_retreat(threatened_units, threat_assessment, game_engine):
    """Planuje kontrolowany odwrót zagrożonych jednostek
    
    Args:
        threatened_units: Lista jednostek wymagających odwrotu
        threat_assessment: Wynik assess_defensive_threats
        game_engine: Silnik gry
        
    Returns:
        dict: {unit_id: retreat_position}
    """
    retreat_plan = {}
    key_points = get_all_key_points(game_engine)
    
    for unit in threatened_units:
        unit_id = unit['id']
        unit_pos = (unit['q'], unit['r'])
        assessment = threat_assessment.get(unit_id, {})
        
        # Strategia odwrotu:
        # 1. Jeśli blisko punktu kluczowego - zostań i broń
        # 2. Jeśli daleko - wycofaj się do najbliższego punktu kluczowego
        # 3. Unikaj pozycji w zasięgu wrogów
        
        safe_point = assessment.get('nearest_safe_point')
        safe_distance = assessment.get('safe_point_distance', float('inf'))
        
        if safe_distance <= 2:
            # Jesteś blisko punktu kluczowego - zostań i broń
            retreat_plan[unit_id] = unit_pos
            print(f"[RETREAT] {unit_id}: Zostaje przy punkcie kluczowym {safe_point}")
        elif safe_point:
            # Znajdź bezpieczną pozycję w kierunku punktu kluczowego
            retreat_pos = find_safe_retreat_position(unit, safe_point, assessment['threatening_enemies'], game_engine)
            retreat_plan[unit_id] = retreat_pos
            print(f"[RETREAT] {unit_id}: Odwrót do {retreat_pos} (kierunek: {safe_point})")
        else:
            # Brak punktów kluczowych - odwrót w bezpiecznym kierunku
            retreat_pos = find_safe_fallback_position(unit, assessment['threatening_enemies'], game_engine)
            retreat_plan[unit_id] = retreat_pos
            print(f"[RETREAT] {unit_id}: Odwrót awaryjny do {retreat_pos}")
    
    return retreat_plan


def find_safe_retreat_position(unit, target_point, threatening_enemies, game_engine):
    """Znajduje bezpieczną pozycję odwrotu w kierunku punktu docelowego"""
    unit_pos = (unit['q'], unit['r'])
    board = getattr(game_engine, 'board', None)
    if not board:
        return unit_pos
    
    # Sprawdź pozycje w kierunku celu
    max_range = min(unit['mp'], unit['fuel'], 4)  # Maksymalny zasięg ruchu
    
    best_position = unit_pos
    best_score = -1000
    
    # Generuj kandydatów w kierunku celu
    for distance in range(1, max_range + 1):
        # Oblicz kierunek do celu
        direction_q = target_point[0] - unit_pos[0]
        direction_r = target_point[1] - unit_pos[1]
        
        # Normalizuj kierunek
        if direction_q != 0 or direction_r != 0:
            length = max(abs(direction_q), abs(direction_r), abs(direction_q + direction_r))
            step_q = direction_q // max(length, 1) if length > 0 else 0
            step_r = direction_r // max(length, 1) if length > 0 else 0
            
            candidate_pos = (
                unit_pos[0] + step_q * distance,
                unit_pos[1] + step_r * distance
            )
            
            # Sprawdź czy pozycja jest dostępna
            if not board.is_occupied(candidate_pos[0], candidate_pos[1]):
                # Oceń bezpieczeństwo pozycji
                safety_score = evaluate_position_safety(candidate_pos, threatening_enemies, target_point)
                
                if safety_score > best_score:
                    best_score = safety_score
                    best_position = candidate_pos
    
    return best_position


def find_safe_fallback_position(unit, threatening_enemies, game_engine):
    """Znajduje bezpieczną pozycję odwrotu gdy brak punktów kluczowych"""
    unit_pos = (unit['q'], unit['r'])
    board = getattr(game_engine, 'board', None)
    if not board:
        return unit_pos
    
    max_range = min(unit['mp'], unit['fuel'], 3)
    best_position = unit_pos
    best_safety = -1000
    
    # Sprawdź wszystkie dostępne pozycje w zasięgu
    for q_offset in range(-max_range, max_range + 1):
        for r_offset in range(-max_range, max_range + 1):
            if abs(q_offset) + abs(r_offset) + abs(q_offset + r_offset) <= max_range * 2:
                candidate_pos = (unit_pos[0] + q_offset, unit_pos[1] + r_offset)
                
                if not board.is_occupied(candidate_pos[0], candidate_pos[1]):
                    # Oceń bezpieczeństwo - im dalej od wrogów, tym lepiej
                    min_enemy_distance = float('inf')
                    for enemy in threatening_enemies:
                        enemy_distance = calculate_hex_distance(candidate_pos, enemy['pos'])
                        min_enemy_distance = min(min_enemy_distance, enemy_distance)
                    
                    if min_enemy_distance > best_safety:
                        best_safety = min_enemy_distance
                        best_position = candidate_pos
    
    return best_position


def evaluate_position_safety(position, threatening_enemies, target_point=None):
    """Ocenia bezpieczeństwo pozycji względem wrogów i celów"""
    safety_score = 0
    
    # Bonus za dystans od wrogów
    for enemy in threatening_enemies:
        enemy_distance = calculate_hex_distance(position, enemy['pos'])
        safety_score += enemy_distance * 10  # Im dalej od wroga, tym lepiej
    
    # Bonus za bliskość do punktu docelowego
    if target_point:
        target_distance = calculate_hex_distance(position, target_point)
        safety_score -= target_distance * 5  # Im bliżej celu, tym lepiej
    
    return safety_score


def deploy_purchased_units(game_engine, player_id):
    """Wdraża zakupione jednostki do walki
    
    Args:
        game_engine: Silnik gry
        player_id: ID gracza
        
    Returns:
        int: Liczba wdrożonych jednostek
    """
    debug_print(f"🚢 SPRAWDZAM ZAKUPIONE JEDNOSTKI dla gracza {player_id}", "BASIC", "DEPLOY")
    
    current_player = getattr(game_engine, 'current_player_obj', None)
    if not current_player:
        debug_print(f"❌ Brak obiektu gracza", "BASIC", "DEPLOY")
        return 0
    
    nation = getattr(current_player, 'nation', 'Unknown')
    
    # Sprawdź foldery z zakupionymi jednostkami (nowa implementacja)
    import glob
    from pathlib import Path
    import os
    
    # Szukaj w assets/tokens/nowe_dla_{player_id}/*/token.json
    assets_path = Path("assets/tokens")
    commander_folder = assets_path / f"nowe_dla_{player_id}"
    
    purchased_files = []
    if commander_folder.exists():
        # Znajdź wszystkie foldery z tokenami
        for token_folder in commander_folder.glob("*/"):
            token_json = token_folder / "token.json"
            if token_json.exists():
                purchased_files.append(str(token_json))
    
    deployed_count = 0
    
    debug_print(f"📁 Sprawdzam folder: {commander_folder}", "FULL", "DEPLOY")
    debug_print(f"📦 Znaleziono {len(purchased_files)} plików token.json", "BASIC", "DEPLOY")
    
    for file_path in purchased_files:
        try:
            import json
            with open(file_path, 'r', encoding='utf-8') as f:
                unit_data = json.load(f)
            
            debug_print(f"⚙️  Przetwarzam jednostkę z {file_path}", "FULL", "DEPLOY")
            
            # Każdy plik token.json zawiera dane jednej jednostki
            deployment_pos = find_deployment_position(unit_data, game_engine, player_id)
            
            if deployment_pos:
                # Znajdź folder tokena (parent folder of file_path)
                token_folder = os.path.dirname(file_path)
                
                # Stwórz token i umieść na mapie
                success = create_and_deploy_token(unit_data, deployment_pos, game_engine, player_id, token_folder)
                if success:
                    deployed_count += 1
                    debug_print(f"🎯 WYSTAWIONO {unit_data.get('label', 'jednostka')} na {deployment_pos}", "BASIC", "DEPLOY")
                    
                    # Usuń folder po deployment
                    token_folder = Path(file_path).parent
                    shutil.rmtree(token_folder)
                    debug_print(f"🗑️  Usunięto folder {token_folder}", "FULL", "DEPLOY")
                
        except Exception as e:
            debug_print(f"❌ Błąd wdrażania z {file_path}: {e}", "BASIC", "ERROR")
    
    if deployed_count > 0:
        debug_print(f"✅ WDROŻONO ŁĄCZNIE {deployed_count} nowych jednostek", "BASIC", "DEPLOY")
    
    return deployed_count


def find_deployment_position(unit_data, game_engine, player_id):
    """Znajduje najlepszą pozycję do wdrożenia nowej jednostki - INTELIGENTNY SYSTEM"""
    try:
        # Import inteligentnego systemu spawnowania
        import sys
        import os
        sys.path.append(os.path.dirname(__file__))
        from smart_deployment import find_optimal_spawn_position, LAST_DEPLOY_CHOICE
        
        print(f"[DEPLOY] Używam inteligentnego systemu spawnowania...")
        optimal_position = find_optimal_spawn_position(unit_data, game_engine, player_id)
        
        if optimal_position:
            # Jeśli global LAST_DEPLOY_CHOICE zawiera breakdown – pokaż krótki powód
            try:
                from smart_deployment import LAST_DEPLOY_CHOICE as _LDC
                if _LDC and _LDC.get('position') == optimal_position:
                    print(f"[DEPLOY] Inteligentny system wybrał pozycję: {optimal_position} | { _LDC.get('reason','') }")
            except Exception:
                print(f"[DEPLOY] Inteligentny system wybrał pozycję: {optimal_position}")
            return optimal_position
        else:
            print(f"[DEPLOY] Inteligentny system nie znalazł pozycji, używam fallback...")
            
    except Exception as e:
        print(f"[DEPLOY] Błąd w inteligentnym systemie: {e}, używam fallback...")
    
    # FALLBACK - prosty system (dla zgodności wstecznej)
    board = getattr(game_engine, 'board', None)
    if not board:
        return None
    
    current_player = getattr(game_engine, 'current_player_obj', None)
    nation = getattr(current_player, 'nation', 'Unknown')
    
    # Pobierz spawn points dla tej nacji
    map_data = getattr(game_engine, 'map_data', {})
    spawn_points = map_data.get('spawn_points', {}).get(nation, [])
    
    # Prosty wybór pierwszego dostępnego spawnu
    for spawn_str in spawn_points:
        try:
            spawn_pos = tuple(map(int, spawn_str.split(',')))
            if not board.is_occupied(spawn_pos[0], spawn_pos[1]):
                print(f"[DEPLOY] Fallback wybrał pozycję: {spawn_pos}")
                return spawn_pos
        except (ValueError, IndexError):
            continue
    
    # Sprawdź sąsiednie pozycje
    for spawn_str in spawn_points:
        try:
            spawn_pos = tuple(map(int, spawn_str.split(',')))
            neighbors = board.neighbors(spawn_pos[0], spawn_pos[1])
            
            for neighbor in neighbors:
                if not board.is_occupied(neighbor[0], neighbor[1]):
                    print(f"[DEPLOY] Fallback wybrał sąsiada spawnu: {neighbor}")
                    return neighbor
        except (ValueError, IndexError):
            continue
    
    return None


def evaluate_deployment_position(position, my_units, game_engine):
    """Ocenia jakość pozycji deployment"""
    score = 100  # Bazowy wynik
    
    # Bonus za bliskość do moich jednostek
    if my_units:
        min_distance_to_friendly = float('inf')
        for unit in my_units:
            unit_pos = (unit['q'], unit['r'])
            distance = calculate_hex_distance(position, unit_pos)
            min_distance_to_friendly = min(min_distance_to_friendly, distance)
        
        if min_distance_to_friendly <= 3:
            score += 50  # Blisko wsparcia
        elif min_distance_to_friendly <= 6:
            score += 20  # Średnio blisko
    
    # Bonus za bliskość do punktów kluczowych
    key_points = get_all_key_points(game_engine)
    for kp_pos, kp_data in key_points.items():
        distance = calculate_hex_distance(position, kp_pos)
        if distance <= 2:
            score += kp_data.get('value', 0) // 10  # Bonus proporcjonalny do wartości
    
    return score


def create_and_deploy_token(unit_data, position, game_engine, player_id, token_folder):
    """Tworzy token i umieszcza go na mapie - DOKŁADNIE JAK CZŁOWIEK"""
    try:
        from engine.token import Token
        import os
        
        # Przygotuj dane tokena DOKŁADNIE jak w panel_mapa.py
        current_player = getattr(game_engine, 'current_player_obj', None)
        nation = getattr(current_player, 'nation', 'Unknown')
        token_owner = f"{player_id} ({nation})"
        
        # Ustaw owner w danych żetonu (jak w panel_mapa.py)
        unit_data["owner"] = token_owner
        
        # Utwórz obiekt Token DOKŁADNIE jak człowiek - używając Token.from_json()
        new_token = Token.from_json(unit_data)
        new_token.set_position(position[0], position[1])
        new_token.owner = token_owner
        
        # Resetuj punkty ruchu i paliwa po wystawieniu (jak w panel_mapa.py)
        new_token.apply_movement_mode(reset_mp=True)
        new_token.currentFuel = new_token.maxFuel
        
        # KLUCZOWE: Skopiuj pliki do aktualne/ JAK ROBI CZŁOWIEK!
        png_src = os.path.join(token_folder, "token.png")
        json_src = os.path.join(token_folder, "token.json")
        if os.path.exists(png_src):
            dest_dir = os.path.join("assets", "tokens", "aktualne")
            os.makedirs(dest_dir, exist_ok=True)
            base_name = os.path.basename(token_folder)
            png_dst = os.path.join(dest_dir, base_name + ".png")
            shutil.copy2(png_src, png_dst)
            # KLUCZOWE: Ustaw ścieżkę obrazka JAK ROBI CZŁOWIEK!
            new_token.stats['image'] = png_dst.replace('\\', '/')
            debug_print(f"📁 Skopiowano PNG do: {png_dst}", "FULL", "DEPLOY")
        
        # Skopiuj również token.json do katalogu aktualne (jak robi człowiek)
        if os.path.exists(json_src):
            json_dst = os.path.join(dest_dir, base_name + ".json")
            shutil.copy2(json_src, json_dst)
            debug_print(f"📁 Skopiowano JSON do: {json_dst}", "FULL", "DEPLOY")
        
        # KLUCZOWE: Dodaj żeton do game_engine.tokens (nie board.tokens!)
        game_engine.tokens.append(new_token)
        
        # KLUCZOWE: Synchronizuj board z tokens
        game_engine.board.set_tokens(game_engine.tokens)
        
        # KLUCZOWE: Aktualizuj widoczność wszystkich graczy
        from engine.engine import update_all_players_visibility
        update_all_players_visibility(game_engine.players, game_engine.tokens, game_engine.board)
        
        # SAVE STATE - zapisz żeby żeton nie zniknął po restarcie
        try:
            os.makedirs("saves", exist_ok=True)
            game_engine.save_state(os.path.join("saves", "after_deployment.json"))
            debug_print(f"💾 Zapisano stan gry z nowym żetonem", "FULL", "SAVE")
        except Exception as save_err:
            debug_print(f"⚠️ Błąd zapisu stanu: {save_err}", "BASIC", "ERROR")
        
        debug_print(f"✅ Token {new_token.id} wdrożony na ({position[0]}, {position[1]}) jak człowiek", "BASIC", "DEPLOY")
        return True
        
    except Exception as e:
        print(f"[DEPLOY] Błąd tworzenia tokena: {e}")
        import traceback
        traceback.print_exc()
        return False


def defensive_coordination(my_units, threat_assessment, game_engine):
    """Koordynuje obronę - grupuje jednostki wokół punktów kluczowych"""
    key_points = get_all_key_points(game_engine)
    defensive_groups = {}
    
    # Grupuj jednostki według najbliższych punktów kluczowych
    for unit in my_units:
        unit_pos = (unit['q'], unit['r'])
        closest_kp = None
        min_distance = float('inf')
        
        for kp_pos in key_points.keys():
            distance = calculate_hex_distance(unit_pos, kp_pos)
            if distance < min_distance:
                min_distance = distance
                closest_kp = kp_pos
        
        if closest_kp:
            if closest_kp not in defensive_groups:
                defensive_groups[closest_kp] = []
            defensive_groups[closest_kp].append(unit)
    
    # Planuj koordynowaną obronę dla każdej grupy
    for kp_pos, group in defensive_groups.items():
        if len(group) >= 2:  # Minimum 2 jednostki dla koordynacji
            plan_group_defense(kp_pos, group, game_engine)
    
    return defensive_groups


def plan_group_defense(key_point, defending_units, game_engine):
    """Planuje obronę grupy jednostek wokół punktu kluczowego"""
    print(f"[GROUP_DEFENSE] Planowanie obrony punktu {key_point} przez {len(defending_units)} jednostek")
    
    # Strategia:
    # 1. Najsilniejsze jednostki bezpośrednio przy punkcie
    # 2. Wsparcie w kręgu zewnętrznym
    # 3. Koordynacja ognia i ruchu
    
    # Sortuj według siły bojowej
    defending_units.sort(key=lambda u: u.get('combat_value', 0), reverse=True)
    
    board = getattr(game_engine, 'board', None)
    if not board:
        return
    
    # Przydziel pozycje obronne
    assigned_positions = {}
    
    # Pierwsza jednostka - bezpośrednio przy punkcie kluczowym
    if not board.is_occupied(key_point[0], key_point[1]) and defending_units:
        strongest_unit = defending_units[0]
        assigned_positions[strongest_unit['id']] = key_point
        print(f"[GROUP_DEFENSE] {strongest_unit['id']} przydzielony do obrony {key_point}")
    
    # Pozostałe jednostki - w kręgu wokół punktu
    if len(defending_units) > 1:
        neighbors = board.neighbors(key_point[0], key_point[1])
        neighbor_idx = 0
        
        for i, unit in enumerate(defending_units[1:], 1):
            if neighbor_idx < len(neighbors):
                neighbor_pos = neighbors[neighbor_idx]
                if not board.is_occupied(neighbor_pos[0], neighbor_pos[1]):
                    assigned_positions[unit['id']] = neighbor_pos
                    print(f"[GROUP_DEFENSE] {unit['id']} przydzielony do wsparcia na {neighbor_pos}")
                neighbor_idx += 1
    
    return assigned_positions


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


def enforce_garrison_limits(game_engine, hex_id, kp_data, token, current_ratio):
    """Enforce garrison limits with early rotation based on key point depletion"""
    try:
        # Parametry rotacji
        EARLY_ROTATION_THRESHOLD = 0.7  # Rotuj gdy punkt ma <70% wartości
        MAX_GARRISON_TIME = 3  # Max 3 tury na jednym punkcie
        
        garrison_tracker = getattr(game_engine, 'garrison_tracker', {})
        if not hasattr(game_engine, 'garrison_tracker'):
            game_engine.garrison_tracker = {}
            garrison_tracker = game_engine.garrison_tracker
        
        current_turn = getattr(game_engine, 'turn_number', getattr(game_engine, 'current_turn', 1))
        
        # Sprawdź jak długo jednostka jest na tym punkcie
        token_id = getattr(token, 'id', 'unknown')
        if hex_id not in garrison_tracker:
            garrison_tracker[hex_id] = {}
        
        if token_id not in garrison_tracker[hex_id]:
            garrison_tracker[hex_id][token_id] = current_turn
        
        turns_stationed = current_turn - garrison_tracker[hex_id][token_id]
        
        # Logika rotacji
        should_rotate = False
        reason = ""
        
        if current_ratio < EARLY_ROTATION_THRESHOLD:
            should_rotate = True
            reason = f"punkt wyczerpany ({current_ratio:.1%})"
        elif turns_stationed >= MAX_GARRISON_TIME:
            should_rotate = True
            reason = f"długi garnizon ({turns_stationed} tur)"
        
        if should_rotate:
            setattr(token, 'hold_position', False)
            # Usuń z trackera
            if token_id in garrison_tracker[hex_id]:
                del garrison_tracker[hex_id][token_id]
            print(f"[ROTATION] {token_id} zwolniony z {hex_id}: {reason}")
        else:
            print(f"[GARRISON] {token_id} pozostaje na {hex_id} (tura {turns_stationed+1}, wartość {current_ratio:.1%})")
    
    except Exception as e:
        print(f"[GARRISON] Błąd rotacji: {e}")


# Eksport kluczowych funkcji dla użycia zewnętrznego
__all__ = [
    'AICommander', 'AdaptiveAICommander', 'make_tactical_turn', 'check_ai_reaction_attacks', 
    'ai_attempt_combat', 'evaluate_combat_ratio', 'execute_ai_combat',
    'test_basic_safety', 'log_commander_action', 'enforce_garrison_limits'
]

