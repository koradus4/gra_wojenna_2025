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

# --- Safe stdout encoding (unikaj UnicodeEncodeError w konsoli cp1250) ---
try:
    import sys
    if hasattr(sys.stdout, 'reconfigure'):
        sys.stdout.reconfigure(encoding='utf-8', errors='ignore')
except Exception:
    pass

# 🎚️ POZIOM DEBUGOWANIA - łatwa kontrola komunikatów
DEBUG_LEVEL = "BASIC"  # "BASIC" = tylko kupowanie/wystawianie, "FULL" = wszystkie szczegóły

def debug_print(message, level="BASIC", category="INFO"):
    """Drukuje komunikaty tylko gdy poziom debugowania pozwala"""
    if DEBUG_LEVEL == "FULL":
        print(f"[{category}] {message}")
    elif DEBUG_LEVEL == "BASIC" and level == "BASIC":
        print(f"🎯 {message}")

print("🚀 GRA WOJENNA - GŁÓWNY LAUNCHER")
print(f"🎚️ Poziom debugowania: {DEBUG_LEVEL}")
print("💡 Zmiana debug: w konsoli wpisz 'BASIC' lub 'FULL'")
print("-" * 50)

def change_debug_level():
    """Funkcja do zmiany poziomu debugowania przez konsole"""
    global DEBUG_LEVEL
    try:
        import sys
        import select
        if sys.stdin in select.select([sys.stdin], [], [], 0)[0]:
            line = input().strip().upper()
            if line in ["BASIC", "FULL"]:
                DEBUG_LEVEL = line
                print(f"🎚️ Zmieniono poziom debug na: {DEBUG_LEVEL}")
    except:
        pass  # Ignoruj błędy input w GUI


class GameLauncher:
    def __init__(self):
        self.root = tk.Tk()
        self.root.title("Gra Wojenna 2025 - Launcher")
        
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
        # UI
        self.setup_ui()
        self.root.bind('<Control-Shift-L>', lambda _e: self.clean_logs_gui())

    def setup_ui(self):
        # Główny frame (jedna kolumna – bez AI)
        self.root.columnconfigure(0, weight=1)
        self.root.rowconfigure(0, weight=1)
        
        main_frame = ttk.Frame(self.root, padding="20")
        main_frame.grid(row=0, column=0, sticky="nsew")
        
        # Pojedyncza kolumna
        main_frame.columnconfigure(0, weight=1, minsize=800)
        main_frame.rowconfigure(0, weight=1)
        
        # Tytuł i opcje gry
        frame = ttk.Frame(main_frame)
        frame.grid(row=0, column=0, sticky="nsew")
        
        ttk.Label(frame, text="🎮 Gra Wojenna 2025", font=("Arial", 16, "bold")).grid(row=0, column=0, columnspan=2, pady=(0, 20))
        # (Konfiguracja AI usunięta)
        # Opcje gry
        game_frame = ttk.LabelFrame(frame, text="Opcje gry", padding="15")
        game_frame.grid(row=2, column=0, columnspan=2, sticky="ew", pady=(0, 20))
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
        desc_frame = ttk.Frame(game_frame)
        desc_frame.grid(row=5, column=0, sticky="w", padx=(20, 0), pady=(5, 0))
        ttk.Label(desc_frame, text="• VP: Gra do końca, zwycięzca na podstawie punktów", font=("Arial", 9), foreground="gray").pack(anchor="w")
        ttk.Label(desc_frame, text="• Eliminacja: Koniec gdy jeden naród zostanie", font=("Arial", 9), foreground="gray").pack(anchor="w")
        # Czyszczenie
        clean_frame = ttk.LabelFrame(frame, text="Czyszczenie danych", padding="15")
        clean_frame.grid(row=3, column=0, columnspan=2, sticky="ew", pady=(0, 20))
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
        
        # Główne przyciski - LEWA KOLUMNA
        main_button_frame = ttk.Frame(frame)
        main_button_frame.grid(row=4, column=0, columnspan=2, pady=20)

        ttk.Button(main_button_frame, text="🚀 Uruchom Grę", command=self.start_game).grid(row=0, column=0, padx=(0, 20))
        ttk.Button(main_button_frame, text="❌ Zamknij", command=self.root.quit).grid(row=0, column=1)
        # (Panel AI usunięty)

    # (Tryby test/auto/alternatywny usunięte)
    
    def clean_logs_gui(self):
        """Czyści katalog `logs/` z poziomu GUI."""
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
                "Start gry",
                "Rozpocząć nową grę z aktualnymi ustawieniami?\n\n"
                "W razie potrzeby użyj przycisku 'Wyczyść logi', aby przed startem opróżnić katalog logs/.",
            )
            if not proceed:
                print("ℹ️ Start gry został anulowany przez użytkownika")
                return

            self.root.destroy()
            self.launch_game_with_settings()
        except Exception as e:
            messagebox.showerror("Błąd", f"Uruchomienie gry nieudane: {e}")

    def launch_game_with_settings(self):
        debug_print("🚀 ROZPOCZYNANIE DIAGNOSTYKI MAIN_AI.PY", "BASIC", "STARTUP")
        
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
        debug_print("🔥 KONIEC DIAGNOSTYKI", "FULL", "DIAGNOSTICS")
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
        # Tryb human vs human – brak AI
        for player in players:
            player.is_ai = False
            player.is_ai_commander = False
        for p in players:
            if not hasattr(p, 'economy') or p.economy is None:
                p.economy = EconomySystem()
        game_engine.players = players
        
        update_all_players_visibility(players, game_engine.tokens, game_engine.board)
        for p in players:
            if hasattr(p, 'punkty_ekonomiczne'):
                p.punkty_ekonomiczne = p.economy.get_points()['economic_points']
        turn_manager = TurnManager(players, game_engine=game_engine)
        
        # Nowe ustawienia zwycięstwa
        max_turns_val = int(self.max_turns.get())
        victory_mode_val = self.victory_mode.get()
        
        print(f"🎯 Ustawienia gry: {max_turns_val} tur, tryb: {victory_mode_val}")
        
        victory_conditions = VictoryConditions(max_turns=max_turns_val, victory_mode=victory_mode_val)
        self.main_game_loop(players, turn_manager, victory_conditions, game_engine)
    def main_game_loop(self, players, turn_manager, victory_conditions, game_engine):
        just_loaded_save = False
        last_loaded_player_info = None
        while True:
            # Ustaw kontekst tury (dla pór dnia/mnożników widoczności)
            try:
                from utils.turn_context import set_current_turn
                set_current_turn(turn_manager.current_turn)
            except Exception:
                pass
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
            # Prosty debug – zawsze tura człowieka
            print(f"👤 TURA CZŁOWIEKA: {current_player.id} ({current_player.nation} {current_player.role})")
            
            # DODANE: Logowanie stanu key pointów na początku tury
            game_engine.log_key_points_status(current_player)
            
            update_all_players_visibility(players, game_engine.tokens, game_engine.board)
            # Tylko gałąź człowieka
            if current_player.role == "Generał":
                app = PanelGenerala(turn_number=turn_manager.current_turn, ekonomia=current_player.economy, gracz=current_player, gracze=players, game_engine=game_engine)
            elif current_player.role == "Dowódca":
                app = PanelDowodcy(turn_number=turn_manager.current_turn, remaining_time=current_player.time_limit * 60, gracz=current_player, game_engine=game_engine)
            else:
                app = None
            if app and hasattr(app, 'update_weather'):
                app.update_weather(turn_manager.get_ui_weather_report())
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
            # Zaktualizuj kontekst tury po zmianie
            try:
                from utils.turn_context import set_current_turn
                set_current_turn(turn_manager.current_turn)
            except Exception:
                pass
            if is_full_turn_end:
                game_engine.process_key_points(players)
            game_engine.update_all_players_visibility(players)
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
                    print(f"{emoji} {p.nation} {p.role} (id={p.id}): {vp} VP")
                    
                print("\n💡 WARUNKI ZWYCIĘSTWA:")
                print(f"• Tryb: {victory_info['victory_mode']}")
                print(f"• Limit tur: {victory_info['max_turns']}")
                print(f"• Powód zakończenia: {victory_info['victory_reason']}")
                print("="*50)
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

    def on_closing(self):
        """Obsługuje zamykanie aplikacji z archiwizacją sesji"""
        try:
            print("🔚 [MAIN] Zamykanie aplikacji...")
            
            # Archiwizacja sesji przed zamknięciem
            print("📦 [MAIN] Archiwizacja sesji...")
            stats = archive_sessions()
            
            if stats['archived'] > 0:
                print(f"✅ [MAIN] Zarchiwizowano {stats['archived']} sesji")
                if stats['cleaned'] > 0:
                    print(f"🗑️ [MAIN] Wyczyszczono {stats['cleaned']} starych sesji")
            else:
                print("ℹ️ [MAIN] Brak sesji do archiwizacji")
            
        except Exception as e:
            print(f"⚠️ [MAIN] Błąd podczas archiwizacji: {e}")
        finally:
            # Zawsze zamknij aplikację
            print("👋 [MAIN] Aplikacja zamknięta")
            self.root.destroy()

    def run(self):
        self.root.mainloop()


if __name__ == "__main__":
    launcher = GameLauncher()
    launcher.run()
