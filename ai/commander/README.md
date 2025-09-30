"""
AI Commander – moduł odpowiedzialny za dystrybucję PE do żetonów i wywoływanie ich logiki autonomicznej.

Zakres odpowiedzialności:
1. Przejmuje PE przekazane przez generała i magazynuje je w rezerwie dowódcy.
2. Na początku każdej tury odzyskuje niewykorzystane przydziały żetonów.
3. Dzieli rezerwę **po równo** pomiędzy wszystkie własne żetony (reszta zostaje w puli dowódcy).
4. Utrzymuje słownik przydziałów (`token_allowances`) oraz aktualizuje atrybuty żetonu (`ai_reserved_pe`, `ai_commander_id`).
5. Uruchamia maksymalnie 3 żetony na turę wywołując ich `execute_turn` – każdy start kosztuje 1 PE z przydziału jednostki.

Ograniczenia i gwarancje:
- Dowódca nie ingeruje w szczegółową logikę ruchu – cała taktyka jest w `TokenAI`.
- Widzi i obsługuje wyłącznie własne żetony (na podstawie `token.owner`).
- Nie może przekroczyć przydzielonych środków ani zmieniać reguł ekonomii.
- Niewykorzystane PE zawsze wracają do wspólnej puli dowódcy przed kolejną turą.
"""