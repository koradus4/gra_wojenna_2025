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
import json
import math
import os
import shutil
from pathlib import Path

# --- Nowe moduły refaktoryzacji (etap 2 - szkielety) ---
try:
    from .wybor_celow import find_target, find_alternative_target, find_alternative_target_around, get_keypoint_value  # type: ignore
    from .grupowanie_ai import adaptive_grouping, assign_targets_with_coordination, dynamic_reassignment, group_units_by_proximity  # type: ignore
except Exception:
    # W razie problemu (np. podczas pierwszego ładowania) korzystamy z lokalnych definicji poniżej
    pass

# --- KONFIGURACJA (centralizacja) ---
from ai.konfiguracja_ai import (
    EARLY_ROTATION_THRESHOLD_RATIO,
    FREE_KEYPOINT_VALUE_DISTANCE_FACTOR,
    FREE_HIGH_VALUE_BONUS_MULTIPLIER,
    FREE_MED_VALUE_BONUS_MULTIPLIER,
    HEX_MISSING_LOG_PREFIX,
)
from ai.log_kategorie_ai import (
    TACTIC, DEPLOY, ERROR, FUEL, PROGRESSIVE, PRIORIZER, WARN, INFO,
    DEFENSE, RESUPPLY, MOVE, ADAPTIVE, ASSIGN, SAVE
)

# --- Refaktoryzacja etap 3: zewnętrzne moduły ruchu i okupacji ---
try:
    from ai.ruch_jednostek import move_towards, choose_movement_mode  # type: ignore
    from ai.okupacja_punktow import enforce_garrison_limits, GARRISON_LIMITS  # type: ignore
    from ai.wsparcie_garnizonu import assign_garrison_support, clear_obsolete_garrison_support  # type: ignore
except Exception:
    # Fallback - jeśli import się nie powiedzie pozostają lokalne (część funkcji zachowana niżej)
    pass

# --- Moduł obrony (delegacja) ---
try:
    from ai.obrona_ai import (
        calculate_hex_distance,
        assess_defensive_threats,
        plan_defensive_retreat,
        defensive_coordination,
    )
except Exception:
    pass

# --- STAŁE RESUPPLY w ai.zaopatrzenie_ai ---
try:
    from ai.zaopatrzenie_ai import (
        RESUPPLY_SECOND_MOVE_MIN_FUEL_GAIN,
        RESUPPLY_TARGET_FUEL_THRESHOLD,
        RESUPPLY_PER_UNIT_CAP_MID_TURN,
    )
except Exception:
    # fallback wartości (nie powinny być użyte jeśli import działa)
    RESUPPLY_SECOND_MOVE_MIN_FUEL_GAIN = 2
    RESUPPLY_TARGET_FUEL_THRESHOLD = 0.65
    RESUPPLY_PER_UNIT_CAP_MID_TURN = 3  # Zaktualizowane z 1 do 3


### enforce_garrison_limits delegowany w całości do ai.okupacja_punktow

# (delegacja) opportunistic_capture_phase przeniesiona do ai.rajdy_ai
def opportunistic_capture_phase(game_engine, my_units, player_id):
    from ai.rajdy_ai import opportunistic_capture_phase as _raid
    return _raid(game_engine, my_units, player_id)

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
    # KONFIG: najpierw rozważ lokalne cele, dopiero potem dalsze
    LOCAL_RADIUS = 12  # hexy
    DIST_EXPONENT = 1.5  # mocniejsza kara za dystans

    # Import czystych funkcji scoringu (fallback jeśli brak)
    try:
        from ai.priorytety_ai import compute_keypoint_priority, apply_free_point_bonus, apply_defended_penalty
    except Exception:
        def compute_keypoint_priority(value, enemy_distance, dist_exponent):
            if value <= 0:
                return 0
            return (value * 10) / (max(enemy_distance, 1) ** dist_exponent)
        def apply_free_point_bonus(base_score, value, high_mult, med_mult):
            if value >= 120:
                return base_score * FREE_HIGH_VALUE_BONUS_MULTIPLIER
            if value >= 70:
                return base_score * FREE_MED_VALUE_BONUS_MULTIPLIER
            return base_score
        def apply_defended_penalty(score, occupied_by_me, enemy_distance):
            if occupied_by_me:
                score *= 0.65
            return score

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
                debug_print(f"{HEX_MISSING_LOG_PREFIX} priorytetyzacja {hex_id}", "FULL", "WARN")
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

        # Czyste obliczenie wyniku + bonusy / kary
        priority_score = compute_keypoint_priority(value, enemy_distance, DIST_EXPONENT)
        if not occupied_any:
            priority_score = apply_free_point_bonus(priority_score, value, FREE_HIGH_VALUE_BONUS_MULTIPLIER, FREE_MED_VALUE_BONUS_MULTIPLIER)
        priority_score = apply_defended_penalty(priority_score, occupied_by_me, enemy_distance)

        priorities.append({
            'target': target_pos,
            'hex_id': hex_id,
            'value': value,
            'enemy_distance': enemy_distance,
            'priority': priority_score,
            'free': not occupied_any
        })

    # Podział na lokalne i dalekie
    local = []
    distant = []
    # Heurystyka: przyjmij środek ciężkości własnych jednostek (jeśli dostępne) aby określić lokalność
    try:
        my_tokens = [t for t in all_tokens if my_nation and my_nation in getattr(t, 'owner', '')]
        if my_tokens:
            avg_q = sum(getattr(t, 'q', 0) for t in my_tokens) / len(my_tokens)
            avg_r = sum(getattr(t, 'r', 0) for t in my_tokens) / len(my_tokens)
            center = (avg_q, avg_r)
        else:
            center = (0, 0)
    except Exception:
        center = (0, 0)

    if board:
        for p in priorities:
            dist_center = board.hex_distance(center, tuple(p['target']))
            if dist_center <= LOCAL_RADIUS:
                local.append((p, dist_center))
            else:
                distant.append((p, dist_center))
        # Bonus dla lokalnych: lekki mnożnik odwrotnie proporcjonalny do dystansu od środka
        boosted = []
        for p, dc in local:
            boost = 1 + (max(0, (LOCAL_RADIUS - dc)) / (LOCAL_RADIUS * 3))  # max +33%
            p['priority'] *= boost
            boosted.append(p)
        local = boosted
        priorities = sorted(local, key=lambda x: x['priority'], reverse=True) + \
                     sorted([p for p, _ in distant], key=lambda x: x['priority'], reverse=True)
    else:
        priorities = sorted(priorities, key=lambda x: x['priority'], reverse=True)

    # --- TEMP LOG (diagnostyka) ---
    try:
        if priorities:
            debug_print("[PRIORIZER] TOP 8 celów (hex value dist score free)")
            for entry in priorities[:8]:
                tgt = entry['target']
                debug_print(f"[P] {tgt} v={entry['value']} d={entry['enemy_distance']} s={round(entry['priority'],2)} free={entry['free']}")
    except Exception as _e:
            debug_print(f"[PRIORIZER_LOG_ERR] {_e}", "BASIC", "ERROR")
    # ------------------------------

    return priorities


# (delegacja) grouping -> ai.grupowanie_ai


from .logowanie_ai import LOG_COLUMNS, log_commander_action, log_commander_turn  # rozszerzone logowanie


def is_unit_holding(unit_dict: dict) -> bool:
    """Pomocniczo sprawdza czy jednostka ma atrybut token.hold_position == True"""
    try:
        token = unit_dict.get('token')
        if not token:
            return False
        return bool(getattr(token, 'hold_position', False))
    except Exception:
        return False


def _check_and_manage_garrisons(game_engine, my_units):
    """Sprawdza garnizone na początku tury i zarządza rotacją jednostek.
    
    Args:
        game_engine: GameEngine
        my_units: Lista jednostek gracza
    """
    try:
        kp_state = getattr(game_engine, 'key_points_state', {})
        if not kp_state:
            return
            
        debug_print(f"🏰 [GARRISON CHECK] Sprawdzanie {len(my_units)} jednostek pod kątem garnizonów", "FULL", TACTIC)
        
        # Sprawdź każdą jednostkę czy stoi na punkcie kluczowym
        for unit in my_units:
            unit_pos = (unit['q'], unit['r'])
            hex_id = f"{unit_pos[0]},{unit_pos[1]}"
            kp_data = kp_state.get(hex_id)
            
            if kp_data:
                # Jednostka stoi na punkcie kluczowym
                token = unit.get('token')
                current_value = kp_data.get('current_value', 0)
                initial_value = kp_data.get('initial_value', 1)
                current_ratio = current_value / max(initial_value, 1)
                
                debug_print(f"🏰 [GARRISON] {unit.get('id', 'UNKNOWN')} na punkcie {hex_id}: wartość {current_value}/{initial_value} ({current_ratio:.1%})", "FULL", TACTIC)
                
                if token and current_value > 0:
                    # Punkt nadal ma wartość - sprawdź czy jednostka powinna zostać
                    if not getattr(token, 'hold_position', False):
                        # Jednostka nie ma garnizonu - ustaw go
                        setattr(token, 'hold_position', True)
                        debug_print(f"🏰 [GARRISON SET] {unit.get('id', 'UNKNOWN')}: Automatycznie ustawiono garnizon na {hex_id}", "BASIC", TACTIC)
                    
                    # Sprawdź czy garnizon powinien zostać zwolniony (delegacja do okupacja_punktow)
                    enforce_garrison_limits(game_engine, hex_id, kp_data, token, current_ratio)
                    
                elif token and current_value <= 0:
                    # Punkt wyczerpany - zwolnij garnizon
                    if getattr(token, 'hold_position', False):
                        setattr(token, 'hold_position', False)
                        debug_print(f"🏰 [GARRISON RELEASE] {unit.get('id', 'UNKNOWN')}: Punkt {hex_id} wyczerpany - zwalniam garnizon", "BASIC", TACTIC)
                        
    except Exception as e:
        debug_print(f"🏰 [GARRISON ERROR] Błąd sprawdzania garnizonów: {e}", "BASIC", ERROR)


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
    """Delegat do ai.walka_ai.ai_attempt_combat"""
    from ai.walka_ai import ai_attempt_combat as _aac
    return _aac(unit, game_engine, player_id, player_nation)


def find_enemies_in_range(unit, game_engine, player_id):
    from ai.walka_ai import find_enemies_in_range as _fe
    return _fe(unit, game_engine, player_id)


def evaluate_combat_ratio(unit, enemy):
    from ai.walka_ai import evaluate_combat_ratio as _ecr
    return _ecr(unit, enemy)

def _attempt_retreat_low_cv(unit, game_engine):
    from ai.walka_ai import attempt_retreat_low_cv as _ret
    return _ret(unit, game_engine)

def _try_flank_before_attack(unit, enemy, game_engine):
    from ai.walka_ai import try_flank_before_attack as _fl
    return _fl(unit, enemy, game_engine)


def execute_ai_combat(unit, enemy, game_engine, player_nation="Unknown"):
    from ai.walka_ai import execute_ai_combat as _exec
    return _exec(unit, enemy, game_engine, player_nation)


def check_ai_reaction_attacks(moved_token, game_engine, ai_player_nation="Unknown"):
    from ai.reakcje_ai import check_ai_reaction_attacks as _react
    return _react(moved_token, game_engine, ai_player_nation)


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
    """Sprawdź czy jednostka może się ruszyć - POPRAWIONE"""
    mp = unit.get('mp', 0)
    fuel = unit.get('fuel', 0)
    
    # POPRAWKA: Jeśli brak fuel, nie odrzucaj jednostki - zwróć False ale pozwól na uzupełnienie
    can_move_result = mp > 0 and fuel > 0
    
    if not can_move_result and fuel <= 0:
            debug_print(f"🔧 [FUEL CHECK] {unit.get('id', 'UNKNOWN')} - MP:{mp}, Fuel:{fuel} - BRAK PALIWA!", "FULL", "FUEL")
    
    return can_move_result


# (refaktoryzacja) find_target przeniesiona do ai/wybor_celow.py


# (refaktoryzacja) find_alternative_target_around przeniesiona do ai/wybor_celow.py


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
            debug_print(f"[TACTIC] INTEL: Jednostka {unit.get('id')} -> rozproszenie {final_target}", "FULL", TACTIC)
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
                debug_print(f"[TACTIC] DEFEND: Jednostka {unit.get('id')} -> pozycja obronna {final_target}", "FULL", TACTIC)
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
                    debug_print(f"[TACTIC] ATTACK: Fast spearhead {unit.get('id')} -> {final_target}", "FULL", TACTIC)
                    return final_target
                else:
                    # Fast flankers
                    flank_offsets = [(-2, 1), (2, 1), (-1, 2), (1, 2)]
                    offset_idx = (unit_index - 2) % len(flank_offsets)
                    offset = flank_offsets[offset_idx]
                    flank_target = (base_q + offset[0], base_r + offset[1])
                    
                    final_target = find_alternative_target_around(unit, flank_target, game_engine)
                    debug_print(f"[TACTIC] ATTACK: Fast flanker {unit.get('id')} -> {final_target}", "FULL", TACTIC)
                    return final_target
            else:
                # Slow units - wsparcie z tyłu
                support_offsets = [(-3, 0), (-2, -1), (-3, 1), (-2, 1)]
                offset_idx = unit_index % len(support_offsets)
                offset = support_offsets[offset_idx]
                support_target = (base_q + offset[0], base_r + offset[1])
                
                final_target = find_alternative_target_around(unit, support_target, game_engine)
                debug_print(f"[TACTIC] ATTACK: Slow support {unit.get('id')} -> {final_target}", "FULL", TACTIC)
                return final_target
                    
        elif mission_type == "SECURE_KEYPOINT":
            # ZABEZPIECZENIE: Ulepszona formacja pierścieniowa
            if total_units == 1:
                # Pojedyncza jednostka - bezpośrednio do celu
                final_target = find_alternative_target_around(unit, base_target, game_engine)
                debug_print(f"[TACTIC] SECURE: Solo unit {unit.get('id')} -> {final_target}", "FULL", TACTIC)
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
                debug_print(f"[TACTIC] SECURE: Formation unit {unit.get('id')} -> {final_target}", "FULL", TACTIC)
                return final_target
            
            # Overflow - znajdź dowolne miejsce wokół celu
            final_target = find_alternative_target_around(unit, base_target, game_engine, search_radius=4)
            debug_print(f"[TACTIC] SECURE: Overflow unit {unit.get('id')} -> {final_target}", "FULL", TACTIC)
            return final_target
        else:
            # UNKNOWN mission type - fallback z alternatywą
            final_target = find_alternative_target_around(unit, base_target, game_engine)
            debug_print(f"[TACTIC] UNKNOWN: {mission_type} -> {final_target}", "FULL", TACTIC)
            return final_target
            
    except Exception as e:
            debug_print(f"[TACTIC] ERROR: {e} -> fallback {base_target}", "BASIC", "ERROR")
            return base_target


def calculate_progressive_target(unit, final_target, game_engine):
    from ai.ruch_postepowy_ai import calculate_progressive_target as _prog
    return _prog(unit, final_target, game_engine)


def advanced_autonomous_mode(my_units, game_engine):
    """
    ZAAWANSOWANY TRYB AUTONOMICZNY z TARGET RESERVATION:
    - Adaptacyjne grupowanie
    - Priorytetyzacja celów 
    - Koordynacja bez duplikatów
    - Inteligentna alokacja sił
    """
    debug_print(f"🎯 [ADVANCED AUTO] Rozpoczynam z {len(my_units)} żetonami", "FULL", TACTIC)
    
    # Filtruj tylko dostępne key pointy (current_value > 0)
    key_points = getattr(game_engine, 'key_points_state', {})
    available_keypoints = {}
    
    for hex_id, kp_data in key_points.items():
        if kp_data.get('current_value', 0) > 0:
            available_keypoints[hex_id] = kp_data
    
    debug_print(f"🎯 [ADVANCED AUTO] Dostępne key pointy: {len(available_keypoints)}", "FULL", TACTIC)
    if not available_keypoints:
        debug_print("❌ [ADVANCED AUTO] Brak dostępnych key pointów!", "BASIC", WARN)
        return []
    
    # NOWY: Priorytetyzacja celów
    prioritized_targets = prioritize_targets(available_keypoints, game_engine)
    debug_print(f"🎯 [TARGETS] Priorytetyzowano {len(prioritized_targets)} celów", "FULL", PRIORIZER)
    
    # SZCZEGÓŁOWE LOGOWANIE CELÓW
    debug_print("📊 [TARGET ANALYSIS] === ANALIZA CELÓW ===", "BASIC", PRIORIZER)
    for i, target in enumerate(prioritized_targets[:8]):  # Top 8 celów
        debug_print(f"🎯 [{i+1}] {target['target']} - wartość:{target['value']}, dystans:{target['enemy_distance']}, score:{target['priority']:.1f}, wolny:{target['free']}", "BASIC", PRIORIZER)
    
    # NOWY: Adaptacyjne grupowanie
    groups = adaptive_grouping(my_units, game_engine)
    debug_print(f"🎯 [GROUPING] Utworzono {len(groups)} adaptacyjnych grup", "FULL", ASSIGN)
    
    # SZCZEGÓŁOWE LOGOWANIE GRUP
    debug_print("👥 [GROUP ANALYSIS] === ANALIZA GRUP ===", "BASIC", ASSIGN)
    for i, group in enumerate(groups):
        leader = group[0] if group else None
        if leader:
            debug_print(f"👥 [G{i+1}] Lider: {leader.get('id', 'UNKNOWN')} na ({leader.get('q', '?')},{leader.get('r', '?')}), jednostek: {len(group)}", "BASIC", ASSIGN)
    
    # NOWY: Koordynacja celów - bez duplikatów
    group_assignments = assign_targets_with_coordination(groups, prioritized_targets, game_engine)
    # NOWE: natychmiastowa próba reasignacji pustych celów
    try:
        if any(a.get('target') is None for a in group_assignments if isinstance(a, dict)):
            group_assignments = dynamic_reassignment(group_assignments, game_engine)
    except Exception as _dre:
        debug_print(f"[ADVANCED AUTO] Reassignment fail: {_dre}", "FULL", WARN)
    
    debug_print(f"🎯 [FINAL] Przypisano cele dla {len(group_assignments)} grup", "BASIC", ASSIGN)
    
    # SZCZEGÓŁOWE LOGOWANIE PRZYPISAŃ
    debug_print("🎯 [ASSIGNMENT ANALYSIS] === PRZYPISANIA GRUP ===", "BASIC", ASSIGN)
    for i, assignment in enumerate(group_assignments):
        if isinstance(assignment, dict):
            target = assignment.get('target')
            group = assignment.get('group', [])
            leader = group[0] if group else None
            leader_id = leader.get('id', 'UNKNOWN') if leader else 'NO_LEADER'
            if target:
                debug_print(f"🎯 [A{i+1}] Grupa {leader_id} -> CEL {target} ({len(group)} jednostek)", "BASIC", ASSIGN)
            else:
                debug_print(f"⚠️ [A{i+1}] Grupa {leader_id} -> BRAK CELU! ({len(group)} jednostek)", "BASIC", ASSIGN)
    
    return group_assignments


# (delegacja) target selection helpers -> ai.wybor_celow


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
    """Delegat do ai.ruch_jednostek.choose_movement_mode (usunięto duplikat)."""
    from ai.ruch_jednostek import choose_movement_mode as _cmm  # lazy import
    return _cmm(unit, target, game_engine)


def move_towards(unit, target, game_engine):
    """(Refaktoryzacja) Właściwa implementacja przeniesiona do ai.ruch_jednostek.move_towards"""
    from ai.ruch_jednostek import move_towards as _mv  # lazy import
    return _mv(unit, target, game_engine)


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
        debug_print(f"🧠 [ADAPTIVE AI] Zainicjalizowano dla {getattr(self.player,'nation','?')}", "FULL", ADAPTIVE)

    def analyze_strategic_state(self, game_engine):
            from ai.strategia_ai import analyze_strategic_state as _an_strat
            return _an_strat(self, game_engine)

    def _adapt_strategy_to_state(self):
            from ai.strategia_ai import _adapt_strategy_to_state as _ad_str
            return _ad_str(self)

    def optimize_budget(self, game_engine):
            from ai.ekonomia_ai import optimize_budget as _opt_budget
            return _opt_budget(self, game_engine)

    def prioritize_keypoints(self, game_engine):
            from ai.strategia_ai import prioritize_keypoints as _pk
            return _pk(self, game_engine)

    def gather_reconnaissance(self, game_engine):
            from ai.rozpoznanie_ai import gather_reconnaissance as _gr
            return _gr(self, game_engine)

    # Recon cluster & threat analysis -> ai.rozpoznanie_ai

    def adaptive_purchase_ai(self, game_engine, budget_plan):
            from ai.ekonomia_ai import adaptive_purchase_ai as _apa
            return _apa(self, game_engine, budget_plan)

    def _determine_purchase_priority(self):
            from ai.strategia_ai import _determine_purchase_priority as _dpp
            return _dpp(self)

    def _get_available_purchase_options(self, game_engine):
            from ai.strategia_ai import _get_available_purchase_options as _gapo
            return _gapo(self, game_engine)

    def _select_optimal_purchases(self, available_units, budget, priorities, current_army_size):
            from ai.strategia_ai import _select_optimal_purchases as _sop
            return _sop(self, available_units, budget, priorities, current_army_size)

    def adaptive_strategic_behavior(self, game_engine):
        """GŁÓWNA FUNKCJA - Koordynuje wszystkie adaptacyjne systemy"""
        try:
            debug_print(f"🧠 [ADAPTIVE AI] === ANALIZA STRATEGICZNA ===", "BASIC", ADAPTIVE)
            
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
            
            debug_print(f"📋 [ADAPTIVE AI] Strategia gotowa: {strategic_state}, agresja {self.aggression_level:.1f}", "BASIC", ADAPTIVE)
            
            # 7. Wykonaj automatyczne akcje jeśli włączone
            if getattr(self.commander, 'auto_execute', True):
                self._execute_strategic_plan(strategic_plan, game_engine)
            
            return strategic_plan
            
        except Exception as e:
            debug_print(f"❌ [ADAPTIVE AI] Błąd systemu adaptacyjnego: {e}", "BASIC", ERROR)
            return None

    def _generate_action_recommendations(self):
            from ai.rekomendacje_ai import _generate_action_recommendations as _gar
            return _gar(self)

    def _execute_strategic_plan(self, strategic_plan, game_engine):
            from ai.rekomendacje_ai import _execute_strategic_plan as _esp
            return _esp(self, strategic_plan, game_engine)

    def _adaptive_movement_tactics(self, unit, base_target, strategic_plan, game_engine):
            from ai.ruch_adaptacyjny_ai import _adaptive_movement_tactics as _amt
            return _amt(self, unit, base_target, strategic_plan, game_engine)

    def _find_defensive_position_near(self, target, unit, game_engine):
            from ai.ruch_adaptacyjny_ai import _find_defensive_position_near as _fdpn
            return _fdpn(self, target, unit, game_engine)

    def _is_position_safe(self, position, game_engine):
            from ai.ruch_adaptacyjny_ai import _is_position_safe as _ips
            return _ips(self, position, game_engine)


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

        debug_print(f"[AICommander] Tura dla gracza (id={player_id})", "BASIC", INFO)

        # Pobierz nazwę narodu dla logów
        player_nation = "Unknown"
        current_player = getattr(game_engine, 'current_player_obj', None)
        if current_player:
            player_nation = getattr(current_player, 'nation', 'Unknown')

        # ===== WAŻNE: USTAW COMMANDER REF NA POCZĄTKU =====
        temp_ai_commander = AICommander(current_player) if current_player else None
        if temp_ai_commander:
            game_engine.current_player_commander = temp_ai_commander
            debug_print(f"🔧 [COMMANDER INIT] Ustawiono current_player_commander dla {player_nation}", "FULL", INFO)

        # LOGUJ POCZĄTEK TURY
        log_commander_action(
            unit_id="TURN_START",
            action_type="turn_begin",
            from_pos=None,
            to_pos=None,
            reason=f"AI Commander turn started for player {player_id}",
            player_nation=player_nation
        )

        # ===== REFRESH MOVEMENT POINTS NA POCZĄTKU TURY =====
        try:
            if hasattr(game_engine, 'tokens'):
                refreshed_count = 0
                for token in game_engine.tokens:
                    if getattr(token, 'player_id', None) == player_id:
                        max_mp = getattr(token, 'maxMovePoints', getattr(token, 'stats', {}).get('move', 5))
                        token.currentMovePoints = max_mp
                        refreshed_count += 1
                debug_print(f"🔄 [MP REFRESH] Odświeżono MP dla {refreshed_count} jednostek gracza {player_id}", "FULL", INFO)
        except Exception as e:
            debug_print(f"[MP REFRESH ERROR] {e}", "BASIC", ERROR)

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
                debug_print(f"[AI KP INIT] Zainicjalizowano/uzupełniono key pointy: {len(kp_state)}", "FULL", INFO)
        except Exception as _e:
            debug_print(f"[AI KP INIT] Błąd inicjalizacji key pointów: {_e}", "BASIC", ERROR)
        
        # === USUNIĘTO SYSTEM ROZKAZÓW ===
        # AI Dowódcy działają autonomicznie bez rozkazów od AI Generała
        debug_print(f"🔄 [AI] Tryb w pełni autonomiczny - brak systemu rozkazów", "FULL", TACTIC)
        debug_print(f"� [AI] Tryb w pełni autonomiczny - brak systemu rozkazów", "FULL", TACTIC)

        # ===== NOWY: ADAPTACYJNY SYSTEM AI =====
        adaptive_ai = None
        strategic_plan = None
        try:
            # Użyj już istniejącego temp_ai_commander
            if temp_ai_commander:
                adaptive_ai = AdaptiveAICommander(temp_ai_commander)
                
                # Wykonaj pełną analizę strategiczną
                strategic_plan = adaptive_ai.adaptive_strategic_behavior(game_engine)
                
                if strategic_plan:
                    debug_print(f"🧠 [ADAPTIVE] Plan strategiczny gotowy: {strategic_plan['state']}", "BASIC", ADAPTIVE)
                    # Ustaw priorytetyzację dla reszty tury
                    if hasattr(game_engine, 'current_player_commander'):
                        # Przekaż dane adaptacyjne
                        temp_ai_commander.adaptive_plan = strategic_plan
                        temp_ai_commander.adaptive_ai = adaptive_ai
            
        except Exception as e:
            debug_print(f"⚠️ [ADAPTIVE] Błąd systemu adaptacyjnego: {e}", "BASIC", ERROR)
            strategic_plan = None
        
        # 1. Zbierz dane
        my_units = get_my_units(game_engine, player_id)
        starting_unit_ids = {u.get('id') for u in my_units}
        
        # 🔥 NOWE: Sprawdź i zarządzaj garnizonami na początku tury
        _check_and_manage_garrisons(game_engine, my_units)
        
        # 🔥 NOWE: Wyczyść przestarzałe wsparcie garnizonów
        cleared_support = clear_obsolete_garrison_support(my_units, game_engine)
        
        # 🔥 NOWE: Przydziel wsparcie do garnizonów
        assigned_support = assign_garrison_support(my_units, game_engine)
        
        # Sanity: usuń martwe / nieistniejące assigned_target (np. po zmianie key pointów)
        for u in my_units:
            at = u.get('assigned_target')
            if at:
                kps = getattr(game_engine, 'key_points_state', {})
                at_key = f"{at[0]},{at[1]}"
                if at_key not in kps:
                    u.pop('assigned_target', None)
        debug_print(f"[AI] Znaleziono {len(my_units)} jednostek dla gracza {player_id}", "BASIC", INFO)
        if not my_units:
            debug_print(f"[AI] Brak jednostek dla gracza {player_id}", "BASIC", WARN)
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
                debug_print(f"[AI WEIGHTS] Low income streak={commander_ref.turns_on_low_income}: econ_weight={commander_ref.econ_weight:.2f}, vp_weight={commander_ref.vp_weight:.2f}", "FULL", ADAPTIVE)
        except Exception as _e:
            debug_print(f"[AI WEIGHTS] Błąd adaptacji wag: {_e}", "BASIC", ERROR)
        
        # 2. Faza OPPORTUNISTIC CAPTURE (przed grupowaniem / walką)
        opportunistic_captured = opportunistic_capture_phase(game_engine, my_units, player_id)
        if opportunistic_captured:
            debug_print(f"[OPPORTUNISTIC] Zajęto błyskawicznie {len(opportunistic_captured)} wolnych punktów", "FULL", TACTIC)
        # Odfiltruj jednostki które już ruszyły
        my_units = [u for u in my_units if not u.get('moved_capture')]

        # 2b. GRUPOWANIE JEDNOSTEK - TYLKO ZAAWANSOWANY TRYB AUTONOMICZNY
        # USUNIĘTO: system rozkazów strategicznych
        debug_print(f"🎯 [AI] ZAAWANSOWANY TRYB AUTONOMICZNY AKTYWOWANY!", "BASIC", TACTIC)
        group_assignments = advanced_autonomous_mode(my_units, game_engine)
        
        # NOWY: Dynamiczne przeprzydzielanie sił
        group_assignments = dynamic_reassignment(group_assignments, game_engine)
        
        advanced_mode = True
        debug_print(f"[AI] Utworzono {len(group_assignments)} zorganizowanych grup", "BASIC", ASSIGN)
        
        # DIAGNOSTYKA / NORMALIZACJA: Upewnij się, że każdy assignment ma 'leader' i 'distance'
        try:
            board = getattr(game_engine, 'board', None)
            enriched = 0
            for a_idx, assign in enumerate(group_assignments):
                if not isinstance(assign, dict):
                    debug_print(f"[ASSIGNMENTS DEBUG] Pozycja {a_idx}: nie-dict -> {type(assign)}", "FULL", ASSIGN)
                    continue
                grp = assign.get('group')
                tgt = assign.get('target')
                if 'leader' not in assign:
                    if grp and len(grp) > 0:
                        assign['leader'] = grp[0]
                        enriched += 1
                        debug_print(f"[ASSIGNMENTS FIX] Dodano leader dla assignment {a_idx} -> {assign['leader'].get('id')}", "FULL", ASSIGN)
                    else:
                        debug_print(f"[ASSIGNMENTS WARN] Brak group lub pusta grupa w assignment {a_idx}", "BASIC", WARN)
                        continue
                # Distance – jeśli brak i mamy target
                if 'distance' not in assign:
                    distance = None
                    try:
                        if board and tgt and assign['leader']:
                            if hasattr(board, 'hex_distance'):
                                distance = board.hex_distance((assign['leader']['q'], assign['leader']['r']), tgt)
                            else:
                                path = board.find_path((assign['leader']['q'], assign['leader']['r']), tgt, max_mp=assign['leader'].get('mp',1), max_fuel=assign['leader'].get('fuel',1)) if hasattr(board, 'find_path') else None
                                if path:
                                    distance = len(path)-1
                    except Exception as de:
                        debug_print(f"[ASSIGNMENTS WARN] Błąd wyliczania distance dla {a_idx}: {de}", "BASIC", ERROR)
                    if distance is not None:
                        assign['distance'] = distance
                        debug_print(f"[ASSIGNMENTS FIX] Dodano distance={distance} dla assignment {a_idx}", "FULL", ASSIGN)
            if enriched:
                debug_print(f"[ASSIGNMENTS SUMMARY] Uzupełniono {enriched} assignmentów o brakujący leader", "FULL", ASSIGN)
        except Exception as dbg_e:
            debug_print(f"[ASSIGNMENTS DEBUG] Błąd normalizacji: {dbg_e}", "BASIC", ERROR)
        
        # 3. COMBAT PHASE - dla każdej jednostki sprawdź możliwe ataki
        combat_count = 0
        for i, unit in enumerate(my_units):
            unit_name = unit.get('id', f'unit_{i}')
            unit_id = unit.get('id')
            can_move_result = can_move(unit)

            # Jeśli brak paliwa spróbuj taktycznego uzupełnienia
            if not can_move_result and unit.get('fuel', 0) <= 0:
                debug_print(f"🔧 {unit_name} potrzebuje paliwa", "FULL", FUEL)
                commander_ref = getattr(game_engine, 'current_player_commander', None)
                debug_print(f"[DEBUG] commander_ref: {commander_ref}", "FULL", RESUPPLY)
                if commander_ref and hasattr(commander_ref, 'tactical_resupply'):
                    debug_print(f"Wywołuję tactical_resupply dla {unit_name}", "FULL", RESUPPLY)
                    resupply_success = commander_ref.tactical_resupply(game_engine, "LOW_FUEL", unit_id)
                    debug_print(f"tactical_resupply result: {resupply_success}", "FULL", RESUPPLY)
                    if resupply_success:
                        token = unit.get('token')
                        if token:
                            unit['fuel'] = getattr(token, 'currentFuel', 0)
                            unit['mp'] = getattr(token, 'currentMovePoints', 0)
                            can_move_result = can_move(unit)
                            debug_print(f"SUCCESS {unit_name} fuel={unit['fuel']} mp={unit['mp']}", "BASIC", RESUPPLY)
                else:
                    debug_print("Brak commander_ref lub tactical_resupply method", "BASIC", RESUPPLY)

            if can_move_result:
                combat_attempted = ai_attempt_combat(unit, game_engine, player_id, player_nation)
                if combat_attempted:
                    combat_count += 1
        debug_print(f"COMBAT PHASE: {combat_count} ataków wykonanych", "BASIC", TACTIC)

        # 3.1. MID-TURN TACTICAL RESUPPLY - uzupełnij jednostki po walkach
        debug_print("=== MID-TURN RESUPPLY ===", "BASIC", RESUPPLY)
        try:
            current_player = getattr(game_engine, 'current_player_obj', None)
            if current_player and hasattr(current_player, 'is_ai_commander'):
                commander_ref = getattr(game_engine, 'current_player_commander', None)
                if commander_ref and hasattr(commander_ref, 'tactical_resupply'):
                    damaged_units = [u for u in my_units if u.get('token') and 
                                     getattr(u.get('token'), 'combat_value', 0) < u.get('token').stats.get('combat_value', 0) * 0.7]
                    if damaged_units:
                        debug_print(f"Znaleziono {len(damaged_units)} jednostek wymagających uzupełnienia", "FULL", RESUPPLY)
                        commander_ref.tactical_resupply(game_engine, "DAMAGE")
                    else:
                        debug_print("Wszystkie jednostki w dobrej kondycji", "FULL", RESUPPLY)
        except Exception as e:
            debug_print(f"Błąd fazy mid-turn resupply: {e}", "BASIC", ERROR)

        # 3.5. NOWA FAZA DEFENSYWNA - ocena zagrożeń i planowanie obrony
        debug_print("=== FAZA DEFENSYWNA ===", "BASIC", DEFENSE)

        threat_assessment = assess_defensive_threats(my_units, game_engine)

        threatened_units = []
        for unit in my_units:
            assessment = threat_assessment.get(unit['id'], {})
            threat_level = assessment.get('threat_level', 0)
            if threat_level > 5:  # Próg zagrożenia
                threatened_units.append(unit)

        if threatened_units:
            debug_print(f"Znaleziono {len(threatened_units)} zagrożonych jednostek", "FULL", DEFENSE)

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
                            debug_print(f"{unit['id']} odwrót do {target_pos}", "FULL", DEFENSE)

            debug_print(f"Wykonano {retreat_count} ruchów defensywnych", "BASIC", DEFENSE)

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
                if not isinstance(assignment, dict):
                    debug_print(f"[ADVANCED MOVE] Pomijam assignment {assignment_idx} (typ {type(assignment)})", "FULL", MOVE)
                    continue
                group = assignment.get('group') or []
                if not group:
                    debug_print(f"[ADVANCED MOVE] Pomijam assignment {assignment_idx} (brak group)", "FULL", MOVE)
                    continue
                leader = assignment.get('leader')
                if leader is None:
                    leader = group[0]
                    assignment['leader'] = leader
                    debug_print(f"[ADVANCED MOVE FIX] Autouzupelniono leader dla assignment {assignment_idx} -> {leader.get('id')}", "FULL", MOVE)
                target = assignment.get('target')
                if target is None:
                    # Fallback 1: dynamic reasignacja jeszcze raz (rzadkie)
                    try:
                        reassign_try = dynamic_reassignment([assignment], game_engine)
                        if reassign_try and isinstance(reassign_try[0], dict):
                            target = reassign_try[0].get('target')
                            assignment['target'] = target
                    except Exception:
                        pass
                    # Fallback 2: lokalne wyszukanie celu dla lidera
                    if target is None:
                        try:
                            target_candidate = find_target(leader, game_engine)
                            if target_candidate:
                                target = target_candidate
                                assignment['target'] = target_candidate
                                debug_print(f"[ADVANCED MOVE FIX] Nadano awaryjny cel {target}", "FULL", MOVE)
                        except Exception as _ft_err:
                            debug_print(f"[ADVANCED MOVE WARN] Brak fallback target: {_ft_err}", "FULL", MOVE)
                
                # LOGOWANIE DECYZJI STRATEGICZNEJ
                if target:
                    debug_print(f"🎯 [STRATEGIC] Grupa {assignment_idx + 1} idzie do {target} - powód: przypisany cel", "BASIC", MOVE)
                else:
                    debug_print(f"⚠️ [STRATEGIC] Grupa {assignment_idx + 1} BEZ CELU - jednostki będą stać w miejscu", "BASIC", MOVE)
                # Distance fallback
                if 'distance' not in assignment:
                    board = getattr(game_engine, 'board', None)
                    dist_val = None
                    if board and target:
                        try:
                            if hasattr(board, 'hex_distance'):
                                dist_val = board.hex_distance((leader['q'], leader['r']), target)
                            else:
                                path = board.find_path((leader['q'], leader['r']), target, max_mp=leader.get('mp',1), max_fuel=leader.get('fuel',1)) if hasattr(board, 'find_path') else None
                                if path:
                                    dist_val = len(path)-1
                        except Exception as de2:
                            debug_print(f"[ADVANCED MOVE WARN] Nie mogę policzyć distance: {de2}", "BASIC", ERROR)
                    if dist_val is not None:
                        assignment['distance'] = dist_val
                distance_report = assignment.get('distance', '?')

                debug_print(f"🎯 [ADVANCED MOVE] Grupa {assignment_idx + 1}: {len(group)} żetonów -> cel {target}", "FULL", MOVE)
                debug_print(f"🎯 [ADVANCED MOVE] Lider: {leader.get('id')} (dystans: {distance_report})", "FULL", MOVE)

                # NOWE: Użyj priorytetów z adaptacyjnego systemu jeśli dostępne
                if strategic_plan and target and 'target_priorities' in strategic_plan:
                    # Sprawdź czy cel grupy pasuje do top priorytetów
                    target_str = f"{target[0]},{target[1]}"
                    for priority_hex, priority_data in strategic_plan['target_priorities']:
                        if priority_hex == target_str:
                            priority_level = priority_data['priority']
                            debug_print(f"🎯 [ADAPTIVE] Cel {target} ma priorytet {priority_level:.1f} ({priority_data['type']})", "FULL", ADAPTIVE)
                            break

                # Przetwórz wszystkie jednostki w grupie
                for unit_idx, unit in enumerate(group):
                    total_processed += 1
                    unit_name = unit.get('id', f'unit_{total_processed}')
                    can_move_result = can_move(unit)
                    # --- PERSISTENT TARGET ---
                    # Jeśli jednostka ma już assigned_target i to nie jest zrealizowane, nadpisz finalny target grupy
                    at = unit.get('assigned_target')
                    if at:
                        # Sprawdź czy cel nadal istnieje w key_points_state
                        kps = getattr(game_engine, 'key_points_state', {})
                        at_key = f"{at[0]},{at[1]}"
                        if at_key not in kps:  # jeśli zniknął (np. usunięty / zdobyty i skreślony) – wyczyść
                            unit.pop('assigned_target', None)
                        else:
                            target = at  # kontynuuj marsz
                    else:
                        # Nadaj nowe assigned_target jeśli nie ma i grupa ma target
                        unit['assigned_target'] = target
                        debug_print(f"🔒 [PERSIST] {unit_name}: przypisano stały cel {target}", "FULL", ASSIGN)
                    
                    # NOWE: Jeśli brak fuel - spróbuj uzupełnić
                    if not can_move_result and unit.get('fuel', 0) <= 0:
                        debug_print(f"🔧 [TACTICAL RESUPPLY] {unit_name} potrzebuje paliwa w fazie MOVEMENT", "FULL", RESUPPLY)
                        commander_ref = getattr(game_engine, 'current_player_commander', None)
                        if commander_ref and hasattr(commander_ref, 'tactical_resupply'):
                            resupply_success = commander_ref.tactical_resupply(game_engine, "LOW_FUEL", unit.get('id'))
                            if resupply_success:
                                token = unit.get('token')
                                if token:
                                    unit['fuel'] = getattr(token, 'currentFuel', 0)
                                    unit['mp'] = getattr(token, 'currentMovePoints', 0)
                                    can_move_result = can_move(unit)
                                    debug_print(f"🔧 [RESUPPLY SUCCESS] {unit_name} fuel = {unit['fuel']}, mp = {unit['mp']}", "FULL", RESUPPLY)
                        else:
                            debug_print(f"🔧 [RESUPPLY FAILED] Brak commander_ref lub tactical_resupply method", "BASIC", RESUPPLY)
                    
                    # NOWE: jeśli jednostka utrzymuje pozycję (garnizon) pomijamy ruch
                    if is_unit_holding(unit):
                        debug_print(f"🛡️ [ADVANCED MOVE] {unit_name}: UTRZYMUJE POZYCJĘ (garnizon)", "FULL", MOVE)
                        continue

                    if can_move_result:
                        # NOWE: Adaptacyjna taktyka na podstawie stanu strategicznego
                        final_target = target
                        if final_target is None:
                            debug_print(f"[ADVANCED MOVE] Pomijam jednostkę {unit_name} brak celu", "FULL", MOVE)
                            continue
                        if strategic_plan:
                            final_target = adaptive_ai._adaptive_movement_tactics(
                                unit, target, strategic_plan, game_engine
                            ) if adaptive_ai else target

                        debug_print(f"🚨 [MOVE] Wywołuję move_towards dla {unit_name}", "FULL", MOVE)
                        success = move_towards(unit, final_target, game_engine)
                        if success:
                            moved_count += 1
                            # Jeśli osiągnięto cel (stanęliśmy na heksie celu) można zwolnić assigned_target
                            if (unit.get('q'), unit.get('r')) == unit.get('assigned_target'):
                                debug_print(f"🏁 [PERSIST] {unit_name}: osiągnięto cel {unit['assigned_target']}, zwalniam", "FULL", ASSIGN)
                                unit.pop('assigned_target', None)
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
                            debug_print(f"✅ [ADVANCED MOVE] {unit_name}: Ruch do {final_target}", "BASIC", MOVE)
                        else:
                            debug_print(f"❌ [ADVANCED MOVE] {unit_name}: Ruch nieudany", "BASIC", MOVE)
                    else:
                        debug_print(f"⚠️ [ADVANCED MOVE] {unit_name}: Nie może się ruszyć (MP={unit.get('mp', 0)}, Fuel={unit.get('fuel', 0)})", "FULL", MOVE)

        debug_print(f"[AI] Ruszono {moved_count} jednostek z {len(my_units)} (sukces: {moved_count/len(my_units)*100:.1f}%)", "BASIC", MOVE)

        # LOGUJ KONIEC TURY (szczegółowy w actions + zagregowany w turns)
        group_count = len(group_assignments)
        mode_type = "advanced"
        opportunistic_count = len(opportunistic_captured) if 'opportunistic_captured' in locals() and opportunistic_captured else 0
        # Przygotuj podstawowe metryki artylerii (jeśli tokens mają pola strzałów)
        artillery_tokens = [u for u in my_units if u.get('token') and getattr(u.get('token'), 'is_artillery', lambda: False)()]
        total_artillery = len(artillery_tokens)
        total_shots = 0
        reaction_used = 0
        for u in artillery_tokens:
            t = u.get('token')
            total_shots += getattr(t, 'shots_fired_this_turn', 0) or 0
            if getattr(t, 'reaction_shot_used', False):
                reaction_used += 1
        avg_shots = round(total_shots / total_artillery, 2) if total_artillery > 0 else 0

        # Resupply (jeśli commander_ref posiada liczniki – TODO: dodać w zaopatrzeniu)
        commander_ref = getattr(game_engine, 'current_player_commander', None)
        resupply_attempts = getattr(commander_ref, 'resupply_attempts_this_turn', None)
        resupply_successes = getattr(commander_ref, 'resupply_successes_this_turn', None)

        threatened_units_count = len(threatened_units) if 'threatened_units' in locals() else 0

        # Akcja szczegółowa (stary CSV)
        log_commander_action(
            unit_id="TURN_END",
            action_type="turn_summary",
            from_pos=None,
            to_pos=None,
            reason=f"Turn completed: {moved_count}/{len(my_units)} units moved, {group_count} groups ({mode_type})",
            player_nation=player_nation,
            extra={
                'decision_reason': mode_type,
                'extra_tags': f"opp={opportunistic_count};groups={group_count};adv={advanced_mode}",
                'path_used': moved_count,
                'path_len': len(my_units)
            }
        )

        # Zagregowany CSV (turns_*.csv)
        turn_number = getattr(game_engine, 'turn_number', getattr(game_engine, 'current_turn', None))
        econ_weight = getattr(commander_ref, 'econ_weight', None) if commander_ref else None
        vp_weight = getattr(commander_ref, 'vp_weight', None) if commander_ref else None
        low_income_streak = getattr(commander_ref, 'turns_on_low_income', None) if commander_ref else None
        # Oblicz straty (casualties_turn) i nowe jednostki (new_units_turn)
        final_units = get_my_units(game_engine, player_id)
        final_unit_ids = {u.get('id') for u in final_units}
        casualties_turn = len([uid for uid in starting_unit_ids if uid and uid not in final_unit_ids]) if starting_unit_ids else 0
        new_units_turn = max(0, len([uid for uid in final_unit_ids if uid and uid not in starting_unit_ids]))

        log_commander_turn({
            'turn': turn_number,
            'nation': player_nation,
            'mode': mode_type,
            'groups': group_count,
            'units_total': len(my_units),
            'units_moved': moved_count,
            'moved_pct': round(moved_count / len(my_units) * 100, 1) if my_units else 0,
            'opportunistic_captures': opportunistic_count,
            'combats': combat_count,
            'retreats': retreat_count if 'retreat_count' in locals() else 0,
            'deployments': deployed_count if 'deployed_count' in locals() else 0,
            'resupply_attempts': 0,  # TODO: będzie dodane w przyszłości
            'resupply_successes': 0,
            'threatened_units': len(threatened_units) if 'threatened_units' in locals() else 0,
            'low_income_streak': low_income_streak,
            'econ_weight': econ_weight,
            'vp_weight': vp_weight,
            'artillery_units': total_artillery,
            'artillery_shots': total_shots,
            'artillery_reaction_used': reaction_used,
            'artillery_avg_shots': avg_shots,
            'casualties_turn': casualties_turn,
            'new_units_turn': new_units_turn,
            # === NOWE DIAGNOSTYKI FAZA 1 ===
            'total_targets_analyzed': len(locals().get('prioritized_targets', [])),
            'avg_target_score': round(sum(t.get('priority', 0) for t in locals().get('prioritized_targets', [])[:10]) / min(10, len(locals().get('prioritized_targets', []))), 2) if locals().get('prioritized_targets') else 0,
            'targets_with_fallback': 0,  # TODO: liczyć w find_target
            'groups_without_targets': len([a for a in locals().get('group_assignments', []) if isinstance(a, dict) and not a.get('target')]),
            'dynamic_reassignments': 0,  # TODO: liczyć w dynamic_reassignment
            'strategic_state': strategic_plan.get('state') if strategic_plan else 'UNKNOWN',
            'aggression_level': strategic_plan.get('aggression_level') if strategic_plan else 0.5,
            'high_priority_targets': len([t for t in locals().get('prioritized_targets', [])[:5] if t.get('priority', 0) > 50]),
            'free_targets_captured': len([t for t in locals().get('prioritized_targets', [])[:10] if t.get('free', False)]),
            'coordination_failures': 0,  # TODO: liczyć niepowodzenia w assign_targets_with_coordination
            'memory_targets_used': 0,  # TODO: liczyć użycie ai_target_memory
            'tactical_resupply_calls': 0,  # TODO: liczyć wywołania tactical_resupply
            'notes': f"Advanced mode: {advanced_mode}, Strategic plan: {strategic_plan is not None}"
        })

    except Exception as e:
        debug_print(f"[AI] Błąd tury: {e}", "BASIC", ERROR)
        # NIE CRASHUJ - po prostu zakończ turę


class AICommander:
    """Wrapper klasa dla kompatybilności z istniejącym kodem"""
    def __init__(self, player: Any):
        """Inicjalizacja prostych pól konfiguracyjnych dowódcy AI."""
        try:
            self.player = player
            # Garrisony i limity
            self.garrisons = {}
            self.min_garrison_size = 1
            self.max_garrison_fraction = 0.3
            self.default_garrison_size = 1
            # Wagi strategiczne (mogą być adaptowane później)
            self.econ_weight = 1.0
            self.vp_weight = 0.5
            # Ekonomia adaptacyjna
            self.turns_on_low_income = 0
            self.low_income_threshold = 5
            # Kolejka drugiego ruchu po mid‑turn tankowaniu
            self._second_chance_queue = []
            # Flaga zapobiegająca wielokrotnemu PRE_TURN resupply
            self._did_pre_resupply_turn = None
            # Śledzenie liczby mid-turn resupply per jednostka w bieżącej turze
            self._mid_turn_resupply_counts = {}
            # Globalny cooldown dla triggera LOW_FUEL (jedno zbiorcze wywołanie na segment ruchu)
            self._last_low_fuel_resupply_turn = None
            self._low_fuel_resupply_used_this_turn = False
        except Exception:
            # W ostateczności nie blokuj dalszego działania
            pass

    def should_hold_position(self, unit_dict: dict) -> bool:
        """Zwraca True jeśli jednostka ma pozostać na zajętym key poincie.
        Używa atrybutu token.hold_position ustawianego przy wejściu na punkt.
        """
        token = unit_dict.get('token')
        if not token:
            return False
        return bool(getattr(token, 'hold_position', False))

    def pre_resupply(self, game_engine: Any) -> None:
            from ai.zaopatrzenie_ai import pre_resupply as _pr
            return _pr(self, game_engine)

    def tactical_resupply(self, game_engine: Any, trigger: str = "DAMAGE", unit_id: str = None) -> bool:
            from ai.zaopatrzenie_ai import tactical_resupply as _tr
            return _tr(self, game_engine, trigger, unit_id)

    def _perform_resupply(self, game_engine: Any, punkty: int, context: str) -> bool:
        from ai.zaopatrzenie_ai import _perform_resupply as _prf
        return _prf(self, game_engine, punkty, context)

    def _process_second_chance_moves(self, game_engine, context: str):
        from ai.zaopatrzenie_ai import _process_second_chance_moves as _scm
        return _scm(self, game_engine, context)

    def _is_token_in_combat_zone(self, token, game_engine) -> bool:
        from ai.zaopatrzenie_ai import _is_token_in_combat_zone as _cz
        return _cz(self, token, game_engine)

    def make_tactical_turn(self, game_engine: Any) -> None:
        """Wykonaj turę taktyczną - używa prostych funkcji"""
        player_id = getattr(self.player, 'id', None)
        debug_print(f"[AICommander] Tura dla {self.player.nation} (id={player_id})", "BASIC", INFO)
        make_tactical_turn(game_engine, player_id)

    # === USUNIĘTO SYSTEM ROZKAZÓW ===
    # AI Dowódcy działają autonomicznie bez rozkazów od AI Generała


# ========== STRATEGIA DEFENSYWNA (delegaty do ai.obrona_ai) ==========

def calculate_hex_distance(pos1, pos2):  # delegat
    from ai.obrona_ai import calculate_hex_distance as _chd
    return _chd(pos1, pos2)

def get_all_key_points(game_engine):  # delegat
    from ai.obrona_ai import get_all_key_points as _gakp
    return _gakp(game_engine)

def assess_defensive_threats(my_units, game_engine):  # delegat
    from ai.obrona_ai import assess_defensive_threats as _adt
    return _adt(my_units, game_engine)

def plan_defensive_retreat(threatened_units, threat_assessment, game_engine):  # delegat
    from ai.obrona_ai import plan_defensive_retreat as _pdr
    return _pdr(threatened_units, threat_assessment, game_engine)

def find_safe_retreat_position(unit, target_point, threatening_enemies, game_engine):  # delegat
    from ai.obrona_ai import find_safe_retreat_position as _fsr
    return _fsr(unit, target_point, threatening_enemies, game_engine)

def find_safe_fallback_position(unit, threatening_enemies, game_engine):  # delegat
    from ai.obrona_ai import find_safe_fallback_position as _ffp
    return _ffp(unit, threatening_enemies, game_engine)

def evaluate_position_safety(position, threatening_enemies, target_point=None):  # delegat
    from ai.obrona_ai import evaluate_position_safety as _eps
    return _eps(position, threatening_enemies, target_point)


def deploy_purchased_units(game_engine, player_id):  # delegat do deployment_ai
    from ai.deployment_ai import deploy_purchased_units as _dpu
    return _dpu(game_engine, player_id)


def find_deployment_position(unit_data, game_engine, player_id):
    """Znajduje najlepszą pozycję do wdrożenia nowej jednostki - INTELIGENTNY SYSTEM"""
    try:
        # Import inteligentnego systemu spawnowania
        import sys
        import os
        sys.path.append(os.path.dirname(__file__))
        from smart_deployment import find_optimal_spawn_position, LAST_DEPLOY_CHOICE
        debug_print(f"[DEPLOY] Używam inteligentnego systemu spawnowania...", "FULL", DEPLOY)
        optimal_position = find_optimal_spawn_position(unit_data, game_engine, player_id)
        
        if optimal_position:
            # Jeśli global LAST_DEPLOY_CHOICE zawiera breakdown – pokaż krótki powód
            try:
                from smart_deployment import LAST_DEPLOY_CHOICE as _LDC
                if _LDC and _LDC.get('position') == optimal_position:
                    debug_print(f"[DEPLOY] Inteligentny system wybrał pozycję: {optimal_position} | { _LDC.get('reason','') }", "BASIC", DEPLOY)
            except Exception:
                debug_print(f"[DEPLOY] Inteligentny system wybrał pozycję: {optimal_position}", "BASIC", DEPLOY)
            return optimal_position
        else:
            debug_print(f"[DEPLOY] Inteligentny system nie znalazł pozycji, używam fallback...", "BASIC", DEPLOY)
            
    except Exception as e:
        debug_print(f"[DEPLOY] Błąd w inteligentnym systemie: {e}, używam fallback...", "BASIC", ERROR)
    
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
                debug_print(f"[DEPLOY] Fallback wybrał pozycję: {spawn_pos}", "FULL", DEPLOY)
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
                    debug_print(f"[DEPLOY] Fallback wybrał sąsiada spawnu: {neighbor}", "FULL", DEPLOY)
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
        debug_print(f"[DEPLOY] Błąd tworzenia tokena: {e}", "BASIC", ERROR)
        import traceback
        traceback.print_exc()
        return False


def defensive_coordination(my_units, threat_assessment, game_engine):  # delegat
    from ai.obrona_ai import defensive_coordination as _dc
    return _dc(my_units, threat_assessment, game_engine)

def plan_group_defense(key_point, defending_units, game_engine):  # delegat
    from ai.obrona_ai import plan_group_defense as _pgd
    return _pgd(key_point, defending_units, game_engine)


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
        debug_print("TEST: Brak crashu przy pustych danych ✓", "FULL", INFO)
        return True
    except Exception as e:
        debug_print(f"TEST: Błąd - {e}", "BASIC", ERROR)
        return False

if __name__ == "__main__":
    # Uruchom test bezpieczeństwa
    test_basic_safety()


# enforce_garrison_limits -> ai.okupacja_punktow


# Eksport kluczowych funkcji dla użycia zewnętrznego
__all__ = [
    'AICommander', 'AdaptiveAICommander', 'make_tactical_turn', 'check_ai_reaction_attacks', 
    'ai_attempt_combat', 'evaluate_combat_ratio', 'execute_ai_combat',
    'test_basic_safety', 'log_commander_action', 'enforce_garrison_limits'
]

