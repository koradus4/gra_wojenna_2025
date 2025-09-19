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
            # Jeżeli extra zawiera szczegóły PE z resupply, zmapuj do nowych pól
            if extra and isinstance(extra, dict):
                if 'resupply_budget_available' in extra:
                    dane['resupply_budget_available'] = extra.get('resupply_budget_available')
                if 'resupply_pe_spent' in extra:
                    dane['resupply_pe_spent'] = extra.get('resupply_pe_spent')
                if 'pe_spent_fuel' in extra:
                    dane['pe_spent_fuel'] = extra.get('pe_spent_fuel')
                if 'pe_spent_combat' in extra:
                    dane['pe_spent_combat'] = extra.get('pe_spent_combat')
                if 'before_fuel' in extra:
                    dane['before_fuel'] = extra.get('before_fuel')
                if 'after_fuel' in extra:
                    dane['after_fuel'] = extra.get('after_fuel')
                if 'before_cv' in extra:
                    dane['before_cv'] = extra.get('before_cv')
                if 'after_cv' in extra:
                    dane['after_cv'] = extra.get('after_cv')
                if 'global_pe_remaining' in extra:
                    dane['global_pe_remaining'] = extra.get('global_pe_remaining')
                if 'resupply_total_need' in extra:
                    dane['resupply_total_need'] = extra.get('resupply_total_need')
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

# --- Nowe adaptery diagnostyczne ---

def _log_tactical_diag(payload: Dict[str, Any]) -> None:
    adv = _get_adv_logger()
    if adv is None:
        return
    try:
        adv.loguj_akcje_taktyczna(payload)
    except Exception:
        pass


def log_attack_opportunity_scan(unit_id: str, player_nation: str, candidates_count: int, min_ratio: float, enemies_preview: str = "", extra: Dict[str, Any] | None = None) -> None:
    payload = {
        'nation': player_nation,
        'phase': 'combat',
        'action_category': 'Rozpoznanie_Bojowe',
        'action_type': 'attack_opportunity_scan',
        'unit_id': unit_id,
        'micro_decisions_count': candidates_count,
        'threshold': min_ratio,
        'success_indicators': enemies_preview[:200]
    }
    if extra:
        payload.update(extra)
    _log_tactical_diag(payload)


def log_combat_precheck(unit_id: str, player_nation: str, enemy_id: str, ratio: float, threshold: float, decision: str, reason: str = "") -> None:
    payload = {
        'nation': player_nation,
        'phase': 'combat',
        'action_category': 'Skoordynowany_Atak',
        'action_type': 'combat_precheck',
        'unit_id': unit_id,
        'target_id': enemy_id,
        'ratio': ratio,
        'threshold': threshold,
        'decision': decision,
        'reason': reason
    }
    _log_tactical_diag(payload)


def log_combat_decision(unit_id: str, player_nation: str, enemy_id: str, ratio: float, threshold: float, decision: str, reason: str = "", extra: Dict[str, Any] | None = None) -> None:
    payload = {
        'nation': player_nation,
        'phase': 'combat',
        'action_category': 'Skoordynowany_Atak',
        'action_type': 'combat_decision',
        'unit_id': unit_id,
        'target_id': enemy_id,
        'ratio': ratio,
        'threshold': threshold,
        'decision': decision,
        'reason': reason
    }
    if extra and isinstance(extra, dict):
        payload.update(extra)
    _log_tactical_diag(payload)


def log_move_aborted(unit_id: str, player_nation: str, from_pos: tuple, to_pos: tuple, validate_status: str, error_code: str = "", reason: str = "",
                     nearest_reachable_dist: int | None = None,
                     nearest_reachable_hex_q: int | None = None,
                     nearest_reachable_hex_r: int | None = None,
                     obstacle_hint: str | None = None) -> None:
    payload = {
        'nation': player_nation,
        'phase': 'movement',
        'action_category': 'Manewry_Odwrotu',
        'action_type': 'move_aborted',
        'unit_id': unit_id,
        'from_hex_q': from_pos[0],
        'from_hex_r': from_pos[1],
        'to_hex_q': to_pos[0],
        'to_hex_r': to_pos[1],
        'validate_status': validate_status,
        'error_code': error_code,
        'reason': reason
    }
    # Nowe pola diagnostyczne (opcjonalne)
    if nearest_reachable_dist is not None:
        payload['nearest_reachable_dist'] = nearest_reachable_dist
    if nearest_reachable_hex_q is not None:
        payload['nearest_reachable_hex_q'] = nearest_reachable_hex_q
    if nearest_reachable_hex_r is not None:
        payload['nearest_reachable_hex_r'] = nearest_reachable_hex_r
    if obstacle_hint:
        payload['obstacle_hint'] = obstacle_hint
    _log_tactical_diag(payload)


def log_path_planned(unit_id: str, player_nation: str, from_pos: tuple, to_pos: tuple, length: int, mp: int, fuel: int) -> None:
    payload = {
        'nation': player_nation,
        'phase': 'movement',
        'action_category': 'Manewry_Odwrotu',
        'action_type': 'path_planned',
        'unit_id': unit_id,
        'from_hex_q': from_pos[0],
        'from_hex_r': from_pos[1],
        'to_hex_q': to_pos[0],
        'to_hex_r': to_pos[1],
        'action_complexity': length,
        'execution_time_ms': 0,
        'micro_decisions_count': mp,
        'unit_synergy_score': fuel
    }
    _log_tactical_diag(payload)


def log_kp_vacate_attempt(unit_id: str, player_nation: str, hex_id: str, ratio: float, turns_stationed: int, reason: str) -> None:
    try:
        q, r = (int(hex_id.split(',')[0]), int(hex_id.split(',')[1])) if ',' in hex_id else (None, None)
    except Exception:
        q, r = (None, None)
    payload = {
        'nation': player_nation,
        'phase': 'garrison',
        'action_category': 'Przegrupowanie_Zasobow',
        'action_type': 'kp_vacate_attempt',
        'unit_id': unit_id,
        'to_hex_q': q,
        'to_hex_r': r,
        'ratio': ratio,
        'micro_decisions_count': turns_stationed,
        'reason': reason
    }
    _log_tactical_diag(payload)


def log_kp_vacate_blocked(unit_id: str, player_nation: str, hex_id: str, ratio: float, turns_stationed: int, reason: str) -> None:
    try:
        q, r = (int(hex_id.split(',')[0]), int(hex_id.split(',')[1])) if ',' in hex_id else (None, None)
    except Exception:
        q, r = (None, None)
    payload = {
        'nation': player_nation,
        'phase': 'garrison',
        'action_category': 'Przygotowanie_Obrony',
        'action_type': 'kp_vacate_blocked',
        'unit_id': unit_id,
        'to_hex_q': q,
        'to_hex_r': r,
        'ratio': ratio,
        'micro_decisions_count': turns_stationed,
        'validate_status': 'blocked',
        'reason': reason
    }
    _log_tactical_diag(payload)


__all__ += [
    'log_attack_opportunity_scan', 'log_combat_precheck', 'log_combat_decision',
    'log_move_aborted', 'log_path_planned', 'log_kp_vacate_attempt', 'log_kp_vacate_blocked'
]
