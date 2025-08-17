# TESTY - STRUKTURA UPORZĄDKOWANA

## 📁 ORGANIZACJA TESTÓW

### `/tests/core/` - Testy logiki biznesowej
- `test_key_points_*.py` - System key points i ekonomii
- `test_*punktow*.py` - Przydzielanie i zarządzanie punktami
- `test_victory_system_fixed.py` - System zwycięstwa

### `/tests/engine/` - Testy silnika gry
- `test_action_refactored.py` - System akcji (główny)
- `test_fog_of_war.py` - Widoczność i mgła wojny
- `test_*ruchu*.py` - Testy ruchu i modyfikatorów terenu
- `test_*walka*.py` - System walki
- `test_*token*.py` - Zarządzanie żetonami

### `/tests/gui/` - Testy interfejsu
- `test_panel_*.py` - Testy paneli GUI
- `test_overlay_*.py` - Testy nakładek

### `/tests/integration/` - Testy integracyjne
- `test_*symulacja*.py` - Pełne symulacje rozgrywki
- `test_integralnosc_*.py` - Testy całościowej integralności
- `test_system_ready.py` - Test gotowości systemu

### `/tests/testy_dla_podrecznika/` - Testy dokumentacyjne
- Testy używane do generowania przykładów w podręczniku

## 🧹 USUNIĘTE PLIKI
- `debug_*.py` - Pliki debugowania (nie testy)
- `test_simple*.py` - Proste testy zastąpione przez system_ready
- `test_compare_*.py` - Testy porównawcze (nieaktualne)
- `test_dialog*.py` - Testy dialogów (przestarzałe)

## 🚀 URUCHAMIANIE TESTÓW

### Wszystkie testy:
```bash
python -m pytest tests/
```

### Konkretny moduł:
```bash
python -m pytest tests/engine/
python -m pytest tests/core/
python -m pytest tests/gui/
python -m pytest tests/integration/
```

### Szybkie sprawdzenie systemu:
```bash
python tests/integration/test_system_ready.py
```

## 📋 PRIORYTET TESTÓW

1. **KRYTYCZNE** - `test_system_ready.py`
2. **WYSOKIE** - `tests/engine/test_action_refactored.py`
3. **WYSOKIE** - `tests/core/test_key_points_system.py`
4. **ŚREDNIE** - testy GUI
5. **NISKIE** - testy dokumentacyjne

## 🔄 AKTUALIZACJA
Data: 17.08.2025
Status: Uporządkowane i sklasyfikowane
Autor: Automatyczne porządkowanie
