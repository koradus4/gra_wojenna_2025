import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from core.tura import TurnManager
from engine.player import Player
from gui.panel_generala import PanelGenerala
from gui.panel_dowodcy import PanelDowodcy
from core.ekonomia import EconomySystem
from engine.engine import GameEngine, update_all_players_visibility, clear_temp_visibility
from gui.panel_gracza import PanelGracza
from core.zwyciestwo import VictoryConditions
from utils.game_cleaner import clean_all_for_new_game, quick_clean
import tkinter as tk
from tkinter import messagebox

def show_clean_options():
    """Pokazuje opcje czyszczenia i konfiguracji gry przed uruchomieniem"""
    root = tk.Tk()
    root.title("Gra Wojenna - Opcje")
    root.geometry("450x400")
    root.resizable(False, False)
    
    # Centrowanie okna
    root.update_idletasks()
    x = (root.winfo_screenwidth() // 2) - (450 // 2)
    y = (root.winfo_screenheight() // 2) - (400 // 2)
    root.geometry(f"450x400+{x}+{y}")
    
    frame = tk.Frame(root, padx=20, pady=20)
    frame.pack(fill="both", expand=True)
    
    tk.Label(frame, text="Gra Wojenna - Alternatywny Launcher", 
             font=("Arial", 14, "bold")).pack(pady=(0, 20))
    
    # Opcje gry
    game_options = {}
    
    # Liczba tur
    turns_frame = tk.LabelFrame(frame, text="Liczba tur", font=("Arial", 10, "bold"))
    turns_frame.pack(fill="x", pady=(0, 10))
    
    game_options['max_turns'] = tk.StringVar(value="10")
    
    tk.Radiobutton(turns_frame, text="10 tur (szybka gra)", 
                  variable=game_options['max_turns'], value="10").pack(anchor="w", padx=10)
    tk.Radiobutton(turns_frame, text="20 tur (standardowa)", 
                  variable=game_options['max_turns'], value="20").pack(anchor="w", padx=10)
    tk.Radiobutton(turns_frame, text="30 tur (długa kampania)", 
                  variable=game_options['max_turns'], value="30").pack(anchor="w", padx=10)
    
    # Warunki zwycięstwa
    victory_frame = tk.LabelFrame(frame, text="Warunki zwycięstwa", font=("Arial", 10, "bold"))
    victory_frame.pack(fill="x", pady=(0, 15))
    
    game_options['victory_mode'] = tk.StringVar(value="turns")
    
    tk.Radiobutton(victory_frame, text="🏆 Victory Points (porównanie po turach)", 
                  variable=game_options['victory_mode'], value="turns").pack(anchor="w", padx=10)
    tk.Radiobutton(victory_frame, text="💀 Eliminacja wroga (koniec przed limitem)", 
                  variable=game_options['victory_mode'], value="elimination").pack(anchor="w", padx=10)
    
    tk.Label(victory_frame, text="• VP: Gra do końca, zwycięzca na podstawie punktów\n• Eliminacja: Koniec gdy jeden naród zostanie",
             font=("Arial", 8), fg="gray", justify="left").pack(anchor="w", padx=10, pady=(5, 5))
    
    # Sekcja czyszczenia
    clean_frame = tk.LabelFrame(frame, text="Opcje czyszczenia", font=("Arial", 10, "bold"))
    clean_frame.pack(fill="x", pady=(0, 15))
    
    def quick_clean_action():
        try:
            result = messagebox.askyesno("Potwierdzenie", 
                                       "Czy na pewno chcesz wyczyścić rozkazy strategiczne i zakupione żetony?\n\n"
                                       "To usunie:\n"
                                       "• Rozkazy strategiczne AI\n"
                                       "• Zakupione żetony (nowe_dla_* + aktualne/)\n"
                                       "• Wpisy w index.json i start_tokens.json")
            if result:
                quick_clean()
                messagebox.showinfo("Sukces", "Szybkie czyszczenie zakończone pomyślnie!")
        except Exception as e:
            messagebox.showerror("Błąd", f"Błąd podczas szybkiego czyszczenia: {e}")
    
    def full_clean_action():
        try:
            result = messagebox.askyesno("Potwierdzenie", 
                                       "Czy na pewno chcesz wyczyścić WSZYSTKIE dane gry?\n\n"
                                       "To usunie:\n"
                                       "• Rozkazy strategiczne AI\n"
                                       "• Zakupione żetony (nowe_dla_* + aktualne/)\n"
                                       "• Wpisy w index.json i start_tokens.json\n"
                                       "• Logi AI\n"
                                       "• Logi akcji gry\n\n"
                                       "UWAGA: Ta operacja jest nieodwracalna!")
            if result:
                clean_all_for_new_game()
                messagebox.showinfo("Sukces", "Pełne czyszczenie zakończone pomyślnie!")
        except Exception as e:
            messagebox.showerror("Błąd", f"Błąd podczas pełnego czyszczenia: {e}")
    
    def start_game():
        # Zapisz opcje gry
        max_turns = int(game_options['max_turns'].get())
        victory_mode = game_options['victory_mode'].get()
        root.destroy()
        run_game(max_turns, victory_mode)
    
    clean_btn_frame = tk.Frame(clean_frame)
    clean_btn_frame.pack(pady=10)
    
    tk.Button(clean_btn_frame, text="🧹 Szybkie czyszczenie", command=quick_clean_action).pack(side="left", padx=(0, 10))
    tk.Button(clean_btn_frame, text="🗑️ Pełne czyszczenie", command=full_clean_action).pack(side="left")
    
    tk.Label(clean_frame, text="Szybkie: rozkazy + żetony (kompletne) | Pełne: wszystko + logi", 
             font=("Arial", 9), fg="gray").pack()
    
    # Główne przyciski
    main_btn_frame = tk.Frame(frame)
    main_btn_frame.pack(pady=15)
    
    tk.Button(main_btn_frame, text="▶ Start Gry", command=start_game, 
              font=("Arial", 11, "bold"), bg="#4CAF50", fg="white").pack(side="left", padx=(0, 10))
    tk.Button(main_btn_frame, text="Wyjście", command=root.quit).pack(side="left")
    
    root.mainloop()

def run_game(max_turns=10, victory_mode="turns"):
    """Uruchamia właściwą grę z podanymi opcjami"""
    print(f"🎯 Uruchamianie gry: {max_turns} tur, tryb: {victory_mode}")
    
    # Automatyczne ustawienia graczy
    miejsca = ["Polska", "Polska", "Polska", "Niemcy", "Niemcy", "Niemcy"]
    czasy = [5, 5, 5, 5, 5, 5]  # Czas na turę w minutach
    
    # Inicjalizacja silnika gry (GameEngine jako źródło prawdy)
    game_engine = GameEngine(
        map_path="data/map_data.json",
        tokens_index_path="assets/tokens/index.json",
        tokens_start_path="assets/start_tokens.json",
        seed=42,
        read_only=True  # Zapobiega nadpisywaniu pliku mapy
    )

    # Automatyczne przypisanie id dowódców zgodnie z ownerami żetonów
    # Polska: dowódcy id=2,3; Niemcy: dowódcy id=5,6
    # Ustal kolejność graczy na podstawie miejsc i ról, aby pierwszym był generał wybranej nacji
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

    # Uzupełnij economy dla wszystkich graczy (Generał i Dowódca)
    for p in players:
        if not hasattr(p, 'economy') or p.economy is None:
            p.economy = EconomySystem()

    # --- UDOSTĘPNIJ LISTĘ GRACZY W GAME_ENGINE ---
    game_engine.players = players

    # --- AKTUALIZACJA WIDOCZNOŚCI NA START ---
    update_all_players_visibility(players, game_engine.tokens, game_engine.board)

    # --- SYNCHRONIZACJA PUNKTÓW EKONOMICZNYCH DOWÓDCÓW Z SYSTEMEM EKONOMII ---
    for p in players:
        if hasattr(p, 'punkty_ekonomiczne'):
            p.punkty_ekonomiczne = p.economy.get_points()['economic_points']

    # Inicjalizacja menedżera tur
    turn_manager = TurnManager(players, game_engine=game_engine)
    # --- WARUNKI ZWYCIĘSTWA z nowymi opcjami ---
    victory_conditions = VictoryConditions(max_turns=max_turns, victory_mode=victory_mode)
    just_loaded_save = False  # Flaga: czy właśnie wczytano save
    # Pętla tur
    last_loaded_player_info = None  # Przechowuj info o aktywnym graczu po wczytaniu save
    while True:
        # Ustaw kontekst tury dla mnożników pory dnia
        try:
            from utils.turn_context import set_current_turn
            set_current_turn(turn_manager.current_turn)
        except Exception:
            pass
        # Jeśli po wczytaniu save jest info o aktywnym graczu, przełącz na niego
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
        update_all_players_visibility(players, game_engine.tokens, game_engine.board)
        if current_player.role == "Generał":
            app = PanelGenerala(turn_number=turn_manager.current_turn, ekonomia=current_player.economy, gracz=current_player, gracze=players, game_engine=game_engine)
        elif current_player.role == "Dowódca":
            app = PanelDowodcy(turn_number=turn_manager.current_turn, remaining_time=current_player.time_limit * 60, gracz=current_player, game_engine=game_engine)
        # Patch: podmień funkcję on_load w PanelGracza, by ustawiać last_loaded_player_info
        def patch_on_load(panel_gracza):
            def new_on_load():
                import os
                from tkinter import filedialog, messagebox
                saves_dir = os.path.join(os.getcwd(), 'saves')
                os.makedirs(saves_dir, exist_ok=True)
                path = filedialog.askopenfilename(
                    filetypes=[('Plik zapisu', '*.json')],
                    initialdir=saves_dir
                )
                if path:
                    try:
                        from engine.save_manager import load_game
                        global last_loaded_player_info
                        global just_loaded_save
                        last_loaded_player_info = load_game(path, game_engine)
                        just_loaded_save = True
                        if hasattr(panel_gracza.master, 'panel_mapa'):
                            panel_gracza.master.panel_mapa.refresh()
                        if last_loaded_player_info:
                            msg = f"Gra została wczytana!\nAktywny gracz: {last_loaded_player_info.get('role','?')} {last_loaded_player_info.get('id','?')} ({last_loaded_player_info.get('nation','?')})"
                            messagebox.showinfo("Wczytanie gry", msg)
                        else:
                            messagebox.showinfo("Wczytanie gry", "Gra została wczytana!")
                        panel_gracza.winfo_toplevel().destroy()  # Zamknij całe okno, nie tylko ramkę
                    except Exception as e:
                        messagebox.showerror("Błąd wczytywania", str(e))
            panel_gracza.on_load = new_on_load
            if hasattr(panel_gracza, 'btn_load'):
                panel_gracza.btn_load.config(command=panel_gracza.on_load)

        # DEBUG: sprawdź dzieci left_frame
        if hasattr(app, 'left_frame'):
            for child in app.left_frame.winfo_children():
                if isinstance(child, PanelGracza):
                    patch_on_load(child)

        # --- USTAW AKTUALNEGO GRACZA W SILNIKU (DLA PANEL_MAPA) ---
        game_engine.current_player_obj = current_player

        # Aktualizacja pogody dla panelu
        if hasattr(app, 'update_weather'):
            app.update_weather(turn_manager.get_ui_weather_report())
        # Aktualizacja punktów ekonomicznych dla paneli generałów
        if isinstance(app, PanelGenerala):
            # Debug: bilans przed losowaniem
            start_points = current_player.economy.economic_points
            current_player.economy.generate_economic_points()
            current_player.economy.add_special_points()
            available_points = current_player.economy.get_points()['economic_points']
            app.update_economy(available_points)  # Przekazanie dostępnych punktów ekonomicznych

            # Synchronizacja dostępnych punktów w sekcji suwaków
            app.zarzadzanie_punktami(available_points)

        # Aktualizacja punktów ekonomicznych dla paneli dowódców
        if isinstance(app, PanelDowodcy):
            przydzielone_punkty = current_player.economy.get_points()['economic_points']
            app.update_economy(przydzielone_punkty)  # Aktualizacja interfejsu dowódcy
            # --- Synchronizacja punktów ekonomicznych dowódcy z systemem ekonomii ---
            current_player.punkty_ekonomiczne = przydzielone_punkty

        try:
            app.mainloop()  # Uruchomienie panelu
        except Exception as e:
            print(f"Błąd: {e}")

        # Przejście do następnej tury/podtury        # Przejście do kolejnego gracza i zwrócenie informacji czy zakończyła się pełna tura
        is_full_turn_end = turn_manager.next_turn()
        try:
            from utils.turn_context import set_current_turn
            set_current_turn(turn_manager.current_turn)
        except Exception:
            pass
          # --- ROZDZIEL PUNKTY Z KEY_POINTS tylko na koniec pełnej tury ---
        if is_full_turn_end:
            game_engine.process_key_points(players)  # Ignoruj zwracaną wartość
            
        # --- AKTUALIZUJ WIDOCZNOŚĆ NA KOŃCU KAŻDEJ TURY ---
        game_engine.update_all_players_visibility(players)
            
        # --- SPRAWDZENIE KOŃCA GRY ---
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
        # Reset blokady trybu ruchu na początku każdej tury, ale NIE po wczytaniu save
        if not just_loaded_save:
            for t in game_engine.tokens:
                t.movement_mode_locked = False
        # --- DODANE: wymuszenie aktualnej referencji gracza po wczytaniu save ---
        if just_loaded_save:
            # Po wczytaniu save'a zsynchronizuj listę players i current_player z game_engine
            players = game_engine.players
            clear_temp_visibility(game_engine.players)
            update_all_players_visibility(game_engine.players, game_engine.tokens, game_engine.board)
            # Znajdź aktualnego gracza po wczytaniu save
            found = None
            for p in game_engine.players:
                if (str(p.id) == str(last_loaded_player_info.get('id')) and
                    p.role == last_loaded_player_info.get('role') and
                    p.nation == last_loaded_player_info.get('nation')):
                    found = p
                    break
            if found:
                game_engine.current_player_obj = found
                current_player = found
            # Usunięto próbę synchronizacji panelu mapy, bo okno mogło być już zniszczone
        just_loaded_save = False
        clear_temp_visibility(players)
        # --- KONIEC DODATKU ---

if __name__ == "__main__":
    show_clean_options()
