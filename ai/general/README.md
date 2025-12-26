"""
AI Generał odpowiada za ekonomiczną "warstwę strategiczną" – generuje i dystrybuuje punkty ekonomiczne (PE) do dowódców, a także raportuje wszystkie decyzje do nowych katalogów logów w `ai/logs/general/`.

Kluczowe zadania:
1. W każdej turze wywołuje `EconomySystem.generate_economic_points()` oraz `add_special_points()`, dokładnie tak jak gracze human, dlatego wszystkie premie/boni działają identycznie.
2. Buduje „profile dowódców” agregując liczbę żetonów oraz średnie zużycie PE z maksymalnie 5 poprzednich tur. Profil wyznacza minimum (1 PE na żeton), bazową konsumpcję (średnia vs fallback) oraz dodatkowy bufor (`headroom`).
3. Ustala podział rezerwy: domyślnie odkłada 15% bieżących PE, ale współczynnik adaptacyjnie zmienia się w przedziale 10–20% na podstawie realnych wydatków dowódców (historia w `deque`).
4. Wylicza zapotrzebowanie dowódców i przydziela środki proporcjonalnie do oszacowanej luki (`baseline + headroom`), zapisując szczegółowe wpisy w logach tekstowych i CSV (`ai/logs/general/...`).
5. Transferuje PE korzystając z metod ekonomii (`subtract_points`, `add_economic_points`) i aktualizuje historię budżetową każdego dowódcy, dzięki czemu kolejne tury lepiej reagują na dynamiczne potrzeby.

Ograniczenia i świadome uproszczenia:
- AI Generał nie analizuje mapy ani morale – jedyną miarą zapotrzebowania jest liczba żetonów i historyczne zużycie PE.
- Rezerwa pozostaje pasywna; służy jedynie jako bufor bezpieczeństwa przeciwko nagłym deficytom.
- GeneralAI nie aktywuje jednostek – po rozdaniu środków przekazuje sterowanie do modułu `CommanderAI`.
- Profil dowódcy zakłada koszt 1 PE na żeton; brak priorytetowania typów jednostek czy kampanii.
"""