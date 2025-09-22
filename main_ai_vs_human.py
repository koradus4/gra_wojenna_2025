import sys
import os

# Umożliw import modułów z katalogu głównego
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

import argparse
from core.tura import TurnManager
from engine.player import Player
from gui.panel_generala import PanelGenerala
from gui.panel_dowodcy import PanelDowodcy
from core.ekonomia import EconomySystem
from engine.engine import GameEngine, update_all_players_visibility, clear_temp_visibility
from core.zwyciestwo import VictoryConditions
from ai.ai_general import AIGeneral
from ai.ai_commander import AICommander
from czyszczenie.game_cleaner import quick_clean as quick_clean_full


def build_players():
    """Buduje listę graczy w stałej kolejności slotów 1..6.
    Polska: id 1 (Generał), 2/3 (Dowódcy) – wszyscy HUMAN
    Niemcy: id 4 (Generał), 5/6 (Dowódcy) – wszyscy AI
    """
    miejsca = ["Polska", "Polska", "Polska", "Niemcy", "Niemcy", "Niemcy"]
    czasy = [5, 5, 5, 5, 5, 5]

    polska_gen = miejsca.index("Polska")
    polska_dow1 = miejsca.index("Polska", polska_gen + 1)
    polska_dow2 = miejsca.index("Polska", polska_dow1 + 1)
    niemcy_gen = miejsca.index("Niemcy")
    niemcy_dow1 = miejsca.index("Niemcy", niemcy_gen + 1)
    niemcy_dow2 = miejsca.index("Niemcy", niemcy_dow1 + 1)

    if niemcy_gen < polska_gen:
        players = [
            Player(4, "Niemcy", "Generał", czasy[niemcy_gen]),
            Player(5, "Niemcy", "Dowódca", czasy[niemcy_dow1]),
            Player(6, "Niemcy", "Dowódca", czasy[niemcy_dow2]),
            Player(1, "Polska", "Generał", czasy[polska_gen]),
            Player(2, "Polska", "Dowódca", czasy[polska_dow1]),
            Player(3, "Polska", "Dowódca", czasy[polska_dow2]),
        ]
    else:
        players = [
            Player(1, "Polska", "Generał", czasy[polska_gen]),
            Player(2, "Polska", "Dowódca", czasy[polska_dow1]),
            Player(3, "Polska", "Dowódca", czasy[polska_dow2]),
            Player(4, "Niemcy", "Generał", czasy[niemcy_gen]),
            Player(5, "Niemcy", "Dowódca", czasy[niemcy_dow1]),
            Player(6, "Niemcy", "Dowódca", czasy[niemcy_dow2]),
        ]

    # Ekonomia dla wszystkich graczy
    for p in players:
        if not hasattr(p, 'economy') or p.economy is None:
            p.economy = EconomySystem()

    return players


def run_game(max_turns: int, victory_mode: str, clean_before: bool):
    print(f"🎮 Start: AI Niemcy vs Polska (HUMAN) | {max_turns} tur | tryb: {victory_mode}")
    if clean_before:
        print("🧹 Szybkie czyszczenie przed grą…")
        try:
            quick_clean_full()
            print("✅ Czyszczenie zakończone")
        except Exception as e:
            print(f"⚠️ Błąd czyszczenia: {e}")

    # Silnik gry
    game_engine = GameEngine(
        map_path="data/map_data.json",
        tokens_index_path="assets/tokens/index.json",
        tokens_start_path="assets/start_tokens.json",
        seed=42,
        read_only=True,
    )

    players = build_players()
    game_engine.players = players

    # Widoczność na start i synchronizacja ekonomii
    update_all_players_visibility(players, game_engine.tokens, game_engine.board)
    for p in players:
        if hasattr(p, 'punkty_ekonomiczne'):
            p.punkty_ekonomiczne = p.economy.get_points()['economic_points']

    # Przypnij AI po stronie Niemiec
    ai_generals = {}
    ai_commanders = {}
    for p in players:
        if p.nation == "Niemcy" and p.role == "Generał":
            ai_generals[p.id] = AIGeneral("german")
        elif p.nation == "Niemcy" and p.role == "Dowódca":
            ai_commanders[p.id] = AICommander(p)

    turn_manager = TurnManager(players, game_engine=game_engine)
    victory_conditions = VictoryConditions(max_turns=max_turns, victory_mode=victory_mode)

    just_loaded_save = False
    last_loaded_player_info = None

    while True:
        if last_loaded_player_info:
            found = None
            for p in players:
                if (str(p.id) == str(last_loaded_player_info.get('id')) and
                    p.role == last_loaded_player_info.get('role') and
                    p.nation == last_loaded_player_info.get('nation')):
                    found = p
                    break
            if found:
                current_player = found
                turn_manager.current_player_index = players.index(found)
            last_loaded_player_info = None
        else:
            current_player = turn_manager.get_current_player()

        game_engine.current_player_obj = current_player

        # Log diagnostyczny
        print(f"🏳️‍⚧️ TURA {turn_manager.current_turn}: {current_player.nation} {current_player.role} (id={current_player.id})")

        # Status KeyPoints na początku tury
        game_engine.log_key_points_status(current_player)

        update_all_players_visibility(players, game_engine.tokens, game_engine.board)

        if current_player.id in ai_generals:
            print(f"🤖 AI GENERAL TURN: {current_player.nation} (id={current_player.id})")
            # Ekonomia tylko dla Generała
            current_player.economy.generate_economic_points()
            current_player.economy.add_special_points()
            ai_generals[current_player.id].make_turn(game_engine)
            is_full_turn_end = turn_manager.next_turn()
        elif current_player.id in ai_commanders:
            print(f"🤖 AI COMMANDER TURN: {current_player.nation} (id={current_player.id})")
            ai_commander = ai_commanders[current_player.id]
            # Resupply przed turą taktyczną
            ai_commander.pre_resupply(game_engine)
            ai_commander.make_tactical_turn(game_engine)
            is_full_turn_end = turn_manager.next_turn()
        else:
            # Polska – pełne GUI dla człowieka
            if current_player.role == "Generał":
                app = PanelGenerala(
                    turn_number=turn_manager.current_turn,
                    ekonomia=current_player.economy,
                    gracz=current_player,
                    gracze=players,
                    game_engine=game_engine,
                )
                # Generowanie ekonomii przed panelem
                current_player.economy.generate_economic_points()
                current_player.economy.add_special_points()
                available_points = current_player.economy.get_points()['economic_points']
                app.update_economy(available_points)
                try:
                    app.zarzadzanie_punktami(available_points)
                except Exception:
                    pass
            else:
                app = PanelDowodcy(
                    turn_number=turn_manager.current_turn,
                    remaining_time=current_player.time_limit * 60,
                    gracz=current_player,
                    game_engine=game_engine,
                )
                # Synchronizacja ekonomii dla dowódcy
                przydzielone_punkty = current_player.economy.get_points()['economic_points']
                app.update_economy(przydzielone_punkty)
                current_player.punkty_ekonomiczne = przydzielone_punkty

            if hasattr(app, 'update_weather'):
                app.update_weather(turn_manager.current_weather)

            if app:
                try:
                    app.mainloop()
                except Exception as e:
                    print(f"Błąd panelu: {e}")

            is_full_turn_end = turn_manager.next_turn()

        if is_full_turn_end:
            game_engine.process_key_points(players)

        game_engine.update_all_players_visibility(players)

        if victory_conditions.check_game_over(turn_manager.current_turn, players):
            print(victory_conditions.get_victory_message())

            victory_info = victory_conditions.get_victory_info()
            print("\n" + "=" * 50)
            print(f"🏆 WYNIKI GRY - {victory_info['victory_mode'].upper()}")
            print("=" * 50)

            if victory_info['winner_nation']:
                print(f"🥇 ZWYCIĘZCA: {victory_info['winner_nation']}")

            print("\n📊 SZCZEGÓŁOWE WYNIKI:")
            for p in players:
                vp = getattr(p, "victory_points", 0)
                emoji = "🥇" if victory_info['winner_nation'] == p.nation else "🥈" if vp > 0 else "🥉"
                print(f"{emoji} {p.nation} {p.role} (id={p.id}): {vp} VP")

            print("\n💡 WARUNKI ZWYCIĘSTWA:")
            print(f"• Tryb: {victory_info['victory_mode']}")
            print(f"• Limit tur: {victory_info['max_turns']}")
            print(f"• Powód zakończenia: {victory_info['victory_reason']}")
            print("=" * 50)
            break

        # Reset blokady trybu ruchu, o ile nie wczytywaliśmy save'a
        if not just_loaded_save:
            for t in game_engine.tokens:
                t.movement_mode_locked = False

        if just_loaded_save:
            players = game_engine.players
            clear_temp_visibility(game_engine.players)
            update_all_players_visibility(game_engine.players, game_engine.tokens, game_engine.board)
        just_loaded_save = False
        clear_temp_visibility(players)


def main():
    parser = argparse.ArgumentParser(
        description="Launcher: AI Niemcy vs Polska (pełna kontrola człowieka)")
    parser.add_argument("--turns", type=int, default=20, help="Limit tur (domyślnie 20)")
    parser.add_argument("--victory", choices=["turns", "elimination"], default="turns",
                        help="Tryb zwycięstwa: turns/elimination")
    parser.add_argument("--clean", action="store_true", help="Wyczyść sesję przed startem")
    args = parser.parse_args()

    # Nie narzucamy profilu AI – używamy bieżącej konfiguracji z ai/configs/ai_config.json
    run_game(max_turns=args.turns, victory_mode=args.victory, clean_before=args.clean)


if __name__ == "__main__":
    main()
