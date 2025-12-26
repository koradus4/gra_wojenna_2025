import tkinter as tk
from tkinter import ttk, messagebox
import sys
from core.tura import TurnManager
from engine.player import Player
from gui.panel_generala import PanelGenerala
from gui.panel_dowodcy import PanelDowodcy
from core.ekonomia import EconomySystem
from engine.engine import GameEngine, update_all_players_visibility, clear_temp_visibility
from gui.panel_gracza import PanelGracza
from core.zwyciestwo import VictoryConditions
from utils.session_archiver import archive_sessions
from ai.logs.czyszczenie_logow import clean_logs as clean_logs_script

# Import AI modules
from ai import GeneralAI, CommanderAI

# --- Safe stdout encoding (unikaj UnicodeEncodeError w konsoli cp1250) ---
try:
    import sys
    if hasattr(sys.stdout, 'reconfigure'):
        sys.stdout.reconfigure(encoding='utf-8', errors='ignore')
except Exception:
    pass

# 🎚️ POZIOM DEBUGOWANIA - łatwa kontrola komunikatów
DEBUG_LEVEL = "BASIC"  # "BASIC" = tylko kupowanie/wystawianie, "FULL" = wszystkie szczegóły
SHOW_STARTUP_BANNER = False

def debug_print(message, level="BASIC", category="INFO"):
    """Drukuje komunikaty tylko gdy poziom debugowania pozwala"""
    if DEBUG_LEVEL == "FULL":
        print(f"[{category}] {message}")
    elif DEBUG_LEVEL == "BASIC" and level == "BASIC":
        print(f"🎯 {message}")

if SHOW_STARTUP_BANNER:
    print("🤖 GRA WOJENNA - AI LAUNCHER")
    print(f"🎚️ Poziom debugowania: {DEBUG_LEVEL}")
    print("💡 Zmiana debug: w konsoli wpisz 'BASIC' lub 'FULL'")
    print("-" * 50)


class AIGameLauncher:
    def __init__(self):
        self.root = tk.Tk()
        self.root.title("Gra Wojenna 2025 - AI Launcher")
        
        # Konfiguracja obsługi zamykania aplikacji
        self.root.protocol("WM_DELETE_WINDOW", self.on_closing)
        
        # Zmaksymalizuj okno
        self.root.state('zoomed')  # Windows maximized
        
        # Fallback rozmiar jeśli maximized nie działa
        self.root.geometry("1400x1000")
        try:
            self.root.minsize(1200, 900)
        except Exception:
            pass
            
        # Opcje gry
        self.max_turns = tk.StringVar(value="10")
        self.victory_mode = tk.StringVar(value="turns")
        
        # AI/Human settings dla każdego gracza
        self.player_types = {
            'polska_general': tk.StringVar(value="human"),
            'polska_commander1': tk.StringVar(value="human"), 
            'polska_commander2': tk.StringVar(value="human"),
            'niemcy_general': tk.StringVar(value="ai"),
            'niemcy_commander1': tk.StringVar(value="ai"),
            'niemcy_commander2': tk.StringVar(value="ai")
        }
        
        # UI
        self.setup_ui()
        self.root.bind('<Control-Shift-L>', lambda _e: self.clean_logs_gui())

    def setup_ui(self):
        # Główny frame
        self.root.columnconfigure(0, weight=1)
        self.root.rowconfigure(0, weight=1)
        
        main_frame = ttk.Frame(self.root, padding="20")
        main_frame.grid(row=0, column=0, sticky="nsew")
        
        main_frame.columnconfigure(0, weight=1)
        main_frame.columnconfigure(1, weight=1)
        main_frame.rowconfigure(0, weight=1)
        
        # Lewa kolumna - konfiguracja graczy
        left_frame = ttk.Frame(main_frame)
        left_frame.grid(row=0, column=0, sticky="nsew", padx=(0, 10))
        
        # Prawa kolumna - opcje gry
        right_frame = ttk.Frame(main_frame)  
        right_frame.grid(row=0, column=1, sticky="nsew", padx=(10, 0))
        
        # === LEWA KOLUMNA - KONFIGURACJA GRACZY ===
        ttk.Label(left_frame, text="🤖 Konfiguracja Graczy AI/Human", font=("Arial", 16, "bold")).grid(row=0, column=0, columnspan=2, pady=(0, 20))
        
        # Polska
        polska_frame = ttk.LabelFrame(left_frame, text="🇵🇱 Polska", padding="15")
        polska_frame.grid(row=1, column=0, columnspan=2, sticky="ew", pady=(0, 20))
        
        # Generał Polski
        ttk.Label(polska_frame, text="Generał:", font=("Arial", 11, "bold")).grid(row=0, column=0, sticky="w")
        gen_pol_frame = ttk.Frame(polska_frame)
        gen_pol_frame.grid(row=0, column=1, sticky="w", padx=(10, 0))
        ttk.Radiobutton(gen_pol_frame, text="👤 Human", variable=self.player_types['polska_general'], value="human").pack(side="left", padx=(0, 10))
        ttk.Radiobutton(gen_pol_frame, text="🤖 AI", variable=self.player_types['polska_general'], value="ai").pack(side="left")
        
        # Dowódca 1 Polski
        ttk.Label(polska_frame, text="Dowódca 1:", font=("Arial", 11)).grid(row=1, column=0, sticky="w", pady=(5, 0))
        cmd1_pol_frame = ttk.Frame(polska_frame)
        cmd1_pol_frame.grid(row=1, column=1, sticky="w", padx=(10, 0), pady=(5, 0))
        ttk.Radiobutton(cmd1_pol_frame, text="👤 Human", variable=self.player_types['polska_commander1'], value="human").pack(side="left", padx=(0, 10))
        ttk.Radiobutton(cmd1_pol_frame, text="🤖 AI", variable=self.player_types['polska_commander1'], value="ai").pack(side="left")
        
        # Dowódca 2 Polski
        ttk.Label(polska_frame, text="Dowódca 2:", font=("Arial", 11)).grid(row=2, column=0, sticky="w", pady=(5, 0))
        cmd2_pol_frame = ttk.Frame(polska_frame)
        cmd2_pol_frame.grid(row=2, column=1, sticky="w", padx=(10, 0), pady=(5, 0))
        ttk.Radiobutton(cmd2_pol_frame, text="👤 Human", variable=self.player_types['polska_commander2'], value="human").pack(side="left", padx=(0, 10))
        ttk.Radiobutton(cmd2_pol_frame, text="🤖 AI", variable=self.player_types['polska_commander2'], value="ai").pack(side="left")
        
        # Niemcy
        niemcy_frame = ttk.LabelFrame(left_frame, text="🇩🇪 Niemcy", padding="15")
        niemcy_frame.grid(row=2, column=0, columnspan=2, sticky="ew", pady=(0, 20))
        
        # Generał Niemiecki
        ttk.Label(niemcy_frame, text="Generał:", font=("Arial", 11, "bold")).grid(row=0, column=0, sticky="w")
        gen_ger_frame = ttk.Frame(niemcy_frame)
        gen_ger_frame.grid(row=0, column=1, sticky="w", padx=(10, 0))
        ttk.Radiobutton(gen_ger_frame, text="👤 Human", variable=self.player_types['niemcy_general'], value="human").pack(side="left", padx=(0, 10))
        ttk.Radiobutton(gen_ger_frame, text="🤖 AI", variable=self.player_types['niemcy_general'], value="ai").pack(side="left")
        
        # Dowódca 1 Niemiecki
        ttk.Label(niemcy_frame, text="Dowódca 1:", font=("Arial", 11)).grid(row=1, column=0, sticky="w", pady=(5, 0))
        cmd1_ger_frame = ttk.Frame(niemcy_frame)
        cmd1_ger_frame.grid(row=1, column=1, sticky="w", padx=(10, 0), pady=(5, 0))
        ttk.Radiobutton(cmd1_ger_frame, text="👤 Human", variable=self.player_types['niemcy_commander1'], value="human").pack(side="left", padx=(0, 10))
        ttk.Radiobutton(cmd1_ger_frame, text="🤖 AI", variable=self.player_types['niemcy_commander1'], value="ai").pack(side="left")
        
        # Dowódca 2 Niemiecki
        ttk.Label(niemcy_frame, text="Dowódca 2:", font=("Arial", 11)).grid(row=2, column=0, sticky="w", pady=(5, 0))
        cmd2_ger_frame = ttk.Frame(niemcy_frame)
        cmd2_ger_frame.grid(row=2, column=1, sticky="w", padx=(10, 0), pady=(5, 0))
        ttk.Radiobutton(cmd2_ger_frame, text="👤 Human", variable=self.player_types['niemcy_commander2'], value="human").pack(side="left", padx=(0, 10))
        ttk.Radiobutton(cmd2_ger_frame, text="🤖 AI", variable=self.player_types['niemcy_commander2'], value="ai").pack(side="left")
        
        # === PRAWA KOLUMNA - OPCJE GRY ===
        ttk.Label(right_frame, text="⚙️ Opcje Gry", font=("Arial", 16, "bold")).grid(row=0, column=0, columnspan=2, pady=(0, 20))
        
        # Opcje gry
        game_frame = ttk.LabelFrame(right_frame, text="Ustawienia gry", padding="15")
        game_frame.grid(row=1, column=0, columnspan=2, sticky="ew", pady=(0, 20))
        
        ttk.Label(game_frame, text="Maksymalna liczba tur:", font=("Arial", 11, "bold")).grid(row=0, column=0, sticky="w", pady=(0, 5))
        turns_frame = ttk.Frame(game_frame)
        turns_frame.grid(row=1, column=0, sticky="w", padx=(20, 0))
        ttk.Radiobutton(turns_frame, text="10 tur (szybka gra)", variable=self.max_turns, value="10").pack(anchor="w")
        ttk.Radiobutton(turns_frame, text="20 tur (standardowa)", variable=self.max_turns, value="20").pack(anchor="w")
        ttk.Radiobutton(turns_frame, text="30 tur (długa kampania)", variable=self.max_turns, value="30").pack(anchor="w")
        
        ttk.Separator(game_frame, orient='horizontal').grid(row=2, column=0, sticky="ew", pady=10)
        
        ttk.Label(game_frame, text="Warunki zwycięstwa:", font=("Arial", 11, "bold")).grid(row=3, column=0, sticky="w", pady=(5, 5))
        victory_frame = ttk.Frame(game_frame)
        victory_frame.grid(row=4, column=0, sticky="w", padx=(20, 0))
        ttk.Radiobutton(victory_frame, text="🏆 Victory Points (porównanie po turach)", variable=self.victory_mode, value="turns").pack(anchor="w")
        ttk.Radiobutton(victory_frame, text="💀 Eliminacja wroga (koniec przed limitem)", variable=self.victory_mode, value="elimination").pack(anchor="w")
        
        # Czyszczenie
        clean_frame = ttk.LabelFrame(right_frame, text="Czyszczenie danych", padding="15")
        clean_frame.grid(row=2, column=0, columnspan=2, sticky="ew", pady=(0, 20))

        ttk.Button(clean_frame, text="🧹 Wyczyść logi", command=self.clean_logs_gui).grid(row=0, column=0, sticky="w")
        ttk.Label(
            clean_frame,
            text="Czyści logi AI oraz zakupione żetony (bez wpływu na zapisy ani dane ML).",
            font=("Arial", 9),
            foreground="gray",
        ).grid(row=1, column=0, sticky="w", pady=(6, 0))
        ttk.Label(
            clean_frame,
            text="Skrót klawiszowy: Ctrl+Shift+L",
            font=("Arial", 8),
            foreground="gray",
        ).grid(row=2, column=0, sticky="w")
        
        # Główne przyciski
        main_button_frame = ttk.Frame(right_frame)
        main_button_frame.grid(row=3, column=0, columnspan=2, pady=20)

        ttk.Button(main_button_frame, text="🚀 Uruchom Grę AI", command=self.start_game).grid(row=0, column=0, padx=(0, 20))
        ttk.Button(main_button_frame, text="❌ Zamknij", command=self.root.quit).grid(row=0, column=1)
        
        # Podgląd konfiguracji
        config_frame = ttk.LabelFrame(right_frame, text="📊 Podgląd konfiguracji", padding="10")
        config_frame.grid(row=4, column=0, columnspan=2, sticky="ew", pady=(0, 10))
        
        self.config_label = ttk.Label(config_frame, text="", font=("Arial", 9), foreground="gray")
        self.config_label.pack()
        
        self.update_config_preview()
        
        # Bind do aktualizacji podglądu
        for var in self.player_types.values():
            var.trace_add("write", lambda *args: self.update_config_preview())
    
    def update_config_preview(self):
        """Aktualizuje podgląd konfiguracji"""
        config_text = "Konfiguracja:\n"
        config_text += f"🇵🇱 Polska: Gen({self.player_types['polska_general'].get()}), "
        config_text += f"Dow1({self.player_types['polska_commander1'].get()}), "
        config_text += f"Dow2({self.player_types['polska_commander2'].get()})\n"
        config_text += f"🇩🇪 Niemcy: Gen({self.player_types['niemcy_general'].get()}), "
        config_text += f"Dow1({self.player_types['niemcy_commander1'].get()}), "
        config_text += f"Dow2({self.player_types['niemcy_commander2'].get()})"
        
        self.config_label.config(text=config_text)

    def clean_logs_gui(self):
        """Czyści katalog `logs/` z poziomu AI launchera."""
        try:
            confirm = messagebox.askyesno(
                "Czyszczenie logów",
                "Czy na pewno usunąć logi AI oraz zakupione żetony z poprzednich sesji?",
            )
            if not confirm:
                return

            removed = clean_logs_script(confirm=False, verbose=False)
            if removed == 0:
                messagebox.showinfo(
                    "Czyszczenie danych",
                    "Logi AI i zakupione żetony są już czyste.",
                )
            else:
                messagebox.showinfo(
                    "Czyszczenie danych",
                    "Usunięto artefakty logów AI i zakupionych żetonów z poprzednich sesji.",
                )
        except Exception as error:
            messagebox.showerror(
                "Błąd czyszczenia",
                f"Nie udało się wyczyścić logów:\n{error}",
            )

    def start_game(self):
        try:
            proceed = messagebox.askyesno(
                "Start gry AI",
                "Uruchomić grę z bieżącą konfiguracją AI/Human?\n\n"
                "Jeśli chcesz wyczyścić logi przed startem, użyj przycisku 'Wyczyść logi'.",
            )
            if not proceed:
                print("ℹ️ Start gry AI został anulowany przez użytkownika")
                return

            self.root.destroy()
            self.launch_ai_game()
        except Exception as e:
            messagebox.showerror("Błąd", f"Uruchomienie gry AI nieudane: {e}")

    def launch_ai_game(self):
        """Uruchamia grę z konfiguracją AI/Human"""
        debug_print("🚀 ROZPOCZYNANIE DIAGNOSTYKI MAIN_AI_LAUNCHER.PY", "BASIC", "STARTUP")
        
        # Konfiguracja graczy z AI/Human
        miejsca = ["Polska", "Polska", "Polska", "Niemcy", "Niemcy", "Niemcy"]
        czasy = [5, 5, 5, 5, 5, 5]
        
        debug_print("🔧 TWORZENIE GAMEENGINE...", "BASIC", "STARTUP")
        game_engine = GameEngine(
            map_path="data/map_data.json",
            tokens_index_path="assets/tokens/index.json",
            tokens_start_path="assets/start_tokens.json",
            seed=42,
            read_only=True
        )
        debug_print("✅ GAMEENGINE UTWORZONY", "BASIC", "STARTUP")
        
        # Diagnostyka paliwa
        debug_print("🔥 NATYCHMIASTOWA DIAGNOSTYKA PALIWA:", "FULL", "DIAGNOSTICS")
        niepelne_baki = 0
        polskie_tokeny = 0
        for token in game_engine.tokens:
            owner = getattr(token, 'owner', '')
            if '2 (' in str(owner) or '3 (' in str(owner):
                polskie_tokeny += 1
                current_fuel = getattr(token, 'currentFuel', -1)
                max_fuel = getattr(token, 'maxFuel', -1)
                if current_fuel < max_fuel:
                    niepelne_baki += 1
                    debug_print(f"❌ {token.id}: {current_fuel}/{max_fuel}", "FULL", "DIAGNOSTICS")
        debug_print(f"🔥 POLSKICH TOKENÓW: {polskie_tokeny}, NIEPEŁNE BAKI: {niepelne_baki}", "FULL", "DIAGNOSTICS")
        
        # Znajdź pozycje graczy
        polska_gen = miejsca.index("Polska")
        polska_dow1 = miejsca.index("Polska", polska_gen + 1)
        polska_dow2 = miejsca.index("Polska", polska_dow1 + 1)
        niemcy_gen = miejsca.index("Niemcy")
        niemcy_dow1 = miejsca.index("Niemcy", niemcy_gen + 1)
        niemcy_dow2 = miejsca.index("Niemcy", niemcy_dow1 + 1)
        
        # Utwórz graczy z konfiguracją AI/Human
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
        
        # Mapowanie player_id -> konfiguracja
        player_config_map = {
            1: 'polska_general',
            2: 'polska_commander1', 
            3: 'polska_commander2',
            4: 'niemcy_general',
            5: 'niemcy_commander1',
            6: 'niemcy_commander2'
        }
        
        # Ustaw AI flags według konfiguracji
        for player in players:
            config_key = player_config_map[player.id]
            is_ai = self.player_types[config_key].get() == "ai"
            
            player.is_ai = is_ai
            player.is_ai_commander = is_ai and player.role == "Dowódca" 
            
            print(f"🎯 Gracz {player.id} ({player.nation} {player.role}): {'🤖 AI' if is_ai else '👤 Human'}")
        
        # Inicjalizuj ekonomię
        for p in players:
            if not hasattr(p, 'economy') or p.economy is None:
                p.economy = EconomySystem()
        
        game_engine.players = players
        
        # Aktualizuj widoczność
        update_all_players_visibility(players, game_engine.tokens, game_engine.board)
        
        # Synchronizuj punkty ekonomiczne
        for p in players:
            if hasattr(p, 'punkty_ekonomiczne'):
                p.punkty_ekonomiczne = p.economy.get_points()['economic_points']
        
        turn_manager = TurnManager(players, game_engine=game_engine)
        
        # Ustawienia zwycięstwa
        max_turns_val = int(self.max_turns.get())
        victory_mode_val = self.victory_mode.get()
        
        print(f"🎯 Ustawienia gry: {max_turns_val} tur, tryb: {victory_mode_val}")
        
        victory_conditions = VictoryConditions(max_turns=max_turns_val, victory_mode=victory_mode_val)
        self.main_game_loop(players, turn_manager, victory_conditions, game_engine)

    def main_game_loop(self, players, turn_manager, victory_conditions, game_engine):
        """Główna pętla gry z obsługą AI"""
        just_loaded_save = False
        last_loaded_player_info = None
        
        while True:
            # Ustaw kontekst tury
            try:
                from utils.turn_context import set_current_turn
                set_current_turn(turn_manager.current_turn)
            except Exception:
                pass
                
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
            
            # ROZGAŁĘZIENIE: AI vs Human
            if current_player.is_ai:
                print(f"🤖 TURA AI: {current_player.id} ({current_player.nation} {current_player.role})")
                
                # LOGOWANIE key pointów na początku tury AI
                game_engine.log_key_points_status(current_player)
                
                if current_player.role == "Generał":
                    # AI Generał - dystrybucja PE
                    ai_general = GeneralAI(current_player)
                    ai_general.execute_turn(players, game_engine)
                elif current_player.role == "Dowódca":
                    # AI Komendant - zarządzanie żetonami
                    ai_commander = CommanderAI(current_player)
                    ai_commander.execute_turn(game_engine)
                    
            else:
                print(f"👤 TURA CZŁOWIEKA: {current_player.id} ({current_player.nation} {current_player.role})")
                
                # Logowanie key pointów na początku tury człowieka
                game_engine.log_key_points_status(current_player)
                
                update_all_players_visibility(players, game_engine.tokens, game_engine.board)
                
                # GUI dla człowieka
                if current_player.role == "Generał":
                    app = PanelGenerala(turn_number=turn_manager.current_turn, 
                                      ekonomia=current_player.economy, 
                                      gracz=current_player, 
                                      gracze=players, 
                                      game_engine=game_engine)
                elif current_player.role == "Dowódca":
                    app = PanelDowodcy(turn_number=turn_manager.current_turn, 
                                     remaining_time=current_player.time_limit * 60, 
                                     gracz=current_player, 
                                     game_engine=game_engine)
                else:
                    app = None
                
                if app and hasattr(app, 'update_weather'):
                    app.update_weather(turn_manager.get_ui_weather_report())
                
                # Obsługa ekonomii dla generała
                if isinstance(app, PanelGenerala):
                    current_player.economy.generate_economic_points()
                    current_player.economy.add_special_points()
                    available_points = current_player.economy.get_points()['economic_points']
                    app.update_economy(available_points)
                    app.zarzadzanie_punktami(available_points)
                
                # Obsługa ekonomii dla dowódcy
                if isinstance(app, PanelDowodcy):
                    przydzielone_punkty = current_player.economy.get_points()['economic_points']
                    app.update_economy(przydzielone_punkty)
                    current_player.punkty_ekonomiczne = przydzielone_punkty
                
                if app:
                    try:
                        app.mainloop()
                    except Exception as e:
                        print(f"Błąd: {e}")
            
            # Przejdź do następnej tury
            is_full_turn_end = turn_manager.next_turn()
            
            # Zaktualizuj kontekst tury po zmianie
            try:
                from utils.turn_context import set_current_turn
                set_current_turn(turn_manager.current_turn)
            except Exception:
                pass
            
            # Przetwarzaj key points na końcu pełnej tury
            if is_full_turn_end:
                game_engine.process_key_points(players)
            
            # Aktualizuj widoczność
            game_engine.update_all_players_visibility(players)
            
            # Sprawdź warunki zwycięstwa
            if victory_conditions.check_game_over(turn_manager.current_turn, players):
                print(victory_conditions.get_victory_message())
                
                victory_info = victory_conditions.get_victory_info()
                print("\n" + "="*50)
                print(f"🏆 WYNIKI GORY - {victory_info['victory_mode'].upper()}")
                print("="*50)
                
                if victory_info['winner_nation']:
                    print(f"🥇 ZWYCIĘZCA: {victory_info['winner_nation']}")
                
                print("\n📊 SZCZEGÓŁOWE WYNIKI:")
                for p in players:
                    vp = getattr(p, "victory_points", 0)
                    emoji = "🥇" if victory_info['winner_nation'] == p.nation else "🥈" if vp > 0 else "🥉"
                    ai_marker = " 🤖" if p.is_ai else " 👤"
                    print(f"{emoji} {p.nation} {p.role} (id={p.id}){ai_marker}: {vp} VP")
                    
                print("\n💡 WARUNKI ZWYCIĘSTWA:")
                print(f"• Tryb: {victory_info['victory_mode']}")
                print(f"• Limit tur: {victory_info['max_turns']}")
                print(f"• Powód zakończenia: {victory_info['victory_reason']}")
                print("="*50)
                break
            
            # Odblokowac tryb ruchu po zapisie
            if not just_loaded_save:
                for t in game_engine.tokens:
                    t.movement_mode_locked = False
            
            # Obsługa po załadowaniu zapisu
            if just_loaded_save:
                players = game_engine.players
                clear_temp_visibility(game_engine.players)
                update_all_players_visibility(game_engine.players, game_engine.tokens, game_engine.board)
            
            just_loaded_save = False
            clear_temp_visibility(players)

    def on_closing(self):
        """Obsługuje zamykanie aplikacji z archiwizacją sesji"""
        try:
            print("🔚 [AI_LAUNCHER] Zamykanie aplikacji...")
            
            # Archiwizacja sesji przed zamknięciem
            print("📦 [AI_LAUNCHER] Archiwizacja sesji...")
            stats = archive_sessions()
            
            if stats['archived'] > 0:
                print(f"✅ [AI_LAUNCHER] Zarchiwizowano {stats['archived']} sesji")
                if stats['cleaned'] > 0:
                    print(f"🗑️ [AI_LAUNCHER] Wyczyszczono {stats['cleaned']} starych sesji")
            else:
                print("ℹ️ [AI_LAUNCHER] Brak sesji do archiwizacji")
            
        except Exception as e:
            print(f"⚠️ [AI_LAUNCHER] Błąd podczas archiwizacji: {e}")
        finally:
            # Zawsze zamknij aplikację
            print("👋 [AI_LAUNCHER] Aplikacja zamknięta")
            self.root.destroy()

    def run(self):
        self.root.mainloop()


if __name__ == "__main__":
    launcher = AIGameLauncher()
    launcher.run()