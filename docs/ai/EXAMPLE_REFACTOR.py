"""
Przykład refaktoryzacji ai_general.py - użycie centralnej konfiguracji AI

PRZED: Hardcoded wartości w każdym module
PO: Centralna konfiguracja z profilami AI
"""

# === PRZED: Hardcoded Constants ===
# MIN_BUY = 30
# MIN_ALLOCATE = 60  
# ALLOC_RATIO = 0.6
# LOW_FUEL_PERCENT_THRESHOLD = 30
# LOW_FUEL_UNITS_RATIO_TRIGGER = 0.30

# === PO: Użycie Centralnej Konfiguracji ===
from ai.ai_config import get_param

class AIGeneral:
    def __init__(self, player):
        self.player = player
        # ... reszta kodu ...
    
    def analyze_units(self, game_engine, player):
        """Analizuje stan jednostek - ZREFAKTOROWANE do użycia konfiguracji"""
        print("\\n🪖 === ANALIZA JEDNOSTEK ===")

        try:
            my_units = game_engine.get_visible_tokens(player)
        except Exception:
            my_units = []

        if not my_units:
            print("❌ Brak jednostek do analizy")
            self._reset_unit_metrics()
            return

        # === UŻYCIE PARAMETRÓW Z KONFIGURACJI ===
        low_fuel_threshold = get_param('LOGISTICS.LOW_FUEL_PERCENT_THRESHOLD', 30)
        
        print(f"📊 Liczba jednostek: {len(my_units)}")
        print(f"⚙️  Próg niskiego paliwa: {low_fuel_threshold}%")

        low_fuel_units = []
        low_combat_units = []
        
        for unit in my_units:
            # Analiza paliwa z konfigurownym progiem
            fuel_percent = self._calculate_fuel_percentage(unit)
            
            if fuel_percent < low_fuel_threshold:  # ← KONFIGUROWALNY PRÓG
                low_fuel_units.append(unit)
                
            # Analiza combat value
            combat_value = getattr(unit, 'combat_value', 0)
            if combat_value < 3:
                low_combat_units.append(unit)

        # Obliczenie ratio z konfigurownym triggerem
        low_fuel_ratio = len(low_fuel_units) / len(my_units) if my_units else 0.0
        trigger_ratio = get_param('LOGISTICS.LOW_FUEL_UNITS_RATIO_TRIGGER', 0.30)
        
        print(f"⛽ Low fuel ratio: {low_fuel_ratio:.2f} (trigger: {trigger_ratio:.2f})")
        
        # Decyzja o trybie na podstawie konfiguracji
        self._phase = 'REGEN' if low_fuel_ratio >= trigger_ratio else 'BUILD'
        
        return {
            'low_fuel_ratio': low_fuel_ratio,
            'phase': self._phase,
            'total_units': len(my_units)
        }

    def decide_economic_action(self, current_player, game_engine, unit_analysis):
        """Podejmuje decyzje ekonomiczne - ZREFAKTOROWANE"""
        
        econ_points = current_player.economy.get_points().get('economic_points', 0)
        
        # === KONFIGUROWALNY PROGI BUDŻETU ===
        min_buy = get_param('ECONOMY.MIN_BUY', 30)
        min_allocate = get_param('ECONOMY.MIN_ALLOCATE', 60) 
        alloc_ratio = get_param('ECONOMY.ALLOC_RATIO', 0.6)
        
        print(f"💰 PE: {econ_points}, MIN_BUY: {min_buy}, MIN_ALLOCATE: {min_allocate}")
        
        # Logika decyzyjna z konfigurowalnymi progami
        if econ_points < min_buy:
            return EconAction.HOLD, f"Za mało punktów ({econ_points} < {min_buy})"
            
        elif econ_points >= min_allocate:
            commanders = self._get_commanders(game_engine)
            if len(commanders) > 0:
                allocation = int(econ_points * alloc_ratio)  # ← KONFIGUROWALNA RATIO
                return EconAction.ALLOCATE, f"Alokacja {allocation} PE do {len(commanders)} dowódców"
        
        return EconAction.BUY, f"Zakupy za {econ_points} PE"

    def get_budget_strategy(self, state_analysis):
        """Zwraca strategię budżetową - ZREFAKTOROWANE"""
        
        # Pobierz strategie z konfiguracji
        strategies = get_param('ECONOMY.BUDGET_STRATEGIES', {})
        
        # Logika wyboru strategii (bez zmian)
        low_fuel_ratio = state_analysis.get('low_fuel_ratio', 0.0)
        force_ratio = state_analysis.get('force_ratio', 1.0)
        
        if low_fuel_ratio >= get_param('LOGISTICS.LOW_FUEL_UNITS_RATIO_TRIGGER', 0.30):
            strategy_name = 'KRYZYS_PALIWA'
        elif force_ratio < 0.7:
            strategy_name = 'DESPERACJA' 
        elif force_ratio > 1.5:
            strategy_name = 'EKSPANSJA'
        else:
            strategy_name = 'ROZWÓJ'
            
        selected_strategy = strategies.get(strategy_name, strategies.get('ROZWÓJ', {
            'reserve': 0.20, 'allocate': 0.40, 'purchase': 0.40
        }))
        
        print(f"💼 Strategia budżetowa: {strategy_name}")
        print(f"   Reserve: {selected_strategy['reserve']:.0%}")
        print(f"   Allocate: {selected_strategy['allocate']:.0%}")  
        print(f"   Purchase: {selected_strategy['purchase']:.0%}")
        
        return selected_strategy

# === PRZYKŁAD UŻYCIA W INNYCH MODUŁACH ===

# combat_ai.py - PRZED
# THREAT_RETREAT_THRESHOLD = 5

# combat_ai.py - PO
def should_retreat(threat_level):
    threshold = get_param('COMBAT.THREAT_RETREAT_THRESHOLD', 5)
    return threat_level >= threshold

# deployment_ai.py - PRZED  
# DEFAULT_VP_WEIGHT = 0.5

# deployment_ai.py - PO
def calculate_target_score(vp_value, econ_value):
    vp_weight = get_param('DEPLOYMENT.DEFAULT_VP_WEIGHT', 0.5)
    econ_weight = get_param('DEPLOYMENT.DEFAULT_ECON_WEIGHT', 1.0)
    
    return vp_value * vp_weight + econ_value * econ_weight

# === WYKORZYSTANIE PROFILI ===
from ai.ai_config import set_ai_profile, AIProfile, get_ai_profile_info

def switch_to_aggressive_ai():
    """Przełącza AI na tryb agresywny"""
    set_ai_profile(AIProfile.AGGRESSIVE)
    info = get_ai_profile_info()
    print(f"🔥 Switched to: {info['name']} - {info['description']}")
    
    # Teraz wszystkie parametry używają mnożników profilu agresywnego:
    # MIN_BUY = 30 * 0.7 = 21
    # VP_WEIGHT = 0.5 * 1.5 = 0.75  
    # THREAT_THRESHOLD = 5 * 1.4 = 7

def switch_to_defensive_ai():  
    """Przełącza AI na tryb defensywny"""
    set_ai_profile(AIProfile.DEFENSIVE)
    info = get_ai_profile_info()
    print(f"🛡️  Switched to: {info['name']} - {info['description']}")
    
    # Teraz wszystkie parametry używają mnożników profilu defensywnego


# === DEMO UŻYCIA ===
if __name__ == "__main__":
    from ai.ai_config import get_ai_config
    
    config = get_ai_config()
    
    print("=== DEMO: AI Configuration System ===")
    
    # Test różnych profili
    for profile in [AIProfile.BALANCED, AIProfile.AGGRESSIVE, AIProfile.DEFENSIVE]:
        config.set_profile(profile)
        info = config.get_profile_info()
        
        print(f"\\n📋 Profile: {info['name']}")
        print(f"   MIN_BUY: {get_param('ECONOMY.MIN_BUY')}")
        print(f"   VP_WEIGHT: {get_param('DEPLOYMENT.DEFAULT_VP_WEIGHT')}")
        print(f"   THREAT_THRESHOLD: {get_param('COMBAT.THREAT_RETREAT_THRESHOLD')}")
    
    print("\\n✅ All parameters configurable via AI profiles!")