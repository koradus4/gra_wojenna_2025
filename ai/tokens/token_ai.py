"""
Minimalna logika AI dla pojedynczego żetonu.

Ten wariant nie korzysta z pamięci ani rezerwacji – każdy żeton
reaguje jedynie na aktualny stan pola bitwy i zużywa przydzielony
budżet PE na podstawowe uzupełnienia.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Dict, List, Optional, Set, Tuple

import random

from ai.logs import log_token
from engine.action_refactored_clean import CombatAction, MoveAction, VisionService
from engine.detection_filter import apply_detection_filter, get_detection_info_for_player


@dataclass
class MoveOutcome:
    success: bool
    message: Optional[str] = None


class TokenAI:
    """Uproszczone AI pojedynczego żetonu."""

    STATUS_URGENT_RETREAT = "urgent_retreat"
    STATUS_LOW_FUEL = "low_fuel"
    STATUS_THREATENED = "threatened"
    STATUS_NORMAL = "normal"
    HOLD_RELEASE_TURNS = 2

    ACTION_PROFILES: Dict[str, List[str]] = {
        "retreat": ["refuel_minimum", "withdraw"],
        "recovery": ["refuel_minimum", "restore_cv"],
        "combat": ["refuel_minimum", "restore_cv", "attack", "maneuver"],
        "patrol": ["refuel_minimum", "maneuver"],
    }

    def __init__(self, token, specialist=None):
        self.token = token
        self.memory: Dict[str, Any] = {}
        self.specialist = specialist
        self.shared_intel = None
        self._initialize_specialist()
        self._reset_turn_state()

    def _initialize_specialist(self) -> None:
        """Inicjalizuje specjalistę, jeśli nie został przekazany."""
        if self.specialist is None:
            try:
                from .specialized_ai import build_specialist, get_shared_intel_memory
                self.shared_intel = get_shared_intel_memory()
                self.specialist = build_specialist(self.token, self.shared_intel)
            except ImportError:
                self.specialist = None
        else:
            self.shared_intel = getattr(self.specialist, "shared_intel", None)

    def execute_turn(self, engine, player, pe_budget: int = 0) -> int:
        """Wykonuje turę żetonu w trybie minimalnym.

        Zwraca liczbę punktów ekonomicznych faktycznie wykorzystanych
        na uzupełnienia paliwa i wartości bojowej.
        """

        self._reset_turn_state()
        context = self._evaluate_state(engine, player)
        self._update_hold_state(context)
        base_status = self._classify_status(context)
        status = base_status
        specialist_name = type(self.specialist).__name__ if self.specialist else None
        specialist_notes: List[str] = []
        if self.specialist is not None:
            try:
                self.specialist.on_turn_start(self.memory)
                status = self.specialist.adjust_status(status, context)
                if status != base_status:
                    specialist_notes.append(f"status:{base_status}->{status}")
            except Exception:
                pass
        movement_mode = self._choose_movement_mode(status, context)
        base_mode = movement_mode
        if self.specialist is not None:
            try:
                movement_mode = self.specialist.adjust_movement_mode(movement_mode, status, context)
                if movement_mode != base_mode:
                    specialist_notes.append(f"mode:{base_mode}->{movement_mode}")
            except Exception:
                pass
        planned_actions = self._plan_actions(status, context, pe_budget)
        base_actions = list(planned_actions)
        if self.specialist is not None:
            try:
                planned_actions = self.specialist.adjust_actions(planned_actions, status, context, pe_budget)
                planned_snapshot = list(planned_actions)
                if planned_snapshot != base_actions:
                    specialist_notes.append(
                        "actions:" + "->".join(
                            [
                                ",".join(base_actions) or "-",
                                ",".join(planned_snapshot) or "-",
                            ]
                        )
                    )
                planned_actions = planned_snapshot
            except Exception:
                planned_actions = list(planned_actions)
        else:
            planned_actions = list(planned_actions)
        action_profile = self.memory.get("action_profile")
        specialist_flags = context.get("specialist_flags") or set()
        if isinstance(specialist_flags, set):
            specialist_flags = sorted(specialist_flags)
        else:
            specialist_flags = sorted(set(specialist_flags)) if specialist_flags else []
        shared_detection = context.get("shared_enemy_detection") or {}
        shared_contacts = len(shared_detection)
        flags_text = "|".join(specialist_flags) if specialist_flags else None
        notes_text = "|".join(specialist_notes) if specialist_notes else None
        human_note = context.get("human_note")

        log_token(
            f"{self.token.id}: start tury (budżet PE={pe_budget})",
            "INFO",
            allocated_pe=pe_budget,
            position_q=getattr(self.token, "q", None),
            position_r=getattr(self.token, "r", None),
            move_points=getattr(self.token, "currentMovePoints", None),
            fuel=getattr(self.token, "currentFuel", None),
            combat_value=getattr(self.token, "combat_value", None),
            movement_mode=movement_mode,
            status=status,
            planned_actions=planned_actions,
            action_profile=action_profile,
            specialist=specialist_name,
            human_note=human_note,
            specialist_notes=notes_text,
            specialist_flags=flags_text,
            shared_contacts=shared_contacts,
        )
        spent_pe = 0
        allocated_pe = pe_budget
        movement_report = {
            "success": False,
            "last_success": False,
            "attempts": 0,
            "destination": None,
            "threat_level": 0,
            "entered_danger_zone": False,
            "last_distance": 0,
            "total_distance": 0,
            "last_mp_spent": 0,
            "mp_spent_total": 0,
        }
        attack_report: Optional[Dict[str, Optional[int]]] = None
        attack_retry_after_move = False
        pending_hold_reason: Optional[str] = None

        def attempt_attack() -> bool:
            nonlocal attack_report
            if attack_report:
                return True
            self._update_context(engine, player, context)
            enemy_target = self._select_attack_target(engine, context)
            if enemy_target is None:
                evaluation = {
                    "decision": "hold",
                    "reason": "no_target",
                    "target_id": None,
                    "position": context.get("position"),
                    "hold_reason": "no_target",
                }
                self._record_attack_plan(evaluation, executed=False, attack_report=None, context=context)
                return False

            should_attack = self._should_attack(enemy_target, context)
            evaluation = self.memory.pop("_last_attack_evaluation", None) or {}
            evaluation.setdefault("target_id", getattr(enemy_target, "id", None))
            evaluation.setdefault("position", context.get("position"))
            evaluation.setdefault("enemy_position", (getattr(enemy_target, "q", None), getattr(enemy_target, "r", None)))

            if should_attack:
                attack_report_local = self._perform_attack(engine, player, enemy_target)
                attack_report = attack_report_local
                self.memory["last_target_id"] = getattr(enemy_target, "id", None)
                self._record_attack_plan(evaluation, executed=True, attack_report=attack_report_local, context=context)
                return True

            if pending_hold_reason:
                evaluation.setdefault("hold_reason", pending_hold_reason)
            else:
                evaluation.setdefault("hold_reason", evaluation.get("reason"))
            self._record_attack_plan(evaluation, executed=False, attack_report=None, context=context)
            return False
        resupply_report = {
            "budget": max(0, allocated_pe),
            "spent": 0,
            "reserved": 0,
            "fuel_added": 0,
            "cv_added": 0,
        }

        for action in planned_actions:
            available_pe = max(0, allocated_pe - spent_pe)
            self._update_context(engine, player, context)
            if action == "refuel_minimum" and available_pe > 0:
                phase = self._refuel_minimum(available_pe)
                spent_pe += phase["spent"]
                resupply_report["spent"] += phase["spent"]
                resupply_report["fuel_added"] += phase["fuel_added"]
            elif action == "restore_cv" and available_pe > 0:
                phase = self._restore_cv_to_threshold(available_pe)
                spent_pe += phase["spent"]
                resupply_report["spent"] += phase["spent"]
                resupply_report["cv_added"] += phase["cv_added"]
            elif action in {"withdraw", "maneuver"}:
                if not self._can_move():
                    self._set_hold_position("insufficient_resources")
                    continue
                excluded_candidates: Set[Tuple[int, int]] = set()
                while self._can_move():
                    destination, path = self._select_best_hex(
                        engine,
                        context,
                        retreat=(action == "withdraw"),
                        exclude=excluded_candidates,
                    )
                    if destination is None:
                        self._set_hold_position("no_path_available")
                        break
                    if not path:
                        path = [destination]
                    final_destination = path[-1]
                    first_step_failed = False
                    for step_index, step in enumerate(list(path)):
                        if not self._can_move():
                            current_mp = getattr(self.token, "currentMovePoints", 0) or 0
                            if current_mp <= 0:
                                self._set_hold_position("no_move_points")
                                break
                            available_pe = max(0, allocated_pe - spent_pe)
                            midturn = self._midturn_refuel_if_possible(available_pe)
                            if midturn.get("fuel_added", 0) > 0:
                                spent_pe += midturn.get("spent", 0)
                                resupply_report["spent"] += midturn.get("spent", 0)
                                resupply_report["fuel_added"] += midturn.get("fuel_added", 0)
                            if not self._can_move():
                                self._set_hold_position("insufficient_resources")
                                break
                        outcome = self._attempt_move(engine, player, step)
                        movement_report["attempts"] += 1
                        movement_report["last_success"] = bool(getattr(outcome, "success", False))
                        movement_report["success"] = movement_report["success"] or movement_report["last_success"]
                        movement_report["destination"] = final_destination
                        movement_report["threat_level"] = getattr(outcome, "threat_level", 0)
                        movement_report["entered_danger_zone"] = getattr(outcome, "entered_danger_zone", False)
                        distance = getattr(outcome, "distance", 0) or 0
                        mp_spent = getattr(outcome, "mp_spent", 0) or 0
                        if movement_report["last_success"]:
                            movement_report["last_distance"] = distance
                            movement_report["total_distance"] += distance
                            movement_report["last_mp_spent"] = mp_spent
                            movement_report["mp_spent_total"] += mp_spent
                            self.memory["last_destination"] = step
                            failed_steps = self.memory.setdefault("failed_hexes", set())
                            if step in failed_steps:
                                failed_steps.discard(step)
                                log_token(
                                    f"{self.token.id}: reset failed_hex po udanym ruchu",
                                    "DEBUG",
                                    cleared_q=step[0],
                                    cleared_r=step[1],
                                    remaining_failed=len(failed_steps),
                                )
                            if movement_report["entered_danger_zone"]:
                                self._set_hold_position("danger_zone_entry")
                            path.pop(0)
                        else:
                            movement_report["last_distance"] = 0
                            movement_report["last_mp_spent"] = 0
                            failed = self.memory.setdefault("failed_hexes", set())
                            failed.add(step)
                            if step_index == 0:
                                excluded_candidates.add(destination)
                                first_step_failed = True
                            break
                    if first_step_failed:
                        log_token(
                            f"{self.token.id}: alternatywny cel po nieudanym pierwszym kroku",
                            "DEBUG",
                            failed_destination=destination,
                            excluded=len(excluded_candidates),
                            movement_mode=getattr(self.token, "movement_mode", None),
                            action=action,
                        )
                        continue
                    break
                if attack_retry_after_move and attack_report is None:
                    if attempt_attack():
                        pending_hold_reason = None
                    else:
                        if pending_hold_reason:
                            self._set_hold_position(pending_hold_reason)
                            pending_hold_reason = None
                    attack_retry_after_move = False
            elif action == "attack":
                if attempt_attack():
                    pending_hold_reason = None
                    attack_retry_after_move = False
                else:
                    pending_hold_reason = "attack_not_viable"
                    attack_retry_after_move = True

        if attack_retry_after_move and attack_report is None:
            if attempt_attack():
                pending_hold_reason = None
            elif pending_hold_reason:
                self._set_hold_position(pending_hold_reason)
                pending_hold_reason = None
        elif pending_hold_reason and attack_report is None and not self.memory.get("hold_position"):
            self._set_hold_position(pending_hold_reason)
            pending_hold_reason = None

        resupply_budget = max(0, allocated_pe - spent_pe)
        token_destroyed = self._is_destroyed_after_attack(engine, attack_report)

        if not token_destroyed and resupply_budget > 0:
            supplemental = self._perform_resupply(resupply_budget)
            spent_pe += supplemental["spent"]
            resupply_report["spent"] += supplemental["spent"]
            resupply_report["fuel_added"] += supplemental["fuel_added"]
            resupply_report["cv_added"] += supplemental["cv_added"]
            resupply_report["reserved"] += supplemental.get("reserved", 0)
        elif token_destroyed and resupply_budget > 0:
            log_token(
                f"{self.token.id}: pominięto uzupełnienia (żeton zniszczony)",
                "DEBUG",
                resupply_budget=resupply_budget,
            )

        unused_pe = max(0, allocated_pe - spent_pe)
        resupply_report["reserved"] += unused_pe

        if self.specialist is not None:
            try:
                self.specialist.update_context(context)
                turn_reports = {
                    "movement": movement_report,
                    "attack": attack_report,
                    "resupply": resupply_report,
                }
                self.specialist.after_turn(context, turn_reports)
            except Exception:
                pass

        final_flags = context.get("specialist_flags") or set()
        if isinstance(final_flags, set):
            final_flags = sorted(final_flags)
        else:
            final_flags = sorted(set(final_flags)) if final_flags else []
        final_shared_contacts = len((context.get("shared_enemy_detection") or {}))
        final_flags_text = "|".join(final_flags) if final_flags else None

        log_token(
            f"{self.token.id}: koniec tury (wydane PE={spent_pe})",
            "INFO",
            allocated_pe=allocated_pe,
            spent_pe=spent_pe,
            unused_pe=unused_pe,
            movement_success=movement_report["success"],
            movement_attempts=movement_report["attempts"],
            movement_destination=movement_report["destination"],
            movement_last_success=movement_report["last_success"],
            movement_last_distance=movement_report["last_distance"],
            movement_distance_total=movement_report["total_distance"],
            movement_mp_spent=movement_report["mp_spent_total"],
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
            reserved_pe=resupply_report.get("reserved", 0),
            remaining_mp=getattr(self.token, "currentMovePoints", None),
            remaining_fuel=getattr(self.token, "currentFuel", None),
            combat_value=getattr(self.token, "combat_value", None),
            movement_mode=getattr(self.token, "movement_mode", movement_mode),
            token_destroyed=token_destroyed,
            status=status,
            hold_position=self.memory.get("hold_position", False),
            hold_reason=self.memory.get("hold_reason"),
            specialist=specialist_name,
            specialist_flags=final_flags_text,
            shared_contacts=final_shared_contacts,
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
                    "threat_level": getattr(outcome, "threat_level", 0),
                    "entered_danger_zone": getattr(outcome, "entered_danger_zone", False),
                    "movement_mode": getattr(self.token, "movement_mode", None),
                }
            log_token(
                f"{self.token.id}: nieudany ruch na {destination}",
                "WARNING",
                reason=outcome.message or "unknown",
                attempt=attempts,
                movement_mode=getattr(self.token, "movement_mode", None),
            )
        log_token(
            f"{self.token.id}: brak możliwego ruchu",
            "DEBUG",
            attempts=attempts,
            movement_mode=getattr(self.token, "movement_mode", None),
        )
        return {
            "success": False,
            "attempts": attempts,
            "destination": None,
            "threat_level": 0,
            "entered_danger_zone": False,
            "movement_mode": getattr(self.token, "movement_mode", None),
        }

    def _candidate_moves(self, engine) -> List[Tuple[int, int]]:
        context = getattr(self, "context", {}) or {}
        board = context.get("board") or getattr(engine, "board", None)
        if board is None:
            return []
        my_pos = context.get("position") or (self.token.q, self.token.r)
        if None in my_pos:
            return []

        # Pytamy specjalistę o sugerowany cel (np. KP dla konwoju)
        specialist_target = None
        if self.specialist is not None:
            try:
                specialist_target = self.specialist.suggest_movement_target(context)
            except Exception:
                pass
        
        if specialist_target is not None:
            return self._neighbors_towards(engine, my_pos, specialist_target)

        detection_map = context.get("enemy_detection")
        visible_enemies = context.get("visible_enemies")
        if visible_enemies is None:
            visible_enemies = self._visible_enemies(engine, detection_map)

        tracked_enemies = [enemy for enemy in (visible_enemies or []) if None not in (enemy.q, enemy.r)]
        if tracked_enemies:
            try:
                target = min(
                    tracked_enemies,
                    key=lambda enemy: board.hex_distance(my_pos, (enemy.q, enemy.r)),
                )
            except AttributeError:
                target = None
            if target is not None:
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

        start_position = (self.token.q, self.token.r)
        prev_mp = getattr(self.token, "currentMovePoints", 0) or 0
        action = MoveAction(self.token.id, destination[0], destination[1])
        result = engine.execute_action(action, player=player)

        if isinstance(result, tuple):
            success = bool(result[0])
            message = result[1] if len(result) > 1 else None
            data = result[2] if len(result) > 2 else {}
        else:
            success = bool(getattr(result, "success", False))
            message = getattr(result, "message", None)
            data = getattr(result, "data", {}) if hasattr(result, "data") else {}

        current_position = (self.token.q, self.token.r)
        board = getattr(engine, "board", None)
        distance = 0
        if success:
            distance = self._hex_distance(start_position, current_position, board)
        mp_spent = 0
        current_mp = getattr(self.token, "currentMovePoints", 0)
        if current_mp is not None:
            mp_spent = max(0, prev_mp - (current_mp or 0))

        if success:
            log_token(
                f"{self.token.id}: ruch na {destination} udany",
                "INFO",
                destination_q=destination[0],
                destination_r=destination[1],
                remaining_mp=getattr(self.token, "currentMovePoints", None),
                remaining_fuel=getattr(self.token, "currentFuel", None),
                movement_step_distance=distance,
                mp_spent=mp_spent,
                movement_mode=getattr(self.token, "movement_mode", None),
            )
        threat_level = self._estimate_threat_level(engine, destination)
        entered_danger = threat_level > 0 and self._is_in_danger_zone(destination)
        outcome = MoveOutcome(success, message)
        setattr(outcome, "threat_level", threat_level)
        setattr(outcome, "entered_danger_zone", entered_danger)
        setattr(outcome, "distance", distance)
        setattr(outcome, "mp_spent", mp_spent)
        return outcome

    # ------------------------------------------------------------------
    # Walka
    # ------------------------------------------------------------------
    def _select_attack_target(self, engine, context: Dict[str, Any]):
        detection_map = dict(context.get("enemy_detection", {}) or {})
        visible_enemies = list(context.get("visible_enemies") or self._visible_enemies(engine, detection_map) or [])
        if (not visible_enemies) and engine is not None:
            shared_detection = context.get("shared_enemy_detection") or {}
            if shared_detection:
                for enemy in getattr(engine, "tokens", []):
                    enemy_id = getattr(enemy, "id", None)
                    if enemy_id and enemy_id in shared_detection and self._is_enemy(enemy):
                        detection_map.setdefault(enemy_id, shared_detection[enemy_id])
                        visible_enemies.append(enemy)
        if not visible_enemies:
            return None

        board = context.get("board") or getattr(engine, "board", None)
        my_pos = context.get("position") or (self.token.q, self.token.r)
        attack_range = self._attack_range()

        def _sort_key(enemy) -> Tuple[float, float]:
            info = detection_map.get(getattr(enemy, "id", None), {}) or {}
            detection_level = (info.get("detection_level") or 0.0)
            distance = info.get("distance")
            if distance is None and board is not None and None not in (*my_pos, enemy.q, enemy.r):
                try:
                    distance = board.hex_distance(my_pos, (enemy.q, enemy.r))
                except AttributeError:
                    distance = None
            if distance is None:
                distance = 999.0
            return (-detection_level, float(distance))

        ordered = sorted(visible_enemies, key=_sort_key)
        for enemy in ordered:
            if None in (enemy.q, enemy.r):
                continue
            if board is not None:
                try:
                    distance = board.hex_distance(my_pos, (enemy.q, enemy.r))
                except AttributeError:
                    distance = None
            else:
                distance = None
            if distance is not None and distance > attack_range:
                continue
            if self._can_attack(enemy, engine):
                return enemy
        return None

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
            movement_mode=getattr(self.token, "movement_mode", None),
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
            movement_mode=getattr(self.token, "movement_mode", None),
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
            "reserved": 0,
            "fuel_added": 0,
            "cv_added": 0,
        }
        if available_pe <= 0:
            return report

        fuel_phase = self._refuel_minimum(available_pe)
        report["spent"] += fuel_phase["spent"]
        report["fuel_added"] += fuel_phase["fuel_added"]

        remaining = max(0, available_pe - report["spent"])
        cv_phase = self._restore_cv_to_threshold(remaining)
        report["spent"] += cv_phase["spent"]
        report["cv_added"] += cv_phase["cv_added"]

        remaining = max(0, available_pe - report["spent"])
        if remaining > 0:
            fuel_top_off = self._refuel(remaining)
            report["spent"] += fuel_top_off
            report["fuel_added"] += fuel_top_off
            remaining = max(0, available_pe - report["spent"])

        if remaining > 0:
            top_off = self._restore_combat_value(remaining)
            report["spent"] += top_off
            report["cv_added"] += top_off
            remaining = max(0, available_pe - report["spent"])

        report["reserved"] = remaining
        return report

    def _midturn_refuel_if_possible(self, available_pe: int) -> Dict[str, int]:
        report = {"spent": 0, "fuel_added": 0}
        if available_pe <= 0:
            return report

        current_fuel = getattr(self.token, "currentFuel", 0) or 0
        if current_fuel > 0:
            return report

        phase = self._refuel_minimum(available_pe)
        report["spent"] += phase.get("spent", 0)
        report["fuel_added"] += phase.get("fuel_added", 0)

        remaining = max(0, available_pe - report["spent"])
        if getattr(self.token, "currentFuel", 0) <= 0 and remaining > 0:
            added = self._refuel(remaining)
            report["spent"] += added
            report["fuel_added"] += added

        if report["fuel_added"] > 0:
            log_token(
                f"{self.token.id}: dotankowanie w trakcie ruchu o {report['fuel_added']}",
                "INFO",
                spent_pe=report["spent"],
                remaining_pe=max(0, available_pe - report["spent"]),
                remaining_mp=getattr(self.token, "currentMovePoints", None),
                movement_mode=getattr(self.token, "movement_mode", None),
            )
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
            movement_mode=getattr(self.token, "movement_mode", None),
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
            movement_mode=getattr(self.token, "movement_mode", None),
        )
        return to_add

    def _refuel_minimum(self, available_pe: int) -> Dict[str, int]:
        report = {"spent": 0, "fuel_added": 0}
        if available_pe <= 0:
            return report
        max_fuel = getattr(self.token, "maxFuel", 0)
        if max_fuel <= 0:
            return report
        target = int(round(max_fuel * 0.7))
        current = getattr(self.token, "currentFuel", max_fuel)
        if current >= target:
            return report
        need = target - current
        to_add = min(need, available_pe)
        added = self._refuel(to_add)
        report["spent"] = added
        report["fuel_added"] = added
        if added < need:
            log_token(
                f"{self.token.id}: niewystarczające PE na paliwo",
                "INFO",
                needed=need,
                added=added,
                available_pe=available_pe,
            )
        return report

    def _restore_cv_to_threshold(self, available_pe: int) -> Dict[str, int]:
        report = {"spent": 0, "cv_added": 0}
        if available_pe <= 0:
            return report
        max_cv = self.token.stats.get("combat_value", 0)
        if max_cv <= 0:
            return report
        target = int(round(max_cv * 0.8))
        current = getattr(self.token, "combat_value", max_cv)
        if current >= target:
            return report
        need = target - current
        to_add = min(need, available_pe)
        added = self._restore_combat_value(to_add)
        report["spent"] = added
        report["cv_added"] = added
        if added < need:
            log_token(
                f"{self.token.id}: niewystarczające PE na CV",
                "INFO",
                needed=need,
                added=added,
                available_pe=available_pe,
            )
        return report

    def _can_top_off_cv(self) -> bool:
        context = getattr(self, "context", {}) or {}
        position = context.get("position")
        danger_level = self._danger_level_at(position, context.get("danger_zones", {})) if position else 0
        return danger_level == 0 and not self.memory.get("hold_position", False)

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

    def _visible_enemies(
        self,
        engine,
        detection_map: Optional[Dict[str, Dict[str, Any]]] = None,
    ) -> List:
        detection_map = detection_map if detection_map is not None else (self.context or {}).get("enemy_detection") or {}
        board = getattr(engine, "board", None)
        my_pos = (getattr(self.token, "q", None), getattr(self.token, "r", None))
        if None in my_pos:
            return []

        visible: List = []
        for other in getattr(engine, "tokens", []):
            if not self._is_enemy(other):
                continue
            enemy_id = getattr(other, "id", None)
            if enemy_id is None:
                continue
            info = detection_map.get(enemy_id)
            detection_level = (info or {}).get("detection_level", 0.0) or 0.0
            if detection_level <= 0:
                continue
            if board is not None and None not in (other.q, other.r):
                try:
                    distance = board.hex_distance(my_pos, (other.q, other.r))
                    if info is not None and "distance" not in info:
                        info["distance"] = distance
                except AttributeError:
                    continue
            visible.append(other)
        return visible

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

    def _attack_value_for(self, token) -> float:
        stats = getattr(token, "stats", {}) or {}
        attack_spec = stats.get("attack")
        base_value = 0.0

        if isinstance(attack_spec, dict):
            numeric_fields = [
                attack_spec.get(key)
                for key in (
                    "value",
                    "anti_inf",
                    "anti_armor",
                    "bombardment",
                    "support",
                    "siege",
                    "naval",
                    "air",
                )
            ]
            base_candidates = [float(val) for val in numeric_fields if isinstance(val, (int, float))]
            if base_candidates:
                base_value = max(base_candidates)
        elif isinstance(attack_spec, (int, float)):
            base_value = float(attack_spec)

        if base_value <= 0:
            combat_fallback = stats.get("combat_value", getattr(token, "combat_value", 0) or 0)
            base_value = float(combat_fallback) * 0.5

        attack_bonus = stats.get("attack_bonus") or 0.0
        if isinstance(attack_bonus, (int, float)) and attack_bonus != 0:
            base_value *= 1.0 + float(attack_bonus)

        return max(0.0, base_value)

    def _perceived_attack_range(self, enemy, detection_info: Optional[Dict[str, Any]]) -> int:
        base_range = self._attack_range_for(enemy)
        if detection_info is None:
            return max(1, min(base_range, 1))

        detection_level = detection_info.get("detection_level", 0.0) or 0.0
        if detection_level >= 0.8:
            return base_range
        if detection_level >= 0.5:
            return max(1, min(base_range, 2))
        return 1

    def _estimate_enemy_cv(self, enemy, context: Dict[str, Any]) -> int:
        detection_map = context.get("enemy_detection") or {}
        detection_info = detection_map.get(getattr(enemy, "id", None))
        real_cv = getattr(enemy, "combat_value", enemy.stats.get("combat_value", 0)) or 0
        if real_cv <= 0:
            return 0

        if detection_info is None:
            return max(1, int(round(real_cv * random.uniform(0.6, 0.9))))

        detection_level = detection_info.get("detection_level", 0.0) or 0.0
        if detection_level >= 0.8:
            return real_cv
        if detection_level >= 0.5:
            return max(1, int(round(real_cv * random.uniform(0.7, 0.95))))
        return max(1, int(round(real_cv * random.uniform(0.5, 0.85))))

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

    # ------------------------------------------------------------------
    # Nowa logika autonomiczna
    # ------------------------------------------------------------------

    def _reset_turn_state(self) -> None:
        self.context: Dict[str, Any] = {}
        self.memory.setdefault("failed_hexes", set())
        if not self.memory.get("hold_position"):
            self.memory.pop("hold_reason", None)
            self.memory.pop("hold_calm_turns", None)

    def _update_hold_state(self, context: Dict[str, Any]) -> None:
        if not self.memory.get("hold_position"):
            self.memory.pop("hold_calm_turns", None)
            return

        position = context.get("position")
        danger_level = self._danger_level_at(position, context.get("danger_zones", {}))
        visible_enemies = context.get("visible_enemies", []) or []
        if danger_level <= 0 and not visible_enemies:
            calm_turns = int(self.memory.get("hold_calm_turns", 0)) + 1
            if calm_turns >= self.HOLD_RELEASE_TURNS:
                log_token(
                    f"{self.token.id}: zwolnienie hold_position po spokojnych turach",
                    "DEBUG",
                    calm_turns=calm_turns,
                    hold_reason=self.memory.get("hold_reason"),
                )
                self.memory.pop("hold_position", None)
                self.memory.pop("hold_reason", None)
                self.memory.pop("hold_calm_turns", None)
            else:
                self.memory["hold_calm_turns"] = calm_turns
        else:
            self.memory["hold_calm_turns"] = 0

    def _set_hold_position(self, reason: str) -> None:
        normalized = reason or "unspecified"
        if not self.memory.get("hold_position"):
            self.memory["hold_position"] = True
            self.memory["hold_reason"] = normalized
            self.memory["hold_calm_turns"] = 0
        else:
            self.memory.setdefault("hold_reason", normalized)
            self.memory["hold_calm_turns"] = 0

    def _evaluate_state(self, engine, player) -> Dict[str, Any]:
        board = getattr(engine, "board", None)
        position = (getattr(self.token, "q", None), getattr(self.token, "r", None))
        max_mp = getattr(self.token, "maxMovePoints", self.token.stats.get("move", 0) or 0)
        max_fuel = getattr(self.token, "maxFuel", self.token.stats.get("maintenance", 0) or 0)
        current_cv = getattr(self.token, "combat_value", self.token.stats.get("combat_value", 0) or 0)
        detection_map = self._collect_detection_map(engine, player)
        visible_enemies = self._visible_enemies(engine, detection_map)
        friendly_tokens = self._friendly_tokens(engine)
        danger_zones = self._compute_danger_zones(engine, visible_enemies, detection_map)

        context = {
            "position": position,
            "board": board,
            "visible_enemies": visible_enemies,
            "friendly_tokens": friendly_tokens,
            "danger_zones": danger_zones,
            "enemy_detection": detection_map,
            "current_mp": getattr(self.token, "currentMovePoints", 0) or 0,
            "max_mp": max_mp,
            "current_fuel": getattr(self.token, "currentFuel", max_fuel) or 0,
            "max_fuel": max_fuel,
            "combat_value": current_cv,
            "max_cv": self.token.stats.get("combat_value", current_cv) or 0,
        }
        if self.specialist is not None:
            try:
                context = self.specialist.extend_context(context)
            except Exception:
                pass
        self.context = context
        return context

    def _update_context(self, engine, player, context: Dict[str, Any]) -> None:
        context["current_mp"] = getattr(self.token, "currentMovePoints", context.get("current_mp", 0)) or 0
        context["current_fuel"] = getattr(self.token, "currentFuel", context.get("current_fuel", 0)) or 0
        context["combat_value"] = getattr(self.token, "combat_value", context.get("combat_value", 0)) or 0
        context["position"] = (getattr(self.token, "q", None), getattr(self.token, "r", None))
        detection_map = self._collect_detection_map(engine, player, context.get("enemy_detection"))
        visible_enemies = self._visible_enemies(engine, detection_map)
        context["enemy_detection"] = detection_map
        context["visible_enemies"] = visible_enemies
        context["danger_zones"] = self._compute_danger_zones(engine, visible_enemies, detection_map)
        if self.specialist is not None:
            try:
                self.specialist.update_context(context)
            except Exception:
                pass

    def _collect_detection_map(
        self,
        engine,
        player,
        base_map: Optional[Dict[str, Dict[str, Any]]] = None,
    ) -> Dict[str, Dict[str, Any]]:
        detection_map: Dict[str, Dict[str, Any]] = dict(base_map or {})
        if engine is None or player is None:
            return detection_map

        board = getattr(engine, "board", None)
        my_pos = (getattr(self.token, "q", None), getattr(self.token, "r", None))
        sight = self._sight()

        for enemy in getattr(engine, "tokens", []):
            enemy_id = getattr(enemy, "id", None)
            if enemy_id is None or not self._is_enemy(enemy):
                continue

            info = get_detection_info_for_player(player, enemy_id, include_temp=True)
            detection_level = 0.0
            distance = None
            detected_by = None

            if info:
                detection_level = info.get("detection_level", 0.0) or 0.0
                distance = info.get("distance")
                detected_by = info.get("detected_by")

            if detection_level <= 0 and board is not None and sight > 0:
                if None not in (*my_pos, enemy.q, enemy.r):
                    distance = board.hex_distance(my_pos, (enemy.q, enemy.r))
                    if distance is not None and distance < sight:
                        detection_level = VisionService.calculate_detection_level(distance, sight)

            if detection_level <= 0:
                detection_map.pop(enemy_id, None)
                continue

            filtered = apply_detection_filter(enemy, detection_level)
            filtered["detection_level"] = detection_level
            if distance is not None:
                filtered["distance"] = distance
            if detected_by:
                filtered["detected_by"] = detected_by

            detection_map[enemy_id] = filtered

        # Usuń wpisy dla zniszczonych żetonów
        active_ids = {getattr(tok, "id", None) for tok in getattr(engine, "tokens", [])}
        stale_keys = [key for key in detection_map.keys() if key not in active_ids]
        for key in stale_keys:
            detection_map.pop(key, None)

        return detection_map

    def _classify_status(self, context: Dict[str, Any]) -> str:
        max_cv = context.get("max_cv", 0) or 0
        combat_value = context.get("combat_value", 0)
        current_fuel = context.get("current_fuel", 0)
        max_fuel = context.get("max_fuel", 0) or 1
        friendly_nearby = self._friendly_in_radius(context.get("position"), context.get("friendly_tokens", []), 2)
        danger_level = self._danger_level_at(context.get("position"), context.get("danger_zones", {}))

        if max_cv > 0 and combat_value <= max_cv * 0.3 and not friendly_nearby:
            return self.STATUS_URGENT_RETREAT
        if max_fuel > 0 and current_fuel < max_fuel * 0.4:
            return self.STATUS_LOW_FUEL
        if danger_level >= 3:
            return self.STATUS_THREATENED
        return self.STATUS_NORMAL

    def _choose_movement_mode(self, status: str, context: Dict[str, Any]) -> str:
        if hasattr(self.token, "movement_mode_locked"):
            self.token.movement_mode_locked = False

        visible_enemies = bool(context.get("visible_enemies"))
        danger_level = self._danger_level_at(context.get("position"), context.get("danger_zones", {}))
        current_mp = context.get("current_mp", 0)
        max_mp = max(1, context.get("max_mp", 1))
        current_fuel = context.get("current_fuel", 0)
        max_fuel = max(1, context.get("max_fuel", 1))

        fuel_ratio = current_fuel / max_fuel
        mp_ratio = current_mp / max_mp

        if status in {self.STATUS_URGENT_RETREAT, self.STATUS_THREATENED} or visible_enemies or danger_level >= 1:
            mode = "combat"
        elif fuel_ratio >= 0.6 and mp_ratio >= 0.6:
            mode = "march"
        else:
            mode = "recon"

        self._set_movement_mode(mode)
        return mode

    def _set_movement_mode(self, mode: str) -> None:
        try:
            setattr(self.token, "movement_mode", mode)
        except AttributeError:
            pass
        if hasattr(self.token, "movement_mode_locked"):
            self.token.movement_mode_locked = True

    def _plan_actions(self, status: str, context: Dict[str, Any], pe_budget: int) -> List[str]:
        profile_key = self._select_action_profile(status, context)
        profile_actions = list(self.ACTION_PROFILES.get(profile_key, []))
        filtered_actions = self._filter_actions(profile_actions, context, pe_budget)

        forced_actions: List[str] = []
        current_fuel = context.get("current_fuel", 0) or 0
        max_fuel = context.get("max_fuel", 0) or 0
        combat_value = context.get("combat_value", 0) or 0
        max_cv = context.get("max_cv", 0) or 0

        if pe_budget > 0 and max_fuel > 0:
            fuel_gap = max_fuel - current_fuel
            fuel_threshold = max(1, int(max_fuel * 0.05))
            if fuel_gap >= fuel_threshold and "refuel_minimum" not in filtered_actions:
                forced_actions.append("refuel_minimum")

        if pe_budget > 1 and max_cv > 0:
            cv_gap = max_cv - combat_value
            cv_threshold = max(1, int(max_cv * 0.05))
            if cv_gap >= cv_threshold and "restore_cv" not in filtered_actions:
                forced_actions.append("restore_cv")

        if forced_actions:
            existing = [action for action in filtered_actions if action not in forced_actions]
            filtered_actions = forced_actions + existing

        if not filtered_actions and profile_key != "patrol":
            fallback_actions = list(self.ACTION_PROFILES.get("patrol", []))
            filtered_actions = self._filter_actions(fallback_actions, context, pe_budget)
            if filtered_actions:
                profile_key = "patrol"

        self.memory["action_profile"] = profile_key
        return filtered_actions

    def _select_action_profile(self, status: str, context: Dict[str, Any]) -> str:
        if status == self.STATUS_URGENT_RETREAT:
            return "retreat"
        if status == self.STATUS_LOW_FUEL:
            return "recovery"
        if status == self.STATUS_THREATENED:
            return "retreat" if not context.get("visible_enemies") else "combat"
        if context.get("visible_enemies"):
            return "combat"
        if context.get("current_mp", 0) <= 1:
            return "recovery"
        return "patrol"

    def _filter_actions(self, actions: List[str], context: Dict[str, Any], pe_budget: int) -> List[str]:
        filtered: List[str] = []
        max_fuel = context.get("max_fuel", 0) or 0
        max_cv = context.get("max_cv", 0) or 0
        current_fuel = context.get("current_fuel", 0) or 0
        combat_value = context.get("combat_value", 0) or 0

        for action in actions:
            if action == "refuel_minimum" and max_fuel > 0 and current_fuel >= max_fuel * 0.98:
                continue
            if action == "restore_cv" and (pe_budget <= 0 or max_cv <= 0 or combat_value >= max_cv * 0.92):
                continue
            if action in {"maneuver", "withdraw"} and not self._can_move():
                continue
            if action == "attack" and not context.get("visible_enemies"):
                continue
            filtered.append(action)
        return filtered

    def _friendly_tokens(self, engine) -> List:
        if engine is None:
            return []
        friendly = []
        my_nation = self._owner_nation(self.token)
        for tok in getattr(engine, "tokens", []):
            if tok is self.token:
                continue
            if self._owner_nation(tok) == my_nation:
                friendly.append(tok)
        return friendly

    def _friendly_in_radius(self, position: Tuple[int, int], tokens: List, radius: int) -> bool:
        if position is None or tokens is None:
            return False
        for tok in tokens:
            if None in (tok.q, tok.r):
                continue
            if self._hex_distance(position, (tok.q, tok.r)) <= radius:
                return True
        return False

    def _compute_danger_zones(
        self,
        engine,
        enemies: Optional[List] = None,
        detection_map: Optional[Dict[str, Dict[str, Any]]] = None,
    ) -> Dict[Tuple[int, int], int]:
        enemies = enemies or []
        detection_map = detection_map or {}
        danger: Dict[Tuple[int, int], int] = {}
        board = getattr(engine, "board", None) if engine else self.context.get("board")
        for enemy in enemies:
            enemy_pos = (enemy.q, enemy.r)
            if None in enemy_pos:
                continue
            info = detection_map.get(getattr(enemy, "id", None))
            attack_range = self._perceived_attack_range(enemy, info)
            hexes = self._hexes_in_range(enemy_pos, attack_range, board)
            for h in hexes:
                danger[h] = danger.get(h, 0) + 1
        return danger

    def _hexes_in_range(self, center: Tuple[int, int], rng: int, board) -> List[Tuple[int, int]]:
        if rng <= 0:
            return [center]
        hexes = []
        for dq in range(-rng, rng + 1):
            for dr in range(-rng, rng + 1):
                target = (center[0] + dq, center[1] + dr)
                if self._hex_distance(center, target, board) <= rng:
                    hexes.append(target)
        return hexes

    def _hex_distance(self, start: Tuple[int, int], end: Tuple[int, int], board=None) -> int:
        board = board or self.context.get("board")
        if board is not None:
            try:
                return board.hex_distance(start, end)
            except AttributeError:
                pass
        if None in (*start, *end):
            return 9999
        # fallback axial distance
        sq, sr = start
        eq, er = end
        return int((abs(sq - eq) + abs(sr - er) + abs((sq - sr) - (eq - er))) / 2)

    def _danger_level_at(self, position: Tuple[int, int], danger_zones: Dict[Tuple[int, int], int]) -> int:
        if position is None:
            return 0
        return danger_zones.get(position, 0)

    def _plan_candidates(
        self,
        engine,
        context: Dict[str, Any],
        retreat: bool = False,
        exclude: Optional[Set[Tuple[int, int]]] = None,
    ) -> Tuple[List[Tuple[int, int]], Dict[Tuple[int, int], Optional[Tuple[int, int]]]]:
        board = context.get("board")
        start = context.get("position")
        if board is None or None in start:
            return [], {}
        max_mp = context.get("current_mp", 0)
        max_fuel = context.get("current_fuel", 0)
        if max_mp <= 0 or max_fuel <= 0:
            return [], {}

        queue: List[Tuple[int, int, int, int]] = [(start[0], start[1], 0, 0)]
        visited: Dict[Tuple[int, int], Tuple[int, int]] = {start: (0, 0)}
        parents: Dict[Tuple[int, int], Optional[Tuple[int, int]]] = {start: None}
        results: List[Tuple[int, int]] = []

        while queue:
            q, r, cost_mp, cost_fuel = queue.pop(0)
            for neighbor in board.neighbors(q, r):
                if not self._is_passable(engine, neighbor):
                    continue
                tile = board.get_tile(*neighbor)
                move_mod = getattr(tile, "move_mod", 0) if tile else 0
                step_cost = 1 + max(0, move_mod)
                new_cost_mp = cost_mp + step_cost
                new_cost_fuel = cost_fuel + step_cost
                if new_cost_mp > max_mp or new_cost_fuel > max_fuel:
                    continue
                prev = visited.get(neighbor)
                if prev and prev[0] <= new_cost_mp and prev[1] <= new_cost_fuel:
                    continue
                visited[neighbor] = (new_cost_mp, new_cost_fuel)
                parents[neighbor] = (q, r)
                queue.append((neighbor[0], neighbor[1], new_cost_mp, new_cost_fuel))
                results.append(neighbor)

        danger_zones = context.get("danger_zones", {}) or {}
        start_danger = self._danger_level_at(start, danger_zones)
        filtered = []
        excluded_hexes = exclude or set()
        failed_hexes = self.memory.get("failed_hexes", set())
        for hex_pos in results:
            if hex_pos in excluded_hexes:
                continue
            if hex_pos in failed_hexes:
                continue
            if retreat and start_danger > 0:
                if self._danger_level_at(hex_pos, danger_zones) >= start_danger:
                    continue
            filtered.append(hex_pos)
        if retreat and not filtered:
            filtered = [
                hex_pos
                for hex_pos in results
                if hex_pos not in failed_hexes and hex_pos not in excluded_hexes
            ]
        return filtered, parents

    def _reconstruct_path(
        self,
        parents: Dict[Tuple[int, int], Optional[Tuple[int, int]]],
        start: Tuple[int, int],
        goal: Tuple[int, int],
    ) -> List[Tuple[int, int]]:
        path: List[Tuple[int, int]] = []
        current = goal
        while current is not None and current in parents:
            path.append(current)
            current = parents[current]
        path.reverse()
        if path and path[0] == start:
            return path[1:]
        return []

    def _score_tile(
        self,
        engine,
        context: Dict[str, Any],
        position: Tuple[int, int],
        retreat: bool = False,
        start_danger: int = 0,
    ) -> float:
        board = context.get("board")
        tile = board.get_tile(*position) if board else None
        defense_bonus = getattr(tile, "defense_mod", 0) if tile else 0
        danger_level = self._danger_level_at(position, context.get("danger_zones", {}))
        support = 0
        for friend in context.get("friendly_tokens", []):
            if None in (friend.q, friend.r):
                continue
            if self._hex_distance(position, (friend.q, friend.r), board) <= 2:
                support += 1
        nearest_enemy_distance = min(
            (self._hex_distance(position, (enemy.q, enemy.r), board) for enemy in context.get("visible_enemies", []) if None not in (enemy.q, enemy.r)),
            default=5,
        )
        start = context.get("position")
        distance_from_start = self._hex_distance(start, position, board) if start else 0

        objective_bonus = 0.0
        repeat_penalty = 0.0
        last_destination = self.memory.get("last_destination")
        if last_destination and position == last_destination:
            repeat_penalty -= 1.5

        if retreat:
            distance_bonus = max(0.0, distance_from_start)
            objective_score = max(0, nearest_enemy_distance) * 2
            safety_score = (defense_bonus * 1.5) - (danger_level * 3)
            if start_danger > 0 and danger_level >= start_danger:
                safety_score -= 5
        else:
            distance_bonus = max(0.0, distance_from_start * 0.2)
            objective_score = max(0, 5 - nearest_enemy_distance) + distance_bonus
            safety_score = defense_bonus - (danger_level * 2)

            objective_target = context.get("specialist_objective") or context.get("supply_target_kp")
            if objective_target and start and None not in (*start, *objective_target):
                target_distance = self._hex_distance(position, objective_target, board)
                start_distance = self._hex_distance(start, objective_target, board)
                progress = start_distance - target_distance
                if progress > 0:
                    objective_bonus += progress * 5.0
                elif progress <= 0:
                    objective_bonus -= 1.5
                objective_bonus -= target_distance * 0.2
                if target_distance == 0:
                    objective_bonus += 20.0
                elif target_distance <= 1 and progress >= 0:
                    objective_bonus += 3.0

        support_score = support
        return float(safety_score + support_score + objective_score + distance_bonus + objective_bonus + repeat_penalty)

    def _select_best_hex(
        self,
        engine,
        context: Dict[str, Any],
        retreat: bool = False,
        exclude: Optional[Set[Tuple[int, int]]] = None,
    ) -> Tuple[Optional[Tuple[int, int]], List[Tuple[int, int]]]:
        start = context.get("position")
        danger_zones = context.get("danger_zones", {}) or {}
        start_danger = self._danger_level_at(start, danger_zones) if start else 0
        candidates, parents = self._plan_candidates(engine, context, retreat=retreat, exclude=exclude)
        if not candidates:
            return None, []
        scored = [
            (
                self._score_tile(
                    engine,
                    context,
                    pos,
                    retreat=retreat,
                    start_danger=start_danger,
                ),
                pos,
            )
            for pos in candidates
        ]
        scored.sort(key=lambda item: item[0], reverse=True)
        best = scored[0][1]
        path = self._reconstruct_path(parents, start, best)
        return best, path

    def _is_in_danger_zone(self, position: Tuple[int, int]) -> bool:
        return self._danger_level_at(position, self.context.get("danger_zones", {})) > 0

    def _estimate_threat_level(self, engine, position: Tuple[int, int]) -> int:
        danger_zones = self.context.get("danger_zones") or self._compute_danger_zones(engine, self.context.get("visible_enemies", []))
        return self._danger_level_at(position, danger_zones)

    def _can_risk_attack(self, context: Dict[str, Any], has_support: bool = False) -> bool:
        max_cv = context.get("max_cv", 0) or 0
        combat_value = context.get("combat_value", 0) or 0
        max_fuel = context.get("max_fuel", 0) or 0
        current_fuel = context.get("current_fuel", 0) or 0
        fuel_ready = max_fuel == 0 or current_fuel >= max_fuel * 0.5
        cv_ready = max_cv == 0 or combat_value >= max_cv * 0.6
        if not (fuel_ready and cv_ready):
            return False
        if has_support:
            return True
        hold_flag = self.memory.get("hold_position", False)
        return not hold_flag

    def _compute_attack_ratio(
        self,
        enemy,
        context: Dict[str, Any],
        detection_info: Optional[Dict[str, Any]],
        my_pos: Tuple[int, int],
        enemy_pos: Tuple[int, int],
        board,
    ) -> Dict[str, Any]:
        attack_value = max(0.0, float(self._attack_value_for(self.token)))
        attack_range = self._attack_range()

        max_cv = max(1, context.get("max_cv") or self.token.stats.get("combat_value", 0) or 1)
        current_cv = max(0.0, float(getattr(self.token, "combat_value", context.get("combat_value", max_cv)) or 0))
        attacker_health_ratio = min(1.0, current_cv / max_cv)

        max_fuel = max(1, context.get("max_fuel") or self.token.stats.get("maintenance", 0) or 1)
        current_fuel = max(0.0, float(context.get("current_fuel", getattr(self.token, "currentFuel", max_fuel)) or 0))
        fuel_ratio = min(1.0, current_fuel / max_fuel)

        health_factor = 0.65 + 0.35 * attacker_health_ratio
        fuel_factor = 0.7 + 0.3 * fuel_ratio
        range_factor = 1.0 + 0.05 * max(0, attack_range - 1)
        effective_attack = attack_value * health_factor * fuel_factor * range_factor

        enemy_stats = getattr(enemy, "stats", {})
        defense_value = getattr(enemy, "defense_value", enemy_stats.get("defense_value", 0)) or 0
        terrain_mod = 0
        if board is not None and None not in (*enemy_pos,):
            try:
                tile = board.get_tile(enemy_pos[0], enemy_pos[1])
                terrain_mod = getattr(tile, "defense_mod", 0) or 0
            except AttributeError:
                terrain_mod = 0

        terrain_bonus = terrain_mod * 0.8
        base_defense = max(1.0, defense_value + terrain_bonus)

        enemy_max_cv = enemy_stats.get("combat_value", getattr(enemy, "combat_value", 0)) or 0
        enemy_max_cv = max(1, enemy_max_cv)
        enemy_current_cv = max(0.0, float(getattr(enemy, "combat_value", enemy_max_cv) or 0))
        defender_health_ratio = min(1.0, enemy_current_cv / enemy_max_cv)
        defense_health_factor = 0.55 + 0.45 * defender_health_ratio
        effective_defense = base_defense * defense_health_factor

        distance = None
        if board is not None and None not in (*my_pos, *enemy_pos):
            try:
                distance = board.hex_distance(my_pos, enemy_pos)
            except AttributeError:
                distance = None

        perceived_enemy_range = self._perceived_attack_range(enemy, detection_info)
        enemy_attack_value = max(0.0, float(self._attack_value_for(enemy)))
        counterattack = False
        if distance is not None and enemy_attack_value > 0:
            counterattack = perceived_enemy_range >= distance
            if counterattack:
                counter_power = enemy_attack_value * (0.5 + 0.5 * defender_health_ratio)
                effective_defense += counter_power * 0.35

        detection_level = (detection_info.get("detection_level") if detection_info else 0.0) or 0.0
        detection_clamped = max(0.0, min(1.0, detection_level))
        detection_penalty = 0.8 + 0.2 * detection_clamped

        ratio_base = effective_attack / max(1.0, effective_defense)
        ratio_final = ratio_base * detection_penalty

        return {
            "ratio_base": ratio_base,
            "ratio_final": ratio_final,
            "detection": detection_level,
            "terrain_mod": terrain_mod,
            "counterattack": counterattack,
            "distance": distance,
            "attacker_health": attacker_health_ratio,
            "fuel_ratio": fuel_ratio,
            "defender_health": defender_health_ratio,
        }

    def _should_attack(self, enemy, context: Dict[str, Any]) -> bool:
        evaluation: Dict[str, Any] = {
            "target_id": getattr(enemy, "id", None) if enemy else None,
            "position": context.get("position") or (getattr(self.token, "q", None), getattr(self.token, "r", None)),
            "enemy_position": (getattr(enemy, "q", None), getattr(enemy, "r", None)) if enemy else None,
            "support": False,
            "detection": None,
            "ratio": None,
            "ratio_adjusted": None,
            "distance": None,
            "risk_type": None,
            "threshold": None,
            "decision": "hold",
            "reason": None,
        }

        def finalize(decision: str, *, reason: Optional[str] = None) -> bool:
            evaluation["decision"] = decision
            if reason is not None:
                evaluation["reason"] = reason
            if decision == "hold" and evaluation.get("hold_reason") is None:
                evaluation["hold_reason"] = reason
            self.memory["_last_attack_evaluation"] = evaluation
            return decision == "execute"

        if enemy is None:
            return finalize("hold", reason="no_target")

        board = context.get("board")
        my_pos = evaluation.get("position")
        if my_pos is None or None in my_pos:
            my_pos = (getattr(self.token, "q", None), getattr(self.token, "r", None))
            evaluation["position"] = my_pos
        enemy_pos = evaluation["enemy_position"] = (enemy.q, enemy.r)
        if None in (*my_pos, *enemy_pos):
            return finalize("hold", reason="invalid_position")

        distance = self._hex_distance(my_pos, enemy_pos, board)
        evaluation["distance"] = distance
        if distance is None:
            return finalize("hold", reason="distance_unknown")
        if distance > self._attack_range():
            return finalize("hold", reason="out_of_range")

        detection_map = context.get("enemy_detection") or {}
        detection_info = detection_map.get(getattr(enemy, "id", None))
        detection_level = (detection_info.get("detection_level") if detection_info else 0.0) or 0.0
        evaluation["detection"] = detection_level
        if detection_level <= 0:
            return finalize("hold", reason="no_detection")

        ratio_data = self._compute_attack_ratio(enemy, context, detection_info, my_pos, enemy_pos, board)
        ratio = ratio_data.get("ratio_base", 0.0)
        ratio_adjusted = ratio_data.get("ratio_final", ratio)
        evaluation["ratio"] = ratio
        evaluation["ratio_adjusted"] = ratio_adjusted
        evaluation["distance"] = ratio_data.get("distance", distance)
        evaluation["counterattack"] = ratio_data.get("counterattack")
        evaluation["attacker_health"] = ratio_data.get("attacker_health")
        evaluation["defender_health"] = ratio_data.get("defender_health")
        evaluation["fuel_ratio"] = ratio_data.get("fuel_ratio")

        has_support = self._friendly_in_radius(enemy_pos, context.get("friendly_tokens", []), 1)
        evaluation["support"] = has_support

        if ratio_adjusted >= 1.1:
            evaluation["threshold"] = ">=1.1"
            return finalize("execute", reason="threshold_met")
        if ratio_adjusted >= 1.0 and has_support:
            evaluation["threshold"] = ">=1.0_support"
            return finalize("execute", reason="support_threshold")

        if ratio_adjusted >= 0.9 and self._can_risk_attack(context, has_support):
            evaluation["threshold"] = ">=0.9_risk"
            evaluation["risk_type"] = "risk"
            log_token(
                f"{self.token.id}: ryzykowny atak na {enemy.id}",
                "DEBUG",
                ratio=round(ratio, 2),
                ratio_adjusted=round(ratio_adjusted, 2),
                detection=round(detection_level, 2),
                support=has_support,
                fuel=context.get("current_fuel", 0),
                combat_value=context.get("combat_value", 0),
                counterattack=ratio_data.get("counterattack"),
                attacker_health=round(ratio_data.get("attacker_health", 0.0), 2),
                defender_health=round(ratio_data.get("defender_health", 0.0), 2),
                terrain_mod=ratio_data.get("terrain_mod"),
                fuel_ratio=round(ratio_data.get("fuel_ratio", 0.0), 2),
            )
            return finalize("execute", reason="risk_threshold")

        if detection_level < 0.5 and self._can_risk_attack(context, has_support):
            gamble_threshold = 0.75 + (detection_level * 0.2)
            evaluation["threshold"] = f">={gamble_threshold:.2f}_aggressive"
            evaluation["risk_type"] = "aggressive"
            if ratio_adjusted >= gamble_threshold:
                aggression_chance = 0.12 + (0.08 * detection_level)
                roll = random.random()
                evaluation["aggression_chance"] = aggression_chance
                evaluation["risk_roll"] = roll
                if roll <= aggression_chance:
                    log_token(
                        f"{self.token.id}: agresywny atak przy niskiej wykrywalności na {enemy.id}",
                        "DEBUG",
                        ratio=round(ratio, 2),
                        ratio_adjusted=round(ratio_adjusted, 2),
                        detection=round(detection_level, 2),
                        support=has_support,
                        fuel=context.get("current_fuel", 0),
                        combat_value=context.get("combat_value", 0),
                        counterattack=ratio_data.get("counterattack"),
                        attacker_health=round(ratio_data.get("attacker_health", 0.0), 2),
                        defender_health=round(ratio_data.get("defender_health", 0.0), 2),
                        terrain_mod=ratio_data.get("terrain_mod"),
                        fuel_ratio=round(ratio_data.get("fuel_ratio", 0.0), 2),
                        aggression_roll=round(roll, 2),
                        aggression_chance=round(aggression_chance, 2),
                    )
                    return finalize("execute", reason="aggressive_success")
                return finalize("hold", reason="aggressive_roll_failed")
            return finalize("hold", reason="below_aggressive_threshold")

        evaluation["threshold"] = ">=1.0_support" if has_support else ">=1.1"
        return finalize("hold", reason="ratio_below_threshold")

    def _attack_range_for(self, token) -> int:
        attack_stats = getattr(token, "stats", {}).get("attack", {})
        if isinstance(attack_stats, dict):
            return int(attack_stats.get("range", 1))
        return int(attack_stats or 1)

    def _record_attack_plan(
        self,
        evaluation: Optional[Dict[str, Any]],
        executed: bool,
        attack_report: Optional[Dict[str, Any]],
        context: Dict[str, Any],
    ) -> None:
        details: Dict[str, Any] = {
            "planned_attack": True,
            "executed": executed,
        }

        evaluation = dict(evaluation or {})
        decision = evaluation.get("decision") or ("execute" if executed else "hold")
        details["decision"] = decision
        if "reason" in evaluation:
            details["reason"] = evaluation.get("reason")
        if "threshold" in evaluation and evaluation.get("threshold") is not None:
            details["threshold"] = evaluation.get("threshold")
        if "risk_type" in evaluation and evaluation.get("risk_type") is not None:
            details["risk_type"] = evaluation.get("risk_type")
        if "hold_reason" in evaluation and evaluation.get("hold_reason") is not None:
            details["hold_reason"] = evaluation.get("hold_reason")

        target_id = evaluation.get("target_id")
        if target_id is not None:
            details["target"] = target_id

        support_flag = evaluation.get("support")
        if support_flag is not None:
            details["support"] = bool(support_flag)

        detection_val = evaluation.get("detection")
        if isinstance(detection_val, (int, float)):
            details["detection"] = round(float(detection_val), 2)

        ratio_val = evaluation.get("ratio")
        if isinstance(ratio_val, (int, float)):
            details["ratio"] = round(float(ratio_val), 2)

        ratio_adj_val = evaluation.get("ratio_adjusted")
        if isinstance(ratio_adj_val, (int, float)):
            details["ratio_adjusted"] = round(float(ratio_adj_val), 2)

        distance_val = evaluation.get("distance")
        if isinstance(distance_val, (int, float)):
            details["distance"] = distance_val

        counterattack = evaluation.get("counterattack")
        if counterattack is not None:
            details["counterattack"] = counterattack

        for key in ("attacker_health", "defender_health", "fuel_ratio"):
            val = evaluation.get(key)
            if isinstance(val, (int, float)):
                details[key] = round(float(val), 2)

        risk_roll = evaluation.get("risk_roll")
        if isinstance(risk_roll, (int, float)):
            details["risk_roll"] = round(float(risk_roll), 2)
        aggression_chance = evaluation.get("aggression_chance")
        if isinstance(aggression_chance, (int, float)):
            details["aggression_chance"] = round(float(aggression_chance), 2)

        position = evaluation.get("position") or context.get("position")
        if isinstance(position, tuple):
            details["position_q"] = position[0]
            details["position_r"] = position[1]

        enemy_position = evaluation.get("enemy_position")
        if isinstance(enemy_position, tuple):
            details["target_q"] = enemy_position[0]
            details["target_r"] = enemy_position[1]

        if attack_report:
            for key in ("success", "damage_dealt", "damage_taken"):
                if key in attack_report:
                    details[f"attack_{key}"] = attack_report.get(key)

        log_token(
            f"{self.token.id}: plan ataku",
            "DEBUG",
            **details,
        )