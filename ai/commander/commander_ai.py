"""
Minimalna implementacja AI komendanta.

Komendant dzieli dostępne PE po równo między podległe żetony, a każdy
żeton działa według własnej, uproszczonej logiki TokenAI. Niewykorzystane
punkty wracają do puli dowódcy na koniec tury.
"""
from __future__ import annotations

from typing import List

from ai.logs import log_commander
from ai.tokens import create_token_ai
from core.ekonomia import EconomySystem


class CommanderAI:
    def __init__(self, player):
        self.player = player

    def execute_turn(self, game_engine) -> None:
        tokens = self._my_tokens(game_engine)
        total_pe = self._sync_player_points()

        log_commander(
            "Start tury komendanta",
            level="INFO",
            commander_id=self.player.id,
            nation=self.player.nation,
            tokens=len(tokens),
            budget=total_pe,
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
        )

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