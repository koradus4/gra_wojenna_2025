#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Smoketest loggera walk (walka_ai): generuje pojedynczy wpis z CV przed/po.
"""

import sys
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(BASE_DIR))


def smoketest_walka():
    try:
        from utils.session_manager import SessionManager
        from utils.ai_commander_logger_zaawansowany import ZaawansowanyLoggerAI
        from utils.turn_context import set_current_turn, clear_current_turn

        print("🚀 Smoketest walka_ai...")

        session_manager = SessionManager()
        session_dir = session_manager.get_current_session_dir()
        logger = ZaawansowanyLoggerAI(session_dir)

        # ustaw kontekst tury dla automatycznego wstrzyknięcia
        set_current_turn(1)

        dane = {
            'nation': 'TESTOWA',
            'attacker_id': 'A-1',
            'defender_id': 'D-2',
            'attacker_cv_before': 7,
            'attacker_cv_after': 5,
            'defender_cv_before': 6,
            'defender_cv_after': 3,
            'outcome': 'ATTACKER_ADVANCES',
            'hex_q': 10,
            'hex_r': 15,
            'notes': 'smoketest'
        }
        logger.loguj_walke(dane)

        # weryfikacja minimalna: katalog istnieje i przynajmniej jeden csv
        walka_dir = session_dir / 'ai_commander_zaawansowany' / 'walka_ai'
        assert walka_dir.exists(), 'Brak katalogu walka_ai'
        csv_files = list(walka_dir.glob('*.csv'))
        assert csv_files, 'Brak plików CSV w walka_ai po smoketeście'
        print(f"✅ Wpis zapisany do: {csv_files[0]}")

    finally:
        try:
            clear_current_turn()
        except Exception:
            pass


if __name__ == '__main__':
    smoketest_walka()
#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Smoketest loggera walk (walka_ai): generuje pojedynczy wpis z CV przed/po.
"""

import sys
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(BASE_DIR))


def smoketest_walka():
    try:
        from utils.session_manager import SessionManager
        from utils.ai_commander_logger_zaawansowany import ZaawansowanyLoggerAI
        from utils.turn_context import set_current_turn, clear_current_turn

        print("🚀 Smoketest walka_ai...")

        session_manager = SessionManager()
        session_dir = session_manager.get_current_session_dir()
        logger = ZaawansowanyLoggerAI(session_dir)

        # ustaw kontekst tury dla automatycznego wstrzyknięcia
        set_current_turn(1)

        dane = {
            'nation': 'TESTOWA',
            'attacker_id': 'A-1',
            'defender_id': 'D-2',
            'attacker_cv_before': 7,
            'attacker_cv_after': 5,
            'defender_cv_before': 6,
            'defender_cv_after': 3,
            'outcome': 'ATTACKER_ADVANCES',
            'hex_q': 10,
            'hex_r': 15,
            'notes': 'smoketest'
        }
        logger.loguj_walke(dane)

        # weryfikacja minimalna: katalog istnieje i przynajmniej jeden csv
        walka_dir = session_dir / 'ai_commander_zaawansowany' / 'walka_ai'
        assert walka_dir.exists(), 'Brak katalogu walka_ai'
        csv_files = list(walka_dir.glob('*.csv'))
        assert csv_files, 'Brak plików CSV w walka_ai po smoketeście'
        print(f"✅ Wpis zapisany do: {csv_files[0]}")

    finally:
        try:
            clear_current_turn()
        except Exception:
            pass


if __name__ == '__main__':
    smoketest_walka()
