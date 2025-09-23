import tkinter as tk
from tkinter import ttk, messagebox
import subprocess
import sys
from core.tura import TurnManager
from engine.player import Player
from gui.panel_generala import PanelGenerala
from gui.panel_dowodcy import PanelDowodcy
from core.ekonomia import EconomySystem
from engine.engine import GameEngine, update_all_players_visibility, clear_temp_visibility
from gui.panel_gracza import PanelGracza
from core.zwyciestwo import VictoryConditions
from czyszczenie.game_cleaner import clean_all_for_new_game, clean_ai_logs, clean_game_logs
from tools.maintenance.smart_log_cleaner import smart_clean_session, smart_clean_full, smart_archive_and_clean, show_ml_status
from utils.session_archiver import archive_sessions

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
        self.root.bind('<Control-Shift-L>', lambda e: self.quick_clean())
        self.root.bind('<Control-Shift-S>', lambda e: self.session_clean())  # Nowy skrót dla sesji

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
        btns = ttk.Frame(clean_frame)
        btns.grid(row=0, column=0, columnspan=4, sticky="w")
        ttk.Button(btns, text="🧹 Sesja", command=self.session_clean).grid(row=0, column=0, padx=(0, 8))
        ttk.Button(btns, text="🗑️ Pełne", command=self.full_clean).grid(row=0, column=1, padx=(0, 8))
        ttk.Button(btns, text="📚 Archiwum", command=self.archive_clean).grid(row=0, column=2, padx=(0, 8))
        ttk.Button(btns, text="📊 Status ML", command=self.show_ml_status).grid(row=0, column=3)
        
        desc_frame = ttk.Frame(clean_frame)
        desc_frame.grid(row=1, column=0, columnspan=4, sticky="w", pady=(5, 0))
        ttk.Label(desc_frame, text="Sesja: bieżąca gra (zachowuje ML) | Pełne: wszystko (zachowuje ML) | Archiwum: zapisz→wyczyść", 
                 font=("Arial", 9), foreground="gray").pack(anchor="w")
        ttk.Label(desc_frame, text="Skrót: Ctrl+Shift+S (sesja) | Status ML: info o danych uczenia maszynowego", 
                 font=("Arial", 8), foreground="gray").pack(anchor="w")
        
        # Główne przyciski - LEWA KOLUMNA
        main_button_frame = ttk.Frame(frame)
        main_button_frame.grid(row=4, column=0, columnspan=2, pady=20)

        ttk.Button(main_button_frame, text="🚀 Uruchom Grę", command=self.start_game).grid(row=0, column=0, padx=(0, 20))
        ttk.Button(main_button_frame, text="❌ Zamknij", command=self.root.quit).grid(row=0, column=1)
        # (Panel AI usunięty)

    # (Tryby test/auto/alternatywny usunięte)
    
    def quick_clean(self):
        """Szybkie czyszczenie - rozkazy strategiczne i zakupione żetony (stary system)"""
        try:
            result = messagebox.askyesno("Potwierdzenie", 
                                       "Czy na pewno chcesz wyczyścić rozkazy strategiczne i zakupione żetony?\n\n"
                                       "To usunie:\n"
                                       "• Rozkazy strategiczne AI\n"
                                       "• Zakupione żetony (nowe_dla_* + aktualne/)\n"
                                       "• Wpisy w index.json i start_tokens.json")
            if result:
                from czyszczenie.game_cleaner import quick_clean as do_quick_clean
                do_quick_clean()
                messagebox.showinfo("Sukces", "Szybkie czyszczenie zakończone pomyślnie!")
        except Exception as e:
            messagebox.showerror("Błąd", f"Błąd podczas szybkiego czyszczenia: {e}")
    
    def session_clean(self):
        """Inteligentne czyszczenie sesji - zachowuje dane ML + ŻETONY NA MAPIE"""
        try:
            result = messagebox.askyesno("Czyszczenie sesyjne", 
                                       "🧹 Wyczyścić bieżącą sesję gry?\n\n"
                                       "✅ USUWA:\n"
                                       "• Rozkazy strategiczne AI\n" 
                                       "• Zakupione żetony (foldery)\n"
                                       "• Logi z bieżącej sesji\n"
                                       "• Dane z poprzedniej gry\n\n"
                                       "💾 ZACHOWUJE:\n"
                                       "• Wszystkie dane ML\n"
                                       "• ŻETONY NA MAPIE (start_tokens.json)\n"
                                       "• Strukturę mapy (hexów)\n"
                                       "• Archiwa i raporty")
            if result:
                print("🧹 Czyszczenie sesyjne (kompletne - zachowuję ML + żetony na mapie)...")
                
                # 1. Główne czyszczenie sesji (logi, rozkazy)
                stats = smart_clean_session()
                
                # 2. DODATKOWO: Wyczyść zakupione żetony (foldery) - BEZ start_tokens.json
                try:
                    from czyszczenie.game_cleaner import clean_purchased_tokens, clean_purchased_tokens_from_index, clean_csv_logs
                    print("🪙 Czyszczenie zakupionych żetonów (foldery)...")
                    clean_purchased_tokens()  # czyści foldery nowe_dla_*, aktualne/
                    clean_purchased_tokens_from_index()  # czyści index.json
                    # NIE wywołujemy clean_purchased_tokens_from_start() - zachowujemy start_tokens.json!
                    
                    # 3. Dodatkowo wyczyść podstawowe dane gry
                    print("📄 Czyszczenie plików CSV...")
                    clean_csv_logs()  # Wyczyść pliki CSV BEZ potwierdzania
                    
                except ImportError as ie:
                    print(f"⚠️ Nie można zaimportować funkcji czyszczenia: {ie}")
                except Exception as e:
                    print(f"⚠️ Błąd podczas czyszczenia: {e}")
                
                # Wyświetl wyniki
                session_files = stats.get('session_files', 0)
                strategic_orders = stats.get('strategic_orders', 0) 
                purchased_tokens = stats.get('purchased_tokens', 0)
                preserved_ml = stats.get('preserved_ml', 0)
                
                msg = f"✅ SESJA KOMPLETNIE WYCZYSZCZONA!\n\n"
                msg += f"📄 Plików sesyjnych: {session_files}\n"
                msg += f"💾 Zachowanych ML: {preserved_ml}\n" 
                msg += f"🎯 Rozkazy strategiczne: WYCZYSZCZONE\n"
                msg += f"🪙 Żetony folderowe: WYCZYSZCZONE\n"
                msg += f"🗺️ Żetony na mapie: ZACHOWANE ✅\n"
                msg += f"� Pliki CSV: WYCZYSZCZONE"
                
                messagebox.showinfo("Czyszczenie sesyjne", msg)
        except Exception as e:
            messagebox.showerror("Błąd czyszczenia", f"Błąd podczas czyszczenia sesji:\n{e}")
    
    def archive_clean(self):
        """Archiwizuj sesję i wyczyść"""
        try:
            result = messagebox.askyesno("Archiwizacja", 
                                       "📚 Zarchiwizować i wyczyścić sesję?\n\n"
                                       "1. Zapisze wszystkie logi z dzisiaj do archive/\n"
                                       "2. Wyczyści bieżącą sesję\n"
                                       "3. Zachowa wszystkie dane ML\n\n"
                                       "Idealny sposób na zakończenie dnia gry!")
            if result:
                print("📚 Archiwizacja i czyszczenie...")
                stats = smart_archive_and_clean()
                
                msg = f"✅ Sesja zarchiwizowana i wyczyszczona!\n\n"
                msg += f"📦 Zarchiwizowano: {stats.get('archived_files', 0)} plików\n"
                msg += f"📊 w tym ML datasets: {stats.get('ml_datasets', 0)}\n"
                msg += f"🧹 Wyczyszczono: {stats.get('session_files', 0)} plików sesyjnych"
                
                messagebox.showinfo("Archiwizacja", msg)
        except Exception as e:
            messagebox.showerror("Błąd archiwizacji", f"Błąd podczas archiwizacji:\n{e}")
    
    def show_ml_status(self):
        """Pokaż status danych ML"""
        try:
            from tools.maintenance.smart_log_cleaner import SmartLogCleaner
            cleaner = SmartLogCleaner()
            stats = cleaner.get_ml_stats()
            
            if stats.get('status') == 'brak_danych_ml':
                msg = "❌ Brak danych ML\n\nUruchom kilka gier aby wygenerować datasety."
            else:
                msg = f"📊 STATUS DANYCH ML\n\n"
                msg += f"📄 Plików CSV: {stats['csv_files']}\n"
                msg += f"📋 Plików meta: {stats['meta_files']}\n" 
                msg += f"💾 Rozmiar: {stats['total_size_kb']:.1f} KB\n\n"
                msg += "📊 Datasety:\n"
                
                for ds in stats['datasets']:
                    msg += f"• {ds['name']}: {ds['records']} rek., {ds['features']} cech ({ds['size_kb']:.1f} KB)\n"
            
            messagebox.showinfo("Status ML", msg)
        except Exception as e:
            messagebox.showerror("Błąd", f"Błąd sprawdzania statusu ML:\n{e}")
    
    def full_clean(self):
        """Pełne czyszczenie - wszystkie dane gry (zachowuje ML) - BEZ ŻETONÓW Z HEXÓW!"""
        try:
            result = messagebox.askyesno("Pełne czyszczenie", 
                                       "🗑️ PEŁNE CZYSZCZENIE DANYCH GRY?\n\n"
                                       "✅ USUWA:\n"
                                       "• Rozkazy strategiczne AI\n"
                                       "• Zakupione żetony (foldery)\n"
                                       "• WSZYSTKIE logi sesyjne\n"
                                       "• Stare logi AI i game\n"
                                       "• Pliki CSV\n\n"
                                       "💾 ZACHOWUJE:\n"
                                       "• Wszystkie dane ML!\n"
                                       "• ŻETONY NA MAPIE (hexach)!\n"
                                       "• start_tokens.json\n"
                                       "• Strukturę mapy (tereny, punkty)\n\n"
                                       "⚠️ UWAGA: RESET DANYCH GRY!")
            if result:
                print("🗑️ PEŁNE CZYSZCZENIE DANYCH GRY (BEZ żetonów z hexów)...")
                
                # 1. Standardowe pełne czyszczenie (zachowuje ML)
                stats = smart_clean_full()
                
                # 2. DODATKOWO: Wyczyść zakupione żetony (foldery) 
                try:
                    from czyszczenie.game_cleaner import clean_purchased_tokens, clean_purchased_tokens_from_index, clean_csv_logs
                    print("🪙 Czyszczenie zakupionych żetonów (foldery)...")
                    clean_purchased_tokens()  # czyści foldery nowe_dla_*, aktualne/
                    clean_purchased_tokens_from_index()  # czyści index.json
                    # NIE wywołujemy clean_purchased_tokens_from_start() - zachowujemy start_tokens.json!
                    
                    # 3. Wyczyść pliki CSV
                    print("📄 Czyszczenie plików CSV...")
                    clean_csv_logs()  # BEZ potwierdzania w terminalu
                    
                except Exception as e:
                    print(f"⚠️ Błąd podczas dodatkowego czyszczenia: {e}")
                
                msg = f"✅ PEŁNE CZYSZCZENIE ZAKOŃCZONE!\n\n"
                msg += f"📄 Plików sesyjnych: {stats.get('session_files', 0)}\n"
                msg += f"🗑️ Starych plików: {stats.get('old_files', 0)}\n"
                msg += f"💾 Zachowanych ML: {stats.get('preserved_ml', 0)}\n"
                msg += f"🎯 Rozkazy: WYCZYSZCZONE ✅\n"
                msg += f"🪙 Żetony folderowe: WYCZYSZCZONE ✅\n"
                msg += f"🗺️ Żetony z hexów: ZACHOWANE ✅\n"
                msg += f"📍 start_tokens.json: ZACHOWANY ✅"
                
                messagebox.showinfo("Pełne czyszczenie", msg)
        except Exception as e:
            messagebox.showerror("Błąd", f"Błąd podczas pełnego czyszczenia: {e}")

    def clean_logs_only(self):
        """Czyści tylko logi CSV (AI + actions) bez ruszania rozkazów i zakupionych żetonów"""
        try:
            result = messagebox.askyesno(
                "Potwierdzenie",
                "Wyczyścić TYLKO logi CSV?\n\nUsuwa:\n• WSZYSTKIE pliki *.csv w logs/\n• Wszystkie podfoldery z CSV\n\nNie usuwa rozkazów ani nowych żetonów.")
            if result:
                from czyszczenie.game_cleaner import clean_csv_logs
                clean_csv_logs()
                messagebox.showinfo("Sukces", "Wszystkie logi CSV wyczyszczone!")
        except Exception as e:
            messagebox.showerror("Błąd", f"Błąd czyszczenia logów: {e}")

    def start_game(self):
        try:
            # Pytaj o automatyczne czyszczenie przed grą
            result = messagebox.askyesno("Czyszczenie przed grą", 
                                       "Czy wyczyścić dane z poprzedniej sesji?\n\n"
                                       "Usuwa:\n"
                                       "• Stare rozkazy strategiczne AI\n"
                                       "• Zakupione żetony z poprzedniej gry\n\n"
                                       "Rekomendowane dla fair start!")
            if result:
                print("🧹 Auto-czyszczenie przed nową grą...")
                from czyszczenie.game_cleaner import quick_clean
                quick_clean()
            else:
                print("ℹ️ Pominięto czyszczenie - kontynuacja poprzedniej sesji")
            
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
