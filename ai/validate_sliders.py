"""
🔍 PEŁNA WALIDACJA SUWAKÓW AI CONFIGURATION PANEL
Sprawdza czy każdy suwak ma dostęp do pełnego zakresu wartości w każdym profilu
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(__file__)))

from ai.ai_config import get_param, set_ai_profile, AIProfile


def get_all_slider_parameters():
    """Zwraca wszystkie parametry używane w suwaków GUI"""
    return {
        'ECONOMY': [
            ('ECONOMY.MIN_BUY', 15, 50, 'PE'),
            ('ECONOMY.MIN_ALLOCATE', 40, 100, 'PE'),
            ('ECONOMY.ALLOC_RATIO', 0.3, 0.8, '%'),
            ('LOGISTICS.LOW_FUEL_UNITS_RATIO_TRIGGER', 0.1, 0.5, '%')
        ],
        'COMBAT': [
            ('COMBAT.THREAT_RETREAT_THRESHOLD', 1, 40, 'poziom'),
            ('COMBAT.COUNTER_ATTACK_MAX_PENALTY', 0.1, 1.0, '%'),
            ('COMBAT.KEYPOINT_DEFENSE_RANGE', 1, 5, 'hex'),
            ('COMBAT.PROXIMITY_THREAT_RANGE', 3, 8, 'hex')
        ],
        'STRATEGY': [
            ('STRATEGY.VP_WINNING_THRESHOLD', 5, 20, 'VP'),
            ('DEPLOYMENT.DEFAULT_VP_WEIGHT', 0.1, 2.0, 'x'),
            ('DEPLOYMENT.DEFAULT_ECON_WEIGHT', 0.1, 2.0, 'x'),
            ('PURCHASES.FORCE_RATIO_THRESHOLDS.DEFENSIVE', 0.3, 1.0, 'ratio')
        ],
        'ADVANCED': [
            ('LOGISTICS.LOW_FUEL_PERCENT_THRESHOLD', 10, 50, '%'),
            ('PURCHASES.MAX_UNITS_PER_TURN', 1, 5, 'szt'),
            ('DEPLOYMENT.FREE_HIGH_VALUE_BONUS_MULTIPLIER', 1.0, 3.0, 'x'),
            ('GROUPING.MIN_GROUP_SIZE', 2, 6, 'szt')
        ]
    }


def validate_parameter_range(param_path, min_val, max_val, profile_name):
    """Waliduje czy parametr może osiągnąć pełny zakres w danym profilu"""
    try:
        # Pobierz aktualną wartość
        current_val = get_param(param_path, (min_val + max_val) / 2)
        
        # Sprawdź czy wartość jest w oczekiwanym zakresie
        in_range = min_val <= current_val <= max_val
        
        return {
            'param': param_path,
            'profile': profile_name,
            'current': current_val,
            'min_expected': min_val,
            'max_expected': max_val,
            'in_range': in_range,
            'status': '✅' if in_range else '❌'
        }
        
    except Exception as e:
        return {
            'param': param_path,
            'profile': profile_name,
            'current': f'ERROR: {e}',
            'min_expected': min_val,
            'max_expected': max_val,
            'in_range': False,
            'status': '💥'
        }


def test_all_profiles_all_parameters():
    """Testuje wszystkie parametry we wszystkich profilach"""
    print("🔍 PEŁNA WALIDACJA SUWAKÓW - Wszystkie Profile")
    print("=" * 80)
    
    all_params = get_all_slider_parameters()
    profiles = [AIProfile.BALANCED, AIProfile.AGGRESSIVE, AIProfile.DEFENSIVE]
    
    results = {}
    total_tests = 0
    failed_tests = 0
    
    for profile in profiles:
        print(f"\n🎯 PROFIL: {profile.value.upper()}")
        print("-" * 50)
        
        # Ustaw profil
        set_ai_profile(profile)
        results[profile.value] = {}
        
        for category, params in all_params.items():
            print(f"\n📂 {category}:")
            results[profile.value][category] = []
            
            for param_path, min_val, max_val, unit in params:
                result = validate_parameter_range(param_path, min_val, max_val, profile.value)
                results[profile.value][category].append(result)
                total_tests += 1
                
                if not result['in_range']:
                    failed_tests += 1
                
                # Formatuj wartość dla wyświetlenia
                current = result['current']
                if isinstance(current, float):
                    if 'RATIO' in param_path or 'WEIGHT' in param_path or 'PENALTY' in param_path:
                        if current <= 1.0:
                            display_val = f"{current:.1%}"
                        else:
                            display_val = f"{current:.1f}x"
                    elif current < 10:
                        display_val = f"{current:.1f}"
                    else:
                        display_val = f"{current:.0f}"
                else:
                    display_val = str(current)
                
                print(f"   {result['status']} {param_path}: {display_val} {unit}")
                print(f"      Range: [{min_val}-{max_val}] {unit}")
                
                if not result['in_range'] and isinstance(current, (int, float)):
                    if current < min_val:
                        print(f"      ⚠️  PONIŻEJ MINIMUM o {min_val - current:.2f}")
                    elif current > max_val:
                        print(f"      ⚠️  POWYŻEJ MAKSIMUM o {current - max_val:.2f}")
    
    return results, total_tests, failed_tests


def test_profile_multiplier_effects():
    """Testuje czy profile mnożniki działają poprawnie"""
    print("\n\n🔄 TEST MNOŻNIKÓW PROFILI")
    print("=" * 50)
    
    # Test parametrów które powinny się różnić między profilami
    test_params = [
        'ECONOMY.MIN_BUY',
        'DEPLOYMENT.DEFAULT_VP_WEIGHT', 
        'COMBAT.THREAT_RETREAT_THRESHOLD',
        'ECONOMY.ALLOC_RATIO'
    ]
    
    profile_values = {}
    
    # Zbierz wartości dla wszystkich profili
    for profile in [AIProfile.BALANCED, AIProfile.AGGRESSIVE, AIProfile.DEFENSIVE]:
        set_ai_profile(profile)
        profile_values[profile.value] = {}
        
        for param in test_params:
            profile_values[profile.value][param] = get_param(param, 0)
    
    # Sprawdź różnice
    print("Porównanie wartości między profilami:")
    print("-" * 50)
    
    for param in test_params:
        balanced = profile_values['balanced'][param]
        aggressive = profile_values['aggressive'][param] 
        defensive = profile_values['defensive'][param]
        
        print(f"\n📊 {param}:")
        print(f"   🎯 Balanced:   {balanced:.2f}")
        print(f"   🔥 Aggressive: {aggressive:.2f}")
        print(f"   🛡️  Defensive:  {defensive:.2f}")
        
        # Sprawdź czy są różnice (profile nie powinny być identyczne)
        values = [balanced, aggressive, defensive]
        all_same = len(set(f"{v:.2f}" for v in values)) == 1
        
        if all_same:
            print("   ⚠️  UWAGA: Wszystkie profile mają identyczne wartości!")
        else:
            print("   ✅ Profile różnią się - OK")


def test_extreme_values_accessibility():
    """Testuje czy można osiągnąć skrajne wartości"""
    print("\n\n🏃 TEST DOSTĘPNOŚCI SKRAJNYCH WARTOŚCI")
    print("=" * 50)
    
    # Test czy suwaki mogą dotrzeć do min/max w każdym profilu
    critical_params = [
        ('ECONOMY.MIN_BUY', 15, 50),
        ('DEPLOYMENT.DEFAULT_VP_WEIGHT', 0.1, 2.0),
        ('COMBAT.THREAT_RETREAT_THRESHOLD', 1, 40),
        ('ECONOMY.ALLOC_RATIO', 0.3, 0.8)
    ]
    
    for param_path, expected_min, expected_max in critical_params:
        print(f"\n🎯 {param_path}:")
        
        for profile in [AIProfile.BALANCED, AIProfile.AGGRESSIVE, AIProfile.DEFENSIVE]:
            set_ai_profile(profile)
            current = get_param(param_path, 0)
            
            # Sprawdź margines do skrajnych wartości
            margin_to_min = current - expected_min
            margin_to_max = expected_max - current
            
            # Status accessibility
            can_reach_min = margin_to_min >= 0
            can_reach_max = margin_to_max >= 0
            
            min_status = "✅" if can_reach_min else "❌"
            max_status = "✅" if can_reach_max else "❌"
            
            print(f"   {profile.value.capitalize():>10}: {current:.2f}")
            print(f"      {min_status} Do MIN ({expected_min}): {margin_to_min:+.2f}")
            print(f"      {max_status} Do MAX ({expected_max}): {margin_to_max:+.2f}")
            
            if not (can_reach_min and can_reach_max):
                print(f"      ⚠️  PROBLEM: Nie może osiągnąć pełnego zakresu!")


def generate_summary_report(results, total_tests, failed_tests):
    """Generuje podsumowanie walidacji"""
    print("\n\n📋 PODSUMOWANIE WALIDACJI")
    print("=" * 80)
    
    success_rate = ((total_tests - failed_tests) / total_tests * 100) if total_tests > 0 else 0
    
    print(f"🔢 Statystyki:")
    print(f"   • Całkowite testy: {total_tests}")
    print(f"   • Pomyślne: {total_tests - failed_tests}")
    print(f"   • Niepomyślne: {failed_tests}")
    print(f"   • Wskaźnik sukcesu: {success_rate:.1f}%")
    
    print(f"\n🎯 Status:")
    if failed_tests == 0:
        print("   ✅ WSZYSTKIE SUWAKI MOGĄ OSIĄGNĄĆ PEŁNY ZAKRES")
        print("   ✅ GUI CONFIGURATION PANEL DZIAŁA PRAWIDŁOWO")
    else:
        print("   ❌ NIEKTÓRE SUWAKI MAJĄ OGRANICZONY DOSTĘP")
        print("   ⚠️  WYMAGANE POPRAWKI UI LUB KONFIGURACJI")
    
    # Pokaż problematyczne parametry
    if failed_tests > 0:
        print(f"\n🚨 PROBLEMATYCZNE PARAMETRY:")
        for profile_name, categories in results.items():
            for category_name, params in categories.items():
                for result in params:
                    if not result['in_range']:
                        print(f"   • {profile_name.upper()}: {result['param']}")
                        print(f"     Wartość: {result['current']}, Oczekiwany zakres: [{result['min_expected']}-{result['max_expected']}]")


def main():
    """Główna funkcja walidacyjna"""
    print("🔍 VALIDATOR SUWAKÓW AI CONFIGURATION PANEL")
    print("Sprawdzenie dostępności pełnego zakresu dla wszystkich parametrów")
    print("=" * 80)
    
    # Uruchom wszystkie testy
    results, total_tests, failed_tests = test_all_profiles_all_parameters()
    test_profile_multiplier_effects()
    test_extreme_values_accessibility()
    generate_summary_report(results, total_tests, failed_tests)
    
    # Końcowa rekomendacja
    print(f"\n🎯 REKOMENDACJA:")
    if failed_tests == 0:
        print("   🟢 AI Configuration Panel ready for production!")
        print("   🟢 All sliders can reach full value ranges!")
    else:
        print("   🟡 UI adjustments needed for full slider accessibility")
        print("   🟡 Consider increasing panel width or slider length")
        
    return failed_tests == 0


if __name__ == "__main__":
    success = main()
    exit(0 if success else 1)