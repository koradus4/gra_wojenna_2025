"""Centralny moduł balansu żetonów.
Używany przez: Token Editor, Kreator Armii, AI zakupujące jednostki.
Minimalny, stabilny interfejs.
"""
from __future__ import annotations
from dataclasses import dataclass
from typing import Dict, List, Optional
import math
import random

# ================= KONFIGURACJA BAZOWA =================

BASE_STATS: Dict[str, Dict[str, int]] = {
    # movement, attack_range, attack_value, combat_value, defense_value, sight
    "P":  {"movement": 3, "attack_range": 1, "attack_value": 8,  "combat_value": 8,  "defense_value": 10, "sight": 3},
    "K":  {"movement": 6, "attack_range": 1, "attack_value": 6,  "combat_value": 6,  "defense_value": 8,  "sight": 5},
    "TL": {"movement": 5, "attack_range": 1, "attack_value": 10, "combat_value": 10, "defense_value": 12, "sight": 3},
    "TŚ": {"movement": 4, "attack_range": 2, "attack_value": 14, "combat_value": 14, "defense_value": 16, "sight": 3},
    "TC": {"movement": 3, "attack_range": 2, "attack_value": 18, "combat_value": 18, "defense_value": 22, "sight": 3},
    "TS": {"movement": 5, "attack_range": 1, "attack_value": 8,  "combat_value": 8,  "defense_value": 10, "sight": 4},
    "AL": {"movement": 3, "attack_range": 3, "attack_value": 12, "combat_value": 6,  "defense_value": 6,  "sight": 4},
    "AC": {"movement": 2, "attack_range": 4, "attack_value": 18, "combat_value": 8,  "defense_value": 8,  "sight": 5},
    "AP": {"movement": 2, "attack_range": 2, "attack_value": 10, "combat_value": 6,  "defense_value": 8,  "sight": 4},
    "Z":  {"movement": 6, "attack_range": 1, "attack_value": 4,  "combat_value": 4,  "defense_value": 6,  "sight": 6},
    "D":  {"movement": 4, "attack_range": 1, "attack_value": 6,  "combat_value": 8,  "defense_value": 12, "sight": 5},
}

SIZE_MULTIPLIER = {"Pluton": 1.0, "Kompania": 1.4, "Batalion": 1.8}

UPGRADES: Dict[str, Dict[str, int]] = {
    # movement_delta może być ujemne lub dodatnie; range_bonus stosujemy najwyższy; reszta kumulacja
    "drużyna granatników": {"movement_delta": -1, "range_bonus": 1, "attack_delta": 2, "combat_delta": 0, "defense_delta": 1, "maintenance_delta": 1, "cost_delta": 10},
    "sekcja km.ppanc":    {"movement_delta": -1, "range_bonus": 1, "attack_delta": 2, "combat_delta": 0, "defense_delta": 2, "maintenance_delta": 2, "cost_delta": 10},
    "sekcja ckm":         {"movement_delta": -1, "range_bonus": 1, "attack_delta": 2, "combat_delta": 0, "defense_delta": 2, "maintenance_delta": 2, "cost_delta": 10},
    "przodek dwukonny":    {"movement_delta": 2,  "range_bonus": 0, "attack_delta": 0, "combat_delta": 0, "defense_delta": 0, "maintenance_delta": 1, "cost_delta": 5},
    "sam. ciezarowy Fiat 621": {"movement_delta": 5, "range_bonus": 0, "attack_delta": 0, "combat_delta": 0, "defense_delta": 0, "maintenance_delta": 3, "cost_delta": 8},
    "sam.ciezarowy Praga Rv": {"movement_delta": 5, "range_bonus": 0, "attack_delta": 0, "combat_delta": 0, "defense_delta": 0, "maintenance_delta": 3, "cost_delta": 8},
    "ciagnik altyleryjski": {"movement_delta": 3, "range_bonus": 0, "attack_delta": 0, "combat_delta": 0, "defense_delta": 0, "maintenance_delta": 4, "cost_delta": 12},
    "obserwator":          {"movement_delta": 0, "range_bonus": 0, "attack_delta": 0, "combat_delta": 0, "defense_delta": 0, "maintenance_delta": 1, "cost_delta": 5},
}

QUALITY_LEVELS = {"low": 0.9, "standard": 1.0, "elite": 1.1}

# Doktryny mogą modyfikować finalne statystyki / koszt (placeholder)
DOCTRINES = {
    # quality_bias – dodawane do quality_factor przed zaokrągleniem
    # attack_bonus/defense_bonus/combat_bonus – procent (0.05 = +5%) stosowany po przeliczeniu rozmiaru
    "Polska": {"quality_bias": 0.0,  "attack_bonus": 0.00, "defense_bonus": 0.00, "combat_bonus": 0.00},
    "Niemcy": {"quality_bias": 0.02, "attack_bonus": 0.03, "defense_bonus": 0.00, "combat_bonus": 0.02},
}

_BALANCE_RANDOM = random.Random()

def set_balance_seed(seed: int):
    """Opcjonalny seed dla przyszłych elementów losowych (aktualnie brak losowości)."""
    _BALANCE_RANDOM.seed(seed)

UNIT_TYPE_FULL = {
    "P": "Piechota",
    "K": "Kawaleria",
    "TC": "Czołg ciężki",
    "TŚ": "Czołg średni",
    "TL": "Czołg lekki",
    "TS": "Sam. pancerny",
    "AC": "Artyleria ciężka",
    "AL": "Artyleria lekka",
    "AP": "Artyleria plot",
    "Z": "Zaopatrzenie",
    "D": "Dowództwo",
    "G": "Generał",
}

UNIT_SIZE_SYMBOL = {"Pluton": "***", "Kompania": "I", "Batalion": "II"}

def build_unit_names(nation: str, unit_type: str, unit_size: str) -> dict:
    full_type = UNIT_TYPE_FULL.get(unit_type, unit_type)
    symbol = UNIT_SIZE_SYMBOL.get(unit_size, "")
    full_name = f"{nation} {full_type} {unit_size} {symbol}".strip()
    label = full_name  # domyślnie to samo; GUI może podmienić
    return {"label": label, "unit_full_name": full_name}

@dataclass
class ComputedStats:
    movement: int
    attack_range: int
    attack_value: int
    combat_value: int
    defense_value: int
    sight: int
    maintenance: int
    base_cost: int
    total_cost: int
    applied_upgrades: List[str]

# ================== FUNKCJE RDZENIOWE ==================

def compute_base_stats(unit_type: str, unit_size: str, quality: str = "standard", nation: str | None = None) -> Dict[str, int]:
    base = BASE_STATS.get(unit_type, BASE_STATS["P"]).copy()
    mult = SIZE_MULTIPLIER.get(unit_size, 1.0)
    # skalujemy tylko wartości bojowe i obronę
    for k in ["attack_value", "combat_value", "defense_value"]:
        base[k] = int(round(base[k] * mult))
    # quality factor bez losowości (stabilnie)
    qf = QUALITY_LEVELS.get(quality, 1.0)
    if nation in DOCTRINES:
        qf += DOCTRINES[nation].get("quality_bias", 0.0)
    for k in ["attack_value", "combat_value", "defense_value"]:
        base[k] = max(1, int(round(base[k] * qf)))
    # Doktrynalne bonusy procentowe
    if nation in DOCTRINES:
        d = DOCTRINES[nation]
        if d.get("attack_bonus"):
            base["attack_value"] = int(round(base["attack_value"] * (1 + d["attack_bonus"])))
        if d.get("defense_bonus"):
            base["defense_value"] = int(round(base["defense_value"] * (1 + d["defense_bonus"])))
        if d.get("combat_bonus"):
            base["combat_value"] = int(round(base["combat_value"] * (1 + d["combat_bonus"])))
    return base

def estimate_base_cost(unit_type: str, unit_size: str, stats: Dict[str, int]) -> int:
    # Prosty koszt: waga * suma głównych parametrów
    weight_type = {
        "P": 1.0, "K": 1.1, "TL": 1.3, "TŚ": 1.5, "TC": 1.8, "TS": 1.2,
        "AL": 1.2, "AC": 1.5, "AP": 1.1, "Z": 0.8, "D": 1.4
    }.get(unit_type, 1.0)
    size_factor = {"Pluton": 0.8, "Kompania": 1.0, "Batalion": 1.3}.get(unit_size, 1.0)
    core = stats["attack_value"] + stats["combat_value"] + stats["defense_value"]
    base_cost = int(round(core * weight_type * size_factor / 3))  # dzielimy by skala była umiarkowana
    return max(5, base_cost)

def apply_upgrades(stats: Dict[str, int], upgrades: List[str]) -> Dict[str, int]:
    final_stats = stats.copy()
    max_range_bonus = 0
    movement_penalty_applied = False
    for up in upgrades:
        data = UPGRADES.get(up)
        if not data:
            continue
        # ruch: jedna kara -1 max, bonusy kumulują
        mv = data.get("movement_delta", 0)
        if mv < 0:
            if not movement_penalty_applied:
                final_stats["movement"] = max(1, final_stats["movement"] + mv)
                movement_penalty_applied = True
        elif mv > 0:
            final_stats["movement"] += mv
        final_stats["attack_value"] += data.get("attack_delta", 0)
        final_stats["combat_value"] += data.get("combat_delta", 0)
        final_stats["defense_value"] += data.get("defense_delta", 0)
        max_range_bonus = max(max_range_bonus, data.get("range_bonus", 0))
    if max_range_bonus:
        final_stats["attack_range"] += max_range_bonus
    # bezpieczeństwo
    for k in ["attack_value", "combat_value", "defense_value", "movement"]:
        final_stats[k] = max(1, final_stats[k])
    return final_stats

def maintenance_from_cost(total_cost: int, upgrades: List[str]) -> int:
    # bazowo proporcjonalne, z niewielką premią za liczbę upgradów
    base = max(1, math.ceil(total_cost / 18))
    return base + max(0, len(upgrades)//2)

def total_cost_with_upgrades(base_cost: int, upgrades: List[str]) -> int:
    extra = 0
    for up in upgrades:
        extra += UPGRADES.get(up, {}).get("cost_delta", 0)
    return base_cost + extra

def compute_token(unit_type: str, unit_size: str, nation: str, upgrades: Optional[List[str]] = None,
                  quality: str = "standard") -> ComputedStats:
    if upgrades is None:
        upgrades = []
    base_stats = compute_base_stats(unit_type, unit_size, quality, nation=nation)
    base_cost = estimate_base_cost(unit_type, unit_size, base_stats)
    stats_after = apply_upgrades(base_stats, upgrades)
    total_cost = total_cost_with_upgrades(base_cost, upgrades)
    maintenance = maintenance_from_cost(total_cost, upgrades)
    return ComputedStats(
        movement=stats_after["movement"],
        attack_range=stats_after["attack_range"],
        attack_value=stats_after["attack_value"],
        combat_value=stats_after["combat_value"],
        defense_value=stats_after["defense_value"],
        sight=stats_after["sight"],
        maintenance=maintenance,
        base_cost=base_cost,
        total_cost=total_cost,
        applied_upgrades=list(upgrades),
    )

# Prosty test manualny
if __name__ == "__main__":
    print(compute_token("P", "Pluton", "Polska", ["drużyna granatników"]))
