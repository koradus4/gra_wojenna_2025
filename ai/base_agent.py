# -*- coding: utf-8 -*-
"""
Klasy bazowe / interfejsy dla modułu AI.
Wszystkie agenty dziedziczą po BaseAgent.
"""

from abc import ABC, abstractmethod
from typing import List, Optional, Any


class BaseAgent(ABC):
    """
    Klasa bazowa dla agentów AI.

    Atrybuty:
        player_id  – identyfikator gracza (str lub int)
        nation     – nacja gracza ('Polska' lub 'Niemcy')
        difficulty – poziom trudności ('easy', 'normal', 'hard')
        seed       – opcjonalny seed dla deterministycznych decyzji
    """

    def __init__(
        self,
        player_id: Any,
        nation: str,
        difficulty: str = "normal",
        seed: Optional[int] = None,
    ):
        self.player_id = player_id
        self.nation = nation
        self.difficulty = difficulty
        self.seed = seed

    @abstractmethod
    def decide(self, state: dict) -> List[dict]:
        """
        Na podstawie stanu gry (state) zwróć listę akcji do wykonania.

        Parametry:
            state – słownik opisujący bieżący stan gry (format z StateAdapter)

        Zwraca:
            Lista słowników akcji, np.:
            [{"type": "move", "token_id": "P_INF_1", "dest_q": 3, "dest_r": 0}]
        """
        ...

    def reset(self):
        """Zresetuj stan wewnętrzny agenta (np. przed nową grą)."""
        pass

    def __repr__(self) -> str:
        return (
            f"{self.__class__.__name__}("
            f"player_id={self.player_id!r}, "
            f"nation={self.nation!r}, "
            f"difficulty={self.difficulty!r})"
        )
