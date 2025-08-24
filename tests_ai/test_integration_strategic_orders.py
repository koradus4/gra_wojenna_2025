"""
Test integracji systemu strategicznych rozkazów
"""
import sys
from pathlib import Path

# Dodaj ścieżkę do głównego projektu
sys.path.append(str(Path(__file__).parent.parent))

from ai.ai_general import AIGeneral
from ai.ai_commander import AICommander
from unittest.mock import Mock

def test_full_integration():
    """Test pełnego cyklu: General wydaje rozkazy → Commander je odczytuje"""
    
    print("=== TEST INTEGRACJI STRATEGICZNYCH ROZKAZÓW ===\n")
    
    # 1. Setup
    orders_file = Path("data/test_strategic_orders.json")
    current_turn = 5
    
    # 2. AI General wydaje rozkazy
    print("1. AI General wydaje rozkazy...")
    general = AIGeneral("germany")
    orders_issued = general.issue_strategic_orders(orders_file, current_turn=current_turn)
    
    if orders_issued:
        print(f"✅ General wydał rozkazy dla tury {current_turn}")
        print(f"   Strategia: {orders_issued.get('strategy_type', 'UNKNOWN')}")
        print(f"   Liczba rozkazów: {len(orders_issued.get('orders', {}))}")
    else:
        print("❌ General nie wydał rozkazów")
        return False
    
    # 3. AI Commander odbiera rozkazy
    print("\n2. AI Commander odbiera rozkazy...")
    mock_player = Mock()
    mock_player.nation = "germany"
    
    commander = AICommander(mock_player)
    received_order = commander.receive_orders(orders_file, current_turn=current_turn)
    
    if received_order:
        print(f"✅ Commander otrzymał rozkaz:")
        print(f"   Misja: {received_order.get('mission_type', 'UNKNOWN')}")
        print(f"   Cel: {received_order.get('target_hex', 'UNKNOWN')}")
        print(f"   Priorytet: {received_order.get('priority', 'UNKNOWN')}")
        print(f"   Wygasa w turze: {received_order.get('expires_turn', 'UNKNOWN')}")
    else:
        print("❌ Commander nie otrzymał rozkazu")
        return False
    
    # 4. Sprawdź czy rozkaz wygasa
    print("\n3. Test wygasania rozkazów...")
    expired_order = commander.receive_orders(orders_file, current_turn=current_turn + 10)
    
    if expired_order is None:
        print("✅ Rozkaz poprawnie wygasł po przekroczeniu expires_turn")
    else:
        print("❌ Rozkaz nie wygasł gdy powinien")
        return False
    
    # 5. Cleanup
    if orders_file.exists():
        orders_file.unlink()
        print("\n4. Cleanup: Usunięto testowy plik rozkazów")
    
    print("\n✅ WSZYSTKIE TESTY INTEGRACJI PRZESZŁY POMYŚLNIE!")
    return True

if __name__ == "__main__":
    success = test_full_integration()
    if not success:
        sys.exit(1)
