# System Widzenia dla Human Player - Implementacja

## 🎯 Cel
Zaimplementować ten sam system graduowanej widoczności dla human player, jaki już działał dla AI.

## ✅ Zrealizowane Komponenty

### 1. **Rozszerzenie klasy Player**
- **Plik**: `engine/player.py`
- **Dodano**: `self.temp_visible_token_data = {}` + istniejące `temp_visible_tokens`
- **Cel**: Bufor metadanych `detection_level`, `distance`, `detected_by` dla świeżo wykrytych jednostek. Dane są później scalane do `player.visible_token_data` podczas `engine.update_player_visibility()`.

### 2. **Upgrade TokenInfoPanel**
- **Plik**: `gui/token_info_panel.py`
- **Nowe funkcje**:
  - `set_player(player)` - ustawienie gracza dla sprawdzania detection_level
  - `_show_filtered_token()` - wyświetlanie przefiltrowanych informacji o wrogu
  - `_show_full_token()` - wyświetlanie pełnych informacji o własnych tokenach
- **Logika**: Automatyczne wykrywanie tokenów wroga i aplikowanie detection_filter

### 3. **Upgrade PanelMapa**
- **Plik**: `gui/panel_mapa.py`
- **Nowe funkcje**:
  - `_get_token_image_path()` - wybór ikony na podstawie detection_level
  - Przezroczystość tokenów wroga: `opacity = 0.4 + (detection_level * 0.6)`
  - Automatyczne przekazywanie player do TokenInfoPanel
- **Ikony**:
  - `assets/tokens/generic/unknown_contact.png` - dla detection_level < 0.5
  - `assets/tokens/generic/tank_contact.png` - dla czołgów (0.5-0.8)
  - `assets/tokens/generic/infantry_contact.png` - dla piechoty (0.5-0.8)
  - `assets/tokens/generic/artillery_contact.png` - dla artylerii (0.5-0.8)

## 🔍 Jak to działa

### Detection Levels w GUI:
```
PEŁNA INFORMACJA (≥0.8):
- ID: Pełny identyfikator (GE_TANK_01)
- CV: Dokładna wartość (15)
- Nacja: Pełna informacja (Niemcy)
- Ikona: Standardowa ikona jednostki
- Przezroczystość: 100%

CZĘŚCIOWA INFORMACJA (0.5-0.8):
- ID: Skrócony kontakt (CONTACT__01)
- CV: Przybliżony (~8+)
- Nacja: Widoczna (Niemcy)
- Ikona: Generyczna ikona kategorii
- Przezroczystość: 70-88%

MINIMALNA INFORMACJA (<0.5):
- ID: Nieznany kontakt (UNKNOWN_CONTACT)
- CV: Ukryte (???)
- Nacja: Ukryte (???)
- Ikona: unknown_contact.png
- Przezroczystość: 40-70%
```

### Przepływ danych:
1. **Silnik gry** → `VisionService.update_player_vision()` (np. w `MoveAction`) → aktualizuje `temp_visible_hexes`, `temp_visible_tokens` oraz `temp_visible_token_data`.
2. **GameEngine** → `update_all_players_visibility()` → scala dane tymczasowe do trwałego `player.visible_token_data` i czyści bufory na początku kolejnej tury (`clear_temp_visibility`).
3. **GUI** → `PanelMapa._get_token_image_path()` + przezroczystość → wybiera ikonę i kanał alfa na podstawie aktualnego `detection_level`.
4. **GUI** → `TokenInfoPanel.show_token()` → jeśli wróg, wywołuje `apply_detection_filter()` z odczytem przez `player.temp_visible_token_data` (lub trwałe `visible_token_data`).
5. **API pomocnicze** → `engine.detection_filter.get_detection_info_for_player()` / `is_token_detected()` → zwracają najświeższe metadane niezależnie od tego, czy zapisano je w buforze tymczasowym, czy w persystentnym magazynie.

### Utrzymanie danych
- `temp_visible_*` trzymają odkrycia z bieżącej akcji i są czyszczone przez `engine.clear_temp_visibility()` na starcie nowej tury.
- `visible_token_data` gromadzi „ostatnio potwierdzony” poziom detekcji i pozwala porównać postęp widoczności między turami.
- Pomocnicze funkcje `get_detection_info_for_player(player, token_id, include_temp=True)` oraz `is_token_detected(...)` korzystają z obu struktur, dzięki czemu logika AI, tooltipy i inne moduły dostają spójne dane.

## 🧪 Testy
- **Plik**: `tests/test_human_detection_system.py`
- **Status**: ✅ WSZYSTKIE TESTY PRZESZŁY
- **Sprawdza**: 
  - Poprawność `temp_visible_token_data` i scalania do `visible_token_data`
  - Działanie `detection_filter`
  - Integrację z GUI

## 📊 Parytety z AI
| Aspekt | AI Commander | Human Player |
|--------|-------------|--------------|
| Detection calculation | ✅ VisionService | ✅ VisionService |
| Data storage | ✅ temp_visible_token_data | ✅ temp_visible_token_data |
| Information filtering | ✅ detection_filter | ✅ detection_filter |
| Visual representation | ❌ Nie dotyczy | ✅ Ikony + przezroczystość |
| Info panel | ❌ Nie dotyczy | ✅ Graduowane informacje |

## 🎮 Efekt dla gracza
- **Fog of War**: Tokeny wroga są widoczne tylko w zasięgu sight
- **Graduated visibility**: Im dalej, tym mniej szczegółów
- **Visual cues**: Przezroczystość i alternatywne ikony pokazują poziom pewności
- **Tactical advantage**: Observer units zwiększają zasięg pełnej identyfikacji

## 🔧 Konfiguracja
System używa tych samych progów co AI:
- **FULL/PARTIAL próg**: 0.8 detection_level
- **PARTIAL/MINIMAL próg**: 0.5 detection_level
- **Sight range**: Standardowy parametr jednostek (+2 dla Observer)

Human player ma teraz **identyczny** system widzenia jak AI!
