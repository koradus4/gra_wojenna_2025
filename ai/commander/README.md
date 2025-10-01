"""
AI Commander – warstwa pośrednia między Generałem a TokenAI.

Stan obecny:
1. Synchronizuje się z `EconomySystem` gracza (tworzy instancję, jeśli brakuje) i odczytuje dostępne PE.
2. Filtruje `game_engine.tokens` po ownerze w formacie `"{player_id} ({nation})"`, dzięki czemu obsługuje wyłącznie własne jednostki.
3. Dzieli budżet **po równo** pomiędzy wszystkie posiadane żetony – brak limitu 3 jednostek i brak dodatkowych priorytetów.
4. Dla każdego żetonu tworzy `TokenAI`, przekazuje przydzielony budżet, zbiera informację o rzeczywiście wydanych PE i loguje wyniki.
5. Po zakończeniu tury zwraca niewykorzystane środki do ekonomii dowódcy (`economy.economic_points = remaining`).

Ważne ograniczenia:
- Brak atrybutów typu `ai_reserved_pe` – dowódca nie utrzymuje indywidualnych kont dla żetonów.
- Nie ma rotacji/wyboru priorytetów; każdy żeton próbuje wykonać turę w tej samej kolejności, jak pojawił się na liście.
- Nie agreguje informacji z mapy – cała taktyka spoczywa na `TokenAI` i logice silnika.
- System logów (`ai/logs/commander/...`) stanowi jedyne źródło informacji o wydatkach i zwrotach PE.
"""