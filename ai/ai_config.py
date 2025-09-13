"""
AI Commander Configuration System
Centralny system parametryzacji dla wszystkich modułów AI

Cechy:
- Profile AI (Agresywny, Defensywny, Zbalansowany)  
- Ładowanie z JSON/YAML
- Hot-reload podczas gry
- Walidacja parametrów
- Fallback do wartości domyślnych
"""
from __future__ import annotations

import json
import yaml
from pathlib import Path
from typing import Dict, Any, Optional, Union
from enum import Enum
import logging

# Ustawienie loggera
logger = logging.getLogger(__name__)


class AIProfile(Enum):
    """Predefiniowane profile AI"""
    AGGRESSIVE = "aggressive"
    DEFENSIVE = "defensive" 
    BALANCED = "balanced"
    CUSTOM = "custom"


class AIConfigManager:
    """Centralny manager konfiguracji AI"""
    
    def __init__(self, config_dir: str = "ai/configs"):
        self.config_dir = Path(config_dir)
        self.config_dir.mkdir(parents=True, exist_ok=True)
        
        self.current_profile = AIProfile.BALANCED
        self.parameters = {}
        self.profiles = {}
        self.custom_parameters = {}  # Przechowuje custom zmiany
        
        # Ładowanie konfiguracji
        self._load_default_parameters()
        self._load_profiles() 
        self._load_current_config()
    
    def _load_default_parameters(self):
        """Ładuje domyślne parametry - fallback gdy brak pliku konfiguracji"""
        self.parameters = {
            # === EKONOMIA & BUDŻET ===
            'ECONOMY': {
                'MIN_BUY': 30,
                'MIN_ALLOCATE': 60,
                'ALLOC_RATIO': 0.6,
                'UNSPENT_CAP': 80,
                'BUDGET_STRATEGIES': {
                    'ROZWÓJ': {'reserve': 0.20, 'allocate': 0.40, 'purchase': 0.40},
                    'KRYZYS_PALIWA': {'reserve': 0.15, 'allocate': 0.50, 'purchase': 0.35},
                    'DESPERACJA': {'reserve': 0.10, 'allocate': 0.25, 'purchase': 0.65},
                    'OCHRONA': {'reserve': 0.30, 'allocate': 0.55, 'purchase': 0.15},
                    'EKSPANSJA': {'reserve': 0.20, 'allocate': 0.35, 'purchase': 0.45}
                },
                'UNIT_TYPE_PRIORITIES': {
                    'Z': 1.5,  # Zaopatrzenie - kluczowe dla ekonomii PE
                    'P': 1.1,  # Piechota - uniwersalna
                    'D': 1.2   # Dowództwo - ważne
                },
                'ALLOCATION_THRESHOLDS': {
                    'SMALL_ARMY_SIZE': 5,
                    'HIGH_RESUPPLY_RATIO': 0.7
                },
                'BUDGET_ALLOCATIONS': {
                    'SMALL_ARMY': {'allocate': 0.3, 'purchase': 0.6, 'reserve': 0.1},
                    'HIGH_RESUPPLY': {'allocate': 0.8, 'purchase': 0.1, 'reserve': 0.1},
                    'BALANCED': {'allocate': 0.5, 'purchase': 0.4, 'reserve': 0.1}
                }
            },
            
            # === PALIWO & LOGISTYKA ===
            'LOGISTICS': {
                'LOW_FUEL_PERCENT_THRESHOLD': 30,
                'LOW_FUEL_UNITS_RATIO_TRIGGER': 0.30,
                'MAX_UNITS_PER_TURN': 2,
                'RESUPPLY_RATIOS': {
                    'SPOKÓJ': 0.5,
                    'WOJNA': 0.8, 
                    'KRYZYS': 0.9
                },
                'PEACE_CONDITIONS': {
                    'min_force_ratio': 1.5,
                    'max_threats': 0,
                    'min_fuel_level': 0.7
                },
                'CRISIS_CONDITIONS': {
                    'max_force_ratio': 0.8,
                    'min_threats': 2,
                    'max_fuel_level': 0.4
                }
            },
            
            # === WALKA & COMBAT ===
            'COMBAT': {
                'COUNTER_ATTACK_MAX_PENALTY': 0.6,
                'COUNTER_ATTACK_BASE_PENALTY': 0.25,
                'PROXIMITY_THREAT_RANGE': 5,
                'PROXIMITY_MIN_FACTOR': 0.1,
                'THREAT_NORMALIZATION': 100,
                'MAX_UNIT_THREAT_LEVEL': 1.0,
                'THREAT_RETREAT_THRESHOLD': 5,
                'MINIMUM_ATTACK_RATIO': 1.2,  # Minimalny stosunek sił do ataku
                'LOW_CV_RESUPPLY_THRESHOLD': 0.8,  # Próg resupply przed walką
                'MINIMUM_CV_RETREAT_RATIO': 0.25,  # Próg odwrotu przy niskim CV
                'HIGH_DETECTION_THRESHOLD': 0.8,  # Próg dobrej detekcji wroga
                'MEDIUM_DETECTION_THRESHOLD': 0.5,  # Próg średniej detekcji wroga
                'THREAT_RANGE': 6,
                'KEYPOINT_DEFENSE_RANGE': 2
            },
            
            # === STRATEGIA & VP ===
            'STRATEGY': {
                'VP_WINNING_THRESHOLD': 10,
                'VP_LOSING_THRESHOLD': -10,
                'STRATEGY_MULTIPLIERS': {
                    'LOSING': {'victory_points': 2.0, 'economy': 1.2},
                    'WINNING': {'economy': 1.5, 'victory_points': 0.8},
                    'TIED': {'economy': 1.3, 'victory_points': 1.0}
                },
                'DISTANCE_ACCESSIBILITY_THRESHOLD': 10,
                'ACCESSIBILITY_BONUS': 0.3
            },
            
            # === DEPLOYMENT & POZYCJONOWANIE ===
            'DEPLOYMENT': {
                'FREE_KEYPOINT_VALUE_DISTANCE_FACTOR': 1.2,
                'FREE_HIGH_VALUE_BONUS_MULTIPLIER': 2.5,
                'FREE_MED_VALUE_BONUS_MULTIPLIER': 1.6,
                'DEFAULT_ECON_WEIGHT': 1.0,
                'DEFAULT_VP_WEIGHT': 0.5,
                'MIXED_WEIGHT_SPLIT': 0.5,
                'HIGH_VALUE_THRESHOLD': 100,
                'MEDIUM_VALUE_THRESHOLD': 50,
                'GARRISON_LIMITS': {
                    'default': 2,
                    'high_value': 3,
                    'strategic': 4
                },
                'EARLY_ROTATION_THRESHOLD_RATIO': 0.25
            },
            
            # === RUCH & MOBILNOŚĆ ===
            'MOVEMENT': {
                'PROGRESSIVE_STEP_LIMIT': 100,
                'RESOURCE_MOVEMENT_THRESHOLD': 1,
                'MIN_GROUP_SIZE': 3,
                'MAX_GROUP_SIZE': 5,
                'MAX_GROUP_DISTANCE': 8,
                'MAX_RETREAT_RANGE': 4,
                'PROGRESSIVE_MOVE_ENABLED': True,
                'SIGHT_RANGE_DEFAULT': 1,
                'THREAT_DETECTION_BONUS': 1
            },
            
            # === ZAKUPY & JEDNOSTKI ===
            'PURCHASES': {
                'MAX_PURCHASE_ATTEMPTS': 300,
                'MIN_PURCHASE_COST': 15,
                'DYNAMIC_COST_FACTORS': {
                    "AL": 0.20, "AC": 0.25, "AP": 0.20, "TC": 0.25
                },
                'ANTI_SPAM_GROUPS': {
                    "artillery": {
                        "types": ["AL", "AC", "AP"],
                        "base_allow": 2,
                        "max_ratio": 0.45
                    },
                    "heavy_armor": {
                        "types": ["TC"],
                        "base_allow": 1,
                        "max_ratio": 0.30
                    }
                },
                'FORCE_RATIO_THRESHOLDS': {
                    'DEFENSIVE': 0.7,
                    'DOMINANCE': 1.5,
                    'CASUALTIES_THRESHOLD': 3,
                    'MIN_ARMY_SIZE': 8
                }
            }
        }
    
    def _load_profiles(self):
        """Ładuje profile AI z definicjami modyfikatorów"""
        self.profiles = {
            AIProfile.AGGRESSIVE: {
                'name': 'Agresywny Commander',
                'description': 'Maksymalny nacisk na atak, wysokie ryzyko, szybkie tempo',
                'multipliers': {
                    # Ekonomia - mniej oszczędności, więcej na zakupy
                    'ECONOMY.MIN_BUY': 0.7,                    # 21 zamiast 30
                    'ECONOMY.BUDGET_STRATEGIES.EKSPANSJA.purchase': 1.2,  # +20% na zakupy
                    'ECONOMY.BUDGET_STRATEGIES.EKSPANSJA.reserve': 0.5,   # -50% rezerwy
                    
                    # Strategia - priorytet VP nad ekonomią
                    'STRATEGY.STRATEGY_MULTIPLIERS.TIED.victory_points': 1.3,
                    'STRATEGY.STRATEGY_MULTIPLIERS.TIED.economy': 0.8,
                    
                    # Deployment - agresywne pozycjonowanie
                    'DEPLOYMENT.DEFAULT_VP_WEIGHT': 1.5,       # +50% waga VP
                    'DEPLOYMENT.DEFAULT_ECON_WEIGHT': 0.8,     # -20% waga ekonomii
                    
                    # Combat - wyższe tolerancja ryzyka
                    'COMBAT.COUNTER_ATTACK_MAX_PENALTY': 0.4,  # Mniejszy strach przed kontatakiem
                    'COMBAT.THREAT_RETREAT_THRESHOLD': 7,      # Wyższy próg odwrotu
                    
                    # Logistyka - więcej jednostek bojowych
                    'LOGISTICS.MAX_UNITS_PER_TURN': 1.5,       # 3 jednostki zamiast 2
                    'PURCHASES.ANTI_SPAM_GROUPS.artillery.max_ratio': 1.2  # +20% artylerii
                }
            },
            
            AIProfile.DEFENSIVE: {
                'name': 'Defensywny Commander', 
                'description': 'Ochrona pozycji, ekonomia, niska tolerancja ryzyka',
                'multipliers': {
                    # Ekonomia - więcej rezerw, mniej ryzyka
                    'ECONOMY.MIN_ALLOCATE': 1.3,               # 78 zamiast 60
                    'ECONOMY.BUDGET_STRATEGIES.OCHRONA.reserve': 1.5,  # +50% rezerwy
                    'ECONOMY.BUDGET_STRATEGIES.OCHRONA.purchase': 0.7,  # -30% zakupów
                    
                    # Strategia - ekonomia > VP
                    'STRATEGY.STRATEGY_MULTIPLIERS.TIED.economy': 1.5,
                    'STRATEGY.STRATEGY_MULTIPLIERS.TIED.victory_points': 0.7,
                    
                    # Deployment - ostrożne pozycjonowanie
                    'DEPLOYMENT.DEFAULT_ECON_WEIGHT': 1.4,     # +40% waga ekonomii
                    'DEPLOYMENT.DEFAULT_VP_WEIGHT': 0.6,       # -40% waga VP
                    'DEPLOYMENT.GARRISON_LIMITS.default': 1.5, # Większe garnizony
                    
                    # Combat - ostrożność
                    'COMBAT.THREAT_RETREAT_THRESHOLD': 3,      # Niższy próg odwrotu
                    'COMBAT.KEYPOINT_DEFENSE_RANGE': 1.5,      # Większy zasięg obrony
                    
                    # Logistyka - lepsze zaopatrzenie
                    'LOGISTICS.LOW_FUEL_UNITS_RATIO_TRIGGER': 0.8,  # 24% zamiast 30%
                    'LOGISTICS.RESUPPLY_RATIOS.WOJNA': 1.1     # +10% resupply w wojnie
                }
            },
            
            AIProfile.BALANCED: {
                'name': 'Zbalansowany Commander',
                'description': 'Uniwersalny profil, adaptacyjny do sytuacji',
                'multipliers': {
                    # Wszystkie wartości = 1.0 (domyślne)
                    # Można dodać drobne korekty dla "idealnego" balansu
                    'ECONOMY.ALLOC_RATIO': 1.0,
                    'STRATEGY.VP_WINNING_THRESHOLD': 1.0,
                    'COMBAT.THREAT_RETREAT_THRESHOLD': 1.0,
                    'DEPLOYMENT.DEFAULT_ECON_WEIGHT': 1.0,
                    'DEPLOYMENT.DEFAULT_VP_WEIGHT': 1.0
                }
            },
            
            AIProfile.CUSTOM: {
                'name': 'Niestandardowy Commander',
                'description': 'Konfiguracja dostosowana ręcznie przez użytkownika',
                'multipliers': {}  # Brak mnożników - używa wartości bezpośrednich
            }
        }
    
    def _load_current_config(self):
        """Ładuje aktualną konfigurację z pliku"""
        config_file = self.config_dir / "ai_config.json"
        
        if config_file.exists():
            try:
                with open(config_file, 'r', encoding='utf-8') as f:
                    config = json.load(f)
                    
                self.current_profile = AIProfile(config.get('profile', 'balanced'))
                
                # Merge custom parameters
                if 'custom_parameters' in config:
                    self.custom_parameters = config['custom_parameters']
                    self._merge_parameters(config['custom_parameters'])
                    
                logger.info(f"Loaded AI config: {self.current_profile.value}")
                
            except Exception as e:
                logger.error(f"Failed to load AI config: {e}")
                logger.info("Using default configuration")
        else:
            # Stwórz domyślny plik konfiguracji
            self.save_config()
    
    def _merge_parameters(self, custom_params: Dict[str, Any]):
        """Scala custom parametry z domyślnymi"""
        def deep_merge(base: dict, override: dict):
            for key, value in override.items():
                if key in base and isinstance(base[key], dict) and isinstance(value, dict):
                    deep_merge(base[key], value)
                else:
                    base[key] = value
        
        deep_merge(self.parameters, custom_params)
    
    def get_parameter(self, path: str, default: Any = None) -> Any:
        """
        Pobiera parametr z aktualnego profilu
        
        Args:
            path: Ścieżka do parametru w formacie 'CATEGORY.PARAMETER' 
                  lub 'CATEGORY.SUBCATEGORY.PARAMETER'
            default: Wartość domyślna jeśli parametr nie istnieje
            
        Returns:
            Wartość parametru z zastosowanym modyfikatorem profilu
            
        Example:
            config.get_parameter('ECONOMY.MIN_BUY')  # 30 dla balanced, 21 dla aggressive  
            config.get_parameter('STRATEGY.VP_WINNING_THRESHOLD', 10)
        """
        try:
            # Pobierz bazową wartość
            keys = path.split('.')
            value = self.parameters
            
            for key in keys:
                if isinstance(value, dict) and key in value:
                    value = value[key]
                else:
                    return default
            
            # Zastosuj modyfikator profilu jeśli istnieje
            profile_multipliers = self.profiles.get(self.current_profile, {}).get('multipliers', {})
            
            if path in profile_multipliers:
                multiplier = profile_multipliers[path]
                if isinstance(value, (int, float)):
                    return value * multiplier
                    
            return value
            
        except Exception as e:
            logger.error(f"Error getting parameter {path}: {e}")
            return default
    
    def set_parameter(self, path: str, value: Any):
        """Ustawia parametr w konfiguracji"""
        keys = path.split('.')
        
        # Zapisz w parameters (aktywna wartość)
        current = self.parameters
        for key in keys[:-1]:
            if key not in current:
                current[key] = {}
            current = current[key]
        current[keys[-1]] = value
        
        # Zapisz w custom_parameters (do zachowania w pliku)
        custom_current = self.custom_parameters
        for key in keys[:-1]:
            if key not in custom_current:
                custom_current[key] = {}
            custom_current = custom_current[key]
        custom_current[keys[-1]] = value
        
        # Przełącz na custom profil
        self.current_profile = AIProfile.CUSTOM
        
        logger.info(f"Set parameter {path} = {value} (custom)")
    
    def set_profile(self, profile: Union[AIProfile, str]):
        """Zmienia aktualny profil AI"""
        if isinstance(profile, str):
            profile = AIProfile(profile)
            
        self.current_profile = profile
        logger.info(f"Changed AI profile to: {profile.value}")
    
    def get_profile_info(self) -> Dict[str, str]:
        """Zwraca informacje o aktualnym profilu"""
        profile_data = self.profiles.get(self.current_profile, {})
        return {
            'profile': self.current_profile.value,
            'name': profile_data.get('name', 'Unknown'),
            'description': profile_data.get('description', 'No description')
        }
    
    def save_config(self):
        """Zapisuje aktualną konfigurację do pliku"""
        config_file = self.config_dir / "ai_config.json"
        
        config = {
            'profile': self.current_profile.value,
            'profile_info': self.get_profile_info(),
            'custom_parameters': self.custom_parameters,
            'metadata': {
                'version': '1.0',
                'created_by': 'AI Configuration System'
            }
        }
        
        try:
            with open(config_file, 'w', encoding='utf-8') as f:
                json.dump(config, f, indent=2, ensure_ascii=False)
                
            logger.info(f"Saved AI config to: {config_file}")
            
        except Exception as e:
            logger.error(f"Failed to save AI config: {e}")
    
    def export_profile_comparison(self) -> str:
        """Eksportuje porównanie wszystkich profili do pliku Markdown"""
        output = ["# AI Profiles Comparison\n"]
        
        for profile in [AIProfile.BALANCED, AIProfile.AGGRESSIVE, AIProfile.DEFENSIVE]:
            profile_data = self.profiles[profile]
            output.append(f"## {profile_data['name']}")
            output.append(f"*{profile_data['description']}*\n")
            
            # Temporary switch to get modified values
            original_profile = self.current_profile
            self.current_profile = profile
            
            output.append("### Key Parameters:")
            sample_params = [
                'ECONOMY.MIN_BUY',
                'STRATEGY.STRATEGY_MULTIPLIERS.TIED.victory_points',
                'COMBAT.THREAT_RETREAT_THRESHOLD',
                'DEPLOYMENT.DEFAULT_VP_WEIGHT'
            ]
            
            for param in sample_params:
                value = self.get_parameter(param, 'N/A')
                output.append(f"- `{param}`: {value}")
            
            output.append("")  # Empty line
            
            # Restore original profile
            self.current_profile = original_profile
        
        return "\n".join(output)


# Globalna instancja - singleton
_config_manager = None

def get_ai_config() -> AIConfigManager:
    """Zwraca globalną instancję managera konfiguracji"""
    global _config_manager
    if _config_manager is None:
        _config_manager = AIConfigManager()
    return _config_manager


# Convenience functions
def get_param(path: str, default: Any = None) -> Any:
    """Shortcut do pobierania parametrów"""
    return get_ai_config().get_parameter(path, default)

def set_param(path: str, value: Any):
    """Shortcut do ustawiania parametrów"""
    get_ai_config().set_parameter(path, value)

def set_ai_profile(profile: Union[AIProfile, str]):
    """Shortcut do zmiany profilu AI"""
    get_ai_config().set_profile(profile)

def get_ai_profile_info() -> Dict[str, str]:
    """Shortcut do informacji o profilu"""
    return get_ai_config().get_profile_info()


if __name__ == "__main__":
    # Test konfiguracji
    config = AIConfigManager()
    
    print("=== AI Configuration System Test ===")
    print(f"Current profile: {config.get_profile_info()}")
    print(f"MIN_BUY (balanced): {config.get_parameter('ECONOMY.MIN_BUY')}")
    
    config.set_profile(AIProfile.AGGRESSIVE)  
    print(f"MIN_BUY (aggressive): {config.get_parameter('ECONOMY.MIN_BUY')}")
    
    config.set_profile(AIProfile.DEFENSIVE)
    print(f"MIN_BUY (defensive): {config.get_parameter('ECONOMY.MIN_BUY')}")
    
    # Export comparison
    comparison = config.export_profile_comparison()
    print("\n=== Profile Comparison ===")
    print(comparison[:500] + "..." if len(comparison) > 500 else comparison)