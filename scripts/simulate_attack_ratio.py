"""Symulacja rozkładu nowego współczynnika ataku AI.

Skrypt generuje losowe pary jednostek (atakujący vs obrońca) na podstawie
centralnego modelu balansu i oblicza wartość ratio według projektowanego
wzoru opartego na spodziewanych obrażeniach. Wynik to rozkład procentowy
względem progów decyzyjnych (≥1.10, ≥1.00, ≥0.90, ≥0.75).

Uruchomienie:
    python scripts/simulate_attack_ratio.py --samples 100
"""
from __future__ import annotations

import argparse
import random
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, Iterable, List, Sequence, Tuple

import sys


PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from balance.model import ALLOWED_SUPPORT, BASE_STATS, SIZE_MULTIPLIER, compute_token

NATIONS = ("Polska", "Niemcy")
UNIT_TYPES: Tuple[str, ...] = tuple(BASE_STATS.keys())
UNIT_SIZES: Tuple[str, ...] = tuple(SIZE_MULTIPLIER.keys())
TERRAIN_DEFENSE = (0, 1, 2, 3)


@dataclass
class UnitSample:
    nation: str
    unit_type: str
    unit_size: str
    upgrades: Tuple[str, ...]
    attack_value: int
    attack_range: int
    defense_value: int
    combat_value: int

    @property
    def max_cv(self) -> int:
        return max(1, self.combat_value)


def choose_upgrades(unit_type: str, rng: random.Random) -> List[str]:
    allowed = ALLOWED_SUPPORT.get(unit_type, [])
    if not allowed:
        return []
    # Niewielka szansa na każdy element – traktujemy jako ewentualne przydziały wsparcia liniowego.
    selected: List[str] = []
    for name in allowed:
        # Artyleria polowa w roli transportu/wsparcia nie dodaje bezpośrednio siły ognia w ratio,
        # więc ograniczamy się do wsparcia piechoty / obserwatorów.
        if "artyler" in name.lower():
            continue
        if rng.random() < 0.25:
            selected.append(name)
    return selected


def build_unit_sample(unit_type: str, unit_size: str, nation: str, rng: random.Random) -> UnitSample:
    upgrades = tuple(choose_upgrades(unit_type, rng))
    stats = compute_token(unit_type, unit_size, nation, list(upgrades))
    return UnitSample(
        nation=nation,
        unit_type=unit_type,
        unit_size=unit_size,
        upgrades=upgrades,
        attack_value=stats.attack_value,
        attack_range=stats.attack_range,
        defense_value=stats.defense_value,
        combat_value=stats.combat_value,
    )


def sample_units(rng: random.Random, *, samples: int) -> Iterable[Tuple[UnitSample, UnitSample, Dict[str, float]]]:
    for _ in range(samples):
        attacker = build_unit_sample(rng.choice(UNIT_TYPES), rng.choice(UNIT_SIZES), rng.choice(NATIONS), rng)
        defender = build_unit_sample(rng.choice(UNIT_TYPES), rng.choice(UNIT_SIZES), rng.choice(NATIONS), rng)
        attacker_health = rng.uniform(0.65, 1.0)
        defender_health = rng.uniform(0.6, 1.0)
        attacker_fuel = rng.uniform(0.55, 1.0)
        detection_level = rng.uniform(0.4, 1.0)
        terrain = rng.choice(TERRAIN_DEFENSE)
        counterattack_possible = defender.attack_range >= 1 and rng.random() < (0.65 if defender.attack_range >= attacker.attack_range else 0.45)
        context = {
            "attacker_health": attacker_health,
            "defender_health": defender_health,
            "attacker_fuel": attacker_fuel,
            "detection": detection_level,
            "terrain": terrain,
            "counterattack": counterattack_possible,
        }
        yield attacker, defender, context


def compute_attack_snapshot(attacker: UnitSample, defender: UnitSample, context: Dict[str, float]) -> Dict[str, float | bool]:
    # Bazowa moc ataku (wartość ataku po wsparciach, jeśli są bezpośrednio zintegrowane z żetonem).
    base_attack = max(1.0, attacker.attack_value)
    # Zdrowie (combat value jako HP) – im bardziej uszkodzona jednostka, tym mniejsza skuteczność.
    health_factor = 0.65 + 0.35 * context["attacker_health"]
    # Paliwo ogranicza ofensywę, więc traktujemy niski poziom jako karę.
    fuel_factor = 0.7 + 0.3 * context["attacker_fuel"]
    # Delikatny bonus za większy zasięg – łatwiejsze ustawienie ognia.
    range_factor = 1.0 + 0.05 * max(0, attacker.attack_range - 1)
    effective_attack = base_attack * health_factor * fuel_factor * range_factor

    # Obrona uwzględnia teren oraz aktualne zdrowie obrońcy (mniej HP = słabsza odporność).
    terrain_bonus = context["terrain"] * 0.8  # 0.8 odpowiada około 20% wzrostu odporności na jeden poziom terenu.
    base_defense = max(1.0, defender.defense_value + terrain_bonus)
    defense_health_factor = 0.55 + 0.45 * context["defender_health"]
    effective_defense = base_defense * defense_health_factor

    # Ryzyko kontrataku zwiększa próg opłacalności – traktujemy je jak dodatkową "obronę".
    counterattack = context["counterattack"]
    counter_power = 0.0
    counter_defense_add = 0.0
    if counterattack:
        counter_power = max(0.0, defender.attack_value) * (0.5 + 0.5 * context["defender_health"])
        counter_defense_add = counter_power * 0.35
        effective_defense += counter_defense_add

    # Niższy poziom detekcji zmniejsza pewność skuteczności ostrzału.
    detection_penalty = 0.8 + 0.2 * context["detection"]  # 0.8 przy zerowej wiedzy, 1.0 przy pełnej

    ratio = (effective_attack / max(1.0, effective_defense)) * detection_penalty

    # Szacowane straty – traktujemy effective_attack jako bazę obrażeń modyfikowaną przez detekcję.
    # Kontratak (jeśli występuje) już został przeskalowany przez 0.35, więc używamy tej samej wartości.
    estimated_defender_loss = effective_attack * detection_penalty
    estimated_attacker_loss = counter_defense_add

    defender_cv = max(1.0, defender.combat_value)
    attacker_cv = max(1.0, attacker.combat_value)

    return {
        "ratio": ratio,
        "ratio_base": effective_attack / max(1.0, effective_defense),
        "effective_attack": effective_attack,
        "effective_defense": effective_defense,
        "detection_penalty": detection_penalty,
        "estimated_defender_loss": estimated_defender_loss,
        "estimated_attacker_loss": estimated_attacker_loss,
        "defender_loss_pct": min(1.0, estimated_defender_loss / defender_cv),
        "attacker_loss_pct": min(1.0, estimated_attacker_loss / attacker_cv),
        "counterattack": counterattack,
    }


def bucket_ratio(value: float) -> str:
    if value >= 1.10:
        return ">=1.10"
    if value >= 1.00:
        return "[1.00,1.10)"
    if value >= 0.90:
        return "[0.90,1.00)"
    if value >= 0.75:
        return "[0.75,0.90)"
    return "<0.75"


def run_simulation(samples: int, seed: int | None = None) -> None:
    rng = random.Random(seed)
    totals = {
        ">=1.10": 0,
        "[1.00,1.10)": 0,
        "[0.90,1.00)": 0,
        "[0.75,0.90)": 0,
        "<0.75": 0,
    }
    ratios: List[float] = []
    loss_sums = {
        "attacker": 0.0,
        "defender": 0.0,
        "attacker_pct": 0.0,
        "defender_pct": 0.0,
    }
    examples: List[Tuple[float, UnitSample, UnitSample, Dict[str, float]]] = []

    for attacker, defender, context in sample_units(rng, samples=samples):
        metrics = compute_attack_snapshot(attacker, defender, context)
        ratio = metrics["ratio"]
        ratios.append(ratio)
        totals[bucket_ratio(ratio)] += 1
        loss_sums["attacker"] += metrics["estimated_attacker_loss"]
        loss_sums["defender"] += metrics["estimated_defender_loss"]
        loss_sums["attacker_pct"] += metrics["attacker_loss_pct"]
        loss_sums["defender_pct"] += metrics["defender_loss_pct"]
        if len(examples) < 5:
            examples.append((ratio, attacker, defender, context))

    print(f"Próbek: {samples}")
    print("Rozkład względem progów:")
    for bucket, count in totals.items():
        pct = (count / samples) * 100
        print(f"  {bucket:>9}: {count:3d} ({pct:5.1f}%)")

    if ratios:
        avg = sum(ratios) / len(ratios)
        hi = max(ratios)
        lo = min(ratios)
        print(f"\nŚrednie ratio: {avg:.3f} | min: {lo:.3f} | max: {hi:.3f}")

    if samples:
        avg_attacker_loss = loss_sums["attacker"] / samples
        avg_defender_loss = loss_sums["defender"] / samples
        avg_attacker_pct = (loss_sums["attacker_pct"] / samples) * 100
        avg_defender_pct = (loss_sums["defender_pct"] / samples) * 100
        print("\nSzacowane średnie straty na starcie:")
        print(f"  Atakujący: {avg_attacker_loss:.2f} CV (~{avg_attacker_pct:.1f}% maksymalnego CV)")
        print(f"  Obrońca:   {avg_defender_loss:.2f} CV (~{avg_defender_pct:.1f}% maksymalnego CV)")

    print("\nPrzykładowe pary (ratio, atakujący -> obrońca):")
    for ratio, attacker, defender, ctx in examples:
        atk_name = f"{attacker.nation} {attacker.unit_type} {attacker.unit_size}"
        def_name = f"{defender.nation} {defender.unit_type} {defender.unit_size}"
        print(f"  {ratio:.3f}: {atk_name} → {def_name}")
        print(
            f"     atk[{attacker.attack_value}] rng[{attacker.attack_range}] fuel={ctx['attacker_fuel']:.2f} det={ctx['detection']:.2f} | "
            f"def[{defender.defense_value}] ctr_atk[{defender.attack_value}] teren={ctx['terrain']}"
        )


def parse_args(argv: Sequence[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Symulacja rozkładu ratio AI")
    parser.add_argument("--samples", type=int, default=80, help="Liczba losowych par do analizy")
    parser.add_argument("--seed", type=int, default=None, help="Opcjonalny seed generatora")
    return parser.parse_args(argv)


if __name__ == "__main__":
    args = parse_args()
    run_simulation(samples=args.samples, seed=args.seed)
