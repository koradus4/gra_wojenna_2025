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
            self.consider_unit_purchase(player, economic_points)
        elif economic_points >= 15:
            print("💡 DECYZJA: Średnia ilość punktów - może zakup wsparcia")
            print("🤔 Na razie czekam na lepszą okazję...")
        else:
            print("💡 DECYZJA: Mało punktów - oszczędzam")
            
    def consider_unit_purchase(self, player, available_points):
        """Rozważa zakup jednostek"""
        print(f"🛒 Rozważam zakupy za {available_points} punktów:")
        
        # Prosta logika - preferuj piechotę jako podstawę
        if available_points >= 20:
            print("  💭 Mógłbym kupić pluton piechoty (~15-20 pkt)")
            print("  💭 Albo wsparcie dla istniejących jednostek")
            # TODO: Tutaj będzie rzeczywisty zakup
            print("  ⏳ Na razie tylko analizuję - zakupy w następnej wersji")
        else:
            print("  💭 Za mało na nowe jednostki, czekam...")
        
    def plan_strategy(self):
        """Strategic planning"""
        # TODO: Implement strategic AI
        pass
        
    def manage_economy(self):
        """Economic decisions"""
        # TODO: Implement economic AI
        pass
