"""
Test systemu parametryzacji AI Commander
Pokazuje jak działają różne profile i konfiguracja
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(__file__)))

from ai.ai_config import AIConfigManager, AIProfile, get_param, set_ai_profile


def test_parameter_loading():
    """Test ładowania podstawowych parametrów"""
    print("=== TEST: Parameter Loading ===")
    
    config = AIConfigManager()
    
    # Test podstawowych parametrów
    min_buy = config.get_parameter('ECONOMY.MIN_BUY')
    min_allocate = config.get_parameter('ECONOMY.MIN_ALLOCATE')
    
    print(f"✅ MIN_BUY: {min_buy}")
    print(f"✅ MIN_ALLOCATE: {min_allocate}")
    print(f"✅ ALLOC_RATIO: {config.get_parameter('ECONOMY.ALLOC_RATIO')}")
    
    assert min_buy == 30, f"Expected 30, got {min_buy}"
    assert min_allocate == 60, f"Expected 60, got {min_allocate}"


def test_profile_multipliers():
    """Test działania mnożników profili"""
    print("\n=== TEST: Profile Multipliers ===")
    
    config = AIConfigManager()
    
    # Test profilu zbalansowanego (baseline)
    config.set_profile(AIProfile.BALANCED)
    balanced_min_buy = config.get_parameter('ECONOMY.MIN_BUY')
    balanced_vp_weight = config.get_parameter('DEPLOYMENT.DEFAULT_VP_WEIGHT')
    
    print(f"📊 BALANCED:")
    print(f"   MIN_BUY: {balanced_min_buy}")
    print(f"   VP_WEIGHT: {balanced_vp_weight}")
    
    # Test profilu agresywnego
    config.set_profile(AIProfile.AGGRESSIVE)
    aggressive_min_buy = config.get_parameter('ECONOMY.MIN_BUY')
    aggressive_vp_weight = config.get_parameter('DEPLOYMENT.DEFAULT_VP_WEIGHT')
    
    print(f"🔥 AGGRESSIVE:")
    print(f"   MIN_BUY: {aggressive_min_buy} (should be ~21)")
    print(f"   VP_WEIGHT: {aggressive_vp_weight} (should be ~0.75)")
    
    # Test profilu defensywnego
    config.set_profile(AIProfile.DEFENSIVE)
    defensive_min_allocate = config.get_parameter('ECONOMY.MIN_ALLOCATE')
    defensive_econ_weight = config.get_parameter('DEPLOYMENT.DEFAULT_ECON_WEIGHT')
    
    print(f"🛡️  DEFENSIVE:")
    print(f"   MIN_ALLOCATE: {defensive_min_allocate} (should be ~78)")
    print(f"   ECON_WEIGHT: {defensive_econ_weight} (should be ~1.4)")
    
    # Sprawdź czy mnożniki działają
    assert aggressive_min_buy < balanced_min_buy, "Aggressive should have lower MIN_BUY"
    assert aggressive_vp_weight > balanced_vp_weight, "Aggressive should prioritize VP more"
    

def test_convenience_functions():
    """Test funkcji pomocniczych"""
    print("\n=== TEST: Convenience Functions ===")
    
    # Test get_param shortcut
    min_buy = get_param('ECONOMY.MIN_BUY')
    print(f"✅ get_param('ECONOMY.MIN_BUY'): {min_buy}")
    
    # Test profile switching
    set_ai_profile(AIProfile.AGGRESSIVE)
    aggressive_min_buy = get_param('ECONOMY.MIN_BUY')
    
    set_ai_profile(AIProfile.DEFENSIVE)  
    defensive_min_buy = get_param('ECONOMY.MIN_BUY')
    
    print(f"🔄 Profile switching:")
    print(f"   Aggressive MIN_BUY: {aggressive_min_buy}")
    print(f"   Defensive MIN_BUY: {defensive_min_buy}")


def test_budget_strategies():
    """Test strategii budżetowych"""
    print("\n=== TEST: Budget Strategies ===")
    
    strategies = get_param('ECONOMY.BUDGET_STRATEGIES', {})
    
    print("💼 Available budget strategies:")
    for name, ratios in strategies.items():
        total = ratios['reserve'] + ratios['allocate'] + ratios['purchase']
        print(f"   {name}: R={ratios['reserve']:.0%}, A={ratios['allocate']:.0%}, P={ratios['purchase']:.0%} (Total: {total:.0%})")
        
        # Sprawdź czy suma = 100%
        assert abs(total - 1.0) < 0.01, f"Strategy {name} ratios don't sum to 100%: {total}"


def test_combat_parameters():
    """Test parametrów walki"""
    print("\n=== TEST: Combat Parameters ===")
    
    # Test różnych profili
    profiles_results = {}
    
    for profile in [AIProfile.BALANCED, AIProfile.AGGRESSIVE, AIProfile.DEFENSIVE]:
        set_ai_profile(profile)
        
        threat_threshold = get_param('COMBAT.THREAT_RETREAT_THRESHOLD')
        counter_penalty = get_param('COMBAT.COUNTER_ATTACK_MAX_PENALTY')
        
        profiles_results[profile.value] = {
            'threat_threshold': threat_threshold,
            'counter_penalty': counter_penalty
        }
        
        print(f"⚔️  {profile.value.upper()}:")
        print(f"   Threat Retreat Threshold: {threat_threshold}")
        print(f"   Counter Attack Penalty: {counter_penalty}")
    
    # Sprawdź logikę profili
    assert profiles_results['aggressive']['threat_threshold'] > profiles_results['defensive']['threat_threshold'], \
        "Aggressive should have higher retreat threshold"


def demo_ai_behavior_differences():
    """Demonstracja różnic w zachowaniu AI"""
    print("\n=== DEMO: AI Behavior Differences ===")
    
    # Symulacja sytuacji taktycznej
    current_pe = 45
    enemy_threat_level = 4
    vp_target_value = 60
    econ_target_value = 40
    
    print(f"📋 Situation: PE={current_pe}, Threat={enemy_threat_level}")
    print(f"   VP Target Value: {vp_target_value}, Econ Target Value: {econ_target_value}")
    
    for profile in [AIProfile.BALANCED, AIProfile.AGGRESSIVE, AIProfile.DEFENSIVE]:
        set_ai_profile(profile)
        
        # Ekonomiczne decyzje
        min_buy = get_param('ECONOMY.MIN_BUY')
        can_buy = current_pe >= min_buy
        
        # Wybór celu  
        vp_weight = get_param('DEPLOYMENT.DEFAULT_VP_WEIGHT')
        econ_weight = get_param('DEPLOYMENT.DEFAULT_ECON_WEIGHT') 
        
        vp_score = vp_target_value * vp_weight
        econ_score = econ_target_value * econ_weight
        
        prefers_vp = vp_score > econ_score
        
        # Decyzja o odwrocie
        threat_threshold = get_param('COMBAT.THREAT_RETREAT_THRESHOLD')
        should_retreat = enemy_threat_level >= threat_threshold
        
        print(f"\n🎯 {profile.value.upper()} AI:")
        print(f"   Economic Action: {'BUY' if can_buy else 'HOLD'} (threshold: {min_buy})")
        print(f"   Target Priority: {'VP' if prefers_vp else 'ECONOMY'} (VP:{vp_score:.1f} vs Econ:{econ_score:.1f})")
        print(f"   Combat Decision: {'RETREAT' if should_retreat else 'FIGHT'} (threshold: {threat_threshold})")


def run_all_tests():
    """Uruchamia wszystkie testy"""
    print("🧪 AI Configuration System - Test Suite")
    print("=" * 50)
    
    try:
        test_parameter_loading()
        test_profile_multipliers()  
        test_convenience_functions()
        test_budget_strategies()
        test_combat_parameters()
        demo_ai_behavior_differences()
        
        print("\n" + "=" * 50)
        print("✅ ALL TESTS PASSED!")
        print("🎯 AI parametrization system works correctly!")
        
    except Exception as e:
        print(f"\n❌ TEST FAILED: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    run_all_tests()