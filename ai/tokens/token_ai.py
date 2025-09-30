"""
Minimalna logika AI dla pojedynczego żetonu.

Ten wariant nie korzysta z pamięci ani rezerwacji – każdy żeton
reaguje jedynie na aktualny stan pola bitwy i zużywa przydzielony
budżet PE na podstawowe uzupełnienia.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Dict, List, Optional, Tuple

from ai.logs import log_token
from engine.action_refactored_clean import CombatAction, MoveAction


@dataclass
class MoveOutcome:
    success: bool
    message: Optional[str] = None


class TokenAI:
    """Uproszczone AI pojedynczego żetonu."""

    def __init__(self, token):
        self.token = token

    def execute_turn(self, engine, player, pe_budget: int = 0) -> int:
        """Wykonuje turę żetonu w trybie minimalnym.

        Zwraca liczbę punktów ekonomicznych faktycznie wykorzystanych
        na uzupełnienia paliwa i wartości bojowej.
        """

        log_token(
            f"{self.token.id}: start tury (budżet PE={pe_budget})",
            "INFO",
            allocated_pe=pe_budget,
            position_q=getattr(self.token, "q", None),
            position_r=getattr(self.token, "r", None),
            move_points=getattr(self.token, "currentMovePoints", None),
            fuel=getattr(self.token, "currentFuel", None),
            combat_value=getattr(self.token, "combat_value", None),
        )
        spent_pe = 0
        allocated_pe = pe_budget
        movement_report = {"success": False, "attempts": 0, "destination": None}
        attack_report: Optional[Dict[str, Optional[int]]] = None

        if self._can_move():
            movement_report = self._perform_movement(engine, player)

        enemy = self._select_attack_target(engine)
        if enemy:
            attack_report = self._perform_attack(engine, player, enemy)

        resupply_budget = max(0, allocated_pe - spent_pe)
        token_destroyed = self._is_destroyed_after_attack(engine, attack_report)

        if token_destroyed and resupply_budget > 0:
            resupply_report = {
                "budget": resupply_budget,
                "spent": 0,
                "fuel_added": 0,
                "cv_added": 0,
            }
            log_token(
                f"{self.token.id}: pominięto uzupełnienia (żeton zniszczony)",
                "DEBUG",
                resupply_budget=resupply_budget,
            )
        else:
            resupply_report = self._perform_resupply(resupply_budget)

        spent_pe += resupply_report["spent"]
        unused_pe = max(0, allocated_pe - spent_pe)

        log_token(
            f"{self.token.id}: koniec tury (wydane PE={spent_pe})",
            "INFO",
            allocated_pe=allocated_pe,
            spent_pe=spent_pe,
            unused_pe=unused_pe,
            movement_success=movement_report["success"],
            movement_attempts=movement_report["attempts"],
            movement_destination=movement_report["destination"],
            attack_attempted=bool(attack_report),
            attack_success=attack_report.get("success") if attack_report else False,
            counterattack=attack_report.get("counterattack") if attack_report else None,
            damage_dealt=attack_report.get("damage_dealt") if attack_report else None,
            damage_taken=attack_report.get("damage_taken") if attack_report else None,
            attacker_remaining=attack_report.get("attacker_remaining") if attack_report else None,
            defender_remaining=attack_report.get("defender_remaining") if attack_report else None,
            resupply_budget=resupply_budget,
            resupply_spent=resupply_report["spent"],
            refueled=resupply_report["fuel_added"],
            combat_restored=resupply_report["cv_added"],
            remaining_mp=getattr(self.token, "currentMovePoints", None),
            remaining_fuel=getattr(self.token, "currentFuel", None),
            combat_value=getattr(self.token, "combat_value", None),
            token_destroyed=token_destroyed,
        )
        return spent_pe

    # ------------------------------------------------------------------
    # Ruch
    # ------------------------------------------------------------------
    def _perform_movement(self, engine, player) -> Dict[str, Optional[object]]:
        attempts = 0
        for destination in self._candidate_moves(engine):
            attempts += 1
            outcome = self._attempt_move(engine, player, destination)
            if outcome.success:
                return {
                    "success": True,
                    "attempts": attempts,
                    "destination": destination,
                }
            log_token(
                f"{self.token.id}: nieudany ruch na {destination}",
                "WARNING",
                reason=outcome.message or "unknown",
                attempt=attempts,
            )
        log_token(
            f"{self.token.id}: brak możliwego ruchu",
            "DEBUG",
            attempts=attempts,
        )
        return {
            "success": False,
            "attempts": attempts,
            "destination": None,
        }

    def _candidate_moves(self, engine) -> List[Tuple[int, int]]:
        board = getattr(engine, "board", None)
        if board is None:
            return []
        my_pos = (self.token.q, self.token.r)
        if None in my_pos:
            return []

        visible_enemies = self._visible_enemies(engine)
        if visible_enemies:
            target = min(
                visible_enemies,
                key=lambda enemy: board.hex_distance(my_pos, (enemy.q, enemy.r)),
            )
            return self._neighbors_towards(engine, my_pos, (target.q, target.r))

        return self._patrol_neighbors(engine, my_pos)

    def _neighbors_towards(
        self, engine, start: Tuple[int, int], goal: Tuple[int, int]
    ) -> List[Tuple[int, int]]:
        board = engine.board
        options = []
        for neighbor in board.neighbors(*start):
            if not self._is_passable(engine, neighbor):
                continue
            distance = board.hex_distance(neighbor, goal)
            options.append((distance, neighbor))
        options.sort(key=lambda item: item[0])
        return [pos for _, pos in options]

    def _patrol_neighbors(self, engine, start: Tuple[int, int]) -> List[Tuple[int, int]]:
        board = engine.board
        options = []
        for neighbor in board.neighbors(*start):
            if not self._is_passable(engine, neighbor):
                continue
            tile = board.get_tile(*neighbor)
            move_mod = getattr(tile, "move_mod", 0) if tile else 0
            options.append((move_mod, neighbor))
        options.sort(key=lambda item: item[0])
        return [pos for _, pos in options]

    def _attempt_move(self, engine, player, destination: Tuple[int, int]) -> MoveOutcome:
        if destination == (self.token.q, self.token.r):
            return MoveOutcome(False, "already_there")

        action = MoveAction(self.token.id, destination[0], destination[1])
        result = engine.execute_action(action, player=player)

        if isinstance(result, tuple):
            success = bool(result[0])
            message = result[1] if len(result) > 1 else None
        else:
            success = bool(getattr(result, "success", False))
            message = getattr(result, "message", None)

        if success:
            log_token(
                f"{self.token.id}: ruch na {destination} udany",
                "INFO",
                destination_q=destination[0],
                destination_r=destination[1],
                remaining_mp=getattr(self.token, "currentMovePoints", None),
                remaining_fuel=getattr(self.token, "currentFuel", None),
            )
        return MoveOutcome(success, message)

    # ------------------------------------------------------------------
    # Walka
    # ------------------------------------------------------------------
    def _select_attack_target(self, engine):
        board = getattr(engine, "board", None)
        if board is None:
            return None

        attack_range = self._attack_range()
        my_pos = (self.token.q, self.token.r)
        targets = []
        for enemy in engine.tokens:
            if not self._is_enemy(enemy):
                continue
            if None in (enemy.q, enemy.r):
                continue
            distance = board.hex_distance(my_pos, (enemy.q, enemy.r))
            if distance <= attack_range:
                targets.append((distance, enemy))
        if not targets:
            return None
        targets.sort(key=lambda item: item[0])
        return targets[0][1]

    def _perform_attack(self, engine, player, enemy) -> Dict[str, Optional[int]]:
        board = getattr(engine, "board", None)
        distance = None
        if board is not None:
            distance = board.hex_distance((self.token.q, self.token.r), (enemy.q, enemy.r))
        log_token(
            f"{self.token.id}: inicjuje atak na {enemy.id}",
            "DEBUG",
            target_id=enemy.id,
            attack_range=self._attack_range(),
            distance=distance,
        )

        if not self._can_attack(enemy, engine):
            log_token(f"{self.token.id}: cel {enemy.id} poza zasięgiem", "DEBUG")
            return {
                "success": False,
                "message": "target_out_of_range",
                "counterattack": None,
                "damage_dealt": None,
                "damage_taken": None,
            }

        result = engine.execute_action(
            CombatAction(self.token.id, enemy.id),
            player=player,
        )

        data: Dict[str, Any] = {}
        if isinstance(result, tuple):
            success = bool(result[0])
            message = result[1] if len(result) > 1 else None
        else:
            success = bool(getattr(result, "success", False))
            message = getattr(result, "message", None)
            data = getattr(result, "data", {}) or {}

        combat_data = {}
        if isinstance(data, dict):
            combat_data = data.get("combat_result", {}) or {}

        damage_dealt = combat_data.get("attack_result")
        damage_taken = combat_data.get("defense_result")
        counterattack = bool(combat_data.get("can_counterattack")) if combat_data else False
        attacker_remaining = data.get("attacker_remaining") if isinstance(data, dict) else None
        defender_remaining = data.get("defender_remaining") if isinstance(data, dict) else None

        if counterattack and damage_taken:
            log_token(
                f"{self.token.id}: kontratak obrońcy",
                "INFO",
                target_id=enemy.id,
                counterattack_damage=damage_taken,
                attacker_remaining=attacker_remaining,
            )

        log_token(
            f"{self.token.id}: atak na {enemy.id}",
            "INFO" if success else "WARNING",
            result_message=message,
            target_id=enemy.id,
            success=success,
            damage_dealt=damage_dealt,
            damage_taken=damage_taken,
            counterattack=counterattack,
            attacker_remaining=attacker_remaining,
            defender_remaining=defender_remaining,
        )
        return {
            "success": success,
            "message": message,
            "counterattack": counterattack,
            "damage_dealt": damage_dealt,
            "damage_taken": damage_taken,
            "attacker_remaining": attacker_remaining,
            "defender_remaining": defender_remaining,
        }

    # ------------------------------------------------------------------
    # Resupply
    # ------------------------------------------------------------------
    def _perform_resupply(self, available_pe: int) -> Dict[str, int]:
        report = {
            "budget": max(0, available_pe),
            "spent": 0,
            "fuel_added": 0,
            "cv_added": 0,
        }
        if available_pe <= 0:
            return report

        fuel_added = self._refuel(available_pe - report["spent"])
        report["fuel_added"] = fuel_added
        report["spent"] += fuel_added

        cv_added = self._restore_combat_value(available_pe - report["spent"])
        report["cv_added"] = cv_added
        report["spent"] += cv_added
        return report

    def _refuel(self, limit: int) -> int:
        if limit <= 0:
            return 0
        max_fuel = getattr(self.token, "maxFuel", 0)
        if max_fuel <= 0:
            return 0
        current = getattr(self.token, "currentFuel", max_fuel)
        missing = max(0, max_fuel - current)
        to_add = min(missing, limit)
        if to_add <= 0:
            return 0
        self.token.currentFuel = current + to_add
        log_token(
            f"{self.token.id}: uzupełnia paliwo o {to_add}",
            "DEBUG",
            fuel_after=self.token.currentFuel,
        )
        return to_add

    def _restore_combat_value(self, limit: int) -> int:
        if limit <= 0:
            return 0
        max_cv = self.token.stats.get("combat_value", 0)
        if max_cv <= 0:
            return 0
        current = getattr(self.token, "combat_value", max_cv)
        missing = max(0, max_cv - current)
        to_add = min(missing, limit)
        if to_add <= 0:
            return 0
        self.token.combat_value = current + to_add
        log_token(
            f"{self.token.id}: uzupełnia CV o {to_add}",
            "DEBUG",
            combat_after=self.token.combat_value,
        )
        return to_add

    # ------------------------------------------------------------------
    # Pomocnicze
    # ------------------------------------------------------------------
    def _is_destroyed_after_attack(self, engine, attack_report: Optional[Dict[str, Any]]) -> bool:
        if attack_report and attack_report.get("attacker_remaining") is not None:
            if attack_report["attacker_remaining"] <= 0:
                return True
        if hasattr(self.token, "combat_value") and getattr(self.token, "combat_value") is not None:
            if getattr(self.token, "combat_value") <= 0 and not self._is_token_present(engine):
                return True
        return not self._is_token_present(engine)

    def _is_token_present(self, engine) -> bool:
        token_id = getattr(self.token, "id", None)
        for tok in getattr(engine, "tokens", []):
            if getattr(tok, "id", None) == token_id:
                return True
        return False

    def _can_move(self) -> bool:
        return (
            getattr(self.token, "currentMovePoints", 0) > 0
            and getattr(self.token, "currentFuel", 0) > 0
        )

    def _visible_enemies(self, engine) -> List:
        board = getattr(engine, "board", None)
        if board is None:
            return []
        sight = self._sight()
        if sight <= 0:
            return []
        my_pos = (self.token.q, self.token.r)
        enemies = []
        for other in getattr(engine, "tokens", []):
            if not self._is_enemy(other):
                continue
            if None in (other.q, other.r):
                continue
            distance = board.hex_distance(my_pos, (other.q, other.r))
            if distance <= sight:
                enemies.append(other)
        return enemies

    def _is_passable(self, engine, position: Tuple[int, int]) -> bool:
        board = engine.board
        tile = board.get_tile(*position)
        if tile is None or getattr(tile, "move_mod", 0) == -1:
            return False
        return self._token_at(engine, position) is None

    def _token_at(self, engine, position: Tuple[int, int]):
        for tok in getattr(engine, "tokens", []):
            if tok.id == self.token.id:
                continue
            if (tok.q, tok.r) == position:
                return tok
        return None

    def _attack_range(self) -> int:
        attack_stats = self.token.stats.get("attack", {})
        if isinstance(attack_stats, dict):
            return int(attack_stats.get("range", 1))
        return 1

    def _sight(self) -> int:
        sight = self.token.stats.get("sight", 0)
        if isinstance(sight, dict):
            return int(sight.get("value", 0))
        return int(sight or 0)

    def _can_attack(self, enemy, engine) -> bool:
        if not self._is_enemy(enemy):
            return False
        if not self.token.can_attack("normal"):
            return False
        board = getattr(engine, "board", None)
        if board is None:
            return False
        distance = board.hex_distance((self.token.q, self.token.r), (enemy.q, enemy.r))
        return distance <= self._attack_range() and getattr(self.token, "currentMovePoints", 0) > 0

    def _is_enemy(self, other) -> bool:
        if other is None or other is self.token:
            return False
        return self._owner_nation(self.token) != self._owner_nation(other)

    @staticmethod
    def _owner_nation(token) -> Optional[str]:
        owner = getattr(token, "owner", "") or ""
        if "(" in owner and ")" in owner:
            return owner.split("(")[-1].replace(")", "").strip()
        stats_nation = getattr(token, "stats", {}).get("nation")
        if stats_nation:
            return str(stats_nation).strip()
        return None