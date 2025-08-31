# 🎯 System Ograniczenia Strzałów Artylerii

## 📝 **Opis systemu:**

**Problem:** Artyleria była zdominowana w grze - wysoki zasięg (3-4 hex), duży atak (12-18), mogła atakować wielokrotnie bez ograniczeń.

**Rozwiązanie:** Artyleria może wystrzeliwać tylko **1 raz na turę** + opcjonalnie **1 strzał reakcyjny**.

## ⚙️ **Mechanika:**

### **Typy ataków:**
- **Normalny atak:** Standardowy atak w swojej turze (1 na turę)
- **Atak reakcyjny:** Odpowiedź na ruch przeciwnika (1 na turę)

### **Jednostki objęte ograniczeniem:**
```
AL - Artyleria lekka     (zasięg 3, atak 12)
AC - Artyleria ciężka    (zasięg 4, atak 18) 
AP - Artyleria plot      (zasięg 2, atak 10)
```

### **Jednostki bez ograniczeń:**
```
P  - Piechota           TL - Czołg lekki     
K  - Kawaleria          TŚ - Czołg średni    
TC - Czołg ciężki       TS - Sam. pancerny   
Z  - Zaopatrzenie       D  - Dowództwo
```

## 🔧 **Implementacja techniczna:**

### **1. Nowe pola w Token (`engine/token.py`):**
```python
# Licznik strzałów w bieżącej turze
self.shots_fired_this_turn = 0

# Czy użyto strzału reakcyjnego
self.reaction_shot_used = False
```

### **2. Nowe metody w Token:**
```python
def can_attack(self, attack_type: str = 'normal') -> bool:
    """Sprawdza czy jednostka może zaatakować"""
    
def record_attack(self, attack_type: str = 'normal'):
    """Zapisz wykonany atak"""
    
def is_artillery(self) -> bool:
    """Sprawdź czy jednostka to artyleria"""
    
def reset_turn_actions(self):
    """Reset akcji na początku nowej tury"""
```

### **3. Walidacja w CombatAction (`engine/action_refactored_clean.py`):**
```python
def _validate_combat(self, engine, attacker, defender):
    # Sprawdź ograniczenia strzałów artylerii
    attack_type = 'reaction' if self.is_reaction else 'normal'
    if not attacker.can_attack(attack_type):
        if attacker.is_artillery():
            if attack_type == 'normal':
                return False, "Artyleria już wystrzeliła w tej turze!"
            else:
                return False, "Artyleria już użyła strzału reakcyjnego!"
```

### **4. Reset na początku tury:**
```python
# W core/tura.py i engine/engine.py
for token in self.game_engine.tokens:
    if hasattr(token, 'reset_turn_actions'):
        token.reset_turn_actions()
```

## 🎮 **Wpływ na rozgrywkę:**

### **Dla gracza:**
- **Decyzyjność:** Musisz wybierać kiedy i co ostrzelać
- **Planowanie:** Artyleria wymaga wsparcia innych jednostek
- **Taktyka:** Priorytetyzacja celów staje się kluczowa

### **Dla AI:**
- **Balans:** AI nie może już spamować artylerii
- **Różnorodność:** Zachęca do kupowania różnych typów jednostek
- **Realizm:** Czas przeładowania artylerii jest realistyczny

## 📊 **Przykłady działania:**

### **Scenariusz 1: Normalny atak**
```
Tura 1: Artyleria lekka atakuje piechote → SUKCES
        Artyleria lekka próbuje zaatakować czołg → ODMOWA
        
Tura 2: Reset - artyleria może znów atakować
```

### **Scenariusz 2: Atak reakcyjny**
```
Niemiecki czołg porusza się w zasięgu polskiej artylerii
→ Artyleria wykonuje atak reakcyjny → SUKCES
→ Artyleria nie może już wykonać ataku reakcyjnego w tej turze
```

### **Scenariusz 3: Kombinacja**
```
Artyleria wykonuje normalny atak → może jeszcze reakcyjny
Artyleria wykonuje reakcyjny → może jeszcze normalny
Po użyciu obu → musi czekać do następnej tury
```

## ✅ **Korzyści systemu:**

1. **Eliminuje arty spam** - koniec z masowym ostrzeliwaniem
2. **Zwiększa tactical depth** - każdy strzał ma wagę
3. **Realistyczne** - salwa artylerii trwa dłużej niż strzał piechoty
4. **Balansuje meta** - artyleria nadal użyteczna, ale nie overpowered
5. **Counter-play** - przeciwnik może planować po pierwszym strzale

## 🧪 **Testy:**

Pełny test w `tests/test_artillery_shot_limits.py` weryfikuje:
- ✅ Ograniczenia dla artylerii (AL, AC, AP)
- ✅ Brak ograniczeń dla innych jednostek  
- ✅ System normalny + reakcyjny
- ✅ Reset na początku tury
- ✅ Integracja z CombatAction
- ✅ Walidacja komunikatów błędów

## 🔄 **Kompatybilność:**

System jest **w pełni wstecznie kompatybilny**:
- Stare save'y działają (nowe pola mają domyślne wartości)
- Jednostki bez `unitType` są traktowane jak nie-artyleria
- Istniejące CombatAction automatycznie respektuje ograniczenia

---

**🎯 Wynik:** Artyleria zachowuje swoją siłę bojową, ale traci możliwość dominacji przez spam ataków. Gra staje się bardziej zbalansowana i taktyczna!
