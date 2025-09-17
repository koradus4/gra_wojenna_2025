# Opis modułów AI (prosty, dla laików) - AKTUALIZACJA 4.0

Ten dokument w prostych słowach wyjaśnia do czego służy każdy plik w folderze `ai/`. Ma pomóc nowej osobie szybko zrozumieć strukturę sztucznej inteligencji w grze. 

**NAJNOWSZE AKTUALIZACJE:**
- ✅ **Victory AI Phase 1-5** - kompletny system strategiczny (Phase 1-5 COMPLETE)
- ✅ **PE Validation System** - zabezpieczenie ekonomiczne  
- ✅ **VP Intelligence System** - vp_intelligence.py (Phase 5)
- 🔄 **Phase 6** - Final integration w przygotowaniu

---
## 1. ai_commander.py
"Dowódca taktyczny". Koordynuje zachowania jednostek w turze: wybiera cele, grupuje żetony, porusza je, walczy, uzupełnia paliwo/siłę i kończy turę. Zawiera też klasę adaptacyjnej AI (uczy się sytuacji VP i zmienia poziom agresji). **NOWE:** Integracja z PE validation - nie może wydać więcej PE niż ma. Wiele funkcji deleguje do innych modułów.

## 2. ai_general.py
"Generał strategiczny". Wyższy poziom AI: analizuje ekonomię, punkty zwycięstwa (VP), sytuację paliwową, podejmuje decyzje jak wydać punkty (alokacja / zakupy / oszczędzanie) i (opcjonalnie) może tworzyć strategiczne rozkazy dla commanderów. **NOWE:** PE validation system - bezpieczne transfery do dowódców z walidacją. **ZAKTUALIZOWANE:** Dynamiczny system zakupów oparty na kontekście strategicznym (force_ratio, casualties, sytuacja battlefield) zamiast sztywnych limitów liczbowych. Dużo logów CSV do późniejszej analizy.

## 3. deployment_ai.py ⚠️ **ZASTĄPIONY - UNIFIED SYSTEM**
~~Stary system wystawiania jednostek~~ **ZASTĄPIONY przez unified_deployment.py**. Legacy moduł - nie używany od wdrożenia unified systemu.

## 3a. unified_deployment.py ✅ **NOWY - UNIFIED SYSTEM**
**"Ujednolicony system deployment human+ai"**. Łączy najlepsze cechy obu systemów: niezawodność human (Token.from_json(), natychmiastowe dodanie do runtime) + inteligencję AI (smart positioning, marker system). Jeden kod dla human i AI deployment. Używa `find_optimal_spawn_position()` z smart_deployment.py + sprawdzone metody z gui/panel_mapa.py.

## 4. ekonomia_ai.py
**ROZSZERZONY:** Logika zakupów / wydatków z PE validation. Kalkuluje budżet, sugeruje co kupić, **NOWE:** sprawdza czy operacja nie spowoduje ujemnych PE. Zawiera funkcje bezpieczeństwa ekonomicznego.

## 5. grupowanie_ai.py
Tworzenie grup jednostek na podstawie bliskości oraz przypisywanie ich do celów. Dodatkowo potrafi ponownie przydzielić grupy gdy cel zniknął lub stał się nieaktualny.

## 6. konfiguracja_ai.py ⚠️ **LEGACY - CZĘŚCIOWO ZASTĄPIONY**
~~Stary zbiór stałych~~ - **ZASTĄPIONY przez ai_config.py** dla większości parametrów. Pozostały tylko niektóre stałe (rotacje garnizonów, bonusy keypoints, logi). Nowy system `get_param()` w ai_config.py jest rekomendowany dla nowych parametrów.

## 6a. ai_config.py ✅ **NOWY - CENTRALNY SYSTEM KONFIGURACJI**
**"Mózg konfiguracyjny AI"**. Zaawansowany system zarządzania parametrami z `AIConfigManager`: 
- **Profile AI:** AGGRESSIVE (0.7x min_buy), DEFENSIVE (1.3x attack), BALANCED (1.0x all), CUSTOM (ręczne)
- **Kategorie:** ECONOMY, COMBAT, LOGISTICS, STRATEGY, MOVEMENT, DEPLOYMENT, PURCHASES
- **API:** `get_param('ECONOMY.MIN_BUY')`, `set_param()`, `set_ai_profile()` 
- **GUI Integration:** Panel konfiguracji z suwakami, custom parametry zapisywane do JSON
- **29 aktywnych get_param():** walka_ai.py (6), ai_general.py (19), ekonomia_ai.py (4)
**EFEKT:** AI jest w pełni konfigurowalne bez zmiany kodu. Gracze mogą tuning przez GUI.

## 7. logowanie_ai.py
**ROZSZERZONY (PL SYSTEM):** Cienka warstwa kompatybilności przekierowująca wszystkie wywołania na polski ZaawansowanyLoggerAI. Stary system CSV został usunięty. Logowane kategorie:
- decyzje_strategiczne, akcje_taktyczne, decyzje_ekonomiczne,
- analiza_wywiadu (z intelligence_type), wydajnosc_ai, analiza_zwyciestwa.
Logger tworzy pliki w `logs/sesja_aktualna/.../ai_commander_zaawansowany/`. Commander udostępnia alias `commander.logger` wskazujący na ten logger.

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
System rozpoznania: zbiera dane o widocznych wrogach, grupuje ich w klastry, ocenia zagrożenia dla punktów kluczowych i zapisuje do pamięci AI. **NOWE:** Logi wywiadu zapisują `intelligence_type` dla pełniejszych podsumowań „Analiza wywiadu”.

## 16. ruch_adaptacyjny_ai.py
Dodatkowe zasady ruchu zależne od stanu strategicznego (wygrywamy → bezpiecznie; przegrywamy → agresywnie; remis → balans). Wybiera np. bezpieczniejsze hexy obok celu.

## 17. ruch_jednostek.py
Podstawowy ruch jednostek: wybór trybu (march / combat / recon) na podstawie dystansu do celu i wrogów, a potem wykonanie kroków z prostą adaptacją gdy ścieżka zablokowana.

## 18. ruch_postepowy_ai.py
"Ruch postępowy" – jeśli jednostka nie dojdzie do celu w tej turze, wybiera najlepszy punkt pośredni dający realny postęp (lub fallback jeśli teren blokuje).

## 19. smart_deployment.py ✅ **ENHANCED - UNIFIED INTEGRATION**
Inteligentny dobór miejsca spawnu: ocenia zagrożenia, niebronione punkty, klastry przyjaciół, unika przepełnienia i wybiera strategicznie korzystny hex. **NOWE:** Główny dostawca inteligentnego pozycjonowania dla unified_deployment.py. Funkcja `find_optimal_spawn_position()` używana przez unified system.

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

## 25. victory_ai.py ✅ **NOWY - PHASE 1-5 COMPLETE**
**"Strategiczny mózg AI"**. Zaawansowany system Victory AI z 5 fazami:
- **Phase 1:** Intelligent Scouting (72 scout checks) + Enemy Detection (uczciwy visibility)
- **Phase 2:** Multi-turn Attack Planning (4-fazowy system: POSITIONING → CONCENTRATION → ATTACK → EXPLOITATION) 
- **Phase 3:** Balanced Defense + KP Security (60% defense, 30% attack, 10% reserve + PE collection protection)
- **Phase 4:** Advanced Logistics AI (Commander-General Communication + Force Requirements Analysis)
- **Phase 5:** VP Intelligence System (Victory Points optimization + predictive modeling)
**NOWE:** Kompletne logowanie przez polski ZaawansowanyLoggerAI (wydajność, analiza zwycięstwa, decyzje). Przestarzały writer CSV został usunięty. Integruje się z ai_commander.py (alias `commander.logger`).

## 26. vp_intelligence.py ✅ **NOWY - PHASE 5 COMPLETE**
**"VP Intelligence System"**. Zaawansowany system analizy Victory Points:
- Real-time VP trend analysis + predictive modeling (next 3-5 turns)
- VP opportunity identification + enemy VP threat assessment
- Strategic VP recommendations + comprehensive CSV logging
- Integracja z Phase 1-4 dla complete strategic mastery

## 27. logs/ (podfolder)
Zbiera wygenerowane pliki CSV i logi pomocnicze (np. testy ruchu, **NOWE:** PE flow analysis, Victory AI operations, VP Intelligence logs). Nie zawiera kodu logiki.

---
### Jak całość współpracuje? (AKTUALIZACJA VICTORY AI PHASE 1-5 + PE VALIDATION + UNIFIED DEPLOYMENT)
1. **Victory AI Strategic Layer** (`victory_ai.py`) - scouting, threat assessment, attack planning, defense allocation, logistics analysis, VP intelligence
2. **VP Intelligence System** (`vp_intelligence.py`) - Victory Points optimization + predictive modeling
3. Generał (`ai_general.py`) decyduje o wydatkach z **PE validation** i (opcjonalnie) tworzy rozkazy.
4. **PE transfer security** - bezpieczne przekazywanie PE do dowódców z walidacją.
5. Commander (`ai_commander.py`) + Victory AI integration - pobiera jednostki, priorytety i planuje turę **bez możliwości ujemnych PE**.
6. Wczesny rajd (`rajdy_ai.py`) próbuje zająć wolne punkty.
7. Grupy są tworzone (`grupowanie_ai.py`) i dostają cele (`wybor_celow.py`, `priorytety_ai.py`).
8. **Victory AI Phase Execution** - multi-turn attack plans + intelligent scouting patrol + logistics analysis + VP optimization
9. Ruch i walka (`ruch_jednostek.py`, `ruch_postepowy_ai.py`, `walka_ai.py`).
10. **Victory AI Defense Coordination** + Obrona i rotacje garnizonów (`obrona_ai.py`, `okupacja_punktow.py`).
11. **Bezpieczne uzupełnienia** (`zaopatrzenie_ai.py`) z PE validation.
12. **🎯 UNIFIED DEPLOYMENT** (`unified_deployment.py`) - jeden system dla human i AI z inteligentnym pozycjonowaniem.
13. **Enhanced logging** (`logowanie_ai.py`) z PE flow tracking + Victory AI operations + VP Intelligence logs.

---
### Najprostszy mentalny model (VICTORY AI PHASE 1-5 UPDATE)
- **🧠 Strategiczny mózg → Victory AI (victory_ai.py) - scouting, planning, defense, logistics, VP intelligence**
- **🏆 VP Intelligence → VP Intelligence System (vp_intelligence.py) - Victory Points optimization + predictive modeling**
- **💰 Ekonomia (głowa) → Generał + PE Security**
- **⚔️ Taktyka i wykonanie (ręce) → Commander + Victory AI Integration + moduły ruchu/walki**
- **👁️ Zmysły → Rozpoznanie + Victory AI Enemy Detection.**
- **🚛 Logistyka → Zaopatrzenie + PE Validation + Deployment + Victory AI Logistics.**
- **🛡️ Obrona / garnizony → Victory AI Defense Allocation + Obrona + Okupacja.**
- **📊 Pamięć i analiza → Logi + PE Flow + Victory AI Operations + VP Intelligence + zapisane cele.**

---
### 🎛️ AI CONFIGURATION SYSTEM - KLUCZOWA REFAKTORYZACJA ✅
**Problem rozwiązany:** Hardcoded wartości rozproszone po 25+ modułach AI.
**Rozwiązanie:** Centralna konfiguracja z `get_param()` i profile AI.

**Główne komponenty:**
- `get_param('ECONOMY.MIN_BUY', 30)` - zamiast hardcoded MIN_BUY = 30
- **29 aktywnych get_param():** walka_ai.py (6), ai_general.py (19), ekonomia_ai.py (4)
- **Profile AI:** AGGRESSIVE/DEFENSIVE/BALANCED/CUSTOM z automatycznymi multiplierami
- **GUI Integration:** Panel konfiguracji z suwakami + JSON persistence
- **Custom Parameters:** Gracze mogą modyfikować AI przez GUI (np. THREAT_RETREAT_THRESHOLD=99)

**Efekt:** AI jest w pełni konfigurowalne, testowalną A/B testing profile. ✅

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
