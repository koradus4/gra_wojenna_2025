import tkinter as tk
from tkinter import ttk, messagebox
from core.tura import TurnManager
from engine.player import Player
from gui.panel_generala import PanelGenerala
from gui.panel_dowodcy import PanelDowodcy
from core.ekonomia import EconomySystem
from engine.engine import GameEngine, update_all_players_visibility, clear_temp_visibility
from gui.panel_gracza import PanelGracza
from core.zwyciestwo import VictoryConditions
from ai.ai_general import AIGeneral
from ai.ai_commander import AICommander


class GameLauncher:
    def __init__(self):
        self.root = tk.Tk()
        self.root.title("Gra Wojenna 2025 - Launcher")
        self.root.geometry("500x500")  # Jeszcze większe okno
        self.ai_polish_general = tk.BooleanVar()
        self.ai_german_general = tk.BooleanVar()
        # Osobne opcje dla każdego dowódcy
        self.ai_polish_commander_1 = tk.BooleanVar()
        self.ai_polish_commander_2 = tk.BooleanVar()
        self.ai_german_commander_1 = tk.BooleanVar()
        self.ai_german_commander_2 = tk.BooleanVar()
        self.setup_ui()

    def setup_ui(self):
        frame = ttk.Frame(self.root, padding="20")
        frame.grid(row=0, column=0, sticky="nsew")
        ttk.Label(frame, text="Gra Wojenna 2025", font=("Arial", 16, "bold")).grid(row=0, column=0, columnspan=2, pady=(0, 20))
        
        # Sekcja AI
        lf = ttk.LabelFrame(frame, text="Konfiguracja AI", padding="15")
        lf.grid(row=1, column=0, columnspan=2, sticky="ew", pady=(0, 20))
        
        # Generałowie
        ttk.Label(lf, text="Generałowie:", font=("Arial", 11, "bold")).grid(row=0, column=0, sticky="w", pady=(0, 5))
        ttk.Checkbutton(lf, text="Polski Generał (id=1) - AI", variable=self.ai_polish_general).grid(row=1, column=0, sticky="w", padx=(20, 0))
        ttk.Checkbutton(lf, text="Niemiecki Generał (id=4) - AI", variable=self.ai_german_general).grid(row=2, column=0, sticky="w", padx=(20, 0))
        
        # Separator
        ttk.Separator(lf, orient='horizontal').grid(row=3, column=0, sticky="ew", pady=10)
        
        # Dowódcy polscy
        ttk.Label(lf, text="Dowódcy polscy:", font=("Arial", 11, "bold")).grid(row=4, column=0, sticky="w", pady=(5, 5))
        ttk.Checkbutton(lf, text="Polski Dowódca 1 (id=2) - AI", variable=self.ai_polish_commander_1).grid(row=5, column=0, sticky="w", padx=(20, 0))
        ttk.Checkbutton(lf, text="Polski Dowódca 2 (id=3) - AI", variable=self.ai_polish_commander_2).grid(row=6, column=0, sticky="w", padx=(20, 0))
        
        # Dowódcy niemieccy
        ttk.Label(lf, text="Dowódcy niemieccy:", font=("Arial", 11, "bold")).grid(row=7, column=0, sticky="w", pady=(10, 5))
        ttk.Checkbutton(lf, text="Niemiecki Dowódca 1 (id=5) - AI", variable=self.ai_german_commander_1).grid(row=8, column=0, sticky="w", padx=(20, 0))
        ttk.Checkbutton(lf, text="Niemiecki Dowódca 2 (id=6) - AI", variable=self.ai_german_commander_2).grid(row=9, column=0, sticky="w", padx=(20, 0))
        
        # Przyciski
        button_frame = ttk.Frame(frame)
        button_frame.grid(row=2, column=0, columnspan=2, pady=20)
        ttk.Button(button_frame, text="Start Gry", command=self.start_game).grid(row=0, column=0, padx=(0, 10))
        ttk.Button(button_frame, text="Test AI", command=self.test_ai).grid(row=0, column=1, padx=(0, 10))
        ttk.Button(button_frame, text="Wyjście", command=self.root.quit).grid(row=0, column=2)

    def test_ai(self):
        """Szybki test AI bez uruchamiania pełnej gry"""
        from ai.ai_commander import test_basic_safety
        result = test_basic_safety()
        messagebox.showinfo("Test AI", f"Test AI Commander: {'✓ OK' if result else '✗ Błąd'}")

    def start_game(self):
        try:
            self.root.destroy()
            self.launch_game_with_settings()
        except Exception as e:
            messagebox.showerror("Błąd", f"Uruchomienie gry nieudane: {e}")

    def launch_game_with_settings(self):
        miejsca = ["Polska", "Polska", "Polska", "Niemcy", "Niemcy", "Niemcy"]
        czasy = [5, 5, 5, 5, 5, 5]
        game_engine = GameEngine(
            map_path="data/map_data.json",
            tokens_index_path="assets/tokens/index.json",
            tokens_start_path="assets/start_tokens.json",
            seed=42,
            read_only=True
        )
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
        ai_generals = {}
        ai_commanders = {}
        for player in players:
            if player.role == "Generał":
                if player.nation == "Polska" and self.ai_polish_general.get():
                    player.is_ai = True
                    ai_generals[player.id] = AIGeneral("polish")
                    print(f"[AI] Generał AI aktywny: {player.nation} (id={player.id})")
                elif player.nation == "Niemcy" and self.ai_german_general.get():
                    player.is_ai = True
                    ai_generals[player.id] = AIGeneral("german")
                    print(f"[AI] Generał AI aktywny: {player.nation} (id={player.id})")
            elif player.role == "Dowódca":
                # Sprawdź konkretnego dowódcę po ID
                should_be_ai = False
                
                if player.id == 2 and self.ai_polish_commander_1.get():  # Polski Dowódca 1
                    should_be_ai = True
                elif player.id == 3 and self.ai_polish_commander_2.get():  # Polski Dowódca 2
                    should_be_ai = True
                elif player.id == 5 and self.ai_german_commander_1.get():  # Niemiecki Dowódca 1
                    should_be_ai = True
                elif player.id == 6 and self.ai_german_commander_2.get():  # Niemiecki Dowódca 2
                    should_be_ai = True
                
                if should_be_ai:
                    player.is_ai_commander = True
                    ai_commanders[player.id] = AICommander(player)
                    print(f"[AI] Dowódca AI aktywny: {player.nation} Dowódca {player.id} (id={player.id})")
                else:
                    player.is_ai_commander = False
                    print(f"[HUMAN] Dowódca ludzki: {player.nation} Dowódca {player.id} (id={player.id})")
        for p in players:
            if not hasattr(p, 'economy') or p.economy is None:
                p.economy = EconomySystem()
        game_engine.players = players
        update_all_players_visibility(players, game_engine.tokens, game_engine.board)
        for p in players:
            if hasattr(p, 'punkty_ekonomiczne'):
                p.punkty_ekonomiczne = p.economy.get_points()['economic_points']
        turn_manager = TurnManager(players, game_engine=game_engine)
        victory_conditions = VictoryConditions(max_turns=10)
        turn_manager.ai_generals = ai_generals
        turn_manager.ai_commanders = ai_commanders
        self.main_game_loop(players, turn_manager, victory_conditions, game_engine, ai_generals, ai_commanders)

    def main_game_loop(self, players, turn_manager, victory_conditions, game_engine, ai_generals, ai_commanders):
        just_loaded_save = False
        last_loaded_player_info = None
        while True:
            if last_loaded_player_info:
                found = None
                for p in players:
                    if (str(p.id) == str(last_loaded_player_info.get('id')) and p.role == last_loaded_player_info.get('role') and p.nation == last_loaded_player_info.get('nation')):
                        found = p
                        break
                if found:
                    current_player = found
                    turn_manager.current_player_index = players.index(found)
                last_loaded_player_info = None
            else:
                current_player = turn_manager.get_current_player()
            game_engine.current_player_obj = current_player
            update_all_players_visibility(players, game_engine.tokens, game_engine.board)
            if hasattr(current_player, 'is_ai') and current_player.is_ai and current_player.id in ai_generals:
                print(f"Tura AI: {current_player.nation} {current_player.role}")
                ai_general = ai_generals[current_player.id]
                if current_player.role == "Generał":
                    current_player.economy.generate_economic_points()
                    current_player.economy.add_special_points()
                ai_general.make_turn(game_engine)
                is_full_turn_end = turn_manager.next_turn()
            elif hasattr(current_player, 'is_ai_commander') and current_player.is_ai_commander and current_player.id in ai_commanders:
                print(f"Tura AI Dowódcy (stub): {current_player.nation} id={current_player.id}")
                ai_commander = ai_commanders[current_player.id]
                ai_commander.make_tactical_turn(game_engine)
                is_full_turn_end = turn_manager.next_turn()
            else:
                if current_player.role == "Generał":
                    app = PanelGenerala(turn_number=turn_manager.current_turn, ekonomia=current_player.economy, gracz=current_player, gracze=players, game_engine=game_engine)
                elif current_player.role == "Dowódca":
                    app = PanelDowodcy(turn_number=turn_manager.current_turn, remaining_time=current_player.time_limit * 60, gracz=current_player, game_engine=game_engine)
                else:
                    app = None
                if app and hasattr(app, 'update_weather'):
                    app.update_weather(turn_manager.current_weather)
                if isinstance(app, PanelGenerala):
                    current_player.economy.generate_economic_points()
                    current_player.economy.add_special_points()
                    available_points = current_player.economy.get_points()['economic_points']
                    app.update_economy(available_points)
                    app.zarzadzanie_punktami(available_points)
                if isinstance(app, PanelDowodcy):
                    przydzielone_punkty = current_player.economy.get_points()['economic_points']
                    app.update_economy(przydzielone_punkty)
                    current_player.punkty_ekonomiczne = przydzielone_punkty
                if app:
                    try:
                        app.mainloop()
                    except Exception as e:
                        print(f"Błąd: {e}")
                is_full_turn_end = turn_manager.next_turn()
            if is_full_turn_end:
                game_engine.process_key_points(players)
            game_engine.update_all_players_visibility(players)
            if victory_conditions.check_game_over(turn_manager.current_turn):
                print(victory_conditions.get_victory_message())
                print("=== PODSUMOWANIE ===")
                for p in players:
                    vp = getattr(p, "victory_points", 0)
                    print(f"{p.nation} {p.role} (id={p.id}): {vp} punktów zwycięstwa")
                print("====================")
                break
            if not just_loaded_save:
                for t in game_engine.tokens:
                    t.movement_mode_locked = False
            if just_loaded_save:
                players = game_engine.players
                clear_temp_visibility(game_engine.players)
                update_all_players_visibility(game_engine.players, game_engine.tokens, game_engine.board)
            just_loaded_save = False
            clear_temp_visibility(players)

    def run(self):
        self.root.mainloop()


if __name__ == "__main__":
    launcher = GameLauncher()
    launcher.run()
