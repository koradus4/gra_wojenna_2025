#!/usr/bin/env python3
"""
Demo Systemu Logowania - Test i Demonstracja
(Logging System Demo - Test and Demonstration)

Skrypt demonstracyjny pokazujący działanie nowego systemu logowania
oraz integracji z uczeniem maszynowym.
"""

import sys
import os
from pathlib import Path

# Dodanie ścieżki do modułów
sys.path.append(str(Path(__file__).parent))

from utils.game_log_manager import get_game_log_manager, KategoriaLog, TagLog
from utils.ai_log_integrator import (
    log_commander_action, 
    log_economy_turn,
    log_strategy_decision,
    log_supply_replenishment
)
from utils.ml_data_exporter import MLDataExporter

def demo_podstawowe_logowanie():
    """Demonstracja podstawowego logowania"""
    print("🔵 === Demo: Podstawowe Logowanie ===")
    
    # Pobierz menedżer
    manager = get_game_log_manager()
    
    # Ustaw kontekst gry
    manager.ustaw_kontekst_gry(gracz="Germany", tura=1, gra_id="demo_game_001")
    
    # Logi AI
    manager.log_ai_dowodca(
        "Inicjalizacja pozycji startowych",
        szczegoly={"jednostki_przemieszczone": 12, "czas_wykonania": "2.3s"},
        ml_dane={"initial_strength": 0.8, "deployment_efficiency": 0.95}
    )
    
    manager.log_ai_general(
        "Analiza strategiczna - faza początkowa",
        szczegoly={"enemy_detected": True, "threat_level": "medium"},
        ml_dane={"threat_assessment": 0.6, "resource_availability": 0.9}
    )
    
    manager.log_ai_walka(
        "Pierwsza potyczka: piechota vs piechota",
        szczegoly={"attacker": "inf_ger_01", "defender": "inf_sov_03"},
        ml_dane={"combat_odds": 0.7, "terrain_modifier": 1.2}
    )
    
    # Logi człowieka (symulowane)
    manager.log_human_akcja(
        "Gracz wydał rozkaz przemieszczenia",
        szczegoly={"interface": "map_click", "units_selected": 3}
    )
    
    manager.log_human_decyzja(
        "Wybrana strategia defensywna",
        szczegoly={"strategy": "defensive", "confidence": 0.8}
    )
    
    # Logi systemu
    manager.log_game_mechanika(
        "Przeliczenie fazy ekonomicznej",
        szczegoly={"pe_generated": 45, "calculation_time": "0.1s"}
    )
    
    manager.log_game_error(
        "Ostrzeżenie: jednostka poza mapą",
        szczegoly={"unit_id": "art_ger_02", "position": (-1, 5)},
        poziom="WARNING"
    )
    
    print("✅ Podstawowe logowanie zakończone")

def demo_kompatybilnosc_wsteczna():
    """Demonstracja kompatybilności z istniejącymi funkcjami"""
    print("\n🔄 === Demo: Kompatybilność Wsteczna ===")
    
    # Te funkcje działają identycznie jak wcześniej
    log_commander_action(
        unit_id="tank_01",
        action_type="move",
        from_pos=(5, 3),
        to_pos=(6, 4),
        reason="Advance to strategic position",
        threat_level=3,
        mp_before=8,
        mp_after=6
    )
    
    log_economy_turn(
        turn=1,
        pe_start=100,
        pe_allocated=85,
        pe_spent_purchases=70,
        strategy_used="balanced",
        orders_issued=True,
        decision_metrics={"confidence": 0.85, "risk_level": 0.3}
    )
    
    log_strategy_decision(
        turn=1,
        decision="expand_front",
        rule_used="opportunity_rule_3",
        reasoning="Enemy weakness detected on eastern flank"
    )
    
    # Symulacja zaopatrzenia
    class MockUnit:
        def __init__(self, unit_id):
            self.id = unit_id
    
    mock_unit = MockUnit("tank_02")
    log_supply_replenishment(
        unit=mock_unit,
        action_type="fuel_resupply",
        fuel_before=20,
        fuel_after=80,
        supply_depot=(10, 8),
        cost_pe=3
    )
    
    print("✅ Kompatybilność wsteczna potwierdzona")

def demo_analiza_sesji():
    """Demonstracja analizy sesji"""
    print("\n📊 === Demo: Analiza Sesji ===")
    
    manager = get_game_log_manager()
    
    # Generuj raport
    raport = manager.generuj_raport_sesji()
    
    print(f"🆔 Session ID: {raport['session_id']}")
    print(f"⏱️  Czas sesji: {raport['czas_trwania_sesji']}")
    print(f"📈 Statystyki:")
    stats = raport['statystyki']
    print(f"   • Łącznie wpisów: {stats['wpisy_lacznie']}")
    print(f"   • Wpisy AI: {stats['wpisy_ai']}")  
    print(f"   • Wpisy Human: {stats['wpisy_human']}")
    print(f"   • Wpisy Game: {stats['wpisy_game']}")
    print(f"   • Błędy: {stats['bledy_lacznie']}")
    
    # Zapisz raport
    manager.zapisz_raport_sesji()
    print("✅ Raport sesji zapisany")

def demo_export_ml():
    """Demonstracja eksportu danych ML"""
    print("\n🤖 === Demo: Export Danych ML ===")
    
    exporter = MLDataExporter()
    
    # Generuj datasety
    print("🔄 Generowanie datasetów...")
    datasety = exporter.generuj_wszystkie_datasety()
    
    for nazwa, dataset in datasety.items():
        rozmiar = len(dataset.dane_trenujace)
        print(f"📊 {nazwa}: {rozmiar} wpisów, {len(dataset.cechy)} cech")
        
        if rozmiar > 0:
            print(f"   Cechy: {', '.join(dataset.cechy[:5])}{'...' if len(dataset.cechy) > 5 else ''}")
            print(f"   Opis: {dataset.opis}")
    
    # Eksportuj (tylko jeśli są dane)
    print("💾 Eksportowanie datasetów...")
    niepuste_datasety = {k: v for k, v in datasety.items() if not v.dane_trenujace.empty}
    
    if niepuste_datasety:
        wyniki = {}
        for nazwa, dataset in niepuste_datasety.items():
            pliki = exporter.exportuj_dataset(dataset, format="csv")
            wyniki[nazwa] = pliki
            print(f"✅ {nazwa}: {len(pliki)} plików")
    else:
        print("⚠️  Brak danych do eksportu (potrzeba więcej logów)")
    
    print("✅ Demo eksportu ML zakończone")

def demo_symulacja_rozgrywki():
    """Symulacja kilku tur gry dla wygenerowania danych"""
    print("\n🎮 === Demo: Symulacja Rozgrywki ===")
    
    manager = get_game_log_manager()
    
    # Symuluj 3 tury dla obu graczy
    for tura in range(1, 4):
        print(f"🔄 Tura {tura}")
        
        # Niemcy (AI)
        manager.ustaw_kontekst_gry("Germany", tura)
        
        # Ekonomia
        log_economy_turn(
            turn=tura,
            pe_start=90 + tura*10,
            pe_allocated=80 + tura*5,
            pe_spent_purchases=60 + tura*8,
            strategy_used=["aggressive", "balanced", "defensive"][tura-1],
            orders_issued=True
        )
        
        # Akcje dowódcy
        for i in range(3):
            log_commander_action(
                unit_id=f"unit_{tura}_{i}",
                action_type=["move", "attack", "defend"][i],
                from_pos=(tura*2, i*3),
                to_pos=(tura*2+1, i*3+1),
                reason=f"Tactical maneuver {i+1}",
                threat_level=tura*2,
                aggression_level=0.6 + tura*0.1,
                mp_before=8,
                mp_after=6-i
            )
        
        # Decyzje strategiczne
        log_strategy_decision(
            turn=tura,
            decision=f"strategy_shift_{tura}",
            rule_used=f"rule_set_{tura}",
            reasoning=f"Adaptation for turn {tura} conditions"
        )
        
        # ZSRR (Human - symulowany)
        manager.ustaw_kontekst_gry("Soviet_Union", tura)
        
        manager.log_human_decyzja(
            f"Kontratak na flanke {tura}",
            szczegoly={"flank": ["north", "center", "south"][tura-1]},
            ml_dane={"confidence": 0.7 + tura*0.05}
        )
        
        manager.log_human_akcja(
            f"Przemieszczenie rezerw - tura {tura}",
            szczegoly={"reserves": tura*2, "target_sector": f"sector_{tura}"}
        )
    
    print("✅ Symulacja rozgrywki zakończona")

def main():
    """Główna funkcja demonstracyjna"""
    print("🚀 === DEMO SYSTEMU LOGOWANIA GRY WOJENNEJ ===")
    print("System Logowania z integracją ML i kompatybilnością wsteczną\n")
    
    try:
        # 1. Podstawowe funkcje
        demo_podstawowe_logowanie()
        
        # 2. Kompatybilność
        demo_kompatybilnosc_wsteczna()
        
        # 3. Symulacja gry dla większej ilości danych
        demo_symulacja_rozgrywki()
        
        # 4. Analiza sesji
        demo_analiza_sesji()
        
        # 5. Export ML
        demo_export_ml()
        
        print("\n🎉 === DEMO ZAKOŃCZONE POMYŚLNIE ===")
        print("Sprawdź katalogi logs/ dla wygenerowanych plików")
        
        # Pokaż strukturę wygenerowanych plików
        logs_path = Path("logs")
        if logs_path.exists():
            print(f"\n📁 Struktura katalogów logs/:")
            for item in sorted(logs_path.rglob("*")):
                if item.is_file():
                    relative_path = item.relative_to(logs_path)
                    size_kb = item.stat().st_size / 1024
                    print(f"   {relative_path} ({size_kb:.1f} KB)")
    
    except Exception as e:
        print(f"❌ Błąd podczas demo: {e}")
        import traceback
        traceback.print_exc()
        return 1
    
    return 0

if __name__ == "__main__":
    exit_code = main()
    exit(exit_code)