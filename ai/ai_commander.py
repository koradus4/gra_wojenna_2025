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
import os


def log_commander_action(unit_id, action_type, from_pos, to_pos, reason, player_nation="Unknown"):
    """Loguj akcję AI Commander do CSV w dedykowanym folderze"""
    try:
        # Utwórz katalog logs/ai_commander/ jeśli nie istnieje
        log_dir = "logs/ai_commander"
        if not os.path.exists(log_dir):
            os.makedirs(log_dir)
        
        # Nazwa pliku z datą w folderze ai_commander
        today = datetime.date.today()
        log_file = f"{log_dir}/actions_{today:%Y%m%d}.csv"
        
        # Sprawdź czy plik istnieje, jeśli nie - dodaj nagłówek
        file_exists = os.path.exists(log_file)
        
        with open(log_file, 'a', newline='', encoding='utf-8') as f:
            writer = csv.writer(f)
            
            # Dodaj nagłówek jeśli nowy plik
            if not file_exists:
                writer.writerow([
                    'timestamp', 'nation', 'unit_id', 'action_type', 
                    'from_q', 'from_r', 'to_q', 'to_r', 'reason'
                ])
            
            # Dodaj wpis
            timestamp = datetime.datetime.now().isoformat()
            from_q, from_r = from_pos if from_pos else (None, None)
            to_q, to_r = to_pos if to_pos else (None, None)
            
            writer.writerow([
                timestamp, player_nation, unit_id, action_type,
                from_q, from_r, to_q, to_r, reason
            ])
            
    except Exception as e:
        print(f"[AI] Błąd logowania: {e}")


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
    
    # Sprawdź key points (max 20)
    kp_count = 0
    for hex_id, kp_data in key_points.items():
        if kp_count >= 20:
            break
        kp_count += 1
        
        # Parsuj hex_id do współrzędnych
        try:
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
                    if actual_distance < best_distance:
                        best_target = kp_pos
                        best_distance = actual_distance
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


def move_towards(unit, target, game_engine):
    """Wykonaj ruch w kierunku celu - PARTIAL JEŚLI TRZEBA"""
    
    print(f"[AI] Szukam ścieżki {unit['id']}: ({unit['q']},{unit['r']}) -> {target}")
    
    board = getattr(game_engine, 'board', None)
    if not board:
        print(f"[AI] Brak board w game_engine")
        return False

    unit_pos = (unit['q'], unit['r'])
    token = unit['token']    # Znajdź ścieżkę Z LIMITEM MP
    try:
        # Próbuj pełną ścieżkę
        path = board.find_path(
            unit_pos, target,
            max_mp=unit['mp'],
            max_fuel=unit['fuel']
        )
        
        print(f"[AI] Ścieżka z limitem (MP:{unit['mp']}, Fuel:{unit['fuel']}): {path}")
        
        # Sprawdź czy to pełna ścieżka czy częściowa
        is_partial_path = False
        
        # Jeśli brak pełnej - spróbuj częściowej
        if not path:
            unlimited_path = board.find_path(unit_pos, target)
            print(f"[AI] Ścieżka bez limitu: {unlimited_path}")
            
            if unlimited_path and len(unlimited_path) > 1:
                # Weź tyle kroków ile masz MP
                steps = min(unit['mp'], len(unlimited_path) - 1, 10)
                path = unlimited_path[:steps + 1]
                is_partial_path = True
                print(f"[AI] Częściowa ścieżka ({steps} kroków): {path}")
        
        # Wykonaj ruch jeśli mamy ścieżkę
        if path and len(path) > 1:
            from engine.action_refactored_clean import MoveAction
            
            # MoveAction oczekuje token_id (string) i docelowe współrzędne
            target_hex = path[-1]  # Ostatni hex w ścieżce
            token_id = getattr(token, 'id', None)
            
            if token_id:
                action = MoveAction(token_id, target_hex[0], target_hex[1])
                result = game_engine.execute_action(action)
                
                # ActionResult ma atrybut success, nie metodę get()
                success = getattr(result, 'success', False) if result else False
                if success:
                    print(f"[AI] Ruch {unit['id']}: {unit_pos} -> {target_hex}")
                    
                    # DODAJ LOGOWANIE DO CSV
                    player_nation = "Unknown"
                    current_player = getattr(game_engine, 'current_player_obj', None)
                    if current_player:
                        player_nation = getattr(current_player, 'nation', 'Unknown')
                    
                    # Określ typ ruchu
                    if is_partial_path:
                        move_type = "move_partial"
                        reason = f"Partial path to target {target} (MP limited)"
                    else:
                        move_type = "move_full"
                        reason = f"Full path to target {target}"
                    
                    log_commander_action(
                        unit_id=unit['id'],
                        action_type=move_type,
                        from_pos=unit_pos,
                        to_pos=target_hex,
                        reason=reason,
                        player_nation=player_nation
                    )
                else:
                    print(f"[AI] Ruch nieudany {unit['id']}: {getattr(result, 'message', 'Nieznany błąd')}")
                    
                    # LOGUJ TAKŻE NIEUDANE RUCHY
                    player_nation = "Unknown"
                    current_player = getattr(game_engine, 'current_player_obj', None)
                    if current_player:
                        player_nation = getattr(current_player, 'nation', 'Unknown')
                    
                    log_commander_action(
                        unit_id=unit['id'],
                        action_type="move_failed",
                        from_pos=unit_pos,
                        to_pos=target_hex,
                        reason=f"Failed: {getattr(result, 'message', 'Unknown error')}",
                        player_nation=player_nation
                    )
                return success
            else:
                print(f"[AI] Brak ID tokenu dla {unit['id']}")
                return False
            
    except Exception as e:
        print(f"[AI] Błąd ruchu: {e}")
        
    return False


def make_tactical_turn(game_engine, player_id=None):
    """Główna funkcja AI Commandera - PROSTA I BEZPIECZNA
    
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
        
        # 1. Zbierz dane
        my_units = get_my_units(game_engine, player_id)
        print(f"[AI] Znaleziono {len(my_units)} jednostek dla gracza {player_id}")
        if not my_units:
            print(f"[AI] Brak jednostek dla gracza {player_id}")
            return
        
        # 2. Dla każdej jednostki znajdź cel i rusz
        moved_count = 0
        for i, unit in enumerate(my_units[:5]):  # MAX 5 jednostek na turę
            unit_name = unit.get('id', f'unit_{i}')
            can_move_result = can_move(unit)
            print(f"[AI] {unit_name}: MP={unit.get('mp', 0)}, Fuel={unit.get('fuel', 0)}, Can move: {can_move_result}")
            
            if can_move_result:
                target = find_target(unit, game_engine)
                if target:
                    success = move_towards(unit, target, game_engine)
                    if success:
                        moved_count += 1
                else:
                    print(f"[AI] {unit_name}: Brak celu")
            else:
                print(f"[AI] {unit_name}: Nie może się ruszyć")
        
        print(f"[AI] Ruszono {moved_count} jednostek z {min(len(my_units), 5)}")
        
        # LOGUJ KONIEC TURY
        log_commander_action(
            unit_id="TURN_END",
            action_type="turn_summary",
            from_pos=None,
            to_pos=None,
            reason=f"Turn completed: {moved_count}/{min(len(my_units), 5)} units moved",
            player_nation=player_nation
        )
        
    except Exception as e:
        print(f"[AI] Błąd tury: {e}")
        # NIE CRASHUJ - po prostu zakończ turę


class AICommander:
    """Wrapper klasa dla kompatybilności z istniejącym kodem"""
    def __init__(self, player: Any):
        self.player = player

    def pre_resupply(self, game_engine: Any) -> None:
        """Placeholder dla kompatybilności"""
        pass

    def make_tactical_turn(self, game_engine: Any) -> None:
        """Wykonaj turę taktyczną - używa prostych funkcji"""
        player_id = getattr(self.player, 'id', None)
        print(f"[AICommander] Tura dla {self.player.nation} (id={player_id})")
        make_tactical_turn(game_engine, player_id)


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

