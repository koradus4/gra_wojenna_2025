import random
import os
import json
from typing import Dict, Any, Optional, Tuple

from ai.logs import log_token
from engine.board import Board
from engine.token import load_tokens, Token
from engine.action_refactored_clean import ActionResult

class GameEngine:
    def __init__(self, map_path: str, tokens_index_path: str, tokens_start_path: str, seed: int = 42, read_only: bool = False):
        self.random = random.Random(seed)
        self.board = Board(map_path)
        self.read_only = read_only  # Dodana flaga tylko do odczytu
        state_path = os.path.join("saves", "latest.json")
        if os.path.exists(state_path):
            self.load_state(state_path)
        else:
            self.tokens = load_tokens(tokens_index_path, tokens_start_path)
            self.board.set_tokens(self.tokens)
            self.turn = 1
            self.current_player = 0
        self._init_key_points_state()
        self.ai_reserved_hexes = {}
        self.ai_enemy_memory: Dict[str, Dict[str, Any]] = {}

    def _init_key_points_state(self):
        """Tworzy słownik: hex_id -> {'initial_value': X, 'current_value': Y, 'type': ...} na podstawie mapy."""
        self.key_points_state = {}
        if hasattr(self.board, 'key_points'):
            for hex_id, kp in self.board.key_points.items():
                self.key_points_state[hex_id] = {
                    'initial_value': kp['value'],
                    'current_value': kp['value'],
                    'type': kp.get('type', None)
                }

    def save_state(self, filepath: str):
        os.makedirs(os.path.dirname(filepath), exist_ok=True)
        state = {
            "tokens": [t.serialize() for t in self.tokens],
            "turn": self.turn,
            "current_player": self.current_player
        }
        tmp_file = filepath + ".tmp"
        with open(tmp_file, "w", encoding="utf-8") as f:
            json.dump(state, f, indent=2, ensure_ascii=False)
        os.replace(tmp_file, filepath)

    def load_state(self, filepath: str):
        with open(filepath, "r", encoding="utf-8") as f:
            state = json.load(f)
        self.tokens = [Token.from_dict(t) for t in state["tokens"]]
        self.board.set_tokens(self.tokens)
        self.turn = state["turn"]
        self.current_player = state["current_player"]

    def next_turn(self):
        self.turn += 1
        self.current_player = (self.current_player + 1) % self.get_player_count()
        # Reset punktów ruchu dla wszystkich żetonów
        for token in self.tokens:
            # Ustaw wartości zgodnie z aktualnym trybem ruchu i zresetuj MP
            if hasattr(token, 'apply_movement_mode'):
                try:
                    token.apply_movement_mode(reset_mp=True)
                except Exception:
                    # awaryjnie przywróć proste wartości
                    max_mp = getattr(token, 'maxMovePoints', token.stats.get('move', 0))
                    token.maxMovePoints = max_mp
                    token.currentMovePoints = max_mp
            else:
                max_mp = getattr(token, 'maxMovePoints', getattr(token, 'stats', {}).get('move', 0))
                token.maxMovePoints = max_mp
                token.currentMovePoints = max_mp
            
            # NOWE: Reset ograniczeń strzałów artylerii na początku nowej tury
            if hasattr(token, 'reset_turn_actions'):
                token.reset_turn_actions()
        # Reset morale, pogoda itp. (jeśli dotyczy)
        # Wyczyść tymczasową widoczność i przelicz FOW po zmianie tury
        if hasattr(self, 'players'):
            try:
                clear_temp_visibility(self.players)
                update_all_players_visibility(self.players, self.tokens, self.board)
            except Exception:
                pass

        self.ai_reserved_hexes = {}
        self._decay_enemy_memory()

    def end_turn(self):
        self.next_turn()
        self.save_state(os.path.join("saves", "latest.json"))

    def get_player_count(self):
        # Zaimplementuj zgodnie z logiką graczy
        try:
            return len(getattr(self, 'players', [])) or 2
        except Exception:
            return 2

    def get_state(self):
        """Zwraca uproszczony stan gry do GUI."""
        return {
            'turn': self.turn,
            'tokens': [t.serialize() for t in self.tokens]
        }

    def execute_action(self, action, player=None):
        """Rejestruje i wykonuje akcję (np. ruch, walka). Weryfikuje właściciela żetonu."""
        # Sprawdzenie właściciela żetonu
        token = next((t for t in self.tokens if t.id == getattr(action, 'token_id', None)), None)
        if player and token:
            expected_owner = f"{player.id} ({player.nation})"
            if token.owner != expected_owner:
                return False, "Ten żeton nie należy do twojego dowódcy."
        pre_state = self._prepare_action_log_state(action, token)
        result = action.execute(self)
        self._log_human_action(action, player, pre_state, result)
        return result

    # ------------------------------------------------------------------
    # Human action logging helpers
    # ------------------------------------------------------------------

    def _prepare_action_log_state(self, action, attacker_token: Optional[Token]):
        state: Dict[str, Optional[Dict[str, Any]]] = {
            "attacker": self._capture_token_snapshot(attacker_token),
            "defender": None,
        }
        defender_id = getattr(action, "defender_id", None)
        if defender_id:
            defender = next((t for t in self.tokens if t.id == defender_id), None)
            state["defender"] = self._capture_token_snapshot(defender)
        return state

    def _capture_token_snapshot(self, token: Optional[Token]) -> Optional[Dict[str, Any]]:
        if token is None:
            return None
        stats = getattr(token, "stats", {}) or {}
        return {
            "id": getattr(token, "id", None),
            "name": getattr(token, "name", None),
            "owner": getattr(token, "owner", None),
            "position": (getattr(token, "q", None), getattr(token, "r", None)),
            "combat_value": getattr(token, "combat_value", None),
            "currentMovePoints": getattr(token, "currentMovePoints", None),
            "currentFuel": getattr(token, "currentFuel", None),
            "movement_mode": getattr(token, "movement_mode", None),
            "type": stats.get("type"),
        }

    def _capture_post_action_state(self, action, pre_state: Dict[str, Optional[Dict[str, Any]]]) -> Dict[str, Optional[Dict[str, Any]]]:
        attacker_id = None
        if pre_state.get("attacker"):
            attacker_id = pre_state["attacker"].get("id")
        attacker_id = attacker_id or getattr(action, "token_id", None)
        defender_id = None
        if pre_state.get("defender"):
            defender_id = pre_state["defender"].get("id")
        defender_id = defender_id or getattr(action, "defender_id", None)

        attacker_token = None
        defender_token = None
        if attacker_id:
            attacker_token = next((t for t in self.tokens if t.id == attacker_id), None)
        if defender_id:
            defender_token = next((t for t in self.tokens if t.id == defender_id), None)

        return {
            "attacker": self._capture_token_snapshot(attacker_token),
            "defender": self._capture_token_snapshot(defender_token),
        }

    def _extract_action_result(self, result) -> Tuple[bool, Optional[str], Dict[str, Any]]:
        if isinstance(result, ActionResult):
            return bool(result.success), getattr(result, "message", None), getattr(result, "data", {}) or {}
        if isinstance(result, tuple):
            success = bool(result[0]) if result else False
            message = result[1] if len(result) > 1 else None
            data = result[2] if len(result) > 2 else {}
            if not isinstance(data, dict):
                data = {}
            return success, message, data
        success = bool(getattr(result, "success", False))
        message = getattr(result, "message", None)
        data = getattr(result, "data", {})
        if not isinstance(data, dict):
            data = {}
        return success, message, data

    def _resolve_turn_number(self) -> Optional[int]:
        turn_manager = getattr(self, "turn_manager", None)
        if turn_manager is not None:
            try:
                turn_value = getattr(turn_manager, "current_turn", None)
            except Exception:
                turn_value = None
            if turn_value is not None:
                return turn_value
        return getattr(self, "turn", None)

    def _log_human_action(self, action, player, pre_state: Dict[str, Optional[Dict[str, Any]]], result) -> None:
        if player is None or getattr(player, "is_ai", False):
            return
        try:
            from ai.logs.human_logger import log_human_action
        except Exception:
            return

        success, message, data = self._extract_action_result(result)
        post_state = self._capture_post_action_state(action, pre_state)
        action_type, summary, context = self._summarize_action_for_human_logs(
            action,
            pre_state,
            post_state,
            success,
            message,
            data,
        )

        turn_number = self._resolve_turn_number()
        result_text = message if message else ("OK" if success else None)
        try:
            log_human_action(
                player=player,
                turn=turn_number,
                action_type=action_type,
                summary=summary,
                result=result_text,
                context=context,
            )
        except Exception:
            pass

    def _summarize_action_for_human_logs(
        self,
        action,
        pre_state: Dict[str, Optional[Dict[str, Any]]],
        post_state: Dict[str, Optional[Dict[str, Any]]],
        success: bool,
        message: Optional[str],
        data: Dict[str, Any],
    ) -> Tuple[str, str, Dict[str, Any]]:
        action_name = action.__class__.__name__
        action_type = {
            "MoveAction": "move",
            "CombatAction": "attack",
        }.get(action_name, action_name.lower())

        summary = message or action_type
        context: Dict[str, Any] = {
            "success": success,
        }
        if message:
            context["message"] = message

        attacker_before = pre_state.get("attacker") or {}
        attacker_after = post_state.get("attacker") or {}
        defender_before = pre_state.get("defender") or {}
        defender_after = post_state.get("defender") or {}

        token_id = attacker_before.get("id") or getattr(action, "token_id", None)

        if action_name == "MoveAction":
            start_pos = attacker_before.get("position")
            end_pos = data.get("final_position") or attacker_after.get("position")
            path_cost = data.get("path_cost")
            fuel_cost = data.get("fuel_cost")
            remaining_mp = data.get("remaining_mp", attacker_after.get("currentMovePoints"))
            remaining_fuel = data.get("remaining_fuel", attacker_after.get("currentFuel"))
            status = "sukces" if success else "nieudany"
            summary = f"{token_id} ruch {start_pos} -> {end_pos} ({status})"
            if not success and message:
                summary += f" - {message}"
            context.update(
                {
                    "token_id": token_id,
                    "start_position": start_pos,
                    "end_position": end_pos,
                    "path_cost": path_cost,
                    "fuel_cost": fuel_cost,
                    "remaining_mp": remaining_mp,
                    "remaining_fuel": remaining_fuel,
                    "movement_mode_before": attacker_before.get("movement_mode"),
                    "movement_mode_after": attacker_after.get("movement_mode"),
                }
            )
        elif action_name == "CombatAction":
            defender_id = defender_before.get("id") or getattr(action, "defender_id", None)
            combat_result = data.get("combat_result", {}) if isinstance(data, dict) else {}
            damage_dealt = combat_result.get("attack_result")
            damage_taken = combat_result.get("defense_result")
            counterattack = combat_result.get("can_counterattack")
            outcome = "sukces" if success else "porażka"
            summary = f"{token_id} atakuje {defender_id}: {outcome}"
            if defender_after is None and defender_before:
                summary += " (cel zniszczony)"
            if attacker_after is None and attacker_before:
                summary += " (atakujący zniszczony)"
            context.update(
                {
                    "token_id": token_id,
                    "target_token_id": defender_id,
                    "attacker_position_before": attacker_before.get("position"),
                    "attacker_position_after": attacker_after.get("position"),
                    "defender_position_before": defender_before.get("position"),
                    "defender_position_after": defender_after.get("position"),
                    "damage_dealt": damage_dealt,
                    "damage_taken": damage_taken,
                    "counterattack": counterattack,
                    "attacker_cv_before": attacker_before.get("combat_value"),
                    "attacker_cv_after": attacker_after.get("combat_value"),
                    "defender_cv_before": defender_before.get("combat_value"),
                    "defender_cv_after": defender_after.get("combat_value"),
                    "attacker_remaining_cv": data.get("attacker_remaining"),
                    "defender_remaining_cv": data.get("defender_remaining"),
                    "combat_detail": combat_result,
                }
            )
        else:
            status = "sukces" if success else "porażka"
            summary = f"{token_id or action_type}: {action_type} ({status})"
            context.update(
                {
                    "token_id": token_id,
                    "details": data,
                }
            )

        return action_type, summary, context

    # --- Współdzielona pamięć przeciwnika ---

    def _enemy_memory_key(self, commander_key: str) -> str:
        return commander_key or "global"

    def register_enemy_sighting(
        self,
        commander_key: str,
        enemy_id: str,
        position,
        turn: int,
        unit_type: str = None,
        source_token_id: int = None,
    ) -> None:
        if position is None or len(position) != 2:
            return

        key = self._enemy_memory_key(str(commander_key) if commander_key is not None else "global")
        sightings = self.ai_enemy_memory.setdefault(key, {})
        existing = sightings.get(enemy_id)
        if existing and existing.get("turn", -1) > turn:
            return

        sightings[enemy_id] = {
            "position": (position[0], position[1]),
            "turn": turn,
            "unit_type": unit_type,
            "source": source_token_id,
        }

    def get_enemy_sightings(self, commander_key: str, max_age: int = None):
        key = self._enemy_memory_key(str(commander_key) if commander_key is not None else "global")
        sightings = self.ai_enemy_memory.get(key, {})
        if not sightings:
            return {}

        if max_age is None:
            return dict(sightings)

        current_turn = getattr(self, "turn", 0)
        filtered = {}
        for enemy_id, info in sightings.items():
            if not isinstance(info, dict):
                continue
            last_turn = info.get("turn")
            if max_age is not None and current_turn and last_turn is not None:
                if (current_turn - last_turn) > max_age:
                    continue
            filtered[enemy_id] = info
        return filtered

    def _decay_enemy_memory(self, max_age: int = 6) -> None:
        if not getattr(self, "ai_enemy_memory", None):
            return

        current_turn = getattr(self, "turn", 0)
        to_remove = []
        for commander_key, sightings in list(self.ai_enemy_memory.items()):
            if not isinstance(sightings, dict):
                to_remove.append(commander_key)
                continue

            for enemy_id in list(sightings.keys()):
                info = sightings.get(enemy_id, {})
                if not isinstance(info, dict):
                    del sightings[enemy_id]
                    continue
                last_turn = info.get("turn")
                if max_age is not None and current_turn and last_turn is not None:
                    if (current_turn - last_turn) > max_age:
                        del sightings[enemy_id]

            if not sightings:
                to_remove.append(commander_key)

        for commander_key in to_remove:
            self.ai_enemy_memory.pop(commander_key, None)

    def get_visible_tokens(self, player):
        """Zwraca listę żetonów widocznych dla danego gracza (elastyczne filtrowanie)."""
        visible = []
        player_role = getattr(player, 'role', '').strip().lower()
        player_nation_orig = getattr(player, 'nation', '').strip()
        player_nation = player_nation_orig.lower()
        player_id = getattr(player, 'id', None)
        for token in self.tokens:
            token_nation = str(token.stats.get('nation', '')).strip().lower()
            token_owner = str(token.owner).strip()
            # 1. Mgła wojny i pole 'visible_for' (jeśli istnieje)
            if 'visible_for' in token.stats:
                if player_id in token.stats['visible_for']:
                    visible.append(token)
                    continue
            # 2. Generał widzi wszystkie żetony swojej nacji
            if player_role == 'generał' and token_nation == player_nation:
                visible.append(token)
            # 3. Dowódca widzi tylko swoje żetony
            elif player_role == 'dowódca' and token_owner == f"{player_id} ({player_nation_orig})":
                visible.append(token)
        return visible

    def _process_key_points(self, players):
        """Przetwarza punkty kluczowe: rozdziela punkty ekonomiczne, aktualizuje stan punktów, usuwa wyzerowane."""
        # Mapowanie nacji -> generał
        generals = {p.nation: p for p in players if getattr(p, 'role', '').lower() == 'generał'}
        tokens_by_pos = {(t.q, t.r): t for t in self.tokens}
        to_remove = []
        for hex_id, kp in self.key_points_state.items():
            q, r = map(int, hex_id.split(","))
            token = tokens_by_pos.get((q, r))
            if token and hasattr(token, 'owner') and token.owner:
                # Wyciągnij nację z ownera (np. "2 (Polska)")
                nation = token.owner.split("(")[-1].replace(")", "").strip()
                general = generals.get(nation)
                if general and hasattr(general, 'economy'):
                    give = int(0.1 * kp['initial_value'])
                    if give < 1:
                        give = 1  # Minimalnie 1 punkt
                    if kp['current_value'] <= 0:
                        continue
                    if give > kp['current_value']:
                        give = kp['current_value']
                    general.economy.economic_points += give
                    kp['current_value'] -= give
                    if kp['current_value'] <= 0:
                        to_remove.append(hex_id)
        # Usuń wyzerowane punkty z key_points_state i z planszy
        for hex_id in to_remove:
            self.key_points_state.pop(hex_id, None)
            if hasattr(self.board, 'key_points'):
                self.board.key_points.pop(hex_id, None)        # (Opcjonalnie) zapisz do pliku mapy aktualny stan key_points
        self._save_key_points_to_map()

    def _save_key_points_to_map(self):
        """Zapisuje aktualny stan key_points do pliku mapy (data/map_data.json)."""
        if getattr(self, 'read_only', False):
            return
        try:
            map_path = self.board.__dict__.get('json_path', 'data/map_data.json')
            with open(map_path, encoding='utf-8') as f:
                data = json.load(f)
            # Aktualizuj key_points
            data['key_points'] = {k: {'type': v['type'], 'value': v['current_value']} for k, v in self.key_points_state.items()}
            with open(map_path, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2, ensure_ascii=False)
        except Exception as e:
            pass

    def log_key_points_status(self, current_player):
        """Loguje stan key pointów na początku tury gracza."""
        if not hasattr(self, 'key_points_state') or not self.key_points_state:
            return
            
        print(f"\n📍 KEY POINTS STATUS - TURA: {current_player.nation} {current_player.role} (ID: {current_player.id})")
        print("=" * 80)
        
        tokens_by_pos = {(t.q, t.r): t for t in self.tokens}
        occupied_by_player = []
        occupied_by_others = []
        unoccupied = []
        
        for hex_id, kp in self.key_points_state.items():
            try:
                q, r = map(int, hex_id.split(","))
                token = tokens_by_pos.get((q, r))
                
                kp_info = f"📍 {hex_id}: wartość {kp['current_value']}/{kp['initial_value']} (typ: {kp.get('type', 'unknown')})"
                
                if token and hasattr(token, 'owner') and token.owner:
                    owner_nation = token.owner.split("(")[-1].replace(")", "").strip()
                    owner_id = token.owner.split("(")[0].strip()
                    
                    if owner_nation == current_player.nation:
                        occupied_by_player.append(f"  ✅ {kp_info} - okupowany przez {owner_id} ({owner_nation})")
                    else:
                        occupied_by_others.append(f"  ❌ {kp_info} - okupowany przez {owner_id} ({owner_nation})")
                else:
                    unoccupied.append(f"  🔓 {kp_info} - WOLNY")
            except (ValueError, IndexError) as e:
                print(f"  ⚠️ Błąd parsowania hex_id '{hex_id}': {e}")
        
        # Wyświetl grupami
        if occupied_by_player:
            print("🏆 TWOJE KEY POINTS:")
            for line in occupied_by_player:
                print(line)
        
        if occupied_by_others:
            print("\n🚫 KEY POINTS PRZECIWNIKÓW:")
            for line in occupied_by_others:
                print(line)
        
        if unoccupied:
            print("\n🔓 WOLNE KEY POINTS:")
            for line in unoccupied:
                print(line)
        
        print("=" * 80)

    def _is_supply_unit(self, token):
        """Sprawdza czy jednostka jest typu zaopatrzenie (Z) i może zbierać PE."""
        if not token or not hasattr(token, 'stats'):
            return False
            
        unit_type = token.stats.get('unitType', '')
        return unit_type == 'Z'

    def _get_unit_type_display(self, token):
        """Zwraca czytelny typ jednostki do logowania."""
        if not token or not hasattr(token, 'stats'):
            return 'UNKNOWN'
            
        unit_type = token.stats.get('unitType', 'UNKNOWN')
        type_names = {
            'P': 'Piechota', 'TL': 'Czołg lekki', 'TS': 'Sam. pancerny',
            'K': 'Kawaleria', 'AL': 'Art. lekka', 'AC': 'Art. ciężka', 
            'AP': 'Art. plot', 'Z': 'Zaopatrzenie', 'D': 'Dowództwo', 'G': 'Generał'
        }
        return f"{type_names.get(unit_type, unit_type)} ({unit_type})"

    def process_key_points(self, players):
        """Przetwarza punkty kluczowe: rozdziela punkty ekonomiczne, aktualizuje stan punktów, usuwa wyzerowane."""
        print(f"\n💰 PROCESSING KEY POINTS - koniec pełnej tury")
        generals = {p.nation: p for p in players if getattr(p, 'role', '').lower() == 'generał'}
        tokens_by_pos = {(t.q, t.r): t for t in self.tokens}
        to_remove = []
        # Debug: zbierz sumy dla każdego generała
        debug_points_per_general = {}
        debug_details_per_general = {}
        
        print("🔍 Sprawdzanie okupacji key pointów...")
        for hex_id, kp in self.key_points_state.items():
            q, r = map(int, hex_id.split(","))
            token = tokens_by_pos.get((q, r))
            if token and hasattr(token, 'owner') and token.owner:
                # NOWE: Sprawdź czy to jednostka zaopatrzenia
                if not self._is_supply_unit(token):
                    unit_type_display = self._get_unit_type_display(token)
                    print(f"  ⚠️ {hex_id}: {unit_type_display} nie może zbierać PE - tylko Zaopatrzenie (Z)")
                    continue
                    
                nation = token.owner.split("(")[-1].replace(")", "").strip()
                owner_id = token.owner.split("(")[0].strip()
                general = generals.get(nation)
                if general and hasattr(general, 'economy'):
                    give = int(0.1 * kp['initial_value'])
                    if give < 1:
                        give = 1  # Minimalnie 1 punkt
                    if kp['current_value'] <= 0:
                        print(f"  ⚠️ {hex_id}: WYCZERPANY - okupowany przez {owner_id} ({nation})")
                        continue
                    if give > kp['current_value']:
                        give = kp['current_value']
                    
                    kp_value_before = kp['current_value']
                    old_economy = general.economy.economic_points
                    general.economy.economic_points += give
                    kp['current_value'] -= give
                    
                    print(f"  💰 {hex_id}: +{give} punktów dla generała {nation} (okupant: {owner_id} - Zaopatrzenie)")
                    print(f"      👤 Okupant: {owner_id} ({nation}) - jednostka Zaopatrzenia (Z)")
                    print(f"      💵 Ekonomia generała: {old_economy} → {general.economy.economic_points}")
                    print(f"      📍 Key Point: {kp['current_value']}/{kp['initial_value']} pozostało")

                    try:
                        log_token(
                            f"{getattr(token, 'id', 'unknown')}: przydział PE z KP {hex_id}",
                            "INFO",
                            token_owner=token.owner,
                            token_type=self._get_unit_type_display(token),
                            key_point=hex_id,
                            pe_gain=give,
                            kp_value_before=kp_value_before,
                            kp_value_after=kp['current_value'],
                            general_id=getattr(general, 'id', None),
                            general_nation=nation,
                            general_economy_before=old_economy,
                            general_economy_after=general.economy.economic_points,
                        )
                    except Exception:
                        pass
                    
                    # Debug: zapisz szczegóły
                    debug_points_per_general.setdefault(general, 0)
                    debug_points_per_general[general] += give
                    debug_details_per_general.setdefault(general, []).append((hex_id, give, kp['current_value']))
                    if kp['current_value'] <= 0:
                        to_remove.append(hex_id)
                        print(f"      🚫 Key Point {hex_id} zostanie usunięty (wyczerpany)")
                else:
                    print(f"  ❌ {hex_id}: okupowany przez {owner_id} ({nation}) - BRAK GENERAŁA")
            else:
                print(f"  🔓 {hex_id}: WOLNY ({kp['current_value']}/{kp['initial_value']})")
        
        print(f"\n📊 PODSUMOWANIE PRZYZNANYCH PUNKTÓW:")
        if debug_points_per_general:
            for general, total_points in debug_points_per_general.items():
                print(f"  🏆 {general.nation} Generał: +{total_points} punktów ekonomicznych")
        else:
            print("  🚫 Brak przyznanych punktów (żadne key pointy nie są okupowane)")
            
        # Usuń wyzerowane punkty z key_points_state i z planszy
        if to_remove:
            print(f"\n🗑️ Usuwanie wyczerpanych key pointów: {to_remove}")
        for hex_id in to_remove:
            self.key_points_state.pop(hex_id, None)
            if hasattr(self.board, 'key_points'):
                self.board.key_points.pop(hex_id, None)
        self._save_key_points_to_map()
        # Zwróć informacje o przyznanych punktach
        return debug_points_per_general

    def update_all_players_visibility(self, players):
        """Aktualizuje widoczność dla wszystkich graczy."""
        update_all_players_visibility(players, self.tokens, self.board)

def get_token_vision_hexes(token, board):
    """
    Zwraca zbiór (q, r) heksów w zasięgu widzenia żetonu na podstawie pola 'sight'.
    Używa dystansu heksagonalnego (axial/cube).
    """
    if token.q is None or token.r is None:
        return set()
    vision_range = token.stats.get('sight', 0)
    visible = set()
    for dq in range(-vision_range, vision_range + 1):
        for dr in range(-vision_range, vision_range + 1):
            q = token.q + dq
            r = token.r + dr
            if board.hex_distance((token.q, token.r), (q, r)) <= vision_range:
                if board.get_tile(q, r) is not None:
                    visible.add((q, r))
    return visible

def update_player_visibility(player, all_tokens, board):
    """
    Aktualizuje widoczność gracza: zbiera wszystkie heksy w zasięgu widzenia jego żetonów
    oraz żetony znajdujące się na tych heksach. Uwzględnia tymczasową widoczność (temp_visible_hexes, temp_visible_tokens).
    """
    visible_hexes = set()
    # Dowódca: tylko własne żetony; Generał: sumuje widoczność dowódców swojej nacji
    if player.role.lower() == 'dowódca':
        own_tokens = [t for t in all_tokens if t.owner == f"{player.id} ({player.nation})"]
    elif player.role.lower() == 'generał':
        own_tokens = [t for t in all_tokens if t.owner.endswith(f"({player.nation})")]
    else:
        own_tokens = []
    for token in own_tokens:
        visible_hexes |= get_token_vision_hexes(token, board)
    # Dodaj tymczasową widoczność
    if hasattr(player, 'temp_visible_hexes'):
        visible_hexes |= player.temp_visible_hexes
    player.visible_hexes = visible_hexes
    # Zbierz żetony widoczne na tych heksach
    visible_tokens = set()
    for t in all_tokens:
        if (t.q, t.r) in visible_hexes:
            visible_tokens.add(t.id)
    # Dodaj tymczasowo widoczne żetony
    if hasattr(player, 'temp_visible_tokens'):
        visible_tokens |= player.temp_visible_tokens
    player.visible_tokens = visible_tokens
    
    # NOWE: Dodaj detection data dla graduowanej widoczności
    if hasattr(player, 'temp_visible_token_data'):
        if not hasattr(player, 'visible_token_data'):
            player.visible_token_data = {}
        player.visible_token_data.update(player.temp_visible_token_data)

def update_general_visibility(general, all_players, all_tokens):
    """
    Generał widzi WSZYSTKIE żetony swojej nacji (niezależnie od dowódcy) oraz WSZYSTKIE żetony przeciwnika, które są na heksach widocznych przez jego dowódców.
    """
    nation = general.nation
    dowodcy = [p for p in all_players if p.role.lower() == 'dowódca' and p.nation == nation]
    all_hexes = set()
    for d in dowodcy:
        all_hexes |= getattr(d, 'visible_hexes', set())
    general.visible_hexes = all_hexes
    # Generał widzi wszystkie żetony swojej nacji
    own_tokens = {t.id for t in all_tokens if t.owner.endswith(f"({nation})")}
    # Oraz wszystkie żetony przeciwnika, które są na widocznych heksach
    enemy_tokens = {t.id for t in all_tokens if t.owner and not t.owner.endswith(f"({nation})") and (t.q, t.r) in all_hexes}
    general.visible_tokens = own_tokens | enemy_tokens

def update_all_players_visibility(players, all_tokens, board):
    for player in players:
        update_player_visibility(player, all_tokens, board)
    # Dodatkowa aktualizacja dla generałów (po wszystkich dowódcach!)
    for player in players:
        if player.role.lower() == 'generał':
            update_general_visibility(player, players, all_tokens)

def clear_temp_visibility(players):
    for p in players:
        if hasattr(p, 'temp_visible_hexes'):
            p.temp_visible_hexes.clear()
        if hasattr(p, 'temp_visible_tokens'):
            p.temp_visible_tokens.clear()
        # NOWE: Wyczyść detection data
        if hasattr(p, 'temp_visible_token_data'):
            p.temp_visible_token_data.clear()

# Przykład użycia:
# engine = GameEngine('data/map_data.json', 'data/tokens_index.json', 'data/start_tokens.json', seed=123)
# state = engine.get_state()
