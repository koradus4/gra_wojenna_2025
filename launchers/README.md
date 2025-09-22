# 🚀 Launchery Gry Wojennej

Ten katalog zawiera alternatywne sposoby uruchamiania gry wojennej. Główny launcher znajduje się w katalogu głównym (`main.py`).

## 📋 Dostępne Launchery

### 🎯 **main.py** (Katalog główny) - GŁÓWNY LAUNCHER
**Najbardziej zaawansowany i zalecany launcher**
- 🧠 Pełna obsługa AI (Generał + Dowódca)
- 🎚️ Kontrola poziomu debugowania (BASIC/FULL)
- 🧹 Smart Log Cleaning System z ML protection
- 🔧 AI Config Panel z zaawansowanymi opcjami
- 📊 Szczegółowe logowanie i monitoring
- 💡 Interaktywna zmiana debug level

### 🎮 **main_basic.py**
**Podstawowy launcher z GUI**
- 👥 EkranStartowy GUI do wyboru graczy
- 🤖 Obsługa AI z graceful fallback
- 🧹 Automatyczne czyszczenie przed grą
- ⚡ Prostszy w użyciu dla początkujących

### ⚙️ **main_alternative.py**
**Launcher z opcjami czyszczenia**
- 🎚️ Proste okno opcji (bez EkranStartowy)
- 🏆 Wybór liczby tur (10/20/30)
- 💀 Tryb zwycięstwa (VP/Eliminacja)
- 🧹 Opcje szybkiego i pełnego czyszczenia
- 🎮 Automatyczne ustawienia graczy

### 🤖 **auto_test_ai.py**
**Automatyczny test AI vs AI**
- ⚡ 10-turowy test bez interfejsu
- 🧠 Wszyscy gracze to AI
- 🧹 Automatyczne czyszczenie przed testem
- 📊 Szczegółowa analiza wyników
- 🎯 Idealny do testowania AI

### 🧨 **main_ai_vs_human.py** (katalog główny)
**Pojedynek: AI Niemcy vs Polska (Human)**
- 🇩🇪 AI kontroluje Niemcy: Generał + 2 Dowódców
- 🇵🇱 Polska w pełni sterowana przez człowieka (GUI)
- 🎚️ Wykorzystuje aktualną konfigurację profilu AI (np. aggressive) z `ai/configs/ai_config.json`
- 🧹 Opcjonalne czyszczenie sesji (`--clean`)

## 🚀 Jak uruchomić?

```bash
# Główny launcher (zalecany)
python main.py

# Podstawowy launcher
python launchers/main_basic.py

# Alternatywny launcher
python launchers/main_alternative.py

# Test AI vs AI
python launchers/auto_test_ai.py

# AI Niemcy vs Polska (Human)
python main_ai_vs_human.py --turns 20 --victory turns --clean
```

## 💡 Rekomendacje

- **Dla graczy**: `main.py` (główny) - najlepsze doświadczenie
- **Dla początkujących**: `launchers/main_basic.py` - prostszy GUI
- **Dla szybkich testów**: `launchers/main_alternative.py` - minimalne opcje
- **Dla deweloperów AI**: `launchers/auto_test_ai.py` - automatyczny test

## ⚡ Szybki Start

1. **Nowa gra**: `python main.py`
2. **Test AI**: `python launchers/auto_test_ai.py --clean`
3. **Debugowanie**: Uruchom `main.py` i zmień debug level w konsoli

---
*Aktualizowano: 13 września 2025*