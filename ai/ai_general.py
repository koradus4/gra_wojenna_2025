"""
AI General - Computer player controller
"""

import datetime
import json
import csv
import re
import uuid
import traceback
from enum import Enum, auto
import datetime, csv, json

# Proste stałe progowe ekonomii (można później przenieść do config)
MIN_BUY = 30          # Poniżej – HOLD
MIN_ALLOCATE = 60     # Od tej wartości (i gdy mamy już trochę armii) rozważ ALLOCATE
ALLOC_RATIO = 0.6     # Procent środków przekazywany dowódcom przy ALLOCATE
MAX_UNITS_PER_TURN = 2  # Limit zakupów na turę (anty-spam)
LOW_FUEL_PERCENT_THRESHOLD = 30   # % paliwa poniżej którego jednostka uznana za low-fuel
LOW_FUEL_UNITS_RATIO_TRIGGER = 0.30  # Jeśli >=30% jednostek ma niski poziom paliwa -> priorytet ALLOCATE (regeneracja)
UNSPENT_CAP = 80  # Skala do kar za niewydane punkty dowódcy


class EconAction(Enum):
    PURCHASE = auto()
    ALLOCATE = auto()
    HOLD = auto()

class AIGeneral:
    def __init__(self, nationality, difficulty="medium"):
        self.nationality = nationality  # "german" or "polish"
        self.difficulty = difficulty
        self.is_ai = True
        mapping = {"polish": "Polska", "german": "Niemcy", "pl": "Polska", "de": "Niemcy"}
        self.display_nation = mapping.get(str(nationality).lower(), nationality)
        # Flagi i pamięć stanu między turami
        self.debug = False  # Ustaw True jeśli chcesz widzieć surowe DBG tok=...
        self._last_action = None
        self._last_lowfuel_ratio = 0.0
        self._prev_commander_points = {}
    
    @staticmethod
    def _norm(txt):
        return str(txt).strip().lower() if txt is not None else ''
    
    def make_turn(self, game_engine):
        """Główny przebieg tury AI Generała."""
        print(f"\n🤖 === AI GENERAŁ {self.display_nation.upper()} - ROZPOCZĘCIE TURY ===")
        # Numer tury (obsługa dwóch możliwych atrybutów)
        self._current_turn = getattr(game_engine, 'turn_number', None) or getattr(game_engine, 'current_turn', None)
        current_player = getattr(game_engine, 'current_player_obj', None)
        if not current_player:
            print("❌ Błąd: Nie znaleziono aktywnego gracza AI")
            return
        print(f"👤 Aktywny gracz: {current_player.nation} {current_player.role} (ID: {current_player.id})")
        # Analizy
        self.analyze_economy(current_player)
        self.analyze_units(game_engine, current_player)
        # Faza strategiczna zależna od poziomu paliwa
        low_ratio = getattr(self, '_low_fuel_ratio', 0.0)
        self._phase = 'REGEN' if low_ratio >= LOW_FUEL_UNITS_RATIO_TRIGGER else 'BUILD'
        # Decyzje strategiczne (purchase/allocate/hold)
        self.make_strategic_decisions(game_engine, current_player)
        print(f"✅ AI GENERAŁ {self.display_nation.upper()} - KONIEC TURY\n")
        
    def analyze_economy(self, player):
        """Analizuje stan ekonomiczny"""
        print("\n💰 === ANALIZA EKONOMII ===")
        
        if not hasattr(player, 'economy') or not player.economy:
            print("❌ Brak systemu ekonomii dla gracza")
            return
            
        points_data = player.economy.get_points()
        economic_points = points_data.get('economic_points', 0)
        special_points = points_data.get('special_points', 0)
        
        print(f"💵 Punkty ekonomiczne: {economic_points}")
        print(f"⭐ Punkty specjalne: {special_points}")
        
        # Ocena sytuacji ekonomicznej
        if economic_points >= 50:
            print("✅ Sytuacja ekonomiczna: DOBRA - można inwestować")
        elif economic_points >= 20:
            print("⚠️ Sytuacja ekonomiczna: ŚREDNIA - ostrożnie z wydatkami")
        else:
            print("❌ Sytuacja ekonomiczna: ZŁA - oszczędzaj!")
            
    def analyze_units(self, game_engine, player):
        """Analizuje stan jednostek i zapisuje metryki (low fuel ratio)."""
        print("\n🪖 === ANALIZA JEDNOSTEK ===")

        try:
            my_units = game_engine.get_visible_tokens(player)
        except Exception:
            my_units = []

        if not my_units:
            print("❌ Brak jednostek do analizy")
            # Reset metryk gdy brak jednostek
            self._low_fuel_units = 0
            self._total_units_last_scan = 0
            self._low_fuel_ratio = 0.0
            return

        print(f"📊 Liczba jednostek: {len(my_units)}")

        low_fuel_units = []
        low_combat_units = []
        healthy_units = []

        for unit in my_units:
            max_fuel = max(getattr(unit, 'maxFuel', 0), 1)
            cur_fuel = getattr(unit, 'currentFuel', 0)
            fuel_percent = (cur_fuel / max_fuel) * 100
            combat_value = getattr(unit, 'combat_value', 0)
            print(f"  🎯 {getattr(unit,'id','?')[:20]}... - Paliwo: {cur_fuel}/{max_fuel} ({fuel_percent:.0f}%), Combat: {combat_value}")
            if fuel_percent < LOW_FUEL_PERCENT_THRESHOLD:
                low_fuel_units.append(unit)
            if combat_value < 3:
                low_combat_units.append(unit)
            else:
                healthy_units.append(unit)

        print(f"✅ Jednostki w dobrej kondycji: {len(healthy_units)}")
        print(f"⛽ Jednostki z niskim paliwem: {len(low_fuel_units)}")
        print(f"💥 Jednostki z niskim combat value: {len(low_combat_units)}")

        total = len(my_units)
        self._low_fuel_units = len(low_fuel_units)
        self._total_units_last_scan = total
        self._low_fuel_ratio = (len(low_fuel_units) / total) if total else 0.0
        # Dodatkowy podgląd ratio
        print(f"📈 Low fuel ratio: {self._low_fuel_ratio:.2f} (trigger {LOW_FUEL_UNITS_RATIO_TRIGGER:.2f})")
        
    def decide_action(self, player, game_engine):
        """Wybiera akcję ekonomiczną na tę turę.
        Kryteria minimalne:
         - econ < MIN_BUY -> HOLD
         - econ >= MIN_ALLOCATE i mamy >=6 własnych jednostek -> ALLOCATE
         - (nowe) jeśli wysoki odsetek jednostek z niskim paliwem (>=LOW_FUEL_UNITS_RATIO_TRIGGER) oraz econ >= MIN_BUY -> ALLOCATE (regeneracja)
         - inaczej PURCHASE
        Zwraca (EconAction, metrics_dict)
        """
        econ = player.economy.get_points().get('economic_points', 0)
        try:
            own_units = len(game_engine.get_visible_tokens(player))
        except Exception:
            own_units = 0
        low_ratio = getattr(self, '_low_fuel_ratio', 0.0)
        metrics = {
            'econ': econ,
            'own_units': own_units,
            'min_buy': MIN_BUY,
            'min_allocate': MIN_ALLOCATE,
            'alloc_ratio': ALLOC_RATIO,
            'low_fuel_ratio': round(low_ratio, 3),
            'low_fuel_trigger': LOW_FUEL_UNITS_RATIO_TRIGGER,
            'phase': getattr(self, '_phase', 'BUILD')
        }
        # Jeśli poprzednio ALLOCATE na paliwo a sytuacja już wróciła (cooldown) – preferuj zakup
        recovered = (self._last_action == EconAction.ALLOCATE and self._last_lowfuel_ratio >= LOW_FUEL_UNITS_RATIO_TRIGGER and low_ratio < (LOW_FUEL_UNITS_RATIO_TRIGGER/2))
        if econ < MIN_BUY:
            metrics['rule'] = 'econ<MIN_BUY'
            self._last_action = EconAction.HOLD; self._last_lowfuel_ratio = low_ratio
            return EconAction.HOLD, metrics
        # Priorytet regen paliwa przed zwykłym progiem alokacji
        if low_ratio >= LOW_FUEL_UNITS_RATIO_TRIGGER and econ >= MIN_BUY:
            metrics['rule'] = 'low_fuel_allocate'
            self._last_action = EconAction.ALLOCATE; self._last_lowfuel_ratio = low_ratio
            return EconAction.ALLOCATE, metrics
        if not recovered and econ >= MIN_ALLOCATE and own_units >= 6:
            metrics['rule'] = 'econ>=MIN_ALLOCATE & own_units>=6'
            self._last_action = EconAction.ALLOCATE; self._last_lowfuel_ratio = low_ratio
            return EconAction.ALLOCATE, metrics
        if recovered:
            metrics['rule'] = 'recovered_after_regen'
            self._last_action = EconAction.PURCHASE; self._last_lowfuel_ratio = low_ratio
            return EconAction.PURCHASE, metrics
        metrics['rule'] = 'default_purchase'
        self._last_action = EconAction.PURCHASE; self._last_lowfuel_ratio = low_ratio
        return EconAction.PURCHASE, metrics

    def allocate_points(self, player, game_engine, state=None):
        """Ważone przekazanie części punktów ekonomicznych dowódcom.
        Wagi bazują na brakach: supply, artyleria, avg_fuel, mała liczba jednostek, kara za duże niewydane zasoby.
        Zwraca (allocated_total, commanders_count, weights_dict).
        """
        econ_points = player.economy.get_points().get('economic_points', 0)
        if econ_points <= 0:
            return 0, 0, {}
        commanders = [p for p in (getattr(game_engine, 'players', []) or []) if p.nation == player.nation and p.role == 'Dowódca']
        if not commanders:
            return 0, 0, {}
        if state is None:
            state = self._gather_state(game_engine, player, commanders)
        per_c = state.get('per_commander', {})
        weights = {}
        details = {}
        for c in commanders:
            data = per_c.get(c.id, {})
            base = 0.1
            add_supply = 0.4 if not data.get('has_supply') else 0.0
            add_art = 0.3 if not data.get('has_artillery') else 0.0
            add_fuel = 0.2 if data.get('avg_fuel', 1.0) < 0.6 else 0.0
            tu = data.get('total_units', 0)
            add_units = 0.0
            if tu < 3:
                add_units = (3 - tu) * 0.1
            # Kara – realne niewydane punkty przed alokacją
            unspent = 0
            if hasattr(getattr(c, 'economy', None), 'get_points'):
                unspent = c.economy.get_points().get('economic_points', 0)
            else:
                unspent = getattr(getattr(c,'economy',None), 'economic_points', 0) or 0
            penalty = min(0.4, unspent / max(1, UNSPENT_CAP))
            w = base + add_supply + add_art + add_fuel + add_units - penalty
            if w < 0.05:
                w = 0.05
            weights[c.id] = round(w, 3)
            details[c.id] = {
                'baza': round(base,2),
                'brak_zaop': round(add_supply,2),
                'brak_art': round(add_art,2),
                'niskie_paliwo': round(add_fuel,2),
                'malo_jednostek': round(add_units,2),
                'kara_niewydane': round(penalty,2),
                'suma': round(w,3),
                'unspent': unspent,
                'avg_fuel': data.get('avg_fuel'),
                'total_units': tu
            }
        total_w = sum(weights.values()) or 1.0
        norm_weights = {cid: round(w/total_w, 3) for cid, w in weights.items()}
        to_distribute = int(econ_points * ALLOC_RATIO)
        if to_distribute <= 0:
            return 0, len(commanders), weights
        distributed = 0
        allocations = {}
        # Najpierw proporcjonalnie
        for cid, w in weights.items():
            share = int(to_distribute * (w / total_w))
            allocations[cid] = share
            distributed += share
        # Rozdaj resztę po 1
        remainder = to_distribute - distributed
        if remainder > 0:
            # posortuj wg największej wagi
            for cid,_w in sorted(weights.items(), key=lambda kv: kv[1], reverse=True):
                if remainder <= 0:
                    break
                allocations[cid] += 1
                distributed += 1
                remainder -= 1
        # Odjęcie u generała
        player.economy.economic_points = max(0, player.economy.economic_points - distributed)
        # Dodanie dowódcom
        for c in commanders:
            add = allocations.get(c.id, 0)
            if add <= 0:
                continue
            if not hasattr(c.economy, 'economic_points'):
                c.economy.economic_points = 0
            c.economy.economic_points += add
        # Log
        print(f"📦 Przydzielono (ALLOCATE) łącznie {distributed} punktów ekonomicznych (60% budżetu).")
        for c in commanders:
            cid = c.id
            det = details.get(cid, {})
            print(f"   ➡️ Dowódca {cid}: otrzymał {allocations.get(cid,0)} pkt | waga={weights.get(cid)} (znorm={norm_weights.get(cid)}) -> skład: baza {det.get('baza')} + brak zaop {det.get('brak_zaop')} + brak art {det.get('brak_art')} + niskie paliwo {det.get('niskie_paliwo')} + mało jednostek {det.get('malo_jednostek')} - kara niewydane {det.get('kara_niewydane')} (niewydane wcześniej: {det.get('unspent')})")
        return distributed, len(commanders), {'raw': weights, 'norm': norm_weights, 'details': details, 'allocations': allocations}

    def _log_action(self, player, action: EconAction, econ_before, econ_after, metrics, allocated_total=0, units_bought=0):
        """Log ogólny akcji ekonomicznej AI (osobny od logu pojedynczych zakupów)."""
        from pathlib import Path
        logs_dir = Path('logs')
        logs_dir.mkdir(exist_ok=True)
        date_tag = datetime.datetime.now().strftime('%Y%m%d')
        path = logs_dir / f'ai_actions_{date_tag}.csv'
        is_new = not path.exists()
        row = {
            'timestamp': datetime.datetime.now().isoformat(timespec='seconds'),
            'nation': getattr(player, 'nation', self.display_nation),
            'action': action.name,
            'econ_before': econ_before,
            'econ_after': econ_after,
            'allocated_total': allocated_total,
            'units_bought': units_bought,
            'rule': metrics.get('rule'),
            'metrics_json': json.dumps(metrics, ensure_ascii=False)
        }
        fieldnames = list(row.keys())
        with open(path, 'a', newline='', encoding='utf-8') as f:
            w = csv.DictWriter(f, fieldnames=fieldnames)
            if is_new:
                w.writeheader()
            w.writerow(row)
        print(f"🗂️ Zalogowano akcję AI: {action.name}")

    def make_strategic_decisions(self, game_engine, player):
        """Podejmuje decyzje strategiczne (rozszerzone o PURCHASE/ALLOCATE/HOLD)."""
        print("\n🎯 === DECYZJE STRATEGICZNE ===")
        econ_before = player.economy.get_points().get('economic_points', 0)
        action, metrics = self.decide_action(player, game_engine)
        faza_opis = 'REGEN (odbudowa paliwa)' if metrics.get('phase') == 'REGEN' else 'BUILD (rozbudowa armii)'
        rule_desc = self._friendly_action_reason(metrics.get('rule'))
        print(f"🔎 Decyzja ekonomiczna: {action.name} – {rule_desc} | Punkty: {econ_before} | Faza: {faza_opis}")
        units_bought = 0
        allocated_total = 0
        if action == EconAction.PURCHASE:
            self.consider_unit_purchase(game_engine, player, econ_before)
            ctx = getattr(self, '_last_decision_context', {})
            units_bought = ctx.get('units_bought', 0)
        elif action == EconAction.ALLOCATE:
            commanders = [p for p in (getattr(game_engine, 'players', []) or []) if p.nation == player.nation and p.role == 'Dowódca']
            state = self._gather_state(game_engine, player, commanders)
            allocated_total, cmd_cnt, weights = self.allocate_points(player, game_engine, state=state)
            metrics['allocation_weights'] = weights
            print(f"✅ Zakończono przydział punktów dla {cmd_cnt} dowódców.")
        else:
            print("⛔ HOLD – zatrzymuję punkty")
        econ_after = player.economy.get_points().get('economic_points', 0)
        self._log_action(player, action, econ_before, econ_after, metrics, allocated_total, units_bought)

    def consider_unit_purchase(self, game_engine, player, available_points):
        """Rozważa zakup jednostek - z limitem maksymalnej liczby zakupów."""
        print(f"🛒 Rozważam zakupy za {available_points} punktów:")
        if player.role != "Generał":
            print("📋 Dowódca - brak uprawnień do zakupów")
            return
        try:
            if hasattr(game_engine, 'players') and game_engine.players:
                all_players = game_engine.players
            else:
                all_players = []
            commanders = [p for p in all_players if p.nation == player.nation and p.role == "Dowódca"]
            if not commanders:
                print("⚠️ Brak dowódców – anuluję zakupy")
                return
            # Zbieranie stanu i budżet (zachowujemy starą ścieżkę jeśli incomplete)
            state = self._gather_state(game_engine, player, commanders)
            purchase_budget, reserve, budget_diag = self._decide_budget(available_points, state)
            print(f"📊 Budżet przydzielony na zakupy: {purchase_budget} (rezerwa: {reserve})")
            priorities = self._compute_commander_priorities(state, commanders)
            purchase_plans = self.plan_purchases(purchase_budget, commanders, priorities=priorities, state=state)
            # Limitujemy liczbę zakupów
            purchase_plans = purchase_plans[:MAX_UNITS_PER_TURN]
            bought = 0
            total_cost_spent = 0
            # Zapisz kontekst do późniejszego logowania pojedynczych zakupów
            self._last_decision_context = {
                'state': state,
                'budget_diag': budget_diag,
                'budget_allocated': purchase_budget,
                'reserve': reserve,
            }
            for plan in purchase_plans:
                print(f"➡️ ZAKUP: {plan.get('type')} {plan.get('size')} (cmd={plan.get('commander_id')}, koszt={plan.get('cost')})")
                success = self.purchase_unit_programmatically(player, plan)
                if success:
                    bought += 1
                    total_cost_spent += plan.get('cost', 0)
                else:
                    print("   ❌ Nieudany zakup – przerwam dalsze jeśli brak środków")
                    if player.economy.get_points().get('economic_points', 0) < MIN_BUY:
                        break
            self._last_decision_context['units_bought'] = bought
            self._last_decision_context['total_cost_spent'] = total_cost_spent
        except Exception as e:
            print(f"❌ Błąd w zakupach AI: {e}")
            import traceback; traceback.print_exc()

    # === FAZA 1: ZBIERANIE STANU ===
    def _gather_state(self, game_engine, general_player, commanders):
        """Zbiera uproszczony stan do decyzji ekonomicznych.
        Zwraca dict z kluczami:
          global: {unit_counts_by_type, total_units}
          per_commander: { commander_id: {unit_counts_by_type, total_units, has_supply, has_artillery, avg_fuel} }
          enemy: {unit_counts_by_type, total_units, has_artillery, has_armor}
        (Na razie tylko podstawowe dane – można rozszerzyć później.)
        """
        result = {"global": {}, "per_commander": {}}
        try:
            norm_general = self._norm(getattr(general_player, 'nation', ''))
            commander_ids = {str(c.id) for c in commanders}
            all_tokens = []
            enemy_tokens = []
            if hasattr(game_engine, 'get_visible_tokens'):
                import re
                visible = game_engine.get_visible_tokens(general_player) or []
                for idx, tok in enumerate(visible):
                    nat_raw = getattr(tok, 'nation', None)
                    nat_norm = self._norm(nat_raw)
                    owner_raw = getattr(tok, 'owner', None)
                    owner_str = str(owner_raw) if owner_raw is not None else ''
                    # Wyciągnij wiodące cyfry jako owner_id (obsługa formatu '2 (Polska)' itp.)
                    m = re.match(r'^(\d+)', owner_str)
                    owner_id = m.group(1) if m else owner_str if owner_str.isdigit() else ''
                    own = False
                    reason = ''
                    if nat_norm and norm_general and nat_norm == norm_general:
                        own = True; reason = 'nation'
                    elif owner_id and owner_id in commander_ids.union({str(general_player.id)}):
                        own = True; reason = 'owner_id'
                    (all_tokens if own else enemy_tokens).append(tok)
                    if self.debug and idx < 12:  # szczegóły tylko w trybie debug
                        print(f"DBG tok={getattr(tok,'id','?')[:18]} nat={nat_raw} owner_raw={owner_raw} owner_id={owner_id} own={own} via={reason}")
                # Per dowódca
                for c in commanders:
                    comm_tokens = [t for t in all_tokens if self._match_commander_token(t, c.id)]
                    counts, fuel_vals = {}, []
                    for t in comm_tokens:
                        utype = self._extract_unit_type(t)
                        if not utype:
                            continue
                        counts[utype] = counts.get(utype, 0) + 1
                        mf = getattr(t, 'maxFuel', 0) or 0
                        cf = getattr(t, 'currentFuel', 0) or 0
                        if mf > 0:
                            fuel_vals.append(cf / mf)
                    result['per_commander'][c.id] = {
                        'unit_counts_by_type': counts,
                        'total_units': sum(counts.values()),
                        'has_supply': counts.get('Z',0) > 0,
                        'has_artillery': any(k in counts for k in ('AL','AC','AP')),
                        'avg_fuel': round((sum(fuel_vals)/len(fuel_vals)) if fuel_vals else 1.0, 2)
                    }
            # Global
            g_counts = {}
            for t in all_tokens:
                ut = self._extract_unit_type(t)
                if ut:
                    g_counts[ut] = g_counts.get(ut, 0) + 1
            result['global'] = {'unit_counts_by_type': g_counts, 'total_units': sum(g_counts.values())}
            # Enemy
            e_counts = {}
            for t in enemy_tokens:
                ut = self._extract_unit_type(t)
                if ut:
                    e_counts[ut] = e_counts.get(ut, 0) + 1
            result['enemy'] = {
                'unit_counts_by_type': e_counts,
                'total_units': sum(e_counts.values()),
                'has_artillery': any(k in e_counts for k in ('AL','AC','AP')),
                'has_armor': any(k in e_counts for k in ('TC','TŚ','TL','TS'))
            }
            g = result['global']
            print(f"🛰️ Nasze jednostki: suma {g.get('total_units')} | typy: {g.get('unit_counts_by_type')}")
            e = result.get('enemy', {})
            print(f"🎯 Widziane wrogie jednostki: {e.get('total_units')} (artyleria={e.get('has_artillery')} pancerne={e.get('has_armor')})")
            for cid, data in result['per_commander'].items():
                print(f"   🧭 Dowódca {cid}: {data['total_units']} jednostek | paliwo śr. {data['avg_fuel']} | supply={'TAK' if data['has_supply'] else 'NIE'} | artyleria={'TAK' if data['has_artillery'] else 'NIE'} -> {data['unit_counts_by_type']}")
        except Exception as e:
            print(f"⚠️ _gather_state błąd: {e}")
        return result

    def _friendly_action_reason(self, code):
        mapping = {
            'econ<MIN_BUY': 'Za mało punktów – oszczędzam',
            'low_fuel_allocate': 'Wysoki odsetek jednostek z małym paliwem – priorytet uzupełnień',
            'econ>=MIN_ALLOCATE & own_units>=6': 'Mamy solidną armię i wysoki budżet – wzmacniam dowódców',
            'default_purchase': 'Standard – inwestuję w nowe jednostki',
            'recovered_after_regen': 'Paliwo odbudowane – wracam do zakupów'
        }
        return mapping.get(code, code or '')

    def _match_commander_token(self, token, commander_id):
        """Sprawdza czy token należy do danego dowódcy (obsługa owner z dopiskiem)."""
        import re
        owner_raw = getattr(token, 'owner', None)
        if owner_raw is None:
            return False
        m = re.match(r'^(\d+)', str(owner_raw))
        oid = m.group(1) if m else str(owner_raw)
        return oid == str(commander_id)

    def _extract_unit_type(self, token):
        """Próbuje ustalić typ jednostki: pole unitType/unit_type lub z ID (prefiks)."""
        ut = getattr(token, 'unitType', None) or getattr(token, 'unit_type', None)
        if ut:
            return ut
        tid = getattr(token, 'id', '') or ''
        # Wzorce np.: 'AL_Kompania__2_...', 'nowy_Z_Pluton__2_...', 'P_Batalion__3_...'
        import re
        m = re.match(r'^(?:nowy_)?([A-ZŚŁĆŻŹ]{1,2})_', tid)
        if m:
            return m.group(1)
        return None

    # === FAZA 2: PODZIAŁ BUDŻETU ===
    def _decide_budget(self, available_points, state):
        """Prosty podział budżetu: jeżeli brak artylerii lub zaopatrzenia – wydaj więcej.
        Zwraca (purchase_budget, reserve, diagnostics).
        """
        per_commander = state.get('per_commander', {})
        enemy = state.get('enemy', {})
        need_supply = any(not data['has_supply'] for data in per_commander.values()) if per_commander else False
        need_art = any(not data['has_artillery'] for data in per_commander.values()) if per_commander else False
        enemy_total = enemy.get('total_units', 0) or 0
        own_total = state.get('global', {}).get('total_units', 0) or 0
        pressure = enemy_total / (own_total + 1) if own_total >= 0 else 0
        base_ratio = 0.5
        if need_supply:
            base_ratio += 0.1
        if need_art:
            base_ratio += 0.1
        if pressure > 1.2:
            base_ratio += 0.15
        elif pressure > 0.8:
            base_ratio += 0.05
        if enemy.get('has_armor') and not any('T' in t for t in state.get('global', {}).get('unit_counts_by_type', {}).keys()):
            base_ratio += 0.1
        if base_ratio > 0.85:
            base_ratio = 0.85
        purchase_budget = int(available_points * base_ratio)
        reserve = available_points - purchase_budget
        print(f"⚖️ Budżet decyzja: need_supply={need_supply} need_art={need_art} pressure={pressure:.2f} ratio={base_ratio:.2f}")
        diagnostics = {
            'need_supply': need_supply,
            'need_art': need_art,
            'pressure': pressure,
            'enemy_has_armor': enemy.get('has_armor', False),
            'ratio': base_ratio
        }
        return purchase_budget, reserve, diagnostics
    
    def plan_purchases(self, available_points, commanders, max_purchases=None, priorities=None, state=None):
        """Planuje jakie jednostki kupić (publiczny interfejs)."""
        return self._plan_purchases_internal(available_points, commanders, max_purchases=max_purchases, priorities=priorities, state=state)

    def _plan_purchases_internal(self, available_points, commanders, max_purchases=None, priorities=None, state=None):
        """Wewnętrzna implementacja planowania zakupów.
        priorities: opcjonalny dict commander_id -> waga (float) używany do rotacji przydziału.
        Jeśli brak priorytetów używa starej prostej rotacji.
        """
        print(f"\n📋 Planowanie zakupów (budżet: {available_points} pkt)")
        from core.unit_factory import PRICE_DEFAULTS

        unit_type_order = ["P","K","TC","TŚ","TL","TS","AC","AL","AP","Z","D","G"]
        sizes = ["Pluton","Kompania","Batalion"]
        unit_templates = []
        prio = 1
        for sz in sizes:
            for ut in unit_type_order:
                base_cost = PRICE_DEFAULTS.get(sz, {}).get(ut)
                if base_cost is None:
                    continue
                if base_cost > available_points * 1.2:
                    continue
                human_name = {"P": "Piechota","K": "Kawaleria","TC": "Czołg ciężki","TŚ": "Czołg średni","TL": "Czołg lekki","TS": "Sam. pancerny","AC": "Artyleria ciężka","AL": "Artyleria lekka","AP": "Artyleria plot","Z": "Zaopatrzenie","D": "Dowództwo","G": "Generał"}.get(ut, ut)
                unit_templates.append({"type": ut, "size": sz, "cost": int(base_cost), "priority": prio, "name": f"{human_name} {sz}"})
                prio += 1

        purchases = []
        budget = available_points
        max_purchases_per_turn = max_purchases if max_purchases is not None else min(6, len(commanders) * 3)

        unit_templates.sort(key=lambda x: x['priority'])
        purchase_attempts = 0
        template_index = 0
        total_templates = len(unit_templates)
        if priorities:
            total_w = sum(priorities.values()) or 1.0
            norm = {cid: (w/total_w) for cid, w in priorities.items()}
            scale = 100
            rot = []
            for cid, w in norm.items():
                count = max(1, int(w * scale))
                rot.extend([cid] * count)
            commander_rotation = rot if rot else [c.id for c in commanders]
        else:
            commander_rotation = [c.id for c in commanders]
        rot_len = len(commander_rotation)
        rot_index = 0
        while budget >= 15 and len(purchases) < max_purchases_per_turn and purchase_attempts < 300:
            if state:
                template = self._select_template(unit_templates, purchases, budget, state)
                if template is None:
                    print("⚠️ Heurystyka nie znalazła pasującego szablonu – fallback rotacja")
                    template = unit_templates[template_index % total_templates]
            else:
                template = unit_templates[template_index % total_templates]

            existing_pairs = {(p['type'], p['size']) for p in purchases}
            if not state and (template['type'], template['size']) in existing_pairs and len(existing_pairs) < total_templates:
                template_index += 1
                purchase_attempts += 1
                continue
            if budget >= template['cost']:
                if priorities:
                    commander_id = commander_rotation[rot_index % rot_len]
                    rot_index += 1
                else:
                    commander_id = commanders[len(purchases) % len(commanders)].id
                purchase = template.copy()
                purchase['commander_id'] = commander_id
                supports, added_cost = self.select_supports_for_unit(template, budget - template['cost'])
                purchase['supports'] = supports
                purchase['cost'] = template['cost'] + added_cost
                purchases.append(purchase)
                budget -= purchase['cost']
                print(f"📦 Zaplanowano: {template['name']} dla dowódcy {commander_id} ({purchase['cost']} pkt) wsparcia={supports}")
            template_index += 1
            purchase_attempts += 1

        print(f"💰 Pozostały budżet: {budget} pkt")
        print(f"🎯 Zaplanowano {len(purchases)} zakupów")
        return purchases

    def _select_template(self, unit_templates, purchases, budget, state):
        """Heurystyczny wybór szablonu jednostki na podstawie braków.
        Zwraca dict szablonu lub None.
        Reguły (kolejność):
          1. Brak zaopatrzenia -> Z (najmniejszy rozmiar dostępny)
          2. Brak artylerii -> AL potem AC/AP
          3. Wróg ma pancerz, nasze pancerne < 1 -> TL/TŚ (najtańsze)
          4. Piechota < 3 -> P
          5. Mobilność (brak K i TS) -> K
          6. Dywersyfikacja – weź typ którego najmniej w ratio
        Rozmiar: dla uzupełnień krytycznych Pluton, dla piechoty jeśli budżet pozwala Kompania.
        """
        global_counts = state.get('global', {}).get('unit_counts_by_type', {})
        enemy = state.get('enemy', {})
        # Dodaj do counts także planowane (purchases)
        planned_counts = global_counts.copy()
        for p in purchases:
            planned_counts[p['type']] = planned_counts.get(p['type'], 0) + 1
        def find_template(types_pref, size_pref_order):
            for t in types_pref:
                for s in size_pref_order:
                    cand = next((u for u in unit_templates if u['type']==t and u['size']==s and u['cost']<=budget), None)
                    if cand:
                        return cand
            return None
        # 1 Supply
        if planned_counts.get('Z',0)==0:
            tpl = find_template(['Z'], ['Pluton','Kompania','Batalion'])
            if tpl:
                print("🧪 Heurystyka: brak zaopatrzenia -> wybieram", tpl['name'])
                return tpl
        # 2 Artillery
        if all(planned_counts.get(x,0)==0 for x in ('AL','AC','AP')):
            tpl = find_template(['AL','AC','AP'], ['Pluton','Kompania'])
            if tpl:
                print("🧪 Heurystyka: brak artylerii ->", tpl['name'])
                return tpl
        # 3 Enemy armor
        has_enemy_armor = enemy.get('has_armor')
        own_armor = sum(planned_counts.get(x,0) for x in ('TL','TŚ','TC','TS'))
        if has_enemy_armor and own_armor==0:
            tpl = find_template(['TL','TŚ','TS','TC'], ['Pluton','Kompania'])
            if tpl:
                print("🧪 Heurystyka: reakcja na pancerz wroga ->", tpl['name'])
                return tpl
        # 4 Infantry baseline
        if planned_counts.get('P',0) < 3:
            size_order = ['Kompania','Pluton'] if budget>40 else ['Pluton']
            tpl = find_template(['P'], size_order+['Batalion'])
            if tpl:
                print("🧪 Heurystyka: uzupełniam piechotę ->", tpl['name'])
                return tpl
        # 5 Mobility
        if planned_counts.get('K',0)==0 and planned_counts.get('TS',0)==0:
            tpl = find_template(['K','TS'], ['Pluton','Kompania'])
            if tpl:
                print("🧪 Heurystyka: potrzebna mobilność ->", tpl['name'])
                return tpl
        # 6 Diversity – wybierz typ o najniższym (count / (1 + waga))
        type_counts = {}
        for u in unit_templates:
            type_counts[u['type']] = planned_counts.get(u['type'],0)
        sorted_types = sorted(type_counts.items(), key=lambda kv: kv[1])
        for t,_cnt in sorted_types:
            tpl = find_template([t], ['Pluton','Kompania','Batalion'])
            if tpl:
                print("🧪 Heurystyka: dywersyfikacja ->", tpl['name'])
                return tpl
        return None

    # === PRIORYTETY DOWÓDCÓW ===
    def _compute_commander_priorities(self, state, commanders):
        """Nadaje wagi dowódcom na podstawie braków i stanu paliwa.
        Heurystyka (sumuje czynniki):
          brak zaopatrzenia +0.4
          brak artylerii +0.3
          avg_fuel < 0.6 +0.15
          mało jednostek (<3) + (3-total_units)*0.1
        Minimalna waga 0.1 aby nikt nie był całkiem pominięty.
        Zwraca dict commander_id -> weight.
        """
        out = {}
        per_c = state.get('per_commander', {})
        for c in commanders:
            data = per_c.get(c.id, {})
            w = 0.0
            if not data.get('has_supply'):
                w += 0.4
            if not data.get('has_artillery'):
                w += 0.3
            avg_fuel = data.get('avg_fuel', 1.0)
            if avg_fuel < 0.6:
                w += 0.15
            total_units = data.get('total_units', 0)
            if total_units < 3:
                w += (3 - total_units) * 0.1
            if w < 0.1:
                w = 0.1
            out[c.id] = round(w, 3)
        return out

    def select_supports_for_unit(self, template, remaining_points):
        """Dobiera listę wsparć (supports) mieszczącą się w remaining_points. Zwraca (lista, dodatkowy_koszt)."""
        try:
            from core.unit_factory import ALLOWED_SUPPORT, SUPPORT_UPGRADES, base_price
            unit_type = template['type']
            unit_size = template['size']
            base_cost = template['cost']
            allowed = ALLOWED_SUPPORT.get(unit_type, [])
            supports = []
            extra_cost = 0

            # Strategiczne priorytety wsparć wg typu
            priority_order = []
            if unit_type == 'P':
                priority_order = ["sekcja km.ppanc", "drużyna granatników", "przodek dwukonny"]
            elif unit_type in ('AC','AL','AP'):
                priority_order = ["obserwator", "ciagnik altyleryjski", "sam. ciezarowy Fiat 621"]
            elif unit_type == 'K':
                priority_order = ["sekcja ckm"]
            elif unit_type in ('TL','TC','TS','TŚ'):
                priority_order = ["obserwator"]
            elif unit_type == 'Z':
                priority_order = ["drużyna granatników"]

            # Filtruj dozwolone i unikalne
            ordered = [s for s in priority_order if s in allowed]
            # Dodaj ewentualnie transport jeśli korzyść ruchu i budżet > próg
            for sup in ordered:
                upg = SUPPORT_UPGRADES.get(sup)
                if not upg:
                    continue
                cost_inc = upg['purchase'] + upg.get('unit_maintenance',0)  # użyj purchase do limitu budżetu
                if cost_inc <= remaining_points - extra_cost:
                    supports.append(sup)
                    extra_cost += upg['purchase']

            # Ograniczenie: maks 1 transport – zapewnione priorytetami (tylko jeden z listy transportów tutaj)
            return supports, extra_cost
        except Exception as e:
            print(f"⚠️ Błąd select_supports_for_unit: {e}")
            return [], 0
        
    def purchase_unit_programmatically(self, player, purchase_plan):
        """Programowo kupuje jednostkę jak TokenShop"""
        print(f"\n� Kupuję jednostkę: {purchase_plan['name']}")
        
        try:
            from pathlib import Path
            import json
            import datetime
            
            commander_id = purchase_plan['commander_id']
            
            # Sprawdź czy mamy wystarczająco punktów
            current_points = player.economy.get_points()['economic_points']
            cost = purchase_plan['cost']
            
            print(f"💳 Sprawdzam finanse: {current_points} pkt (koszt: {cost} pkt)")
            
            if current_points < cost:
                print(f"❌ Niewystarczające środki: {current_points} < {cost}")
                return False
            
            # Utwórz folder dla żetonu w strukturze kreatora
            folder_name = f"nowe_dla_{commander_id}"
            tokens_dir = Path("assets/tokens")
            target_dir = tokens_dir / folder_name
            target_dir.mkdir(parents=True, exist_ok=True)
            
            print(f"📁 Tworzę folder: {target_dir}")
            
            # Generuj unikalne ID jak w kreatora
            now = datetime.datetime.now().strftime("%Y%m%d%H%M%S")
            unit_type = purchase_plan["type"]
            unit_size = purchase_plan["size"]
            
            # Określ kod nacji
            if commander_id in [1, 2, 3]:  # Polska
                nation_code = "PL"
                nation_name = "Polska"
            else:  # Niemcy (4, 5, 6)
                nation_code = "N"
                nation_name = "Niemcy"
            
            label = f"{unit_size} {nation_code}"
            token_id = f"nowy_{unit_type}_{unit_size}__{commander_id}_{label.replace(' ', '_')}_{now}"
            
            # Utwórz folder dla konkretnego tokena
            token_folder = target_dir / token_id
            token_folder.mkdir(exist_ok=True)
            
            print(f"🏷️  ID żetonu: {token_id}")
            
            # Przygotuj dane żetonu
            unit_data = self.prepare_unit_data(purchase_plan, commander_id, token_id, nation_name)
            
            # Zapisz JSON
            json_path = token_folder / "token.json"
            with open(json_path, "w", encoding="utf-8") as f:
                json.dump(unit_data, f, indent=2, ensure_ascii=False)
            
            print(f"💾 Zapisano JSON: {json_path}")
            
            # Utwórz obrazek żetonu
            img_path = token_folder / "token.png"
            self.create_token_image(purchase_plan, nation_name, img_path)
            
            print(f"🖼️  Utworzono obrazek: {img_path}")
            
            # Odejmij punkty
            player.economy.subtract_points(cost)
            remaining_points = player.economy.get_points()['economic_points']

            # Logowanie decyzji zakupowej
            try:
                self._log_purchase_decision(player, purchase_plan, current_points, remaining_points)
            except Exception as log_err:
                print(f"⚠️ Logger AI purchase błąd: {log_err}")
            
            print(f"💰 Płatność: -{cost} pkt (pozostało: {remaining_points} pkt)")
            print(f"✅ Żeton {purchase_plan['name']} utworzony pomyślnie!")
            
            return True
            
        except Exception as e:
            print(f"❌ Błąd podczas tworzenia żetonu: {e}")
            import traceback
            traceback.print_exc()
            return False
    
    def prepare_unit_data(self, purchase_plan, commander_id, token_id, nation_name):
        """Przygotowuje dane JSON dla żetonu wykorzystując wspólną fabrykę (pełna parytet z TokenShop)."""
        print("📝 Przygotowuję dane żetonu (fabryka)...")
        from core.unit_factory import compute_unit_stats, build_label_and_full_name

        unit_type = purchase_plan["type"]
        unit_size = purchase_plan["size"]

        # TODO: w przyszłości AI będzie wybierało wsparcia; na razie brak wsparć (parytet bazowy)
        supports = purchase_plan.get("supports", [])  # spodziewana lista nazw wsparć
        stats = compute_unit_stats(unit_type, unit_size, supports)
        name_parts = build_label_and_full_name(nation_name, unit_type, unit_size, str(commander_id))

        rel_img_path = f"assets/tokens/nowe_dla_{commander_id}/{token_id}/token.png"
        unit_data = {
            "id": token_id,
            "nation": nation_name,
            "unitType": unit_type,
            "unitSize": unit_size,
            "shape": "prostokąt",
            "label": name_parts["label"],
            "unit_full_name": name_parts["unit_full_name"],
            "move": stats.move,
            "attack": {"range": stats.attack_range, "value": stats.attack_value},
            "combat_value": stats.combat_value,
            "defense_value": stats.defense_value,
            "maintenance": stats.maintenance,
            "price": stats.price,
            "sight": stats.sight,
            "owner": str(commander_id),
            "image": rel_img_path,
            "w": 240,
            "h": 240
        }
        print(f"📊 Statystyki: ruch={stats.move}, atak={stats.attack_value}, obrona={stats.defense_value}, combat={stats.combat_value}, cena={stats.price}")
        return unit_data
    
    def create_token_image(self, purchase_plan, nation, img_path):
        """Tworzy obrazek żetonu - IDENTYCZNY z kreatorem"""
        print("🎨 Tworzę obrazek żetonu...")
        
        try:
            from PIL import Image, ImageDraw, ImageFont
            # Import funkcji z kreatora
            from edytory.token_editor_prototyp import create_flag_background
            
            # Podstawowe wymiary (jak w kreatora)
            width, height = 240, 240
            unit_type = purchase_plan["type"]
            unit_size = purchase_plan["size"]
            
            # IDENTYCZNA logika z token_shop.py
            base_bg = create_flag_background(nation, width, height)
            token_img = base_bg.copy()
            draw = ImageDraw.Draw(token_img)
            
            # Czarna ramka jak w kreatora
            draw.rectangle([0, 0, width, height], outline="black", width=6)
            
            # Pełne nazwy jednostek (jak w kreatora)
            unit_type_full = {
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
                "G": "Generał"
            }.get(unit_type, unit_type)
            
            # Symbole wojskowe (jak w kreatora)
            unit_symbol = {
                "Pluton": "***", 
                "Kompania": "I", 
                "Batalion": "II"
            }.get(unit_size, "")
            
            # Fonty (jak w kreatora)
            try:
                font_type = ImageFont.truetype("arialbd.ttf", 38)
                font_size = ImageFont.truetype("arial.ttf", 22)
                font_symbol = ImageFont.truetype("arialbd.ttf", 36)
            except Exception:
                font_type = font_size = font_symbol = ImageFont.load_default()
            
            margin = 12
            
            # Kolor tekstu dla nacji (jak w kreatora)
            text_color = self.get_text_color_for_nation(nation)
            
            # Zawijanie tekstu (jak w kreatora)
            def wrap_text(text, font, max_width):
                words = text.split()
                lines = []
                line = ""
                for w in words:
                    test = line + (" " if line else "") + w
                    if draw.textlength(test, font=font) <= max_width:
                        line = test
                    else:
                        if line:
                            lines.append(line)
                        line = w
                if line:
                    lines.append(line)
                return lines
            
            # Layout tekstu (jak w kreatora)
            max_text_width = int(width * 0.9)
            type_lines = wrap_text(unit_type_full, font_type, max_text_width)
            
            # Oblicz wysokości
            total_type_height = sum(draw.textbbox((0,0), line, font=font_type)[3] - draw.textbbox((0,0), line, font=font_type)[1] for line in type_lines)
            total_type_height += (len(type_lines)-1) * 4
            
            bbox_size = draw.textbbox((0,0), unit_size, font=font_size)
            size_height = bbox_size[3] - bbox_size[1]
            
            bbox_symbol = draw.textbbox((0,0), unit_symbol, font=font_symbol)
            symbol_height = bbox_symbol[3] - bbox_symbol[1]
            
            gap_type_to_size = margin * 2
            gap_size_to_symbol = 4
            total_height = total_type_height + gap_type_to_size + size_height + gap_size_to_symbol + symbol_height
            
            # Rysuj tekst (jak w kreatora)
            y = (height - total_height) // 2
            
            # Typ jednostki (wieloliniowy)
            for line in type_lines:
                bbox = draw.textbbox((0, 0), line, font=font_type)
                x = (width - (bbox[2] - bbox[0])) / 2
                draw.text((x, y), line, fill=text_color, font=font_type)
                y += bbox[3] - bbox[1] + 4
            
            y += gap_type_to_size - 4
            
            # Rozmiar jednostki
            bbox_size = draw.textbbox((0, 0), unit_size, font=font_size)
            x_size = (width - (bbox_size[2] - bbox_size[0])) / 2
            draw.text((x_size, y), unit_size, fill=text_color, font=font_size)
            
            y += bbox_size[3] - bbox_size[1] + gap_size_to_symbol
            
            # Symbol wojskowy
            bbox_symbol = draw.textbbox((0, 0), unit_symbol, font=font_symbol)
            x_symbol = (width - (bbox_symbol[2] - bbox_symbol[0])) / 2
            draw.text((x_symbol, y), unit_symbol, fill=text_color, font=font_symbol)
            
            # Zapisz
            token_img.save(img_path)
            print(f"✅ Obrazek zapisany: {img_path}")
            
        except Exception as e:
            print(f"⚠️  Błąd tworzenia obrazka: {e}")
            import traceback
            traceback.print_exc()
            # Fallback - prosty placeholder
            try:
                img = Image.new('RGB', (240, 240), (128, 128, 128))
                img.save(img_path)
            except:
                pass
    
    def get_text_color_for_nation(self, nation):
        """Określa kolor tekstu dla nacji (jak w kreatora)"""
        if nation == "Polska":
            return "black"
        elif nation == "Niemcy":
            return "white"
        else:
            return "black"

    # === LOGOWANIE ZAKUPÓW ===
    def _log_purchase_decision(self, player, purchase_plan, points_before, points_after):
        """Zapisuje szczegóły zakupu AI do pliku CSV (per dzień)."""
        from pathlib import Path
        import csv, datetime, json
        logs_dir = Path('logs')
        logs_dir.mkdir(exist_ok=True)
        date_tag = datetime.datetime.now().strftime('%Y%m%d')
        path = logs_dir / f'ai_purchases_{date_tag}.csv'
        is_new = not path.exists()
        ctx = getattr(self, '_last_decision_context', {})
        budget_diag = ctx.get('budget_diag', {})
        state = ctx.get('state', {})
        row = {
            'timestamp': datetime.datetime.now().isoformat(timespec='seconds'),
            'nation': getattr(player, 'nation', self.display_nation),
            'commander_id': purchase_plan.get('commander_id'),
            'unit_type': purchase_plan.get('type'),
            'unit_size': purchase_plan.get('size'),
            'cost': purchase_plan.get('cost'),
            'supports': ';'.join(purchase_plan.get('supports', [])),
            'points_before': points_before,
            'points_after': points_after,
            'budget_allocated': ctx.get('budget_allocated'),
            'reserve': ctx.get('reserve'),
            'need_supply': budget_diag.get('need_supply'),
            'need_art': budget_diag.get('need_art'),
            'pressure': budget_diag.get('pressure'),
            'enemy_has_armor': budget_diag.get('enemy_has_armor'),
            'ratio': budget_diag.get('ratio'),
            'global_counts': json.dumps(state.get('global', {}).get('unit_counts_by_type', {}), ensure_ascii=False),
            'enemy_counts': json.dumps(state.get('enemy', {}).get('unit_counts_by_type', {}), ensure_ascii=False)
        }
        fieldnames = list(row.keys())
        with open(path, 'a', newline='', encoding='utf-8') as f:
            writer = csv.DictWriter(f, fieldnames=fieldnames)
            if is_new:
                writer.writeheader()
            writer.writerow(row)
        print(f"📝 Zalogowano zakup AI -> {path.name}")

    # === LOGOWANIE UZUPEŁNIEŃ (paliwo / amunicja / combat) ===
    def log_supply_replenishment(self, unit, action_type, fuel_before, fuel_after,
                                 ammo_before, ammo_after, source, trigger_reason,
                                 cost_points=0, batch_id=None, notes=""):
        """Rejestruje pojedyncze zdarzenie uzupełnienia zasobów jednostki.

        Parametry:
          unit           – obiekt żetonu (musi mieć id, unitType lub unit_type, nation opcjonalnie)
          action_type    – str: REFUEL | REARM | REFIT | COMBINED (luźna konwencja)
          fuel_before/after, ammo_before/after – wartości liczbowe (None jeśli nie dotyczy)
          source         – np. AUTO_TURN | AI_ALLOCATION | BASE | MANUAL_PLAYER
          trigger_reason – np. LOW_FUEL | PERIODIC | ENTER_BASE | BATCH_ALLOC
          cost_points    – koszt w punktach ekonomicznych (jeśli był)
          batch_id       – wspólne ID serii uzupełnień (uuid4.hex) lub None
          notes          – dodatkowa adnotacja tekstowa
        """
        try:
            from pathlib import Path
            import datetime, csv
            logs_dir = Path('logs')
            logs_dir.mkdir(exist_ok=True)
            date_tag = datetime.datetime.now().strftime('%Y%m%d')
            path = logs_dir / f'supply_{date_tag}.csv'
            is_new = not path.exists()
            fuel_before = 0 if fuel_before is None else fuel_before
            fuel_after = fuel_before if fuel_after is None else fuel_after
            ammo_before = 0 if ammo_before is None else ammo_before
            ammo_after = ammo_before if ammo_after is None else ammo_after
            delta_fuel = fuel_after - fuel_before
            delta_ammo = ammo_after - ammo_before
            row = {
                'timestamp': datetime.datetime.now().isoformat(timespec='seconds'),
                'turn': getattr(self, '_current_turn', ''),
                'nation': getattr(unit, 'nation', ''),
                'unit_id': getattr(unit, 'id', ''),
                'unit_type': getattr(unit, 'unitType', getattr(unit, 'unit_type', '')),
                'action_type': action_type,
                'fuel_before': fuel_before,
                'fuel_after': fuel_after,
                'ammo_before': ammo_before,
                'ammo_after': ammo_after,
                'delta_fuel': delta_fuel,
                'delta_ammo': delta_ammo,
                'source': source,
                'trigger_reason': trigger_reason,
                'cost_points': cost_points,
                'batch_id': batch_id or '',
                'notes': notes
            }
            fieldnames = list(row.keys())
            with open(path, 'a', newline='', encoding='utf-8') as f:
                w = csv.DictWriter(f, fieldnames=fieldnames)
                if is_new:
                    w.writeheader()
                w.writerow(row)
            # Zwięzły log konsolowy
            print(f"⛽ LOG SUPPLY: {action_type} unit={row['unit_id'][:10]} fuel {fuel_before}->{fuel_after} ammo {ammo_before}->{ammo_after} ({delta_fuel}/{delta_ammo})")
        except Exception as e:
            print(f"⚠️ log_supply_replenishment błąd: {e}")

    def log_supply_batch(self, units_events, source, trigger_reason, cost_points_total=0, notes=""):
        """Loguje serię uzupełnień (nadawane wspólne batch_id).

        units_events: iterable rekordów dict zawierających klucze:
            unit, action_type, fuel_before, fuel_after, ammo_before, ammo_after, cost_points (opcjonalnie), notes (opcjonalnie)
        """
        try:
            import uuid
            batch_id = uuid.uuid4().hex
            per_unit_cost_acc = 0
            for ev in units_events:
                cp = ev.get('cost_points', 0)
                per_unit_cost_acc += cp
                self.log_supply_replenishment(
                    ev['unit'],
                    ev.get('action_type', 'REFUEL'),
                    ev.get('fuel_before'), ev.get('fuel_after'),
                    ev.get('ammo_before'), ev.get('ammo_after'),
                    source, trigger_reason,
                    cost_points=cp,
                    batch_id=batch_id,
                    notes=ev.get('notes', notes)
                )
            if cost_points_total and cost_points_total != per_unit_cost_acc:
                print(f"ℹ️ Uwaga: cost_points_total({cost_points_total}) != suma indywidualna({per_unit_cost_acc})")
        except Exception as e:
            print(f"⚠️ log_supply_batch błąd: {e}")
        
    def plan_strategy(self):
        """Strategic planning"""
        # TODO: Implement strategic AI
        pass
        
    def manage_economy(self):
        """Economic decisions"""
        # TODO: Implement economic AI
        pass
