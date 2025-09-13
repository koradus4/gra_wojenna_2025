# 🎯 AI COMMANDER PIPELINE - Przegląd z Victory AI Integration + AI Configuration System

## -1. **🎛️ AI CONFIGURATION LAYER** ✅ **NOWY - CENTRALNE PARAMETRY**
- **Centralna konfiguracja:** `get_param()` zamiast hardcoded wartości (29 aktywnych wywołań)
- **Profile AI:** AGGRESSIVE (0.7x min_buy), DEFENSIVE (1.3x attack), BALANCED (1.0x all), CUSTOM
- **GUI Integration:** Panel konfiguracji z suwakami + JSON persistence (ai/configs/ai_config.json)
- **Dynamic Parameters:** Commander wykorzystuje `get_param('ECONOMY.MIN_BUY')`, `get_param('COMBAT.MINIMUM_ATTACK_RATIO')` etc.
- **A/B Testing Ready:** Profile można zmieniać bez restart - natychmiastowy effect na AI behavior

## 0. **🧠 VICTORY AI STRATEGIC LAYER** ✅ **NOWE - PHASE 1-3 ACTIVE**
- **Victory AI Phase 1:** Intelligent Scouting + Enemy Detection (72 scout checks per turn)
- **Victory AI Phase 2:** Multi-turn Attack Planning (4-phase system: POSITIONING → CONCENTRATION → ATTACK → EXPLOITATION)  
- **Victory AI Phase 3:** Balanced Defense Allocation (60% defense, 30% attack, 10% reserve + KP security)
- **Integration:** Victory AI recommendations feed into Commander tactical decisions
- **CSV Logging:** victory_operations_{date}.csv tracks all strategic operations

## 1. **INICJALIZACJA TURY**
- Określa gracza AI i tworzy instancję AICommander
- **Odświeża punkty ruchu wszystkich jednostek na maksimum** 🔄
- Inicjalizuje key pointy jeśli nie istnieją
- Ustawia referencję current_player_commander dla dostępu z innych modułów

## 2. **ADAPTACYJNY SYSTEM STRATEGICZNY + VICTORY AI INTEGRATION + AI CONFIGURATION**
- Tworzy AdaptiveAICommander i analizuje stan VP (WINNING/LOSING/TIED)
- **Victory AI Input:** Receives threat assessment and scout intelligence data
- **Configurable Economics:** `get_param('ECONOMY.MIN_BUY')`, `get_param('ECONOMY.ALLOC_RATIO')`, `get_param('LOGISTICS.LOW_FUEL_PERCENT_THRESHOLD')`
- Ustala poziom agresywności (0.3-0.9) i priorytety celów **enhanced by Victory AI recommendations**
- **Profile AI Influence:** AGGRESSIVE profile = 0.7x min_buy, DEFENSIVE = 1.3x attack thresholds
- **Enhanced Reconnaissance:** Victory AI provides 72 scout checks + enemy detection data
- **Multi-turn Planning:** Victory AI attack plans influence strategic decisions

## 3. **ZBIERANIE JEDNOSTEK I GARNIZONÓW + VICTORY AI DEFENSE ALLOCATION**
- Pobiera wszystkie jednostki gracza z tokenów gry
- **Victory AI Phase 3:** Balanced defense allocation (60% defense, 30% attack, 10% reserve)
- **Victory AI KP Security:** Intelligent assignment of KP defenders with prioritization
- Sprawdza które jednostki stoją na key pointach i ustawia garnizony **guided by Victory AI**
- Zarządza rotacją garnizonów dla wyczerpanych punktów
- **🔥 GARRISON SUPPORT SYSTEM** - wyczyść przestarzałe i przydziel nowe wsparcie po odświeżeniu MP
- **Victory AI PE Security:** Ensures PE collection capability is maintained

## 4. **FAZA OPPORTUNISTIC CAPTURE + VICTORY AI SCOUTING**
- **Victory AI Scout Patrol:** Executes intelligent patrol missions (not aimless wandering!)
- **Victory AI Enemy Detection:** Scans visible enemies with fair visibility checking
- Deleguje do `ai.rajdy_ai` błyskawiczne przechwyty **informed by Victory AI intel**
- Zajmuje wolne key pointy w zasięgu ruchu przed główną turą
- Oznacza jednostki jako "moved_capture" aby nie ruszały się ponownie
- **Victory AI Logging:** Records scout missions and enemy contacts in CSV

## 5. **ZAAWANSOWANY TRYB AUTONOMICZNY + VICTORY AI ATTACK PLANNING**
- **Victory AI Multi-turn Plans:** Executes current phase of active attack plans (POSITIONING/CONCENTRATION/ATTACK/EXPLOITATION)
- **Victory AI Force Allocation:** Uses 30% attack allocation from defense/attack/reserve split  
- Priorytetyzuje cele na podstawie wartości vs dystans z bonusami **+ Victory AI target recommendations**
- Grupuje jednostki adaptacyjnie (1-5 grup) według bliskości **coordinated with Victory AI plans**
- Przypisuje cele grupom z koordynacją (bez duplikatów) **following Victory AI strategic guidance**
- **Victory AI Plan Validation:** Continuously validates if plans should continue or abort

## 6. **FAZA WALKI + AI CONFIGURATION**
- Każda jednostka próbuje walczyć z wrogami w zasięgu
- Deleguje do `ai.walka_ai` ocenę stosunku sił i wykonanie ataku **using `get_param('COMBAT.MINIMUM_ATTACK_RATIO')`**
- **Configurable Combat:** `get_param('COMBAT.THREAT_RETREAT_THRESHOLD')`, `get_param('COMBAT.LOW_CV_RESUPPLY_THRESHOLD')`
- Automatyczne uzupełnienie paliwa/CV przed walką
- **Mid-turn resupply** - uzupełnienie jednostek po walkach

## 7. **FAZA DEFENSYWNA**
- Deleguje do `ai.obrona_ai` ocenę zagrożeń dla jednostek
- Planuje kontrolowany odwrót zagrożonych jednostek
- Koordynuje obronę wokół key pointów

## 8. **🎯 UNIFIED DEPLOYMENT SYSTEM**
- Deleguje do `ai.unified_deployment` **NOWY jednolity system dla human i AI**
- **Inteligentne pozycjonowanie:** `smart_deployment.py` + `find_optimal_spawn_position()`
- **Niezawodność human:** `Token.from_json()` + natychmiastowe `game_engine.tokens.append()`
- **Markery deployment:** `.deployed` system zapobiega duplikatom
- Kopiuje pliki do `assets/tokens/aktualne/` identycznie jak system human

## 9. **FAZA RUCHU GŁÓWNEGO**
- Każda grupa wykonuje ruch do przypisanego celu
- Deleguje do `ai.ruch_jednostek` wybór trybu ruchu i pathfinding
- Progressive movement dla dalskich celów + garrison check po ruchu
- **Persistent targets** - jednostki pamiętają swoje cele między turami
- **Adaptacyjne taktyki** - integracja z systemem strategicznym AdaptiveAI

## 10. **SYSTEM ZAOPATRZENIA**
- Deleguje do `ai.zaopatrzenie_ai` tactical resupply w trakcie tury
- Limity 3x LOW_FUEL per token per turę + PE validation
- "Druga szansa" ruchu dla uzupełnionych jednostek
- **Integracja w fazach walki i ruchu** - automatyczne uzupełnienie przed kluczowymi akcjami

## 11. **LOGOWANIE I ZAKOŃCZENIE**
- Zapisuje szczegółowe CSV z akcjami jednostek i podsumowaniem tury
- Eksportuje metryki: combaty, retreaty, deployments, strategic state
- Czyści zmienne tymczasowe i kończy turę

## 12. **🧠 VICTORY AI COORDINATION & NEXT PHASES** 🔄 **DEVELOPMENT**

### **Current Status (Phase 1-5 COMPLETE):**
- ✅ **Strategic Scouting:** 72 scout checks + intelligent patrol zones  
- ✅ **Multi-turn Attack Planning:** 4-phase attack system with validation
- ✅ **Balanced Defense:** 60%/30%/10% force allocation + KP security + PE protection
- ✅ **Advanced Logistics:** Commander-General communication + force requirements analysis
- ✅ **VP Intelligence:** Victory Points optimization + predictive modeling
- ✅ **Full Integration:** Victory AI seamlessly coordinates with existing AI pipeline

### **Victory AI Status Update (September 2025):**
- ✅ **Phase 1-3:** Scouting + Attack Planning + Defense - COMPLETE
- ✅ **Phase 4:** Advanced Logistics AI - COMPLETE (Commander-General Communication + Force Requirements Analysis)
- ✅ **Phase 5:** VP Intelligence System - COMPLETE (vp_intelligence.py + VP Optimization)
- � **Phase 6:** Full Integration - IN PROGRESS (Complete Victory AI System)

---

**Cały system jest modularny z delegacją do 25+ wyspecjalizowanych modułów AI + Victory AI strategic layer.**
