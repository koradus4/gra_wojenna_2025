# Gdzie AI Commander wystawia zakupione żetony - Dokumentacja

## 📍 **ODPOWIEDŹ Z DOWODAMI**

AI Commander wystawia zakupione żetony na **predefiniowanych spawn points** dla każdej nacji zgodnie z `data/map_data.json`.

## **Dokładne pozycje deployment:**

### 🇵🇱 **POLSKA** (Commander ID: 2, 3)
**Spawn points w kolejności priorytetów:**
1. `(6, -3)` - **GŁÓWNY spawn point** - Wschodni brzeg
2. `(0, 2)` - Backup #1
3. `(0, 13)` - Backup #2  
4. `(0, 14)` - Backup #3
5. `(0, 21)` - Backup #4
6. `(0, 29)` - Backup #5
7. `(0, 32)` - Backup #6
8. `(6, 30)` - Backup #7
9. `(18, 24)` - Backup #8
10. `(24, -12)` - Backup #9
11. `(25, 20)` - Backup #10

### 🇩🇪 **NIEMCY** (Commander ID: 5, 6) 
**Spawn points w kolejności priorytetów:**
1. `(52, -26)` - **GŁÓWNY spawn point** - Zachodni brzeg
2. `(55, -23)` - Backup #1
3. `(55, -20)` - Backup #2
4. `(55, -17)` - Backup #3
5. `(55, -15)` - Backup #4
6. `(55, -11)` - Backup #5
7. `(55, -5)` - Backup #6
8. `(54, 6)` - Backup #7
9. `(49, 8)` - Backup #8
10. `(41, 12)` - Backup #9
11. `(40, -20)` - Backup #10

## **Algorytm deployment:**

### 1. **Sprawdź spawn points w kolejności**
```python
# ai/ai_commander.py - find_deployment_position()
spawn_points = map_data.get('spawn_points', {}).get(nation, [])

for spawn_str in spawn_points:
    spawn_pos = tuple(map(int, spawn_str.split(',')))
    
    if not board.is_occupied(spawn_pos[0], spawn_pos[1]):
        # UŻYJ tego spawn point
        return spawn_pos
```

### 2. **Jeśli spawn points zajęte - sprawdź sąsiednie pozycje**
```python
# Sprawdź neighbors wokół spawn points
if not best_position:
    for spawn_str in spawn_points:
        spawn_pos = tuple(map(int, spawn_str.split(',')))
        neighbors = board.neighbors(spawn_pos[0], spawn_pos[1])
        
        for neighbor in neighbors:
            if not board.is_occupied(neighbor[0], neighbor[1]):
                # UŻYJ sąsiedniej pozycji
                return neighbor
```

### 3. **System oceny pozycji**
```python
def evaluate_deployment_position(position, my_units, game_engine):
    score = 100  # Bazowy wynik
    
    # Bonus za bliskość do swoich jednostek (+50 jeśli ≤3 hex)
    # Bonus za bliskość do key points (+wartość/10)
    # Malus za bliskość do wrogów
    
    return score
```

## **Dowody z testów:**

### Test deployment pozycji:
```
🇵🇱 TEST DEPLOYMENT POLSKI
SCENARIUSZ 1: Pusta mapa - pierwszy deployment
   Wybrana pozycja: (6, -3)
   Hex coordinates: q=6, r=-3
   Czy to spawn point: True
   Który spawn point: #1 z 11

🇩🇪 TEST DEPLOYMENT NIEMIEC  
SCENARIUSZ: Deployment niemieckich jednostek
   Wybrana pozycja: (52, -26)
   Czy to spawn point: True
   Który spawn point: #1 z 11
```

### Test rzeczywistego deployment:
```
[DEPLOY] Wdrożono nowy_3_PL_K_Pluton na (6, -3)
[DEPLOY] Wdrożono nowy_3_PL_K_Pluton na (0, 2)
[DEPLOY] Wdrożono nowy_5_N_TC_Pluton na (52, -26)
```

## **Strategiczne znaczenie pozycji:**

### Polska spawn points:
- **(6, -3)** - Wschodni brzeg, dobry dostęp do centrum mapy
- **(0, 2), (0, 13), (0, 14)** - Linia północno-wschodnia
- **(24, -12), (25, 20)** - Pozycje południowe

### Niemiecki spawn points:
- **(52, -26)** - Zachodni brzeg, kontrola zachodnich podejść
- **(55, -23) do (55, -5)** - Linia zachodnia
- **(54, 6), (49, 8), (41, 12)** - Pozycje północno-zachodnie

## **Konfiguracja źródłowa:**

Spawn points są zdefiniowane w `data/map_data.json`:
```json
{
  "spawn_points": {
    "Polska": ["6,-3", "0,2", "0,13", "0,14", ...],
    "Niemcy": ["52,-26", "55,-23", "55,-20", "55,-17", ...]
  }
}
```

## **Podsumowanie:**

### ✅ **Gdzie AI Commander stawia jednostki:**
1. **PRIORYTET 1:** Pierwszy wolny spawn point z listy dla nacji
2. **PRIORYTET 2:** Sąsiednie pozycje do spawn points jeśli zajęte
3. **PRIORYTET 3:** Pozycje z najwyższą oceną (bliskość jednostek/key points)

### ✅ **Typowe pozycje:**
- **Polska rozpoczyna:** `(6, -3)` - wschodni brzeg
- **Niemcy rozpoczynają:** `(52, -26)` - zachodni brzeg
- **Backup pozycje:** kolejne spawn points z listy

**System jest deterministyczny i przewidywalny - zawsze wykorzystuje predefiniowane spawn points w ustalonej kolejności.**

---

**Źródło danych:** `data/map_data.json`  
**Test verification:** `tests/ai/test_deployment_positions.py`  
**Status:** ✅ VERIFIED WITH EVIDENCE
