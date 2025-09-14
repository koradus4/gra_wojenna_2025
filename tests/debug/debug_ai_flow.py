#!/usr/bin/env python3
"""
🧪 DEBUG AI COMMANDER FLOW
Sprawdza dokładnie gdzie AI Commander się zatrzymuje
"""

from engine.engine import GameEngine
from ai.ai_config import set_player_ai_profile, AIProfile
from engine.player import Player

def debug_ai_commander_flow():
    """Debuguje przepływ AI Commander"""
    
    print("🧪 DEBUG AI COMMANDER FLOW")
    print("="*60)
    
    # Setup game engine
    game_engine = GameEngine(
        map_path="data/map_data.json",
        tokens_index_path="assets/tokens/index.json", 
        tokens_start_path="assets/start_tokens.json",
        seed=42,
        read_only=False
    )
    
    # Ustawienia AI profile
    set_player_ai_profile(2, AIProfile.AGGRESSIVE)
    
    # Stwórz gracza
    player = Player(2, "Polska", "Dowódca", 300)
    player.is_ai_commander = True
    
    # Dodaj gracza do game_engine.players (to może być problem!)
    if not hasattr(game_engine, 'players'):
        game_engine.players = []
    game_engine.players.append(player)
    
    game_engine.current_player_obj = player
    
    print(f"🤖 AI Commander utworzony dla gracza {player.id} ({player.nation})")
    print(f"📋 game_engine.players: {len(getattr(game_engine, 'players', []))}")
    print(f"📋 current_player_obj: {getattr(game_engine, 'current_player_obj', 'BRAK')}")
    
    # Sprawdź początkowe pozycje polskich jednostek
    polish_units = [t for t in game_engine.tokens if '2 (Polska)' in str(t.owner)]
    print(f"\n📊 Jednostek polskich gracza 2: {len(polish_units)}")
    
    print(f"\n🎮 URUCHAMIANIE make_tactical_turn...")
    print("="*60)
    
    # Uruchom główną funkcję bezpośrednio
    try:
        from ai.ai_commander import make_tactical_turn
        make_tactical_turn(game_engine, 2)
        print("✅ make_tactical_turn zakończona pomyślnie!")
    except Exception as e:
        print(f"❌ Błąd podczas make_tactical_turn: {e}")
        import traceback
        traceback.print_exc()
        return False
    
    # Sprawdź pozycje po turze
    print(f"\n📊 ANALIZA PO TURZE:")
    print("="*30)
    
    polish_units_after = [t for t in game_engine.tokens if '2 (Polska)' in str(t.owner)]
    
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
    print(f"   AI fix status: {'SUCCESS' if moved_units > 0 else 'POTRZEBNE DALSZE DEBUGOWANIE'}")
    
    return moved_units > 0

if __name__ == "__main__":
    debug_ai_commander_flow()