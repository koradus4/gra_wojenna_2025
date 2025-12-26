from pathlib import Path
import sys
sys.path.insert(0, str(Path(__file__).parent.parent / "edytory"))
import test_railway_generator as gen_mod

def test_generator_all():
    # Uruchom kompletny zestaw testów generatora z katalogu edytory
    assert gen_mod.run_all_tests()