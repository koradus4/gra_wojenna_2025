from datetime import date, datetime, timedelta


def get_day_number(turn: int) -> int:
    """Zwraca numer dnia bitwy (1..), zakładając 6 tur na dobę."""
    if turn <= 0:
        return 1
    return 1 + (turn - 1) // 6


def get_day_phase(turn: int) -> str:
    """Zwraca porę dnia dla danej tury: 'rano'|'dzień'|'wieczór'|'noc'."""
    # 1=rano, 2-3=dzień, 4=wieczór, 5-6=noc
    idx = ((turn - 1) % 6) + 1
    if idx == 1:
        return "rano"
    if idx in (2, 3):
        return "dzień"
    if idx == 4:
        return "wieczór"
    return "noc"


class TurnManager:
    def __init__(self, players, game_engine=None, start_date: str | None = None):
        """
        Inicjalizuje menedżera tur.
        :param players: Lista obiektów klasy Player w ustalonej kolejności.
        :param game_engine: Instancja GameEngine przechowująca stan gry.
        :param start_date: Opcjonalna data startu bitwy w formacie 'YYYY-MM-DD'.
        """
        self.players = players
        self.current_turn = 1
        self.current_player_index = 0
        self.game_engine = game_engine

        # Opcjonalna data rozpoczęcia bitwy (np. 1939-09-09). Jeśli brak, UI pokaże "Dzień X".
        self.start_date: date | None = None
        if isinstance(start_date, str):
            try:
                self.start_date = datetime.strptime(start_date, "%Y-%m-%d").date()
            except Exception:
                self.start_date = None

        # Inicjalizacja obiektu Pogoda jako atrybutu klasy
        from core.pogoda import Pogoda
        self.weather = Pogoda()
        self.weather.generuj_pogode()
        self.current_weather = self.weather.generuj_raport_pogodowy()

    # ---- Czas i prezentacja ----
    def get_current_day_number(self) -> int:
        return get_day_number(self.current_turn)

    def get_current_day_phase(self) -> str:
        return get_day_phase(self.current_turn)

    def _format_date_short(self, d: date) -> str:
        """Format: '9 IX 1939' (rzymski miesiąc)."""
        months_roman = ["I", "II", "III", "IV", "V", "VI", "VII", "VIII", "IX", "X", "XI", "XII"]
        return f"{d.day} {months_roman[d.month - 1]} {d.year}"

    def get_current_date(self) -> str | None:
        """Zwraca sformatowaną datę kalendarzową, jeśli znana, w przeciwnym razie None."""
        if not self.start_date:
            return None
        # Dzień 1 = start_date, więc przesunięcie o (day_number-1)
        day = self.start_date + timedelta(days=self.get_current_day_number() - 1)
        return self._format_date_short(day)

    def get_ui_weather_report(self) -> str:
        """Buduje zwięzły raport do panelu pogodowego: Data | Pora dnia | Pogoda."""
        phase = self.get_current_day_phase()
        date_str = self.get_current_date()
        day_str = f"Data: {date_str}" if date_str else f"Dzień: {self.get_current_day_number()}"
        # Zwięzła pogoda z atrybutów (temperatura, zachmurzenie, opady)
        weather_str = ""
        try:
            temp = getattr(self.weather, 'temperatura', None)
            clouds = getattr(self.weather, 'zachmurzenie', None)
            precip = getattr(self.weather, 'opady', None)
            if temp is not None and clouds is not None and precip is not None:
                weather_str = f"{temp}°C, {clouds}, {precip}"
            elif hasattr(self, "current_weather") and isinstance(self.current_weather, str):
                # Awaryjnie spłaszcz istniejący raport
                weather_str = " ".join(self.current_weather.split())
        except Exception:
            pass
        parts = [day_str, f"Pora dnia: {phase}"]
        if weather_str:
            parts.append(f"Pogoda: {weather_str}")
        return " | ".join(parts)

    def rozpocznij_nowa_ture(self):
        """Rozpoczyna nową turę i generuje pogodę raz na dzień."""

        if self.current_turn % 6 == 1:  # Generowanie pogody raz na dzień (co 6 tur)
            self.weather.generuj_pogode()

        # Inkrementacja tury
        self.current_turn += 1

    def next_turn(self):
        """
        Przechodzi do następnego gracza w kolejności.
        Zwraca True, jeśli wszyscy gracze zakończyli swoje tury.
        """
        self.current_player_index += 1

        if self.current_player_index >= len(self.players):
            self.current_player_index = 0
            self.current_turn += 1

            # Reset punktów ruchu wszystkich żetonów na początku nowej tury
            if self.game_engine is not None and hasattr(self.game_engine, 'tokens'):
                for token in self.game_engine.tokens:
                    max_mp = getattr(token, 'maxMovePoints', token.stats.get('move', 0))
                    token.maxMovePoints = max_mp
                    token.currentMovePoints = max_mp
                    
                    # NOWE: Reset ograniczeń strzałów artylerii na początku nowej tury
                    if hasattr(token, 'reset_turn_actions'):
                        token.reset_turn_actions()

            if self.current_turn % 6 == 0:  # Co 6 tur generujemy nowy raport pogodowy
                self.weather.generuj_pogode()
                self.current_weather = self.weather.generuj_raport_pogodowy()

            return True  # Zakończono pełną turę

        return False

    def get_current_player(self):
        """
        Zwraca aktualnego gracza.
        :return: Obiekt klasy Player.
        """
        return self.players[self.current_player_index]

    def get_turn_info(self):
        """
        Zwraca informacje o aktualnej turze.
        :return: Słownik z informacjami o turze.
        """
        current_player = self.get_current_player()
        return {
            "turn": self.current_turn,
            "player": current_player.id,
            "nation": current_player.nation,
            "role": current_player.role,
        }

    def is_game_over(self, max_turns=10):
        """
        Sprawdza, czy gra powinna się zakończyć po osiągnięciu maksymalnej liczby tur.
        :param max_turns: Maksymalna liczba tur.
        :return: True, jeśli gra się zakończyła, False w przeciwnym razie.
        """
        return self.current_turn > max_turns