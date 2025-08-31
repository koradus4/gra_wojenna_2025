# 🎖️ Balansowanie Żetonów - Kompletny Przewodnik

## 🎯 **Gdzie balansować jednostki:**

**GŁÓWNY PLIK: `balance/model.py`** - Centralny system balansowania

## 📊 **System BASE_STATS - Podstawowe statystyki jednostek**

### 🗂️ **11 typów jednostek w BASE_STATS:**
```python
BASE_STATS = {
    "P":  {"movement": 3, "attack_range": 1, "attack_value": 8,  "combat_value": 8,  "defense_value": 10, "sight": 3},  # Piechota
    "K":  {"movement": 6, "attack_range": 1, "attack_value": 6,  "combat_value": 6,  "defense_value": 8,  "sight": 5},  # Kawaleria
    "TL": {"movement": 5, "attack_range": 1, "attack_value": 10, "combat_value": 10, "defense_value": 12, "sight": 3},  # Czołg lekki
    "TŚ": {"movement": 4, "attack_range": 2, "attack_value": 14, "combat_value": 14, "defense_value": 16, "sight": 3},  # Czołg średni
    "TC": {"movement": 3, "attack_range": 2, "attack_value": 18, "combat_value": 18, "defense_value": 22, "sight": 3},  # Czołg ciężki
    "TS": {"movement": 5, "attack_range": 1, "attack_value": 8,  "combat_value": 8,  "defense_value": 10, "sight": 4},  # Sam. pancerny
    "AL": {"movement": 3, "attack_range": 3, "attack_value": 12, "combat_value": 6,  "defense_value": 6,  "sight": 4},  # Artyleria lekka
    "AC": {"movement": 2, "attack_range": 4, "attack_value": 18, "combat_value": 8,  "defense_value": 8,  "sight": 5},  # Artyleria ciężka
    "AP": {"movement": 2, "attack_range": 2, "attack_value": 10, "combat_value": 6,  "defense_value": 8,  "sight": 4},  # Artyleria plot
    "Z":  {"movement": 6, "attack_range": 1, "attack_value": 4,  "combat_value": 4,  "defense_value": 6,  "sight": 6},  # Zaopatrzenie
    "D":  {"movement": 4, "attack_range": 1, "attack_value": 6,  "combat_value": 8,  "defense_value": 12, "sight": 5},  # Dowództwo
}
```

### 📈 **Jak działa escalation wzrostu siły:**
- **Czołgi:** TL (10 atak) → TŚ (14 atak) → TC (18 atak)
- **Artyleria:** AL (zasięg 3) → AC (zasięg 4, więcej ataku)
- **Mobilność vs Siła:** Kawaleria (movement 6, atak 6) vs Piechota (movement 3, atak 8)

## ⚙️ **System SIZE_MULTIPLIER - Skalowanie wielkości**

```python
SIZE_MULTIPLIER = {"Pluton": 1.0, "Kompania": 1.4, "Batalion": 1.8}
```

**Przykład:** Piechota Pluton (8 ataku) → Kompania (11 ataku) → Batalion (14 ataku)

## 🔧 **System UPGRADES - Ulepszenia jednostek**

### 🛠️ **8 typów ulepszeń:**
```python
UPGRADES = {
    "drużyna granatników":     {"movement_delta": 0, "range_bonus": 0, "attack_delta": 3, "combat_delta": 2, "defense_delta": 1, "sight_delta": 0, "maintenance_delta": 2, "cost_delta": 12},
    "sekcja ckm":             {"movement_delta": -1, "range_bonus": 1, "attack_delta": 2, "combat_delta": 0, "defense_delta": 2, "sight_delta": 0, "maintenance_delta": 2, "cost_delta": 10},
    "przodek dwukonny":       {"movement_delta": 2, "range_bonus": 0, "attack_delta": 0, "combat_delta": 0, "defense_delta": 0, "sight_delta": 0, "maintenance_delta": 1, "cost_delta": 5},
    "sam. ciezarowy Fiat 621": {"movement_delta": 5, "range_bonus": 0, "attack_delta": 0, "combat_delta": 0, "defense_delta": 0, "sight_delta": 0, "maintenance_delta": 3, "cost_delta": 8},
    "sam.ciezarowy Praga Rv": {"movement_delta": 5, "range_bonus": 0, "attack_delta": 0, "combat_delta": 0, "defense_delta": 0, "sight_delta": 0, "maintenance_delta": 3, "cost_delta": 8},
    "ciagnik altyleryjski":   {"movement_delta": 3, "range_bonus": 0, "attack_delta": 0, "combat_delta": 0, "defense_delta": 0, "sight_delta": 0, "maintenance_delta": 4, "cost_delta": 12},
    "obserwator":            {"movement_delta": 0, "range_bonus": 0, "attack_delta": 0, "combat_delta": 0, "defense_delta": 0, "sight_delta": 2, "maintenance_delta": 1, "cost_delta": 5},
}
```

### 🎯 **Kategorie ulepszeń:**
- **Bojowe:** drużyna granatników (+3 atak), sekcja ckm (+2 atak, +1 zasięg)
- **Transportowe:** Fiat/Praga (+5 movement), ciągnik artylery (+3 movement)
- **Specjalne:** obserwator (+2 sight), przodek dwukonny (+2 movement)

## 🌍 **System DOCTRINES - Bonusy narodowe**

```python
DOCTRINES = {
    "Polska": {"quality_bias": 0.0,  "attack_bonus": 0.00, "defense_bonus": 0.00, "combat_bonus": 0.00},
    "Niemcy": {"quality_bias": 0.02, "attack_bonus": 0.03, "defense_bonus": 0.00, "combat_bonus": 0.02},
}
```

**Niemcy otrzymują:** +3% atak, +2% combat, +2% quality

## 🔄 **Jak system działa:**

### 1. **Algorytm compute_token():**
```python
def compute_token(unit_type, unit_size, nation, upgrades, quality="standard"):
    # 1. Pobierz BASE_STATS[unit_type]
    # 2. Pomnóż przez SIZE_MULTIPLIER[unit_size] 
    # 3. Zastosuj QUALITY_LEVELS[quality]
    # 4. Dodaj wszystkie UPGRADES[upgrade] (delta/bonus)
    # 5. Zastosuj DOCTRINES[nation] bonusy
    # 6. Oblicz koszt: estimate_base_cost() + suma cost_delta
```

### 2. **Kaskadowe zastosowanie modyfikatorów:**
```
BASE → SIZE → QUALITY → UPGRADES → DOCTRINE → FINAL STATS
P(8 atak) → Kompania(11) → elite(12) → granatników(15) → Niemcy(15.45) = 15 ataku
```

## 🛠️ **Jak balansować:**

### 1. **Edytuj BASE_STATS:**
```python
# Wzmocnij piechot
"P": {"movement": 3, "attack_value": 10, "combat_value": 10, ...}  # było 8,8

# Osłab czołgi ciężkie  
"TC": {"movement": 2, "attack_value": 16, "combat_value": 16, ...}  # było 3,18,18
```

### 2. **Dostosuj SIZE_MULTIPLIER:**
```python
# Zwiększ różnicę między wielkościami
SIZE_MULTIPLIER = {"Pluton": 1.0, "Kompania": 1.5, "Batalion": 2.0}
```

### 3. **Zmodyfikuj UPGRADES:**
```python
# Wzmocnij obserwatora
"obserwator": {"sight_delta": 3, "cost_delta": 8}  # było 2, 5

# Nowy upgrade
"pancerz dodatkowy": {"defense_delta": 3, "movement_delta": -1, "cost_delta": 15}
```

### 4. **Balansuj DOCTRINES:**
```python
# Nowa nacja
"ZSRR": {"quality_bias": -0.02, "attack_bonus": 0.00, "defense_bonus": 0.05, "combat_bonus": 0.08}
```

## 📋 **Zalecane wartości dla balansowania:**

### **Movement (punkty ruchu):**
```
1-2 = Bardzo wolne (artyleria ciężka, fortyfikacje)
3-4 = Powolne (piechota, czołgi ciężkie)  
5-6 = Szybkie (czołgi lekkie, kawaleria)
7-8 = Bardzo szybkie (z transportem)
```

### **Attack_value (siła ataku):**
```
4-6  = Słabe (zaopatrzenie, wsparcie)
8-10 = Średnie (piechota, czołgi lekkie)
12-14 = Mocne (czołgi średnie, artyleria)
16-20 = Bardzo mocne (czołgi ciężkie)
```

### **Defense_value (wartość obrony):**
```
6-8  = Słaba (artyleria, zaopatrzenie)
10-12 = Średnia (piechota, czołgi lekkie)
14-18 = Mocna (czołgi średnie)
20-25 = Bardzo mocna (czołgi ciężkie, dowództwo)
```

### **Sight (zasięg widzenia):**
```
2-3 = Krótki zasięg (czołgi ciężkie)
4-5 = Średni zasięg (artyleria, dowództwo)  
6-7 = Długi zasięg (zaopatrzenie, z obserwatorem)
```

## 🔄 **System jest CENTRALNY - aplikuje się automatycznie do:**

### ✅ **Token Shop (gui/token_shop.py)**
- Ceny jednostek z compute_token()
- Statystyki w czasie rzeczywistym
- Podgląd żetonu z finalnymi wartościami

### ✅ **Token Editor (edytory/token_editor_prototyp.py)**  
- Import wszystkich UPGRADES z balance.model
- Kalkulacja statystyk przez compute_token()
- Spójność z systemem sklepu

### ✅ **AI Commander (ai/ai_commander.py)**
- Zakupy jednostek przez compute_token()
- Ocena wartości bojowej uwzględnia finalne statystyki
- Planowanie taktyczne z rzeczywistymi parametrami

### ✅ **Silnik gry (engine/)**
- Token.stats zawiera finalne wartości z balance.model
- Walka uwzględnia combat_value, defense_value
- Ruch konsumuje MP według movement

## 💡 **Wskazówki balansowania:**

### **Dla nowych graczy:**
- Zwiększ BASE_STATS dla podstawowych jednostek (P, K, TL)
- Zmniejsz cost_delta dla podstawowych ulepszeń
- Dodaj gentle DOCTRINE bonusy

### **Dla weteranów:**
- Zwiększ różnice między typami jednostek
- Dodaj specialized ulepszenia z trade-offami
- Skomplikowane DOCTRINES z bonusami/malowadami

### **Dla AI:**
- Balansuj estimate_base_cost() aby AI kupowało różnorodnie
- Upewnij się że wszystkie typy mają sensowne niche
- Test czy AI nie preferuje jednego typu za bardzo

## 💰 **Przykładowe koszty jednostek (aktualne):**

### **Podstawowe jednostki:**
```
Piechota (P):     Pluton: 7 pkt,  Kompania: 12 pkt,  Batalion: 20 pkt
Kawaleria (K):    Pluton: 6 pkt,  Kompania: 10 pkt,  Batalion: 17 pkt
Czołg lekki (TL): Pluton: 11 pkt, Kompania: 20 pkt,  Batalion: 33 pkt
Czołg średni (TŚ): Pluton: 18 pkt, Kompania: 31 pkt, Batalion: 51 pkt
Czołg ciężki (TC): Pluton: 28 pkt, Kompania: 49 pkt, Batalion: 81 pkt
```

### **Wpływ ulepszeń (przykłady):**
```
Piechota Kompania + drużyna granatników:    12 → 22 pkt (+10) [atak 11→13]
Artyleria lekka Kompania + obserwator:      13 → 18 pkt (+5)  [sight +2]
Piechota Pluton + sam. ciężarowy Fiat 621:  7 → 15 pkt (+8)  [ruch 3→8]
```

### **Relacja koszt/efektywność:**
- **Najbardziej opłacalne:** Kawaleria (6 pkt za movement 6)
- **Najdroższe:** Czołgi ciężkie (28-81 pkt)
- **Best bang for buck:** Piechota Pluton (7 pkt za 8 attack, 10 defense)

## 🧪 **Testowanie zmian:**

### 1. **Uruchom Token Shop:**
```
python main.py → New Game → Commander Panel → Token Shop
```

### 2. **Sprawdź Token Editor:**
```
python edytory/token_editor_prototyp.py
```

### 3. **Test w grze AI vs AI:**
```
python main_ai.py
```

## ⚠️ **UWAGI:**

- **Zmiany w balance.model aplikują się NATYCHMIAST** do wszystkich komponentów
- **Backup przed dużymi zmianami** - balance.model jest krytyczny dla całej gry  
- **Test wszystkie typy jednostek** po zmianie BASE_STATS
- **Sprawdź AI zakupy** po zmianie kosztów - AI może przestać kupować pewne typy

---
*System balansowania tokenów jest scentralizowany w balance.model podobnie jak balansowanie heksów w map_data.json*
