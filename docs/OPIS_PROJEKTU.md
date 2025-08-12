# KAMPANIA 1939 - KOMPLETNY OPIS PROJEKTU

## WPROWADZENIE

"Kampania 1939" to zaawansowana gra strategiczna turowa z systemem sztucznej inteligencji. Projekt zawiera kompletny silnik gry, intuicyjny interfejs użytkownika oraz nowoczesny system AI zdolny do strategicznego myślenia i taktycznego działania.

## ARCHITEKTURA SYSTEMU

### 1. SILNIK GRY (`engine/`)
Serce aplikacji - obsługuje logikę gry:
- **`engine.py`** - główny silnik, integruje wszystkie komponenty
- **`board.py`** - mapa heksagonalna, pathfinding, overlay
- **`token.py`** - jednostki wojskowe, ładowanie z JSON
- **`player.py`** - gracze, widoczność, punkty zwycięstwa
- **`action.py`** - system rozkazów (ruch, walka)
- **`save_manager.py`** - zapis/wczytanie stanu gry
- **`hex_utils.py`** - funkcje geometryczne dla heksów

### 2. INTERFEJS UŻYTKOWNIKA (`gui/`)
Kompletny system GUI dla różnych ról:
- **`ekran_startowy.py`** - wybór graczy i rozpoczęcie gry
- **`panel_generala.py`** - interfejs dla generała (pełna mapa)
- **`panel_dowodcy.py`** - interfejs dla dowódcy (lokalna mapa)
- **`panel_gracza.py`** - wspólne elementy UI (VP, czas, akcje)
- **`panel_mapa.py`** - główny komponent mapy z interakcją
  - Przezroczystość żetonów nieaktywnych dowódców
  - Automatyczne centrowanie na jednostkach gracza
  - System scrollowania i nawigacji
- **`token_info_panel.py`** - szczegóły wybranej jednostki
- **`token_shop.py`** - kupowanie nowych jednostek
  - Kolory napisów zgodne z Token Editor
  - Poprawione zarządzanie zakupami

### 3. SYSTEMY PODSTAWOWE (`core/`)
Mechaniki rozgrywki:
- **`tura.py`** - zarządzanie turami i kolejnością graczy
- **`ekonomia.py`** - system punktów ekonomicznych
- **`pogoda.py`** - warunki atmosferyczne wpływające na grę
- **`dyplomacja.py`** - relacje między frakcjami
- **`zwyciestwo.py`** - warunki zakończenia gry

### 4. SZTUCZNA INTELIGENCJA (`ai/`)
Kompletny system AI z różnymi typami dowódców:
- **`commanders/`** - implementacje AI dla różnych dowódców
  - `ai_general.py` - AI Generał (strategia wysokiego poziomu)
  - `ai_field_commander.py` - AI Dowódca polowy (taktyka)
  - `base_commander.py` - bazowa klasa dowódcy
  - `human_commander.py` - wrapper dla gracza ludzkiego
- **`algorithms/`** - algorytmy AI (Mini-Max, MCTS, A*)
- **`ml/`** - Machine Learning modele (przygotowane)
- **`visualization/`** - wizualizacja decyzji AI

### 5. LAUNCHER AI (`game_launcher_ai.py`)
Dedykowany launcher dla rozgrywek z AI:
- Konfiguracja AI vs Człowiek dla każdego gracza
- Poziomy trudności: Easy, Medium, Hard, Expert
- Panel debugowania AI w czasie rzeczywistym
- Wizualizacja procesu podejmowania decyzji

## SYSTEM AI - SZCZEGÓŁY

### 🤖 Typy AI

#### AI Generał (Strategia)
- **Widoczność**: Cała mapa strategiczna
- **Funkcje**:
  - Zarządzanie ekonomią (punkty ekonomiczne)
  - Wsparcie dowódców (przydzielanie zasobów)
  - Zakup nowych jednostek
  - Planowanie strategiczne długoterminowe
- **Algorytmy**: Monte Carlo Tree Search (MCTS)

#### AI Dowódca (Taktyka)
- **Widoczność**: Tylko własne jednostki (inne przezroczyste)
- **Funkcje**:
  - Zarządzanie ruchem jednostek
  - Walka taktyczna
  - Uzupełnianie paliwa/zapasów
  - Wykonanie planów generała
- **Algorytmy**: Mini-Max z Alpha-Beta Pruning

### 🧠 Algorytmy AI
- **Mini-Max z Alpha-Beta Pruning**: Decyzje taktyczne dowódców
- **Monte Carlo Tree Search (MCTS)**: Planowanie strategiczne generałów
- **A* Pathfinding**: Optymalne ścieżki ruchu jednostek
- **Funkcje Ewaluacji**: Ocena pozycji strategicznych i taktycznych

### 📊 Poziomy Trudności AI

#### 🟢 Easy (Łatwy)
- Dokładność decyzji: 65%
- Mini-Max głębokość: 2
- MCTS symulacje: 500
- Czasem podejmuje suboptymalne decyzje

#### 🟡 Medium (Średni)
- Dokładność decyzji: 80%
- Mini-Max głębokość: 3
- MCTS symulacje: 1000
- Zbalansowane decyzje

#### 🔴 Hard (Trudny)
- Dokładność decyzji: 95%
- Mini-Max głębokość: 4
- MCTS symulacje: 1500
- Bardzo efektywne decyzje

#### ⚫ Expert (Ekspert)
- Dokładność decyzji: 100%
- Mini-Max głębokość: 5
- MCTS symulacje: 2000
- Perfekcyjne decyzje strategiczne

### 🔧 Debugowanie AI
- **Panel Debugowania**: Monitorowanie myślenia AI w czasie rzeczywistym
- **Drzewo Decyzji**: Graficzna wizualizacja procesu podejmowania decyzji
- **Metryki Wydajności**: Analiza skuteczności AI
- **Historia Decyzji**: Wszystkie podjęte decyzje z uzasadnieniem

## WYDAJNOŚĆ I OPTYMALIZACJA

### Wymagania Systemowe dla AI:
- **CPU**: Wielordzeniowy (MCTS wykorzystuje wielowątkowość)
- **RAM**: 4GB+ (dla większych drzew decyzji)
- **Dysk**: 100MB+ (dla logów i modeli ML)

### Optymalizacje:
- AI automatycznie dostosowuje parametry do wydajności systemu
- Limity czasowe zapobiegają zawieszeniu gry
- Cache wyników ewaluacji zwiększa szybkość
- Wielowątkowość dla MCTS i pathfinding

## ROZWIĄZYWANIE PROBLEMÓW AI

### Częste Problemy:

1. **AI nie podejmuje decyzji**:
   - Sprawdź czy są jednostki do sterowania
   - Zwiększ limit czasu AI
   - Włącz debugowanie

2. **Gra działa wolno z AI**:
   - Zmniejsz głębokość Mini-Max
   - Ogranicz symulacje MCTS
   - Wyłącz debugowanie
   - Wybierz łatwiejszy poziom AI

3. **Błędy importu AI**:
   - Sprawdź czy wszystkie pliki AI są w miejscu
   - Uruchamiaj z głównego katalogu projektu
   - Sprawdź zależności Python

### Logi Debugowania AI:
AI zapisuje szczegółowe logi w trybie debugowania:
- Decyzje podjęte z uzasadnieniem
- Czasy wykonania algorytmów
- Błędy i ostrzeżenia
- Metryki wydajności

## ROZWÓJ AI - PRZYSZŁE PLANY

### Planowane Funkcjonalności:
- **Uczenie przez wzmacnianie**: DQN/PPO implementation
- **Multigaming**: AI uczy się z wielu rozgrywek
- **Adaptive AI**: AI dostosowuje się do stylu gracza
- **Tournament Mode**: Turnieje AI vs AI
- **Custom AI**: Możliwość tworzenia własnych strategii

### Rozszerzalność:
System jest przygotowany na dodanie:
- Nowych typów komendantów AI
- Dodatkowych algorytmów AI
- Własnych funkcji ewaluacji
- Nowych sposobów uczenia maszynowego

## PRZEPŁYW DZIAŁANIA

### Uruchomienie:
1. **main.py** → Ekran startowy → Wybór graczy (Human vs Human)
2. **main_alternative.py** → Bezpośredni start z domyślnymi ustawieniami
3. **🆕 game_launcher_ai.py** → Launcher z AI - konfiguracja AI vs Człowiek

### Uruchamianie z AI:
```bash
cd kampania1939_ai
python game_launcher_ai.py
```

### Konfiguracja AI:
1. **Wybór Trybu Gry**: Człowiek vs AI, AI vs AI, Człowiek vs Człowiek
2. **Konfiguracja Graczy**: Dla każdego z 6 graczy wybierz AI lub Człowiek
3. **Poziom Trudności**: Easy/Medium/Hard/Expert dla każdego AI
4. **Parametry AI**: Głębokość algorytmów, tryb debugowania
5. **Rozpocznij Grę**: Obserwuj jak AI podejmuje decyzje

### Inicjalizacja gry:
1. Ładowanie mapy (`data/map_data.json`)
2. Ładowanie jednostek (`assets/tokens/`)
3. Tworzenie objektów graczy z ekonomią
4. Inicjalizacja widoczności
5. Uruchomienie pętli tur

### Pętla rozgrywki:
```
PĘTLA GŁÓWNA:
├── Sprawdzenie załadowanego save
├── Aktualizacja aktywnego gracza
├── Uruchomienie odpowiedniego panelu (Generał/Dowódca)
├── Oczekiwanie na akcje gracza
├── Przetwarzanie rozkazów
├── Aktualizacja widoczności
├── Sprawdzenie warunków końca tury
├── Przejście do kolejnego gracza
└── Sprawdzenie warunków końca gry
```

### Mechanika tur:
1. **Generał** - widzi całość, zarządza ekonomią, wydaje rozkazy strategiczne
2. **Dowódca 1** - kontroluje swoje jednostki, wykonuje ruchy taktyczne  
3. **Dowódca 2** - kontroluje swoje jednostki, wykonuje ruchy taktyczne
4. **Generał przeciwny** - jak wyżej dla drugiej strony
5. **Dowódcy przeciwni** - jak wyżej
6. **Koniec tury** - rozliczenie ekonomii, reset punktów ruchu

## KLUCZOWE FEATURES

### System widoczności:
- Każda jednostka ma zasięg widzenia
- Generał widzi wszystkie jednostki swojej armii
- Dowódca widzi tylko swoje + wykryte wrogie
- Tymczasowa widoczność podczas ruchu
- **NOWE**: Przezroczystość żetonów nieaktywnych dowódców (40% alpha)
- **NOWE**: Automatyczne centrowanie mapy na jednostkach gracza

### System ekonomiczny:
- Punkty ekonomiczne co turę
- Punkty specjalne z kluczowych lokacji
- Kupowanie nowych jednostek
- Uzupełnianie zapasów
- **NAPRAWIONE**: Poprawne usuwanie żetonów z puli po wystawieniu

### System walki:
- Wartości ataku/obrony jednostek
- Modyfikatory terenu i dystansu  
- Losowość wyników
- Różne typy amunicji

### Tryby ruchu:
- **Combat** - wolny, ekonomiczny
- **March** - standardowy
- **Recon** - szybki, kosztowny

## BEZPIECZEŃSTWO I INTEGRALNOŚĆ

### Weryfikacja właściciela:
- Każdy rozkaz sprawdza czy jednostka należy do gracza
- Blokada dostępu do cudzych jednostek

### Integralność zapisu:
- Pełna serializacja stanu gry
- Weryfikacja spójności po wczytaniu
- Backup automatyczny

### Walidacja rozkazów:
- Sprawdzanie punktów ruchu/paliwa
- Walidacja ścieżek ruchu
- Kontrola zasięgu ataku

## ROZSZERZALNOŚĆ

Projekt przygotowany na:
- Implementację AI dowódców
- Dodanie nowych typów jednostek
- Rozbudowę systemu dyplomacji
- Multiplayer online
- Moddowanie map i scenariuszy

## TESTOWANIE

Kompletny zestaw testów:
- Testy integracyjne całej rozgrywki
- Testy systemu zapisu/wczytania
- Testy mechanik ruchu i walki
- Testy interfejsu użytkownika

## OSTATNIE AKTUALIZACJE (Czerwiec 2025)

### ✅ Naprawione błędy:
- **Problem wystawiania żetonów** - poprawne usuwanie z puli po deployment
- **Błąd AttributeError** - dodana inicjalizacja `current_path` w PanelMapa
- **Kolory napisów** - Token Shop używa tych samych kolorów co Token Editor
- **Migające przyciski** - poprawne odświeżanie stanu po wystawieniu żetonu

### 🆕 Nowe funkcje:
- **System AI** - kompletna implementacja AI vs AI gameplay
- **AI General + AI Field Commander** - hierarchia dowodzenia AI
- **Game Launcher AI** - dedykowany launcher dla AI vs AI
- **Poziomy trudności AI** - Easy, Medium, Hard, Expert
- **Debugowanie AI** - panel monitorowania myślenia AI w czasie rzeczywistym
- **Przezroczystość żetonów** - nieaktywni dowódcy mają żetony z 40% alpha
- **Auto-centrowanie mapy** - automatyczne wycentrowanie na jednostkach gracza
- **Lepszy UX** - natychmiastowe rozpoznanie żetonów aktywnego dowódcy

### 🎯 Usprawnienia wizualne:
- Żetony aktywnego dowódcy: jasne, wyraźne kolory
- Żetony nieaktywnych: przyciemnione, w tle
- Generał widzi wszystkie żetony normalnie
- Płynne przejścia między turami
- Wizualizacja decyzji AI
- Panel debugowania AI z metrykami wydajności

### 🤖 Nowy System AI:
- **AI vs AI rozgrywki** - pełne auto-play
- **Człowiek vs AI** - wyzwanie dla gracza
- **Różne algorytmy**: Mini-Max, MCTS, A* pathfinding
- **Konfigurowalność**: parametry, poziomy trudności
- **Transparentność**: pełne debugowanie procesu myślenia AI

## SZYBKI START

### Dla Nowych Użytkowników:
1. **Uruchom**: `python main.py` (standardowa gra)
2. **Lub z AI**: `python game_launcher_ai.py` (AI vs Człowiek)
3. **Wybierz**: "Człowiek vs AI Łatwy"
4. **Rozpocznij grę** i obserwuj decyzje AI
5. **Włącz debugowanie** aby zobaczyć myślenie AI

### Dla Zaawansowanych:
1. **AI vs AI**: Obserwuj walkę algorytmów
2. **Debugowanie**: Monitoruj proces podejmowania decyzji
3. **Konfiguracja**: Dostosuj parametry AI do swoich potrzeb
4. **Eksperymenty**: Testuj różne poziomy trudności

## AUTOR I LICENCJA

**Projekt**: Kampania 1939 z systemem AI  
**Data**: 2025-06-21  
**Status**: Aktywny rozwój  
**Kompatybilność**: Pełna z oryginalnym kodem gry

System AI został stworzony jako rozszerzenie istniejącej gry, zachowując pełną kompatybilność z oryginalnym kodem.

---

**Miłej gry z nowym inteligentnym przeciwnikiem!** 🎮🤖
