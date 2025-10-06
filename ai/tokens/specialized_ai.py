"""Moduł specjalizacji AI dla żetonów.

Zapewnia delikatne, bezpieczne rozszerzenia zachowań `TokenAI` tak, aby
różne typy jednostek korzystały z dedykowanych heurystyk, jednocześnie
pozostając kompatybilne z przyszłymi warstwami dowodzenia.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Set, Tuple, Type


# ---------------------------------------------------------------------------
# Współdzielona pamięć rozpoznania
# ---------------------------------------------------------------------------


@dataclass
class SharedIntelMemory:
    """Minimalna współdzielona pamięć kontaktów przeciwnika.
    
    Zapamiętuje ostatnie meldunki wykryć wraz z prostym licznikiem czasu.
    Nie ma ambicji bycia pełnym systemem – jedynie wspiera specjalistów
    w podejmowaniu bardziej świadomych decyzji.
    """

    _reports: Dict[str, Dict[str, Any]] = field(default_factory=dict)
    _tick: int = 0

    def snapshot(self) -> Dict[str, Dict[str, Any]]:
        """Zwraca kopię danych, aby uniknąć mutacji przez użytkowników."""
        return {enemy_id: dict(payload) for enemy_id, payload in self._reports.items()}

    def ingest(self, reporter_id: str, detection_map: Optional[Dict[str, Dict[str, Any]]]) -> None:
        """Aktualizuje pamięć na podstawie lokalnej mapy detekcji."""
        if not detection_map:
            return
        self._tick += 1
        for enemy_id, info in detection_map.items():
            if not isinstance(info, dict):
                continue
            payload = dict(info)
            payload.setdefault("last_seen_by", reporter_id)
            payload["timestamp"] = self._tick
            self._reports[enemy_id] = payload

    def forget(self, max_age: int = 12) -> None:
        """Usuwa najstarsze meldunki, aby pamięć nie rosła bez kontroli."""
        if max_age <= 0:
            return
        threshold = self._tick - max_age
        stale_keys = [enemy_id for enemy_id, info in self._reports.items() if info.get("timestamp", 0) <= threshold]
        for enemy_id in stale_keys:
            self._reports.pop(enemy_id, None)


_GLOBAL_SHARED_INTEL = SharedIntelMemory()


def get_shared_intel_memory() -> SharedIntelMemory:
    return _GLOBAL_SHARED_INTEL


def _flag(context: Dict[str, Any], flag: str) -> None:
    """Pomocnik: dodaje flagę do kontekstu dla celów diagnostycznych."""
    if not flag:
        return
    flags = context.setdefault("specialist_flags", set())
    if isinstance(flags, set):
        flags.add(flag)
    else:
        merged = set(flags) if hasattr(flags, "__iter__") else set()
        merged.add(flag)
        context["specialist_flags"] = merged


# ---------------------------------------------------------------------------
# Bazowa klasa specjalistów
# ---------------------------------------------------------------------------


class TokenSpecialist:
    """Interfejs rozszerzeń zachowania `TokenAI`.
    
    Specjaliści działają delikatnie: mogą wzbogacać kontekst, korygować
    wybór profilu akcji lub priorytetyzować czynności. Wszystkie metody
    mają bezpieczne domyślne implementacje, dzięki czemu brak przydzielonego
    specjalisty nie psuje logiki bazowej.
    """

    handled_types: Set[str] = set()

    def __init__(self, token, shared_intel: SharedIntelMemory):
        self.token = token
        self.shared_intel = shared_intel

    # --- cykl tury -----------------------------------------------------
    def on_turn_start(self, memory: Dict[str, Any]) -> None:
        """Wywoływane na początku tury; okazja do czyszczenia pamięci."""
        if self.shared_intel:
            self.shared_intel.forget(max_age=18)

    def extend_context(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """Rozszerza kontekst o dane specjalisty (np. cele, sygnały)."""
        if self.shared_intel:
            context.setdefault("shared_enemy_detection", self.shared_intel.snapshot())
        context.setdefault("specialist_flags", set())
        return context

    def adjust_status(self, status: str, context: Dict[str, Any]) -> str:
        """Pozwala skorygować status (np. normal→retreat przy zagrożeniu)."""
        return status

    def adjust_movement_mode(self, movement_mode: str, status: str, context: Dict[str, Any]) -> str:
        """Pozwala zmienić tryb ruchu (march/combat/recon)."""
        return movement_mode

    def suggest_movement_target(self, context: Dict[str, Any]) -> Optional[Tuple[int, int]]:
        """Sugeruje cel ruchu (np. KP dla konwoju). None = brak sugestii."""
        return None

    def choose_action_profile(self, profile_key: str, status: str, context: Dict[str, Any]) -> str:
        """Zmienia profil akcji (retreat/recovery/combat/patrol)."""
        return profile_key

    def adjust_actions(
        self,
        planned_actions: List[str],
        status: str,
        context: Dict[str, Any],
        pe_budget: int,
    ) -> List[str]:
        """Modyfikuje kolejkę akcji przed ich wykonaniem."""
        return list(planned_actions)

    def update_context(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """Hook po akcjach – pozwala zaaktualizować dane kontekstu."""
        return context

    def after_turn(self, context: Dict[str, Any], reports: Dict[str, Any]) -> None:
        """Wywoływane na końcu tury; okazja do zapisania obserwacji."""
        if self.shared_intel:
            detection_map = context.get("enemy_detection")
            reporter_id = getattr(self.token, "id", None)
            if reporter_id:
                self.shared_intel.ingest(reporter_id, detection_map)


class GenericSpecialist(TokenSpecialist):
    """Domyślny specjalista – zachowuje pełną kompatybilność z bazowym AI."""


# ---------------------------------------------------------------------------
# Specjalista zaopatrzenia
# ---------------------------------------------------------------------------


class SupplySpecialist(TokenSpecialist):
    """Specjalista dla jednostek zaopatrzeniowych (Z, ZA, SUPPLY).
    
    Cel: utrzymać najbardziej wartościowy Key Point na mapie, unikając walki.
    """

    handled_types = {"Z", "ZA", "SUPPLY"}

    def __init__(self, token, shared_intel: SharedIntelMemory):
        super().__init__(token, shared_intel)
        self._assigned_kp: Optional[Tuple[int, int]] = getattr(token, "supply_assigned_kp", None)
        self._kp_locked_turns: int = int(getattr(token, "supply_kp_lock_turns", 0) or 0)
        self._persist_state()

    def on_turn_start(self, memory: Dict[str, Any]) -> None:
        super().on_turn_start(memory)
        # Dekrementacja blokady KP
        if self._kp_locked_turns > 0:
            self._kp_locked_turns -= 1
        self._persist_state()

    def extend_context(self, context: Dict[str, Any]) -> Dict[str, Any]:
        context = super().extend_context(context)
        # Wybór najlepszego KP
        board = context.get("board")
        if board and hasattr(board, "key_points"):
            best_kp = self._choose_best_kp(context)
            if best_kp:
                context["supply_target_kp"] = best_kp
                if best_kp != self._assigned_kp:
                    old_kp = self._assigned_kp
                    self._assigned_kp = best_kp
                    self._kp_locked_turns = 3  # Blokada na 3 tury
                    self._persist_state()
                    _flag(context, "zmiana_celu_kp")

                    # Zwięzły opis do raportu
                    scoring = context.get("kp_scoring_details", {})
                    context["human_note"] = self._format_target_note(old_kp, best_kp, scoring)
            elif self._assigned_kp:
                context["supply_target_kp"] = self._assigned_kp
        elif self._assigned_kp:
            context["supply_target_kp"] = self._assigned_kp

        objective = context.get("supply_target_kp") or self._assigned_kp
        if objective:
            context["specialist_objective"] = objective
        self._persist_state()
        return context

    def _choose_best_kp(self, context: Dict[str, Any]) -> Optional[Tuple[int, int]]:
        """Wybiera najlepszy Key Point – minimalistyczny scoring: wartość / dystans.
        
        Konwój nie ma wywiadu, nie zna całej mapy zagrożeń. Jedynie wybiera
        najbardziej wartościowy cel w zasięgu, unikając widzialnych wrogów.
        """
        board = context.get("board")
        if not board or not hasattr(board, "key_points"):
            return None

        my_pos = context.get("position")
        if None in my_pos:
            return None

        danger_zones = context.get("danger_zones", {})

        # Jeśli KP jest zablokowany i nie ma bezpośredniego zagrożenia, trzymamy cel
        if self._kp_locked_turns > 0 and self._assigned_kp:
            kp_danger = danger_zones.get(self._assigned_kp, 0)
            if kp_danger < 2:
                return self._assigned_kp

        candidates = []
        for kp_key, kp_data in board.key_points.items():
            # Parsuj klucz - może być string "q,r" lub tupla (q,r)
            if isinstance(kp_key, str):
                try:
                    parts = kp_key.split(",")
                    kp_hex = (int(parts[0]), int(parts[1]))
                except (ValueError, IndexError):
                    continue
            else:
                kp_hex = kp_key
            if not isinstance(kp_data, dict):
                continue
            kp_value = kp_data.get("value", 0)
            if kp_value <= 0:
                continue

            distance = self._hex_distance(my_pos, kp_hex, board)
            threat = danger_zones.get(kp_hex, 0)

            # Minimalistyczny scoring: wartość / dystans, mocna kara za widzianych wrogów
            score = kp_value / (distance + 1) - (threat * 3)
            candidates.append((score, kp_hex, kp_value, distance, threat))

        if not candidates:
            return None

        candidates.sort(key=lambda x: x[0], reverse=True)
        best = candidates[0]
        
        # Diagnostyka do logu (dla raportu)
        context.setdefault("kp_scoring_details", {}).update({
            "best_kp": best[1],
            "kp_value": best[2],
            "distance": best[3],
            "threat": best[4],
            "score": round(best[0], 2),
        })
        
        return best[1]

    def _hex_distance(self, start: Tuple[int, int], end: Tuple[int, int], board) -> int:
        """Oblicza dystans hex (fallback do axial, jeśli board nie wspiera)."""
        if board and hasattr(board, "hex_distance"):
            try:
                return board.hex_distance(start, end)
            except Exception:
                pass
        # Fallback axial
        sq, sr = start
        eq, er = end
        return int((abs(sq - eq) + abs(sr - er) + abs((sq - sr) - (eq - er))) / 2)

    def suggest_movement_target(self, context: Dict[str, Any]) -> Optional[Tuple[int, int]]:
        """Konwój zawsze podąża do przypisanego KP."""
        target_kp = context.get("supply_target_kp") or self._assigned_kp
        my_pos = context.get("position")
        if target_kp and my_pos != target_kp:
            return target_kp
        return None

    def adjust_status(self, status: str, context: Dict[str, Any]) -> str:
        """Zaopatrzenie przy wysokim zagrożeniu przełącza się na retreat."""
        danger = (context.get("danger_zones") or {}).get(context.get("position"), 0)
        if danger >= 3 and status == "normal":
            _flag(context, "wrog_w_zasiegu")
            context["human_note"] = f"Wycofanie: wrogów {danger} w bezpośrednim zasięgu"
            return "threatened"
        return status

    def adjust_actions(
        self,
        planned_actions: List[str],
        status: str,
        context: Dict[str, Any],
        pe_budget: int,
    ) -> List[str]:
        """Konwoje nie atakują i priorytetyzują paliwo."""
        result = list(planned_actions)
        my_pos = context.get("position")

        # Priorytet paliwa
        fuel = context.get("current_fuel", 0)
        max_fuel = max(1, context.get("max_fuel", 1))
        fuel_pct = int(fuel / max_fuel * 100)
        if fuel < max_fuel * 0.8 and "refuel_minimum" not in result and pe_budget > 0:
            _flag(context, "niski_poziom_paliwa")
            result.insert(0, "refuel_minimum")
            context["human_note"] = f"Tankowanie: paliwo {fuel_pct}%"

        # Usuwamy atak i – tylko przy realnym zagrożeniu – dodajemy wycofanie
        if "attack" in result:
            result = [action for action in result if action != "attack"]
            danger_zones = context.get("danger_zones") or {}
            danger_here = danger_zones.get(my_pos, 0) if my_pos else 0
            visible_enemies = context.get("visible_enemies") or []
            board = context.get("board")
            nearest_enemy_distance = None
            if board and visible_enemies:
                distances = []
                for enemy in visible_enemies:
                    enemy_pos = getattr(enemy, "q", None), getattr(enemy, "r", None)
                    if None in enemy_pos:
                        continue
                    try:
                        distances.append(board.hex_distance(my_pos, enemy_pos))
                    except Exception:
                        continue
                if distances:
                    nearest_enemy_distance = min(distances)
            should_withdraw = (
                status in {"threatened", "urgent_retreat"}
                or danger_here >= 2
                or (nearest_enemy_distance is not None and nearest_enemy_distance <= 2)
            )
            if should_withdraw and "withdraw" not in result:
                result.append("withdraw")
                if "human_note" not in context:
                    context["human_note"] = "Wycofanie: zagrożenie w pobliżu"
            _flag(context, "pacyfista")
            if should_withdraw:
                _flag(context, "wycofanie_przy_zagrozeniu")

        # Przy garnizonie na KP: hold_position
        target_kp = context.get("supply_target_kp")
        if my_pos == target_kp and target_kp:
            _flag(context, "garnizon_na_kp")
            # Czyścimy maneuver, bo już jesteśmy na miejscu
            result = [a for a in result if a not in {"maneuver", "withdraw"}]
            self._persist_state()
            if "human_note" not in context:
                context["human_note"] = f"Garnizon: KP {target_kp} zabezpieczony"

        return result

    def _persist_state(self) -> None:
        setattr(self.token, "supply_assigned_kp", self._assigned_kp)
        setattr(self.token, "supply_kp_lock_turns", self._kp_locked_turns)

    @staticmethod
    def _format_target_note(
        old_kp: Optional[Tuple[int, int]],
        new_kp: Tuple[int, int],
        scoring: Optional[Dict[str, Any]],
    ) -> str:
        prefix = f"Cel {old_kp}→{new_kp}" if old_kp else f"Cel KP {new_kp}"
        if not scoring:
            return prefix
        kp_val = scoring.get("kp_value")
        dist = scoring.get("distance")
        threat = scoring.get("threat")
        score_val = scoring.get("score")
        details = []
        if kp_val is not None:
            details.append(f"wart {kp_val}")
        if dist is not None:
            details.append(f"dyst {dist}")
        if threat is not None:
            details.append(f"zag {threat}")
        if score_val is not None:
            details.append(f"score {score_val}")
        return prefix + (" | " + ", ".join(details) if details else "")


# ---------------------------------------------------------------------------
# Pustki dla przyszłych specjalistów
# ---------------------------------------------------------------------------


class CavalrySpecialist(TokenSpecialist):
    """Placeholder dla kawalerii – na razie zachowuje domyślne AI."""
    handled_types = {"K", "CAV"}


class InfantrySpecialist(TokenSpecialist):
    """Placeholder dla piechoty – na razie zachowuje domyślne AI."""
    handled_types = {"P", "INF"}


class TankSpecialist(TokenSpecialist):
    """Placeholder dla czołgów – na razie zachowuje domyślne AI."""
    handled_types = {"C", "T", "TL", "TS", "TŚ", "TC", "ARM"}


class ArtillerySpecialist(TokenSpecialist):
    """Placeholder dla artylerii – na razie zachowuje domyślne AI."""
    handled_types = {"AL", "AC", "AP", "AR", "ART"}


# ---------------------------------------------------------------------------
# Rejestr i fabryka specjalistów
# ---------------------------------------------------------------------------


SPECIALIST_CLASSES: List[Type[TokenSpecialist]] = [
    SupplySpecialist,
    CavalrySpecialist,
    InfantrySpecialist,
    TankSpecialist,
    ArtillerySpecialist,
]


def _normalize_unit_type(token) -> str:
    """Wydobywa znormalizowany typ jednostki (np. 'Z', 'K', 'P')."""
    unit_type = None
    stats = getattr(token, "stats", {}) or {}
    raw = stats.get("unitType") or stats.get("unit_type")
    if raw:
        unit_type = str(raw).upper()
    else:
        # Spróbuj wydobyć kod prefixu z identyfikatora (np. "K_", "P_", "Z_")
        token_id = getattr(token, "id", "") or ""
        if "_" in token_id:
            unit_type = token_id.split("_")[0].upper()
    return unit_type or "GENERIC"


def build_specialist(token, shared_intel: Optional[SharedIntelMemory] = None) -> TokenSpecialist:
    """Buduje odpowiedniego specjalistę dla danego żetonu."""
    shared_intel = shared_intel or get_shared_intel_memory()
    normalized_type = _normalize_unit_type(token)
    for specialist_cls in SPECIALIST_CLASSES:
        if normalized_type in specialist_cls.handled_types:
            return specialist_cls(token, shared_intel)
    return GenericSpecialist(token, shared_intel)


def create_token_ai(token):
    """Publiczna fabryka AI – zachowuje kompatybilny podpis."""
    from .token_ai import TokenAI  # Opóźniony import, aby uniknąć cykli.

    specialist = build_specialist(token, get_shared_intel_memory())
    return TokenAI(token, specialist=specialist)


__all__ = [
    "SharedIntelMemory",
    "TokenSpecialist",
    "SupplySpecialist",
    "CavalrySpecialist",
    "InfantrySpecialist",
    "TankSpecialist",
    "ArtillerySpecialist",
    "build_specialist",
    "get_shared_intel_memory",
    "create_token_ai",
]