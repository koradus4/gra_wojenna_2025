import sys
from datetime import datetime
from pathlib import Path

print("🚀 Smoke test nowego systemu logowania")

try:
    from utils.session_manager import SessionManager
    from ai.logowanie_ai import log_commander_action
    from utils.ai_commander_logger_zaawansowany import ZaawansowanyLoggerAI
except Exception as e:
    print(f"❌ Import error: {e}")
    sys.exit(1)

try:
    session_dir = SessionManager.get_current_session_dir()
    print(f"📁 Session dir: {session_dir}")

    # 1) Proxy: stare wywołanie → nowy logger (akcje taktyczne)
    log_commander_action(
        unit_id='TEST_UNIT',
        action_type='move',
        from_pos=(1, 2),
        to_pos=(2, 3),
        reason='smoke_test_action_move',
        player_nation='Niemcy',
        extra={'phase': 'test_phase'}
    )
    print("✅ log_commander_action wykonany (proxy → nowy logger)")

    # 2) Bezpośrednio: wydajność AI
    adv = ZaawansowanyLoggerAI(session_dir)
    adv.loguj_wydajnosc({
        'turn': 1,
        'nation': 'Niemcy',
        'decision_latency_ms': 12,
        'calculations_performed': 34,
        'algorithms_used': 'test',
        'memory_usage_mb': 123.4,
        'cpu_utilization_pct': 7.8,
        'decision_tree_depth': 2,
        'alternatives_evaluated': 3,
        'optimization_iterations': 1,
        'ai_confidence_score': 0.9,
        'learning_rate_applied': 0.01,
        'model_accuracy_current': 0.75,
        'prediction_success_rate': 0.5,
        'adaptive_behavior_triggered': False,
        'error_recovery_attempts': 0,
        'system_stability_index': 1.0
    })
    print("✅ loguj_wydajnosc wykonany (nowy logger)")

    # 3) Walidacja plików
    today = datetime.now().strftime('%Y%m%d')
    base = Path(session_dir) / 'ai_commander_zaawansowany'
    tactical = base / 'akcje_taktyczne' / f'akcje_taktyczne_{today}.csv'
    perf = base / 'wydajnosc_ai' / f'wydajnosc_ai_{today}.csv'

    ok_tactical = tactical.exists()
    ok_perf = perf.exists()

    print(f"📄 Akcje taktyczne: {tactical} → {'OK' if ok_tactical else 'MISSING'}")
    print(f"📄 Wydajność AI:   {perf} → {'OK' if ok_perf else 'MISSING'}")

    if ok_tactical and ok_perf:
        print("🎉 Smoke test zaliczony: nowy system zapisuje pliki.")
        sys.exit(0)
    else:
        print("⚠️ Smoke test częściowy: nie wszystkie pliki powstały.")
        sys.exit(2)

except Exception as e:
    print(f"❌ Smoke test error: {e}")
    sys.exit(2)
