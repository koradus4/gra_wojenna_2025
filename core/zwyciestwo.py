# Plik do dalszej implementacji

class VictoryConditions:
    def __init__(self, max_turns=30, victory_mode="turns"):  # domyślnie 30 rund
        """
        Inicjalizuje warunki zwycięstwa.
        :param max_turns: Maksymalna liczba tur (10, 20, 30).
        :param victory_mode: Tryb zwycięstwa - "turns" (standardowy) lub "elimination" (eliminacja)
        """
        self.max_turns = max_turns
        self.victory_mode = victory_mode
        self.game_over = False
        self.winner_nation = None
        self.victory_reason = ""

    def check_game_over(self, current_turn, players=None):
        """
        Sprawdza, czy gra się zakończyła.
        :param current_turn: Aktualny numer tury.
        :param players: Lista graczy (potrzebna dla trybu eliminacji).
        :return: True, jeśli gra się zakończyła, False w przeciwnym razie.
        """
        if self.game_over:
            return True
            
        # Sprawdzenie limitu tur
        # Uwaga: używamy '>' zamiast '>=' aby zakończenie następowało PO pełnej turze,
        # czyli dopiero gdy licznik tury został zwiększony na początku kolejnego cyklu.
        if current_turn > self.max_turns:
            self.game_over = True
            self.victory_reason = f"Osiągnięto maksymalną liczbę tur ({self.max_turns})"
            
            # W trybie punktowym wyznacz zwycięzcę
            if self.victory_mode == "turns" and players:
                self._determine_victory_points_winner(players)
            
            return True
        
        # Sprawdzenie eliminacji (tylko w trybie elimination)
        if self.victory_mode == "elimination" and players:
            return self._check_elimination_victory(players)
            
        return False

    def _check_elimination_victory(self, players):
        """Sprawdza warunki zwycięstwa przez eliminację"""
        # Grupuj graczy po narodach
        nations_alive = {}
        for player in players:
            if player.nation not in nations_alive:
                nations_alive[player.nation] = False
            
            # Sprawdź czy gracz ma żywe jednostki (używamy globalnego game_engine jeśli dostępny)
            try:
                from engine.engine import GameEngine
                # Znajdź aktywny GameEngine w module
                game_engine = None
                import sys
                for name, obj in sys.modules.items():
                    if hasattr(obj, 'game_engine') and hasattr(obj.game_engine, 'tokens'):
                        game_engine = obj.game_engine
                        break
                        
                if game_engine and player.has_living_units(game_engine):
                    nations_alive[player.nation] = True
                else:
                    # Fallback - sprawdź czy ma dowolne tokeny (bez sprawdzania HP)
                    nations_alive[player.nation] = True  # Zakładamy że żyje
            except:
                # W przypadku błędu zakładaj że naród żyje
                nations_alive[player.nation] = True
        
        # Policz żywych narodów
        alive_nations = [nation for nation, alive in nations_alive.items() if alive]
        
        if len(alive_nations) <= 1:
            self.game_over = True
            if len(alive_nations) == 1:
                self.winner_nation = alive_nations[0]
                self.victory_reason = f"Zwycięstwo przez eliminację - {self.winner_nation} zniszczył wszystkich wrogów!"
            else:
                self.victory_reason = "Remis - wszyscy gracze zostali wyeliminowani!"
            return True
            
        return False

    def _determine_victory_points_winner(self, players):
        """Wyznacza zwycięzcę na podstawie Victory Points"""
        nation_vp = {}
        for player in players:
            vp = getattr(player, "victory_points", 0)
            if player.nation not in nation_vp:
                nation_vp[player.nation] = 0
            nation_vp[player.nation] += vp
        
        if nation_vp:
            winning_nation = max(nation_vp.keys(), key=lambda x: nation_vp[x])
            max_vp = nation_vp[winning_nation]
            
            # Sprawdź czy jest remis
            winners = [nation for nation, vp in nation_vp.items() if vp == max_vp]
            
            if len(winners) > 1:
                self.victory_reason += f" - REMIS! Narody {', '.join(winners)} mają po {max_vp} VP"
            else:
                self.winner_nation = winning_nation
                self.victory_reason += f" - Zwycięstwo {winning_nation} z {max_vp} Victory Points!"

    def get_victory_message(self):
        """
        Zwraca wiadomość o zakończeniu gry.
        :return: Komunikat o zakończeniu gry.
        """
        if self.victory_mode == "elimination":
            return f"Gra zakończona! {self.victory_reason}"
        else:
            return f"Gra zakończona! {self.victory_reason}"

    def get_victory_info(self):
        """Zwraca szczegółowe informacje o zwycięstwie"""
        return {
            "game_over": self.game_over,
            "winner_nation": self.winner_nation,
            "victory_reason": self.victory_reason,
            "victory_mode": self.victory_mode,
            "max_turns": self.max_turns
        }
