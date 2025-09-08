# 🛡️ VICTORY AI PHASE 3 - IMPLEMENTATION PLAN

## **STATUS: ✅ ZAIMPLEMENTOWANE (8 września 2025)**

## **OVERVIEW**
Phase 3 integruje istniejące systemy defensywne z Victory AI dla strategicznej alokacji obrony i bezpieczeństwa PE collection.

**Implementation Complete:** Wszystkie funkcje zostały zaimplementowane w `ai/victory_ai.py` i przeszły testy integracyjne.

---

## **FUNKCJE DO IMPLEMENTACJI**

### **3.1 `calculate_defense_allocation(total_forces, active_attack_plans, game_engine) -> Dict`**

**Cel:** Określ ile sił zostaje przy obronie KP vs. ide na atak

**Input:**
- `total_forces`: Lista wszystkich dostępnych jednostek
- `active_attack_plans`: Plany ataku z Phase 2
- `game_engine`: Dostęp do game state

**Output:**
```python
{
    'defensive_units': List[Dict],  # jednostki do obrony
    'attack_units': List[Dict],     # jednostki do ataku
    'reserve_units': List[Dict],    # rezerwa
    'allocation_ratios': {
        'defense_percent': float,
        'attack_percent': float,
        'reserve_percent': float
    }
}
```

**Logika:**
1. Bazowa alokacja: 60% obrona, 30% atak, 10% rezerwa
2. Modyfikatory:
   - Wysoki threat_level → więcej obrony
   - Aktywne attack plany → więcej ataku
   - PE collection endangered → priorytet obrona

### **3.2 `assign_kp_defenders(available_defenders, key_points, threat_level, game_engine) -> Dict`**

**Cel:** Przypisz konkretne jednostki do obrony konkretnych KP

**Input:**
- `available_defenders`: Jednostki do obrony
- `key_points`: Lista KP do ochrony
- `threat_level`: Ogólny poziom zagrożenia
- `game_engine`: Game state access

**Output:**
```python
{
    'kp_assignments': {
        (hex_q, hex_r): {
            'defenders': List[Dict],
            'support_units': List[Dict],
            'priority_level': int
        }
    },
    'unassigned_defenders': List[Dict]
}
```

**Logika:**
1. Priorytetyzuj KP według wartości PE + strategic value
2. Przydziel defenders według calculate_garrison_support()
3. Wykorzystaj istniejące wsparcie_garnizonu.py
4. Integracja z defensive_coordination()

### **3.3 `maintain_pe_collection_capability(defense_plan, game_engine) -> bool`**

**Cel:** Upewnij się że PE collection nie jest zagrożone

**Input:**
- `defense_plan`: Plan obrony z assign_kp_defenders()
- `game_engine`: Game state

**Output:**
- `True`: PE collection bezpieczne
- `False`: Konieczna realoakacja obrony

**Logika:**
1. Sprawdź wszystkie PE-generating KP
2. Verify coverage przez Zaopatrzenie (Z) units
3. Check threat level dla każdego PE point
4. Alert jeśli critical PE points nie są chronione

### **3.4 `victory_ai_phase3_controller(player_id, game_engine) -> Dict`**

**Main controller** dla Phase 3:

```python
def victory_ai_phase3_controller(player_id, game_engine):
    # 1. Pobierz force allocation
    total_forces = get_my_units(player_id, game_engine)
    active_plans = get_active_attack_plans(player_id)
    
    allocation = calculate_defense_allocation(total_forces, active_plans, game_engine)
    
    # 2. Assign defenders
    key_points = get_strategic_key_points(game_engine)
    threat_level = assess_overall_threat(player_id, game_engine)
    
    kp_defense = assign_kp_defenders(
        allocation['defensive_units'], 
        key_points, 
        threat_level, 
        game_engine
    )
    
    # 3. Validate PE security
    pe_secure = maintain_pe_collection_capability(kp_defense, game_engine)
    
    # 4. Integration with existing systems
    integrate_with_garrison_support(kp_defense, game_engine)
    
    return {
        'allocation': allocation,
        'kp_assignments': kp_defense,
        'pe_secure': pe_secure,
        'recommendations': generate_defense_recommendations()
    }
```

---

## **INTEGRATION POINTS**

### **Istniejące systemy do wykorzystania:**
1. **`wsparcie_garnizonu.py`** - assign_garrison_support(), calculate_garrison_support()
2. **`obrona_ai.py`** - assess_defensive_threats(), defensive_coordination()
3. **`ai_commander.py`** - defensive phase integration

### **Nowe CSV logging:**
- `victory_ai_phase3_YYYYMMDD.csv` - defense allocation decisions
- Kolumny: timestamp, player_id, action, allocation_ratios, kp_assignments, pe_status

### **Phase 1+2 Integration:**
- Phase 1 scouts dostarczają threat intel
- Phase 2 attack plans wpływają na defense allocation
- Phase 3 defense zabezpiecza PE collection

---

## **IMPLEMENTATION SEQUENCE**

### **Step 1:** `calculate_defense_allocation()` (2h)
- Basic force splitting algorithm
- Integration with existing unit data
- Unit tests

### **Step 2:** `assign_kp_defenders()` (3h)
- KP prioritization logic
- Integration z wsparcie_garnizonu.py
- Defender assignment algorithm

### **Step 3:** `maintain_pe_collection_capability()` (2h)
- PE point security validation
- Threat assessment for PE units
- Security alerts

### **Step 4:** `victory_ai_phase3_controller()` (2h)
- Main controller implementation
- CSV logging setup
- Integration with ai_commander.py

### **Step 5:** Testing & Integration (2h)
- Unit tests for all functions
- Integration test with Phase 1+2
- Real gameplay test

**Total Estimated Time:** ~11 hours

---

## **SUCCESS CRITERIA**

1. ✅ Defense allocation based on strategic priorities
2. ✅ KP security maintained without over-allocation
3. ✅ PE collection capability preserved
4. ✅ Integration with existing defensive systems
5. ✅ CSV logging for analysis
6. ✅ Real gameplay validation

**Next after Phase 3:** Phase 4 - Victory conditions monitoring
