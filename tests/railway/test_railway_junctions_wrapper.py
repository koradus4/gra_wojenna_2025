from pathlib import Path
import sys
sys.path.insert(0, str(Path(__file__).parent.parent / "edytory"))
import test_railway_junctions as jun_mod

def test_junctions():
    assert jun_mod.test_junction()