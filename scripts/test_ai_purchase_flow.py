"""Quick headless smoke test verifying AI purchase and deployment flow."""
from __future__ import annotations

from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from engine.engine import GameEngine, update_all_players_visibility
from engine.player import Player
from core.ekonomia import EconomySystem
from ai.general.general_ai import GeneralAI
from ai.commander.commander_ai import CommanderAI


def run_smoke_test(seed: int = 42) -> dict:
    engine = GameEngine(
        map_path="data/map_data.json",
        tokens_index_path="assets/tokens/index.json",
        tokens_start_path="assets/start_tokens.json",
        seed=seed,
        read_only=True,
    )

    initial_tokens = {token.id for token in engine.tokens}

    players = [
        Player(4, "Niemcy", "Generał", 5),
        Player(5, "Niemcy", "Dowódca", 5),
        Player(6, "Niemcy", "Dowódca", 5),
    ]

    for player in players:
        player.is_ai = True
        player.is_ai_commander = player.role == "Dowódca"
        player.economy = EconomySystem()

    engine.players = players
    update_all_players_visibility(players, engine.tokens, engine.board)

    general = GeneralAI(players[0])
    general.execute_turn(players, engine)

    purchases = getattr(players[0], "ai_purchase_events", [])
    queues_before = [len(getattr(player, "ai_reinforcement_queue", [])) for player in players]

    for commander in players[1:]:
        CommanderAI(commander).execute_turn(engine)

    queues_after = [len(getattr(player, "ai_reinforcement_queue", [])) for player in players]

    final_tokens = {token.id for token in engine.tokens}
    new_tokens = sorted(final_tokens - initial_tokens)

    result = {
        "purchase_events": purchases,
        "queue_before": queues_before,
        "queue_after": queues_after,
        "tokens_total_before": len(initial_tokens),
        "tokens_total_after": len(final_tokens),
        "tokens_new": new_tokens,
    }
    return result


if __name__ == "__main__":
    summary = run_smoke_test()
    print("AI purchase events:", len(summary["purchase_events"]))
    for event in summary["purchase_events"]:
        print("  •", event)
    print("Commander queue before deploy:", summary["queue_before"])
    print("Commander queue after deploy:", summary["queue_after"])
    print("Tokens before/after:", summary["tokens_total_before"], "->", summary["tokens_total_after"])
    print("New tokens spawned:", summary["tokens_new"])
