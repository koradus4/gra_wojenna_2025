# -*- coding: utf-8 -*-
"""
DecisionQueue – kolejkowanie i filtrowanie akcji AI przed przekazaniem
ich do silnika.

Każda akcja to słownik z kluczem 'type' i odpowiednimi polami, np.:
  {"type": "move",   "token_id": "P_INF_1", "dest_q": 3, "dest_r": 0}
  {"type": "combat", "attacker_id": "P_INF_1", "defender_id": "N_TANK_1"}
  {"type": "purchase", "blueprint_id": "infantry", "spawn_q": 0, "spawn_r": 0}
"""

from typing import Callable, Dict, List, Optional


class DecisionQueue:
    """Prosta kolejka akcji AI z obsługą filtrów i priorytetów."""

    # Wyższy priorytet = wcześniejsze wykonanie
    _DEFAULT_PRIORITY: Dict[str, int] = {
        "combat": 10,
        "move": 5,
        "purchase": 1,
    }

    def __init__(self):
        self._queue: List[Dict] = []

    # ------------------------------------------------------------------
    # Dodawanie akcji
    # ------------------------------------------------------------------

    def add(self, action: Dict, priority: Optional[int] = None) -> None:
        """
        Dodaj akcję do kolejki.

        Parametry:
            action   – słownik akcji (musi zawierać klucz 'type')
            priority – opcjonalny priorytet; jeśli None, używa domyślnego
        """
        if "type" not in action:
            raise ValueError("Akcja musi zawierać klucz 'type'.")
        action = dict(action)
        action["_priority"] = (
            priority
            if priority is not None
            else self._DEFAULT_PRIORITY.get(action["type"], 0)
        )
        self._queue.append(action)

    def add_all(self, actions: List[Dict]) -> None:
        """Dodaj wiele akcji naraz."""
        for action in actions:
            self.add(action)

    # ------------------------------------------------------------------
    # Pobieranie akcji
    # ------------------------------------------------------------------

    def pop_all(self) -> List[Dict]:
        """
        Zwróć wszystkie akcje posortowane malejąco według priorytetu
        i wyczyść kolejkę.
        """
        sorted_actions = sorted(
            self._queue, key=lambda a: a["_priority"], reverse=True
        )
        self._queue.clear()
        # Usuń wewnętrzne pole priorytetu przed zwróceniem
        for action in sorted_actions:
            action.pop("_priority", None)
        return sorted_actions

    def peek(self) -> List[Dict]:
        """Zwróć kopię kolejki bez modyfikowania jej (bez pola _priority)."""
        return [
            {k: v for k, v in a.items() if k != "_priority"}
            for a in sorted(self._queue, key=lambda a: a["_priority"], reverse=True)
        ]

    # ------------------------------------------------------------------
    # Filtrowanie
    # ------------------------------------------------------------------

    def filter(self, predicate: Callable[[Dict], bool]) -> None:
        """Usuń z kolejki akcje, dla których predicate zwraca False."""
        self._queue = [a for a in self._queue if predicate(a)]

    def remove_type(self, action_type: str) -> None:
        """Usuń wszystkie akcje danego typu."""
        self._queue = [a for a in self._queue if a.get("type") != action_type]

    # ------------------------------------------------------------------
    # Narzędzia
    # ------------------------------------------------------------------

    def clear(self) -> None:
        """Wyczyść kolejkę."""
        self._queue.clear()

    def __len__(self) -> int:
        return len(self._queue)

    def __bool__(self) -> bool:
        return bool(self._queue)

    def __repr__(self) -> str:
        return f"DecisionQueue({len(self._queue)} actions)"
