# System Logowania Gry Wojennej - Dokumentacja Techniczna
# (War Game Logging System - Technical Documentation)

## 📋 Spis Treści (Table of Contents)

1. [Przegląd Systemu](#przeglad-systemu)
2. [Struktura Katalogów](#struktura-katalogow)
3. [Komponenty Systemu](#komponenty-systemu)
4. [Integracja z Istniejącym Kodem](#integracja)
5. [Eksport Danych ML](#eksport-ml)
6. [Instrukcja Użycia](#instrukcja)
7. [Przykłady Kodu](#przyklady)
8. [Rozwiązywanie Problemów](#troubleshooting)

## 🎯 Przegląd Systemu (System Overview)

System logowania został zaprojektowany do organizacji i analizy wszystkich aspektów rozgrywki:

- **Segregacja danych**: AI vs Human vs Game Mechanics
- **Kategoryzacja akcji**: Dowódca, Walka, Ruch, Zaopatrzenie, Strategia
- **Format ML-ready**: Przygotowane dane do uczenia maszynowego
- **Kompatybilność**: Zachowana zgodność z istniejącymi funkcjami

### Główne Cele
- 📊 **Analityka rozgrywki** - szczegółowe śledzenie decyzji i błędów
- 🤖 **Podłoże pod ML** - dane w formatach odpowiednich do trenowania
- 🔄 **Kompatybilność** - zachowanie istniejących funkcji logowania
- 📁 **Organizacja** - czytelna struktura katalogów

## 📁 Struktura Katalogów (Directory Structure)

```
logs/
├── ai/                          # Sztuczna Inteligencja (AI Logs)
│   ├── dowodca/                # AI Commander logs
│   │   ├── dane_YYYYMMDD_HHMMSS.json
│   │   ├── dane_YYYYMMDD_HHMMSS.csv
│   │   └── python_YYYYMMDD_HHMMSS.log
│   ├── general/                # AI General logs  
│   │   ├── dane_YYYYMMDD_HHMMSS.json
│   │   └── dane_YYYYMMDD_HHMMSS.csv
│   ├── walka/                  # Combat logs
│   ├── ruch/                   # Movement logs
│   ├── zaopatrzenie/          # Supply logs
│   └── strategia/             # Strategy logs
├── human/                      # Gracz Ludzki (Human Player)
│   ├── akcje/                 # Player actions
│   ├── decyzje/               # Player decisions
│   └── interfejs/             # UI interactions
├── game/                       # Mechanika Gry (Game Mechanics)
│   ├── mechanika/             # Core game mechanics
│   ├── stan/                  # Game state changes
│   └── bledy/                 # Error logs
└── analysis/                   # Analiza Danych (Data Analysis)
    ├── ml_ready/              # ML-ready datasets
    │   ├── ai_decyzje_TIMESTAMP.csv
    │   ├── skutecznosc_walki_TIMESTAMP.json
    │   └── ekonomia_ai_TIMESTAMP.parquet
    ├── raporty/               # Analysis reports
    └── statystyki/            # Statistics
```

## 🔧 Komponenty Systemu (System Components)

### 1. GameLogManager
**Lokalizacja**: `utils/game_log_manager.py`

Główny menedżer logowania z funkcjonalnościami:
- Kategoryzacja logów (KategoriaLog enum)
- System tagów (TagLog enum) 
- Wieloformatowe zapisywanie (JSON/CSV/Log)
- Statystyki sesji

### 2. IntegratorLogow  
**Lokalizacja**: `utils/ai_log_integrator.py`

Warstwa kompatybilności z istniejącymi funkcjami:
- `log_commander_action()` - akcje dowódcy
- `log_economy_turn()` - ekonomia AI
- `log_strategy_decision()` - decyzje strategiczne
- `log_supply_replenishment()` - zaopatrzenie

### 3. MLDataExporter
**Lokalizacja**: `utils/ml_data_exporter.py`  

Eksporter danych do uczenia maszynowego:
- Automatyczna ekstrakcja cech (feature extraction)
- Normalizacja danych 
- Tworzenie datasetów treningowych
- Export w formatach CSV/JSON/Parquet

## 🔗 Integracja z Istniejącym Kodem (Integration)

### Szybka Integracja (Quick Integration)
Dodaj na górze plików AI:

```python
# Kompatybilne funkcje logowania
from utils.ai_log_integrator import (
    log_commander_action,
    log_economy_turn,
    log_strategy_decision,
    log_supply_replenishment
)

# Nowy system (opcjonalnie)
from utils.game_log_manager import get_game_log_manager
```

### Zastąpienie Istniejących Importów
**Stary kod**:
```python
from ai.logowanie_ai import log_commander_action
```

**Nowy kod**:
```python
from utils.ai_log_integrator import log_commander_action
```

### Zachowanie Kompatybilności
Wszystkie istniejące wywołania funkcji działają bez zmian:

```python
# To działa identycznie jak wcześniej
log_commander_action(
    unit_id="tank_01",
    action_type="move", 
    from_pos=(10, 5),
    to_pos=(11, 6),
    reason="Advance to objective"
)
```

## 🤖 Eksport Danych ML (ML Data Export)

### Automatyczny Eksport
```python
from utils.ml_data_exporter import MLDataExporter

# Utworz eksporter
exporter = MLDataExporter()

# Wygeneruj wszystkie datasety
datasety = exporter.generuj_wszystkie_datasety()

# Eksportuj w wszystkich formatach
pliki = exporter.exportuj_wszystkie_datasety("wszystkie")
```

### Dostępne Datasety

#### 1. AI Decyzje (ai_decyzje)
**Cechy**:
- `tura` - numer tury
- `pe_start`, `pe_allocated` - ekonomia
- `threat_level`, `aggression_level` - parametry AI
- `action_*` - typ akcji (one-hot encoding)
- `strategic_state_encoded` - stan strategiczny

**Etykiety**: `target_decision` - typ decyzji do predykcji

#### 2. Skuteczność Walki (skutecznosc_walki)  
**Cechy**:
- `threat_level`, `mp_before`, `fuel_before` - stan jednostki
- `unit_*` - typ jednostki (one-hot)
- `aggression_level` - agresja AI

**Etykiety**:
- `combat_dmg_dealt` - zadane obrażenia (regresja)
- `combat_success` - sukces walki (klasyfikacja)

#### 3. Ekonomia AI (ekonomia_ai)
**Cechy**:
- `pe_start`, `pe_allocated`, `pe_spent_purchases` - ekonomia
- `efficiency_ratio` - obliczona efektywność
- `strategy_*` - używana strategia (one-hot)

**Etykiety**:
- `pe_efficiency` - efektywność ekonomiczna
- `strategy_success` - sukces strategii

## 🚀 Instrukcja Użycia (Usage Instructions)

### 1. Podstawowe Logowanie

```python
from utils.game_log_manager import get_game_log_manager, KategoriaLog, TagLog

# Pobierz menedżer
manager = get_game_log_manager()

# Ustaw kontekst gry
manager.ustaw_kontekst_gry(gracz="Germany", tura=5)

# Loguj akcję AI
manager.log_ai_dowodca(
    "Przesunięcie czołgów na pozycje ofensywne",
    szczegoly={"jednostki": 3, "cel": "Moskwa"},
    ml_dane={"threat_level": 8, "aggression": 0.7}
)

# Loguj błąd gry  
manager.log_game_error(
    "Błąd walidacji ruchu jednostki",
    szczegoly={"unit_id": "inf_05", "position": (10, 15)},
    poziom="ERROR"
)
```

### 2. Funkcje Wygodne (Convenience Methods)

```python
# AI Logs
manager.log_ai_dowodca("Akcja dowódcy")
manager.log_ai_general("Decyzja generała") 
manager.log_ai_walka("Walka jednostki")
manager.log_ai_ruch("Ruch jednostki")
manager.log_ai_zaopatrzenie("Zaopatrzenie")

# Human Logs  
manager.log_human_akcja("Akcja gracza")
manager.log_human_decyzja("Decyzja gracza")

# Game Logs
manager.log_game_mechanika("Mechanika gry")
manager.log_game_error("Błąd systemu")
```

### 3. Generowanie Raportów

```python
# Raport sesji
raport = manager.generuj_raport_sesji()
print(f"Łącznie wpisów: {raport['statystyki']['wpisy_lacznie']}")

# Zapisz raport  
manager.zapisz_raport_sesji()
```

### 4. Eksport ML

```python
from utils.ml_data_exporter import MLDataExporter

exporter = MLDataExporter()

# Pojedynczy dataset
dataset_ai = exporter.przygotuj_dataset_ai_decyzje()
pliki = exporter.exportuj_dataset(dataset_ai, "csv")

# Wszystkie datasety
wszystkie = exporter.exportuj_wszystkie_datasety()
```

## 💡 Przykłady Kodu (Code Examples)

### Przykład 1: Integracja w AI General

```python
# W pliku ai/ai_general.py
from utils.ai_log_integrator import log_economy_turn, log_strategy_decision
from utils.game_log_manager import get_game_log_manager

class AIGeneral:
    def __init__(self):
        self.log_manager = get_game_log_manager()
        
    def process_turn(self, turn):
        # Ustaw kontekst
        self.log_manager.ustaw_kontekst_gry("AI_Player", turn)
        
        # Stare funkcje działają bez zmian
        log_economy_turn(
            turn=turn,
            pe_start=100,
            pe_allocated=80,
            pe_spent_purchases=60,
            strategy_used="aggressive"
        )
        
        # Nowe funkcje z dodatkowymi danymi ML
        self.log_manager.log_ai_general(
            "Analiza strategiczna zakończona",
            ml_dane={
                "enemy_strength": 0.6,
                "our_strength": 0.8,
                "threat_assessment": 0.4
            }
        )
```

### Przykład 2: Eksport Danych dla ML

```python
# Skrypt analizy danych
from utils.ml_data_exporter import MLDataExporter
import pandas as pd

def analizuj_dane_ai():
    exporter = MLDataExporter()
    
    # Wygeneruj dataset AI
    dataset = exporter.przygotuj_dataset_ai_decyzje()
    
    if not dataset.dane_trenujace.empty:
        print(f"Dataset: {dataset.nazwa}")
        print(f"Rozmiar: {len(dataset.dane_trenujace)} wpisów")
        print(f"Cechy: {dataset.cechy}")
        
        # Podstawowa analiza
        df = dataset.dane_trenujace
        print(f"Średnia agresji AI: {df.get('aggression_level', pd.Series()).mean()}")
        
        # Eksport
        pliki = exporter.exportuj_dataset(dataset)
        print(f"Eksportowano: {pliki}")

if __name__ == "__main__":
    analizuj_dane_ai()
```

### Przykład 3: Analiza Logów

```python
# Skrypt analizy błędów
from utils.game_log_manager import get_game_log_manager
import json
from pathlib import Path

def analizuj_bledy():
    logs_dir = Path("logs")
    
    # Znajdź pliki błędów
    error_files = list(logs_dir.rglob("**/dane_*.json"))
    
    errors = []
    for file in error_files:
        with open(file) as f:
            data = json.load(f)
            
        for entry in data:
            if entry.get('poziom') == 'ERROR':
                errors.append(entry)
    
    print(f"Znaleziono {len(errors)} błędów:")
    for error in errors[-5:]:  # ostatnie 5
        print(f"- {error['timestamp']}: {error['akcja']}")

analizuj_bledy()
```

## 🛠️ Rozwiązywanie Problemów (Troubleshooting)

### Problem: Brak katalogów logów
**Objawy**: FileNotFoundError przy próbie zapisu  
**Rozwiązanie**:
```python
from utils.game_log_manager import get_game_log_manager
manager = get_game_log_manager()  # Automatycznie tworzy katalogi
```

### Problem: Stare funkcje nie działają
**Objawy**: ImportError dla log_commander_action  
**Rozwiązanie**:
```python
# Zmień import z:
from ai.logowanie_ai import log_commander_action
# Na:
from utils.ai_log_integrator import log_commander_action
```

### Problem: Pusty dataset ML
**Objawy**: "Pusty dataset: Brak danych AI"  
**Rozwiązanie**:
1. Sprawdź czy katalog `logs/` ma dane
2. Upewnij się, że logi AI zawierają pole `ml_dane`
3. Zweryfikuj format danych w JSON/CSV

### Problem: Błędy encoding
**Objawy**: UnicodeDecodeError  
**Rozwiązanie**: Wszystkie pliki używają UTF-8, sprawdź ustawienia systemu

### Debug Mode
```python
import logging
logging.basicConfig(level=logging.DEBUG)

from utils.game_log_manager import get_game_log_manager
manager = get_game_log_manager()
# Włączy szczegółowe logi debugowania
```

## 📊 Formaty Plików (File Formats)

### JSON Format
```json
{
  "timestamp": "2025-09-13T10:30:45.123456",
  "kategoria": "ai/dowodca",
  "tagi": ["ai", "strategia"],
  "gracz": "Germany",
  "tura": 5,
  "akcja": "Przesunięcie czołgów",
  "szczegoly": {
    "unit_count": 3,
    "target": "Moscow"
  },
  "ml_dane": {
    "threat_level": 8,
    "aggression": 0.7
  }
}
```

### CSV Format
```csv
timestamp,kategoria,tagi,gracz,tura,akcja,poziom,szczegoly_json,ml_dane_json
2025-09-13T10:30:45,ai/dowodca,"ai,strategia",Germany,5,Przesunięcie czołgów,INFO,"{""unit_count"":3}","{""threat_level"":8}"
```

## 📈 Statystyki i Metryki (Statistics & Metrics)

System automatycznie zbiera:
- Liczba wpisów per kategoria (AI/Human/Game)
- Liczba błędów
- Czas sesji
- Rozmiary datasetów ML

Dostęp przez:
```python
manager = get_game_log_manager()
stats = manager.generuj_raport_sesji()
print(stats['statystyki'])
```

## 🎯 Wykorzystanie w ML (ML Usage)

### Przygotowanie Danych
1. Uruchom grę z nowym systemem logowania
2. Wygeneruj logi przez kilka rozgrywek  
3. Eksportuj datasety ML
4. Trenuj modele na przygotowanych danych

### Przykładowe Modele
- **Klasyfikacja decyzji**: Predykcja następnej akcji AI
- **Regresja obrażeń**: Przewidywanie skuteczności walki
- **Analiza strategii**: Ocena efektywności różnych strategii

---

## 📝 Changelog

**v1.0.0** (2025-09-13)
- Pierwsza wersja systemu logowania
- Implementacja GameLogManager
- Integrator dla kompatybilności wstecznej  
- MLDataExporter z 3 podstawowymi datasetami
- Pełna dokumentacja techniczna

---

*Dokumentacja utworzona automatycznie przez AI Assistant*
*System przygotowany do rozbudowy i dostosowania do konkretnych potrzeb*