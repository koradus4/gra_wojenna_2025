"""
Podstawowa logika AI Generała - dystrybucja PE w oparciu o realne potrzeby dowódców.
"""
from collections import defaultdict, deque
import math
from typing import List, Dict, Tuple
from engine.player import Player
from core.ekonomia import EconomySystem
from ai.logs import log_general, log_debug, log_error


class GeneralAI:
    """AI Generał - zarządza ekonomią i dystrybuuje PE"""
    
    def __init__(self, player: Player):
        self.player = player
        # Rezerwa bazowa 15%, z adaptacyjnym korygowaniem (10-20%)
        self.base_reserve_ratio = 0.15
        self.min_reserve_ratio = 0.10
        self.max_reserve_ratio = 0.20
        self.history_window = 5
        self._commander_budget_history: Dict[int, deque] = defaultdict(lambda: deque(maxlen=self.history_window))
        
    def execute_turn(self, all_players: List[Player], game_engine) -> None:
        """Wykonuje turę AI Generała - tylko dystrybucja PE"""
        print(f"🎖️ AI Generał {self.player.nation} (id={self.player.id}) rozpoczyna turę")
        log_general(f"Generał {self.player.nation} (id={self.player.id}) rozpoczyna turę", "DEBUG")
        
        # 1. Wygeneruj punkty ekonomiczne
        self.player.economy.generate_economic_points()
        self.player.economy.add_special_points()
        
        total_pe = self.player.economy.get_points()['economic_points']
        print(f"💰 Dostępne PE: {total_pe}")
        log_general(f"Dostępne PE: {total_pe}", "INFO")
        
        if total_pe <= 0:
            print("❌ Brak PE do dystrybucji")
            log_general("Brak PE do dystrybucji", "WARNING")
            return
            
        # 2. Znajdź dowódców tej samej nacji
        commanders = [p for p in all_players 
                     if p.nation == self.player.nation and p.role == "Dowódca"]
        
        if not commanders:
            print("⚠️ Brak dowódców do dystrybucji PE")
            log_general("Brak dowódców do dystrybucji PE", "WARNING")
            return
            
        commander_profiles = self._build_commander_profiles(commanders, game_engine)
        profile_by_id = {profile['id']: profile for profile in commander_profiles}

        for profile in commander_profiles:
            log_general(
                "Profil dowódcy",
                "DEBUG",
                commander_id=profile['id'],
                token_count=profile['token_count'],
                minimum=profile['minimum'],
                headroom=profile['headroom'],
                baseline=profile['baseline'],
            )
        if not commander_profiles:
            log_general("Brak przypisanych żetonów do dowódców – całość w rezerwie", "WARNING")
            return

        reserve_pe, distributable_pe = self._calculate_reserve_split(total_pe, commander_profiles)
        log_general(
            "Podział rezerwy i środków",
            "DEBUG",
            total_pe=total_pe,
            reserve_pe=reserve_pe,
            distributable_pe=distributable_pe,
        )

        allocation = self._allocate_to_commanders(distributable_pe, commander_profiles)

        total_allocated = sum(allocation.values())
        reserve_pe = max(0, total_pe - total_allocated)

        print("💡 Plan dystrybucji:")
        print(f"   • Rezerwa: {reserve_pe} PE")
        print(f"   • Środki dla dowódców: {total_allocated} PE")
        log_general(
            f"Plan dystrybucji: rezerwa={reserve_pe} PE, dowódcy={total_allocated} PE",
            "INFO",
        )

        for profile in commander_profiles:
            commander_id = profile['id']
            log_general(
                "Planowany przydział dla dowódcy",
                "INFO",
                commander_id=commander_id,
                allocated_pe=allocation.get(commander_id, 0),
                token_count=profile['token_count'],
                minimum=profile['minimum'],
                headroom=profile['headroom'],
            )

        # przekazanie środków
        for commander in commanders:
            pe_to_give = allocation.get(commander.id, 0)
            if pe_to_give <= 0:
                continue

            if self.player.economy.economic_points < pe_to_give:
                missing = pe_to_give - self.player.economy.economic_points
                log_error(
                    f"Brak PE dla dowódcy {commander.id} (brakuje {missing})",
                    "GENERAL",
                )
                pe_to_give = self.player.economy.economic_points

            if pe_to_give <= 0:
                continue

            self.player.economy.subtract_points(pe_to_give)
            commander.economy.add_economic_points(pe_to_give)
            print(f"✅ Przekazano {pe_to_give} PE → Dowódca {commander.id}")
            log_general(
                "Przekazano PE dowódcy",
                "INFO",
                commander_id=commander.id,
                allocated_pe=pe_to_give,
                commander_tokens=profile_by_id.get(commander.id, {}).get('token_count'),
                commander_points_after=commander.economy.get_points()['economic_points'],
                reserve_after=self.player.economy.get_points()['economic_points'],
            )

            history = self._commander_budget_history[commander.id]
            history.append(pe_to_give)

        final_pe = self.player.economy.get_points()['economic_points']
        setattr(self.player, "ai_reserved_points", final_pe)

        print(f"🏁 Generał kończy turę. Pozostało PE: {final_pe}")
        log_general(f"Generał kończy turę. Pozostało PE: {final_pe}", "DEBUG")

        for commander in commanders:
            cmd_points = commander.economy.get_points()['economic_points']
            profile = next((p for p in commander_profiles if p['id'] == commander.id), None)
            need_info = "?"
            if profile:
                need_info = (
                    f"min={profile['minimum']} headroom={profile['headroom']} tokens={profile['token_count']}"
                )
            print(f"   📊 Dowódca {commander.id}: {cmd_points} PE (potrzeby: {need_info})")
            log_general(
                "Stan dowódcy po dystrybucji",
                "INFO",
                commander_id=commander.id,
                points=cmd_points,
                needs=need_info,
            )

    def _build_commander_profiles(self, commanders: List[Player], game_engine) -> List[Dict[str, int]]:
        profiles: List[Dict[str, int]] = []

        for commander in commanders:
            token_count = self._count_commander_tokens(commander, game_engine)
            minimum = token_count  # 1 PE na aktywację żetonu

            avg_consumption = self._average_consumption(commander)
            fallback_consumption = max(token_count, 1)
            consumption_baseline = max(avg_consumption, fallback_consumption)
            headroom = max(1, math.ceil(consumption_baseline * 0.5))

            profiles.append(
                {
                    'id': commander.id,
                    'minimum': minimum,
                    'headroom': headroom,
                    'token_count': token_count,
                    'baseline': consumption_baseline,
                }
            )

        return profiles

    def _count_commander_tokens(self, commander: Player, game_engine) -> int:
        count = 0
        for token in getattr(game_engine, 'tokens', []):
            owner = getattr(token, 'owner', None)
            owner_id = None
            owner_nation = None

            if isinstance(owner, str):
                if '(' in owner and ')' in owner:
                    try:
                        owner_id = int(owner.split('(')[0].strip())
                        owner_nation = owner.split('(')[1].replace(')', '').strip()
                    except (ValueError, IndexError):
                        owner_id = None
                        owner_nation = None
            else:
                owner_id = getattr(owner, 'id', None)
                owner_nation = getattr(owner, 'nation', None)

            if owner_id == commander.id and (owner_nation is None or owner_nation == commander.nation):
                count += 1

        return count

    def _average_consumption(self, commander: Player) -> float:
        history = getattr(commander, 'ai_consumption_history', None)
        if not history:
            return 0.0
        if isinstance(history, deque):
            values = list(history)
        else:
            values = list(history)
        if not values:
            return 0.0
        return sum(values) / len(values)

    def _calculate_reserve_split(self, total_pe: int, profiles: List[Dict[str, int]]) -> Tuple[int, int]:
        current_reserved = getattr(self.player, 'ai_reserved_points', 0)
        avg_budget = self._average_commander_budget()

        reserve_ratio = self.base_reserve_ratio
        if avg_budget > 0:
            if current_reserved > avg_budget * 1.5:
                reserve_ratio = max(self.min_reserve_ratio, reserve_ratio - 0.05)
            elif current_reserved < avg_budget * 0.5:
                reserve_ratio = min(self.max_reserve_ratio, reserve_ratio + 0.02)

        reserve_pe = int(total_pe * reserve_ratio)
        distributable = total_pe - reserve_pe

        total_minimum = sum(p['minimum'] for p in profiles)
        if distributable < total_minimum:
            shortfall = total_minimum - distributable
            reserve_pe = max(0, reserve_pe - shortfall)
            distributable = total_pe - reserve_pe

        return reserve_pe, max(0, distributable)

    def _average_commander_budget(self) -> float:
        values = []
        for history in self._commander_budget_history.values():
            if history:
                values.append(sum(history) / len(history))
        if not values:
            return 0.0
        return sum(values) / len(values)

    def _allocate_to_commanders(self, distributable: int, profiles: List[Dict[str, int]]) -> Dict[int, int]:
        allocation: Dict[int, int] = {p['id']: 0 for p in profiles}
        if distributable <= 0 or not profiles:
            return allocation

        total_minimum = sum(p['minimum'] for p in profiles)

        if total_minimum == 0:
            equal_share = distributable // len(profiles)
            for profile in profiles:
                allocation[profile['id']] = equal_share
            remainder = distributable - equal_share * len(profiles)
            for profile in profiles[:remainder]:
                allocation[profile['id']] += 1
            return allocation

        if distributable <= total_minimum:
            ratio = distributable / total_minimum
            accumulated = 0
            for profile in profiles:
                share = math.floor(profile['minimum'] * ratio)
                allocation[profile['id']] = share
                accumulated += share

            remainder = distributable - accumulated
            if remainder > 0:
                profiles_sorted = sorted(profiles, key=lambda p: (-p['minimum'], p['id']))
                for profile in profiles_sorted:
                    if remainder <= 0:
                        break
                    allocation[profile['id']] += 1
                    remainder -= 1
            return allocation

        # przydziel minimum, reszta wg headroom
        for profile in profiles:
            allocation[profile['id']] = profile['minimum']

        remainder = distributable - total_minimum
        if remainder <= 0:
            return allocation

        weights = []
        for profile in profiles:
            weight = max(1, profile['headroom'])
            weights.append((profile['id'], weight))

        weight_sum = sum(weight for _, weight in weights) or 1
        distributed_extra = 0
        fractional_store = []

        for commander_id, weight in weights:
            exact_share = remainder * weight / weight_sum
            share = math.floor(exact_share)
            allocation[commander_id] += share
            distributed_extra += share
            fractional_store.append((exact_share - share, commander_id))

        leftover = remainder - distributed_extra
        if leftover > 0:
            fractional_store.sort(reverse=True)
            idx = 0
            while leftover > 0 and idx < len(fractional_store):
                _, commander_id = fractional_store[idx]
                allocation[commander_id] += 1
                leftover -= 1
                idx += 1

        return allocation