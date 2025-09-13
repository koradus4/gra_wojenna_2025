"""
Integrator Logów AI - Łączy nowy system GameLogManager z istniejącymi funkcjami AI
(AI Log Integrator - Connects new GameLogManager with existing AI functions)

Zapewnia kompatybilność wsteczną (backward compatibility) z istniejącymi funkcjami 
log_commander_action, log_economy_turn itd., przekierowując je do nowego systemu.
"""

from __future__ import annotations
from typing import Any, Dict, Optional, List
from utils.game_log_manager import (
    get_game_log_manager, 
    KategoriaLog, 
    TagLog
)

class IntegratorLogow:
    """
    Integrator istniejących funkcji logowania z nowym GameLogManager
    (Integrator of existing logging functions with new GameLogManager)
    """
    
    def __init__(self):
        self.manager = get_game_log_manager()
        self.mapowanie_kategorii = self._utworz_mapowanie_kategorii()
    
    def _utworz_mapowanie_kategorii(self) -> Dict[str, KategoriaLog]:
        """Mapowanie starych nazw na nowe kategorie"""
        return {
            "commander": KategoriaLog.AI_DOWODCA,
            "general": KategoriaLog.AI_GENERAL,
            "combat": KategoriaLog.AI_WALKA,
            "movement": KategoriaLog.AI_RUCH,
            "supply": KategoriaLog.AI_ZAOPATRZENIE,
            "strategy": KategoriaLog.AI_STRATEGIA,
            "economy": KategoriaLog.AI_GENERAL,  # ekonomia idzie do AI General
            "keypoints": KategoriaLog.AI_STRATEGIA,
            "victory": KategoriaLog.AI_STRATEGIA,
            "garrison": KategoriaLog.AI_ZAOPATRZENIE,
        }
    
    def _przygotuj_ml_dane(self, **kwargs) -> Dict[str, Any]:
        """
        Przygotowuje dane do uczenia maszynowego z parametrów funkcji
        (Prepares ML data from function parameters)
        """
        ml_dane = {}
        
        # Parametry numeryczne dla ML
        numeryczne = ['turn', 'pe_start', 'pe_allocated', 'pe_spent_purchases', 
                     'mp_before', 'mp_after', 'fuel_before', 'fuel_after',
                     'combat_dmg_dealt', 'combat_dmg_taken', 'threat_level',
                     'target_search_best_score', 'aggression_level', 
                     'assignment_score', 'cost_points_total']
        
        for param in numeryczne:
            if param in kwargs and kwargs[param] is not None:
                try:
                    ml_dane[param] = float(kwargs[param])
                except (ValueError, TypeError):
                    pass
        
        # Parametry kategoryczne
        kategoryczne = ['action_type', 'unit_type', 'movement_mode', 
                       'strategic_state', 'decision_reason', 'nation']
        
        for param in kategoryczne:
            if param in kwargs and kwargs[param] is not None:
                ml_dane[param] = str(kwargs[param])
        
        # Pozycje hex
        pozycje = ['from_pos', 'to_pos', 'target_pos']
        for param in pozycje:
            if param in kwargs and kwargs[param] is not None:
                pos = kwargs[param]
                if isinstance(pos, (tuple, list)) and len(pos) >= 2:
                    ml_dane[f"{param}_q"] = pos[0]
                    ml_dane[f"{param}_r"] = pos[1]
        
        return ml_dane

# Funkcje kompatybilności wstecznej (Backward compatibility functions)

def log_commander_action(unit_id: str, action_type: str, from_pos, to_pos, 
                        reason: str, **kwargs) -> bool:
    """
    Kompatybilna funkcja logowania akcji dowódcy 
    (Compatible commander action logging function)
    """
    integrator = IntegratorLogow()
    
    # Przygotowanie wiadomości
    pos_info = ""
    if from_pos and to_pos:
        pos_info = f" z {from_pos} do {to_pos}"
    elif from_pos:
        pos_info = f" na {from_pos}"
    
    wiadomosc = f"Jednostka {unit_id}: {action_type}{pos_info}"
    
    # Szczegóły
    szczegoly = {
        "unit_id": unit_id,
        "action_type": action_type,
        "from_pos": from_pos,
        "to_pos": to_pos,
        "reason": reason,
        **kwargs
    }
    
    # Dane ML
    ml_dane = integrator._przygotuj_ml_dane(
        unit_id=unit_id, 
        action_type=action_type,
        from_pos=from_pos,
        to_pos=to_pos,
        **kwargs
    )
    
    return integrator.manager.log_ai_dowodca(
        wiadomosc=wiadomosc,
        szczegoly=szczegoly,
        ml_dane=ml_dane
    )

def log_economy_turn(turn: int, pe_start: int, pe_allocated: int, 
                    pe_spent_purchases: int, strategy_used: str, 
                    orders_issued: bool = False, 
                    decision_metrics: Optional[Dict] = None) -> bool:
    """
    Kompatybilna funkcja logowania ekonomii 
    (Compatible economy logging function)
    """
    integrator = IntegratorLogow()
    
    wiadomosc = (f"Tura {turn}: PE {pe_start}→{pe_allocated}→{pe_spent_purchases}, "
                f"strategia: {strategy_used}")
    
    szczegoly = {
        "turn": turn,
        "pe_start": pe_start,
        "pe_allocated": pe_allocated,
        "pe_spent_purchases": pe_spent_purchases,
        "strategy_used": strategy_used,
        "orders_issued": orders_issued,
        "decision_metrics": decision_metrics or {}
    }
    
    ml_dane = integrator._przygotuj_ml_dane(**szczegoly)
    
    return integrator.manager.log_ai_general(
        wiadomosc=wiadomosc,
        szczegoly=szczegoly,
        ml_dane=ml_dane
    )

def log_keypoints_turn(turn: int, key_points_state: Dict[str, Any]) -> bool:
    """
    Kompatybilna funkcja logowania punktów kluczowych
    (Compatible key points logging function)
    """
    integrator = IntegratorLogow()
    
    # Zliczanie kontrolowanych punktów
    kontrolowane = sum(1 for v in key_points_state.values() if v.get('controlled', False))
    total = len(key_points_state)
    
    wiadomosc = f"Tura {turn}: Punkty kluczowe {kontrolowane}/{total}"
    
    szczegoly = {
        "turn": turn,
        "key_points_state": key_points_state,
        "kontrolowane": kontrolowane,
        "total": total
    }
    
    ml_dane = integrator._przygotuj_ml_dane(**szczegoly)
    
    return integrator.manager.log(
        kategoria=KategoriaLog.AI_STRATEGIA,
        wiadomosc=wiadomosc,
        tagi=[TagLog.AI, TagLog.STRATEGIA],
        szczegoly=szczegoly,
        ml_dane=ml_dane
    )

def log_strategy_decision(turn: int, decision: str, rule_used: str, 
                         reasoning: str = "") -> bool:
    """
    Kompatybilna funkcja logowania decyzji strategicznych
    (Compatible strategy decision logging function)
    """
    integrator = IntegratorLogow()
    
    wiadomosc = f"Tura {turn}: Decyzja '{decision}' (reguła: {rule_used})"
    
    szczegoly = {
        "turn": turn,
        "decision": decision,
        "rule_used": rule_used,
        "reasoning": reasoning
    }
    
    ml_dane = integrator._przygotuj_ml_dane(**szczegoly)
    
    return integrator.manager.log(
        kategoria=KategoriaLog.AI_STRATEGIA,
        wiadomosc=wiadomosc,
        tagi=[TagLog.AI, TagLog.STRATEGIA, TagLog.DECYZJA],
        szczegoly=szczegoly,
        ml_dane=ml_dane
    )

def log_supply_replenishment(unit, action_type: str, fuel_before: int, 
                           fuel_after: int, **kwargs) -> bool:
    """
    Kompatybilna funkcja logowania zaopatrzenia
    (Compatible supply logging function)  
    """
    integrator = IntegratorLogow()
    
    unit_id = getattr(unit, 'id', str(unit))
    zmiana_paliwa = fuel_after - fuel_before
    
    wiadomosc = f"Zaopatrzenie {unit_id}: {action_type}, paliwo {fuel_before}→{fuel_after}"
    
    szczegoly = {
        "unit_id": unit_id,
        "action_type": action_type,
        "fuel_before": fuel_before,
        "fuel_after": fuel_after,
        "fuel_change": zmiana_paliwa,
        **kwargs
    }
    
    ml_dane = integrator._przygotuj_ml_dane(
        fuel_before=fuel_before,
        fuel_after=fuel_after,
        fuel_change=zmiana_paliwa,
        action_type=action_type,
        **kwargs
    )
    
    return integrator.manager.log_ai_zaopatrzenie(
        wiadomosc=wiadomosc,
        szczegoly=szczegoly,
        ml_dane=ml_dane
    )

def log_supply_batch(units_events: List[Dict], source: str, trigger_reason: str,
                    cost_points_total: int = 0, notes: str = "") -> bool:
    """
    Kompatybilna funkcja logowania grupowego zaopatrzenia
    (Compatible batch supply logging function)
    """
    integrator = IntegratorLogow()
    
    jednostki_count = len(units_events)
    wiadomosc = f"Zaopatrzenie grupowe: {jednostki_count} jednostek, koszt {cost_points_total}PE"
    
    szczegoly = {
        "units_events": units_events,
        "source": source,
        "trigger_reason": trigger_reason,
        "cost_points_total": cost_points_total,
        "notes": notes,
        "units_count": jednostki_count
    }
    
    ml_dane = integrator._przygotuj_ml_dane(
        cost_points_total=cost_points_total,
        units_count=jednostki_count,
        source=source
    )
    
    return integrator.manager.log_ai_zaopatrzenie(
        wiadomosc=wiadomosc,
        szczegoly=szczegoly,
        ml_dane=ml_dane
    )

def log_victory_ai_csv(action: str, player_id: str, turn: int, **kwargs) -> bool:
    """
    Kompatybilna funkcja logowania AI zwycięstwa
    (Compatible victory AI logging function)
    """
    integrator = IntegratorLogow()
    
    wiadomosc = f"Victory AI {player_id}: {action} (tura {turn})"
    
    szczegoly = {
        "action": action,
        "player_id": player_id,
        "turn": turn,
        **kwargs
    }
    
    ml_dane = integrator._przygotuj_ml_dane(
        turn=turn,
        action=action,
        player_id=player_id,
        **kwargs
    )
    
    return integrator.manager.log(
        kategoria=KategoriaLog.AI_STRATEGIA,
        wiadomosc=wiadomosc,
        tagi=[TagLog.AI, TagLog.STRATEGIA],
        szczegoly=szczegoly,
        ml_dane=ml_dane
    )

def log_garrison_issue_to_csv(issue_type: str, unit_id: str, 
                             garrison_hex: str, details: Dict) -> bool:
    """
    Kompatybilna funkcja logowania problemów garnizonu
    (Compatible garrison issue logging function)
    """
    integrator = IntegratorLogow()
    
    wiadomosc = f"Problem garnizonu {unit_id} na {garrison_hex}: {issue_type}"
    
    szczegoly = {
        "issue_type": issue_type,
        "unit_id": unit_id,
        "garrison_hex": garrison_hex,
        "details": details
    }
    
    ml_dane = integrator._przygotuj_ml_dane(
        issue_type=issue_type,
        unit_id=unit_id,
        garrison_hex=garrison_hex
    )
    
    return integrator.manager.log_ai_zaopatrzenie(
        wiadomosc=wiadomosc,
        szczegoly=szczegoly,
        ml_dane=ml_dane,
        poziom="WARNING"
    )

# Funkcja pomocnicza dla testów
def log_test_event(phase: str, component: str, action: str, 
                  status: str, message: str, **kwargs) -> bool:
    """
    Funkcja logowania wydarzeń testowych
    (Test event logging function)
    """
    integrator = IntegratorLogow()
    
    wiadomosc = f"TEST [{phase}] {component}.{action}: {status} - {message}"
    
    szczegoly = {
        "test_phase": phase,
        "component": component, 
        "action": action,
        "status": status,
        "message": message,
        **kwargs
    }
    
    ml_dane = integrator._przygotuj_ml_dane(
        test_phase=phase,
        component=component,
        action=action,
        status=status,
        **kwargs
    )
    
    poziom = "ERROR" if status == "ERROR" else "INFO"
    
    return integrator.manager.log(
        kategoria=KategoriaLog.GAME_MECHANIKA,
        wiadomosc=wiadomosc,
        tagi=[TagLog.SYSTEM, TagLog.DEBUG],
        szczegoly=szczegoly,
        ml_dane=ml_dane,
        poziom=poziom
    )

# Export funkcji dla kompatybilności
__all__ = [
    'IntegratorLogow',
    'log_commander_action',
    'log_economy_turn', 
    'log_keypoints_turn',
    'log_strategy_decision',
    'log_supply_replenishment',
    'log_supply_batch',
    'log_victory_ai_csv',
    'log_garrison_issue_to_csv',
    'log_test_event'
]