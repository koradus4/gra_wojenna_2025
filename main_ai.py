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
from utils.game_cleaner import clean_all_for_new_game, quick_clean, clean_ai_logs, clean_game_logs

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

print("🚀 GRA WOJENNA - GŁÓWNY LAUNCHER Z AI")
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
        self.root.geometry("900x820")
        try:
            self.root.minsize(900, 820)
        except Exception:
            pass
        # Zmienne sterujące
        self.ai_polish_general = tk.BooleanVar()
        self.ai_german_general = tk.BooleanVar()
        self.ai_polish_commander_1 = tk.BooleanVar()
        self.ai_polish_commander_2 = tk.BooleanVar()
        self.ai_german_commander_1 = tk.BooleanVar()
        self.ai_german_commander_2 = tk.BooleanVar()
        self.max_turns = tk.StringVar(value="10")
        self.victory_mode = tk.StringVar(value="turns")
        # UI
        self.setup_ui()
        self.root.bind('<Control-Shift-L>', lambda e: self.clean_logs_only())

    def setup_ui(self):
        frame = ttk.Frame(self.root, padding="20")
        frame.grid(row=0, column=0, sticky="nsew")
        ttk.Label(frame, text="Gra Wojenna 2025", font=("Arial", 16, "bold")).grid(row=0, column=0, columnspan=2, pady=(0, 20))
        # Konfiguracja AI
        lf = ttk.LabelFrame(frame, text="Konfiguracja AI", padding="15")
        lf.grid(row=1, column=0, columnspan=2, sticky="ew", pady=(0, 20))
        ttk.Label(lf, text="Generałowie:", font=("Arial", 11, "bold")).grid(row=0, column=0, sticky="w", pady=(0, 5))
        ttk.Checkbutton(lf, text="Polski Generał (id=1) - AI", variable=self.ai_polish_general).grid(row=1, column=0, sticky="w", padx=(20, 0))
        ttk.Checkbutton(lf, text="Niemiecki Generał (id=4) - AI", variable=self.ai_german_general).grid(row=2, column=0, sticky="w", padx=(20, 0))
        ttk.Separator(lf, orient='horizontal').grid(row=3, column=0, sticky="ew", pady=10)
        ttk.Label(lf, text="Dowódcy polscy:", font=("Arial", 11, "bold")).grid(row=4, column=0, sticky="w", pady=(5, 5))
        ttk.Checkbutton(lf, text="Polski Dowódca 1 (id=2) - AI", variable=self.ai_polish_commander_1).grid(row=5, column=0, sticky="w", padx=(20, 0))
        ttk.Checkbutton(lf, text="Polski Dowódca 2 (id=3) - AI", variable=self.ai_polish_commander_2).grid(row=6, column=0, sticky="w", padx=(20, 0))
        ttk.Label(lf, text="Dowódcy niemieccy:", font=("Arial", 11, "bold")).grid(row=7, column=0, sticky="w", pady=(10, 5))
        ttk.Checkbutton(lf, text="Niemiecki Dowódca 1 (id=5) - AI", variable=self.ai_german_commander_1).grid(row=8, column=0, sticky="w", padx=(20, 0))
        ttk.Checkbutton(lf, text="Niemiecki Dowódca 2 (id=6) - AI", variable=self.ai_german_commander_2).grid(row=9, column=0, sticky="w", padx=(20, 0))
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
        btns.grid(row=0, column=0, columnspan=3, sticky="w")
        ttk.Button(btns, text="🧹 Szybkie czyszczenie", command=self.quick_clean).grid(row=0, column=0, padx=(0, 10))
        ttk.Button(btns, text="🗑️ Pełne czyszczenie", command=self.full_clean).grid(row=0, column=1, padx=(0, 10))
        ttk.Button(btns, text="🧾 Czyść logi CSV", command=self.clean_logs_only).grid(row=0, column=2)
        ttk.Label(clean_frame, text="Szybkie: rozkazy + żetony | Pełne: wszystko + logi | Logi CSV: tylko pliki", font=("Arial", 9), foreground="gray").grid(row=1, column=0, columnspan=3, pady=(5, 0))
        ttk.Label(clean_frame, text="Skrót: Ctrl+Shift+L (czyści logi AI + actions_*.csv)", font=("Arial", 8), foreground="gray").grid(row=2, column=0, columnspan=3)
        # Główne przyciski
        main_button_frame = ttk.Frame(frame)
        main_button_frame.grid(row=4, column=0, columnspan=2, pady=20)
        ttk.Button(main_button_frame, text="Start Gry", command=self.start_game).grid(row=0, column=0, padx=(0, 10))
        ttk.Button(main_button_frame, text="Test AI", command=self.test_ai).grid(row=0, column=1, padx=(0, 10))
        ttk.Button(main_button_frame, text="Wyjście", command=self.root.quit).grid(row=0, column=2)

    def test_ai(self):
        """Szybki test AI bez uruchamiania pełnej gry"""
        from ai.ai_commander import test_basic_safety
        result = test_basic_safety()
        messagebox.showinfo("Test AI", f"Test AI Commander: {'✓ OK' if result else '✗ Błąd'}")
    
    def quick_clean(self):
        """Szybkie czyszczenie - rozkazy strategiczne i zakupione żetony"""
        try:
            result = messagebox.askyesno("Potwierdzenie", 
                                       "Czy na pewno chcesz wyczyścić rozkazy strategiczne i zakupione żetony?\n\n"
                                       "To usunie:\n"
                                       "• Rozkazy strategiczne AI\n"
                                       "• Zakupione żetony (nowe_dla_*)")
            if result:
                quick_clean()
                messagebox.showinfo("Sukces", "Szybkie czyszczenie zakończone pomyślnie!")
        except Exception as e:
            messagebox.showerror("Błąd", f"Błąd podczas szybkiego czyszczenia: {e}")
    
    def full_clean(self):
        """Pełne czyszczenie - wszystkie dane gry"""
        try:
            result = messagebox.askyesno("Potwierdzenie", 
                                       "Czy na pewno chcesz wyczyścić WSZYSTKIE dane gry?\n\n"
                                       "To usunie:\n"
                                       "• Rozkazy strategiczne AI\n"
                                       "• Zakupione żetony (nowe_dla_*)\n"
                                       "• Logi AI\n"
                                       "• Logi akcji gry\n\n"
                                       "UWAGA: Ta operacja jest nieodwracalna!")
            if result:
                clean_all_for_new_game()
                messagebox.showinfo("Sukces", "Pełne czyszczenie zakończone pomyślnie!")
        except Exception as e:
            messagebox.showerror("Błąd", f"Błąd podczas pełnego czyszczenia: {e}")

    def clean_logs_only(self):
        """Czyści tylko logi CSV (AI + actions) bez ruszania rozkazów i zakupionych żetonów"""
        try:
            result = messagebox.askyesno(
                "Potwierdzenie",
                "Wyczyścić TYLKO logi CSV?\n\nUsuwa:\n• Logi AI (foldery ai_*)\n• actions_*.csv\n\nNie usuwa rozkazów ani nowych żetonów.")
            if result:
                clean_ai_logs()
                clean_game_logs()
                messagebox.showinfo("Sukces", "Logi CSV wyczyszczone!")
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
                from utils.game_cleaner import quick_clean
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
        ai_generals = {}
        ai_commanders = {}
        for player in players:
            if player.role == "Generał":
                if player.nation == "Polska" and self.ai_polish_general.get():
                    player.is_ai = True
                    ai_generals[player.id] = AIGeneral("polish")
                    debug_print(f"🤖 GENERAŁ AI aktywny: {player.nation} (id={player.id})", "BASIC", "AI_SETUP")
                elif player.nation == "Niemcy" and self.ai_german_general.get():
                    player.is_ai = True
                    ai_generals[player.id] = AIGeneral("german")
                    debug_print(f"🤖 GENERAŁ AI aktywny: {player.nation} (id={player.id})", "BASIC", "AI_SETUP")
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
                    debug_print(f"🎯 DOWÓDCA AI aktywny: {player.nation} Dowódca {player.id} (id={player.id})", "BASIC", "AI_SETUP")
                else:
                    player.is_ai_commander = False
                    debug_print(f"👤 Dowódca ludzki: {player.nation} Dowódca {player.id} (id={player.id})", "FULL", "AI_SETUP")
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
            # DODANE: Debug info o aktualnym graczu
            print(f"🔍 DEBUG: current_player = {current_player.id} ({current_player.nation} {current_player.role})")
            print(f"🔍 DEBUG: is_ai = {getattr(current_player, 'is_ai', False)}")
            print(f"🔍 DEBUG: is_ai_commander = {getattr(current_player, 'is_ai_commander', False)}")
            print(f"🔍 DEBUG: in ai_generals = {current_player.id in ai_generals}")
            print(f"🔍 DEBUG: in ai_commanders = {current_player.id in ai_commanders}")
            
            # DODANE: Logowanie stanu key pointów na początku tury
            game_engine.log_key_points_status(current_player)
            
            update_all_players_visibility(players, game_engine.tokens, game_engine.board)
            if hasattr(current_player, 'is_ai') and current_player.is_ai and current_player.id in ai_generals:
                print(f"🤖 AI GENERAL TURN: {current_player.nation} {current_player.role}")
                ai_general = ai_generals[current_player.id]
                if current_player.role == "Generał":
                    current_player.economy.generate_economic_points()
                    current_player.economy.add_special_points()
                ai_general.make_turn(game_engine)
                is_full_turn_end = turn_manager.next_turn()
            elif hasattr(current_player, 'is_ai_commander') and current_player.is_ai_commander and current_player.id in ai_commanders:
                print(f"🤖 AI COMMANDER TURN: {current_player.nation} id={current_player.id}")
                ai_commander = ai_commanders[current_player.id]
                
                # NOWE: Automatyczne uzupełnianie przed turą taktyczną
                print(f"[AI] Resupply faza dla {current_player.nation}")
                ai_commander.pre_resupply(game_engine)
                
                # Tura taktyczna
                print(f"[AI] Tactical turn dla {current_player.nation}")
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

    def run(self):
        self.root.mainloop()


if __name__ == "__main__":
    launcher = GameLauncher()
    launcher.run()
