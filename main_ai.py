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

class GameLauncher:
    def __init__(self):
        self.root = tk.Tk()
        self.root.title("Gra Wojenna 2025 - Launcher")
        self.root.geometry("400x300")
        
        # Zmienne do przechowywania ustawień
        self.ai_polish_general = tk.BooleanVar()
        self.ai_german_general = tk.BooleanVar()
        
        self.setup_ui()
        
    def setup_ui(self):
        # Główny frame
        main_frame = ttk.Frame(self.root, padding="20")
        main_frame.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        
        # Tytuł
        title_label = ttk.Label(main_frame, text="Gra Wojenna 2025", 
                               font=("Arial", 16, "bold"))
        title_label.grid(row=0, column=0, columnspan=2, pady=(0, 20))
        
        # Sekcja AI
        ai_frame = ttk.LabelFrame(main_frame, text="Ustawienia AI", padding="10")
        ai_frame.grid(row=1, column=0, columnspan=2, sticky=(tk.W, tk.E), pady=(0, 20))
        
        # Checkbox dla polskiego generała AI
        polish_ai_cb = ttk.Checkbutton(ai_frame, 
                                      text="Polski Generał - AI",
                                      variable=self.ai_polish_general)
        polish_ai_cb.grid(row=0, column=0, sticky=tk.W, pady=2)
        
        # Checkbox dla niemieckiego generała AI
        german_ai_cb = ttk.Checkbutton(ai_frame, 
                                      text="Niemiecki Generał - AI",
                                      variable=self.ai_german_general)
        german_ai_cb.grid(row=1, column=0, sticky=tk.W, pady=2)
        
        # Przyciski
        button_frame = ttk.Frame(main_frame)
        button_frame.grid(row=2, column=0, columnspan=2, pady=20)
        
        start_button = ttk.Button(button_frame, text="Rozpocznij Grę", 
                                 command=self.start_game)
        start_button.grid(row=0, column=0, padx=(0, 10))
        
        exit_button = ttk.Button(button_frame, text="Wyjście", 
                                command=self.root.quit)
        exit_button.grid(row=0, column=1)
        
    def start_game(self):
        """Uruchom grę z wybranymi ustawieniami"""
        try:
            self.root.destroy()  # Zamknij launcher
            self.launch_game_with_settings()
        except Exception as e:
            messagebox.showerror("Błąd", f"Nie można uruchomić gry: {str(e)}")
    
    def launch_game_with_settings(self):
        """Uruchom główną grę z ustawieniami AI"""
        # Automatyczne ustawienia graczy
        miejsca = ["Polska", "Polska", "Polska", "Niemcy", "Niemcy", "Niemcy"]
        czasy = [5, 5, 5, 5, 5, 5]  # Czas na turę w minutach
        
        # Inicjalizacja silnika gry
        game_engine = GameEngine(
            map_path="data/map_data.json",
            tokens_index_path="assets/tokens/index.json",
            tokens_start_path="assets/start_tokens.json",
            seed=42,
            read_only=True  # Zapobiega nadpisywaniu pliku mapy
        )

        # Automatyczne przypisanie id dowódców zgodnie z ownerami żetonów
        polska_gen = miejsca.index("Polska")
        polska_dow1 = miejsca.index("Polska", polska_gen+1)
        polska_dow2 = miejsca.index("Polska", polska_dow1+1)
        niemcy_gen = miejsca.index("Niemcy")
        niemcy_dow1 = miejsca.index("Niemcy", niemcy_gen+1)
        niemcy_dow2 = miejsca.index("Niemcy", niemcy_dow1+1)

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

        # Oznacz graczy AI i dodaj obiekty AI
        ai_generals = {}
        for player in players:
            if player.role == "Generał":
                if player.nation == "Polska" and self.ai_polish_general.get():
                    player.is_ai = True
                    ai_generals[player.id] = AIGeneral("polish")
                    print(f"Polski Generał (ID: {player.id}) będzie kontrolowany przez AI")
                elif player.nation == "Niemcy" and self.ai_german_general.get():
                    player.is_ai = True
                    ai_generals[player.id] = AIGeneral("german")
                    print(f"Niemiecki Generał (ID: {player.id}) będzie kontrolowany przez AI")

        # Uzupełnij economy dla wszystkich graczy (skopiowane z main_alternative.py)
        for p in players:
            if not hasattr(p, 'economy') or p.economy is None:
                p.economy = EconomySystem()

        # Udostępnij listę graczy w game_engine
        game_engine.players = players

        # Aktualizacja widoczności na start
        from engine.engine import update_all_players_visibility
        update_all_players_visibility(players, game_engine.tokens, game_engine.board)

        # Inicjalizacja systemów gry
        economy_system = EconomySystem()
        victory_conditions = VictoryConditions(max_turns=10)
        turn_manager = TurnManager(players, game_engine)
        
        # Dodaj AI generals do turn_manager jako atrybut
        turn_manager.ai_generals = ai_generals

        # Uruchomienie głównej pętli gry (skopiowane z main_alternative.py)
        self.main_game_loop(players, turn_manager, economy_system, victory_conditions, game_engine, ai_generals)

    def main_game_loop(self, players, turn_manager, economy_system, victory_conditions, game_engine, ai_generals):
        """Główna pętla gry skopiowana z main_alternative.py"""
        from engine.engine import update_all_players_visibility, clear_temp_visibility
        
        just_loaded_save = False
        last_loaded_player_info = None
        
        while True:
            current_player = turn_manager.get_current_player()
            update_all_players_visibility(players, game_engine.tokens, game_engine.board)
            
            # Sprawdź czy gracz jest AI
            if hasattr(current_player, 'is_ai') and current_player.is_ai and current_player.id in ai_generals:
                print(f"Tura AI: {current_player.nation} {current_player.role}")
                ai_general = ai_generals[current_player.id]
                
                # Ustaw aktualnego gracza w silniku (potrzebne dla AI)
                game_engine.current_player_obj = current_player
                
                # Dla AI Generałów - wygeneruj punkty ekonomiczne
                if current_player.role == "Generał":
                    current_player.economy.generate_economic_points()
                    current_player.economy.add_special_points()
                    available_points = current_player.economy.get_points()['economic_points']
                    print(f"AI Generał otrzymał {available_points} punktów ekonomicznych")
                
                # AI podejmuje decyzje
                ai_general.make_turn(game_engine)
                
                # AI automatycznie kończy turę
                is_full_turn_end = turn_manager.next_turn()
            else:
                # Gracz człowiek - uruchom odpowiedni panel
                if current_player.role == "Generał":
                    app = PanelGenerala(turn_number=turn_manager.current_turn, ekonomia=current_player.economy, gracz=current_player, gracze=players, game_engine=game_engine)
                elif current_player.role == "Dowódca":
                    app = PanelDowodcy(turn_number=turn_manager.current_turn, remaining_time=current_player.time_limit * 60, gracz=current_player, game_engine=game_engine)
                
                # Ustaw aktualnego gracza w silniku
                game_engine.current_player_obj = current_player
                
                # Aktualizacja pogody dla panelu
                if hasattr(app, 'update_weather'):
                    app.update_weather(turn_manager.current_weather)
                
                # Aktualizacja dla generałów
                if isinstance(app, PanelGenerala):
                    current_player.economy.generate_economic_points()
                    current_player.economy.add_special_points()
                    available_points = current_player.economy.get_points()['economic_points']
                    app.update_economy(available_points)
                    app.zarzadzanie_punktami(available_points)
                
                # Aktualizacja dla dowódców
                if isinstance(app, PanelDowodcy):
                    przydzielone_punkty = current_player.economy.get_points()['economic_points']
                    app.update_economy(przydzielone_punkty)
                    current_player.punkty_ekonomiczne = przydzielone_punkty
                
                try:
                    app.mainloop()  # Uruchomienie panelu
                except Exception as e:
                    print(f"Błąd: {e}")
                
                # Przejście do następnej tury
                is_full_turn_end = turn_manager.next_turn()
            
            # Rozdziel punkty na końcu pełnej tury
            if is_full_turn_end:
                game_engine.process_key_points(players)
            
            # Aktualizuj widoczność
            game_engine.update_all_players_visibility(players)
            
            # Sprawdzenie końca gry
            if victory_conditions.check_game_over(turn_manager.current_turn):
                print(victory_conditions.get_victory_message())
                print("=== PODSUMOWANIE ===")
                for p in players:
                    vp = getattr(p, "victory_points", 0)
                    print(f"{p.nation} {p.role} (id={p.id}): {vp} punktów zwycięstwa")
                print("====================")
                break
            
            # Reset blokady trybu ruchu
            if not just_loaded_save:
                for t in game_engine.tokens:
                    t.movement_mode_locked = False
            
            just_loaded_save = False
            clear_temp_visibility(players)

    def run(self):
        """Uruchom launcher"""
        self.root.mainloop()

# Funkcja główna
if __name__ == "__main__":
    launcher = GameLauncher()
    launcher.run()
