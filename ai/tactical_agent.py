# -*- coding: utf-8 -*-
"""
TacticalAgent – agent dowódcy AI.
Odpowiada za decyzje ruchu i walki (tryb 'dowódca').

Strategia (Faza 3 / Iteracja 1):
  1. Dla każdego własnego żetonu dobierz najlepszy cel ruchu (key point lub
     wróg w zasięgu).
  2. Jeśli wróg jest w zasięgu ataku – zakolejkuj akcję walki.
  3. Filtruj akcje: nie atakuj jeśli przewidywane straty > progu.
"""

import random
from typing import Any, Dict, List, Optional

from .base_agent import BaseAgent
from .decision_queue import DecisionQueue
from .evaluator import Evaluator, _hex_distance


class TacticalAgent(BaseAgent):
    """
    Agent dowódcy AI – kieruje jednostkami na polu bitwy.

    Używa Evaluatora do oceny potencjalnych ruchów i ataków,
    a DecisionQueue do kolejkowania i priorytetyzacji akcji.
    """

    def __init__(
        self,
        player_id: Any,
        nation: str,
        difficulty: str = "normal",
        seed: Optional[int] = None,
    ):
        super().__init__(player_id, nation, difficulty, seed)
        self._rng = random.Random(seed)
        self._evaluator = Evaluator(self._difficulty_weights(difficulty))
        self._queue = DecisionQueue()

    # ------------------------------------------------------------------
    # Główna metoda decyzyjna
    # ------------------------------------------------------------------

    def decide(self, state: Dict[str, Any]) -> List[Dict]:
        """
        Wygeneruj listę akcji dla bieżącego stanu gry.

        Parametry:
            state – słownik stanu (z StateAdapter.extract)

        Zwraca:
            Lista akcji: [{"type": ..., ...}, ...]
        """
        self._queue.clear()

        for token in state.get("self_tokens", []):
            # Wybierz najlepszy cel ruchu
            move_action = self._best_move(token, state)
            if move_action:
                self._queue.add(move_action)

            # Sprawdź czy możliwy atak
            attack_action = self._best_attack(token, state)
            if attack_action:
                self._queue.add(attack_action)

        return self._queue.pop_all()

    # ------------------------------------------------------------------
    # Dobór ruchu
    # ------------------------------------------------------------------

    def _best_move(
        self, token: Dict, state: Dict
    ) -> Optional[Dict]:
        """Wybierz najlepsze pole docelowe dla żetonu."""
        candidates = self._generate_move_candidates(token, state)
        if not candidates:
            return None

        best = max(
            candidates,
            key=lambda c: self._evaluator.score_move(
                token,
                c["dest_q"],
                c["dest_r"],
                state,
                move_cost=c.get("cost", 1),
            ),
        )
        return {
            "type": "move",
            "token_id": token["id"],
            "dest_q": best["dest_q"],
            "dest_r": best["dest_r"],
        }

    def _generate_move_candidates(
        self, token: Dict, state: Dict
    ) -> List[Dict]:
        """
        Zbuduj listę kandydatów do ruchu: key pointy + pozycje wrogów.
        W iteracji startowej: uproszczone bez pełnego A* (stub).
        """
        candidates = []

        # Kieruj się ku key pointom
        for kp in state.get("key_points", []):
            candidates.append(
                {"dest_q": kp["q"], "dest_r": kp["r"], "cost": 1}
            )

        # Kieruj się ku widocznym wrogom
        for enemy in state.get("enemy_visible", []):
            candidates.append(
                {"dest_q": enemy["q"], "dest_r": enemy["r"], "cost": 1}
            )

        # Przefiltruj kandydatów zbyt odległych (powyżej MP żetonu)
        mp = token.get("mp", 0)
        candidates = [
            c
            for c in candidates
            if _hex_distance(token["q"], token["r"], c["dest_q"], c["dest_r"])
            <= mp
        ]

        return candidates

    # ------------------------------------------------------------------
    # Dobór ataku
    # ------------------------------------------------------------------

    def _best_attack(
        self, token: Dict, state: Dict
    ) -> Optional[Dict]:
        """Wybierz najlepszego wroga do ataku (jeśli w zasięgu)."""
        atk_range = token.get("rng", 1)
        reachable_enemies = [
            e
            for e in state.get("enemy_visible", [])
            if _hex_distance(token["q"], token["r"], e["q"], e["r"]) <= atk_range
        ]

        if not reachable_enemies:
            return None

        # Filtruj według opłacalności
        viable = [
            e
            for e in reachable_enemies
            if self._evaluator.should_attack(token, e)
        ]
        if not viable:
            return None

        best_target = max(
            viable,
            key=lambda e: self._evaluator.score_attack(token, e),
        )
        return {
            "type": "combat",
            "attacker_id": token["id"],
            "defender_id": best_target["id"],
        }

    # ------------------------------------------------------------------
    # Konfiguracja wag według trudności
    # ------------------------------------------------------------------

    @staticmethod
    def _difficulty_weights(difficulty: str) -> Dict:
        overrides: Dict[str, Dict] = {
            "easy": {"max_loss_ratio": 0.3, "offense_value_ratio": 1.0},
            "normal": {},
            "hard": {"max_loss_ratio": 0.7, "offense_value_ratio": 0.6},
        }
        return overrides.get(difficulty, {})
