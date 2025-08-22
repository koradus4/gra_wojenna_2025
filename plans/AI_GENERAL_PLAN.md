# PLAN ROZWOJU AI GENERAŁA - WERSJA 1.0

## 📌 CEL GŁÓWNY
Stworzenie uczciwego i inteligentnego AI Generała, który podejmuje decyzje ekonomiczne w oparciu o analizę stanu własnych dowódców i ich jednostek, działając w ramach tych samych zasad co gracz ludzki.

## 📁 PLIKI PROJEKTU WYKORZYSTANE W PLANIE

### **GŁÓWNE PLIKI IMPLEMENTACJI:**

**ai/ai_general.py** - Główny plik AI Generała
- *Dlaczego:* Zawiera logikę decyzyjną AI, metody zakupów, budżetu
- *Użycie:* Dodanie dostępu do VP, Key Points, poprawki logiki decide_action()

**engine/engine.py** - Rdzeń gry z danymi strategicznymi  
- *Dlaczego:* Zawiera key_points_state, player management, kontroler główny
- *Użycie:* Dostęp do Key Points, stanu gry dla AI

**engine/player.py** - Zarządzanie graczami i ich danymi
- *Dlaczego:* Zawiera victory_points, economic_points, dowódców gracza
- *Użycie:* Dostęp AI do VP, PE, listy dowódców

**core/zwyciestwo.py** - System warunków zwycięstwa
- *Dlaczego:* Zarządza VP, max_turns, warunkami końca gry
- *Użycie:* AI analizuje etap gry i stan VP dla strategii

**core/tura.py** - Zarządzanie turami
- *Dlaczego:* TurnManager z current_turn, fazy gry
- *Użycie:* AI określa etap gry (wczesny/średni/późny)

**core/ekonomia.py** - System ekonomiczny  
- *Dlaczego:* Zarządzanie punktami ekonomicznymi, Key Points
- *Użycie:* AI analizuje dochody z Key Points

### **PLIKI POMOCNICZE:**

**core/unit_factory.py** - Fabryka jednostek
- *Dlaczego:* Tworzenie żetonów, szablony jednostek
- *Użycie:* AI używa do zakupów programowych

**engine/token.py** - Definicje żetonów
- *Dlaczego:* Struktura danych żetonów, combat value, paliwo  
- *Użycie:* AI analizuje stan jednostek dowódców

**engine/board.py** - Zarządzanie mapą
- *Dlaczego:* Pozycje żetonów, hex_grid, lokalizacje
- *Użycie:* AI analizuje pozycje strategiczne

**gui/panel_gracza.py** - Panel gracza z logiką ekonomiczną
- *Dlaczego:* Metody budget allocation, UI economiczny
- *Użycie:* AI wykorzystuje te same metody co human

**gui/panel_generala.py** - GUI Human Generała z pełną logiką
- *Dlaczego:* Zawiera metody: toggle_support_sliders(), open_token_shop(), update_economy()
- *Użycie:* AI musi replikować te EXACT funkcjonalności bez GUI

**gui/token_shop.py** - Sklep zakupu jednostek Human Generała
- *Dlaczego:* Pełna logika zakupów: wybór typu, rozmiaru, wsparcia, transportu
- *Użycie:* AI musi używać identycznej logiki zakupów programowo

**gui/zarzadzanie_punktami_ekonomicznymi.py** - Przydzielanie PE dowódcom
- *Dlaczego:* Suwaki i logika alokacji punktów między dowódców
- *Użycie:* AI replika tej logiki dla sprawiedliwego podziału PE

## 🔍 ANALIZA STANU (CO AI MUSI WIEDZIEĆ)

### Analiza per dowódca:
- **Żetony dowódcy:** lista wszystkich jednostek każdego dowódcy
- **Stan paliwa per dowódca:** % żetonów z niskim paliwem (<30%)
- **Combat value per dowódca:** średni combat value żetonów dowódcy
- **Typ jednostek per dowódca:** piechota, artyleria, zaopatrzenie, etc.
- **Lokalizacja dowódcy:** pozycja względem wrogów i key points
- **Historia strat per dowódca:** trendy ubytków w poprzednich turach

### Analiza globalna:
- **Dostępne punkty ekonomiczne generała**
- **Status VP:** nasze_vp vs wrogie_vp  
- **Etap gry:** aktualna_tura / (max_tur / 3)
- **Key Points:** lokalizacje i kontrola (własne/wrogie/neutralne)
- **Prognoza dochodów:** z key points w kolejnych turach

## 🔍 ANALIZA HUMAN GENERAŁA (WZORZEC DO REPLIKACJI)

### **EXACT FUNKCJONALNOŚCI HUMAN GENERAŁA:**

**1. ALOKACJA PUNKTÓW** (`toggle_support_sliders()` w panel_generala.py):
- Otwiera modal z suwakami dla każdego dowódcy
- Podział max punktów między dowódców z kontrolą limitu
- Synchronizacja: `dowodca.economy.economic_points += przydzielone`
- Odejmowanie z puli: `self.ekonomia.subtract_points(suma)`

**2. ZAKUP JEDNOSTEK** (`open_token_shop()` → `TokenShop.buy_unit()`):
- Wybór: nacja, typ jednostki, rozmiar, wsparcie, transport
- Generowanie unikalnego ID: `nowy_{typ}_{rozmiar}__{dowodca_id}_{label}_{timestamp}`
- Tworzenie: token.json + token.png w folderze assets/tokens/nowe_dla_{dowodca_id}/
- Odejmowanie kosztów: `self.ekonomia.subtract_points(cena)`
- Callback: `on_purchase_callback()` → `refresh_points()`

**3. RAPORT EKONOMICZNY** (`update_economy()`):
- Wyświetla: PE generała, punkty specjalne, PE każdego dowódcy
- Źródło danych: `self.ekonomia.get_points()` + `dowodca.economy.get_points()`

**AI MUSI MIEĆ TE SAME MOŻLIWOŚCI - BEZ GUI:**
- Te same metody alokacji/zakupu
- Te same źródła danych (ekonomia, dowódcy)
- Te same koszty i ograniczenia
- Identyczny workflow tworzenia jednostek

## ⚙️ OPCJE DZIAŁANIA AI GENERAŁA

**ZACHOWANE 100% - BEZ ZMIAN:**

1. **ALOKACJA PUNKTÓW** dowódcom
   - Identyczne zasady jak human generał
   - Te same możliwości przekazywania PE
   - Pełny parytet bez oszukiwania

2. **ZAKUP ŻETONÓW** dla dowódców  
   - Te same możliwości co human generał
   - Identyczne szablony i koszty jednostek
   - Bez oszukiwania, pełen parytet

3. **KOMBINACJA** alokacji + zakupów
   - Podział budżetu między opcje (20-40-40)
   - Adaptacja % według sytuacji
   - Bez utraty funkcjonalności

4. **HOLD** (oszczędzanie)
   - W sytuacjach niepewności

**NOWE DANE STRATEGICZNE:**
- AI teraz **widzi VP** i może dostosować % budżetu
- AI teraz **widzi Key Points** i może priorytetyzować kontrolę
- AI teraz **zna etap gry** i może planować długoterminowo

## 🧠 ZASADY DECYZYJNE AI

### 📊 DANE WEJŚCIOWE (Co AI musi wiedzieć - PARYTET Z HUMAN GENERAŁEM)

**Victory Points (VP) - PEŁNY DOSTĘP:**
- [x] Własne VP (`player.victory_points`)
- [x] VP przeciwnika (suma VP wrogiej nacji)
- [x] Historia VP (`player.vp_history`) - trend zwycięstwa
- [x] VP za eliminację = cena zniszczonej jednostki

**Key Points - PEŁNY DOSTĘP:**
- [x] Lokalizacje wszystkich Key Points (`game_engine.key_points_state`)
- [x] Wartość każdego Key Point (ekonomiczna korzyść)
- [x] Kto kontroluje które punkty (własne/wrogie/neutralne)
- [x] Historia dochodów z Key Points

**Informacje o grze - PEŁNY DOSTĘP:**
- [x] Aktualna tura (`game_engine.turn` lub `turn_manager.current_turn`)
- [x] Maksymalna liczba tur (`victory_conditions.max_turns`)
- [x] Pozostały czas: `(max_turns - current_turn)`
- [x] Faza gry: `current_turn / (max_turns / 3)`

**Analiza dowódców - ZACHOWANE:**
- [x] Żetony per dowódca z paliwo/combat value
- [x] Jednostki dowódcy (bez zmian)
- [x] Priorytety dowódców (bez zmian)

### 💰 PODSTAWOWE ZASADY BUDŻETU (20-40-40)

**BAZOWA STRATEGIA:**
- **20% REZERWA** - zawsze na nieprzewidziane sytuacje
- **40% ALOKACJA** - punkty ekonomiczne dla dowódców (paliwo, regeneracja)
- **40% ZAKUPY** - nowe żetony dla dowódców

### 🔄 ADAPTACJA CO TURĘ NA PODSTAWIE:

**1. ANALIZA DOWÓDCÓW:**
- **Paliwo:** % jednostek każdego dowódcy z niskim paliwem (<30%)
- **Combat Value:** średni combat value żetonów każdego dowódcy
- **Zapotrzebowanie:** który dowódca najbardziej potrzebuje wsparcia

**2. ETAP GRY** (wszystkie tury ÷ 3):
- **POCZĄTEK** (1/3 tur): 20-40-40 → focus na rozwój
- **ŚRODEK** (2/3 tur): adaptacja → walka o pozycje
- **KONIEC** (3/3 tur): adaptacja → decydujące ruchy

**3. STATUS VP:**
- **WYGRYWAMY VP:** więcej na alokację (ochrona)
- **PRZEGRYWAMY VP:** więcej na zakupy (agresja)
- **REMIS VP:** standardowe 20-40-40

### 📊 KONKRETNE ADAPTACJE BUDŻETU:

**KRYZYS PALIWA** (>30% jednostek dowódcy bez paliwa):
- 15% rezerwa, **70% alokacja**, 15% zakupy

**KOŃCÓWKA + PRZEGRYWAMY VP:**
- 10% rezerwa, 25% alokacja, **65% zakupy** (desperacja!)

**KOŃCÓWKA + WYGRYWAMY VP:**
- 30% rezerwa, **55% alokacja**, 15% zakupy (ochrona!)

**ŚRODEK + RÓWNE VP:**
- 20% rezerwa, 35% alokacja, **45% zakupy** (ekspansja!)

### 🎮 PRIORYTETY STRATEGICZNE

**1. SURVIVAL** (najwyższy priorytet):
- Uzupełnij paliwo jeśli >30% jednostek sparaliżowanych
- Kup Supply (Z) jeśli brak zaopatrzenia
- Zabezpiecz generała przed eliminacją

**2. VP HUNTING** (gdy przegrywamy):
- Priorytet jednostek ofensywnych (artyleria, pancerne)
- Agresywne pozycjonowanie
- Więcej % na zakupy niż uzupełnienia

**3. KEY POINTS CONTROL**:
- Oceniaj wartość ekonomiczną vs ryzyko
- Priorytet dla najbogatszych punktów
- Mobilne jednostki do szybkiego zajmowania

**4. VP PROTECTION** (gdy wygrywamy):
- Obronne pozycjonowanie
- Więcej % na uzupełnienia
- Unikaj niepotrzebnych walk

### ⚖️ SYSTEM PODEJMOWANIA DECYZJI

**ALGORYTM CO TURĘ:**

**KROK 1 - ZBIERANIE DANYCH STRATEGICZNYCH:**
```
// NOWE: Pełny dostęp do danych strategicznych
own_vp = sum(vp for p in players if p.nation == ai_nation)
enemy_vp = sum(vp for p in players if p.nation != ai_nation)
vp_status = own_vp - enemy_vp

current_turn = game_engine.turn
max_turns = victory_conditions.max_turns
turns_left = max_turns - current_turn
game_phase = current_turn / (max_turns / 3)

key_points_controlled = analyze_key_points_control(game_engine.key_points_state)
```

**KROK 2 - ANALIZA DOWÓDCÓW (ZACHOWANE):**
```
FOR każdy_dowódca:
  - paliwo_ratio = żetony_z_niskim_paliwem / wszystkie_żetony
  - combat_avg = średni_combat_value_żetonów
  - potrzeba_wsparcia = (paliwo_ratio * 0.6) + (combat_avg_loss * 0.4)
```

**KROK 3 - OKREŚLENIE STRATEGII:**
```
IF max(paliwo_ratio_dowódców) > 0.3: "KRYZYS_PALIWA"
ELIF game_phase > 2.0 AND vp_status < 0: "DESPERACJA" 
ELIF game_phase > 2.0 AND vp_status > 0: "OCHRONA"
ELIF game_phase > 1.0: "EKSPANSJA"
ELSE: "ROZWÓJ"
```

**KROK 4 - WYKONANIE (ZACHOWANE 100%):**
1. Zastosuj % budżetu według strategii
2. **ALOKUJ** punkty dowódcom według priorytetów
3. **KUP** żetony dla dowódców z największymi brakami
4. **KOMBINUJ** oba podejścia według potrzeb

### Zasady uczciwości:
- AI działa w ramach tych samych reguł co gracz ludzki
- Brak bonusów, skrótów ani oszukiwania
- Pełny parytet możliwości z human generałem

## 🚀 PLAN IMPLEMENTACJI

### FAZA 1: Rozbudowa analizy stanu ✅ **UKOŃCZONE**
- [x] **Udoskonalenie zbierania danych o jednostkach** - analyze_units() z pełną analizą per dowódca
- [x] **Śledzenie trendów (straty, zużycie paliwa)** - struktura _unit_analysis z metrykami
- [x] **Analiza zagrożeń i możliwości** - nowa metoda analyze_strategic_situation() 
- [x] **Dostęp do VP, Key Points, fazy gry** - pełna implementacja w analyze_strategic_situation()

### FAZA 2: Rozbudowa logowania i audytu ✅ **UKOŃCZONE**
- [x] **Log ekonomii AI** - pe_start/allocated/spent/remaining per tura ✅ log_economy_turn()
- [x] **Log Key Points** - wartość/kontrola/dochód per tura per punkt ✅ log_keypoints_turn()
- [x] **Weryfikacja PE** - czy poprawnie aktualizowane między turami ✅ w make_turn()
- [x] **Audyt strategii** - analiza decyzji AI w kontekście sytuacji ✅ log_strategy_decision()

### FAZA 3: Rozbudowa opcji działania ✅ **UKOŃCZONE**
- [x] **Implementacja kombinacji zakupów + przydziału** ✅ EconAction.COMBO z elastycznym budżetem
- [x] **Elastyczne % podziału budżetu** ✅ BUDGET_STRATEGIES z adaptacją 20-40-40 
- [x] **Uwzględnienie priorytetów strategicznych** ✅ _determine_strategy() implementuje plan

### FAZA 4: Inteligentne zasady decyzyjne ✅ **UKOŃCZONE**
- [x] **Implementacja ustalonych zasad** ✅ Strategiczny decide_action() zgodny z planem
- [x] **Testowanie różnych scenariuszy** ✅ 5 strategii: ROZWÓJ/KRYZYS_PALIWA/DESPERACJA/OCHRONA/EKSPANSJA  
- [x] **Balansowanie agresywności vs ostrożności** ✅ Adaptacyjne % budżetu według sytuacji VP/fazy gry

### FAZA 5: Optymalizacja i testy
- [ ] Testy z graczami ludzkimi
- [ ] Dostrajanie parametrów
- [ ] Dokumentacja końcowa
- [ ] **Weryfikacja logów** - kontrola poprawności PE i Key Points między turami

## ✅ **IMPLEMENTACJA UKOŃCZONA - GOTOWE DO TESTÓW**

### 🎯 **CO ZOSTAŁO ZAIMPLEMENTOWANE:**

**PEŁNY PARYTET Z HUMAN GENERAŁEM:**
- ✅ Dostęp do Victory Points (VP) - własne i wrogiego gracza
- ✅ Dostęp do Key Points - kontrola, wartość, dochody  
- ✅ Dostęp do informacji o turze - aktualna/max/faza gry
- ✅ Analiza jednostek per dowódca - paliwo, combat value, typy
- ✅ Identyczne możliwości ekonomiczne (alokacja + zakupy)

**STRATEGICZNE ZASADY DECYZYJNE:**
- ✅ System 20-40-40 z adaptacją według sytuacji
- ✅ 5 strategii: ROZWÓJ/KRYZYS_PALIWA/DESPERACJA/OCHRONA/EKSPANSJA
- ✅ Akcja COMBO - kombinacja alokacji + zakupów
- ✅ Elastyczne % budżetu według VP, fazy gry, stanu paliwa

**SYSTEM LOGOWANIA I AUDYTU:**
- ✅ Log ekonomii AI per tura (PE start/allocated/spent/remaining)
- ✅ Log Key Points per tura (kontrola/wartość/dochód)
- ✅ Log strategii AI (decyzje/zasady/kontekst)
- ✅ Pliki CSV w logs/ai_general/ z timestamps

**ROZBUDOWANE ANALIZY:**
- ✅ analyze_units() - pełna analiza per dowódca z metrykami
- ✅ analyze_strategic_situation() - VP, Key Points, faza gry
- ✅ _determine_strategy() - implementuje logikę z planu

### 🚀 **GOTOWE DO FAZY TESTOWEJ:**
AI Generał ma teraz **pełny parytet** z human generałem oraz **inteligentne zasady strategiczne** zgodnie z planem. Wszystkie funkcjonalności są zaimplementowane i gotowe do testów!

## 📊 METRYKI SUKCESU

**PODSTAWOWE:**
- AI podejmuje sensowne decyzje ekonomiczne
- Nie ma przewagi nad graczem ludzkim (fairplay)
- Reaguje adaptacyjnie na zmieniającą się sytuację
- Kod jest zrozumiały i łatwy do modyfikacji

**LOGOWANIE I AUDYT:**

### 💰 Log Ekonomii AI (per tura):
```csv
timestamp,turn,nation,pe_start,pe_allocated,pe_spent_purchases,pe_total_used,pe_remaining,strategy_used,vp_own,vp_enemy,vp_status
```
- **pe_start** - PE na początku tury
- **pe_allocated** - ile PE rozdano dowódcom
- **pe_spent_purchases** - ile PE wydano na zakupy
- **pe_total_used** - suma wydatków (allocated + purchases)
- **pe_remaining** - ile PE zostało na koniec tury
- **strategy_used** - użyta strategia (KRYZYS_PALIWA, DESPERACJA, etc.)

### 🗺️ Log Key Points (per tura):
```csv
timestamp,turn,hex_id,kp_type,kp_value_start,kp_controlled_by,kp_income_generated,kp_value_end
```
- **kp_value_start** - wartość Key Point na początku tury
- **kp_controlled_by** - kto kontroluje (Polska/Niemcy/Neutral)
- **kp_income_generated** - ile PE wygenerował w tej turze
- **kp_value_end** - wartość Key Point na końcu tury

### 🎯 Cel logowania:
- **Weryfikacja PE** - sprawdzenie czy PE są poprawnie aktualizowane między turami
- **Audyt Key Points** - śledzenie dochodów i kontroli punktów strategicznych
- **Debug strategii** - analiza czy AI podejmuje sensowne decyzje
- **Balans gry** - kontrola czy AI nie ma nieuczciwych korzyści

## 📝 LOG ZMIAN
- **20.08.2025** - Utworzenie planu, sekcja na przyszłe ustalenia zasad
- **22.08.2025** - Dodanie wymagań pełnego parytetu z human generałem (VP, Key Points, tury)
- **22.08.2025** - Dodanie wymagań szczegółowego logowania PE i Key Points per tura

---
*Dokument roboczy - będzie aktualizowany w miarę ustalania szczegółów implementacji*
