# -*- coding: utf-8 -*-
"""
StrategicAgent – agent generała AI.
Odpowiada za priorytety key points, alokację ekonomii i zakupy jednostek.

Strategia (Faza 5 / Iteracja 1):
  1. Przeanalizuj key pointy – znajdź pilne do obrony lub przejęcia.
  2. Zaplanuj zakupy jeśli budżet na to pozwala (stub – Faza 6).
  3. Wygeneruj dyrektywę taktyczną dla dowódców (klucz 'directive').
"""

import math
from typing import Any, Dict, List, Optional

from .base_agent import BaseAgent
from .decision_queue import DecisionQueue
from .evaluator import Evaluator


class StrategicAgent(BaseAgent):
    """
    Agent generała AI – zarządza strategią i ekonomią.

    Decyzje:
    - 'directive' – priorytety dla dowódców (key pointy do zajęcia)
    - 'purchase'  – zlecenie zakupu jednostki przez silnik (Faza 6)
    """

    def __init__(
        self,
        player_id: Any,
        nation: str,
        difficulty: str = "normal",
        seed: Optional[int] = None,
    ):
        super().__init__(player_id, nation, difficulty, seed)
        self._evaluator = Evaluator()
        self._queue = DecisionQueue()

    # ------------------------------------------------------------------
    # Główna metoda decyzyjna
    # ------------------------------------------------------------------

    def decide(self, state: Dict[str, Any]) -> List[Dict]:
        """
        Wygeneruj listę akcji / dyrektyw dla bieżącego stanu gry.

        Parametry:
            state – słownik stanu (z StateAdapter.extract)

        Zwraca:
            Lista akcji: [{"type": "directive", ...}, {"type": "purchase", ...}]
        """
        self._queue.clear()

        # 1. Wydaj dyrektywy taktyczne oparte na analizie key pointów
        directives = self._generate_directives(state)
        self._queue.add_all(directives)

        # 2. Zakupy (stub – pełna implementacja w Fazie 6)
        purchase = self._plan_purchase(state)
        if purchase:
            self._queue.add(purchase)

        return self._queue.pop_all()

    # ------------------------------------------------------------------
    # Dyrektywy
    # ------------------------------------------------------------------

    def _generate_directives(self, state: Dict[str, Any]) -> List[Dict]:
        """Ustal priorytety key pointów i wyemituj dyrektywy."""
        directives = []
        urgent_kps = self._find_urgent_key_points(state)

        for kp in urgent_kps:
            directives.append(
                {
                    "type": "directive",
                    "target_q": kp["q"],
                    "target_r": kp["r"],
                    "kp_type": kp.get("type"),
                    "turns_left": kp.get("turns_left"),
                    "priority": kp.get("urgency_score", 0),
                }
            )
        return directives

    def _find_urgent_key_points(self, state: Dict[str, Any]) -> List[Dict]:
        """
        Zwróć key pointy posortowane wg pilności (mniej tur życia = pilniejszy).
        """
        result = []
        for kp in state.get("key_points", []):
            initial = kp.get("initial") or 1
            current = kp.get("current") or 0
            turns_left = math.ceil(current / max(1, 0.1 * initial))
            type_weight = {
                "city": 3,
                "supply": 2,
                "crossroads": 1,
            }.get(kp.get("type"), 1)
            urgency_score = type_weight * 10 - turns_left
            result.append(
                {
                    **kp,
                    "turns_left": turns_left,
                    "urgency_score": urgency_score,
                }
            )
        result.sort(key=lambda k: k["urgency_score"], reverse=True)
        return result

    # ------------------------------------------------------------------
    # Zakupy (stub)
    # ------------------------------------------------------------------

    def _plan_purchase(self, state: Dict[str, Any]) -> Optional[Dict]:
        """
        Planowanie zakupów – stub do implementacji w Fazie 6.

        Gdy API zakupów (engine.purchase_unit) będzie gotowe, tu trafia
        logika wyboru jednostki i miejsca spawnu.
        """
        # TODO: Faza 6 – zaimplementuj zakupy przez engine.purchase_unit
        return None
