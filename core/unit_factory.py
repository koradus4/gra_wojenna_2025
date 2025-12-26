"""Wspólna fabryka jednostek: identyczne statystyki / koszty jak w token_shop.update_stats

Pozwala AI (i w przyszłości GUI) obliczać parametry jednostki z jednego źródła prawdy.
"""
from dataclasses import dataclass
from typing import List, Dict, Optional

# --- Dane bazowe (skopiowane z token_shop.update_stats) ---
RANGE_DEFAULTS = {
    "P": 1, "K": 1, "R": 1, "TC": 2, "TŚ": 2, "TL": 1, "TS": 2,
    "AC": 6, "AL": 4, "AP": 3, "Z": 1, "D": 0, "G": 0
}

MOVE_DEFAULTS = {
    "P": 2, "K": 4, "R": 6, "TC": 2, "TŚ": 3, "TL": 4, "TS": 5,
    "AC": 1, "AL": 2, "AP": 2, "Z": 3, "D": 2, "G": 2
}

ATTACK_DEFAULTS = {
    "Pluton": {"P": 2, "K": 2, "R": 2, "TC": 8, "TŚ": 6, "TL": 4, "TS": 3, "AC": 12, "AL": 8, "AP": 6, "Z": 1, "D": 0, "G": 0},
    "Kompania": {"P": 4, "K": 4, "R": 3, "TC": 15, "TŚ": 12, "TL": 8, "TS": 6, "AC": 24, "AL": 16, "AP": 12, "Z": 2, "D": 0, "G": 0},
    "Batalion": {"P": 6, "K": 6, "R": 5, "TC": 22, "TŚ": 18, "TL": 12, "TS": 9, "AC": 36, "AL": 24, "AP": 18, "Z": 3, "D": 0, "G": 0}
}

COMBAT_DEFAULTS = {
    "P__Pluton": 8, "P__Kompania": 15, "P__Batalion": 30,
    "K__Pluton": 6, "K__Kompania": 12, "K__Batalion": 24,
    "R__Pluton": 5, "R__Kompania": 10, "R__Batalion": 18,
    "TC__Pluton": 12, "TC__Kompania": 24, "TC__Batalion": 48,
    "TŚ__Pluton": 10, "TŚ__Kompania": 20, "TŚ__Batalion": 42,
    "TL__Pluton": 8, "TL__Kompania": 16, "TL__Batalion": 36,
    "TS__Pluton": 6, "TS__Kompania": 12, "TS__Batalion": 30,
    "AC__Pluton": 8, "AC__Kompania": 16, "AC__Batalion": 48,
    "AL__Pluton": 6, "AL__Kompania": 12, "AL__Batalion": 42,
    "AP__Pluton": 6, "AP__Kompania": 12, "AP__Batalion": 36,
    "Z__Pluton": 4, "Z__Kompania": 12, "Z__Batalion": 24,
    "D__Pluton": 3, "D__Kompania": 9, "D__Batalion": 18,
    "G__Pluton": 2, "G__Kompania": 6, "G__Batalion": 12,
}

DEFENSE_DEFAULTS = {
    "Pluton": {"P": 4, "K": 2, "R": 2, "TC": 8, "TŚ": 6, "TL": 4, "TS": 3, "AC": 2, "AL": 3, "AP": 3, "Z": 2, "D": 1, "G": 1},
    "Kompania": {"P": 8, "K": 4, "R": 3, "TC": 15, "TŚ": 12, "TL": 8, "TS": 6, "AC": 4, "AL": 6, "AP": 6, "Z": 4, "D": 2, "G": 2},
    "Batalion": {"P": 15, "K": 6, "R": 5, "TC": 22, "TŚ": 18, "TL": 12, "TS": 9, "AC": 6, "AL": 9, "AP": 9, "Z": 6, "D": 3, "G": 3},
}

MAINTENANCE_DEFAULTS = {
    "Pluton": {"P": 2, "K": 3, "R": 3, "TC": 8, "TŚ": 6, "TL": 4, "TS": 3, "AC": 4, "AL": 3, "AP": 3, "Z": 2, "D": 1, "G": 1},
    "Kompania": {"P": 4, "K": 6, "R": 3, "TC": 16, "TŚ": 12, "TL": 8, "TS": 6, "AC": 8, "AL": 6, "AP": 6, "Z": 4, "D": 2, "G": 2},
    "Batalion": {"P": 8, "K": 9, "R": 4, "TC": 24, "TŚ": 18, "TL": 12, "TS": 9, "AC": 12, "AL": 9, "AP": 9, "Z": 6, "D": 3, "G": 3},
}

PRICE_DEFAULTS = {
    "Pluton": {"P": 15, "K": 18, "R": 18, "TC": 40, "TŚ": 32, "TL": 25, "TS": 20, "AC": 35, "AL": 25, "AP": 20, "Z": 16, "D": 80, "G": 120},
    "Kompania": {"P": 30, "K": 36, "R": 34, "TC": 80, "TŚ": 64, "TL": 50, "TS": 40, "AC": 70, "AL": 50, "AP": 40, "Z": 32, "D": 80, "G": 120},
    "Batalion": {"P": 45, "K": 54, "R": 50, "TC": 120, "TŚ": 96, "TL": 75, "TS": 60, "AC": 105, "AL": 75, "AP": 60, "Z": 48, "D": 80, "G": 120},
}

SIGHT_DEFAULTS = {"P": 1, "K": 3, "R": 6, "TC": 2, "TŚ": 2, "TL": 2, "TS": 3, "AC": 2, "AL": 2, "AP": 2, "D": 4, "G": 6, "Z": 2}

SUPPORT_UPGRADES = {
    "drużyna granatników": {"movement": -1, "range": 1, "attack": 2, "combat": 0, "unit_maintenance": 1, "purchase": 10, "defense": 1},
    "sekcja km.ppanc": {"movement": -1, "range": 1, "attack": 2, "combat": 0, "unit_maintenance": 2, "purchase": 10, "defense": 2},
    "sekcja ckm": {"movement": -1, "range": 1, "attack": 2, "combat": 0, "unit_maintenance": 2, "purchase": 10, "defense": 2},
    "przodek dwukonny": {"movement": 2, "range": 0, "attack": 0, "combat": 0, "unit_maintenance": 1, "purchase": 5, "defense": 0},
    "sam. ciezarowy Fiat 621": {"movement": 5, "range": 0, "attack": 0, "combat": 0, "unit_maintenance": 3, "purchase": 8, "defense": 0},
    "sam.ciezarowy Praga Rv": {"movement": 5, "range": 0, "attack": 0, "combat": 0, "unit_maintenance": 3, "purchase": 8, "defense": 0},
    "ciagnik altyleryjski": {"movement": 3, "range": 0, "attack": 0, "combat": 0, "unit_maintenance": 4, "purchase": 12, "defense": 0},
    "obserwator": {"movement": 0, "range": 0, "attack": 0, "combat": 0, "unit_maintenance": 1, "purchase": 5, "defense": 0},
}

TRANSPORT_TYPES = [
    "przodek dwukonny",
    "sam. ciezarowy Fiat 621",
    "sam.ciezarowy Praga Rv",
    "ciagnik altyleryjski",
]

# Dozwolone wsparcia (kopiowane z token_shop)
ALLOWED_SUPPORT = {
    "P": ["drużyna granatników", "sekcja km.ppanc", "sekcja ckm", "przodek dwukonny", "sam. ciezarowy Fiat 621", "sam.ciezarowy Praga Rv"],
    "K": ["sekcja ckm"],
    "R": ["obserwator"],
    "TC": ["obserwator"],
    "TŚ": ["obserwator"],
    "TL": ["obserwator"],
    "TS": ["obserwator"],
    "AC": ["drużyna granatników", "sekcja ckm", "sekcja km.ppanc", "sam. ciezarowy Fiat 621", "sam.ciezarowy Praga Rv", "ciagnik altyleryjski", "obserwator"],
    "AL": ["drużyna granatników", "sekcja ckm", "sekcja km.ppanc", "przodek dwukonny", "sam. ciezarowy Fiat 621", "sam.ciezarowy Praga Rv", "ciagnik altyleryjski", "obserwator"],
    "AP": ["drużyna granatników", "sekcja ckm", "sekcja km.ppanc", "przodek dwukonny", "sam. ciezarowy Fiat 621", "sam.ciezarowy Praga Rv", "ciagnik altyleryjski", "obserwator"],
    "Z": ["drużyna granatników", "sekcja km.ppanc", "sekcja ckm", "obserwator"],
    "D": ["drużyna granatników", "sekcja km.ppanc", "sekcja ckm", "sam. ciezarowy Fiat 621", "sam.ciezarowy Praga Rv", "obserwator"],
    "G": ["drużyna granatników", "sekcja km.ppanc", "sekcja ckm", "sam. ciezarowy Fiat 621", "sam.ciezarowy Praga Rv", "obserwator"],
}

def base_price(unit_type: str, unit_size: str) -> int:
    return int(PRICE_DEFAULTS.get(unit_size, {}).get(unit_type, 0))


@dataclass
class UnitStats:
    move: int
    attack_range: int
    attack_value: int
    combat_value: int
    defense_value: int
    maintenance: int
    price: int
    sight: int

    def to_json_fragment(self) -> Dict[str, int]:
        return {
            "move": self.move,
            "attack": {"range": self.attack_range, "value": self.attack_value},
            "combat_value": self.combat_value,
            "defense_value": self.defense_value,
            "maintenance": self.maintenance,
            "price": self.price,
            "sight": self.sight,
        }


def compute_unit_stats(unit_type: str, unit_size: str, supports: Optional[List[str]] = None) -> UnitStats:
    """[DEPRECATED] Legacy algorytm (używany tylko jako fallback w GUI).

    PRZENIESIONE do balance.model.compute_token – nowe GUI / AI / testy powinny korzystać
    wyłącznie z centralnego modelu. Ten kod zostanie usunięty po migracji wszystkich
    odniesień. Zachowany tymczasowo aby nie przerwać istniejących zapisanych scenariuszy.

    Oblicza statystyki jednostki na podstawie baz i listy wsparć.

    Zasady (wierne token_shop.update_stats):
      1. Bazowe wartości z tabel.
      2. Jeden transport (pierwszy z TRANSPORT_TYPES na liście supports) – jego movement dodany od razu.
      3. Kara -1 do ruchu z pierwszego wsparcia dającego movement < 0 (nie dotyczy transportu) – tylko raz.
      4. Atak/combat/price/maintenance/defense sumują się ze wszystkich wsparć (poza movement wyjątek powyżej).
      5. Range – bierzemy najwyższy bonus range spośród wsparć (poza transportem; transport range zawsze 0).
      6. Maintenance/price/defense transportu doliczane dodatkowo po pętli (w token_shop jest efekt finalny – tam dodawane są też purchase+maintenance+defense transportu; movement już dodany na początku).
    """
    supports = supports or []

    move = int(MOVE_DEFAULTS.get(unit_type, 0))
    attack_range = int(RANGE_DEFAULTS.get(unit_type, 0))
    attack_value = int(ATTACK_DEFAULTS.get(unit_size, {}).get(unit_type, 0))
    combat_value = int(COMBAT_DEFAULTS.get(f"{unit_type}__{unit_size}", 0))
    defense_value = int(DEFENSE_DEFAULTS.get(unit_size, {}).get(unit_type, 0))
    maintenance = int(MAINTENANCE_DEFAULTS.get(unit_size, {}).get(unit_type, 0))
    price = int(PRICE_DEFAULTS.get(unit_size, {}).get(unit_type, 0))
    sight = int(SIGHT_DEFAULTS.get(unit_type, 0))

    # Transport (pierwszy występujący)
    transport = None
    for s in supports:
        if s in TRANSPORT_TYPES:
            transport = s
            break
    if transport:
        upg = SUPPORT_UPGRADES[transport]
        move += upg["movement"]

    movement_penalty_applied = False
    max_range_bonus = 0
    for s in supports:
        if s == transport:
            continue
        upg = SUPPORT_UPGRADES.get(s)
        if not upg:
            continue
        if upg["movement"] < 0 and not movement_penalty_applied:
            move -= 1
            movement_penalty_applied = True
        attack_value += upg["attack"]
        combat_value += upg["combat"]
        price += upg["purchase"]
        maintenance += upg["unit_maintenance"]
        max_range_bonus = max(max_range_bonus, upg["range"])
        defense_value += upg["defense"]

    if max_range_bonus > 0:
        attack_range += max_range_bonus

    if transport:
        t_upg = SUPPORT_UPGRADES[transport]
        maintenance += t_upg["unit_maintenance"]
        price += t_upg["purchase"]
        defense_value += t_upg["defense"]

    return UnitStats(
        move=move,
        attack_range=attack_range,
        attack_value=attack_value,
        combat_value=combat_value,
        defense_value=defense_value,
        maintenance=maintenance,
        price=price,
        sight=sight,
    )


def build_label_and_full_name(nation: str, unit_type: str, unit_size: str, commander_id: str) -> Dict[str, str]:
    """Zwraca label i unit_full_name dokładnie jak w token_shop.update_unit_names()."""
    nation_short = "PL" if nation == "Polska" else ("N" if nation == "Niemcy" else nation[:2].upper())
    label = f"nowy_{commander_id}_{nation_short}_{unit_type}_{unit_size}"
    unit_type_full = {
    "P": "Piechota",
    "K": "Kawaleria",
    "R": "Zwiad",
        "TC": "Czołg ciężki",
        "TŚ": "Czołg średni",
        "TL": "Czołg lekki",
        "TS": "Sam. pancerny",
        "AC": "Artyleria ciężka",
        "AL": "Artyleria lekka",
        "AP": "Artyleria plot",
        "Z": "Zaopatrzenie",
        "D": "Dowództwo",
        "G": "Generał"
    }.get(unit_type, unit_type)
    unit_symbol = {"Pluton": "***", "Kompania": "I", "Batalion": "II"}.get(unit_size, "")
    unit_full_name = f"{nation} {unit_type_full} {unit_size} {unit_symbol}".strip()
    return {"label": label, "unit_full_name": unit_full_name}
