# 🛠️ Scripts & Launchers

Ten folder zawiera wszystkie skrypty pomocnicze i launchery do gry.

## 🎮 AI Launchers

### `ai_observer_launcher.py` ➡️ **PRZENIESIONY NA GŁÓWNY POZIOM**
**Kontrolowana obserwacja gry z AI z pauzami**
- 🎯 Wszystkie jednostki AI (generałowie + dowódcy) 
- ⏱️ Konfigurowalne pauzy (5-120s) po każdej turze AI
- 🗺️ Wizualizacja stanu mapy
- 📊 Statystyki żetonów w czasie rzeczywistym
- 🔍 Monitoring folderów transferowych
- 🎮 Możliwość przejścia dalej klawiszem

**Nowe użycie:** `python ai_observer_launcher.py` (z głównego poziomu)

### `quick_ai_launcher.py`
**Szybkie uruchomienie z pełnym AI**
- Automatycznie wszystkie AI włączone
- 5 tur dla szybkich testów
- Bez GUI - bezpośredni start

**Użycie:** `python scripts/quick_ai_launcher.py`

### `debug_gra_z_logami.py`
**Gra z pełnym logowaniem AI** 
- Monkey patches dla logowania
- Szczegółowe logi CSV
- Podstawowy launcher bez kontroli tempa

**Użycie:** `python scripts/debug_gra_z_logami.py`

## 📊 Demonstracje

### `DEMO_AI_PURCHASE_SYSTEM.py`
**Demonstracja systemu zakupów AI**
- Pokazuje statystyki działania AI General → AI Commander
- Wyniki z testów i logów
- Instrukcje użycia systemu

**Użycie:** `python scripts/DEMO_AI_PURCHASE_SYSTEM.py`

## 🧹 Maintenance

### `cleanup_project.py`
### `master_cleanup.py` 
Skrypty do czyszczenia projektu

### `reorganize_project.py`
Reorganizacja struktury projektu

### `prepare_refactor.py`
Przygotowanie do refaktoringu

### `inspect_ai_plan.py`
Inspekcja planów AI

### `export_to_github.bat`
Export do GitHuba

## 🎯 Zalecane użycie

1. **Do obserwacji AI:** `ai_observer_launcher.py` 
2. **Do szybkich testów:** `quick_ai_launcher.py`
3. **Do debugowania:** `debug_gra_z_logami.py`
4. **Do prezentacji:** `DEMO_AI_PURCHASE_SYSTEM.py`

---
*Wszystkie skrypty zostały przeniesione z głównego folderu dla lepszej organizacji.*
