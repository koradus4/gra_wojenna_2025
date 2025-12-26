"""
Minimalna implementacja AI komendanta.

Komendant dzieli dostępne PE po równo między podległe żetony, a każdy
żeton działa według własnej, uproszczonej logiki TokenAI. Niewykorzystane
punkty wracają do puli dowódcy na koniec tury.
"""
from __future__ import annotations

import json
import unicodedata
from pathlib import Path
from typing import List, Dict, Optional, Tuple, Any

from ai.logs import log_commander, log_error
from ai.tokens import create_token_ai
from balance.model import compute_token, build_unit_names, ALLOWED_SUPPORT
from core.unit_factory import base_price
from core.ekonomia import EconomySystem
from engine.token import Token


class CommanderAI:
    def __init__(self, player):
        self.player = player

    def execute_turn(self, game_engine) -> None:
        total_pe_before_spawn = self._sync_player_points()
        reinforcement_report = self._handle_reinforcements(game_engine, total_pe_before_spawn)
        total_pe = reinforcement_report["remaining_pe"]
        tokens = self._my_tokens(game_engine)
        needs = self._collect_support_needs(tokens)
        setattr(self.player, "ai_support_needs", needs)

        log_commander(
            "Start tury komendanta",
            level="INFO",
            commander_id=self.player.id,
            nation=self.player.nation,
            commander_name=getattr(self.player, "name", None),
            tokens=len(tokens),
            budget_before_spawn=total_pe_before_spawn,
            budget_after_spawn=total_pe,
            reinforcement_orders=len(reinforcement_report["processed_orders"]),
            reinforcement_spawned=len(reinforcement_report["spawned"]),
            reinforcement_spent=reinforcement_report["spent"],
            resupply_needs=needs,
        )

        if not tokens:
            log_commander(
                "Brak żetonów do aktywacji",
                level="WARNING",
            )
            return

        share = total_pe // len(tokens) if tokens else 0
        log_commander(
            "Plan przydziału PE",
            level="DEBUG",
            commander_id=self.player.id,
            token_count=len(tokens),
            share_per_token=share,
            budget=total_pe,
        )
        spent_total = 0

        for token in tokens:
            token_ai = create_token_ai(token)
            log_commander(
                "Przydział żetonowi",
                level="DEBUG",
                commander_id=self.player.id,
                token_id=token.id,
                allocated_pe=share,
                token_position_q=getattr(token, "q", None),
                token_position_r=getattr(token, "r", None),
            )
            spent = token_ai.execute_turn(game_engine, self.player, share)
            actual_spent = min(share, spent)
            refunded = max(0, share - actual_spent)
            spent_total += actual_spent
            log_commander(
                "Podsumowanie żetonu",
                level="INFO",
                commander_id=self.player.id,
                token_id=token.id,
                allocated_pe=share,
                spent_pe=actual_spent,
                refunded_pe=refunded,
            )

        allocated_total = share * len(tokens)
        refunded_total = max(0, allocated_total - spent_total)
        unassigned_total = max(0, total_pe - allocated_total)
        log_commander(
            "Zbiorcze podsumowanie tury",
            level="INFO",
            commander_id=self.player.id,
            allocated_total=allocated_total,
            spent_total=spent_total,
            refunded_total=refunded_total,
            unassigned_total=unassigned_total,
            reinforcement_spent=reinforcement_report["spent"],
            reinforcement_count=len(reinforcement_report["spawned"]),
        )
        remaining = max(0, total_pe - spent_total)
        self._update_player_points(remaining)

        log_commander(
            "Koniec tury komendanta",
            level="INFO",
            commander_id=self.player.id,
            spent=spent_total,
            remaining=remaining,
            token_share=share,
            tokens=len(tokens),
            reinforcement_spent=reinforcement_report["spent"],
            reinforcement_count=len(reinforcement_report["spawned"]),
        )

    def _handle_reinforcements(self, game_engine, available_pe: int) -> Dict[str, Any]:
        report = {
            "spawned": [],
            "spent": 0,
            "remaining_pe": available_pe,
            "processed_orders": [],
        }

        if available_pe <= 0 or game_engine is None:
            return report

        self._ingest_purchase_orders()
        queue = self._get_reinforcement_queue()
        if not queue:
            return report

        board = getattr(game_engine, "board", None)
        if board is None:
            log_commander(
                "Pominięto wzmocnienia – brak planszy",
                level="DEBUG",
                commander_id=self.player.id,
            )
            return report

        candidates = self._collect_spawn_candidates(board, game_engine)
        if not candidates:
            log_commander(
                "Brak wolnych pól spawnu",
                level="DEBUG",
                commander_id=self.player.id,
                nation=self.player.nation,
            )
            return report

        max_spawns = getattr(self.player, "ai_reinforcement_cap", 2)
        spawned_tokens = []
        processed_orders = []
        total_spent = 0
        remaining_budget = available_pe

        orders_snapshot = list(self._iter_reinforcement_orders(queue))

        for order in orders_snapshot:
            if len(spawned_tokens) >= max(1, int(max_spawns)):
                break

            normalized, error = self._normalize_reinforcement_order(order)
            if normalized is None:
                log_error(
                    "Nieprawidłowe zamówienie wzmocnienia",
                    component="COMMANDER",
                    commander_id=self.player.id,
                    error=error,
                )
                processed_orders.append(order)
                continue

            cost = int(normalized.get("cost", 0))
            if cost <= 0:
                log_error(
                    "Pominięto zamówienie wzmocnienia – niepoprawny koszt",
                    component="COMMANDER",
                    commander_id=self.player.id,
                    order_id=normalized.get("order_id"),
                )
                processed_orders.append(order)
                continue

            if cost > remaining_budget:
                log_commander(
                    "Wzmocnienie oczekuje na budżet",
                    level="DEBUG",
                    commander_id=self.player.id,
                    order_id=normalized.get("order_id"),
                    required=cost,
                    available=remaining_budget,
                )
                continue

            spawn_hex = self._select_spawn_hex(candidates, normalized, game_engine)
            if spawn_hex is None:
                log_commander(
                    "Brak pola spawnu dla zamówienia",
                    level="WARNING",
                    commander_id=self.player.id,
                    order_id=normalized.get("order_id"),
                    unit_type=normalized.get("unit_type"),
                )
                continue

            token = self._spawn_token_from_blueprint(game_engine, normalized["token_blueprint"], spawn_hex)
            if token is None:
                log_error(
                    "Nie udało się utworzyć żetonu wzmocnienia",
                    component="COMMANDER",
                    commander_id=self.player.id,
                    order_id=normalized.get("order_id"),
                )
                processed_orders.append(order)
                continue

            remaining_budget = self._apply_reinforcement_spend(cost)
            total_spent += cost
            report["remaining_pe"] = remaining_budget

            normalized["status"] = "deployed"
            normalized["last_deployed_turn"] = getattr(game_engine, "turn", None)
            self._append_reinforcement_history(token, cost, normalized, spawn_hex, game_engine)
            spawned_tokens.append(token)
            processed_orders.append(order)
            candidates = [hex_pos for hex_pos in candidates if hex_pos != spawn_hex]

            log_commander(
                "Wystawiono wzmocnienie",
                level="INFO",
                commander_id=self.player.id,
                token_id=getattr(token, "id", None),
                unit_type=normalized.get("unit_type"),
                unit_size=normalized.get("unit_size"),
                cost=cost,
                spawn_q=spawn_hex[0],
                spawn_r=spawn_hex[1],
                remaining_budget=remaining_budget,
            )

        if processed_orders:
            self._remove_processed_orders(queue, processed_orders)

        report["spawned"] = spawned_tokens
        report["spent"] = total_spent
        report["processed_orders"] = processed_orders
        report["remaining_pe"] = remaining_budget
        return report

    def _ingest_purchase_orders(self) -> None:
        events = getattr(self.player, "ai_purchase_events", None)
        if not events:
            return

        queue = self._get_reinforcement_queue()
        existing_ids = {
            order.get("token_id")
            for order in queue
            if isinstance(order, dict) and order.get("token_id")
        }

        accepted = 0
        failed = 0
        deferred: List[Dict[str, Any]] = []

        for event in events:
            if not isinstance(event, dict):
                failed += 1
                continue

            if event.get("commander_id") != self.player.id:
                deferred.append(event)
                continue

            folder_value = event.get("folder")
            if not folder_value:
                failed += 1
                log_error(
                    "Pominięto zakup – brak ścieżki folderu",
                    component="COMMANDER",
                    commander_id=self.player.id,
                    event=event,
                )
                continue

            bundle_path = Path(folder_value)
            blueprint_path = bundle_path / "token.json"

            try:
                with open(blueprint_path, "r", encoding="utf-8") as blueprint_file:
                    blueprint = json.load(blueprint_file)
            except FileNotFoundError:
                failed += 1
                log_error(
                    "Pominięto zakup – brak token.json",
                    component="COMMANDER",
                    commander_id=self.player.id,
                    folder=str(bundle_path),
                )
                continue
            except json.JSONDecodeError as exc:
                failed += 1
                log_error(
                    "Pominięto zakup – uszkodzony token.json",
                    component="COMMANDER",
                    commander_id=self.player.id,
                    folder=str(bundle_path),
                    error=str(exc),
                )
                continue

            token_id = blueprint.get("id") or event.get("token_id")
            if not token_id:
                failed += 1
                log_error(
                    "Pominięto zakup – brak identyfikatora żetonu",
                    component="COMMANDER",
                    commander_id=self.player.id,
                    folder=str(bundle_path),
                )
                continue

            if token_id in existing_ids:
                log_commander(
                    "Zignorowano duplikat zamówienia",
                    level="DEBUG",
                    commander_id=self.player.id,
                    token_id=token_id,
                )
                continue

            supports = blueprint.get("support_upgrades") or blueprint.get("supports") or []
            if "supports" not in blueprint:
                blueprint["supports"] = supports

            order = {
                "token_id": token_id,
                "token_blueprint": blueprint,
                "unit_type": blueprint.get("unitType"),
                "unit_size": blueprint.get("unitSize", "Pluton"),
                "quality": blueprint.get("quality", "standard"),
                "upgrades": supports,
                "priority": event.get("weight", 0),
                "cost": int(event.get("cost") or blueprint.get("price") or 0),
                "source": "general_purchase",
                "category": event.get("category"),
                "focus": event.get("focus"),
                "folder": str(bundle_path),
                "image": blueprint.get("image"),
            }

            if order["cost"] <= 0:
                order["cost"] = int(blueprint.get("price") or 0)

            queue.append(order)
            existing_ids.add(token_id)
            accepted += 1

            log_commander(
                "Dodano zamówienie z zakupów generała",
                level="INFO",
                commander_id=self.player.id,
                token_id=token_id,
                cost=order["cost"],
                priority=order["priority"],
                category=order.get("category"),
                focus=order.get("focus"),
            )

        setattr(self.player, "ai_purchase_events", deferred)

        if accepted or failed:
            log_commander(
                "Podsumowanie importu zakupów",
                level="DEBUG",
                commander_id=self.player.id,
                imported=accepted,
                failed=failed,
                remaining=len(deferred),
            )

    def _get_reinforcement_queue(self) -> List[Dict[str, Any]]:
        queue = getattr(self.player, "ai_reinforcement_queue", None)
        if queue is None:
            queue = []
            setattr(self.player, "ai_reinforcement_queue", queue)
        return queue

    def _iter_reinforcement_orders(self, queue: List[Dict[str, Any]]):
        indexed = list(enumerate(queue))
        indexed.sort(key=lambda item: (-int(item[1].get("priority", 0)), item[0]))
        for _, order in indexed:
            yield order

    def _normalize_reinforcement_order(self, order: Dict[str, Any]) -> Tuple[Optional[Dict[str, Any]], Optional[str]]:
        if not isinstance(order, dict):
            return None, "invalid_order_format"

        priority = order.get("priority")
        if not isinstance(priority, (int, float)):
            order["priority"] = 0

        sequence = getattr(self.player, "ai_reinforcement_sequence", 0)
        if "order_id" not in order:
            sequence += 1
            setattr(self.player, "ai_reinforcement_sequence", sequence)
            order["order_id"] = f"order_{self.player.id}_{sequence}"

        blueprint = order.get("token_blueprint")
        unit_type = order.get("unit_type") or (blueprint.get("unitType") if isinstance(blueprint, dict) else None)
        unit_size = order.get("unit_size") or (blueprint.get("unitSize") if isinstance(blueprint, dict) else "Pluton")
        quality = order.get("quality", "standard")
        upgrades = order.get("upgrades", [])

        if not unit_type:
            return None, "missing_unit_type"

        if blueprint is None:
            blueprint = self._build_token_blueprint(unit_type, unit_size, upgrades, quality, order)
            if blueprint is None:
                return None, "blueprint_generation_failed"
            order["token_blueprint"] = blueprint

        cost = order.get("cost")
        if not isinstance(cost, (int, float)) or cost <= 0:
            price = blueprint.get("price")
            if not isinstance(price, (int, float)) or price <= 0:
                return None, "invalid_cost"
            cost = int(price)
            order["cost"] = cost

        order["unit_type"] = unit_type
        order["unit_size"] = unit_size
        order["quality"] = quality
        order["upgrades"] = self._sanitize_upgrades(unit_type, upgrades)

        return order, None

    def _build_token_blueprint(
        self,
        unit_type: str,
        unit_size: str,
        upgrades: List[str],
        quality: str,
        order: Dict[str, Any],
    ) -> Optional[Dict[str, Any]]:
        sanitized_upgrades = self._sanitize_upgrades(unit_type, upgrades)
        try:
            stats = compute_token(unit_type, unit_size, self.player.nation, sanitized_upgrades, quality=quality)
            names = build_unit_names(self.player.nation, unit_type, unit_size)
        except Exception as error:
            log_error(
                "Błąd budowy blueprintu żetonu",
                component="COMMANDER",
                commander_id=self.player.id,
                unit_type=unit_type,
                unit_size=unit_size,
                error=str(error),
            )
            return None

        token_id = order.get("token_id")
        if not token_id:
            token_id = self._generate_token_id(unit_type, unit_size)
            order["token_id"] = token_id

        legacy_price = base_price(unit_type, unit_size)
        price = max(stats.total_cost, legacy_price)

        blueprint = {
            "id": token_id,
            "nation": self.player.nation,
            "unitType": unit_type,
            "unitSize": unit_size,
            "move": stats.movement,
            "combat_value": stats.combat_value,
            "defense_value": stats.defense_value,
            "maintenance": stats.maintenance,
            "price": price,
            "sight": stats.sight,
            "attack": {"range": stats.attack_range, "value": stats.attack_value},
            "label": names.get("label"),
            "unit_full_name": names.get("unit_full_name"),
            "quality": quality,
            "supports": sanitized_upgrades,
            "image": order.get("image", ""),
            "shape": order.get("shape", ""),
            "w": order.get("w", 0),
            "h": order.get("h", 0),
        }
        return blueprint

    def _generate_token_id(self, unit_type: str, unit_size: str) -> str:
        sequence = getattr(self.player, "ai_spawn_sequence", 0) + 1
        setattr(self.player, "ai_spawn_sequence", sequence)
        nation_code = self._sanitize_code(self.player.nation)
        size_code = self._sanitize_code(unit_size)[:3] or "SZ"
        return f"{unit_type}_{size_code}_{nation_code}_{self.player.id}_{sequence}"

    def _sanitize_code(self, text: str) -> str:
        normalized = unicodedata.normalize("NFKD", text or "")
        return "".join(ch for ch in normalized if ch.isalnum()).upper()

    def _sanitize_upgrades(self, unit_type: str, upgrades: Any) -> List[str]:
        if not isinstance(upgrades, (list, tuple)):
            return []
        allowed = set(ALLOWED_SUPPORT.get(unit_type, []))
        return [upgrade for upgrade in upgrades if upgrade in allowed]

    def _collect_spawn_candidates(self, board, game_engine) -> List[Tuple[int, int]]:
        spawn_points = getattr(board, "spawn_points", {})
        if not isinstance(spawn_points, dict):
            return []

        possible_keys = [self.player.nation, str(self.player.nation).lower(), str(self.player.nation).upper()]
        raw_points = None
        for key in possible_keys:
            if key in spawn_points:
                raw_points = spawn_points[key]
                break

        if not raw_points:
            return []

        candidates: List[Tuple[int, int]] = []
        for entry in raw_points:
            if isinstance(entry, str) and "," in entry:
                try:
                    q, r = [int(part.strip()) for part in entry.split(",", 1)]
                except ValueError:
                    continue
            elif isinstance(entry, (list, tuple)) and len(entry) >= 2:
                try:
                    q, r = int(entry[0]), int(entry[1])
                except (TypeError, ValueError):
                    continue
            else:
                continue

            if not self._is_hex_occupied(board, q, r, game_engine):
                candidates.append((q, r))

        return candidates

    def _is_hex_occupied(self, board, q: int, r: int, game_engine) -> bool:
        if hasattr(board, "is_occupied"):
            try:
                if board.is_occupied(q, r):
                    return True
            except TypeError:
                pass

        for token in getattr(game_engine, "tokens", []):
            if getattr(token, "q", None) == q and getattr(token, "r", None) == r:
                return True
        return False

    def _select_spawn_hex(self, candidates: List[Tuple[int, int]], order: Dict[str, Any], game_engine) -> Optional[Tuple[int, int]]:
        if not candidates:
            return None
        return candidates[0]

    def _spawn_token_from_blueprint(self, game_engine, blueprint: Dict[str, Any], position: Tuple[int, int]) -> Optional[Token]:
        try:
            token_data = dict(blueprint)
            owner = f"{self.player.id} ({self.player.nation})"
            token_data["owner"] = owner
            token = Token.from_json(token_data)
            token.set_position(position[0], position[1])
            token.owner = owner
            token.apply_movement_mode(reset_mp=True)
            token.currentFuel = getattr(token, "maxFuel", getattr(token, "currentFuel", 0))
        except Exception as error:
            log_error(
                "Błąd tworzenia żetonu wzmocnienia",
                component="COMMANDER",
                commander_id=self.player.id,
                error=str(error),
            )
            return None

        game_engine.tokens.append(token)
        if hasattr(game_engine, "board") and hasattr(game_engine.board, "set_tokens"):
            game_engine.board.set_tokens(game_engine.tokens)

        players = getattr(game_engine, "players", None)
        if players is not None:
            if hasattr(game_engine, "update_all_players_visibility"):
                try:
                    game_engine.update_all_players_visibility(players)
                except Exception:
                    pass
            else:
                try:
                    from engine.engine import update_all_players_visibility as _update_visibility

                    _update_visibility(players, game_engine.tokens, game_engine.board)
                except Exception:
                    pass

        return token

    def _apply_reinforcement_spend(self, spent: int) -> int:
        economy = getattr(self.player, "economy", None)
        if economy is None:
            economy = EconomySystem()
            self.player.economy = economy

        economy.subtract_points(spent)
        remaining = economy.get_points().get("economic_points", 0)
        setattr(self.player, "punkty_ekonomiczne", remaining)
        return remaining

    def _append_reinforcement_history(
        self,
        token: Token,
        cost: int,
        order: Dict[str, Any],
        position: Tuple[int, int],
        game_engine,
    ) -> None:
        history = getattr(self.player, "ai_reinforcement_history", None)
        if history is None:
            history = []
            setattr(self.player, "ai_reinforcement_history", history)

        history.append(
            {
                "turn": getattr(game_engine, "turn", None),
                "token_id": getattr(token, "id", None),
                "unit_type": order.get("unit_type"),
                "unit_size": order.get("unit_size"),
                "cost": cost,
                "position": {"q": position[0], "r": position[1]},
                "source": order.get("source"),
            }
        )

    def _remove_processed_orders(self, queue: List[Dict[str, Any]], processed: List[Dict[str, Any]]) -> None:
        if not processed:
            return
        queue[:] = [order for order in queue if order not in processed]

    # ------------------------------------------------------------------
    # Pomocnicze
    # ------------------------------------------------------------------
    def _my_tokens(self, game_engine) -> List:
        expected_owner = f"{self.player.id} ({self.player.nation})"
        owned = []
        for token in getattr(game_engine, "tokens", []):
            owner = getattr(token, "owner", "") or ""
            if owner == expected_owner:
                owned.append(token)
        return owned

    def _collect_support_needs(self, tokens: List) -> Dict[str, int]:
        fuel_need = 0
        repair_need = 0

        for token in tokens:
            fuel_current = getattr(token, "fuel", None)
            fuel_max = getattr(token, "maxFuel", None)
            if isinstance(fuel_current, (int, float)) and isinstance(fuel_max, (int, float)):
                if fuel_current < fuel_max:
                    fuel_need += fuel_max - fuel_current

            cv_current = getattr(token, "currentCombatStrength", None)
            cv_max = getattr(token, "maxCombatStrength", None)
            if isinstance(cv_current, (int, float)) and isinstance(cv_max, (int, float)):
                if cv_current < cv_max:
                    repair_need += cv_max - cv_current

        return {
            "fuel": int(fuel_need),
            "repair": int(repair_need),
        }

    def _sync_player_points(self) -> int:
        economy = getattr(self.player, "economy", None)
        if economy is None:
            economy = EconomySystem()
            self.player.economy = economy
        total = economy.get_points().get("economic_points", 0)
        setattr(self.player, "punkty_ekonomiczne", total)
        return total

    def _update_player_points(self, value: int) -> None:
        setattr(self.player, "punkty_ekonomiczne", value)
        if getattr(self.player, "economy", None) is not None:
            self.player.economy.economic_points = value