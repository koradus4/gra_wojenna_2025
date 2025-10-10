"""
AI Commander – warstwa pośrednia między Generałem a TokenAI.

Stan obecny:
1. Synchronizuje się z `EconomySystem` gracza (tworzy instancję, jeśli brakuje), odczytuje dostępne PE i zapisuje wartość w `player.punkty_ekonomiczne`.
2. Filtruje `game_engine.tokens` po ownerze w formacie `"{player_id} ({nation})"`, dzięki czemu obsługuje wyłącznie własne jednostki.
3. Dzieli budżet **po równo** (`total_pe // liczba_żetonów`) pomiędzy wszystkie posiadane żetony – nadal brak limitu 3 jednostek i brak dodatkowych priorytetów.
4. Dla każdego żetonu tworzy `TokenAI`, przekazuje przydzielony budżet, porównuje wydane PE z przydziałem, rejestruje zwroty i szczegóły przebiegu w logach (`ai/logs/commander/...`).
5. Po zakończeniu tury sumuje wydatki, raportuje refundy/unassigned PE i zwraca niewykorzystane środki do ekonomii dowódcy (`economy.economic_points = remaining`).
6. Obsługuje kolejkę wzmocnień (`player.ai_reinforcement_queue`): weryfikuje budżet, zajętość pól spawnu z mapy, tworzy blueprint żetonu (przez `balance.model.compute_token`) i wystawia jednostkę (`Token.from_json`) wraz z logowaniem i historią (`player.ai_reinforcement_history`).

Ważne ograniczenia:
- Brak atrybutów typu `ai_reserved_pe` – dowódca nie utrzymuje indywidualnych kont dla żetonów.
- Nie ma rotacji/wyboru priorytetów; każdy żeton próbuje wykonać turę w kolejności z listy `tokens`.
- Nie agreguje informacji z mapy – cała taktyka spoczywa na `TokenAI` i logice silnika.
- System logów (`ai/logs/commander/...`) stanowi jedyne źródło informacji o wydatkach i zwrotach PE oraz planowanym podziale.
- Kolejka wzmocnień wymaga poprawnych danych wejściowych (typ/rozmiar jednostki, budżet). Przy braku środków zamówienia pozostają w kolejce; brak wolnych pól spawnu również nie usuwa zamówienia.
- Maksymalnie kilka wzmocnień na turę (domyślnie 2) – parametr `player.ai_reinforcement_cap` pozwala regulować liczbę spawnów.
"""