# STRUKTURA PROJEKTU KAMPANIA 1939

## 📌 STAN BIEŻĄCY (16 września 2025) – WERSJA 4.2 – POLSKI SYSTEM LOGOWANIA + ROTACJA SESJI

**POLSKI SYSTEM LOGOWANIA - NOWOŚĆ! (15-16.09.2025)**
**Kompletna reorganizacja systemu logowania z polskimi nazwami i automatyczną rotacją sesji.**
├── main.py                      # GŁÓWNY LAUNCHER - zaawansowany AI launcher (main_ai.py → main.py)
├── requirements.txt             # Zależności
├── STRUKTURA_PROJEKTU.md        # Ten plik
├── accessibility/               # Rozszerzenia dostępności (szkielety)
├── backup/                      # System kopii zapasowych
├── core/                        # Logika „biznesowa" tur, ekonomii itd.
├── data/                        # Dane map / konfiguracja
├── docs/                        # Dokumentacja dodatkowa + System logowania
│   ├── logging/                # ✅ (NOWY) Dokumentacja systemu logowania
│   │   ├── PLAN_NOWY_SYSTEM_LOGOW_ZAKONCZONE.md # Plan polskiego systemu - UKOŃCZONY!
│   │   ├── README.md          # Przewodnik po dokumentacji systemu logowania
│   │   └── [inne pliki logging] # Analiza, implementacja, podsumowania
│   └── [inne dokumenty]       # Dokumentacje balansingu, AI, implementacji
├── edytory/                     # Edytory map / żetonów
├── engine/                      # Silnik gry (board, token, akcje, widoczność)
├── gui/                         # Panele interfejsu użytkownika
├── launchers/                   # 🚀 ALTERNATYWNE LAUNCHERY
│   ├── README.md               # Przewodnik po launcherach
│   ├── main_basic.py           # Podstawowy launcher z EkranStartowy GUI
│   ├── main_alternative.py     # Launcher z opcjami czyszczenia (szybki start)
│   └── auto_test_ai.py         # Automatyczny test AI vs AI (10 tur)
├── saves/                       # Zapisy stanu
├── scripts/                     # Skrypty porządkowe / automatyzacja
├── tests/                       # Testy (uporządkowane w podkatalogi):** AI General używał tylko podstawowe parametry i heurystyki, ograniczając inteligencję strategiczną.

**Rozwiązanie AI General Intelligence:**
- **29 nowych parametrów strategicznych** w kategorii `GENERAL_STRATEGY`
- **5 modułów inteligencji:** Purchase Strategy, Battlefield Analysis, Allocation Intelligence, Strategic Decisions, Strategic Limits
- **GUI Integration:** Nowa zakładka "🏛️ AI General" z polskimi opisami parametrów
- **4 funkcje strategiczne** wzbogacone o inteligentne parametry
- **Parametryzowana logika:** od zakupów jednostek po analizę battlefield

**Nowe komponenty inteligencji:**
- **Purchase Strategy:** Priorytetyzacja typów jednostek (P,C,A,Z,D) z wagami
- **Battlefield Analysis:** Force ratio sensitivity, opportunity/retreat thresholds
- **Allocation Intelligence:** Inteligentne wagi PE dla dowódców (fuel crisis, supply shortage)
- **Strategic Decisions:** Risk tolerance, adaptation speed, economic vs military focus
- **Strategic Limits:** Dynamiczne limity zakupów, progi kryzysu i zwycięstwa

**Zaimplementowane funkcje:**
- `_select_template()`: Inteligentna priorytetyzacja zakupów z battlefield intelligence
- `allocate_points()`: Parametryzowane wagi alokacji PE (6 czynników)
- `_determine_strategy()`: Battlefield analysis z 9 parametrami strategicznymi
- `consider_unit_purchase()`: Dynamiczne limity z adaptation speed

**Wyniki weryfikacji:**
- **AI General inicjalizacja**: Wszystkie nowe parametry działają bez błędów ✅
- **GUI Integration**: Zakładka AI General z 10 kluczowymi parametrami ✅
- **Strategic Intelligence**: 29 parametrów wpływa na 4 kluczowe funkcje decyzyjne ✅
- **Polish UX**: Pełne polskie opisy parametrów z praktycznymi przykładami ✅

**Pliki:** `ai/ai_config.py` (+29 parametrów), `gui/ai_config_panel.py` (+zakładka), `ai/ai_general.py` (4 funkcje), `PLAN_ROZWOJU_AI_SYSTEMU.md` (kompletny)

**LAUNCHER ORGANIZATION SYSTEM - NOWOŚĆ! (13.09.2025):**

**Problem:** Cztery różne pliki główne (main.py, main_ai.py, main_alternative.py, auto_game_10_turns.py) na root level powodowały zamieszanie i duplikację funkcjonalności.

**Rozwiązanie Launcher Organization:**
- **Jeden główny launcher:** `main.py` (wcześniej main_ai.py) z najzaawansowanymi funkcjami
- **Katalog launchers/:** Wszystkie alternatywne sposoby uruchomienia w jednym miejscu
- **Czytelna organizacja:** README.md z przewodnikiem po dostępnych opcjach
- **Zachowana funkcjonalność:** Wszystkie pliki działają z poprawionymi import paths

**Nowa struktura launcherów:**
- **main.py (root):** Główny zaawansowany launcher (🧠 AI, 🎚️ debug, 🧹 Smart Cleaning)
- **launchers/main_basic.py:** Podstawowy launcher z EkranStartowy GUI
- **launchers/main_alternative.py:** Szybki launcher z opcjami czyszczenia
- **launchers/auto_test_ai.py:** Automatyczny test AI vs AI (10 tur)
- **launchers/README.md:** Przewodnik po wszystkich opcjach uruchomienia

**Korzyści organizacji:**
- **Czytelny root directory:** Tylko jeden plik główny `main.py`
- **Uporządkowane alternatywy:** Wszystkie opcje w jednym katalogu z opisem
- **Zachowana funkcjonalność:** Każdy launcher działa niezależnie z właściwymi importami
- **User-friendly:** README z jasnymi rekomendacjami dla różnych przypadków użycia

**Wyniki weryfikacji:**
- **Import paths:** Wszystkie launchers działają poprawnie z nowej lokalizacji ✅
- **Funkcjonalność:** Każdy launcher zachowuje pełną kompatybilność ✅
- **Dokumentacja:** README z jasnymi instrukcjami i rekomendacjami ✅
- **Clean root:** Tylko jeden główny launcher w katalogu głównym ✅

**Pliki:** `main.py` (główny), `launchers/main_basic.py`, `launchers/main_alternative.py`, `launchers/auto_test_ai.py`, `launchers/README.md`

**POLSKI SYSTEM LOGOWANIA - NOWOŚĆ! (15-16.09.2025):**

**Problem:** System używał angielskich nazw katalogów (`current_session`) i tworzył duplikaty folderów timestampowych bez kontroli rotacji.

**Rozwiązanie Polskiego Systemu Logowania:**
- **Polskie nazwy katalogów:** `logs/sesja_aktualna/` zamiast `current_session/`
- **SessionManager Singleton:** Zapobieganie duplikatom - jeden katalog na sesję
- **Automatyczna rotacja:** Maksymalnie 5 sesji w `logs/archiwum_sesji/`
- **Separacja danych ML:** Nowy katalog `logs/dane_ml/` chroniony przed czyszczeniem
- **Inteligentne archiwizowanie:** Stare sesje automatycznie przenoszone do archiwum

**Nowe komponenty systemu:**
- **SessionManager:** Singleton zarządzający aktualną sesją z polskimi nazwami
- **Automatyczna archiwizacja:** Przenoszenie sesji do `archiwum_sesji/` z rotacją 5 sesji
- **Separacja ML:** Dane strategiczne/taktyczne/gameplay w oddzielnych katalogach
- **System czyszczenia:** Aktualizowany z obsługą polskich nazw i ochroną ML
- **Kompatybilność:** Obsługa zarówno starych jak i nowych ścieżek

**Zaimplementowana struktura:**
- `logs/sesja_aktualna/` - Bieżąca sesja z timestampem (POLSKI NAZWA)
- `logs/archiwum_sesji/` - Ostatnie 5 zakończonych sesji
- `logs/dane_ml/` - Dane uczenia maszynowego (strategiczne/taktyczne/gameplay)
- Zachowana kompatybilność z `current_session` dla starych modułów

**Wyniki weryfikacji:**
- **Polskie nazwy**: System używa `sesja_aktualna/` we wszystkich nowych modułach ✅
- **Singleton sesji**: Jeden katalog na sesję - koniec z duplikatami ✅
- **Rotacja 5 sesji**: Automatyczne kasowanie najstarszych w archiwum ✅
- **Separacja ML**: Dane ML chronione w osobnym katalogu `dane_ml/` ✅

**Pliki:** `utils/session_manager.py` (Singleton), `ai/logowanie_ai.py` (aktualizowany), `czyszczenie/` (polskie nazwy), `main.py` (archiwizacja przy zamknięciu)

**SMART LOG CLEANING SYSTEM - NOWOŚĆ! (13.09.2025):**

**Problem:** Stary system czyszczenia niszczył cenne dane ML (ai_decyzje_*.csv, ekonomia_ai_*.csv) bez ostrzeżenia, destabilizując system uczenia maszynowego.

**Rozwiązanie Smart Log Cleaning:**
- **Inteligentne czyszczenie** w `utils/smart_log_cleaner.py` z ochroną danych ML
- **3 tryby bezpiecznego czyszczenia:** session (tylko sesyjne), full (zachowaj ML), archive (pełne archiwum)
- **ML Data Protection:** Automatyczna ochrona `logs/analysis/ml_ready/` z metadanymi
- **Hierarchiczna struktura logów:** 112+ plików w organized categories (ai/, human/, game/, analysis/)
- **Integration z main launcher:** Nowe przyciski czyszczenia w `main_ai.py`

**Nowe komponenty systemu:**
- **Smart Session Clean:** Usuwa tylko logi sesyjne, zachowuje dane ML i analizy
- **Smart Full Clean:** Usuwa wszystkie logi OPRÓCZ cennych danych ML (ai_decyzje, ekonomia_ai)
- **Archive Mode:** Tworzy timestamped backup przed czyszczeniem
- **ML Status Monitor:** Real-time tracking danych ML (3 pliki CSV, 6.3 KB)
- **Safety Integration:** Stare skrypty czyszczenia teraz chronią dane ML

**Wyniki weryfikacji:**
- **ML Data Protection**: 100% zachowane przez wszystkie tryby czyszczenia ✅
- **Hierarchical Cleaning**: logs/ai/, logs/human/, logs/game/, logs/analysis/ selektywnie ✅
- **Safety Warnings**: Stare skrypty wymagają "ZNISZCZ_ML" confirmation ✅
- **Main Launcher Integration**: 4 nowe przyciski czyszczenia z user-friendly dialogs ✅

**Pliki:** `utils/smart_log_cleaner.py`, `main_ai.py` (+session/full/archive buttons), `czyszczenie/game_cleaner.py` (ML protection), `czyszczenie/czyszczenie_csv.py` (warnings)

**AI CONFIGURATION SYSTEM - KOMPLETNE ROZWIĄZANIE (13.09.2025):**

**Problem:** AI wykorzystywało hardcoded wartości rozproszone po 25+ modułach, uniemożliwiając tunowanie i A/B testing.

**Rozwiązanie AI Configuration System:**
- **Centralna konfiguracja** w `ai/ai_config.py` z `AIConfigManager`
- **Profile AI:** AGGRESSIVE (0.7x min_buy), DEFENSIVE (1.3x attack), BALANCED (1.0x all), CUSTOM
- **Kategorie parametrów:** ECONOMY, COMBAT, LOGISTICS, STRATEGY, MOVEMENT, DEPLOYMENT, PURCHASES
- **GUI Integration:** Panel konfiguracji z suwakami + JSON persistence (ai/configs/ai_config.json)
- **29 aktywnych get_param():** walka_ai.py (6), ai_general.py (19), ekonomia_ai.py (4)

**Nowe komponenty systemu:**
- `get_param('ECONOMY.MIN_BUY', 30)` - zamiast hardcoded MIN_BUY = 30
- `set_param()`, `set_ai_profile()` - dynamiczna konfiguracja 
- **Profile multipliers:** AGGRESSIVE profile → MIN_BUY = 21 (30 * 0.7)
- **Custom parameters:** THREAT_RETREAT_THRESHOLD=99 z GUI → wpływa na AI behavior
- **Hot-reload:** Zmiany parametrów bez restarta gry

**Wyniki weryfikacji (End-to-End test):**
- **Refaktoryzacja**: 29 get_param() calls zastąpiły hardcoded values ✅
- **GUI → AI workflow**: Custom parametry z GUI wpływają na zachowanie AI ✅  
- **Profile system**: AGGRESSIVE/DEFENSIVE/BALANCED działają poprawnie ✅
- **A/B Testing ready**: System gotowy do tuningu i eksperymentów ✅

**Pliki:** `ai/ai_config.py`, `ai/configs/ai_config.json`, `gui/ai_config_panel.py`, refaktoryzowane `ai/walka_ai.py`, `ai/ai_general.py`, `ai/ekonomia_ai.py`

Aktualizacja koncentruje się na: **konfigurowaniu AI przez gracza** oraz **eliminacji hardcoded wartości z systemu**.

**SYSTEM PE VALIDATION - KOMPLETNE ROZWIĄZANIE (3.09.2025):**

**Problem:** AI Generałowie i Dowódcy mogli wydawać ujemne PE, powodując destabilizację ekonomiczną gry.

**Rozwiązanie PE VALIDATION:**
- **Multi-layer protection** w `ai/zaopatrzenie_ai.py` i `core/ekonomia.py`
- **Blokada ujemnych PE** - system nie pozwala wydać więcej niż dostępne
- **Poprawne transfery PE** - Generał → Dowódcy z walidacją
- **Bilanse ekonomiczne** - wszystkie operacje PE weryfikowane
- **Comprehensive logging** - pełne śledzenie przepływu PE w CSV

**Nowe systemy bezpieczeństwa:**
- `validate_pe_spending()` - walidacja przed każdym wydatkiem
- `transfer_pe_to_commanders()` - bezpieczne transfery z logowaniem
- `check_pe_balance()` - weryfikacja bilansów po operacjach
- `block_negative_pe()` - hard stop dla ujemnych wartości
- Real-time PE tracking w logach AI

**Wyniki weryfikacji (AI vs AI test):**
- **Ujemne PE**: WYELIMINOWANE ✅
- **Transfery PE**: DZIAŁAJĄ POPRAWNIE ✅  
- **Bilanse**: ZGADZAJĄ SIĘ 100% ✅
- **Stabilność ekonomiczna**: ZAPEWNIONA ✅

**Pliki:** `auto_game_10_turns.py`, `tools/launcher_analizy_pe.py`, `tools/analizator_przeplywu_pe.py`

Aktualizacja koncentruje się na: **stabilizacji ekonomicznej systemu AI** oraz **eliminacji krytycznych bugów PE**.

NOWE (3.6):
* `casualties_turn` – liczba utraconych własnych jednostek w danej turze (turn summary)
* `new_units_turn` – liczba nowo pojawionych jednostek (spawn / zakup) w turze (turn summary)
* `skip_reason` – kolumna dodana do logu akcji (action log) – NA RAZIE pusty placeholder (diagnoza stagnacji w kolejnym kroku)

Cel: przygotowanie sygnałów do przyszłego Emergency Mode oraz analizy tempa odbudowy sił – bez modyfikacji heurystyk ruchu/zakupów.

## 🎯 SYSTEM OGRANICZENIA STRZAŁÓW ARTYLERII (POZIOM 1 - ZAIMPLEMENTOWANY 31.08.2025):

**Problem:** Artyleria była zdominowaną bronią - wysoki zasięg (3-4 hex), duży atak (12-18), mogła atakować wielokrotnie bez ograniczeń, powodując dominację "arty spam".

**Rozwiązanie:** System **1 normalny atak + 1 atak reakcyjny na turę** dla wszystkich jednostek artylerii.

**Implementacja:**
- **Token.shots_fired_this_turn** - licznik normalnych ataków w turze
- **Token.reaction_shot_used** - flaga użycia ataku reakcyjnego
- **Token.can_attack(attack_type)** - walidacja możliwości ataku
- **Token.record_attack(attack_type)** - rejestracja wykonanego ataku
- **Token.is_artillery()** - identyfikacja artylerii (AL, AC, AP)
- **Token.reset_turn_actions()** - reset na początku nowej tury

**Integracja z silnikiem:**
- **CombatAction._validate_combat()** - automatyczna walidacja przed atakiem
- **core/tura.py** i **engine/engine.py** - auto-reset na początku tury
- **Pełna kompatybilność wsteczna** - stare save'y działają bez zmian

**Wpływ na balans:**
- **Artyleria (AL, AC, AP):** Limitowana do 1+1 ataku na turę
- **Inne jednostki (P, TL, K, Z, itp.):** Bez ograniczeń
- **Zwiększona tactical depth** - każdy strzał artylerii ma większą wagę
- **Eliminacja dominacji** arty spam bez utraty użyteczności artylerii

## 🗺️ WIDOCZNOŚĆ I FOG OF WAR (ISTOTNE DLA AI) - ZAKTUALIZOWANE

**SYSTEM GRADUOWANEJ WIDOCZNOŚCI (POZIOM 1 - ZAIMPLEMENTOWANY 30.08.2025):**

**Podstawowa mechanika:**
- Dowódca: widzi heksy w zasięgu swoich żetonów + **graduation detection_level**
- Generał: agregacja widoczności dowódców + pełna wiedza o własnych jednostkach
- Aktualizacja: `engine.update_all_players_visibility(players)` po ruchach / na starcie tury

**NOWE: System graduowanej detekcji przeciwników:**
- `detection_level = f(distance, sight_range)` - krzywa nieliniowa 0.0-1.0
- **FULL INFO** (detection ≥ 0.8): Pełne dane wroga (ID, CV, typ, nacja)
- **PARTIAL INFO** (detection ≥ 0.5): Ograniczone dane (skrócone ID, przedział CV, typ szacowany)
- **MINIMAL INFO** (detection < 0.5): Minimalne dane ("Nieznany kontakt", CV="???")

**Implementacja:**
- `VisionService.calculate_detection_level(distance, sight)` - oblicza poziom
- `VisionService._add_visible_enemy_tokens()` - dodaje detection_level do visible_token_data  
- `detection_filter.py` - filtruje informacje na podstawie poziomu
- `gui/detection_display.py` - przygotowuje dane do wyświetlenia w UI
- AI Commander używa detection_level do podejmowania decyzji

**Korzyści dla rozgrywki:**
- Realistyczne rozpoznanie bez "cheat vision"
- Zwiększona wartość jednostek zwiadowczych
- AI musi radzić sobie z niepewnością tak jak człowiek
- Stopniowe odkrywanie informacji zamiast binarnego "widzi/nie widzi"

AI musi działać w ramach tej samej informacji (brak „cheat vision").

Najważniejsze zmiany od 3.3 → 3.5:
1. **System ograniczenia strzałów artylerii** - kompletny z testami i dokumentacją
2. **Aktualizacja dokumentacji** - nowe przewodniki balansowania TOKEN i HEX
3. **Czyszczenie projektów** - usunięcie starych tokenów i plików tymczasowych
4. **Testy systemowe** - weryfikacja funkcjonalności artylerii i integracji
5. **Preparacja do dalszego rozwoju** - uporządkowana struktura dla kolejnych iteracji

Status: **System artylerii zbalansowany i testowany**; gotowy do dalszych ulepszeń AI i mechanik rozgrywki.

---

## 📁 STRUKTURA KODU (REALNA + PLANOWANA)

```
projekt/
├── main.py                      # Główny launcher gry (GUI, konfiguracja)
├── main_alternative.py          # Szybki start (bez ekranu konfiguracji)
├── requirements.txt             # Zależności
├── STRUKTURA_PROJEKTU.md        # Ten plik
├── accessibility/               # Rozszerzenia dostępności (szkielety)
├── backup/                      # System kopii zapasowych
├── core/                        # Logika „biznesowa” tur, ekonomii itd.
├── data/                        # Dane map / konfiguracja
├── docs/                        # Dokumentacja dodatkowa
├── edytory/                     # Edytory map / żetonów
├── engine/                      # Silnik gry (board, token, akcje, widoczność)
├── gui/                         # Panele interfejsu użytkownika
├── saves/                       # Zapisy stanu
├── scripts/                     # Skrypty porządkowe / automatyzacja
├── tests/                       # Testy (uporządkowane w podkatalogi)
│   ├── core/                   # Testy logiki biznesowej
│   ├── engine/                 # Testy silnika gry
│   ├── gui/                    # Testy interfejsu
│   ├── integration/            # Testy integracyjne
│   └── testy_dla_podrecznika/  # Testy dokumentacyjne
├── tools/                       # Narzędzia diagnostyczne i analizy PE
│   ├── analizator_przeplywu_pe.py    # Analiza przepływu PE między generałami i dowódcami
│   ├── launcher_analizy_pe.py        # Launcher testów PE z czyszczeniem danych
│   ├── sprawdzenie_rzetelnosci_zetonow.py  # Walidacja spójności tokenów PNG/JSON
│   ├── analizator_ai_na_zywo.py      # Real-time monitoring logów AI
│   └── diagnostyka_key_points.py     # Diagnostyka systemu key points
├── utils/                       # Pomocnicze moduły + Polski System Logowania
│   ├── session_manager.py       # ✅ (NOWY) Singleton zarządzający sesjami z polskimi nazwami
│   ├── smart_log_cleaner.py     # ✅ (NOWY) Inteligentne czyszczenie logów z ochroną ML  
│   ├── ml_data_collector.py     # ✅ (NOWY) Kolektor danych ML do logs/dane_ml/
│   └── [inne utility modules]   # Helper functions i narzędzia wspomagające
├── czyszczenie/                 # System czyszczenia (UPDATED z polskimi nazwami + ML protection)
│   ├── czyszczenie_csv.py       # ✅ (UPDATED) CSV cleaning z polskimi nazwami + warnings "ZNISZCZ_ML"
│   ├── game_cleaner.py          # ✅ (UPDATED) Multi-mode cleaner z obsługą sesja_aktualna/ + ML protection
│   ├── OPIS_NARZEDZI_CZYSZCZENIA.md # ✅ (NOWY) Kompletna dokumentacja narzędzi czyszczenia
│   ├── czyszczenie_wszystkich_zetonow.py  # Token cleanup utility
│   └── czyszczenie_zakupionych_zetonow.py # Purchased tokens cleanup
└── ai/                          # Wstępny moduł sztucznej inteligencji (Faza 1 częściowa)
```

### Katalog `ai/` (stan bieżący + AI Configuration System + PE validation system)
```
ai/
├── __init__.py
├── ai_config.py               # ✅ (NOWY) Centralny system konfiguracji AI z profile/parameters
├── configs/
│   └── ai_config.json         # ✅ (NOWY) JSON persistence custom parameters z GUI
├── ai_general.py              # ✅ (REFAKTORYZOWANY) Generał AI: 19 get_param() calls
├── ai_commander.py            # (ROZSZERZONY) Dowódca AI: taktyka, ruch, PE spending controls
├── walka_ai.py                # ✅ (REFAKTORYZOWANY) Combat system: 6 get_param() calls
├── ekonomia_ai.py             # ✅ (REFAKTORYZOWANY) Ekonomia: 4 get_param() calls
├── zaopatrzenie_ai.py         # (NOWY) System PE validation i bezpiecznych transferów
├── logowanie_ai.py            # (ROZSZERZONY) Logi PE flow i economic tracking
├── wybor_celow.py             # Target selection dla jednostek
├── grupowanie_ai.py           # Adaptive grouping i koordinacja
├── ruch_jednostek.py          # Movement system z MP validation
├── okupacja_punktow.py        # Garrison management
├── obrona_ai.py               # Defensive positioning
├── rajdy_ai.py                # Opportunistic captures
├── reakcje_ai.py              # Reaction fire system
├── priorytety_ai.py           # Key points scoring
├── konfiguracja_ai.py         # ⚠️ (LEGACY) Partial constants - mostly replaced by ai_config.py
├── log_kategorie_ai.py        # Log categories definition
├── test_ai_config.py          # ✅ (NOWY) Testy systemu konfiguracji
└── logs/                      # NOWY POLSKI SYSTEM LOGOWANIA - ROTACJA + SEPARACJA ML ✅
    ├── sesja_aktualna/        # 🇵🇱 BIEŻĄCA SESJA (zamiast current_session)
    │   └── [TIMESTAMP]/       # Jeden katalog timestampowy na sesję (Singleton)
    │       ├── ai_commander/  # Logi dowódców AI (actions, turns)
    │       ├── ai_general/    # Logi generała AI (economy, strategy, keypoints)
    │       ├── vp_intelligence/# Analiza Victory Points
    │       └── specialized/   # Wyspecjalizowane logi (garrison, victory_ai)
    ├── archiwum_sesji/        # 🗄️ ARCHIWUM OSTATNICH 5 SESJI (nowy katalog)
    │   ├── 2025-09-16_14-30/ # Sesja zakończona #1 (najnowsza)
    │   ├── 2025-09-16_13-45/ # Sesja zakończona #2
    │   ├── 2025-09-16_13-20/ # Sesja zakończona #3
    │   ├── 2025-09-16_12-15/ # Sesja zakończona #4
    │   └── 2025-09-16_11-00/ # Sesja zakończona #5 (najstarsza, będzie usunięta)
    ├── dane_ml/               # 🧠 DANE UCZENIA MASZYNOWEGO (nowy, chroniony)
    │   ├── strategiczne/      # AI decision patterns, force ratios, victory patterns
    │   │   └── ai_decyzje_analiza.csv # Strategiczne decyzje AI z kontekstem
    │   ├── taktyczne/         # Combat decisions, terrain effects, unit effectiveness
    │   │   └── combat_decisions.csv  # Decyzje bojowe i ich rezultaty
    │   └── gameplay/          # Turn statistics, player actions, game flow
    │       └── turn_statistics.csv   # Statystyki tur i flow gry
    └── analysis/              # Analysis and reports ⭐ ZACHOWANE KOMPATYBILNIE
        ├── ml_ready/          # 🛡️ ML TRAINING DATA - NEVER DELETED (legacy)
        ├── raporty/           # Generated analysis reports
        └── statystyki/        # Aggregated statistics and insights
```
```
ai/
├── __init__.py
 ├── ai_general.py        # (ZAIMPLEMENTOWANE) Generał AI: analiza ekonomii, alokacja punktów, logi
 ├── state_adapter.py     # (PLAN) Ekstrakcja stanu z GameEngine → struktury AI
 ├── evaluator.py         # (PLAN) Heurystyki i funkcje oceny (scoring)
 ├── tactical_agent.py    # (PLAN) Decyzje ruchu i walki (dowódcy)
 ├── strategic_agent.py   # (PLAN) Priorytety key points, zakupy, plan tury
 ├── base_agent.py        # (PLAN) Klasy bazowe / interfejsy
 ├── decision_queue.py    # (PLAN) Kolejkowanie i filtrowanie akcji
 ├── memory/              # (PLAN) Logi i dane adaptacyjne
 └── README.md            # (PLAN) Dokumentacja modułu AI
```

### Tabela postępu faz AI (stan na 13.09.2025)

| Faza | Status | Pokrycie | Notatki |
|------|--------|----------|---------|
| 0 Dokumentacja kontraktu | ZAKOŃCZONA | 100% | API zidentyfikowane w wersji 3.0 |
| 1 Szkielet modułu | ZAKOŃCZONA | 100% | AI Commander + AI General implementowane |
| 2 Adapter stanu | ZAKOŃCZONY | 100% | PE validation + economic state management |
| 3 Ruch taktyczny | ZAKOŃCZONY | 85% | Ruch, progresywny movement, garrison limit, opportunistic capture |
| 4 Walka selektywna | ZAKOŃCZONY | 80% | System ograniczenia artylerii, PE-controlled combat, get_param() refactor |
| 5 Strategia key points | ZAKOŃCZONY | 75% | Capture + bonusy + PE-based prioritization |
| 6 Ekonomia / zakupy | ZAKOŃCZONY | 100% | ✅ **PE validation + AI Configuration System complete** |
| 7 Poziomy trudności | ZAKOŃCZONY | 75% | ✅ **Profile AI (AGGRESSIVE/DEFENSIVE/BALANCED/CUSTOM) implemented** |
| 8 Logowanie decyzji | ZAKOŃCZONY | 95% | Comprehensive PE flow logging, economic analysis |
| 9 Adaptacja | CZĘŚCIOWO | 40% | ✅ **Profile system + hot-reload**, brak ML adaptacji |

### Obecna funkcjonalność AI (3.9 - AI CONFIGURATION SYSTEM COMPLETE)

**AI GENERAL (KOMPLETNY POZIOM STRATEGICZNY + AI CONFIGURATION):**
* ✅ Pełny parytet z human generałem - VP, Key Points, faza gry
* ✅ 5 strategii adaptacyjnych (ROZWÓJ/KRYZYS_PALIWA/DESPERACJA/OCHRONA/EKSPANSJA)
* ✅ System budżetu 20-40-40 z elastycznym podziałem
* ✅ **19 get_param() calls** - eliminacja hardcoded wartości (MIN_BUY, ALLOC_RATIO, BUDGET_STRATEGIES)
* ✅ Analiza per dowódca (paliwo, combat value, typy jednostek)
* ✅ EconAction.COMBO - kombinacja alokacji + zakupów
* ✅ **PE VALIDATION SYSTEM** - eliminacja ujemnych PE, bezpieczne transfery
* ✅ **AI Configuration System** - profile AI, custom parameters z GUI
* ✅ **Economic stability** - walidacja bilansów, multi-layer protection
* ✅ Kompletne logowanie ekonomii, Key Points, strategii, PE flow
* ❌ **BRAK: MCTS algorithm, machine learning**

**AI COMMANDER (KOMPLETNY POZIOM TAKTYCZNY + PE CONTROLS):**
* ✅ Ruch (full + progresywny) z adaptacją MP i PE validation
* ✅ **PE spending controls** - brak możliwości ujemnych wydatków
* ✅ Oportunistyczne capture + priorytety dla odłączonych KP
* ✅ Garrison limit + podstawowy stub rotacji
* ✅ **Comprehensive PE logging** - pełne śledzenie wydatków
* ✅ Rozszerzone logi: path_len, path_used, progressive_used, decision_reason
* ✅ Combat system z walidacją PE przed resupply
* ✅ Turn summary: casualties_turn / new_units_turn
* ✅ **Economic safety** - blokada operacji przy niewystarczających PE
* ❌ Brak pełnej rotacji garnizonów (stabilny placeholder)
* ❌ Brak advanced retreat/reposition heurystyk

**AI CONFIGURATION SYSTEM (NOWY - 3.9):**
* ✅ **Central Configuration:** `ai_config.py` z `AIConfigManager`
* ✅ **Profile System:** AGGRESSIVE/DEFENSIVE/BALANCED/CUSTOM z multiplierami
* ✅ **29 get_param() calls:** walka_ai.py (6), ai_general.py (19), ekonomia_ai.py (4)
* ✅ **GUI Integration:** Panel konfiguracji + JSON persistence
* ✅ **Hot-reload:** Zmiany parametrów bez restarta
* ✅ **A/B Testing Ready:** Custom parametry wpływają na AI behavior
* ✅ **Categories:** ECONOMY, COMBAT, LOGISTICS, STRATEGY, MOVEMENT, DEPLOYMENT, PURCHASES

### Znane ograniczenia (3.9 - POST AI CONFIGURATION SYSTEM)

**AI GENERAL (STABILNE - PO AI CONFIGURATION):**
* ✅ **Hardcoded values resolved** - 19 get_param() calls implemented
* ✅ **Profile system implemented** - AGGRESSIVE/DEFENSIVE/BALANCED/CUSTOM
* ✅ **GUI configurable** - custom parameters from interface working
* Brak Monte Carlo Tree Search dla trudniejszych poziomów
* Brak machine learning adaptacji między grami  
* Brak opponent modeling
* ✅ **Parametrized strategies** - profile multipliers working, no more fixed values

**AI COMMANDER (STABILNE OGRANICZENIA - PO AI CONFIGURATION):**
* ✅ **PE VALIDATION RESOLVED** - system ekonomiczny bezpieczny i stabilny
* ✅ **Combat parameters configurable** - MINIMUM_ATTACK_RATIO, THREAT_RETREAT_THRESHOLD via get_param()
* ✅ **Resupply system działający** - kontrola PE, walidacja wydatków
* ✅ **Economic stability** - brak crashy ekonomicznych, poprawne bilanse
* Brak advanced risk-based combat (cv_ratio / przewidywane straty) 
* skip_reason: kolumna istnieje, podstawowe wypełnianie (potrzebne rozszerzenie)
* Brak purge martwych alokacji (budżet mrożony w sektorach 0 units)
* Brak effective_move_rate & attack_success_rate (agregaty)
* Brak zaawansowanej rotacji garnizonów (podstawowy system działa)

**SYSTEM BALANSOWANIA:**
* ✅ **Artyleria zbalansowana** - eliminacja dominacji przez ograniczenie strzałów
* ✅ **PE system bezpieczny** - eliminacja ujemnych PE, stabilna ekonomia
* ✅ **Dokumentacja kompletna** - przewodniki TOKEN i HEX balancing
* ❌ **Potrzebne dalsze testy** - wpływ na AI vs AI i długie kampanie
* ❌ **Brak reakcji AI** na nowy system (może wymagać dostrojenia heurystyk)

---

## ♻️ REFAKTORYZACJA AI COMMANDER (02.09.2025) – PODSUMOWANIE DZISIEJSZEJ SESJI

CEL: Uporządkować monolityczny plik dowódcy, wprowadzić modularną strukturę i bezpieczne wywołania aby móc iteracyjnie dodawać heurystyki (Emergency / skip_reason / resupply) bez ryzyka psucia podstawowego flow.

KLUCZOWE ZMIANY STRUKTURALNE:
* Styl funkcyjny (nagłówek pliku: brak klas, małe funkcje, ograniczenia długości) – łatwiejsze wycinanie do osobnych modułów.
* Snapshot stanu jednostek (starting_unit_ids / ending_unit_ids) → baza dla `casualties_turn` i `new_units_turn`.
* Centralizacja logowania: jednolite wywołania `log_commander_action` / `log_commander_turn` (moduł `ai.logowanie_ai`).
* Dodane kolumny schematu (action: `skip_reason`; turn: `casualties_turn`, `new_units_turn`).
* Fallback importów (try/except) – gdy moduł nie istnieje, Commander nie przerywa tury (degradacja łagodna zamiast crash).

WYDZIELONE / DOCZEPUJĄCE SIĘ MODUŁY (refaktoryzacja etapowa):
| Obszar | Moduł | Status |
|--------|-------|--------|
| Wybór celów | `ai.wybor_celow` | używany (find_target, alternatywy) |
| Grupowanie / koordynacja | `ai.grupowanie_ai` | używany (adaptive_grouping, reassignment) |
| Ruch / tryb ruchu | `ai.ruch_jednostek` | używany (move_towards, choose_movement_mode) |
| Okupacja / garnizony | `ai.okupacja_punktow` | używany (enforce_garrison_limits) |
| Obrona | `ai.obrona_ai` | podłączone funkcje oceny zagrożeń |
| Rajdy / capture opportunistyczne | `ai.rajdy_ai` | delegacja opportunistic_capture_phase |
| Walka | `ai.walka_ai` | delegaty (ratio, flank, execute) |
| Reakcje | `ai.reakcje_ai` | reaction fire sprawdzany po ruchu |
| Zaopatrzenie | `ai.zaopatrzenie_ai` | stałe & liczniki (paliwo / resupply future) |
| Priorytety KP | `ai.priorytety_ai` | czyste funkcje scoringu (bonusy / kary) |

BEZPIECZEŃSTWO / OGRANICZENIE RYZYKA:
* Limit iteracji (cięcia list) przy pętlach: `[:200]`, `[:80]` – zapobiega wzrostowi kosztu przy większych mapach.
* `getattr(..., default)` wszędzie → brak twardych zależności przy brakujących polach.
* Try/except wokół importów modułów eksperymentalnych.
* Test jednostkowy (minimalny) sprawdzający obecność nowych kolumn logów – sanity gate przy kolejnych zmianach.

CO JESZCZE DO DOKOŃCZENIA (NA BAZIE NOWEJ STRUKTURY):
* Implementacja realnych wartości `skip_reason` (źródła stagnacji: NO_PATH, ZERO_MP, GARRISON_HOLD, LOW_FUEL, BLOCKED).
* Agregaty: `effective_move_rate` (moved_units / eligible_movers) & `attack_success_rate` (successful_attacks / attempted_attacks).
* Emergency Mode – wyzwalacz oparty o trend `casualties_turn` + niski stosunek `new_units_turn`.
* Resupply logika właściwa (obecnie placeholder pre_resupply) – wykorzystanie paliwa i progów CV.
* Purge martwych alokacji sektorów – zwalnianie „zamrożonych” budżetów.
* Risk‑based combat gating (cv_ratio & projected losses) – wpięcie przed `execute_ai_combat`.

OGRANICZENIA OBECNEJ IMPLEMENTACJI (TECHNICZNE):
* `casualties_turn` zakłada zniknięcie ID = utrata – nie rozróżnia jeszcze transferu / despawn eventów specjalnych.
* Brak osobnej warstwy state adapter dla Commandera – część ekstrakcji stanu nadal inline.
* Brak izolowanych testów funkcji scoringu (priorytety KP) – tylko log diagnostyczny TOP 8.
* Brak mechanizmu throttle dla spamujących debug_print przy FULL – potencjalny koszt IO.

WERYFIKACJA: Commander po refaktoryzacji przechodzi test logów (generuje plik z nowymi kolumnami). Brak regresji w podstawowym ruchu (przejścia pętli taktycznej). 

Następna iteracja: wypełnianie `skip_reason` + dodanie liczników ataków (attempted/success) w `walka_ai` do agregacji.

---

## 🧠 ARCHITEKTURA LOGICZNA

| Warstwa | Obecnie | Rola w AI |
|---------|---------|-----------|
| Engine (`engine/`) | TAK | Dostarcza prymitywy: ruch, walka, widoczność, stan |
| Core (`core/`) | TAK | Tury, ekonomia (key points), warunki zwycięstwa |
| GUI (`gui/`) | TAK | Interakcja człowieka – dla AI nieużywana (AI działa programowo) |
| Edytory | TAK | Generowanie/scenariusze testowe |
| AI (`ai/`) | CZĘŚCIOWO | Ekonomia (alokacja), analiza stanu – brak ruchu i walk |

---

## 🔌 PUBLICZNY KONTRAKT DLA AI

### 1. Silnik (`GameEngine` w `engine/engine.py`)
Kluczowe atrybuty/metody dostępne bez zmian kodu:
- `engine.tokens` – lista obiektów `Token`
- `engine.board` – obiekt planszy
- `engine.turn`, `engine.current_player`
- `engine.execute_action(action, player)` → `(success, message)` / `ActionResult`
- `engine.end_turn()` / `engine.next_turn()`
- `engine.process_key_points(players)` – przydział ekonomii
- `engine.update_all_players_visibility(players)` – aktualizacja FOW
- `engine.key_points_state` – słownik key points

### 2. Token (`engine/token.py`)
Pola: `id, owner, q, r, stats{move, combat_value, defense_value, attack{value, range}, sight, price, nation}`
Dynamiczne: `currentMovePoints, currentFuel, combat_value, movement_mode`
Metody: `apply_movement_mode(reset_mp=True)`, `get_movement_points()`, `can_move_reason()`

### 3. Plansza (`engine/board.py`)
- `find_path(start, goal, max_mp, max_fuel, visible_tokens=null, fallback_to_closest=False)`
- `hex_distance(a, b)`
- `get_tile(q, r)` → `Tile(move_mod, defense_mod, type, value, spawn_nation)`
- `is_occupied(q, r)` / `neighbors(q, r)`

### 4. Akcje (`engine/action_refactored_clean.py`)
- `MoveAction(token_id, dest_q, dest_r)`
- `CombatAction(attacker_id, defender_id)`
- `ActionResult(success, message, data)`

### 5. Widoczność
- Po wywołaniu `update_all_players_visibility`: `player.visible_hexes`, `player.visible_tokens`
- Generał: pełna widoczność własnych + wrogowie odkryci przez dowódców

### 6. Key Points
- Format: `key_points_state['q,r'] = {initial_value, current_value, type}`
- Pozostała „żywotność” = `ceil(current_value / (0.1 * initial_value))` tur

### 7. (Do dodania) API zakupów – proponowany kontrakt
```
engine.purchase_unit(player, blueprint_id, spawn_hex) -> (success: bool, msg: str, token_id: Optional[str])
```
Walidacja: dostępne punkty ekonomiczne, poprawny spawn (`tile.spawn_nation == player.nation`), unikalność ID.

---

## 🧩 UPROSZCZONY WIDOK STANU DLA AI (PROPOZYCJA)
```jsonc
{
  "turn": 7,
  "player": {"id": 2, "role": "dowódca", "nation": "Polska"},
  "economy": {"points": 40},
  "key_points": [ {"q":3,"r":-1,"type":"city","current":70,"ours":true} ],
  "self_tokens": [ {"id":"P_INF_1","q":3,"r":0,"cv":5,"mp":5,"fuel":10,"atk":4,"rng":2,"def":3} ],
  "enemy_visible": [ {"id":"N_TANK_2","q":5,"r":0,"cv":8,"rng":1} ],
  "map": {"cols": X, "rows": Y}
}
```

---

## 🧮 HEURYSTYKA STARTOWA (ITERACJA 1)
Formuła punktacji heksa docelowego:  
`SCORE = (V_strategiczna + V_ofensywna - R_ryzyko) / (1 + koszt_ruchu)`

Składniki:
- `V_strategiczna`: +współczynnik * (typ key point * pozostałe tury życia) + bonus za `defense_mod`
- `V_ofensywna`: możliwość ataku na jednostkę o niskim `combat_value` / wysokiej cenie
- `R_ryzyko`: liczba wrogich kontrataków * przewidywane straty
- `koszt_ruchu`: suma kosztów MP trasy (A*)

Progi decyzji (konfigurowalne):
- Nie atakuj jeśli przewidywane straty > 60% własnego `combat_value`
- Priorytet key pointu jeśli wyczerpie się w ≤ 3 turach
- Unikaj pól w zasięgu ≥ 3 wrogich jednostek o zasięgu ataku

---

## 🔄 PLAN WDROŻENIA AI (FAZY)

| Faza | Zakres | Artefakty | Kryterium sukcesu |
|------|--------|-----------|-------------------|
| 0 | Dokumentacja kontraktu | Ten plik | API kompletne bez refactoru silnika |
| 1 | Szkielet modułu | `ai/` + klasy bazowe | Import działa, test pusty przechodzi |
| 2 | Adapter stanu | `state_adapter.py` | Zwraca spójny JSON dla dowódcy i generała |
| 3 | Ruch taktyczny | `tactical_agent.py` | Jednostki przemieszczają się legalnie do celu |
| 4 | Walka selektywna | Ewaluator | AI eliminuje osłabione jednostki bez suicydów |
| 5 | Strategia key points | `strategic_agent.py` | AI kieruje ≥50% ruchów ku kluczowym celom |
| 6 | Ekonomia / zakupy | purchase API | Nowe jednostki poprawnie spawnują się |
| 7 | Poziomy trudności | konfiguracja wag | Różne style zachowań (defensywne/agresywne) |
| 8 | Logowanie decyzji | `memory/` | Powtarzalność przy identycznym seed |
| 9 | Adaptacja (opcjonalnie) | analityka wag | Poprawa wyniku VP w serii testów |

---

## 🧪 REKOMENDOWANE TESTY (NOWE DLA AI)
- `test_ai_state_adapter.py` – poprawność formatu i filtrowanie widoczności
- `test_ai_path_selection.py` – wybór najkorzystniejszej ścieżki (mniejszy koszt)
- `test_ai_target_selection.py` – selekcja celu o najlepszym stosunku (wartość / ryzyko)
- `test_ai_key_point_focus.py` – ruch w stronę krytycznego key pointu
- `test_ai_purchase_logic.py` – brak nadwyżek ekonomii i validacja spawnów
- `test_ai_determinism.py` – identyczne decyzje dla ustalonego seeda

---

## 📊 STATYSTYKI (AKTUALNE – WERSJA 3.1)
- Edytor żetonów: 1427 linii
- Edytor map: 1088 linii
- Silnik (engine + akcje + board + token): ~850+ linii
- GUI: ~1000+ linii
- Moduł AI: wstępny (2 pliki: `__init__.py`, `ai_general.py`) – kod alokatora + logika analizy

Funkcjonalności potwierdzone: ruch, walka, pathfinding, widoczność warstwowa, key points z ekonomią, zapis stanu, refaktoryzowane akcje.

---

## 🏆 SYSTEM KEY POINTS – SKRÓT TECHNICZNY
- Struktura w `engine.key_points_state`
- Przydział ekonomii: `give = max(1, int(0.1 * initial_value))` (nie większy niż `current_value`)
- Po wyzerowaniu usunięcie z mapy + zapis aktualizacji

Sugestia dla AI: planowanie kolejki przejęć według (pozostałe_tury * typ_wagi) – (dystans MP).

---

## 🗺️ WIDOCZNOŚĆ I FOG OF WAR (ISTOTNE DLA AI)
- Dowódca: widzi tylko heksy w zasięgu swoich żetonów (+ tymczasowe)
- Generał: agregacja widoczności dowódców + pełna wiedza o własnych jednostkach
- Aktualizacja: `engine.update_all_players_visibility(players)` po ruchach / na starcie tury

AI musi działać w ramach tej samej informacji (brak „cheat vision”).

---

## 🔐 ZASADY FAIR PLAY DLA AI
- Brak podejmowania akcji na podstawie niewidocznych wrogów
- Brak modyfikacji punktów ruchu / paliwa poza systemem
- Zakupy tylko przez publiczne API zakupów
- Decyzje deterministyczne przy ustalonym seed (testowalność)

---

## 🧭 NASTĘPNE KROKI (PRIORYTETY TECHNICZNE – AKTUALNE 13.09.2025)

### **COMPLETED - AI CONFIGURATION SYSTEM ✅**
~~1. AI Configuration System - eliminacja hardcoded wartości~~
~~2. Profile AI - AGGRESSIVE/DEFENSIVE/BALANCED/CUSTOM~~
~~3. GUI Integration - panel konfiguracji + JSON persistence~~
~~4. Refactoring - 29 get_param() calls w 3 modułach~~
~~5. Hot-reload system - zmiany parametrów bez restarta~~

### **COMPLETED - PE VALIDATION SYSTEM ✅**
~~1. PE validation system - eliminacja ujemnych PE~~
~~2. Economic stability - bezpieczne transfery PE~~
~~3. Comprehensive PE logging - pełne śledzenie przepływu~~
~~4. Multi-layer protection - walidacja na wszystkich poziomach~~

### **COMPLETED - SMART LOG CLEANING SYSTEM ✅**
~~1. Smart log cleaner - inteligentne czyszczenie z ochroną ML~~
~~2. ML Data Protection - automatyczne zabezpieczenie cennych danych~~
~~3. Hierarchical cleaning - selektywne czyszczenie kategorii logów~~  
~~4. Main launcher integration - user-friendly cleaning buttons~~
~~5. Safety warnings - legacy scripts z konfirmacją "ZNISZCZ_ML"~~

### **IMMEDIATE PRIORITIES – AI OPTIMIZATION POST-PE-FIX**
1. ✅ **AI Combat Logic Fix** - poprawiona logika oceny siły wroga (attack/defense zamiast HP)
2. **Advanced skip_reason** implementation - rozszerzona diagnostyka stagnacji
3. **Emergency Mode trigger** oparty o casualties_turn + PE shortage
4. **Purge martwych alokacji** - reset po 3 turach z total_units == 0
5. **Enhanced resupply logic** - optymalizacja PE spending priorities
6. **Garrison rotation system** - zaawansowany management okupacji
7. **Attack success rate tracking** - metryki skuteczności walk

### **MEDIUM TERM – SYSTEM OPTIMIZATION**
8. **AI vs AI balance testing** - długie kampanie z PE validation
9. **Economic efficiency metrics** - analiza wykorzystania PE
10. **Advanced combat risk assessment** - cv_ratio + projected losses
11. **MCTS foundation** - przygotowanie do lookahead 3-5 tur
12. **Adaptive strategy tuning** - parametryzacja wag na podstawie wyników

### **LONG TERM – ADVANCED AI FEATURES**
13. **Machine Learning integration** - meta-statystyki skuteczności
14. **Enhanced General↔Commander feedback** - adaptacja alokacji wg efektywności
15. **Specialization profiles** - AI Commander variants (agresywny/defensywny/mobilny)
16. **Advanced economic modeling** - przewidywanie potrzeb PE based on map analysis

## 🗒 CHANGELOG
**4.1 (13.09.2025) - SMART LOG CLEANING SYSTEM + AI GENERAL INTELLIGENCE**
* **🧹 SMART LOG CLEANING SYSTEM** - inteligentne czyszczenie z ochroną danych ML
* `utils/smart_log_cleaner.py` - 3 tryby czyszczenia (session/full/archive) z ML protection
* **ML Data Protection:** Automatic protection of `logs/analysis/ml_ready/` (ai_decyzje, ekonomia_ai)
* **Hierarchical Structure:** 112+ plików w organized categories (ai/, human/, game/, analysis/)
* **Main Launcher Integration:** 4 nowe przyciski czyszczenia w `main_ai.py` z user dialogs
* **Legacy Scripts Safety:** `czyszczenie/game_cleaner.py` i `czyszczenie_csv.py` z ML warnings
* **Real-time ML Status:** Monitoring 3 CSV files, 6.3 KB danych ML w czasie rzeczywistym
* **End-to-end Safety:** Wszystkie systemy czyszczenia chronią cenne dane treningowe ✅

**4.0 (13.09.2025) - AI GENERAL INTELLIGENCE UPGRADE**
* **🧠 AI GENERAL INTELLIGENCE SYSTEM** - 29 nowych parametrów strategicznych
* **5 modułów inteligencji:** Purchase Strategy, Battlefield Analysis, Allocation Intelligence, Strategic Decisions, Strategic Limits
* **GUI Integration:** Nowa zakładka "🏛️ AI General" z polskimi opisami parametrów
* **4 funkcje strategiczne** wzbogacone: _select_template(), allocate_points(), _determine_strategy(), consider_unit_purchase()
* **Battlefield Intelligence:** Force ratio sensitivity, opportunity/retreat thresholds, enemy threat analysis
* **Strategic Polish UX:** Pełne polskie opisy z praktycznymi przykładami użycia ✅

**3.9 (13.09.2025) - AI CONFIGURATION SYSTEM COMPLETE**
* **🎛️ AI CONFIGURATION SYSTEM** - kompletny system centralnej konfiguracji AI
* `ai/ai_config.py` z `AIConfigManager` - profile AI, parametry, hot-reload
* **Profile System:** AGGRESSIVE/DEFENSIVE/BALANCED/CUSTOM z multiplierami
* **GUI Integration:** Panel konfiguracji + JSON persistence (`ai/configs/ai_config.json`)
* **29 get_param() calls:** walka_ai.py (6), ai_general.py (19), ekonomia_ai.py (4)
* **Refactoring complete:** Eliminacja hardcoded wartości (MIN_BUY, ALLOC_RATIO, MINIMUM_ATTACK_RATIO)
* **Custom parameters working:** THREAT_RETREAT_THRESHOLD=99 z GUI wpływa na AI behavior
* **A/B Testing ready:** Profile można zmieniać bez restarta - natychmiastowy efekt
* **Categories implemented:** ECONOMY, COMBAT, LOGISTICS, STRATEGY, MOVEMENT, DEPLOYMENT, PURCHASES
* **End-to-end workflow:** GUI → JSON → AI behavior confirmed working ✅

**3.8 (03.09.2025) - PE VALIDATION SYSTEM COMPLETE**
* **🔒 SYSTEM PE VALIDATION** - kompletna implementacja zabezpieczeń ekonomicznych
* Multi-layer protection w `ai/zaopatrzenie_ai.py` i `core/ekonomia.py`
* `validate_pe_spending()`, `transfer_pe_to_commanders()`, `check_pe_balance()`
* Eliminacja ujemnych PE - hard stop dla nieprawidłowych operacji
* Comprehensive PE flow logging - pełne śledzenie ekonomii w CSV
* `auto_game_10_turns.py` z PE tracking - launcher testów AI vs AI
* `tools/launcher_analizy_pe.py` - zintegrowany system testów z czyszczeniem
* `tools/analizator_przeplywu_pe.py` - analiza ekonomii per rundę
* **Weryfikacja sukcesu:** Ujemne PE wyeliminowane, bilanse zgadzają się 100%
* **Stabilność ekonomiczna:** AI bezpieczne, brak crashy, poprawne transfery PE

**3.7 (02.09.2025) - AI IMPROVEMENTS FAZA 2**
* Ulepszenia AI target selection - success rate 0% → 37.5%
* Poprawione ładowanie key_points, zwiększone limity wyszukiwania
* Rozszerzona diagnostyka pathfindingu - 5 nowych kolumn CSV
* Refaktoryzacja AI Commander - struktura modularna, bezpieczne wywołania

**3.6 (02.09.2025) - ROZSZERZENIE LOGÓW AI (ATTRITION PHASE 1)**
* Dodane kolumny turn summary: `casualties_turn`, `new_units_turn`
* Dodana kolumna action log: `skip_reason` (placeholder – brak wypełniania)
* Przygotowanie pod Emergency Mode i analizę tempa odbudowy
* Brak zmian heurystyk (czysto obserwacyjne wdrożenie)

**3.5 (31.08.2025) - SYSTEM BALANSOWANIA ARTYLERII**
* **🎯 SYSTEM OGRANICZENIA STRZAŁÓW ARTYLERII** - pełna implementacja
* Token.shots_fired_this_turn, reaction_shot_used - ograniczenia AL/AC/AP do 1+1 ataku/turę
* CombatAction._validate_combat() - automatyczna walidacja przed atakiem
* core/tura.py i engine/engine.py - auto-reset na początku tury
* tests/test_artillery_shot_limits.py - komprehensywny test suite (wszystkie testy przeszły)
* docs/ARTILLERY_SHOT_LIMITS.md - kompletna dokumentacja systemu
* docs/TOKEN_BALANCING_GUIDE.md - przewodnik balansowania jednostek
* Czyszczenie projektu: usunięcie starych tokenów z assets/tokens/
* Eliminacja dominacji "arty spam" przy zachowaniu użyteczności artylerii

**3.4 (30.08.2025) - NOWA WERSJA**
* **🎯 SYSTEM GRADUOWANEJ WIDOCZNOŚCI POZIOM 1** - pełna implementacja
* VisionService.calculate_detection_level() - krzywa nieliniowa detekcji
* detection_filter.py - filtrowanie informacji o wrogach (FULL/PARTIAL/MINIMAL)
* gui/detection_display.py - przygotowanie danych do GUI
* AI Commander integracja z detection_level dla realistycznych decyzji
* Kompleksowe testy i demonstracje funkcjonalności
* Aktualizacja engine/action_refactored_clean.py i engine/engine.py

**3.3 (29.08.2025)**
* Pakiet 6 usprawnień AI Commander (movement/capture/garrison/logi)
* Rozszerzone logi ekonomii (allocate/purchase budgets, low_fuel_ratio, orders_issued)
* Tryb SLEEP strategicznych rozkazów (generowanie = False)
* Launcher: czyszczenie logów, skrót, większe okno
* Diagnoza attrition → plan Emergency Mode & purge
* Wykryty brak czyszczenia `assets/tokens/aktualne/`

**3.2 (24.08.2025)** – analiza stanu, logi rozszerzone, identyfikacja braków

**3.0 (15.08.2025)** – kontrakt AI, szkic faz

## ⚡ SZYBKI START (AKTUALIZOWANY 13.09.2025 - WERSJA 4.1)
1. Uruchom launcher → Start Gry (potwierdź auto‑czyszczenie lub wybierz Smart Clean)
2. **NOWE - Smart Cleaning:** Test nowych przycisków czyszczenia (🧹 Sesja, 🗑️ Pełne, 📚 Archiwum) ✅
3. **NOWE - ML Protection:** Sprawdź status danych ML przyciskiem 📊 Status ML ✅
4. **AI General Intelligence:** Test nowej zakładki "🏛️ AI General" z 29 parametrami ✅
5. **AI Configuration:** Otwórz Panel Konfiguracji AI w GUI - spróbuj profili ✅
6. **Custom parameters:** Ustaw THREAT_RETREAT_THRESHOLD=99 i obserwuj wpływ ✅
7. Włącz AI dla obu stron (generał + dowódcy), zagraj 5-10 tur.
8. **NOWE - Safe Cleaning:** Po grze użyj Smart Session Clean zachowując dane ML ✅
9. **Weryfikacja get_param():** Obserwuj logi - 29 wywołań get_param() w akcji ✅
10. **Test PE validation:** Uruchom `tools/launcher_analizy_pe.py`
11. **Smart Log Status:** Sprawdź `python utils/smart_log_cleaner.py --mode ml_status` ✅
12. **Analiza ekonomii:** Sprawdź `tools/analizator_przeplywu_pe.py`
13. **Weryfikacja stabilności:** PE bilanse muszą się zgadzać 100%
14. **Test systemu artylerii:** `python tests/test_artillery_shot_limits.py`
15. **ML Data Safety:** Zweryfikuj że wszystkie tryby czyszczenia chronią dane ML ✅

## 🧪 METRYKI – STAN 3.9 (AI CONFIGURATION SYSTEM COMPLETE)
| Metryka | Status | Cel | Wykorzystanie |
|---------|--------|-----|---------------|
| **ai_configuration_system** | **ZAIMPLEMENTOWANA** | **parameter management** | **eliminacja hardcoded values** |
| **profile_ai_multipliers** | **ZAIMPLEMENTOWANA** | **AI behavior variants** | **AGGRESSIVE/DEFENSIVE/BALANCED** |
| **get_param_refactoring** | **ZAIMPLEMENTOWANA (29 calls)** | **centralized config** | **walka/ekonomia/ai_general** |
| **gui_integration** | **ZAIMPLEMENTOWANA** | **user customization** | **panel konfiguracji + JSON** |
| **pe_flow_validation** | **ZAIMPLEMENTOWANA** | **economic stability** | **eliminacja ujemnych PE** |
| **pe_transfer_safety** | **ZAIMPLEMENTOWANA** | **safe General→Commander** | **poprawne alokacje** |
| **pe_balance_checking** | **ZAIMPLEMENTOWANA** | **bilans accuracy** | **weryfikacja operacji** |
| casualties_turn | ZAIMPLEMENTOWANA | tracking attrition | wyzwalacz Emergency Mode |
| new_units_turn | ZAIMPLEMENTOWANA | tempo odtwarzania | ocena regeneracji sił |
| skip_reason | SCHEMAT (podstawowe) | diagn. stagnacji | tuning heurystyk ruchu |
| effective_move_rate | PLAN | aktywność taktyczna | wykrycie stagnacji |
| attack_success_rate | PLAN | skuteczność walk | ocena wpływu limitów artylerii |
| artillery_shots_used | CZĘŚCIOWO (surowe dane) | monitor artylerii | walidacja limitu 1+1 |
| **econ_efficiency** | **PLAN (ready for impl.)** | **wydatkowanie budżetu** | **ocena alokacji PE** |

## 🧼 PLAN ROZSZERZENIA CZYSZCZENIA
Aktualnie: quick_clean() usuwa tylko `nowe_dla_*`; full_clean() dodatkowo logi. NIE usuwa `assets/tokens/aktualne/` ani `saves/after_deployment.json`.
Plan: dodać `clean_deployed_tokens()` + wywołać w full_clean (opcjonalna flaga zachowania).

## 🔍 DIAGNOSTYKA PO SESJI
| Pytanie | Gdzie patrzeć | Oczekiwane |
|---------|---------------|------------|
| **Czy PE validation działa?** | **tools/analizator_przeplywu_pe.py output** | **Brak ujemnych PE, bilanse się zgadzają** |
| **Czy transfery PE są bezpieczne?** | **AI economic logs pe_allocated kolumna** | **Poprawne Generał→Dowódcy without overflow** |
| **Czy system artylerii działa?** | **actions CSV artillery_shots kolumna** | **≤ 2 ataki/turę per jednostka artylerii** |
| Czy attrition stabilne? | ai_actions own_units / casualties_turn | Brak gwałtownych spadków <50%/3 tury |
| Czy budżet nie stoi? | econ_after vs econ_before | Spadek >50% przy COMBO |
| **Czy ekonomia nie crashuje?** | **Exception logs + PE negative values** | **Zero crashes, zero negative PE** |
| Czy ruch aktywny? | turn_summary moved_units | ≥70% wczesnych tur |
| skip_reason (po wdrożeniu) pełny? | actions CSV | <10% pustych |
| Czy AI adaptuje się do limitów artylerii? | attack_success_rate (PLANNED) | Stabilny / rosnący bez spamu |

---

## 📚 META
Dokument przygotowuje grunt pod implementację gracza komputerowego bez refaktoryzacji istniejących modułów. Zmiany w silniku ograniczyć do dodania (jeśli brak) jednolitego API zakupów. **System ograniczenia artylerii + metryki attrition tworzą podstawę do wdrożenia Emergency Mode.**

Wersja: 4.2 (16 września 2025)
Status: **Polski System Logowania UKOŃCZONY (4.2)** – logs/sesja_aktualna/ + rotacja 5 sesji + separacja ML
Autor aktualizacji: automatyczny asystent + implementacja polskiego systemu logowania

**Najważniejsze osiągnięcia wersji 4.2:**
- ✅ **Polskie nazwy katalogów:** `logs/sesja_aktualna/` zamiast `current_session/`
- ✅ **SessionManager Singleton:** Zapobieganie duplikatom timestampów
- ✅ **Rotacja 5 sesji:** Automatyczne archiwizowanie do `logs/archiwum_sesji/`
- ✅ **Separacja danych ML:** Nowy katalog `logs/dane_ml/` chroniony przed czyszczeniem
- ✅ **System czyszczenia:** Aktualizowany z obsługą polskich nazw + dokumentacja
- ✅ **Kompatybilność:** Zachowane działanie z obiema nazwami (stara/nowa)

**Poprzednie osiągnięcia (4.0-4.1):**
- ✅ AI General Intelligence System z 29 parametrami strategicznymi
- ✅ Smart Log Cleaning z ochroną danych ML
- ✅ Reorganizacja launcherów w katalog `launchers/`
- ✅ System artylerii zbalansowany + metryki attrition

---

*Koniec dokumentu.*
