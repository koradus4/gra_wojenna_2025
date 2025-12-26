#!/usr/bin/env python3
"""Headless launcher do sesji AI vs AI.

Skrypt przygotowuje środowisko, opcjonalnie czyści logi AI,
po czym uruchamia pełną sesję z generałami oraz dowódcami sterowanymi przez AI.
"""
from __future__ import annotations

import argparse
import subprocess
import sys
from pathlib import Path
from typing import Dict

PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from core.tura import TurnManager
from core.ekonomia import EconomySystem
from core.zwyciestwo import VictoryConditions
from engine.player import Player
from engine.engine import (
    GameEngine,
    update_all_players_visibility,
    clear_temp_visibility,
)
from ai import GeneralAI, CommanderAI


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Uruchamia autonomiczną sesję AI vs AI w trybie bez GUI.",
    )
    parser.add_argument(
        "--turns",
        type=int,
        default=10,
        help="Liczba pełnych tur do rozegrania (domyślnie: 10)",
    )
    parser.add_argument(
        "--victory",
        choices=["turns", "elimination"],
        default="turns",
        help="Tryb zwycięstwa (domyślnie: turns)",
    )
    parser.add_argument(
        "--skip-clean",
        action="store_true",
        help="Pomiń czyszczenie logów AI przed startem",
    )
    parser.add_argument(
        "--seed",
        type=int,
        default=42,
        help="Ziarno RNG dla GameEngine (domyślnie: 42)",
    )
    return parser.parse_args()


def clean_ai_logs(project_root: Path) -> None:
    """Uruchamia skrypt czyszczący logi AI (jeśli istnieje)."""
    cleaner = project_root / "ai" / "logs" / "czyszczenie_logow.py"
    if not cleaner.exists():
        print("⚠️ Nie znaleziono skryptu czyszczenia logów AI – pomijam ten krok.")
        return

    print("🧹 Czyszczę logi AI (tryb --all)...")
    result = subprocess.run([sys.executable, str(cleaner), "--all"], cwd=project_root)
    if result.returncode == 0:
        print("✅ Logi AI zostały wyczyszczone.")
    else:
        print(f"⚠️ Czyszczenie logów AI zakończyło się kodem {result.returncode} – kontynuuję dalej.")


def build_players() -> list[Player]:
    """Tworzy listę sześciu graczy (Generał + 2 Dowódców na stronę)."""
    config = [
        (1, "Polska", "Generał"),
        (2, "Polska", "Dowódca"),
        (3, "Polska", "Dowódca"),
        (4, "Niemcy", "Generał"),
        (5, "Niemcy", "Dowódca"),
        (6, "Niemcy", "Dowódca"),
    ]
    players: list[Player] = []
    for player_id, nation, role in config:
        player = Player(player_id, nation, role, time_limit=5, economy=EconomySystem())
        player.is_ai = True
        players.append(player)
    return players


def run_session(turns: int, victory_mode: str, skip_clean: bool, seed: int) -> None:
    if not skip_clean:
        clean_ai_logs(PROJECT_ROOT)

    print("🧠 Inicjalizacja silnika gry...")
    engine = GameEngine(
        map_path="data/map_data.json",
        tokens_index_path="assets/tokens/index.json",
        tokens_start_path="assets/start_tokens.json",
        seed=seed,
        read_only=True,
    )

    players = build_players()
    engine.players = players
    update_all_players_visibility(players, engine.tokens, engine.board)

    generals: Dict[int, GeneralAI] = {p.id: GeneralAI(p) for p in players if p.role == "Generał"}
    commanders: Dict[int, CommanderAI] = {p.id: CommanderAI(p) for p in players if p.role == "Dowódca"}

    turn_manager = TurnManager(players, game_engine=engine)
    victory = VictoryConditions(max_turns=turns, victory_mode=victory_mode)

    full_turns_completed = 0

    print("🚀 Start sesji AI vs AI")
    print("=" * 80)

    while True:
        current_player = turn_manager.get_current_player()
        print("\n" + "=" * 80)
        print(
            f"🕒 Tura {turn_manager.current_turn} – {current_player.nation} {current_player.role} (id={current_player.id})"
        )
        try:
            engine.log_key_points_status(current_player)
        except Exception as exc:
            print(f"⚠️ Nie udało się zalogować stanu key pointów: {exc}")

        if current_player.role == "Generał":
            generals[current_player.id].execute_turn(players, engine)
        elif current_player.role == "Dowódca":
            commanders[current_player.id].execute_turn(engine)
        else:
            print(f"⚠️ Nieobsługiwana rola gracza: {current_player.role}")

        update_all_players_visibility(players, engine.tokens, engine.board)

        full_cycle_completed = turn_manager.next_turn()

        if full_cycle_completed:
            full_turns_completed += 1
            print(f"\n🔄 Zakończono pełną turę #{full_turns_completed}")
            try:
                engine.process_key_points(players)
            except Exception as exc:
                print(f"⚠️ Błąd podczas przetwarzania key pointów: {exc}")
            engine.update_all_players_visibility(players)
            clear_temp_visibility(players)

        if victory.check_game_over(turn_manager.current_turn, players):
            print("\n" + "=" * 80)
            print("🏁 " + victory.get_victory_message())
            break

        if full_turns_completed >= turns:
            print("\n✅ Osiągnięto zaplanowaną liczbę pełnych tur – kończę sesję.")
            break

    info = victory.get_victory_info()
    print("=" * 80)
    print("📊 Podsumowanie sesji AI:")
    print(f"   • Tryb zwycięstwa: {info['victory_mode']}")
    print(f"   • Limit tur: {info['max_turns']}")
    print(f"   • Ukończone pełne tury: {full_turns_completed}")
    if info.get("winner_nation"):
        print(f"   • Zwycięzca: {info['winner_nation']}")
    if info.get("victory_reason"):
        print(f"   • Powód zakończenia: {info['victory_reason']}")
    print("=" * 80)


def main() -> None:
    args = parse_args()
    run_session(
        turns=args.turns,
        victory_mode=args.victory,
        skip_clean=args.skip_clean,
        seed=args.seed,
    )


if __name__ == "__main__":
    main()
