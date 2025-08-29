import pytest

try:
    import tkinter as tk
except Exception:  # brak tkinter => pomijamy test
    tk = None

@pytest.mark.skipif(not tk, reason="Tkinter not available")
def test_army_creator_preview_basic():
    from edytory.prototyp_kreator_armii import ArmyCreatorStudio
    root = tk.Tk(); root.withdraw()
    app = ArmyCreatorStudio(root)
    app.army_size.set(8)
    app.army_budget.set(400)
    preview = app.generate_balanced_army_preview(8, 400)
    assert 0 < len(preview) <= 8
    total_cost = sum(u['cost'] for u in preview)
    assert total_cost <= 400
    final = app.generate_final_army(8, 400)
    assert len(final) == len(preview)
    keys = {"name","nation","unit_type","movement_points"}
    assert keys.issubset(final[0].keys())
    root.destroy()
