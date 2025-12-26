# STRUKTURA PROJEKTU KAMPANIA 1939

## 📌 Stan bieżący (1 października 2025) – wersja 3.8
- Minimalna, trzywarstwowa AI (`GeneralAI`, `CommanderAI`, `TokenAI`) korzysta z tych samych mechanik co gracze human i loguje decyzje do `ai/logs/`.
- Silnik tur łączy limity artylerii (1 strzał + 1 reakcja na turę), system pór dnia oraz wymóg jednostki **Zaopatrzenia (Z)** przy zbieraniu PE z key pointów.
- Polski system logowania (`utils/session_manager.py`, `ai/logs/`) obsługuje rotację sesji i czyszczenie danych z ochroną katalogów ML.
- Launchery Tkinter pozwalają uruchomić tryb human vs human (`main.py`) lub scenariusze mieszane AI/Human (`ai_launcher.py`).
- Repozytorium utrzymujemy w Pythonie 3.12; zależności minimalne (`Pillow`, `numpy`) znajdują się w `requirements.txt`.

## 📂 Drzewo katalogów (wysokopoziomowe)
```
projekt/
├── main.py                     # Launcher human vs human z opcją czyszczenia logów
├── ai_launcher.py              # Launcher konfiguracji AI/Human per gracz
├── auto_game_10_turns.py       # Szybki scenariusz testowy (AI vs AI)
├── launchers/                  # Alternatywne starty GUI (basic/alternative)
├── ai/                         # Minimalne AI + logi i testy
├── engine/                     # Silnik gry: GameEngine, akcje, widoczność, tokeny
├── core/                       # Logika tur, ekonomia, warunki zwycięstwa, pogoda
├── gui/                        # Panele Tkinter dla generała, dowódców i mapy
├── data/                       # Pliki map, konfiguracje startowe, requests/
├── assets/                     # Grafika mapy globalnej, tokeny startowe
├── docs/                       # Dokumentacja techniczna (AI, engine, balans)
├── tests/                      # Testy jednostkowe/integracyjne (w tym `tests/ai/`)
├── utils/                      # SessionManager, archiwizacja sesji, narzędzia pomocnicze
├── czyszczenie/                # Skrypty czyszczenia logów (CSV/sesje) i dokumentacja
├── edytory/                    # Prototypy edytorów map i żetonów
├── scripts/                    # Automatyzacja i analizy (np. logi PE)
├── tools/                      # Analizatory diagnostyczne, maintenance (smart_log_cleaner), raporty PE
├── backup/                     # Kopie zapasowe i narzędzia przywracania
├── saves/                      # Zapisy gier
├── accessibility/              # Eksperymentalne rozszerzenia dostępności
├── plans/                      # Plany balansowe i szkice kampanii
├── requirements.txt
└── STRUKTURA_PROJEKTU.md
```

## 🚀 Launchery i tryby uruchomienia
- `main.py` – domyślny launcher human vs human z panelami generała, dowódców i czyszczeniem logów.
- `ai_launcher.py` – pełna konfiguracja AI/Human dla każdego gracza, używa `GeneralAI` i `CommanderAI`.
- `launchers/main_basic.py` – uproszczony ekran startowy.
- `launchers/main_alternative.py` – szybkie uruchomienie z priorytetem czyszczenia danych.
- `auto_game_10_turns.py` – skrypt regresyjny uruchamiający 10 tur AI vs AI na uproszczonej konfiguracji.

## 🧠 Warstwa AI (minimalna)
- `ai/general/general_ai.py` – Generał zbiera PE przez `EconomySystem`, buduje profile dowódców, rezerwuje 10–20% budżetu i dystrybuuje resztę.
- `ai/commander/commander_ai.py` – Dowódca synchronizuje PE, dzieli budżet po równo na żetony, uruchamia `TokenAI` i zwraca niewykorzystane środki.
- `ai/tokens/token_ai.py` – Pojedynczy żeton decyduje o ruchu (wróg → podejście, inaczej patrol), ataku i zużyciu budżetu na paliwo/CV.
- Dokumentacja szczegółowa: `ai/README.md`, `ai/general/README.md`, `ai/commander/README.md`, `ai/tokens/README.md`.

## ⚙️ Silnik (`engine/`) i logika rdzeniowa (`core/`)
- `engine/engine.py` – steruje turą, akcjami, widocznością i ekonomią key pointów.
- `engine/action_refactored_clean.py` – implementacje `MoveAction` i `CombatAction`, walidacja ruchu oraz gradacja widoczności.
- `engine/detection_filter.py`, `VisionService` – obsługa progów FULL/PARTIAL/MINIMAL, z mnożnikami pory dnia.
- `core/tura.py` – `TurnManager` (6 tur = 1 doba, raporty pogodowe, reset zasobów).
- `core/ekonomia.py` – `EconomySystem` z walidacją PE i wsparciem dla AI/human.
- `core/zwyciestwo.py` – warunki zwycięstwa (Victory Points oraz eliminacja).
- `engine/SILNIK_GRY_ANALIZA.md` oraz `core/ANALIZA_FOLDERU_CORE.md` opisują moduły w szczegółach technicznych.

## 🗃️ Dane, assety i edytory
- `data/map_data.json` – definiuje heksy, key pointy i parametry startowe.
- `assets/` – grafiki map i żetonów (`tokens/`), wykorzystywane przez GUI.
- `edytory/` – prototypy narzędzi (`token_editor_prototyp.py`, `map_editor_prototyp.py`).
- `plans/` oraz `docs/` – materiały projektowe, balans, raporty faz.

## 🧾 Logowanie i czyszczenie
- `utils/session_manager.py` – singleton sesji logów (`ai/logs/sessions/`, rotacja archiwum).
- `tools/maintenance/smart_log_cleaner.py` – CLI z trybami czyszczenia i ochroną `ai/logs/dane_ml/`.
- `czyszczenie/` – `czyszczenie_csv.py`, `game_cleaner.py` oraz dokumentacja (`OPIS_NARZEDZI_CZYSZCZENIA.md`).
- `ai/logs/` – logger AI (tekst + CSV) oraz narzędzia czyszczenia (`ai/logs/czyszczenie_logow.py`).
- Główne launchery integrują przyciski czyszczenia i archiwizacji (`utils/session_archiver.py`).

## 🧪 Testy i automatyzacja
- `tests/ai/` – testy jednostkowe AI (`test_token_ai.py`, `test_ai_basic.py`).
- `tests/core/`, `tests/engine/`, `tests/integration/` – regresja silników, limitów artylerii, FOW.
- `tests/test_polish_logging.py` – smoke test polskiego systemu logowania.
- `tests/run_phase4_tests.py` oraz logi w `tests/results/` dokumentują uruchomienia pakietów.

## 📚 Dokumentacja uzupełniająca
- `docs/` – przewodniki balansowe, raporty faz rozwoju, dokumentacja logowania.
- `engine/SILNIK_GRY_ANALIZA.md` – szczegółowy opis mechanik silnika.
- `core/ANALIZA_FOLDERU_CORE.md` – analiza modułów `core/` i powiązań.
- `docs/README.md` oraz `docs/TOKEN_BALANCING_GUIDE.md` – zasady balansowania jednostek.

## 🔧 Kluczowe narzędzia developerskie
- `scripts/` – automatyczne analizy logów, generator raportów PE.
- `tools/` – diagnostyka (`analizator_przeplywu_pe.py`, `diagnostyka_key_points.py`).
- `backup/` – `backup_local_min.py`, `restore_from_backup.py` do snapshotów.

## ✅ Najważniejsze fakty operacyjne
- Uruchomienie gry wymaga aktywnego środowiska Tkinter (Windows) i zależności z `requirements.txt`.
- Logi gry rotują automatycznie, ale `Ctrl+Shift+L` w launcherach wymusza czyszczenie.
- Key pointy generują PE wyłącznie, gdy stoi na nich jednostka Zaopatrzenia – inne żetony blokują pole.
- Limit artylerii (1 atak + 1 reakcja) oraz gradacja widoczności obowiązują zarówno AI, jak i graczy human.
