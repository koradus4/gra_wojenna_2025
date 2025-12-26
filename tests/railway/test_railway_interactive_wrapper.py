from pathlib import Path
import sys
sys.path.insert(0, str(Path(__file__).parent.parent / "edytory"))
import test_railway_interactive as inter_mod

def test_interactive_all():
    assert inter_mod.test_basic_railway_generation()
    assert inter_mod.test_curved_railway()
    assert inter_mod.test_railway_path_simulation()