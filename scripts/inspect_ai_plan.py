"""Uruchomienie:  python scripts/inspect_ai_plan.py
Pokazuje jakie jednostki AI planuje kupić przy dużym budżecie.
"""
import os, sys
# Zapewnij, że katalog główny projektu jest w sys.path (uruchamianie z PowerShell może mieć pusty sys.path[0])
PROJECT_ROOT = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.dirname(PROJECT_ROOT)
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

from ai.ai_general import AIGeneral

class DummyCommander:
    def __init__(self, i):
        self.id = i
        self.nation = 'Polska'
        self.role = 'Dowódca'

def main():
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument('-b','--budget', type=int, default=1000)
    parser.add_argument('-m','--max', type=int, default=30, help='maksymalna liczba zakupów')
    args = parser.parse_args()

    a = AIGeneral('polish')
    commanders = [DummyCommander(1), DummyCommander(2)]
    plans = a.plan_purchases(args.budget, commanders, max_purchases=args.max)
    print('LICZBA PLANÓW:', len(plans))
    uniq = sorted({(p['type'], p['size']) for p in plans})
    print('UNIKALNE (typ, rozmiar):', uniq)
    print('TYPY:', sorted({t for t,_ in uniq}))
    # Sprawdź brakujące kombinacje względem PRICE_DEFAULTS
    from core.unit_factory import PRICE_DEFAULTS
    expected = {(t, s) for s, mapping in PRICE_DEFAULTS.items() for t in mapping.keys()}
    missing = sorted(expected - set(uniq))
    if missing:
        print('BRAKUJĄCE (typ,rozmiar):', missing)
    else:
        print('✅ Pokryto wszystkie kombinacje dostępne w PRICE_DEFAULTS (limity budżetu/zakupów uwzględnione)')
    for p in plans:
        print(f" - {p['type']} {p['size']} koszt={p['cost']} supports={p.get('supports')}")

if __name__ == '__main__':
    main()
