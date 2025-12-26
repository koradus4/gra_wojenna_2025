import math
import pytest

from core.tura import get_day_number, get_day_phase
from engine.action_refactored_clean import VisionService


def test_day_number_and_phase_mapping():
    # 1..6 -> dzien 1; 7 -> dzien 2
    assert get_day_number(1) == 1
    assert get_day_number(6) == 1
    assert get_day_number(7) == 2

    assert get_day_phase(1) == "rano"
    assert get_day_phase(2) == "dzień"
    assert get_day_phase(3) == "dzień"
    assert get_day_phase(4) == "wieczór"
    assert get_day_phase(5) == "noc"
    assert get_day_phase(6) == "noc"


def test_detection_multiplier_by_phase(monkeypatch):
    # Stub current turn via turn_context
    from utils.turn_context import set_current_turn

    # Załóżmy sight=4 i odległość=2 – baza bez mnożnika
    base = VisionService.calculate_detection_level(2, 4)

    # rano/dzień: 1.0x
    set_current_turn(1)  # rano
    d_morning = VisionService.calculate_detection_level(2, 4)
    set_current_turn(2)  # dzień
    d_day = VisionService.calculate_detection_level(2, 4)

    # wieczór: 0.9x
    set_current_turn(4)
    d_evening = VisionService.calculate_detection_level(2, 4)

    # noc: 0.7x
    set_current_turn(5)
    d_night = VisionService.calculate_detection_level(2, 4)

    # Spodziewane relacje (z tolerancją numeryczną)
    assert math.isclose(d_morning, base, rel_tol=1e-6)
    assert math.isclose(d_day, base, rel_tol=1e-6)
    assert d_evening == pytest.approx(base * 0.9, rel=1e-6)
    assert d_night == pytest.approx(base * 0.7, rel=1e-6)
