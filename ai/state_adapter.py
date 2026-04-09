# -*- coding: utf-8 -*-
"""
StateAdapter – ekstrahuje stan z GameEngine i przekształca go do struktury
czytelnej dla agentów AI.

Format wyjściowy (uproszczony JSON):
{
  "turn": 7,
  "player": {"id": 2, "role": "dowódca", "nation": "Polska"},
  "economy": {"points": 40},
  "key_points": [{"q": 3, "r": -1, "type": "city", "current": 70, "ours": True}],
  "self_tokens": [{"id": "P_INF_1", "q": 3, "r": 0, "cv": 5, "mp": 5, ...}],
  "enemy_visible": [{"id": "N_TANK_2", "q": 5, "r": 0, "cv": 8, "rng": 1}],
  "map": {"cols": X, "rows": Y}
}
"""

from typing import Any, Dict, List, Optional


class StateAdapter:
    """Konwertuje stan GameEngine na uproszczoną strukturę danych dla AI."""

    def extract(
        self,
        engine: Any,
        player: Any,
        visible_tokens: Optional[List[Any]] = None,
    ) -> Dict[str, Any]:
        """
        Zbuduj słownik stanu dla danego gracza.

        Parametry:
            engine         – instancja GameEngine
            player         – instancja Player (dowódca lub generał)
            visible_tokens – opcjonalna lista widzialnych żetonów (jeśli None,
                             używa player.visible_tokens gdy dostępne)

        Zwraca:
            Słownik stanu zgodny z formatem opisanym w STRUKTURA_PROJEKTU.md
        """
        if visible_tokens is None:
            visible_tokens = getattr(player, "visible_tokens", [])

        state: Dict[str, Any] = {
            "turn": engine.turn,
            "player": self._extract_player(player),
            "economy": self._extract_economy(player),
            "key_points": self._extract_key_points(engine, player),
            "self_tokens": self._extract_self_tokens(engine, player),
            "enemy_visible": self._extract_enemy_tokens(engine, player, visible_tokens),
            "map": self._extract_map(engine),
        }
        return state

    # ------------------------------------------------------------------
    # Pomocnicze metody prywatne
    # ------------------------------------------------------------------

    def _extract_player(self, player: Any) -> Dict[str, Any]:
        return {
            "id": getattr(player, "id", None),
            "role": getattr(player, "role", None),
            "nation": getattr(player, "nation", None),
        }

    def _extract_economy(self, player: Any) -> Dict[str, Any]:
        return {
            "points": getattr(player, "economic_points", 0),
        }

    def _extract_key_points(self, engine: Any, player: Any) -> List[Dict[str, Any]]:
        nation = getattr(player, "nation", None)
        result = []
        kps = getattr(engine, "key_points_state", {})
        for hex_id, kp in kps.items():
            try:
                q, r = map(int, hex_id.split(","))
            except ValueError:
                continue
            # Sprawdź czy key point jest nasz (na podstawie spawn_nation kafelka)
            tile = engine.board.get_tile(q, r)
            ours = (
                tile is not None
                and getattr(tile, "spawn_nation", None) == nation
            )
            result.append(
                {
                    "q": q,
                    "r": r,
                    "type": kp.get("type"),
                    "current": kp.get("current_value"),
                    "initial": kp.get("initial_value"),
                    "ours": ours,
                }
            )
        return result

    def _extract_self_tokens(self, engine: Any, player: Any) -> List[Dict[str, Any]]:
        player_id = getattr(player, "id", None)
        nation = getattr(player, "nation", None)
        result = []
        for token in engine.tokens:
            if not self._token_belongs_to(token, player_id, nation):
                continue
            result.append(self._token_to_dict(token))
        return result

    def _extract_enemy_tokens(
        self,
        engine: Any,
        player: Any,
        visible_tokens: List[Any],
    ) -> List[Dict[str, Any]]:
        player_id = getattr(player, "id", None)
        nation = getattr(player, "nation", None)
        visible_ids = {getattr(t, "id", None) for t in visible_tokens}
        result = []
        for token in engine.tokens:
            if self._token_belongs_to(token, player_id, nation):
                continue
            if token.id not in visible_ids:
                continue
            result.append(self._token_to_dict(token))
        return result

    def _extract_map(self, engine: Any) -> Dict[str, Any]:
        board = engine.board
        return {
            "cols": getattr(board, "cols", None),
            "rows": getattr(board, "rows", None),
        }

    # ------------------------------------------------------------------

    @staticmethod
    def _token_belongs_to(token: Any, player_id: Any, nation: Optional[str]) -> bool:
        owner = getattr(token, "owner", "")
        if player_id is not None and str(player_id) in str(owner):
            return True
        if nation and nation in str(owner):
            return True
        return False

    @staticmethod
    def _token_to_dict(token: Any) -> Dict[str, Any]:
        stats = getattr(token, "stats", {})
        atk = stats.get("attack", 0)
        atk_value = atk.get("value", 0) if isinstance(atk, dict) else atk
        atk_range = atk.get("range", 1) if isinstance(atk, dict) else 1
        return {
            "id": token.id,
            "q": token.q,
            "r": token.r,
            "cv": getattr(token, "combat_value", stats.get("combat_value", 0)),
            "dv": stats.get("defense_value", 0),
            "mp": getattr(token, "currentMovePoints", stats.get("move", 0)),
            "max_mp": getattr(token, "maxMovePoints", stats.get("move", 0)),
            "fuel": getattr(token, "currentFuel", stats.get("maintenance", 0)),
            "atk": atk_value,
            "rng": atk_range,
            "sight": stats.get("sight", 1),
            "price": stats.get("price", 0),
            "nation": stats.get("nation", ""),
            "movement_mode": getattr(token, "movement_mode", "combat"),
        }
