"""Czyste funkcje oceny / priorytetyzacji punktów kluczowych AI (po polsku)."""
from __future__ import annotations

def compute_keypoint_priority(value: float, enemy_distance: int, dist_exponent: float) -> float:
    if value <= 0:
        return 0.0
    d = max(enemy_distance, 1)
    try:
        return (value * 10.0) / (d ** dist_exponent)
    except Exception:
        return float(value)

def apply_free_point_bonus(base_score: float, value: float, high_mult: float, med_mult: float) -> float:
    if value >= 120:
        return base_score * high_mult
    if value >= 70:
        return base_score * med_mult
    return base_score

def apply_defended_penalty(score: float, occupied_by_me: bool, enemy_distance: int) -> float:
    if occupied_by_me:
        score *= 0.65
    return score
