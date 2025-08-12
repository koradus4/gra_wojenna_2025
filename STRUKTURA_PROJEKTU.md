# STRUKTURA PROJEKTU KAMPANIA 1939

## � AKTUALNA ANALIZA PROJEKTU (LIPIEC 2025)

```
kampania1939_restored/
├── main.py                     # 🎮 GŁÓWNY LAUNCHER GRY (z AI General)
├── main_ai_vs_human.py         # 🤖 AI vs CZŁOWIEK - zaawansowane AI z uczeniem (1184 linie)
├── main_alternative.py         # 🚀 SZYBKI LAUNCHER (bez GUI startowego)
├── README.md                   # Podstawowe informacje o projekcie
├── requirements.txt            # Zależności Python
├── PLAN_ROZWOJU_FUNKCJONALNOSCI.md # 📋 Plan rozwoju (5 kierunków)
├── PLAN_WEB_OBSERVER.md        # Plan obserwatora web
├── STRUKTURA_PROJEKTU.md       # 📖 Ten plik - dokumentacja projektu
├── .gitignore                  # Pliki ignorowane przez Git
├── .venv/                      # Środowisko wirtualne Python
├── __pycache__/                # Cache Python
├── ekran_startowy.log          # Logi ekranu startowego
│
├── ai/                         # 🤖 MODUŁ SZTUCZNEJ INTELIGENCJI
│   ├── __init__.py             # Inicjalizacja modułu AI
│   ├── ai_general.py           # 🧠 AI Generał - zaawansowany system zakupów
│   ├── learning_data/          # 📊 Dane uczenia się AI (pliki JSON)
│   └── README.md               # Dokumentacja modułu AI
│
├── accessibility/              # ♿ DOSTĘPNOŚĆ (przygotowane do rozwoju)
│   ├── interfejs_wizualny.py   # Ulepszenia wizualne (puste)
│   ├── komendy_glosowe.py      # Sterowanie głosowe (przygotowane)
│   └── narracja_glosowa.py     # Narracja dla niewidomych (przygotowane)
│
├── archive/                    # 📦 ARCHIWUM STARYCH PLIKÓW
│   ├── backup_files            # Kopie zapasowe
│   └── test_*.py              # Stare testy (zarchiwizowane)
│
├── backup/                     # 🔄 SYSTEM AUTOMATYCZNYCH KOPII
│   ├── auto_backup.py          # 🐍 Python - uniwersalny backup
│   ├── auto_backup.bat         # 🖥️ Windows Batch - szybki backup  
│   ├── auto_backup.ps1         # 💻 PowerShell - nowoczesny backup
│   ├── BACKUP_SCRIPTS.md       # 📋 Dokumentacja skryptów backup
│   └── README.md               # 🚀 Przewodnik quick start
│
├── core/                       # ⚙️ PODSTAWOWE SYSTEMY GRY
│   ├── dyplomacja.py           # 🤝 Relacje między frakcjami
│   ├── ekonomia.py             # 💰 System punktów ekonomicznych
│   ├── pogoda.py               # 🌤️ Warunki atmosferyczne, modyfikatory
│   ├── rozkazy.py              # 📜 System rozkazów i akcji
│   ├── siec.py                 # 🌐 Komunikacja sieciowa (przygotowane)
│   ├── strategic_orders.py     # 🎯 Strategiczne rozkazy
│   ├── tura.py                 # 🔄 Zarządzanie turami i podturami
│   └── zwyciestwo.py           # 🏆 Warunki końca gry i punkty zwycięstwa
│
├── data/                       # 📊 DANE KONFIGURACYJNE GRY
│   └── map_data.json           # 🗺️ Definicja mapy heksagonalnej
│
├── docs/                       # 📚 DOKUMENTACJA PROJEKTU
│   ├── INSTRUKCJA_OBSLUGI.md   # 📖 Jak grać - instrukcja użytkownika
│   ├── OPIS_PROJEKTU.md        # 📋 Kompletny opis architektury
│   ├── PLAN_ROZWOJU.md         # 🚀 Plan rozwoju funkcjonalności
│   ├── README_GAMEPLAY.md      # 🎮 Zasady rozgrywki
│   ├── STRUKTURA_PROJEKTU.md   # 📁 Struktura projektu (kopia)
│   └── plans/                  # 📋 Szczegółowe plany rozwoju
│
├── edytory/                    # 🛠️ EDYTORY I NARZĘDZIA DEWELOPERSKIE
│   ├── clear_game_tokens.py    # 🧹 Czyszczenie żetonów z gry
│   ├── map_editor_prototyp.py  # 🗺️ EDYTOR MAP - prototyp (1088 linii)
│   ├── prototyp_kreator_armii.py # 🏭 Kreator armii (przygotowany)
│   ├── token_editor_prototyp.py # 🎨 EDYTOR ŻETONÓW - zaawansowany (1427 linii)
│   └── __pycache__/            # Cache Python
│
├── engine/                     # 🔧 SILNIK GRY (CORE SYSTEM)
│   ├── __init__.py             # Eksport głównych klas
│   ├── action.py               # 🎯 System rozkazów (ruch, walka, reakcje)
│   ├── action_refactored_clean.py # 🔄 Refaktoryzowany system akcji
│   ├── board.py                # 🗺️ Mapa heksagonalna, pathfinding, overlay
│   ├── engine.py               # 🧠 Główny silnik gry - integracja wszystkich komponentów
│   ├── hex_utils.py            # 📐 Funkcje geometryczne dla heksów
│   ├── player.py               # 👤 Gracze, widoczność, punkty zwycięstwa
│   ├── save_manager.py         # 💾 Zapis/wczytanie stanu gry (JSON)
│   ├── token.py                # 🪖 Jednostki wojskowe, statystyki, mechaniki
│   └── __pycache__/            # Cache Python
│
├── gui/                        # 🖼️ INTERFEJS UŻYTKOWNIKA
│   ├── __init__.py             # Inicjalizacja modułu GUI
│   ├── deploy_new_tokens.py    # 🚀 Rozmieszczanie nowych jednostek
│   ├── ekran_startowy.py       # 🎯 Wybór graczy, konfiguracja gry
│   ├── opcje_dostepnosci.py    # ♿ Ustawienia dostępności
│   ├── panel_dowodcy.py        # 👨‍💼 Panel dowódcy (lokalna mapa, taktyka)
│   ├── panel_ekonomiczny.py    # 💰 Zarządzanie budżetem
│   ├── panel_generala.py       # 🎖️ Panel generała (pełna mapa, strategia)
│   ├── panel_gracza.py         # 👤 Wspólne elementy UI (VP, czas, save/load)
│   ├── panel_mapa.py           # 🗺️ Główny komponent mapy z interakcją
│   ├── panel_pogodowy.py       # 🌤️ Panel warunków pogodowych
│   ├── token_info_panel.py     # ℹ️ Szczegółowe informacje o jednostce
│   ├── token_shop.py           # 🏪 Sklep z jednostkami
│   ├── token_shop_standalone.py # 🏪 Standalone wersja sklepu
│   ├── uzupelnij_zeton.py      # 🔧 Uzupełnianie zapasów jednostek
│   ├── zarzadzanie_punktami_ekonomicznymi.py # 💰 Zarządzanie budżetem
│   ├── images/                 # 🖼️ Grafiki interfejsu i portrety graczy (6 portretów generałów)
│   └── __pycache__/            # Cache Python
│
├── saves/                      # 💾 ZAPISY GRY
│   └── latest.json             # Ostatni automatyczny zapis
│
├── scripts/                    # 🔧 SKRYPTY UTRZYMANIOWE
│   ├── cleanup_project.py      # 🧹 Czyszczenie projektu
│   ├── export_to_github.bat    # 📤 Export do GitHub
│   ├── master_cleanup.py       # 🗂️ Główne czyszczenie
│   ├── prepare_refactor.py     # 🔄 Przygotowanie refactoringu
│   └── reorganize_project.py   # 📁 Reorganizacja struktury
│
├── tests/                      # ✅ TESTY JEDNOSTKOWE I INTEGRACYJNE (42 testy)
│   ├── __init__.py             # Inicjalizacja modułu testów
│   ├── test_ai_general.py      # 🤖 Test AI General - system zakupów
│   ├── test_ai_learning.py     # 🧠 Test systemu uczenia się AI
│   ├── test_sklep_jednostek.py # 🏪 Test kompletności sklepu jednostek (183 linie)
│   ├── test_prostej_analizy_sklepu.py # 📊 Test analizy dostępności jednostek
│   ├── test_dokladny_porownanie.py # 🔍 Test dokładnego porównania sklep vs edytor
│   ├── test_full_integration.py # 🔗 Test pełnej integracji gry
│   ├── test_integralnosc_calej_gry.py # 🎮 Test całościowej integralności
│   ├── test_action_refactored.py # ⚡ Test zrefaktorowanego systemu akcji
│   ├── test_combat_system_example.py # ⚔️ Test systemu walki
│   ├── test_modyfikatory_ruchu_terenu.py # 🏃 Test modyfikatorów ruchu
│   ├── test_blokada_ruchu.py   # 🚫 Test blokad ruchu
│   ├── test_launcher_fix.py    # 🚀 Test naprawy launchera
│   ├── test_dialog.py          # 🗣️ Test dialogów GUI
│   ├── test_simple_dialog.py   # 💬 Test prostych dialogów
│   ├── README_TESTS.md         # 📋 Dokumentacja testów
│   ├── PYIMAGE_FIX_INSTRUKCJA.md # 🔧 Instrukcja naprawy błędów PyImage
│   └── ... (więcej plików testowych)
│
├── tools/                      # 🛠️ NARZĘDZIA DIAGNOSTYCZNE
│   ├── check_tokens_vs_json.py # 🔍 Sprawdzanie zgodności żetonów z JSON
│   ├── convert_attack_fields.py # 🔄 Konwersja pól ataku
│   ├── demo_pyimage_fix.py     # 🎯 Demo naprawy PyImage
│   └── diagnostyka_key_points.py # 🔬 Diagnostyka punktów kluczowych
│
├── utils/                      # � NARZĘDZIA POMOCNICZE
│   ├── loader.py               # 📥 Ładowanie danych (pusty)
│   └── __pycache__/            # Cache Python
│
└── assets/                     # 🎨 ZASOBY GRAFICZNE I DANE
    ├── mapa_globalna.jpg       # 🗺️ Tło mapy strategicznej
    └── tokens/                 # 🪖 Definicje i grafiki jednostek (puste - przygotowane)
```

## 🎮 TRYBY URUCHAMIANIA

### 1. 🎯 Główny launcher (main.py)
- **Ekran startowy**: Wybór 6 graczy (3 Polska + 3 Niemcy)
- **Konfiguracja**: Czas na turę, role (Generał/Dowódca)
- **AI General**: Opcjonalne włączenie AI dla generałów
- **Funkcje**: Pełny interfejs, wszystkie mechaniki gry

### 2. 🤖 AI vs Człowiek (main_ai_vs_human.py) - NOWE!
- **Tryb AI vs Human**: Gracz vs inteligentne AI z uczeniem się
- **Wybór nacji**: GUI do wyboru nacji gracza i AI
- **Poziomy trudności**: Łatwy, średni, trudny AI
- **Konfigurowalne tury**: 10, 15, 20, 30 tur (wybór użytkownika)
- **Uczenie się**: AI adaptuje strategię na podstawie historii gier
- **Szczegółowe logi**: Wyświetla wszystkie decyzje AI (zakupy, ataki, ruchy)

### 3. 🚀 Szybki start (main_alternative.py)  
- **Automatyczne ustawienia**: Bez ekranu startowego
- **Domyślni gracze**: 6 graczy, 5 min na turę każdy
- **Kolejność**: Zależy od porządku alfabetycznego
- **Użycie**: Szybkie testowanie, development

### 4. 🛠️ Edytory i narzędzia
- **Edytor map**: `edytory/map_editor_prototyp.py` (1088 linii)
- **Edytor żetonów**: `edytory/token_editor_prototyp.py` (1427 linii)
- **Diagnostyka**: `tools/diagnostyka_key_points.py`

## 🏗️ ARCHITEKTURA SYSTEMU

### 1. 🧠 Silnik Gry (engine/)
**Serce aplikacji** - obsługuje całą logikę gry:
- **`engine.py`** - Główny silnik, integruje wszystkie komponenty
- **`board.py`** - Mapa heksagonalna, pathfinding, geometria
- **`token.py`** - Jednostki wojskowe, statystyki, mechaniki
- **`player.py`** - Gracze, widoczność, punkty zwycięstwa, ekonomia
- **`action.py`** - System rozkazów (ruch, walka, reakcje)
- **`save_manager.py`** - Kompletny zapis/wczytanie stanu gry
- **`hex_utils.py`** - Matematyka i geometria heksagonalna

### 2. 🖼️ Interfejs Użytkownika (gui/)
**Kompletny system GUI** dla różnych ról graczy:
- **`ekran_startowy.py`** - Konfiguracja gry, wybór graczy
- **`panel_generala.py`** - Interfejs strategiczny (pełna mapa, ekonomia)
- **`panel_dowodcy.py`** - Interfejs taktyczny (lokalna mapa)
- **`panel_mapa.py`** - Główny komponent mapy z interakcją
- **`panel_gracza.py`** - Wspólne elementy (VP, czas, save/load)
- **`token_shop.py`** - System zakupów jednostek
- **`zarzadzanie_punktami_ekonomicznymi.py`** - Zarządzanie budżetem

### 3. ⚙️ Systemy Podstawowe (core/)
**Mechaniki biznesowe** gry:
- **`tura.py`** - Zarządzanie turami i podturami
- **`ekonomia.py`** - System punktów ekonomicznych
- **`pogoda.py`** - Warunki atmosferyczne, modyfikatory
- **`zwyciestwo.py`** - Warunki końca gry, punkty zwycięstwa
- **`dyplomacja.py`** - Relacje między frakcjami
- **`rozkazy.py`** - System strategicznych rozkazów

### 4. 🤖 Sztuczna Inteligencja (ai/)
**Zaawansowany system AI z uczeniem się**:
- **`ai_general.py`** - AI Generał z systemem zakupów jednostek
- **`learning_data/`** - Katalog z danymi uczenia się AI (JSON)
- **Funkcje**: Automatyczne decyzje strategiczne, zakupy, rozmieszczenie
- **Uczenie się**: AI analizuje każdą grę i dostosowuje strategię
- **Poziomy trudności**: Łatwy, średni, trudny z różnymi parametrami
- **Integracja**: Bezproblemowa współpraca z interfejsem ludzkiego gracza

### 5. 🛠️ Edytory i Narzędzia (edytory/, tools/)
**Potężne narzędzia deweloperskie**:
- **`map_editor_prototyp.py`** - Zaawansowany edytor map (1088 linii)
- **`token_editor_prototyp.py`** - Kompleksowy edytor jednostek (1427 linii)
- **`diagnostyka_key_points.py`** - Narzędzie diagnostyczne

## 📋 KLUCZOWE PLIKI I FUNKCJE

### 🚀 Uruchamianie Gry:
- **`main.py`** - Główny launcher z ekranem startowym i AI General
- **`main_ai_vs_human.py`** - AI vs Człowiek z uczeniem się (1184 linie)
- **`main_alternative.py`** - Szybki start bez konfiguracji
- **`requirements.txt`** - Zależności: tkinter, PIL, numpy

### 💾 Dane i Konfiguracja:
- **`data/map_data.json`** - Kompletna definicja mapy heksagonalnej
- **`saves/latest.json`** - Automatyczny zapis stanu gry

### 🔧 System Backup:
- **`backup/auto_backup.py`** - Uniwersalny skrypt Python
- **`backup/auto_backup.bat`** - Szybki backup dla Windows
- **`backup/auto_backup.ps1`** - Zaawansowany PowerShell

### 📊 Testy i Diagnostyka:
- **`tests/test_integralnosc_calej_gry.py`** - Test pełnej integralności
- **`tests/test_ai_general.py`** - Test systemu AI
- **`tests/test_sklep_jednostek.py`** - Test kompletności sklepu (183 linie)
- **`tests/test_ai_learning.py`** - Test systemu uczenia się AI
- **`tests/test_dokladny_porownanie.py`** - Test porównania sklep vs edytor
- **`tools/diagnostyka_key_points.py`** - Diagnostyka punktów kluczowych
- **42 testy łącznie** w katalogu tests/

## 📊 STATYSTYKI PROJEKTU

### 📈 Rozmiar Kodu:
- **Edytor żetonów**: 1427 linii (token_editor_prototyp.py)
- **Edytor map**: 1088 linii (map_editor_prototyp.py)
- **Silnik gry**: ~500+ linii (engine.py + komponenty)
- **Interfejs graficzny**: ~1000+ linii (wszystkie panele)
- **System AI**: ~300+ linii (ai_general.py)

### 🎮 Funkcjonalności:
- **6 graczy simultanicznych** (3 Polska + 3 Niemcy)
- **2 tryby uruchamiania** (z ekranem startowym i bez)
- **AI General** zintegrowane z grą
- **Kompletny system ekonomii** z punktami i zarządzaniem
- **System save/load** z pełną persistencją
- **Zaawansowane edytory** map i jednostek

### 🔧 Narzędzia:
- **3 skrypty backup** (Python, Batch, PowerShell)
- **42 testów jednostkowych** i integracyjnych
- **Narzędzia diagnostyczne** dla deweloperów
- **Dokumentacja** - instrukcje, plany rozwoju

## 🕐 OSTATNIE AKTUALIZACJE (LIPIEC 2025) - Aktualizacja z 3 lipca 2025

### ✅ Przeprowadzone:
- **🤖 AI vs Człowiek** - dodany main_ai_vs_human.py z zaawansowanym AI (1184 linie)
- **🧠 System uczenia się AI** - katalog ai/learning_data/ z danymi uczenia się
- **🏪 Kompletność sklepu** - zweryfikowano 100% dostępność jednostek w sklepie
- **✅ Rozszerzenie testów** - 42 testy jednostkowe i integracyjne
- **🔍 Testy sklepu** - test_sklep_jednostek.py, test_prostej_analizy_sklepu.py, test_dokladny_porownanie.py
- **📋 Plan rozwoju** - utworzony PLAN_ROZWOJU_FUNKCJONALNOSCI.md z 5 kierunkami
- **📖 Dokumentacja** - kompleksowa analiza i aktualizacja STRUKTURA_PROJEKTU.md
- **🔍 Analiza projektu** - pełna inwentaryzacja wszystkich komponentów
- **🛠️ Identyfikacja edytorów** - zlokalizowanie zaawansowanych narzędzi deweloperskich
- **🎯 AI Fair Play** - przepisane AI aby ściśle przestrzegało zasad gry (brak nieuczciwych przewag)
- **🏆 System Key Points** - zweryfikowane działanie systemu punktów za kluczowe lokacje
- **🎯 NOWE PRIORYTETY AI** - zaimplementowano nową hierarchię celów dla AI (4 lipca 2025):
  - **🏆 PRIORYTET #1: VP** - eliminacja wrogów dla punktów zwycięstwa (najwyższy priorytet)
  - **🏛️ PRIORYTET #2: Punkty ekonomiczne** - zdobywanie key points dla ekonomii
  - **⚔️ PRIORYTET #3: Agresja skalowana** - dostosowana do fazy gry i statusu VP
  - **🗺️ AI OMNISCIENCE KEY POINTS** - AI zawsze zna lokalizację wszystkich punktów kluczowych
  - **📊 Inteligentna adaptacja** - AI dostosowuje strategię do przewagi VP i fazy gry

### 🎯 Następne Kroki:
1. **Implementacja wybranego kierunku rozwoju** z planu 5 funkcjonalności
2. **Zuniwersalizowanie edytora map** - priorytet dla tworzenia scenariuszy
3. **Rozszerzenie funkcji Generała** - ataki lotnicze i zwiad
4. **System zaopatrzenia** - nowe mechaniki logistyczne
5. **Ulepszenia wizualizacji** - animacje i efekty

---

*Dokument aktualizowany na bieżąco z rozwojem projektu.*

## 🏆 SYSTEM KEY POINTS (PUNKTY KLUCZOWE)

**W grze działa zaawansowany system punktów za kluczowe lokacje:**

### 📍 Rodzaje Key Points:
- **🏘️ Miasta** - wartość 100 punktów każde (8 miast na mapie)
- **🏰 Fortyfikacje** - wartość 150 punktów (1 fortyfikacja na mapie)  
- **🚦 Węzły komunikacyjne** - wartość 75 punktów każdy (3 węzły na mapie)
- **Łącznie**: 12 key points na mapie

### 🎮 Mechanizm działania:
1. **Kontrola**: Jednostka na key point kontroluje go dla swojej nacji
2. **Punkty ekonomiczne**: Co turę Generał dostaje 10% wartości key point (min. 1 punkt)
3. **Wyczerpywanie**: Key point traci wartość równą przyznanym punktom
4. **Usuwanie**: Wyzerowane key points znikają z mapy
5. **Tylko ekonomiczne**: Key points dają punkty ekonomiczne (nie VP)

### 📊 Przykład:
- Miasto (100 pkt) → Generał dostaje 10 pkt ekonomicznych co turę
- Po 10 turach miasto się wyczerpuje i znika z mapy
- Fortyfikacja (150 pkt) → 15 pkt ekonomicznych co turę przez 10 tur

### 🎯 Strategiczne znaczenie:
- **Kontrola terenu** - kluczowe lokacje dają przewagę ekonomiczną
- **Planowanie długoterminowe** - punkty się wyczerpują, trzeba zdobywać nowe
- **Ekonomia wojenna** - punkty służą do zakupu nowych jednostek

---
