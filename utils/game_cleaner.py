"""Warstwa zgodności: dawniej funkcje czyszczenia były w utils.game_cleaner.
Aktualnie główny plik znajduje się w czyszczenie/game_cleaner.py.
Ten plik tylko przekierowuje importy, żeby nie ruszać istniejących zależności.
"""

try:  # pragma: no cover - proste przekierowanie
    from czyszczenie.game_cleaner import *  # noqa: F401,F403
except Exception as e:  # awaryjna informacja gdyby struktura się zmieniła
    raise ImportError(
        "Nie mogę załadować czyszczenie.game_cleaner. Sprawdź czy plik 'czyszczenie/game_cleaner.py' istnieje. Oryginalny błąd: " + str(e)
    )
