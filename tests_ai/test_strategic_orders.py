"""
Testy systemu strategicznych rozkazów General → Commander
"""
import unittest
import json
import os
from pathlib import Path
import tempfile
from unittest.mock import Mock, patch

# Dodaj ścieżkę do głównego projektu
import sys
sys.path.append(str(Path(__file__).parent.parent))

from ai.ai_general import AIGeneral
from ai.ai_commander import AICommander


class TestStrategicOrders(unittest.TestCase):
    
    def setUp(self):
        """Setup przed każdym testem"""
        self.test_data_dir = Path(tempfile.mkdtemp())
        self.orders_file = self.test_data_dir / "strategic_orders.json"
        
    def tearDown(self):
        """Cleanup po każdym teście"""
        if self.orders_file.exists():
            self.orders_file.unlink()
        self.test_data_dir.rmdir()
    
    def test_general_creates_orders_file(self):
        """Test: General tworzy plik z rozkazami"""
        # Given: General z nationality
        general = AIGeneral("germany")
        
        # When: General wydaje rozkazy
        orders = general.issue_strategic_orders(self.orders_file, current_turn=12)
        
        # Then: Plik został utworzony
        self.assertTrue(self.orders_file.exists())
        self.assertIsNotNone(orders)
        self.assertEqual(orders["turn"], 12)
        self.assertIn("orders", orders)
        self.assertIn("germany", orders["orders"])
        
        # Sprawdź strukturę rozkazu
        germany_order = orders["orders"]["germany"]
        self.assertIn("mission_type", germany_order)
        self.assertIn("target_hex", germany_order)
        self.assertIn("expires_turn", germany_order)
    
    def test_commander_reads_orders_for_nation(self):
        """Test: Commander odczytuje rozkazy dla swojego narodu"""
        # Given: Plik z rozkazami
        orders_data = {
            "timestamp": "2025-08-24_22:30:15",
            "turn": 12,
            "orders": {
                "germany": {
                    "mission_type": "SECURE_KEYPOINT",
                    "target_hex": [47, 25],
                    "priority": "HIGH",
                    "expires_turn": 17,
                    "issued_turn": 12,
                    "status": "ACTIVE"
                }
            }
        }
        
        with open(self.orders_file, 'w') as f:
            json.dump(orders_data, f)
        
        # When: Commander sprawdza rozkazy
        mock_player = Mock()
        mock_player.nation = "germany"
        
        commander = AICommander(mock_player)
        orders = commander.receive_orders(self.orders_file, current_turn=13)
        
        # Then: Commander otrzymuje swój rozkaz
        self.assertIsNotNone(orders)
        self.assertEqual(orders["mission_type"], "SECURE_KEYPOINT")
        self.assertEqual(orders["target_hex"], [47, 25])
        self.assertEqual(orders["priority"], "HIGH")
        self.assertEqual(orders["status"], "ACTIVE")
    
    def test_commander_fallback_when_no_orders(self):
        """Test: Commander używa fallback gdy brak rozkazów"""
        # Given: Brak pliku z rozkazami
        mock_player = Mock()
        mock_player.nation = "germany"
        
        commander = AICommander(mock_player)
        
        # When: Commander sprawdza rozkazy (plik nie istnieje)
        orders = commander.receive_orders(self.orders_file, current_turn=13)
        
        # Then: Brak rozkazów - fallback
        self.assertIsNone(orders)
    
    def test_orders_expire_correctly(self):
        """Test: Rozkazy wygasają po określonym czasie"""
        # Given: Rozkaz z expires_turn = 15
        orders_data = {
            "timestamp": "2025-08-24_22:30:15", 
            "turn": 12,
            "orders": {
                "germany": {
                    "mission_type": "SECURE_KEYPOINT",
                    "target_hex": [47, 25],
                    "expires_turn": 15,
                    "issued_turn": 12,
                    "status": "ACTIVE"
                }
            }
        }
        
        with open(self.orders_file, 'w') as f:
            json.dump(orders_data, f)
        
        mock_player = Mock()
        mock_player.nation = "germany"
        
        commander = AICommander(mock_player)
        
        # When: Current turn > expires_turn
        orders = commander.receive_orders(self.orders_file, current_turn=16)
        
        # Then: Rozkaz wygasł
        self.assertIsNone(orders)


if __name__ == '__main__':
    unittest.main()
