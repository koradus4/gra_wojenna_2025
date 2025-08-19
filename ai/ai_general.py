"""
AI General - Computer player controller
"""

class AIGeneral:
    def __init__(self, nationality, difficulty="medium"):
        self.nationality = nationality  # "german" or "polish"
        self.difficulty = difficulty
        self.is_ai = True
        
    def make_turn(self, game_engine):
        """
        Main AI decision making method - teraz z prawdziwą logiką!
        """
        print(f"\n🤖 === AI GENERAŁ {self.nationality.upper()} - ROZPOCZĘCIE TURY ===")
        
        # Znajdź swojego gracza
        current_player = game_engine.current_player_obj
        if not current_player:
            print("❌ Błąd: Nie znaleziono aktywnego gracza AI")
            return
            
        print(f"👤 Aktywny gracz: {current_player.nation} {current_player.role} (ID: {current_player.id})")
        
        # FAZA 1: Analiza ekonomii
        self.analyze_economy(current_player)
        
        # FAZA 2: Analiza jednostek
        self.analyze_units(game_engine, current_player)
        
        # FAZA 3: Decyzje strategiczne
        self.make_strategic_decisions(game_engine, current_player)
        
        print(f"✅ AI GENERAŁ {self.nationality.upper()} - KONIEC TURY\n")
        
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
        """Analizuje stan jednostek"""
        print("\n🪖 === ANALIZA JEDNOSTEK ===")
        
        # Pobierz widoczne jednostki dla generała
        my_units = game_engine.get_visible_tokens(player)
        
        if not my_units:
            print("❌ Brak jednostek do analizy")
            return
            
        print(f"📊 Liczba jednostek: {len(my_units)}")
        
        # Analiza stanu jednostek
        low_fuel_units = []
        low_combat_units = []
        healthy_units = []
        
        for unit in my_units:
            fuel_percent = (unit.currentFuel / max(unit.maxFuel, 1)) * 100
            combat_value = unit.combat_value
            
            print(f"  🎯 {unit.id[:20]}... - Paliwo: {unit.currentFuel}/{unit.maxFuel} ({fuel_percent:.0f}%), Combat: {combat_value}")
            
            if fuel_percent < 30:
                low_fuel_units.append(unit)
            if combat_value < 3:
                low_combat_units.append(unit)
            else:
                healthy_units.append(unit)
                
        # Podsumowanie
        print(f"✅ Jednostki w dobrej kondycji: {len(healthy_units)}")
        print(f"⛽ Jednostki z niskim paliwem: {len(low_fuel_units)}")
        print(f"💥 Jednostki z niskim combat value: {len(low_combat_units)}")
        
    def make_strategic_decisions(self, game_engine, player):
        """Podejmuje decyzje strategiczne"""
        print("\n🎯 === DECYZJE STRATEGICZNE ===")
        
        points_data = player.economy.get_points()
        economic_points = points_data.get('economic_points', 0)
        
        # Prosta logika decyzyjna
        if economic_points >= 30:
            print("💡 DECYZJA: Mam dużo punktów - rozważam zakup jednostek")
            self.consider_unit_purchase(game_engine, player, economic_points)
        elif economic_points >= 15:
            print("💡 DECYZJA: Średnia ilość punktów - może zakup wsparcia")
            print("🤔 Na razie czekam na lepszą okazję...")
        else:
            print("💡 DECYZJA: Mało punktów - oszczędzam")
            
    def consider_unit_purchase(self, game_engine, player, available_points):
        """Rozważa zakup jednostek - teraz z prawdziwymi zakupami!"""
        print(f"🛒 Rozważam zakupy za {available_points} punktów:")
        
        # Sprawdź czy to generał (może kupować jednostki)
        if player.role != "Generał":
            print("📋 Dowódca - brak uprawnień do zakupów")
            return
            
        # Znajdź dowódców tego gracza do przypisania jednostek
        try:
            # Dostęp do wszystkich graczy przez game_engine.players
            if hasattr(game_engine, 'players') and game_engine.players:
                all_players = [p for p in game_engine.players if hasattr(p, 'nation')]
                print(f"🔍 Znaleziono {len(all_players)} graczy w grze")
            else:
                print("❌ Brak dostępu do game_engine.players")
                return
                
            commanders = [p for p in all_players if p.nation == player.nation and p.role == "Dowódca"]
            
            if not commanders:
                print("👥 Brak dostępnych dowódców")
                return
                
            print(f"👥 Znaleziono {len(commanders)} dowódców: {[f'{c.id}({c.nation})' for c in commanders]}")
            
            # FAZA 1A: Zbieranie stanu (per dowódca + globalnie + wróg)
            state = self._gather_state(game_engine, player, commanders)
            # FAZA 1B: Decyzja o podziale budżetu (ile wydać teraz)
            purchase_budget, reserve, budget_diag = self._decide_budget(available_points, state)
            print(f"📊 Budżet przydzielony na zakupy: {purchase_budget} (rezerwa: {reserve})")
            # FAZA 2: Priorytety dowódców
            priorities = self._compute_commander_priorities(state, commanders)
            print("🧮 Priorytety dowódców:", priorities)
            # FAZA 3: Plan zakupów z wykorzystaniem priorytetów
            purchase_plans = self.plan_purchases(purchase_budget, commanders, priorities=priorities, state=state)
            # Zachowaj kontekst decyzji do logowania
            self._last_decision_context = {
                'state': state,
                'priorities': priorities,
                'budget_allocated': purchase_budget,
                'reserve': reserve,
                'budget_diag': budget_diag
            }
            
            # Wykonaj zakupy
            for plan in purchase_plans:
                success = self.purchase_unit_programmatically(player, plan)
                if success:
                    print(f"✅ Zakupiono: {plan['name']}")
                else:
                    print(f"❌ Nie udało się kupić: {plan['name']}")
                    break  # Przerwij jeśli brak środków
                    
        except Exception as e:
            print(f"❌ Błąd w zakupach AI: {e}")
            import traceback
            traceback.print_exc()

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
            all_tokens = []
            enemy_tokens = []
            if hasattr(game_engine, 'get_visible_tokens'):
                visible_all = game_engine.get_visible_tokens(general_player) or []
                # Podział na własne/obce
                for tok in visible_all:
                    tok_nation = getattr(tok, 'nation', None)
                    if tok_nation == general_player.nation:
                        all_tokens.append(tok)
                    else:
                        enemy_tokens.append(tok)
                # Per commander
                for c in commanders:
                    comm_tokens = [t for t in all_tokens if getattr(t, 'owner', None) == str(c.id)]
                    counts = {}
                    fuel_vals = []
                    for t in comm_tokens:
                        utype = getattr(t, 'unitType', None) or getattr(t, 'unit_type', None)
                        if not utype:
                            continue
                        counts[utype] = counts.get(utype, 0) + 1
                        max_fuel = getattr(t, 'maxFuel', 0) or 0
                        cur_fuel = getattr(t, 'currentFuel', 0) or 0
                        if max_fuel > 0:
                            fuel_vals.append(cur_fuel / max_fuel)
                    has_supply = counts.get('Z', 0) > 0
                    has_artillery = any(k in counts for k in ('AL','AC','AP'))
                    avg_fuel = sum(fuel_vals)/len(fuel_vals) if fuel_vals else 1.0
                    result['per_commander'][c.id] = {
                        'unit_counts_by_type': counts,
                        'total_units': sum(counts.values()),
                        'has_supply': has_supply,
                        'has_artillery': has_artillery,
                        'avg_fuel': avg_fuel
                    }
            # global own counts
            g_counts = {}
            for t in all_tokens:
                utype = getattr(t, 'unitType', None) or getattr(t, 'unit_type', None)
                if utype:
                    g_counts[utype] = g_counts.get(utype, 0) + 1
            result['global'] = {'unit_counts_by_type': g_counts,'total_units': sum(g_counts.values())}
            # enemy counts
            e_counts = {}
            for t in enemy_tokens:
                utype = getattr(t, 'unitType', None) or getattr(t, 'unit_type', None)
                if utype:
                    e_counts[utype] = e_counts.get(utype, 0) + 1
            has_enemy_art = any(k in e_counts for k in ('AL','AC','AP'))
            has_enemy_armor = any(k in e_counts for k in ('TC','TŚ','TL','TS'))
            result['enemy'] = {
                'unit_counts_by_type': e_counts,
                'total_units': sum(e_counts.values()),
                'has_artillery': has_enemy_art,
                'has_armor': has_enemy_armor
            }
            # Logi
            print("🛰️ STAN WŁASNY (global):", result['global'])
            print("🛰️ STAN WROGA (widoczny):", result.get('enemy'))
            for cid, data in result['per_commander'].items():
                print(f"   🧭 Dowódca {cid} -> {data}")
        except Exception as e:
            print(f"⚠️ _gather_state błąd: {e}")
        return result

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
            'nation': getattr(player, 'nation', self.nationality),
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
        
    def plan_strategy(self):
        """Strategic planning"""
        # TODO: Implement strategic AI
        pass
        
    def manage_economy(self):
        """Economic decisions"""
        # TODO: Implement economic AI
        pass
