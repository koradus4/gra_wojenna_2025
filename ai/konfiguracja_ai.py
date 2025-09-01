"""Centralne stałe / progi AI (wydzielone).
Docelowo importowane przez inne moduły.
"""
from __future__ import annotations

# Heurystyki rotacji garnizonów
EARLY_ROTATION_THRESHOLD_RATIO = 0.25

# Bonusy wolnych keypointów
FREE_KEYPOINT_VALUE_DISTANCE_FACTOR = 1.2
FREE_HIGH_VALUE_BONUS_MULTIPLIER = 2.5
FREE_MED_VALUE_BONUS_MULTIPLIER = 1.6

# Log / diagnostyka
HEX_MISSING_LOG_PREFIX = "[AI HEX] HEX_MISSING"

__all__ = [
    'EARLY_ROTATION_THRESHOLD_RATIO',
    'FREE_KEYPOINT_VALUE_DISTANCE_FACTOR',
    'FREE_HIGH_VALUE_BONUS_MULTIPLIER',
    'FREE_MED_VALUE_BONUS_MULTIPLIER',
    'HEX_MISSING_LOG_PREFIX'
]
