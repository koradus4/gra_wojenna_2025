"""
AI General – minimalna warstwa ekonomiczna odpowiedzialna za dystrybucję punktów ekonomicznych (PE).

Kluczowe zadania:
1. W każdej turze wywołuje `EconomySystem.generate_economic_points()` oraz `add_special_points()`, dzięki czemu korzysta z tego samego generatora co gracze human.
2. Buduje „profile dowódców” na podstawie liczby żetonów oraz historycznego zużycia PE. Profile pomagają oszacować minimum (1 PE na żeton) oraz dodatkowy bufor (`headroom`).
3. Wyznacza podział rezerwy: domyślnie 15% PE jest odkładane, ale na podstawie historii (deque o długości 5) współczynnik może spaść do 10% lub wzrosnąć do 20%.
4. Przydziela resztę środków proporcjonalnie do potrzeb dowódców, zapisując decyzje w logach CSV/tekst (`ai/logs/general/...`).
5. Przekazuje środki dowódcom przy pomocy tych samych metod ekonomii (`subtract_points` generuje logi bezpieczeństwa, `commander.economy.add_economic_points` zwiększa budżet) i aktualizuje historię alokacji.

Ograniczenia i świadome uproszczenia:
- Brak wglądu w mapę – jedyną metryką zapotrzebowania jest liczba żetonów oraz średnie zużycie PE z poprzednich tur.
- Rezerwa nie jest jeszcze wykorzystywana do żadnych decyzji strategicznych; służy wyłącznie jako bufor bezpieczeństwa przeciwko nagłym brakującym PE.
- GeneralAI nie uruchamia dowódców ani żetonów – po rozdaniu środków pozostawia wykonanie tury module `CommanderAI`.
- Profil dowódcy zakłada minimalny koszt aktywacji równy liczbie żetonów (1 PE na jednostkę); nie ma priorytetowania typów jednostek.
"""