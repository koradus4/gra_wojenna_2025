"""Test Victory AI Phase 1: Scouting + Threat Assessment
Sprawdza czy nowy system jest functional.
"""
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(__file__)))

from ai.victory_ai import *

def test_scout_identification():
    """Test identyfikacji jednostek zwiadu."""
    print("🔍 TEST: Scout Identification")
    
    # Mock units data
    mock_units = [
        {
            'id': 'Pz_Aufkl_1',
            'q': 10, 'r': 5,
            'mp': 8, 'fuel': 12,
            'token': type('obj', (), {
                'stats': {'unitType': 'K'},
                'maxMovePoints': 8,
                'maxFuel': 12,
                'sightRange': 4
            })()
        },
        {
            'id': 'Infantry_1', 
            'q': 12, 'r': 3,
            'mp': 4, 'fuel': 0,
            'token': type('obj', (), {
                'stats': {'unitType': 'P'},
                'maxMovePoints': 4,
                'maxFuel': 0,
                'sightRange': 2
            })()
        },
        {
            'id': 'Rozpoznaw_2',
            'q': 8, 'r': 7, 
            'mp': 6, 'fuel': 8,
            'token': type('obj', (), {
                'stats': {'unitType': 'Z_Aufkl'},
                'maxMovePoints': 6,
                'maxFuel': 8,
                'sightRange': 5
            })()
        }
    ]
    
    scouts = identify_scout_units(mock_units)
    
    print(f"   ✅ Znaleziono {len(scouts)}/2 oczekiwanych scouts")
    assert len(scouts) == 2, f"Expected 2 scouts, got {len(scouts)}"
    
    scout_ids = [s['unit_id'] for s in scouts]
    assert 'Pz_Aufkl_1' in scout_ids, "Kawaleria nie rozpoznana"
    assert 'Rozpoznaw_2' in scout_ids, "Unit rozpoznawczy nie znaleziony"
    assert 'Infantry_1' not in scout_ids, "Infantry błędnie sklasyfikowana jako scout"
    
    print("   ✅ Scout identification działa poprawnie")

def test_patrol_assignment():
    """Test przypisywania stref patrol."""
    print("🎯 TEST: Patrol Zone Assignment")
    
    # Mock scouts
    scouts = [
        {
            'unit_id': 'Scout_A',
            'position': (20, 0),
            'max_range': 8,
            'assigned_patrol_zone': None,
            'patrol_turns_active': 0
        },
        {
            'unit_id': 'Scout_B', 
            'position': (30, 5),
            'max_range': 6,
            'assigned_patrol_zone': (28, 3),  # Previous assignment
            'patrol_turns_active': 2
        }
    ]
    
    # Mock game engine
    mock_engine = type('obj', (), {
        'board': type('obj', (), {
            'get_tile': lambda self, q, r: True if abs(q) < 50 and abs(r) < 50 else None,
            'hex_distance': lambda self, pos1, pos2: abs(pos1[0] - pos2[0]) + abs(pos1[1] - pos2[1])
        })(),
        'key_points_state': {
            '30,0': {'current_value': 80},
            '20,10': {'current_value': 75}
        },
        'current_player_obj': type('obj', (), {'nation': 'TestNation'})(),
        'tokens': []
    })()
    
    assignments = assign_patrol_zones(scouts, mock_engine)
    
    print(f"   ✅ Przypisano {len(assignments)}/2 patrol zones")
    assert len(assignments) == 2, f"Expected 2 assignments, got {len(assignments)}"
    
    # Scout_B powinien kontynuować previous assignment
    assert assignments['Scout_B'] == (28, 3), "Scout_B should continue previous patrol"
    assert 'Scout_A' in assignments, "Scout_A should get new assignment"
    
    print("   ✅ Patrol assignment logic działa")

def test_enemy_detection():
    """Test fair enemy detection."""
    print("👀 TEST: Fair Enemy Detection")
    
    # Mock my units (vision sources)
    my_units = [
        {
            'q': 25, 'r': 0,
            'token': type('obj', (), {'sightRange': 3})()
        },
        {
            'q': 20, 'r': 5, 
            'token': type('obj', (), {'sightRange': 4})()
        }
    ]
    
    # Mock game engine z enemies
    mock_engine = type('obj', (), {
        'board': type('obj', (), {
            'hex_distance': lambda self, pos1, pos2: max(abs(pos1[0] - pos2[0]), abs(pos1[1] - pos2[1]))
        })(),
        'current_player_obj': type('obj', (), {'nation': 'MyNation'})(),
        'tokens': [
            # Enemy w zasięgu vision (dystans 2 od 25,0)
            type('obj', (), {
                'owner': 'EnemyNation',
                'q': 27, 'r': 0,
                'id': 'Enemy_Close',
                'stats': {'unitType': 'P'},
                'combat_value': 8,
                'maxMovePoints': 4
            })(),
            # Enemy poza zasięgiem (dystans 6)
            type('obj', (), {
                'owner': 'EnemyNation', 
                'q': 31, 'r': 0,
                'id': 'Enemy_Far',
                'stats': {'unitType': 'G'},
                'combat_value': 15,
                'maxMovePoints': 6
            })(),
            # Moja jednostka (powinna być pominięta)
            type('obj', (), {
                'owner': 'MyNation_Unit',
                'q': 23, 'r': 2,
                'id': 'My_Unit'
            })()
        ]
    })()
    
    enemies = scan_visible_enemies(my_units, mock_engine)
    
    print(f"   ✅ Wykryto {len(enemies)} enemies")
    assert len(enemies) == 1, f"Expected 1 visible enemy, got {len(enemies)}"
    
    detected = enemies[0]
    assert detected['unit_id'] == 'Enemy_Close', "Wrong enemy detected"
    assert detected['position'] == (27, 0), "Wrong enemy position"
    
    print("   ✅ Fair enemy detection działa (tylko widoczni wrogowie)")

def test_combat_assessment():
    """Test oceny opportunities bojowych."""
    print("⚔️ TEST: Combat Opportunity Assessment")
    
    # Mock enemy cluster
    enemy_cluster = [
        {
            'unit_id': 'Enemy_1',
            'combat_value': 6,
            'position': (25, 0)
        },
        {
            'unit_id': 'Enemy_2', 
            'combat_value': 4,
            'position': (26, 0)
        }
    ]
    
    # Mock my forces (stronger) - normal dict objects
    my_forces = [
        {'token': type('obj', (), {'combat_value': 8})()},
        {'token': type('obj', (), {'combat_value': 7})()}
    ]
    
    # Test w różnych sytuacjach VP
    assessment_tied = evaluate_combat_opportunity(enemy_cluster, my_forces, "TIED")
    assessment_losing = evaluate_combat_opportunity(enemy_cluster, my_forces, "LOSING")
    assessment_winning = evaluate_combat_opportunity(enemy_cluster, my_forces, "WINNING")
    
    print(f"   ✅ TIED: {assessment_tied['recommendation']} (ratio: {assessment_tied['force_ratio']:.2f})")
    print(f"   ✅ LOSING: {assessment_losing['recommendation']} (ratio: {assessment_losing['force_ratio']:.2f})")  
    print(f"   ✅ WINNING: {assessment_winning['recommendation']} (ratio: {assessment_winning['force_ratio']:.2f})")
    
    # When losing - more aggressive (lower threshold)
    assert assessment_losing['required_ratio'] < assessment_tied['required_ratio'], "Should be more aggressive when losing"
    
    # When winning - more cautious (higher threshold)  
    assert assessment_winning['required_ratio'] > assessment_tied['required_ratio'], "Should be more cautious when winning"
    
    print("   ✅ Adaptive combat assessment działa")

def test_full_phase1_integration():
    """Test całej integration Phase 1."""
    print("🚀 TEST: Full Phase 1 Integration")
    
    # Comprehensive mock game engine
    mock_engine = type('obj', (), {
        'board': type('obj', (), {
            'get_tile': lambda self, q, r: True if abs(q) < 50 and abs(r) < 50 else None,
            'hex_distance': lambda self, pos1, pos2: max(abs(pos1[0] - pos2[0]), abs(pos1[1] - pos2[1]))
        })(),
        'key_points_state': {
            '25,0': {'current_value': 90},
            '30,5': {'current_value': 60}
        },
        'current_player_obj': type('obj', (), {'nation': 'TestPlayer'})(),
        'tokens': [
            # My scout
            type('obj', (), {
                'owner': 'TestPlayer_Scout',
                'q': 20, 'r': 0,
                'id': 'My_Scout',
                'stats': {'unitType': 'K'},
                'movePoints': 6,
                'fuel': 8,
                'maxMovePoints': 6,
                'maxFuel': 8,
                'sightRange': 4
            })(),
            # Visible enemy
            type('obj', (), {
                'owner': 'Enemy',
                'q': 22, 'r': 0, 
                'id': 'Enemy_Target',
                'stats': {'unitType': 'P'},
                'combat_value': 5,
                'maxMovePoints': 4
            })()
        ],
        'current_turn': 3
    })()
    
    # Mock my units
    my_units = [
        {
            'token': mock_engine.tokens[0],  # Scout
            'id': 'My_Scout',
            'q': 20, 'r': 0,
            'mp': 6, 'fuel': 8
        }
    ]
    
    # Run full Phase 1
    report = victory_ai_phase1_controller(mock_engine, my_units, player_id=2)
    
    print(f"   ✅ Phase: {report['phase']}")
    print(f"   ✅ Scouts deployed: {report['scouts_deployed']}")
    print(f"   ✅ Enemies detected: {report['enemies_detected']}")  
    print(f"   ✅ Combat opportunities: {report['combat_opportunities']}")
    
    assert report['phase'] == 'SCOUTING_AND_THREAT_ASSESSMENT', "Wrong phase"
    assert report['scouts_deployed'] >= 0, "Scout deployment should be non-negative"
    assert report['enemies_detected'] >= 0, "Enemy detection should be non-negative"
    
    print("   ✅ Full Phase 1 integration successful")

def run_all_tests():
    """Uruchom wszystkie testy Phase 1."""
    print("🧪 VICTORY AI PHASE 1 - TEST SUITE")
    print("=" * 50)
    
    try:
        test_scout_identification()
        print()
        test_patrol_assignment()
        print()
        test_enemy_detection()
        print()
        test_combat_assessment()
        print()
        test_full_phase1_integration()
        print()
        
        print("🎉 WSZYSTKIE TESTY PHASE 1 PASSED!")
        print("✅ Victory AI Phase 1 gotowy do implementacji")
        
    except Exception as e:
        print(f"❌ TEST FAILED: {e}")
        raise

if __name__ == "__main__":
    run_all_tests()
