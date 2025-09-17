import sys
from datetime import datetime
from pathlib import Path

print("🚀 Smoke test mapowania funkcji na nowy logger")

try:
    from utils.session_manager import SessionManager
    from ai.logowanie_ai import (
        log_target_analysis,
        log_group_formation,
        log_strategic_decision,
        log_commander_turn,
    )
except Exception as e:
    print(f"❌ Import error: {e}")
    sys.exit(1)

try:
    session_dir = SessionManager.get_current_session_dir()
    print(f"📁 Session dir: {session_dir}")

    # 1) target_analysis → akcje_taktyczne
    log_target_analysis(
        unit_id='U-TEST',
        candidates=5,
        best_score=0.83,
        best_distance=2,
        fallback_used=True,
        player_nation='Polska',
        extra={'kp_count': 9}
    )
    print("✅ log_target_analysis → akcje_taktyczne")

    # 2) group_formation → akcje_taktyczne
    log_group_formation(
        group_id=7,
        group_size=3,
        leader_pos=(4,5),
        assignment_score=0.72,
        target_pos=(6,7),
        player_nation='Polska',
        extra={'note': 'smoke'}
    )
    print("✅ log_group_formation → akcje_taktyczne")

    # 3) strategic_decision → decyzje_strategiczne
    log_strategic_decision(
        strategic_state='DEFENSIVE',
        aggression_level=0.4,
        total_groups=2,
        reassignments=1,
        player_nation='Polska',
        extra={'economic_impact': 'LOW'}
    )
    print("✅ log_strategic_decision → decyzje_strategiczne")

    # 4) commander_turn → wydajnosc_ai
    log_commander_turn({
        'turn': 1,
        'nation': 'Polska',
        'groups': 2,
        'units_total': 6,
        'units_moved': 4,
        'moved_pct': 0.66,
        'resupply_attempts': 3,
        'resupply_successes': 2,
        'total_targets_analyzed': 11,
        'dynamic_reassignments': 1,
        'coordination_failures': 0,
    })
    print("✅ log_commander_turn → wydajnosc_ai")

    # Walidacja plików
    today = datetime.now().strftime('%Y%m%d')
    base = Path(session_dir) / 'ai_commander_zaawansowany'
    tactical = base / 'akcje_taktyczne' / f'akcje_taktyczne_{today}.csv'
    strategic = base / 'decyzje_strategiczne' / f'decyzje_strategiczne_{today}.csv'
    perf = base / 'wydajnosc_ai' / f'wydajnosc_ai_{today}.csv'

    ok_tactical = tactical.exists()
    ok_strategic = strategic.exists()
    ok_perf = perf.exists()

    print(f"📄 Akcje taktyczne:      {tactical} → {'OK' if ok_tactical else 'MISSING'}")
    print(f"📄 Decyzje strategiczne: {strategic} → {'OK' if ok_strategic else 'MISSING'}")
    print(f"📄 Wydajność AI:         {perf} → {'OK' if ok_perf else 'MISSING'}")

    if ok_tactical and ok_strategic and ok_perf:
        print("🎉 Smoke test mapowania zaliczony")
        sys.exit(0)
    else:
        print("⚠️ Smoke test mapowania częściowy")
        sys.exit(2)

except Exception as e:
    print(f"❌ Smoke test error: {e}")
    sys.exit(2)
