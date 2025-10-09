import sys
from pathlib import Path

# Dodaj główny folder projektu do ścieżki
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

import tkinter as tk
from collections import Counter
import statistics

tk_root = tk.Tk()
tk_root.withdraw()

from edytory.prototyp_kreator_armii import ArmyCreatorStudio
app = ArmyCreatorStudio(tk_root)

results = []
for size, budget in [(20, 1000), (20, 1200), (15, 900)]:
    for _ in range(3):
        preview = app.generate_balanced_army_preview(size, budget)
        cats = Counter(app.unit_templates[u['unit_type']]['category'] for u in preview)
        results.append({
            'size': size,
            'budget': budget,
            'total': len(preview),
            'infantry': cats.get('INFANTRY', 0),
            'tanks': cats.get('TANKS', 0),
            'supply': cats.get('SUPPLY', 0),
            'cav_recon': cats.get('CAVALRY_RECON', 0),
            'artillery': cats.get('ARTILLERY', 0)
        })

print('=== WYNIKI TESTU GENEROWANIA ===')
for r in results:
    ratio = r['tanks'] / r['infantry'] if r['infantry'] > 0 else 0
    print(f"size={r['size']:2} budget={r['budget']:4} -> total={r['total']:2} | P={r['infantry']:2} T={r['tanks']:2} K+R={r['cav_recon']:2} A={r['artillery']:2} Z={r['supply']:2} | T/P={ratio:.2f}")

ratios = [r['tanks'] / r['infantry'] for r in results if r['infantry'] > 0]
zeros = sum(1 for r in results if r['tanks'] == 0 and r['infantry'] > 0)

print('\n=== PODSUMOWANIE ===')
print(f"Min T/P ratio: {min(ratios):.2f}")
print(f"Max T/P ratio: {max(ratios):.2f}")
print(f"Avg T/P ratio: {statistics.mean(ratios):.2f}")
print(f"Generacji bez czołgów: {zeros}/{len(results)}")

tk_root.destroy()
