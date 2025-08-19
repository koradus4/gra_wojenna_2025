import os
import pytest

# Globalne pominięcie testów GUI w środowisku headless / CI.
# Usuń ten plik lub ustaw zmienną środowiskową RUN_GUI_TESTS=1 aby włączyć.
if os.environ.get("RUN_GUI_TESTS") != "1":
    pytest.skip("Pomijam testy GUI (ustaw RUN_GUI_TESTS=1 aby uruchomić)", allow_module_level=True)
