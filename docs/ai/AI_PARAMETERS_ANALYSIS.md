# Analiza Parametrów AI Commander - Kompletny Wykaz

## 🎯 Cel: Centralizacja i Parametryzacja AI

**Problem:** Obecnie parametry AI są rozproszone po 25+ modułach
**Rozwiązanie:** Jeden centralny moduł konfiguracji z profileami AI

---

## 📊 KATEGORIE PARAMETRÓW

### 1. EKONOMIA & BUDŻET
```python
# ai_general.py
MIN_BUY = 30                    # Minimum PE do rozpoczęcia zakupów
MIN_ALLOCATE = 60               # Minimum PE do alokacji dowódcom  
ALLOC_RATIO = 0.6               # Procent PE przekazywany dowódcom
UNSPENT_CAP = 80                # Kara za niewydane PE

# Strategie budżetowe (% podziału PE)
BUDGET_STRATEGIES = {
    'ROZWÓJ':      {'reserve': 0.20, 'allocate': 0.40, 'purchase': 0.40},
    'KRYZYS_PALIWA': {'reserve': 0.15, 'allocate': 0.50, 'purchase': 0.35},
    'DESPERACJA':  {'reserve': 0.10, 'allocate': 0.25, 'purchase': 0.65},
    'OCHRONA':     {'reserve': 0.30, 'allocate': 0.55, 'purchase': 0.15},
    'EKSPANSJA':   {'reserve': 0.20, 'allocate': 0.35, 'purchase': 0.45}
}

# Współczynniki dynamicznego kosztu (anty-spam)
DYNAMIC_COST_FACTORS = {
    "AL": 0.20, "AC": 0.25, "AP": 0.20, "TC": 0.25
}
```

### 2. PALIWO & LOGISTYKA  
```python
# ai_general.py
LOW_FUEL_PERCENT_THRESHOLD = 30      # % paliwa = "niski poziom"
LOW_FUEL_UNITS_RATIO_TRIGGER = 0.30  # 30% jednostek = tryb regeneracji
MAX_UNITS_PER_TURN = 2               # Podstawowy limit zakupów

# Progi resupply kontekstowego
RESUPPLY_RATIOS = {
    'SPOKÓJ':  0.5,  # Przewaga + dobre paliwo + brak zagrożeń
    'WOJNA':   0.8,  # Równowaga sił
    'KRYZYS':  0.9   # Słaba pozycja + zagrożenia
}

# Warunki kontekstowe
PEACE_CONDITIONS = {
    'min_force_ratio': 1.5,
    'max_threats': 0,
    'min_fuel_level': 0.7
}

CRISIS_CONDITIONS = {
    'max_force_ratio': 0.8,
    'min_threats': 2,
    'max_fuel_level': 0.4
}
```

### 3. WALKA & COMBAT
```python
# walka_ai.py 
# evaluate_combat_ratio()
COUNTER_ATTACK_MAX_PENALTY = 0.6     # Maksymalna kara za kontratak
COUNTER_ATTACK_BASE_PENALTY = 0.25   # Bazowa kara za kontratak

# victory_ai.py assess_overall_threat_level()
PROXIMITY_THREAT_RANGE = 5           # Zasięg oceny zagrożenia
PROXIMITY_MIN_FACTOR = 0.1           # Minimalny współczynnik bliskości
THREAT_NORMALIZATION = 100           # Normalizacja siły zagrożenia
MAX_UNIT_THREAT_LEVEL = 1.0          # Maksymalny poziom zagrożenia jednostki
```

### 4. STRATEGIA & VP
```python
# strategia_ai.py
VP_WINNING_THRESHOLD = 10            # Różnica VP = "wygrana"
VP_LOSING_THRESHOLD = -10            # Różnica VP = "przegrana"

# Mnożniki priorytetów strategicznych
STRATEGY_MULTIPLIERS = {
    'LOSING': {
        'victory_points': 2.0,
        'economy': 1.2
    },
    'WINNING': {
        'economy': 1.5, 
        'victory_points': 0.8
    },
    'TIED': {
        'economy': 1.3,
        'victory_points': 1.0
    }
}

# Bonus odległości
DISTANCE_ACCESSIBILITY_THRESHOLD = 10
ACCESSIBILITY_BONUS = 0.3
```

### 5. DEPLOYMENT & POZYCJONOWANIE
```python
# konfiguracja_ai.py
FREE_KEYPOINT_VALUE_DISTANCE_FACTOR = 1.2
FREE_HIGH_VALUE_BONUS_MULTIPLIER = 2.5     # Bonus dla value >100
FREE_MED_VALUE_BONUS_MULTIPLIER = 1.6      # Bonus dla value 50-100

# wybor_celow.py
DEFAULT_ECON_WEIGHT = 1.0            # Waga punktów ekonomicznych
DEFAULT_VP_WEIGHT = 0.5              # Waga punktów VP
MIXED_WEIGHT_SPLIT = 0.5             # Podział dla mieszanych punktów

# Progi wartości punktów (apply_free_point_bonus)  
HIGH_VALUE_THRESHOLD = 100           # "Wysoka wartość"
MEDIUM_VALUE_THRESHOLD = 50          # "Średnia wartość"
```

### 6. RUCH & MOBILNOŚĆ
```python
# ruch_postepowy_ai.py (calculate_progressive_target)
PROGRESSIVE_STEP_LIMIT = 100         # Maksymalna liczba kroków
RESOURCE_MOVEMENT_THRESHOLD = 1      # Minimum MP+fuel dla ruchu

# okupacja_punktow.py  
GARRISON_LIMITS = {
    'default': 2,           # Domyślny limit garnizonu
    'high_value': 3,        # Dla punktów wysokiej wartości  
    'strategic': 4          # Dla punktów strategicznych
}

EARLY_ROTATION_THRESHOLD_RATIO = 0.25  # Próg rotacji garnizonu
```

### 7. OBRONA & ZAGROŻENIA
```python
# Dokumentacja wskazuje na:
THREAT_RETREAT_THRESHOLD = 5         # Poziom zagrożenia = odwrót
THREAT_RANGE = 6                     # Zasięg skanowania wrogów (hex)
KEYPOINT_DEFENSE_RANGE = 2           # Zasięg obrony punktu

# zaopatrzenie_ai.py assess_supply_threat()  
SIGHT_RANGE_DEFAULT = 1              # Domyślny zasięg wzroku
THREAT_DETECTION_BONUS = 1           # Bonus zasięgu detekcji zagrożeń
```

### 8. GRUPOWANIE & KOORDYNACJA
```python
# Dokumentacja API:
MIN_GROUP_SIZE = 3                   # Minimalny rozmiar grupy
MAX_GROUP_SIZE = 5                   # Maksymalny rozmiar grupy  
MAX_GROUP_DISTANCE = 8               # Maksymalny dystans w grupie
MAX_RETREAT_RANGE = 4                # Maksymalny zasięg odwrotu

PROGRESSIVE_MOVE_ENABLED = True      # Włącz ruch progresywny
```

### 9. ZAKUPY & JEDNOSTKI
```python
# ai_general.py _plan_purchases_internal()
MAX_PURCHASE_ATTEMPTS = 300          # Maksymalne próby zakupu
MIN_PURCHASE_COST = 15               # Minimalny koszt jednostki

# Grupy anty-spam
ANTI_SPAM_GROUPS = {
    "artillery": {
        "types": {"AL", "AC", "AP"}, 
        "base_allow": 2, 
        "max_ratio": 0.45
    },
    "heavy_armor": {
        "types": {"TC"}, 
        "base_allow": 1, 
        "max_ratio": 0.30
    }
}

# Heurystyki wyboru jednostek
FORCE_RATIO_THRESHOLDS = {
    'DEFENSIVE': 0.7,        # Poniżej = tryb obronny
    'DOMINANCE': 1.5,        # Powyżej = tryb dominacji
    'CASUALTIES_THRESHOLD': 3, # Próg strat wymagający odbudowy
    'MIN_ARMY_SIZE': 8       # Minimalna wielkość armii
}
```

---

## 🎛️ PROPOZYCJA STRUKTURY KONFIGURACJI

### Profile AI Commander
```python
AI_PROFILES = {
    'AGGRESSIVE': {
        'name': 'Agresywny',
        'description': 'Maksymalne tempo ataku, wysokie ryzyko',
        'multipliers': {
            'attack_priority': 1.5,
            'defense_priority': 0.7, 
            'economy_focus': 0.8,
            'vp_focus': 1.3
        }
    },
    'DEFENSIVE': {
        'name': 'Defensywny', 
        'description': 'Ochrona pozycji, niska tolerancja ryzyka',
        'multipliers': {
            'attack_priority': 0.6,
            'defense_priority': 1.4,
            'economy_focus': 1.2,
            'vp_focus': 0.9
        }
    },
    'BALANCED': {
        'name': 'Zbalansowany',
        'description': 'Uniwersalny profil, adaptacyjny',
        'multipliers': {
            'attack_priority': 1.0,
            'defense_priority': 1.0,
            'economy_focus': 1.0, 
            'vp_focus': 1.0
        }
    }
}
```

### Kategoryzacja Parametrów
```python
PARAMETER_CATEGORIES = {
    'ECONOMY': ['MIN_BUY', 'MIN_ALLOCATE', 'ALLOC_RATIO', 'BUDGET_STRATEGIES'],
    'COMBAT': ['COUNTER_ATTACK_PENALTIES', 'THREAT_LEVELS', 'FORCE_RATIOS'], 
    'LOGISTICS': ['FUEL_THRESHOLDS', 'RESUPPLY_RATIOS', 'SUPPLY_PRIORITIES'],
    'STRATEGY': ['VP_THRESHOLDS', 'STRATEGY_MULTIPLIERS', 'PRIORITY_WEIGHTS'],
    'MOVEMENT': ['GROUP_LIMITS', 'DISTANCE_FACTORS', 'MOBILITY_THRESHOLDS'],
    'DEPLOYMENT': ['GARRISON_LIMITS', 'POSITION_BONUSES', 'VALUE_MULTIPLIERS']
}
```

---

## ✅ ZALETY PARAMETRYZACJI

1. **Łatwe tunowanie:** Zmiana zachowania bez zmiany kodu
2. **A/B Testing:** Porównanie różnych strategii
3. **Profile AI:** Agresywny vs Defensywny vs Balanced  
4. **Debugging:** Szybka identyfikacja problemowych parametrów
5. **Balans gry:** Centralne dostrajanie trudności
6. **Moddability:** Gracze mogą tworzyć własne profile AI

## 🚀 NASTĘPNE KROKI

1. **Analiza:** ✅ Kompletny wykaz parametrów (GOTOWE)
2. **Kategoryzacja:** Pogrupowanie według funkcji
3. **Projekt API:** Struktura centralnego modułu konfiguracji  
4. **Implementacja:** Kod loadowania/zapisywania profili
5. **Refaktor:** Zamiana hardcoded wartości na wywołania API
6. **Testy:** Walidacja różnych profili AI

---

**Podsumowanie:** Znaleziono **80+ parametrów** w **15+ modułach**. 
Parametryzacja to doskonały pomysł dla tuningu AI! 🎯