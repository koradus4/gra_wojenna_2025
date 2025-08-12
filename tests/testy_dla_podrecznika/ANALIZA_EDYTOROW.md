# 🔄 ANALIZA WPŁYWU EDYTORÓW NA AKTUALNOŚĆ PODRĘCZNIKA

## 📋 PRZEGLĄD EDYTORÓW

### 1. **clear_game_tokens.py** - Skrypt czyszczący
- **Funkcja**: Usuwa wszystkie żetony z gry
- **Wpływ na podręcznik**: ❌ **BEZPOŚREDNI**
- **Ryzyko**: Może usunąć wszystkie jednostki, powodując brak danych w podręczniku

### 2. **map_editor_prototyp.py** - Edytor mapy
- **Funkcja**: Edycja terenu, key points, spawn points
- **Wpływ na podręcznik**: ⚠️ **ŚREDNI**
- **Modyfikowane dane**:
  - Typy terenu i modyfikatory ruchu
  - Key points (miasta, fortyfikacje, węzły komunikacyjne)
  - Spawn points dla nacji

### 3. **token_editor_prototyp.py** - Edytor żetonów
- **Funkcja**: Tworzenie i edycja jednostek
- **Wpływ na podręcznik**: ❌ **KRYTYCZNY**
- **Modyfikowane dane**:
  - Statystyki jednostek (ruch, atak, obrona, zasięg)
  - Wsparcie i upgrade'y
  - Ceny i koszty utrzymania

### 4. **prototyp_kreator_armii.py** - Kreator armii
- **Funkcja**: Automatyczne tworzenie armii
- **Wpływ na podręcznik**: ⚠️ **ŚREDNI**
- **Modyfikowane dane**:
  - Koszty bazowe jednostek
  - Wsparcie i upgrade'y
  - Balans armii

## 🎯 SZCZEGÓŁOWA ANALIZA RYZYKA

### ❌ **KRYTYCZNE ZAGROŻENIA**

#### 1. **Zasięgi ataków jednostek**
**Aktualnie w podręczniku:**
- Piechota (P): 2 hex
- Artyleria (AL): 4 hex
- Kawaleria (K): 1 hex
- Czołgi lekkie (TL): 1 hex
- Czołgi średnie (TS): 2 hex
- Czołgi ciężkie (TŚ): 2 hex
- Zaopatrzenie (Z): 1 hex

**Ryzyko z Token Editor:**
```python
# Token Editor może generować dowolne zasięgi:
self.attack_range = tk.StringVar()  # Edytowalny przez użytkownika
"attack": {
    "range": 2,  # MOŻE BYĆ ZMIENIONE!
    "value": 6
}
```

#### 2. **Statystyki jednostek**
**Ryzyko z edytorów:**
- `move` - punkty ruchu
- `attack.value` - wartość ataku  
- `defense_value` - wartość obrony
- `combat_value` - wytrzymałość
- `sight` - zasięg wzroku
- `maintenance` - paliwo/utrzymanie
- `price` - cena zakupu

#### 3. **Wsparcie i upgrade'y**
**Aktualne w edytorach:**
```python
self.support_upgrades = {
    "drużyna granatników": {"movement": -1, "range": 1, "attack": 2, "defense": 1},
    "sekcja km.ppanc": {"movement": -1, "range": 1, "attack": 2, "defense": 2},
    "sekcja ckm": {"movement": -1, "range": 1, "attack": 2, "defense": 2},
    # ... więcej upgradów
}
```

**PROBLEM**: Podręcznik **NIE OPISUJE** systemu wsparcia!

### ⚠️ **ŚREDNIE ZAGROŻENIA**

#### 1. **Key Points na mapie**
**Aktualnie w podręczniku:**
- Miasta: 8 na mapie, wartość 100 pkt każde
- Fortyfikacje: 1 na mapie, wartość 150 pkt
- Węzły komunikacyjne: 3 na mapie, wartość 75 pkt każdy

**Ryzyko z Map Editor:**
```python
self.available_key_point_types = {
    "most": 50,              # NOWY TYP!
    "miasto": 100,           # Może być zmieniona wartość
    "węzeł komunikacyjny": 75,
    "fortyfikacja": 150
}
```

#### 2. **Typy terenu**
**Ryzyko z Map Editor:**
```python
TERRAIN_TYPES = {
    "teren_płaski": {"move_mod": 0, "defense_mod": 0},
    "mała rzeka": {"move_mod": 2, "defense_mod": 1},
    "duża rzeka": {"move_mod": 5, "defense_mod": -1},
    "las": {"move_mod": 2, "defense_mod": 2},
    "bagno": {"move_mod": 3, "defense_mod": 1},
    "mała miejscowość": {"move_mod": 1, "defense_mod": 2},
    "miasto": {"move_mod": 2, "defense_mod": 2},
    "most": {"move_mod": 0, "defense_mod": -1}
}
```

#### 3. **Koszty bazowe jednostek**
**Ryzyko z Army Creator:**
```python
self.unit_templates = {
    "P": {"base_cost": 25},   # Może być zmienione
    "K": {"base_cost": 30},
    "TL": {"base_cost": 35},
    # ... więcej kosztów
}
```

## 🛠️ REKOMENDACJE

### 1. **NATYCHMIASTOWE DZIAŁANIA**
- ❌ **Podręcznik NIE JEST odporny na zmiany z edytorów**
- 🔄 **Wymagana automatyczna synchronizacja**
- 📋 **Dodanie brakujących sekcji (wsparcie, upgrade'y)**

### 2. **AUTOMATYZACJA WERYFIKACJI**
```python
# Potrzebny skrypt weryfikujący po każdej zmianie w edytorach:
def verify_manual_after_editors():
    verify_unit_ranges()
    verify_key_points()
    verify_terrain_types()
    verify_support_system()
    verify_unit_costs()
```

### 3. **MONITORING ZMIAN**
- **Pliki do monitorowania:**
  - `assets/tokens/*/token.json` - statystyki jednostek
  - `data/map_data.json` - key points i teren
  - `assets/start_tokens.json` - rozmieszczenie startowe

## 🎯 KONKRETNE PROBLEMY

### ❌ **BRAKUJĄCE SEKCJE W PODRĘCZNIKU**
1. **System wsparcia** - Edytory mają pełny system upgradów, podręcznik go nie opisuje
2. **Mosty** - Nowy typ key point w edytorze (50 pkt), brak w podręczniku
3. **Złożone typy terenu** - Edytor ma więcej typów niż podręcznik
4. **Automatyczne balansowanie** - Army Creator ma zaawansowane algorytmy

### ⚠️ **ZMIENNE WARTOŚCI**
1. **Zasięgi ataków** - Mogą być zmienione przez Token Editor
2. **Statystyki jednostek** - Wszystkie edytowalne
3. **Ceny jednostek** - Mogą być modyfikowane
4. **Liczba i wartość key points** - Edytowalne przez Map Editor

## 🔄 PLAN AKTUALIZACJI

### FAZA 1: **ROZSZERZENIE PODRĘCZNIKA**
- Dodanie sekcji o systemie wsparcia
- Opis wszystkich typów terenu z edytora
- Dokumentacja systemu balansowania

### FAZA 2: **AUTOMATYZACJA**
- Skrypt synchronizujący podręcznik z danymi z edytorów
- Automatyczne testy weryfikacyjne po zmianach
- System alertów o niespójnościach

### FAZA 3: **MONITOROWANIE**
- Continuous integration dla spójności dokumentacji
- Automatyczne aktualizacje podręcznika
- Wersjonowanie zmian w mechanikach

## 🎯 OSTATECZNA OCENA

### ❌ **PODRĘCZNIK NIE JEST AKTUALNY PO UŻYCIU EDYTORÓW**

**Główne problemy:**
1. **Brak opisu systemu wsparcia** (który jest w pełni zaimplementowany)
2. **Statyczne wartości** mogą zostać zmienione przez edytory
3. **Brakujące typy terenu i key points**
4. **Brak mechanizmu synchronizacji**

**Rekomendacja:** 
🔄 **WYMAGANA NATYCHMIASTOWA AKTUALIZACJA PODRĘCZNIKA**
📋 **DODANIE MECHANIZMU AUTOMATYCZNEJ SYNCHRONIZACJI**
⚠️ **PODRĘCZNIK MOŻE STAĆ SIĘ NIEAKTUALNY PO KAŻDYM UŻYCIU EDYTORÓW**

---

**Status:** ❌ **KRYTYCZNY - PODRĘCZNIK NIEODPORNY NA ZMIANY**
**Priorytet:** 🔴 **WYSOKI - NATYCHMIASTOWE DZIAŁANIE WYMAGANE**
