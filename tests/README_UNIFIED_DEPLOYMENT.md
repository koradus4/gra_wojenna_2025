# 🧪 Unified Deployment System - Testy

## 📍 **Lokalizacja testów**

### **Integration Tests** (`tests/integration/`)
- `test_unified_deployment_status.py` - Status tokenów i plików
- `test_unified_deployment_integration.py` - Gotowość systemu do gry

### **AI Tests** (`tests/ai/`)
- `test_unified_deployment.py` - Pełny test z mockami

## 🚀 **Szybki start**

### **1. Status Check (zalecany)**
```bash
python tests/integration/test_unified_deployment_status.py
```
**Co sprawdza:**
- Tokeny AI w folderach `nowe_dla_X/`
- Status markerów `.deployed` 
- Pliki w `aktualne/`

### **2. Integration Test (przed grą)**
```bash
python tests/integration/test_unified_deployment_integration.py
```
**Co sprawdza:**
- Importy unified_deployment
- Integrację z ai_commander
- Spawn points i strukturę plików
- Gotowość do użycia w grze

### **3. Full Test (opcjonalny)**
```bash
python tests/ai/test_unified_deployment.py
```
**Co robi:**
- Test z mockami
- Może mieć problemy kompatybilności
- Użyj tylko do debugowania

## 📊 **Interpretacja wyników**

### **✅ PASS - System gotowy**
```
🎯 GOTOWOŚĆ SYSTEMU UNIFIED DEPLOYMENT:
✅ SYSTEM GOTOWY DO UŻYCIA W GRZE
```
➡️ **Uruchom grę i testuj AI Commander**

### **⏳ GOTOWY - Brak tokenów**
```
⏳ SYSTEM GOTOWY - BRAK TOKENÓW DO TESTÓW
```
➡️ **Uruchom AI General żeby zakupił tokeny**

### **❌ FAIL - Wymaga naprawy**
```
❌ SYSTEM WYMAGA NAPRAWY
```
➡️ **Sprawdź błędy importów/zależności**

## 🔧 **Troubleshooting**

### **Problem: Brak tokenów AI**
```bash
# Rozwiązanie: Uruchom AI General
python main_ai.py
# Pozwól AI General zakupić jednostki
# Sprawdź czy pojawiają się w assets/tokens/nowe_dla_X/
```

### **Problem: Import errors**
```bash
# Sprawdź czy pliki istnieją
ls ai/unified_deployment.py
ls ai/smart_deployment.py
ls engine/token.py

# Test importów
python -c "from ai.unified_deployment import unified_deploy_purchased_units"
```

### **Problem: Mock errors w full test**
```bash
# Użyj integration testów zamiast full test
python tests/integration/test_unified_deployment_integration.py
```

## 📋 **Workflow testowania**

1. **Pre-game:** `test_unified_deployment_integration.py` ✅
2. **In-game:** Uruchom grę, sprawdź logi `[UNIFIED]`
3. **Post-game:** `test_unified_deployment_status.py` (sprawdź markery)

## 🎯 **Expected behavior w grze**

### **Logi oczekiwane:**
```
🎯 [UNIFIED] deploy_purchased_units wywołany dla gracza 2
✅ [UNIFIED_DEPLOY] Wdrożono token: nowy_K_Pluton__2_... na (25, 15)  
🎯 [UNIFIED_DEPLOY] Wdrożono 1 nowych jednostek dla gracza 2
🎯 [UNIFIED] unified_deployment zwrócił: 1
```

### **Pliki po deployment:**
```
assets/tokens/
├── nowe_dla_2/
│   └── nowy_token_folder/
│       ├── token.json
│       ├── token.png  
│       └── .deployed     ← Nowy marker
├── aktualne/
│   ├── nowy_token.png    ← Skopiowane 
│   └── nowy_token.json   ← Skopiowane
```

**Unified Deployment System = Tested & Ready!** ✨
