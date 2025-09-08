import math
from ai.priorytety_ai import compute_keypoint_priority, apply_free_point_bonus, apply_allied_penalty


def test_compute_keypoint_priority_basic():
    # value rośnie -> score rośnie, większa odległość zmniejsza (przez d^exp)
    s1 = compute_keypoint_priority(100, 1, 1.0)
    s2 = compute_keypoint_priority(100, 5, 1.0)
    assert s1 > s2 > 0


def test_apply_free_point_bonus_thresholds():
    base = 10.0
    high = apply_free_point_bonus(base, 130, 2.0, 1.3)
    med = apply_free_point_bonus(base, 90, 2.0, 1.3)
    low = apply_free_point_bonus(base, 40, 2.0, 1.3)
    assert math.isclose(high, base * 2.0)
    assert math.isclose(med, base * 1.3)
    assert math.isclose(low, base)


def test_apply_allied_penalty():
    v1 = apply_allied_penalty(100, True)
    v2 = apply_allied_penalty(100, False)
    assert v1 < v2
