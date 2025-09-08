"""Czyste funkcje oceny / priorytetyzacji punktów kluczowych AI (po polsku)."""
from __future__ import annotations

def compute_keypoint_priority(distance: int, value: float, dist_exponent: float) -> float:
    """Nowa formuła: dystans wiodący, wartość drugorzędna.
    priority = (distance_score * 100) + (value * modifier)
    gdzie distance_score spada wykładniczo z dystansem
    """
    if value <= 0:
        return 0.0
    d = max(distance, 1)
    try:
        # Dystans wiodący: im bliżej, tym wyższy score
        distance_score = 100.0 / (d ** dist_exponent)
        # Wartość jako modyfikator (nie mnożnik)
        value_modifier = value * 0.1  # Znacznie mniejszy wpływ niż wcześniej
        return distance_score + value_modifier
    except Exception:
        return 50.0 + (value * 0.1)

def apply_free_point_bonus(base_score: float, value: float, high_mult: float, med_mult: float) -> float:
    """Bonusy dla wolnych punktów - ale mniejsze niż wcześniej."""
    if value >= 120:
        return base_score + (base_score * 0.3)  # +30% zamiast x2.5
    if value >= 70:
        return base_score + (base_score * 0.15)  # +15% zamiast x1.6
    return base_score

def apply_allied_penalty(score: float, occupied_by_ally: bool) -> float:
    """Kara tylko za okupację przez sojusznika (nie wroga).
    Uczciwa gra: AI nie może widzieć jednostek wroga jak człowiek.
    """
    if occupied_by_ally:
        score *= 0.5  # 50% kary za punkt zajęty przez sojusznika
    return score
