"""Moduł logowania AI Commandera – wyłącznie ZaawansowanyLoggerAI.

Ten moduł pełni rolę cienkiej warstwy kompatybilności: wszystkie wywołania
historycznych funkcji logujących są mapowane na polski system logowania
ZaawansowanyLoggerAI (kategorie: akcje_taktyczne, decyzje_strategiczne,
wydajnosc_ai itp.). Stary system CSV i fallbacki zostały całkowicie usunięte.

Publiczne API pozostawione dla zgodności: log_commander_action,
log_commander_turn, log_target_analysis, log_group_formation,
log_strategic_decision.
"""
from __future__ import annotations
from datetime import datetime
from typing import Any, Dict

# NOWY IMPORT: SessionManager dla zapobiegania duplikatom katalogów
try:
    from utils.session_manager import SessionManager
    from utils.ai_commander_logger_zaawansowany import ZaawansowanyLoggerAI
    NOWY_SYSTEM_SESJI = True
    _ADV_LOGGER_CACHE = None
except ImportError:
    # Jeśli SessionManager nie jest dostępny – wyłącz logowanie (bez fallbacków)
    NOWY_SYSTEM_SESJI = False
    _ADV_LOGGER_CACHE = None
    print("⚠️ [LOGOWANIE] Zaawansowany system logowania niedostępny – logi AI zostaną pominięte")


def _get_adv_logger():
    """Zwraca instancję ZaawansowanyLoggerAI powiązaną z bieżącą sesją (z cache)."""
    global _ADV_LOGGER_CACHE
    if not NOWY_SYSTEM_SESJI:
        return None
    try:
        if _ADV_LOGGER_CACHE is None:
            session_dir = SessionManager.get_current_session_dir()
            _ADV_LOGGER_CACHE = ZaawansowanyLoggerAI(session_dir)
        return _ADV_LOGGER_CACHE
    except Exception:
        return None

def log_commander_action(unit_id: str, action_type: str, from_pos, to_pos, reason: str,
                         player_nation: str = "Unknown", extra: Dict[str, Any] | None = None):
    """Logowanie akcji AI Commander do polskiego systemu (akcje_taktyczne)."""
    try:
        # Próba mapowania na nowy system (ZaawansowanyLoggerAI)
        adv = _get_adv_logger()
        if adv is not None:
            # Mapowanie minimalne na akcję taktyczną (najbliższy semantycznie odpowiednik)
            dane = {
                'turn': None,
                'phase': None,
                'nation': player_nation,
                'action_category': action_type,
                'unit_primary': unit_id,
                'execution_time_ms': None,
                # Uzasadnienie ruchu jako wskaźniki sukcesu (teksty)
                'success_indicators': reason,
            }
            if from_pos:
                # Pozycje nie mają dedykowanych kolumn w loggerze taktycznym – pomijamy
                pass
            if to_pos:
                # Pozycje docelowe również pomijamy w aktualnym schemacie
                pass
            # Przekazanie powodu i extra jako kontekst
            if extra and isinstance(extra, dict):
                for k, v in extra.items():
                    # Nie wszystkie pola znajdą się w KOLUMNY – logger zapełni N/A
                    dane[k] = v
            adv.loguj_akcje_taktyczna(dane)
            return
    except Exception:
        # Ciche pominięcie w razie błędu logowania aby nie blokować AI
        pass

__all__ = ["log_commander_action", "log_commander_turn", "log_target_analysis", "log_group_formation", "log_strategic_decision"]


def log_target_analysis(unit_id: str, candidates: int, best_score: float, best_distance: int, 
                       fallback_used: bool, player_nation: str = "Unknown", extra: Dict[str, Any] = None):
    """Loguje szczegółową analizę wyboru celu do CSV diagnostycznego."""
    adv = _get_adv_logger()
    if adv is not None:
        dane = {
            'nation': player_nation,
            'phase': 'target_selection',
            'action_category': 'target_analysis',
            'micro_decisions_count': candidates,
            'unit_synergy_score': best_score,
            'success_indicators': str(best_distance),
            'risk_mitigation': fallback_used,
        }
        if extra:
            # action_complexity jako liczba rozpatrywanych kandydatów
            if 'kp_count' in extra:
                dane['action_complexity'] = extra.get('kp_count', 0)
        adv.loguj_akcje_taktyczna(dane)
        return
    # Brak logowania jeżeli nowy system niedostępny
    return


def log_group_formation(group_id: int, group_size: int, leader_pos: tuple, assignment_score: float,
                       target_pos: tuple = None, player_nation: str = "Unknown", extra: Dict[str, Any] = None):
    """Loguje informacje o formowaniu grup do CSV diagnostycznego."""
    adv = _get_adv_logger()
    if adv is not None:
        dane = {
            'nation': player_nation,
            'phase': 'grouping',
            'action_category': 'group_formation',
            'unit_primary': f"GROUP_{group_id}",
            'units_supporting': group_size,
            'formation_type': 'group',
            'unit_synergy_score': assignment_score,
            'coordination_required': True,
        }
        if target_pos:
            dane['success_indicators'] = f"target=({target_pos[0]},{target_pos[1]})"
        if extra:
            for k, v in extra.items():
                dane[k] = v
        adv.loguj_akcje_taktyczna(dane)
        return
    # Brak logowania jeżeli nowy system niedostępny
    return


def log_strategic_decision(strategic_state: str, aggression_level: float, total_groups: int,
                         reassignments: int, player_nation: str = "Unknown", extra: Dict[str, Any] = None):
    """Loguje kluczowe decyzje strategiczne do CSV diagnostycznego."""
    adv = _get_adv_logger()
    if adv is not None:
        # Wyznacz priorytet na podstawie agresji
        if aggression_level is None:
            priority = 'MEDIUM'
        elif aggression_level < 0.33:
            priority = 'LOW'
        elif aggression_level < 0.66:
            priority = 'MEDIUM'
        else:
            priority = 'HIGH'
        dane = {
            'nation': player_nation,
            'decision_type': 'STRATEGIC_DECISION',
            'decision_scope': 'OPERATIONS',
            'priority_level': priority,
            'context_factors': f"state={strategic_state}, groups={total_groups}, reassignments={reassignments}",
            'decision_rationale': f"Strategy: {strategic_state}, aggression {aggression_level:.2f}",
            'confidence_level': 'MEDIUM',
        }
        if extra:
            for k, v in extra.items():
                dane[k] = v
        adv.loguj_decyzje_strategiczna(dane)
        return
    # Brak logowania jeżeli nowy system niedostępny
    return


def log_commander_turn(data: Dict[str, Any]):
    """Loguje zagregowane metryki tury dowódcy do kategorii wydajność (wydajnosc_ai).

    Wejściowy słownik `data` jest mapowany do pól rozumianych przez
    ZaawansowanyLoggerAI (np. calculations_performed, decision_tree_depth,
    prediction_success_rate, itp.). Brakujące wartości są pomijane lub
    uzupełniane wartościami domyślnymi. Funkcja jest bezpieczna – w razie błędu
    zapis zostaje pominięty i nie blokuje działania AI.
    """
    adv = _get_adv_logger()
    if adv is not None:
        try:
            attempts = data.get('resupply_attempts', 0) or 0
            successes = data.get('resupply_successes', 0) or 0
            stability = float(successes) / float(attempts) if attempts else 1.0
            payload = {
                'turn': data.get('turn'),
                'nation': data.get('nation') or data.get('player_nation') or 'Unknown',
                'calculations_performed': data.get('total_targets_analyzed'),
                'decision_tree_depth': data.get('groups'),
                'prediction_success_rate': data.get('moved_pct'),
                'adaptive_behavior_triggered': (data.get('dynamic_reassignments', 0) or 0) > 0,
                'error_recovery_attempts': data.get('coordination_failures'),
                'system_stability_index': stability,
                'algorithms_used': 'turn_summary',
            }
            adv.loguj_wydajnosc(payload)
            return
        except Exception:
            pass
    # Brak logowania jeżeli nowy system niedostępny
    return

__all__.append("log_commander_turn")
