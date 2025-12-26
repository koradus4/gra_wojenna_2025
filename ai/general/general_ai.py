"""
Podstawowa logika AI Generała - dystrybucja PE w oparciu o realne potrzeby dowódców.
"""
from collections import defaultdict, deque
from enum import Enum
import math
import shutil
from typing import List, Dict, Tuple, Optional, Any

from engine.player import Player
from core.ekonomia import EconomySystem
from ai.logs import log_general, log_debug, log_error
from utils.token_blueprint import generate_token_assets
from balance.model import compute_token


class WarState(Enum):
    LOSING = "losing"
    EVEN = "even"
    WINNING = "winning"


class GeneralAI:
    """AI Generał - zarządza ekonomią i dystrybuuje PE"""
    
    def __init__(self, player: Player):
        self.player = player
        # Rezerwa bazowa 15%, z adaptacyjnym korygowaniem (10-20%)
        self.base_reserve_ratio = 0.15
        self.min_reserve_ratio = 0.10
        self.max_reserve_ratio = 0.20
        self.history_window = 5
        self._commander_budget_history = defaultdict(lambda: deque(maxlen=self.history_window))  # type: Dict[int, deque]
        self._last_vp_diff = 0.0
        self._last_token_diff = 0
        self._last_state = WarState.EVEN
        self._last_purchase_budget = 0
        self._last_budget_plan = {}
        
    def execute_turn(self, all_players: List[Player], game_engine) -> None:
        """Wykonuje turę AI Generała - tylko dystrybucja PE"""
        print(f"🎖️ AI Generał {self.player.nation} (id={self.player.id}) rozpoczyna turę")
        log_general(f"Generał {self.player.nation} (id={self.player.id}) rozpoczyna turę", "DEBUG")
        
        # 1. Wygeneruj punkty ekonomiczne
        self.player.economy.generate_economic_points()
        self.player.economy.add_special_points()
        
        war_state = self._assess_war_state(all_players, game_engine)

        total_pe = self.player.economy.get_points()['economic_points']
        print(f"💰 Dostępne PE: {total_pe}")
        log_general(f"Dostępne PE: {total_pe}", "INFO")
        log_general(
            "Ocena stanu wojny",
            "DEBUG",
            war_state=war_state.value,
            vp_diff=self._last_vp_diff,
            token_diff=self._last_token_diff,
        )
        
        if total_pe <= 0:
            print("❌ Brak PE do dystrybucji")
            log_general("Brak PE do dystrybucji", "WARNING")
            setattr(self.player, "ai_reserved_points", 0)
            setattr(self.player, "ai_purchase_budget", 0)
            setattr(self.player, "ai_commander_pool", 0)
            self._last_purchase_budget = 0
            self._last_budget_plan = {}
            return
            
        # 2. Znajdź dowódców tej samej nacji
        commanders = [p for p in all_players 
                     if p.nation == self.player.nation and p.role == "Dowódca"]
        
        if not commanders:
            print("⚠️ Brak dowódców do dystrybucji PE")
            log_general("Brak dowódców do dystrybucji PE", "WARNING")
            setattr(self.player, "ai_commander_pool", 0)
            setattr(self.player, "ai_reserved_points", total_pe)
            setattr(self.player, "ai_purchase_budget", 0)
            self._last_purchase_budget = 0
            self._last_budget_plan = {
                'war_state': war_state.value,
                'reserve': total_pe,
                'commanders': 0,
                'purchases': 0,
                'reserve_effective': total_pe,
                'commanders_effective': 0,
                'purchases_effective': 0,
            }
            return
            
        commander_profiles = self._build_commander_profiles(commanders, game_engine)
        profile_by_id = {profile['id']: profile for profile in commander_profiles}
        support_needs = self._collect_support_needs(commanders)

        log_general(
            "Zebrane potrzeby wsparcia",
            "DEBUG",
            fuel_total=support_needs['fuel'],
            repair_total=support_needs['repair'],
            commanders=len(commanders),
        )

        for profile in commander_profiles:
            log_general(
                "Profil dowódcy",
                "DEBUG",
                commander_id=profile['id'],
                token_count=profile['token_count'],
                minimum=profile['minimum'],
                headroom=profile['headroom'],
                baseline=profile['baseline'],
                support_fuel=profile['support_fuel'],
                support_repair=profile['support_repair'],
            )
        if not commander_profiles:
            log_general("Brak przypisanych żetonów do dowódców – całość w rezerwie", "WARNING")
            setattr(self.player, "ai_commander_pool", 0)
            setattr(self.player, "ai_reserved_points", total_pe)
            setattr(self.player, "ai_purchase_budget", 0)
            self._last_purchase_budget = 0
            self._last_budget_plan = {
                'war_state': war_state.value,
                'reserve': total_pe,
                'commanders': 0,
                'purchases': 0,
                'reserve_effective': total_pe,
                'commanders_effective': 0,
                'purchases_effective': 0,
            }
            return

        budget_plan = self._compute_budget_envelopes(total_pe, commander_profiles, war_state)
        reserve_planned = budget_plan['reserve']
        commander_pool = budget_plan['commanders']
        purchase_planned = budget_plan['purchases']

        self._last_purchase_budget = purchase_planned
        self._last_budget_plan = {
            'war_state': war_state.value,
            'reserve': reserve_planned,
            'commanders': commander_pool,
            'purchases': purchase_planned,
        }

        log_general(
            "Koperty budżetowe",
            "DEBUG",
            reserve=reserve_planned,
            commanders=commander_pool,
            purchases=purchase_planned,
            war_state=war_state.value,
        )

        allocation = self._allocate_to_commanders(commander_pool, commander_profiles)

        total_allocated = sum(allocation.values())
        remaining_after_alloc = total_pe - total_allocated
        reserve_effective = max(0, min(reserve_planned, remaining_after_alloc))
        purchase_effective = max(0, remaining_after_alloc - reserve_effective)

        self._last_purchase_budget = purchase_effective
        self._last_budget_plan.update(
            {
                'reserve_effective': reserve_effective,
                'purchases_effective': purchase_effective,
                'commanders_effective': total_allocated,
            }
        )

        purchases_plan = self._plan_purchases(purchase_effective, war_state, support_needs)
        setattr(self.player, "ai_purchase_plan", purchases_plan)

        purchase_events, purchase_spent = self._execute_purchase_plan(
            commanders=commanders,
            commander_profiles=commander_profiles,
            plan=purchases_plan,
            available_budget=purchase_effective,
        )
        setattr(self.player, "ai_purchase_events", purchase_events)

        unspent_purchase = max(0, purchase_effective - purchase_spent)
        reserve_effective += unspent_purchase
        purchase_effective = purchase_spent
        setattr(self.player, "ai_purchase_budget", unspent_purchase)
        self._last_purchase_budget = purchase_spent
        self._last_budget_plan.update(
            {
                'reserve_effective': reserve_effective,
                'purchases_effective': purchase_effective,
            }
        )

        log_general(
            "Plan zakupów",
            "DEBUG",
            purchase_budget=purchase_effective,
            war_state=war_state.value,
            entries=purchases_plan,
            executed=len(purchase_events),
            spent=purchase_spent,
        )

        print("💡 Plan dystrybucji:")
        print(f"   • Rezerwa: {reserve_effective} PE")
        print(f"   • Zakupy: {purchase_effective} PE")
        print(f"   • Środki dla dowódców: {total_allocated} PE")
        print(
            f"   • Zapotrzebowanie paliwo/naprawy: fuel={support_needs['fuel']} repair={support_needs['repair']}"
        )
        log_general(
            f"Plan dystrybucji: rezerwa={reserve_effective} PE, zakupy={purchase_effective} PE, dowódcy={total_allocated} PE",
            "INFO",
            reserve_plan=reserve_planned,
            commanders_plan=commander_pool,
            purchases_plan=purchase_planned,
            fuel_need_total=support_needs['fuel'],
            repair_need_total=support_needs['repair'],
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
                support_fuel=profile['support_fuel'],
                support_repair=profile['support_repair'],
            )

        # przekazanie środków
        commander_results = []
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

            commander_results.append(
                {
                    'id': commander.id,
                    'allocated': pe_to_give,
                    'points_after': commander.economy.get_points()['economic_points'],
                    'token_count': profile_by_id.get(commander.id, {}).get('token_count'),
                    'support_need': support_needs['details'].get(commander.id, {}),
                }
            )

        final_pe = self.player.economy.get_points()['economic_points']
        setattr(self.player, "ai_reserved_points", reserve_effective)
        setattr(self.player, "ai_purchase_budget", purchase_effective)
        setattr(self.player, "ai_commander_pool", commander_pool)
        self._last_budget_plan['final_pe'] = final_pe

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
                fuel_need=support_needs['details'].get(commander.id, {}).get('fuel'),
                repair_need=support_needs['details'].get(commander.id, {}).get('repair'),
            )

        self._log_turn_summary(
            game_engine=game_engine,
            war_state=war_state,
            total_pe=total_pe,
            reserve_planned=reserve_planned,
            reserve_effective=reserve_effective,
            commander_pool_planned=commander_pool,
            commander_pool_spent=total_allocated,
            purchase_planned=purchase_planned,
            purchase_effective=purchase_effective,
            commanders=commander_results,
            support_needs=support_needs,
            purchases_plan=purchases_plan,
            allocation=allocation,
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
            support_need = self._commander_support_need(commander)

            profiles.append(
                {
                    'id': commander.id,
                    'minimum': minimum,
                    'headroom': headroom,
                    'token_count': token_count,
                    'baseline': consumption_baseline,
                    'support_fuel': support_need.get('fuel', 0),
                    'support_repair': support_need.get('repair', 0),
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

    def _compute_budget_envelopes(
        self,
        total_pe: int,
        profiles: List[Dict[str, int]],
        war_state: WarState,
    ) -> Dict[str, int]:
        if total_pe <= 0:
            return {'reserve': 0, 'commanders': 0, 'purchases': 0}

        base_ratios = {
            WarState.WINNING: {'reserve': 0.20, 'commanders': 0.45, 'purchases': 0.35},
            WarState.EVEN: {'reserve': 0.15, 'commanders': 0.55, 'purchases': 0.30},
            WarState.LOSING: {'reserve': 0.12, 'commanders': 0.68, 'purchases': 0.20},
        }

        ratios = base_ratios.get(war_state, base_ratios[WarState.EVEN]).copy()
        ratios['reserve'] = self._adjust_reserve_ratio(ratios['reserve'])

        non_reserve_total = max(1e-6, ratios['commanders'] + ratios['purchases'])
        remaining_ratio = max(0.0, 1.0 - ratios['reserve'])
        scaling_factor = remaining_ratio / non_reserve_total
        ratios['commanders'] *= scaling_factor
        ratios['purchases'] *= scaling_factor

        exact_shares = {key: total_pe * value for key, value in ratios.items()}
        envelope = {key: int(math.floor(share)) for key, share in exact_shares.items()}
        used = sum(envelope.values())
        remainder = total_pe - used
        if remainder > 0:
            fractional = sorted(
                ((share - math.floor(share), key) for key, share in exact_shares.items()),
                reverse=True,
            )
            idx = 0
            while remainder > 0 and idx < len(fractional):
                _, key = fractional[idx]
                envelope[key] += 1
                remainder -= 1
                idx += 1

        total_minimum = sum(p['minimum'] for p in profiles)
        if envelope['commanders'] < total_minimum:
            shortfall = total_minimum - envelope['commanders']
            take_from_purchases = min(shortfall, envelope['purchases'])
            envelope['commanders'] += take_from_purchases
            envelope['purchases'] -= take_from_purchases
            shortfall -= take_from_purchases

            if shortfall > 0:
                take_from_reserve = min(shortfall, envelope['reserve'])
                envelope['commanders'] += take_from_reserve
                envelope['reserve'] -= take_from_reserve
                shortfall -= take_from_reserve

        for key in ('reserve', 'commanders', 'purchases'):
            envelope[key] = max(0, envelope[key])

        adjustment = total_pe - sum(envelope.values())
        if adjustment > 0:
            envelope['commanders'] += adjustment
        elif adjustment < 0:
            debt = -adjustment
            for key in ('reserve', 'purchases', 'commanders'):
                if debt <= 0:
                    break
                take = min(debt, envelope[key])
                envelope[key] -= take
                debt -= take

        return envelope

    def _collect_support_needs(self, commanders: List[Player]) -> Dict[str, any]:
        aggregate = {'fuel': 0, 'repair': 0, 'details': {}}

        for commander in commanders:
            needs = getattr(commander, 'ai_support_needs', None)
            if not isinstance(needs, dict):
                continue
            fuel = int(needs.get('fuel', 0))
            repair = int(needs.get('repair', 0))
            aggregate['fuel'] += max(0, fuel)
            aggregate['repair'] += max(0, repair)
            aggregate['details'][commander.id] = {
                'fuel': max(0, fuel),
                'repair': max(0, repair),
            }

        return aggregate

    def _adjust_reserve_ratio(self, target_ratio: float) -> float:
        target_ratio = max(self.min_reserve_ratio, min(self.max_reserve_ratio, target_ratio))
        current_reserved = getattr(self.player, 'ai_reserved_points', 0)
        avg_budget = self._average_commander_budget()

        if avg_budget > 0:
            if current_reserved > avg_budget * 1.5:
                target_ratio = max(self.min_reserve_ratio, target_ratio - 0.03)
            elif current_reserved < avg_budget * 0.5:
                target_ratio = min(self.max_reserve_ratio, target_ratio + 0.03)

        return max(self.min_reserve_ratio, min(self.max_reserve_ratio, target_ratio))

    def _average_commander_budget(self) -> float:
        values = []
        for history in self._commander_budget_history.values():
            if history:
                values.append(sum(history) / len(history))
        if not values:
            return 0.0
        return sum(values) / len(values)

    def _assess_war_state(self, all_players: List[Player], game_engine) -> WarState:
        vp_by_nation: Dict[str, int] = defaultdict(int)
        for player in all_players:
            vp_by_nation[player.nation] += getattr(player, "victory_points", 0)

        my_vp = vp_by_nation.get(self.player.nation, 0)
        enemy_vp_values = [vp for nation, vp in vp_by_nation.items() if nation != self.player.nation]
        top_enemy_vp = max(enemy_vp_values) if enemy_vp_values else my_vp

        tokens_by_nation = self._collect_token_stats(game_engine)
        my_tokens = tokens_by_nation.get(self.player.nation, 0)
        enemy_token_values = [count for nation, count in tokens_by_nation.items() if nation != self.player.nation]
        top_enemy_tokens = max(enemy_token_values) if enemy_token_values else my_tokens

        vp_diff = my_vp - top_enemy_vp
        token_diff = my_tokens - top_enemy_tokens

        self._last_vp_diff = vp_diff
        self._last_token_diff = token_diff

        state = self._classify_war_state(vp_diff, token_diff)
        self._last_state = state
        setattr(self.player, "ai_war_state", state.value)
        return state

    def _collect_token_stats(self, game_engine) -> Dict[str, int]:
        tokens_by_nation: Dict[str, int] = defaultdict(int)
        if not game_engine or not getattr(game_engine, "tokens", None):
            return tokens_by_nation

        for token in game_engine.tokens:
            nation = self._resolve_token_nation(token)
            if nation:
                tokens_by_nation[nation] += 1

        return tokens_by_nation

    def _resolve_token_nation(self, token) -> Optional[str]:
        owner = getattr(token, "owner", None)
        if isinstance(owner, str):
            if "(" in owner and ")" in owner:
                try:
                    nation_part = owner.split("(")[1].split(")")[0].strip()
                    if nation_part:
                        return nation_part
                except (IndexError, ValueError):
                    return None
            return None

        if owner is not None:
            nation = getattr(owner, "nation", None)
            if nation:
                return nation

        return getattr(token, "nation", None)

    def _classify_war_state(self, vp_diff: int, token_diff: int) -> WarState:
        dominant_advantage = vp_diff >= 5 or (vp_diff >= 2 and token_diff >= 3)
        dominant_defeat = vp_diff <= -5 or (vp_diff <= -2 and token_diff <= -3)

        if dominant_advantage or (vp_diff >= 3 and token_diff >= 0):
            return WarState.WINNING
        if dominant_defeat or (vp_diff <= -3 and token_diff <= 0):
            return WarState.LOSING
        return WarState.EVEN

    def _commander_support_need(self, commander: Player) -> Dict[str, int]:
        needs = getattr(commander, 'ai_support_needs', None)
        if isinstance(needs, dict):
            return {
                'fuel': max(0, int(needs.get('fuel', 0))),
                'repair': max(0, int(needs.get('repair', 0))),
            }
        return {'fuel': 0, 'repair': 0}

    def _plan_purchases(
        self,
        budget: int,
        war_state: WarState,
        support_needs: Dict[str, any],
    ) -> List[Dict[str, any]]:
        if budget <= 0:
            return []

        prefer_reinforcement = war_state == WarState.LOSING
        prefer_offense = war_state == WarState.WINNING
        prefer_support = war_state == WarState.EVEN

        needs_factor = 1.0 + min(1.0, support_needs['fuel'] / 50.0 if support_needs['fuel'] else 0)
        repair_factor = 1.0 + min(1.0, support_needs['repair'] / 40.0 if support_needs['repair'] else 0)

        priorities: List[Tuple[str, float]] = []

        priorities.append(("infantry", 0.6))
        priorities.append(("armor", 0.7))
        priorities.append(("artillery", 0.5))
        priorities.append(("support", 0.4 * needs_factor))
        priorities.append(("resupply", 0.3 * repair_factor))

        if prefer_reinforcement:
            priorities.append(("reserves", 0.8))
        if prefer_offense:
            priorities.append(("offensive", 0.75))
        if prefer_support:
            priorities.append(("support", 0.6 * needs_factor))

        priorities.sort(key=lambda item: item[1], reverse=True)

        plan: List[Dict[str, any]] = []
        remaining_budget = budget

        for category, weight in priorities:
            if remaining_budget <= 0:
                break

            entry_budget = max(0, int(remaining_budget * min(0.4, weight / (len(priorities) + 1))))
            if entry_budget <= 0:
                continue

            plan.append(
                {
                    'category': category,
                    'weight': round(weight, 2),
                    'allocated': entry_budget,
                    'focus': self._purchase_focus(category, war_state),
                }
            )
            remaining_budget -= entry_budget

        if remaining_budget > 0:
            if plan:
                plan[0]['allocated'] += remaining_budget
            else:
                plan.append(
                    {
                        'category': 'general',
                        'weight': 0.5,
                        'allocated': remaining_budget,
                        'focus': self._purchase_focus('general', war_state),
                    }
                )

        return plan

    def _execute_purchase_plan(
        self,
        *,
        commanders: List[Player],
        commander_profiles: List[Dict[str, Any]],
        plan: List[Dict[str, Any]],
        available_budget: int,
    ) -> Tuple[List[Dict[str, Any]], int]:
        if available_budget <= 0 or not plan or not commanders:
            return [], 0

        remaining_budget = min(available_budget, self.player.economy.get_points()['economic_points'])
        if remaining_budget <= 0:
            return [], 0

        purchase_history = getattr(self.player, "ai_purchase_history", None)
        if not isinstance(purchase_history, list):
            purchase_history = []
            setattr(self.player, "ai_purchase_history", purchase_history)

        token_counts = {profile['id']: profile.get('token_count', 0) for profile in commander_profiles}
        events: List[Dict[str, Any]] = []
        per_commander_events: dict[int, list[Dict[str, Any]]] = defaultdict(list)

        plan_sorted = sorted(plan, key=lambda entry: entry.get('weight', 0), reverse=True)

        for entry in plan_sorted:
            entry_budget = int(entry.get('allocated', 0) or 0)
            if entry_budget <= 0:
                continue

            category = entry.get('category', 'general')
            focus = entry.get('focus')

            while entry_budget > 0 and remaining_budget > 0:
                commander = self._select_purchase_commander(commanders, token_counts)
                if commander is None:
                    break

                candidates = self._recipe_candidates(category, focus)
                bundle = None
                chosen_type = None
                for unit_type, unit_size in candidates:
                    stats = compute_token(unit_type, unit_size, commander.nation, [])
                    unit_cost = stats.total_cost
                    if unit_cost > min(entry_budget, remaining_budget):
                        continue
                    try:
                        bundle = generate_token_assets(
                            commander_id=commander.id,
                            nation=commander.nation,
                            unit_type=unit_type,
                            unit_size=unit_size,
                            supports=[],
                        )
                    except Exception as exc:
                        log_error(
                            "Nie udało się wygenerować żetonu",
                            commander_id=commander.id,
                            unit_type=unit_type,
                            unit_size=unit_size,
                            error=str(exc),
                        )
                        continue
                    chosen_type = (unit_type, unit_size)
                    break

                if bundle is None:
                    break

                try:
                    self.player.economy.subtract_points(bundle.cost)
                except Exception as exc:
                    try:
                        shutil.rmtree(bundle.folder, ignore_errors=True)
                    except Exception:
                        pass
                    log_error(
                        "Nie udało się odjąć PE za zakup",
                        commander_id=commander.id,
                        token_id=bundle.token_id,
                        cost=bundle.cost,
                        error=str(exc),
                    )
                    break
                entry_budget -= bundle.cost
                remaining_budget -= bundle.cost
                token_counts[commander.id] = token_counts.get(commander.id, 0) + 1

                event = {
                    'turn': getattr(self.player, 'current_turn', None),
                    'commander_id': commander.id,
                    'token_id': bundle.token_id,
                    'cost': bundle.cost,
                    'category': category,
                    'focus': focus,
                    'unit_type': chosen_type[0] if chosen_type else None,
                    'unit_size': chosen_type[1] if chosen_type else None,
                    'folder': bundle.folder.as_posix(),
                }
                events.append(event)
                purchase_history.append(event)
                per_commander_events[commander.id].append(event)

                log_general(
                    "Zakupiono jednostkę",
                    "INFO",
                    commander_id=commander.id,
                    token_id=bundle.token_id,
                    unit_type=chosen_type[0] if chosen_type else None,
                    unit_size=chosen_type[1] if chosen_type else None,
                    cost=bundle.cost,
                    category=category,
                    focus=focus,
                    folder=event['folder'],
                    turn=event['turn'],
                    remaining_budget=remaining_budget,
                )

                if remaining_budget <= 0:
                    break

        if per_commander_events:
            for commander in commanders:
                commander_events = per_commander_events.get(commander.id)
                if not commander_events:
                    continue
                existing = getattr(commander, "ai_purchase_events", None)
                if not isinstance(existing, list):
                    existing = []
                    setattr(commander, "ai_purchase_events", existing)
                existing.extend(commander_events)

        spent = sum(event['cost'] for event in events)
        return events, spent

    def _recipe_candidates(self, category: str, focus: Optional[str]) -> List[Tuple[str, str]]:
        mapping = {
            'infantry': [('P', 'Pluton'), ('P', 'Kompania')],
            'armor': [('TC', 'Pluton'), ('TŚ', 'Pluton'), ('TL', 'Pluton')],
            'artillery': [('AC', 'Pluton'), ('AL', 'Pluton'), ('AP', 'Pluton')],
            'support': [('Z', 'Pluton'), ('D', 'Pluton')],
            'resupply': [('Z', 'Pluton'), ('P', 'Pluton')],
            'offensive': [('TŚ', 'Pluton'), ('TL', 'Pluton'), ('P', 'Pluton')],
            'defensive': [('AL', 'Pluton'), ('P', 'Pluton')],
            'reserves': [('P', 'Kompania'), ('P', 'Pluton')],
            'general': [('P', 'Pluton')],
        }

        candidates = mapping.get(category, mapping['general']).copy()
        if focus == 'armor' and ('TŚ', 'Pluton') not in candidates:
            candidates.insert(0, ('TŚ', 'Pluton'))
        if ('P', 'Pluton') not in candidates:
            candidates.append(('P', 'Pluton'))
        return candidates

    def _select_purchase_commander(self, commanders: List[Player], token_counts: Dict[int, int]) -> Optional[Player]:
        if not commanders:
            return None
        return min(
            commanders,
            key=lambda cmd: (token_counts.get(cmd.id, 0), cmd.id),
        )

    def _purchase_focus(self, category: str, war_state: WarState) -> str:
        if category == 'support':
            if war_state == WarState.LOSING:
                return 'engineers+aa'
            if war_state == WarState.WINNING:
                return 'bridge+logistics'
            return 'logistics'
        if category == 'armor':
            return 'heavy' if war_state != WarState.LOSING else 'medium'
        if category == 'artillery':
            return 'counter-battery' if war_state == WarState.EVEN else 'off-map'
        if category == 'infantry':
            return 'motorized' if war_state == WarState.WINNING else 'regular'
        if category == 'offensive':
            return 'armored spearhead'
        if category == 'reserves':
            return 'defensive reserves'
        if category == 'resupply':
            return 'fuel+cv kits'
        return 'mixed'

    def _log_turn_summary(
        self,
        *,
        game_engine,
        war_state: WarState,
        total_pe: int,
        reserve_planned: int,
        reserve_effective: int,
        commander_pool_planned: int,
        commander_pool_spent: int,
        purchase_planned: int,
        purchase_effective: int,
        commanders: List[Dict[str, Any]],
        support_needs: Dict[str, Any],
        purchases_plan: List[Dict[str, Any]],
        allocation: Dict[int, int],
    ) -> None:
        turn_number = getattr(game_engine, 'turn', None)
        commander_snapshot = [dict(entry) for entry in commanders]
        purchases_snapshot = [dict(entry) for entry in purchases_plan]

        summary_payload = {
            'turn': turn_number,
            'nation': self.player.nation,
            'war_state': war_state.value,
            'vp_diff': self._last_vp_diff,
            'token_diff': self._last_token_diff,
            'total_pe_available': total_pe,
            'reserve_planned': reserve_planned,
            'reserve_effective': reserve_effective,
            'commander_pool_planned': commander_pool_planned,
            'commander_pool_spent': commander_pool_spent,
            'purchase_planned': purchase_planned,
            'purchase_effective': purchase_effective,
            'support_fuel_total': support_needs.get('fuel'),
            'support_repair_total': support_needs.get('repair'),
            'commander_allocations': commander_snapshot,
            'purchase_plan': purchases_snapshot,
            'allocation_raw': allocation,
        }

        log_general(
            "Podsumowanie decyzji Generała",
            "INFO",
            **summary_payload,
        )

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