"""Test publicznego kontraktu AI (Complete Contract v1)

Cel: Błyskawicznie wykryć usunięcie / zmianę nazwy publicznych elementów API AI.
Test NIE odpala logiki gry – tylko introspekcja.
"""
from importlib import import_module
from pathlib import Path
import inspect

CONTRACT_FUNCTIONS = [
    # snapshot funkcji globalnych
    "get_my_units",
    "prioritize_targets",
    "calculate_hex_distance",
    "assess_defensive_threats",
    "plan_defensive_retreat",
    "deploy_purchased_units",
    "find_deployment_position",
    "opportunistic_capture_phase",
    "ai_attempt_combat",
    "find_enemies_in_range",
    "evaluate_combat_ratio",
    "execute_ai_combat",
    "check_ai_reaction_attacks",
]

CONTRACT_CLASS = "AICommander"
CLASS_METHODS = [
    "pre_resupply",
    "tactical_resupply",
    "make_tactical_turn",
    "receive_orders",
]

# Świadomie publiczne helpery / re-eksporty które nie są częścią minimalnego kontraktu,
# ale nie powinny powodować faila: (utrzymywane w sync z dokumentacją gdy dodamy public_api)
WHITELIST_EXTRA = {
    'find_target', 'find_alternative_target', 'find_alternative_target_around', 'get_keypoint_value',
    'adaptive_grouping', 'assign_targets_with_coordination', 'dynamic_reassignment', 'group_units_by_proximity',
    'move_towards', 'choose_movement_mode', 'enforce_garrison_limits', 'defensive_coordination', 'debug_print',
    # logowanie i utility
    'log_commander_action', 'log_commander_turn', 'is_unit_holding', 'get_player_nation',
    # planowanie / autonomia
    'execute_mission_tactics', 'calculate_progressive_target', 'advanced_autonomous_mode', 'scan_for_enemies',
    # inne delegaty / aliasy
    'get_all_key_points', 'find_safe_retreat_position', 'find_safe_fallback_position', 'evaluate_position_safety',
    'plan_defensive_retreat', 'assess_defensive_threats'
    , 'can_move', 'evaluate_deployment_position', 'create_and_deploy_token', 'plan_group_defense', 'test_basic_safety'
}

DOC_FILE = Path("docs/ai/api_reference.md")
REQUIRED_DOC_MARKER = "Complete Contract v1"


def test_doc_contains_contract_marker():
    assert DOC_FILE.exists(), "Brak pliku dokumentacji kontraktu: docs/ai/api_reference.md"
    text = DOC_FILE.read_text(encoding="utf-8")
    assert REQUIRED_DOC_MARKER in text, "Brak znacznika wersji kontraktu w dokumentacji"


def test_public_functions_exist():
    mod = import_module("ai.ai_commander")
    missing = [name for name in CONTRACT_FUNCTIONS if not hasattr(mod, name)]
    assert not missing, f"Brak publicznych funkcji kontraktu: {missing}"


def test_ai_commander_class_and_methods():
    mod = import_module("ai.ai_commander")
    assert hasattr(mod, CONTRACT_CLASS), "Brak klasy AICommander"
    cls = getattr(mod, CONTRACT_CLASS)
    for method in CLASS_METHODS:
        assert hasattr(cls, method), f"Brak metody {method} w AICommander"
        attr = getattr(cls, method)
        assert callable(attr), f"{method} nie jest callable"


def test_get_my_units_contract_shape():
    mod = import_module("ai.ai_commander")
    get_my_units = getattr(mod, "get_my_units")

    class DummyGE:  # minimalny obiekt silnika
        tokens = []
        current_player_obj = type("P", (), {"id": 999})()

    units = get_my_units(DummyGE(), player_id=999)
    assert isinstance(units, list), "get_my_units powinno zwrócić listę"
    if units:  # jeżeli kiedyś test będzie na realnym engine
        sample = units[0]
        for key in ["id", "q", "r", "mp", "fuel", "cv", "token"]:
            assert key in sample, f"Brak pola '{key}' w unit_dict"


def test_functions_are_plain_callables():
    mod = import_module("ai.ai_commander")
    for name in CONTRACT_FUNCTIONS:
        obj = getattr(mod, name)
        assert callable(obj), f"{name} nie jest callable"
        # lekkie zabezpieczenie – nie chcemy klas podszywających się pod funkcje
        assert not inspect.isclass(obj), f"{name} powinno być funkcją, a jest klasą"


def test_no_accidental_new_public_items():
    """Opcjonalna straż: jeżeli liczba publicznych funkcji nagle wzrośnie znacznie – ostrzeżenie.
    Pozwala wykryć przypadkowe upublicznienie wewnętrznych helperów.
    (Heurystyka – > +10 nowych nazw względem kontraktu.)
    """
    mod = import_module("ai.ai_commander")
    exported = [n for n, v in vars(mod).items() if callable(v) and not n.startswith("_") and not isinstance(v, type)]
    extra = [n for n in exported if n not in CONTRACT_FUNCTIONS and n not in [CONTRACT_CLASS] and n not in WHITELIST_EXTRA]
    # Po odjęciu białej listy – jeśli >5 nowych to sygnał, że kontrakt się rozszedł niekontrolowanie
    assert len(extra) <= 3, f"Nowe niespodziewane publiczne elementy: {extra[:15]}"

