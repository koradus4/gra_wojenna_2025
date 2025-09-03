# Opis modułów AI (prosty, dla laików) - AKTUALIZACJA 3.8

Ten dokument w prostych słowach wyjaśnia do czego służy każdy plik w folderze `ai/`. Ma pomóc nowej osobie szybko zrozumieć strukturę sztucznej inteligencji w grze. **AKTUALIZACJA:** Dodano PE validation system - kluczowe zabezpieczenie ekonomiczne.

---
## 1. ai_commander.py
"Dowódca taktyczny". Koordynuje zachowania jednostek w turze: wybiera cele, grupuje żetony, porusza je, walczy, uzupełnia paliwo/siłę i kończy turę. Zawiera też klasę adaptacyjnej AI (uczy się sytuacji VP i zmienia poziom agresji). **NOWE:** Integracja z PE validation - nie może wydać więcej PE niż ma. Wiele funkcji deleguje do innych modułów.

## 2. ai_general.py
"Generał strategiczny". Wyższy poziom AI: analizuje ekonomię, punkty zwycięstwa (VP), sytuację paliwową, podejmuje decyzje jak wydać punkty (alokacja / zakupy / oszczędzanie) i (opcjonalnie) może tworzyć strategiczne rozkazy dla commanderów. **NOWE:** PE validation system - bezpieczne transfery do dowódców z walidacją. Dużo logów CSV do późniejszej analizy.

## 3. deployment_ai.py
Wystawianie (spawn) świeżo zakupionych jednostek na mapę. Szuka plików nowych tokenów i próbuje umieścić je w sensownej, wolnej pozycji startowej.

## 4. ekonomia_ai.py
**ROZSZERZONY:** Logika zakupów / wydatków z PE validation. Kalkuluje budżet, sugeruje co kupić, **NOWE:** sprawdza czy operacja nie spowoduje ujemnych PE. Zawiera funkcje bezpieczeństwa ekonomicznego.

## 5. grupowanie_ai.py
Tworzenie grup jednostek na podstawie bliskości oraz przypisywanie ich do celów. Dodatkowo potrafi ponownie przydzielić grupy gdy cel zniknął lub stał się nieaktualny.

## 6. konfiguracja_ai.py
Zbiór stałych (progi, mnożniki bonusów) – centralne miejsce na wartości liczbowo‑konfiguracyjne używane w kilku modułach. **NOWE:** Dodane stałe PE validation (progi bezpieczeństwa).

## 7. logowanie_ai.py
**ROZSZERZONY:** System logowania działań AI do plików CSV. Zapisuje każdą akcję jednostki oraz zagregowane podsumowania tur. **NOWE:** Logowanie PE flow - pełne śledzenie przepływu ekonomii między generałami i dowódcami. Ułatwia debug i analizę zachowań.

## 8. log_kategorie_ai.py
Lista nazw kategorii / tagów używanych w logach (np. TACTIC, MOVE, ERROR, **NOWE:** PE_VALIDATION, ECONOMIC_SAFETY). Pozwala filtrować logi.

## 9. obrona_ai.py
Logika obronna: wykrywa zagrożenia dla własnych jednostek i punktów, planuje odwrót oraz ustawia pozycje obronne (kto w środku, kto w sąsiadach). Grupuje jednostki wokół kluczowych hexów.

## 10. okupacja_punktow.py
Zarządza garnizonami (ile jednostek może stać na punkcie). Pilnuje rotacji – jeśli punkt traci wartość lub jednostka stoi za długo, zwalnia ją.

## 11. priorytety_ai.py
Proste matematyczne funkcje liczące priorytet punktu (wartość vs odległość przeciwnika / bonus za wolny punkt / kara jeśli już okupowany przez nas).

## 12. rajdy_ai.py
"Błyskawiczne przechwyty" – przed główną turą próbuje szybko zająć łatwe, wolne i wartościowe punkty, jeśli są w zasięgu ruchu.

## 13. reakcje_ai.py
Ataki reakcyjne: gdy przeciwnik się poruszy, AI sprawdza czy któraś z jego jednostek może natychmiast odpowiedzieć (zasięg + linię widzenia) i wykonuje kontratak.

## 14. rekomendacje_ai.py
Generuje listę prostych rekomendacji (np. "kup szybkie jednostki" albo "utrzymaj ekonomię") i może (w przyszłości) pół‑automatycznie wykonywać plan.

## 15. rozpoznanie_ai.py
System rozpoznania: zbiera dane o widocznych wrogach, grupuje ich w klastry, ocenia zagrożenia dla punktów kluczowych i zapisuje do pamięci AI.

## 16. ruch_adaptacyjny_ai.py
Dodatkowe zasady ruchu zależne od stanu strategicznego (wygrywamy → bezpiecznie; przegrywamy → agresywnie; remis → balans). Wybiera np. bezpieczniejsze hexy obok celu.

## 17. ruch_jednostek.py
Podstawowy ruch jednostek: wybór trybu (march / combat / recon) na podstawie dystansu do celu i wrogów, a potem wykonanie kroków z prostą adaptacją gdy ścieżka zablokowana.

## 18. ruch_postepowy_ai.py
"Ruch postępowy" – jeśli jednostka nie dojdzie do celu w tej turze, wybiera najlepszy punkt pośredni dający realny postęp (lub fallback jeśli teren blokuje).

## 19. smart_deployment.py
Inteligentny dobór miejsca spawnu: ocenia zagrożenia, niebronione punkty, klastry przyjaciół, unika przepełnienia i wybiera strategicznie korzystny hex. Zapisuje też szczegóły wyboru.

## 20. strategia_ai.py
Warstwa strategiczna: ocena sytuacji VP (wygrywamy / przegrywamy / remis), dostosowanie agresji, priorytetyzacja punktów oraz wybór preferowanych kategorii zakupów.

## 21. walka_ai.py
Cała logika walki: wyszukiwanie wrogów w zasięgu, obliczanie stosunku sił (uwzględnia teren i kontratak), próba flankowania, decyzja o odwrocie przy niskiej wartości bojowej i wykonanie ataku.

## 22. wybor_celow.py
Wybór celu dla pojedynczej jednostki: skanuje punkty kluczowe, liczy wynik (waga ekonomiczna / VP), zapisuje cel w pamięci tokena, szuka alternatyw gdy punkt zajęty.

## 23. zaopatrzenie_ai.py
**NOWY/ROZSZERZONY:** Uzupełnianie paliwa i siły bojowej z PE validation system. Faza przed turą oraz taktyczne uzupełnienia w trakcie (z limitami). **KLUCZOWE:** Zawiera funkcje `validate_pe_spending()`, `transfer_pe_to_commanders()`, `check_pe_balance()` - zabezpieczenia przed ujemnymi PE. Może dawać jednostkom "drugą szansę" na ruch po regeneracji.

## 24. __init__.py
Plik techniczny – pozwala traktować folder `ai` jako moduł Pythona.

## 25. logs/ (podfolder)
Zbiera wygenerowane pliki CSV i logi pomocnicze (np. testy ruchu, **NOWE:** PE flow analysis). Nie zawiera kodu logiki.

---
### Jak całość współpracuje? (AKTUALIZACJA PE VALIDATION)
1. Generał (`ai_general.py`) decyduje o wydatkach z **PE validation** i (opcjonalnie) tworzy rozkazy.
2. **PE transfer security** - bezpieczne przekazywanie PE do dowódców z walidacją.
3. Commander (`ai_commander.py`) pobiera jednostki, priorytety i planuje turę **bez możliwości ujemnych PE**.
4. Wczesny rajd (`rajdy_ai.py`) próbuje zająć wolne punkty.
5. Grupy są tworzone (`grupowanie_ai.py`) i dostają cele (`wybor_celow.py`, `priorytety_ai.py`).
6. Ruch i walka (`ruch_jednostek.py`, `ruch_postepowy_ai.py`, `walka_ai.py`).
7. Obrona i rotacje garnizonów (`obrona_ai.py`, `okupacja_punktow.py`).
8. **Bezpieczne uzupełnienia** (`zaopatrzenie_ai.py`) z PE validation.
9. Deployment nowych jednostek (`deployment_ai.py` / `smart_deployment.py`).
10. **Comprehensive logging** (`logowanie_ai.py`) z PE flow tracking.

---
### Najprostszy mentalny model (UPDATED)
- **Strategia (głowa) → Generał + PE Security**
- **Taktyka i wykonanie (ręce) → Commander + PE Controls + moduły ruchu/walki**
- Zmysły → Rozpoznanie.
- **Logistyka → Zaopatrzenie + PE Validation + Deployment.**
- Obrona / garnizony → Obrona + Okupacja.
- **Pamięć i analiza → Logi + PE Flow + zapisane cele w tokenach.**

---
### 🔒 PE VALIDATION SYSTEM - KLUCZOWE ZABEZPIECZENIE
**Problem rozwiązany:** AI mogło wydawać ujemne PE, powodując destabilizację ekonomiczną.
**Rozwiązanie:** Multi-layer protection w całym systemie AI.

**Główne komponenty:**
- `validate_pe_spending()` - sprawdza czy operacja nie spowoduje ujemnych PE
- `transfer_pe_to_commanders()` - bezpieczne transfery Generał→Dowódca
- `check_pe_balance()` - weryfikacja po każdej operacji ekonomicznej
- `block_negative_pe()` - hard stop dla nieprawidłowych operacji
- Comprehensive PE flow logging - pełne śledzenie w CSV

**Efekt:** Ekonomia AI jest teraz stabilna, bezpieczna i w pełni kontrolowana. ✅

---
Jeśli potrzebujesz bardziej szczegółowej dokumentacji technicznej (np. API funkcji) – daj znać.
