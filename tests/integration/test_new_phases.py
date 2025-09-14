#!/usr/bin/env python3
"""
🧪 TEST NOWEJ KOLEJNOŚCI FAZ
Testuje czy AI teraz MOVEMENT→COMBAT zamiast COMBAT→MOVEMENT
"""

from engine.engine import GameEngine
from ai.ai_config import set_player_ai_profile, AIProfile
from ai.ai_commander import AICommander
from engine.player import Player

def test_new_phase_order():
    """Test nowej kolejności faz: MOVEMENT → COMBAT"""
    
    print("🧪 TEST NOWEJ KOLEJNOŚCI FAZ")
    print("="*60)
    
    # Setup game engine
    game_engine = GameEngine(
        map_path="data/map_data.json",
        tokens_index_path="assets/tokens/index.json", 
        tokens_start_path="assets/start_tokens.json",
        seed=42,
        read_only=False
    )
    
    # Ustawienia AI profile - aggressive dla polskich dowódców
    set_player_ai_profile(2, AIProfile.AGGRESSIVE)  # Polska dowódca 1
    set_player_ai_profile(3, AIProfile.AGGRESSIVE)  # Polska dowódca 2
    
    print("✅ Profile ustawione na AGGRESSIVE (próg ataku = 0.72)")
    
    # Stwórz AI commandera dla gracza 2
    player = Player(2, "Polska", "Dowódca", 300)
    player.is_ai_commander = True
    
    ai_commander = AICommander(player)
    game_engine.current_player_obj = player
    game_engine.current_player_commander = ai_commander
    
    print(f"🤖 AI Commander utworzony dla gracza {player.id} ({player.nation})")
    
    # Sprawdź początkowe pozycje polskich jednostek
    polish_units = [t for t in game_engine.tokens if '2 (Polska)' in str(t.owner)]
    print(f"\n📊 Jednostek polskich gracza 2: {len(polish_units)}")
    
    for i, unit in enumerate(polish_units[:3]):  # Pierwsze 3 jednostki
        print(f"   🎖️ {unit.id}")
        print(f"      📍 Start: q={unit.q}, r={unit.r}")
        print(f"      👁️ Wzrok: {unit.stats.get('sight', 0)}")
        print(f"      🎯 Zasięg: {unit.stats.get('attack', {}).get('range', 1)}")
    
    print(f"\n🎮 URUCHAMIANIE TURY AI COMMANDERA...")
    print("="*60)
    
    # Uruchom turę AI Commandera (z nową kolejnością faz)
    try:
        ai_commander.make_tactical_turn(game_engine)
        print("✅ Tura AI Commander zakończona pomyślnie!")
    except Exception as e:
        print(f"❌ Błąd podczas tury AI: {e}")
        import traceback
        traceback.print_exc()
        return False
    
    # Sprawdź pozycje po turze
    print(f"\n📊 ANALIZA PO TURZE:")
    print("="*30)
    
    polish_units_after = [t for t in game_engine.tokens if '2 (Polska)' in str(t.owner)]
    print(f"Jednostek po turze: {len(polish_units_after)}")
    
    moved_units = 0
    for unit in polish_units_after[:3]:
        # Znajdź odpowiednik przed turą  
        original = next((u for u in polish_units if u.id == unit.id), None)
        if original:
            if original.q != unit.q or original.r != unit.r:
                moved_units += 1
                print(f"   📍 {unit.id}: ({original.q},{original.r}) → ({unit.q},{unit.r}) ✅ RUCH")
            else:
                print(f"   📍 {unit.id}: ({unit.q},{unit.r}) ⏹️ BEZ RUCHU")
    
    print(f"\n🎯 WYNIKI:")
    print(f"   Jednostek, które się poruszyły: {moved_units}/{min(len(polish_units), 3)}")
    print(f"   Nowa kolejność faz: {'DZIAŁA' if moved_units > 0 else 'WYMAGA POPRAWY'}")
    
    return moved_units > 0

if __name__ == "__main__":
    success = test_new_phase_order()
    print(f"\n🎊 KOŃCOWY WYNIK: {'SUCCESS' if success else 'FAILED'}")