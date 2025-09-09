from gui.ekran_startowy import EkranStartowy
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

# AI GENERAŁ I DOWÓDCA IMPORT (odporny na brak modułu ai)
try:
    from ai import AIGeneral, is_ai_general, set_ai_general_enabled  # type: ignore
    from ai.ai_commander import AICommander  # Import AI Commander
except Exception:  # brak modułu lub klasy – degradacja łagodna
    class AIGeneral:  # minimalny stub
        def __init__(self, *_args, **_kwargs):
            pass
        def make_turn_decisions(self):
            print("[AI-STUB] Pomijam decyzje – brak implementacji AI.")
    class AICommander:  # minimalny stub
        def __init__(self, *_args, **_kwargs):
            pass
        def make_turn(self, engine):
            print("[AI-STUB] Pomijam turę AI Commander – brak implementacji.")
    def is_ai_general(_p):
        return False
    def set_ai_general_enabled(_flag):
        print("[AI-STUB] Flaga AI zignorowana – brak modułu ai.")




def main():
    """Główna funkcja gry"""
    try:
        # Ekran startowy
        root = tk.Tk()
        ekran_startowy = EkranStartowy(root)
        root.mainloop()

        # Sprawdź czy użytkownik wybrał dane gry
        try:
            game_data = ekran_startowy.get_game_data()
            miejsca = game_data["miejsca"]
            czasy = game_data["czasy"]
            use_ai_general = game_data.get("use_ai_general", False)  # Odczytanie opcji AI
            max_turns = game_data.get("max_turns", 10)  # Nowe opcje gry
            victory_mode = game_data.get("victory_mode", "turns")
            
            print(f"🎯 Opcje gry: {max_turns} tur, tryb: {victory_mode}")
            
            # NOWE: Automatyczne czyszczenie przed nową grą
            print("\n🧹 Automatyczne czyszczenie przed nową grą...")
            quick_clean()
            print("✅ Czyszczenie zakończone\n")
            
            # Ustawienie konfiguracji AI na podstawie wyboru użytkownika
            set_ai_general_enabled(use_ai_general)
        except AttributeError:
            print("❌ Nie wybrano danych gry - kończę")
            return

        # Inicjalizacja silnika gry (GameEngine jako źródło prawdy)
        game_engine = GameEngine(
            map_path="data/map_data.json",
            tokens_index_path="assets/tokens/index.json",
            tokens_start_path="assets/start_tokens.json",
            seed=42,
            read_only=True  # Zapobiega nadpisywaniu pliku mapy
        )

        # Walidacja konfiguracji miejsc (minimum 3 sloty na każdą nację)
        if miejsca.count("Polska") < 3 or miejsca.count("Niemcy") < 3:
            print("❌ Konfiguracja miejsc nieprawidłowa – potrzeba min. 3 pozycji dla każdej nacji.")
            return

        # Funkcja pomocnicza do zbudowania listy graczy w ustalonej kolejności
        def build_players(miejsca, czasy):
            polska_gen = miejsca.index("Polska")
            polska_dow1 = miejsca.index("Polska", polska_gen+1)
            polska_dow2 = miejsca.index("Polska", polska_dow1+1)
            niemcy_gen = miejsca.index("Niemcy")
            niemcy_dow1 = miejsca.index("Niemcy", niemcy_gen+1)
            niemcy_dow2 = miejsca.index("Niemcy", niemcy_dow1+1)
            if niemcy_gen < polska_gen:
                return [
                    Player(4, "Niemcy", "Generał", czasy[niemcy_gen]),
                    Player(5, "Niemcy", "Dowódca", czasy[niemcy_dow1]),
                    Player(6, "Niemcy", "Dowódca", czasy[niemcy_dow2]),
                    Player(1, "Polska", "Generał", czasy[polska_gen]),
                    Player(2, "Polska", "Dowódca", czasy[polska_dow1]),
                    Player(3, "Polska", "Dowódca", czasy[polska_dow2]),
                ]
            else:
                return [
                    Player(1, "Polska", "Generał", czasy[polska_gen]),
                    Player(2, "Polska", "Dowódca", czasy[polska_dow1]),
                    Player(3, "Polska", "Dowódca", czasy[polska_dow2]),
                    Player(4, "Niemcy", "Generał", czasy[niemcy_gen]),
                    Player(5, "Niemcy", "Dowódca", czasy[niemcy_dow1]),
                    Player(6, "Niemcy", "Dowódca", czasy[niemcy_dow2]),
                ]

        players = build_players(miejsca, czasy)

        # Uzupełnij economy dla wszystkich graczy (Generał i Dowódca)
        from core.ekonomia import EconomySystem
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
        
        # Uruchomienie gry Human vs Human (z możliwością AI Generałów)
        run_human_vs_human_game(game_engine, players, turn_manager, max_turns, victory_mode)
        
    except Exception as e:
        print(f"❌ Błąd w main(): {e}")
        import traceback
        traceback.print_exc()

def run_human_vs_human_game(game_engine, players, turn_manager, max_turns, victory_mode):
    """Uruchomienie gry w trybie Human vs Human (z możliwością AI Generałów)"""
    print("🎮 Uruchamianie gry Human vs Human...")
    print(f"🎯 Opcje: {max_turns} tur, tryb: {victory_mode}")
    print(f"   Utworzono {len(players)} graczy:")
    for p in players:
        ai_status = " [AI]" if is_ai_general(p) else ""
        print(f"   - {p.name} ({p.nation}, {p.role}){ai_status}")
    
    # --- WARUNKI ZWYCIĘSTWA z nowymi opcjami ---
    victory_conditions = VictoryConditions(max_turns=max_turns, victory_mode=victory_mode)
    just_loaded_save = False  # flaga informująca pętlę by pominąć reset ruchu
    last_loaded_player_info = None  # dane gracza po wczytaniu save (tymczasowe)
    
    # Pętla tur - używamy logiki z main_alternative.py
    while True:
        # Jeśli po wczytaniu save jest info o aktywnym graczu, przełącz na niego
        if last_loaded_player_info:  # obsługa wczytania save na początku iteracji
            # Po load_game lista graczy mogła się zmienić – zsynchronizuj
            players = game_engine.players
            turn_manager.players = players  # zapewnij spójność
            update_all_players_visibility(players, game_engine.tokens, game_engine.board)
            # Wybierz aktywnego gracza
            found = None
            for p in players:
                if (str(p.id) == str(last_loaded_player_info.get('id')) and
                    p.role == last_loaded_player_info.get('role') and
                    p.nation == last_loaded_player_info.get('nation')):
                    found = p
                    break
            current_player = found if found else turn_manager.get_current_player()
            if found:
                turn_manager.current_player_index = players.index(found)
            # Nie czyść last_loaded_player_info tutaj dopóki nie zakończysz pełnej iteracji
        else:
            current_player = turn_manager.get_current_player()
            
        update_all_players_visibility(players, game_engine.tokens, game_engine.board)
        
        print(f"\n🏆 TURA {turn_manager.current_turn}: {current_player.name} ({current_player.nation}, {current_player.role})")
        
        # Faza startowa tury gracza (ekonomia / generowanie) – tylko raz na wejście Generała
        app = None
        if current_player.role == "Generał":
            # Generowanie ekonomii przed stworzeniem GUI (by panel startował ze świeżymi danymi)
            start_points = current_player.economy.economic_points
            current_player.economy.generate_economic_points()
            current_player.economy.add_special_points()
            available_points = current_player.economy.get_points()['economic_points']
            print(f"  💰 Generowanie ekonomii: {start_points} → {available_points} punktów")
            if is_ai_general(current_player):
                ai_general = AIGeneral(current_player, game_engine, players)
                ai_general.make_turn_decisions()
                app = None
            else:
                app = PanelGenerala(turn_number=turn_manager.current_turn, ekonomia=current_player.economy, gracz=current_player, gracze=players, game_engine=game_engine)
        elif current_player.role == "Dowódca":
            # Sprawdź czy dowódca jest AI
            if hasattr(current_player, 'is_ai_commander') and current_player.is_ai_commander:
                print(f"🤖 AI Commander {current_player.id} wykonuje turę...")
                ai_commander = AICommander(current_player)
                ai_commander.make_turn(game_engine)
                app = None
            else:
                app = PanelDowodcy(turn_number=turn_manager.current_turn, remaining_time=current_player.time_limit * 60, gracz=current_player, game_engine=game_engine)
        
        # Patch dla save/load funkcjonalności - tylko dla paneli graficznych
        if app is not None:
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
                            nonlocal last_loaded_player_info, just_loaded_save
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

            # Znajdź i zaaplikuj patch dla save/load - tylko dla paneli graficznych
            if hasattr(app, 'left_frame'):
                for child in app.left_frame.winfo_children():
                    if isinstance(child, PanelGracza):
                        patch_on_load(child)

        # --- USTAW AKTUALNEGO GRACZA W SILNIKU (DLA PANEL_MAPA) ---
        game_engine.current_player_obj = current_player

        # Aktualizacja pogody dla panelu - tylko dla paneli graficznych
        if app is not None and hasattr(app, 'update_weather'):
            app.update_weather(turn_manager.current_weather)
            
        # Aktualizacja punktów ekonomicznych dla paneli generałów - tylko dla paneli graficznych
        if app is not None and isinstance(app, PanelGenerala):
            # Panel już ma zaktualizowaną ekonomię (generowanie wykonane wcześniej)
            app.update_economy(current_player.economy.get_points()['economic_points'])
            # Bezpieczne wywołanie suwaki (metoda może oczekiwać innych atrybutów – opakuj)
            try:
                app.zarzadzanie_punktami(current_player.economy.get_points()['economic_points'])
            except Exception:
                pass

        # Aktualizacja punktów ekonomicznych dla paneli dowódców - tylko dla paneli graficznych
        if app is not None and isinstance(app, PanelDowodcy):
            przydzielone_punkty = current_player.economy.get_points()['economic_points']
            app.update_economy(przydzielone_punkty)  # Aktualizacja interfejsu dowódcy
            # --- Synchronizacja punktów ekonomicznych dowódcy z systemem ekonomii ---
            current_player.punkty_ekonomiczne = przydzielone_punkty

        # Uruchomienie panelu graficznego - tylko dla ludzi
        if app is not None:
            try:
                app.mainloop()  # Uruchomienie panelu
            except Exception as e:
                print(f"Błąd panelu: {e}")

        # Przejście do kolejnego gracza i zwrócenie informacji czy zakończyła się pełna tura
        is_full_turn_end = turn_manager.next_turn()
        
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
                
        # Po obsłużeniu iteracji – końcowe czyszczenie flag wczytania
        if last_loaded_player_info:
            last_loaded_player_info = None
        just_loaded_save = False
        clear_temp_visibility(players)

if __name__ == "__main__":
    main()