import importlib, sys, os

# Dodaj root projektu do sys.path
ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)

errors = []

for mod in ["ai.ai_commander", "ai.ruch_jednostek", "ai.okupacja_punktow", "ai.grupowanie_ai", "ai.wybor_celow"]:
    try:
        m = importlib.import_module(mod)
        print(f"OK import {mod}")
    except Exception as e:
        errors.append(f"FAIL {mod}: {e}")

# Sprawdź delegację
try:
    from ai import ai_commander as ac
    from ai import ruch_jednostek as rj
    if getattr(ac.choose_movement_mode, '__module__', '').endswith('ai_commander'):
        print("choose_movement_mode deleguje ->", rj.choose_movement_mode.__module__)
except Exception as e:
    errors.append(f"Delegation check failed: {e}")

if errors:
    print("=== ERRORS ===")
    for e in errors:
        print(e)
    sys.exit(1)
else:
    print("All imports OK")
