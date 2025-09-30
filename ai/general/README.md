"""
AI General – warstwa ekonomiczna AI zarządzająca wyłącznie dystrybucją punktów ekonomicznych (PE).

Zakres odpowiedzialności:
1. W każdej turze generuje PE i punkty specjalne korzystając z `EconomySystem`.
2. Rezerwuje 10% świeżo wygenerowanych PE na potrzeby strategiczne (utrzymywane przy generale).
3. Pozostałe 90% dzieli równo pomiędzy dowódców tej samej nacji.
4. Przekazuje środki do dowódców korzystając z tych samych metod ekonomii co gracz human (`subtract_points`, `add_economic_points`).
5. Loguje plan dystrybucji i finalny stan ekonomii w plikach `ai/logs/general/…`.

Ograniczenia:
- Nie podejmuje decyzji taktycznych ani nie steruje żetonami – jedyną akcją jest transfer PE.
- Działa tylko na graczach o roli "Dowódca" należących do tej samej nacji.
- Musi przestrzegać stanu ekonomii – nie może wydać więcej punktów niż posiada.
"""