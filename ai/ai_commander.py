"""AI Commander – stub implementacyjny (MVP-0 / sekcja 26 planu)

Docelowo: pełny pipeline taktyczny (gather_state -> objectives -> plan -> execute).
Na ten moment: NO_OP dla integracji pętli gry.
"""

from __future__ import annotations
from typing import Any


class AICommander:
	def __init__(self, player: Any):
		self.player = player

	def pre_resupply(self, game_engine: Any) -> None:
		"""Miejsce na algorytm z sekcji 22 (aktualnie pomijamy)."""
		# Placeholder – brak implementacji w MVP-0
		pass

	def make_tactical_turn(self, game_engine: Any) -> None:
		"""Wykonaj turę taktyczną (aktualnie NO_OP)."""
		print(f"[AICommander] NO_OP turn for commander {self.player.id} ({self.player.nation})")

	# Rezerwacja przyszłych metod (dla czytelności planu / unikanie refaktoru nazw)
	def _gather_state(self, game_engine: Any):  # pragma: no cover - jeszcze nieużywane
		return {}

	def _generate_objectives(self, state: dict):  # pragma: no cover - placeholder
		return []

	def _score_objectives(self, state: dict, objectives: list):  # pragma: no cover
		return []

	def _build_plan(self, scored: list):  # pragma: no cover
		return []

	def _execute_plan(self, plan: list, game_engine: Any):  # pragma: no cover
		pass

