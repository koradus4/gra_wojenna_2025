#!/usr/bin/env python3
"""Auto-test 10-rundowej gry AI vs AI z opcjami czyszczenia"""

import sys
import os
import argparse
from pathlib import Path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from engine.engine import GameEngine, update_all_players_visibility, clear_temp_visibility
from engine.player import Player
from core.ekonomia import EconomySystem
from core.tura import TurnManager
from core.zwyciestwo import VictoryConditions
from ai.ai_general import AIGeneral
from ai.ai_commander import AICommander

def clean_old_data():
    """Czyści stare CSV, zakupione żetony i WSZYSTKIE LOGI"""
    print("🧹 CZYSZCZENIE STARYCH DANYCH...")
    print("="*50)
    
    # 1. Czyszczenie WSZYSTKICH LOGÓW
    print("📋 Czyszczenie katalogu logs/...")
    logs_dir = Path("logs")
    if logs_dir.exists():
        cleaned_files = 0
        cleaned_size = 0
        for root, dirs, files in os.walk(logs_dir):
            for file in files:
                file_path = Path(root) / file
                try:
                    file_size = file_path.stat().st_size
                    file_path.unlink()  # Usuń plik
                    cleaned_files += 1
                    cleaned_size += file_size
                except Exception as e:
                    print(f"⚠️ Nie można usunąć {file_path}: {e}")
        
        # Usuń puste katalogi
        for root, dirs, files in os.walk(logs_dir, topdown=False):
            for dir_name in dirs:
                dir_path = Path(root) / dir_name
                try:
                    if not any(dir_path.iterdir()):  # Jeśli katalog pusty
                        dir_path.rmdir()
                except:
                    pass
        
        print(f"✅ Usunięto {cleaned_files} plików logów ({cleaned_size/1024:.1f} KB)")
    else:
        print("📁 Katalog logs/ nie istnieje")
    
    print()
    
    # 2. Czyszczenie CSV (dodatkowe - gdyby były gdzie indziej)
    try:
        from czyszczenie.czyszczenie_csv import clean_csv_files
        print("📄 Czyszczenie CSV w innych lokalizacjach...")
        clean_csv_files()
        print("✅ CSV wyczyszczone!")
    except Exception as e:
        print(f"⚠️ Błąd czyszczenia CSV: {e}")
    
    print()
    
    # 3. NOWE: Kompleksowe czyszczenie żetonów używając nowego systemu
    try:
        from czyszczenie.game_cleaner import clean_purchased_tokens, clean_purchased_tokens_from_index, clean_purchased_tokens_from_start
        print("🪙 Kompleksowe czyszczenie zakupionych żetonów...")
        clean_purchased_tokens()  # Foldery nowe_dla_* i pliki w aktualne/
        clean_purchased_tokens_from_index()  # Wpisy w index.json
        clean_purchased_tokens_from_start()  # Pozycje w start_tokens.json
        print("✅ Żetony kompletnie wyczyszczone ze wszystkich lokalizacji!")
    except Exception as e:
        print(f"⚠️ Błąd czyszczenia żetonów: {e}")
        # Fallback do starego systemu
        try:
            from czyszczenie.czyszczenie_zakupionych_zetonow import TokenFolderCleaner
            print("🔄 Próba fallback do starego systemu...")
            cleaner = TokenFolderCleaner()
            cleaner.clean_folders(force=True)
            print("✅ Żetony wyczyszczone (stary system)")
        except Exception as e2:
            print(f"❌ Całkowity błąd czyszczenia żetonów: {e2}")
    
    print("="*50)
    print("✅ DANE WYCZYSZCZONE - GOTOWE DO NOWEJ ANALIZY!")
    print("="*50)
    print()

def auto_game_10_turns(max_turns: int = 10):
    """Automatyczna gra N tur (domyślnie 10), wszyscy gracze to AI"""
    print(f"🚀 ROZPOCZYNANIE {max_turns}-RUNDOWEJ GRY AI vs AI")
    print("="*60)
    
    # GameEngine
    print("🔧 Tworzenie GameEngine...")
    game_engine = GameEngine(
        map_path="data/map_data.json",
        tokens_index_path="assets/tokens/index.json", 
        tokens_start_path="assets/start_tokens.json",
        seed=42,
        read_only=True
    )
    print(f"✅ GameEngine: {len(game_engine.tokens)} tokenów")
    
    # Gracze - wszyscy AI
    print("🤖 Konfiguracja graczy AI...")
    players = [
        Player(1, "Polska", "Generał", 5),
        Player(2, "Polska", "Dowódca", 5), 
        Player(3, "Polska", "Dowódca", 5),
        Player(4, "Niemcy", "Generał", 5),
        Player(5, "Niemcy", "Dowódca", 5),
        Player(6, "Niemcy", "Dowódca", 5),
    ]
    
    # AI Setup
    ai_generals = {}
    ai_commanders = {}
    
    for player in players:
        player.economy = EconomySystem()
        
        if player.role == "Generał":
            player.is_ai = True
            if player.nation == "Polska":
                ai_generals[player.id] = AIGeneral("polish")
            else:
                ai_generals[player.id] = AIGeneral("german")
            print(f"🧠 AI Generał: {player.nation} (id={player.id})")
            
        elif player.role == "Dowódca":
            player.is_ai_commander = True
            ai_commanders[player.id] = AICommander(player)
            print(f"🎯 AI Dowódca: {player.nation} (id={player.id})")
    
    game_engine.players = players
    update_all_players_visibility(players, game_engine.tokens, game_engine.board)
    
    # Turn Manager
    turn_manager = TurnManager(players, game_engine=game_engine)
    turn_manager.ai_generals = ai_generals
    turn_manager.ai_commanders = ai_commanders
    
    # Victory Conditions - liczba tur konfigurowalna
    victory_conditions = VictoryConditions(max_turns=max_turns, victory_mode="turns")
    
    print(f"🎯 POCZĄTEK GRY - {max_turns} TUR TEST")
    print("="*60)
    
    # === PE TRACKING - STAN POCZĄTKOWY ===
    print("💰 [PE INITIAL] POCZĄTKOWY STAN PE:")
    for nation in ["Polska", "Niemcy"]:
        nation_players = [p for p in players if p.nation == nation]
        total_pe = sum(p.economy.get_points().get('economic_points', 0) for p in nation_players)
        print(f"  🏛️ {nation} łącznie: {total_pe} PE")
        for p in nation_players:
            pe = p.economy.get_points().get('economic_points', 0)
            print(f"    └─ {p.role} (id={p.id}): {pe} PE")
    print("="*40)
    
    # Główna pętla gry
    turn_count = 0
    while turn_count < max_turns:
        current_player = turn_manager.get_current_player()
        game_engine.current_player_obj = current_player
        
        print(f"\n📅 TURA {turn_manager.current_turn} - {current_player.nation} {current_player.role} (id={current_player.id})")
        
        # Logowanie stanu key pointów
        game_engine.log_key_points_status(current_player)
        
        update_all_players_visibility(players, game_engine.tokens, game_engine.board)
        
        # AI Turn
        if hasattr(current_player, 'is_ai') and current_player.is_ai and current_player.id in ai_generals:
            print(f"🧠 AI GENERAL TURN: {current_player.nation}")
            
            # === PE TRACKING - PRZED TURĄ GENERAŁA ===
            pe_before_general = current_player.economy.get_points().get('economic_points', 0)
            commanders = [p for p in players if p.nation == current_player.nation and p.role == 'Dowódca']
            cmd_pe_before = {}
            for cmd in commanders:
                cmd_pe_before[cmd.id] = cmd.economy.get_points().get('economic_points', 0)
            
            print(f"💰 [PE BEFORE] Generał {current_player.nation} (id={current_player.id}): {pe_before_general} PE")
            for cmd in commanders:
                print(f"💰 [PE BEFORE] Dowódca {cmd.nation} (id={cmd.id}): {cmd_pe_before[cmd.id]} PE")
            
            ai_general = ai_generals[current_player.id]
            if current_player.role == "Generał":
                current_player.economy.generate_economic_points()
                current_player.economy.add_special_points()
            ai_general.make_turn(game_engine)
            
            # === PE TRACKING - PO TURZE GENERAŁA ===
            pe_after_general = current_player.economy.get_points().get('economic_points', 0)
            cmd_pe_after = {}
            for cmd in commanders:
                cmd_pe_after[cmd.id] = cmd.economy.get_points().get('economic_points', 0)
            
            print(f"💰 [PE AFTER] Generał {current_player.nation} (id={current_player.id}): {pe_after_general} PE")
            for cmd in commanders:
                gained = cmd_pe_after[cmd.id] - cmd_pe_before[cmd.id]
                print(f"💰 [PE AFTER] Dowódca {cmd.nation} (id={cmd.id}): {cmd_pe_after[cmd.id]} PE (zmiana: {gained:+d})")
            
            allocated_total = pe_before_general - pe_after_general
            commanders_gained_total = sum(cmd_pe_after[cmd.id] - cmd_pe_before[cmd.id] for cmd in commanders)
            balance = allocated_total - commanders_gained_total
            
            print(f"📊 [PE FLOW] Generał przekazał: {allocated_total} PE")
            print(f"📊 [PE FLOW] Dowódcy otrzymali łącznie: {commanders_gained_total} PE")
            print(f"📊 [PE FLOW] Bilans (różnica): {balance} PE {'✅ OK' if abs(balance) <= 1 else '❌ BŁĄD'}")
            
        elif hasattr(current_player, 'is_ai_commander') and current_player.is_ai_commander and current_player.id in ai_commanders:
            print(f"🎯 AI COMMANDER TURN: {current_player.nation} id={current_player.id}")
            
            # === PE TRACKING - PRZED TURĄ DOWÓDCY ===
            pe_before_commander = current_player.economy.get_points().get('economic_points', 0)
            print(f"💰 [PE BEFORE] Dowódca {current_player.nation} (id={current_player.id}): {pe_before_commander} PE")
            
            # === VICTORY AI ANALYSIS - STAN PRZED TURĄ ===
            print(f"🎯 [VICTORY AI] ANALIZA STANU PRZED TURĄ - {current_player.nation} id={current_player.id}")
            
            # Zlicz moje jednostki
            my_tokens = [t for t in game_engine.tokens if current_player.nation in getattr(t, 'owner', '')]
            total_units = len(my_tokens)
            scout_units = []
            combat_units = []
            supply_units = []
            
            for token in my_tokens:
                unit_type = getattr(token, 'stats', {}).get('unitType', 'UNKNOWN') if hasattr(token, 'stats') else 'UNKNOWN'
                unit_id = getattr(token, 'id', 'UNKNOWN')
                mp = getattr(token, 'movePoints', 0)
                fuel = getattr(token, 'fuel', 0)
                
                if unit_type == 'K' or 'Aufkl' in unit_id or 'Rozpoznaw' in unit_id:
                    scout_units.append({'id': unit_id, 'type': unit_type, 'mp': mp, 'fuel': fuel, 'pos': (token.q, token.r)})
                elif unit_type == 'Z':
                    supply_units.append({'id': unit_id, 'mp': mp, 'fuel': fuel, 'pos': (token.q, token.r)})
                elif mp > 0 and fuel > 0:
                    combat_units.append({'id': unit_id, 'type': unit_type, 'mp': mp, 'fuel': fuel, 'pos': (token.q, token.r)})
            
            print(f"📊 [VICTORY AI] SIŁY PRZED TURĄ: {total_units} jednostek łącznie")
            print(f"🔍 [VICTORY AI] SCOUTS: {len(scout_units)} jednostek zwiadu")
            for scout in scout_units[:3]:  # Max 3 dla czytelności
                print(f"  └─ {scout['id']} ({scout['type']}) na {scout['pos']}, MP:{scout['mp']}, Fuel:{scout['fuel']}")
            
            print(f"⚔️ [VICTORY AI] COMBAT: {len(combat_units)} jednostek bojowych z ruchem")
            print(f"🚛 [VICTORY AI] SUPPLY: {len(supply_units)} jednostek zaopatrzenia")
            
            # Sprawdź wrogów w visibility
            enemy_tokens = []
            for token in game_engine.tokens:
                owner = getattr(token, 'owner', '')
                if owner and current_player.nation not in owner:
                    # Sprawdź czy widoczny dla tego gracza
                    is_visible = False
                    if hasattr(token, 'visible_to_players') and isinstance(token.visible_to_players, list):
                        is_visible = current_player.id in token.visible_to_players
                    elif hasattr(token, 'visible_to_players') and isinstance(token.visible_to_players, set):
                        is_visible = current_player.id in token.visible_to_players
                    
                    if is_visible:
                        enemy_tokens.append({
                            'id': getattr(token, 'id', 'UNKNOWN'),
                            'owner': owner,
                            'pos': (token.q, token.r),
                            'type': getattr(token, 'stats', {}).get('unitType', 'UNKNOWN') if hasattr(token, 'stats') else 'UNKNOWN'
                        })
            
            print(f"👁️ [VICTORY AI] WROGOWIE W ZASIĘGU WZROKU: {len(enemy_tokens)} jednostek")
            for enemy in enemy_tokens[:5]:  # Max 5 dla czytelności
                print(f"  └─ {enemy['id']} ({enemy['owner']}, {enemy['type']}) na {enemy['pos']}")
            
            ai_commander = ai_commanders[current_player.id]
            
            # Pre-resupply i tura taktyczna
            ai_commander.pre_resupply(game_engine)
            ai_commander.make_tactical_turn(game_engine)
            
            # === VICTORY AI ANALYSIS - REZULTATY ===
            print(f"🎯 [VICTORY AI] ANALIZA REZULTATÓW TURY - {current_player.nation} id={current_player.id}")
            
            # Sprawdź czy jednostki się ruszyły
            my_tokens_after = [t for t in game_engine.tokens if current_player.nation in getattr(t, 'owner', '')]
            moved_units = []
            units_on_kp = []
            
            for token in my_tokens_after:
                unit_id = getattr(token, 'id', 'UNKNOWN')
                current_pos = (token.q, token.r)
                mp_left = getattr(token, 'movePoints', 0)
                
                # Sprawdź czy na key point
                hex_id = f"{token.q},{token.r}"
                if hex_id in game_engine.key_points_state:
                    kp_value = game_engine.key_points_state[hex_id].get('current_value', 0)
                    units_on_kp.append({'id': unit_id, 'pos': current_pos, 'kp_value': kp_value})
                
                # Sprawdź czy się ruszył (MP < max)
                max_mp = getattr(token, 'maxMovePoints', 0)
                if mp_left < max_mp:
                    moved_units.append({'id': unit_id, 'from_mp': max_mp, 'to_mp': mp_left, 'pos': current_pos})
            
            print(f"🚶 [VICTORY AI] RUCHY WYKONANE: {len(moved_units)} jednostek się ruszyło")
            for move in moved_units[:5]:  # Max 5
                mp_used = move['from_mp'] - move['to_mp']
                print(f"  └─ {move['id']} użył {mp_used} MP, zostało {move['to_mp']}/{move['from_mp']} na {move['pos']}")
            
            print(f"🎯 [VICTORY AI] POZYCJE NA KEY POINTS: {len(units_on_kp)} jednostek")
            for unit_kp in units_on_kp:
                print(f"  └─ {unit_kp['id']} na KP {unit_kp['pos']} wartość: {unit_kp['kp_value']}")
            
            # === PE TRACKING - PO TURZE DOWÓDCY ===
            pe_after_commander = current_player.economy.get_points().get('economic_points', 0)
            spent = pe_before_commander - pe_after_commander
            print(f"💰 [PE AFTER] Dowódca {current_player.nation} (id={current_player.id}): {pe_after_commander} PE (wydał: {spent} PE)")
            
            if spent > 0:
                print(f"🛒 [PE SPENDING] Dowódca {current_player.id} wydał {spent} PE na resupply/operacje")
            
            print("─" * 60)
            
            if spent > 0:
                print(f"🛒 [PE SPENDING] Dowódca {current_player.id} wydał {spent} PE na resupply/operacje")
        
        # Następna tura
        is_full_turn_end = turn_manager.next_turn()
        
        if is_full_turn_end:
            print(f"\n🏁 === KONIEC PEŁNEJ TURY === PE COLLECTION PHASE ===")
            print("🔍 SPRAWDZANIE: Które jednostki mogą zbierać PE z key points")
            
            # Sprawdź wszystkie jednostki Z na key points
            supply_units_on_kp = []
            for token in game_engine.tokens:
                if hasattr(token, 'stats') and token.stats.get('unitType') == 'Z':
                    # Sprawdź czy jest na key point
                    hex_pos = f"{token.q},{token.r}"
                    if hex_pos in game_engine.key_points_state:
                        kp = game_engine.key_points_state[hex_pos]
                        supply_units_on_kp.append({
                            'unit_id': token.id,
                            'owner': getattr(token, 'owner', 'UNKNOWN'),
                            'hex': hex_pos,
                            'kp_value': kp.get('current_value', 0),
                            'kp_initial': kp.get('initial_value', 0)
                        })
            
            print(f"⭐ JEDNOSTKI ZAOPATRZENIA (Z) NA KEY POINTS: {len(supply_units_on_kp)}")
            for unit in supply_units_on_kp:
                percent = (unit['kp_value'] / max(unit['kp_initial'], 1)) * 100
                print(f"  💰 {unit['unit_id']} ({unit['owner']}) na {unit['hex']}: KP {unit['kp_value']}/{unit['kp_initial']} ({percent:.1f}%)")
            
            game_engine.process_key_points(players)
            turn_count += 1
            print(f"🔄 KONIEC RUNDY {turn_count}/{max_turns}")
            
            # === PE TRACKING - KONIEC RUNDY ===
            print("💰 [PE SUMMARY] STAN PE NA KONIEC RUNDY:")
            for nation in ["Polska", "Niemcy"]:
                nation_players = [p for p in players if p.nation == nation]
                total_pe = sum(p.economy.get_points().get('economic_points', 0) for p in nation_players)
                print(f"  🏛️ {nation} łącznie: {total_pe} PE")
                for p in nation_players:
                    pe = p.economy.get_points().get('economic_points', 0)
                    print(f"    └─ {p.role} (id={p.id}): {pe} PE")
            print("="*40)
        
        game_engine.update_all_players_visibility(players)
        
        # Sprawdź warunki zwycięstwa
        if victory_conditions.check_game_over(turn_manager.current_turn, players):
            print(victory_conditions.get_victory_message())
            break
            
        clear_temp_visibility(players)
    
    print("\n" + "="*60)
    print("🏁 GRA ZAKOŃCZONA")
    
    # Analiza wyników
    victory_info = victory_conditions.get_victory_info()
    print(f"🏆 ZWYCIĘZCA: {victory_info.get('winner_nation', 'REMIS')}")
    
    for p in players:
        vp = getattr(p, "victory_points", 0)
        print(f"📊 {p.nation} {p.role} (id={p.id}): {vp} VP")
    
    print("\n📄 ANALIZA WYGENEROWANYCH LOGÓW:")
    print("="*60)
    
    # Sprawdzenie wszystkich logów
    csv_files = []
    log_files = []
    
    if os.path.exists("logs"):
        for root, dirs, files in os.walk("logs"):
            for file in files:
                file_path = os.path.join(root, file)
                try:
                    file_size = os.path.getsize(file_path)
                    if file.endswith('.csv'):
                        with open(file_path, 'r', encoding='utf-8') as f:
                            lines = len(f.readlines())
                        csv_files.append((file_path, lines, file_size))
                    else:
                        log_files.append((file_path, file_size))
                except Exception as e:
                    print(f"⚠️ Błąd odczytu {file_path}: {e}")
    
    # CSV FILES
    if csv_files:
        csv_files.sort(key=lambda x: x[1], reverse=True)  # Sortuj po liczbie linii
        print(f"� PLIKI CSV ({len(csv_files)}):")
        for file_path, line_count, size_bytes in csv_files:
            size_kb = size_bytes / 1024
            rel_path = os.path.relpath(file_path, "logs")
            status = "🔥 WAŻNY" if line_count > 50 else "📄 Mały"
            print(f"  {status} {rel_path}: {line_count} linii, {size_kb:.1f} KB")
            
            # Pokaż próbkę dla ważnych plików
            if line_count > 50:
                try:
                    with open(file_path, 'r', encoding='utf-8') as f:
                        sample_lines = f.readlines()[:3]  # Pierwsze 3 linie
                    print(f"    └─ Próbka: {sample_lines[0].strip()[:60]}..." if sample_lines else "")
                except:
                    pass
    else:
        print("📊 PLIKI CSV: Brak")
    
    print()
    
    # LOG FILES  
    if log_files:
        log_files.sort(key=lambda x: x[1], reverse=True)  # Sortuj po rozmiarze
        print(f"📋 INNE LOGI ({len(log_files)}):")
        for file_path, size_bytes in log_files:
            size_kb = size_bytes / 1024
            rel_path = os.path.relpath(file_path, "logs")
            status = "🔥 DUŻY" if size_kb > 10 else "📄 Mały"
            print(f"  {status} {rel_path}: {size_kb:.1f} KB")
    else:
        print("📋 INNE LOGI: Brak")
    
    # PODSUMOWANIE KLUCZOWE
    print()
    print("🎯 KLUCZOWE ANALIZY:")
    garrison_csv = next((f for f in csv_files if 'garrison' in f[0].lower()), None)
    if garrison_csv:
        print(f"  🏰 GARRISON SUPPORT: {garrison_csv[0]} ({garrison_csv[1]} problemów)")
    else:
        print("  🏰 GARRISON SUPPORT: Brak logów ❌")
    
    # Szukaj logów ekonomicznych zarówno w starych jak i nowych nazwach (economy/economic/decyzje_ekonomiczne)
    pe_csv = next((
        f for f in csv_files 
        if (
            'pe_' in f[0].lower() 
            or 'economic' in f[0].lower() 
            or 'economy' in f[0].lower() 
            or 'decyzje_ekonomiczne' in f[0].lower()
        )
    ), None)
    if pe_csv:
        print(f"  💰 PE COLLECTION: {pe_csv[0]} ({pe_csv[1]} operacji)")
    else:
        print("  💰 PE COLLECTION: Brak logów ❌")
    
    # VICTORY AI ANALYSIS
    # Rozszerzone wykrywanie logów Victory AI: stary plik 'victory_ai' lub nowy polski 'analiza_zwyciestwa'
    victory_csv = next((f for f in csv_files if 'victory_ai' in f[0].lower()), None)
    advanced_victory_csv = next((f for f in csv_files if 'analiza_zwyciestwa' in f[0].lower()), None)
    strategic_csv = next((f for f in csv_files if 'decyzje_strategiczne' in f[0].lower()), None)
    if victory_csv or advanced_victory_csv or strategic_csv:
        if victory_csv:
            print(f"  🎯 VICTORY AI PHASE 1: {victory_csv[0]} ({victory_csv[1]} akcji)")
            # Sprawdź próbkę Victory AI logs (stary format)
            try:
                with open(victory_csv[0], 'r', encoding='utf-8') as f:
                    lines = f.readlines()
                action_counts = {}
                for line in lines[1:]:  # Skip header
                    parts = line.strip().split(',')
                    if len(parts) >= 4:
                        action = parts[3]
                        action_counts[action] = action_counts.get(action, 0) + 1
                print(f"    └─ ANALIZA AKCJI:")
                for action, count in sorted(action_counts.items()):
                    print(f"       • {action}: {count}x")
            except Exception as e:
                print(f"    ⚠️ Błąd analizy Victory AI CSV: {e}")

        if advanced_victory_csv:
            # Nowe polskie logi analizy zwycięstwa
            print(f"  🎯 VICTORY AI ANALIZA (PL): {advanced_victory_csv[0]} ({advanced_victory_csv[1]} wpisów)")
            # Opcjonalnie: pokaż średnią przewidywaną szansę zwycięstwa
            try:
                import csv as _csv
                with open(advanced_victory_csv[0], 'r', encoding='utf-8') as f:
                    reader = _csv.DictReader(f)
                    # Wsparcie zarówno dla angielskich jak i polskich nagłówków
                    rows = list(reader)
                    def _float_or_none(v):
                        try:
                            return float(str(v).replace(',', '.'))
                        except Exception:
                            return None
                    probs = []
                    for row in rows:
                        val = row.get('victory_probability')
                        if val is None:
                            val = row.get('prawdopodobienstwo_zwyciestwa')
                        x = _float_or_none(val)
                        if x is not None:
                            probs.append(x)
                if probs:
                    avg_prob = sum(probs) / len(probs)
                    print(f"    └─ Średnia victory_probability: {avg_prob:.2f}")
            except Exception:
                pass

        if strategic_csv:
            # Wyciągnij informacje dot. scoutów z decyzji strategicznych (SCOUT_*)
            try:
                import csv as _csv
                with open(strategic_csv[0], 'r', encoding='utf-8') as f:
                    reader = _csv.DictReader(f)
                    scout_count = 0
                    for row in reader:
                        dt = (row.get('decision_type') or '').upper()
                        if dt.startswith('SCOUT_'):
                            scout_count += 1
                if scout_count > 0:
                    print(f"  🧭 SCOUTING (z decyzji strategicznych): {scout_count} akcji")
            except Exception:
                pass
    else:
        print("  🎯 VICTORY AI PHASE 1: Brak logów ❌")

    # DODATKOWE: WYDAJNOŚĆ AI i ANALIZA WYWIADU (nowe polskie kategorie)
    perf_csv = next((f for f in csv_files if 'wydajnosc_ai' in f[0].lower()), None)
    intel_csv = next((f for f in csv_files if 'analiza_wywiadu' in f[0].lower()), None)

    if perf_csv:
        print(f"  ⚡ WYDAJNOŚĆ AI: {perf_csv[0]} ({perf_csv[1]} wpisów)")
        # Pokaż proste metryki: średnie opóźnienie decyzji i użycie CPU jeśli są
        try:
            import csv as _csv
            with open(perf_csv[0], 'r', encoding='utf-8') as f:
                reader = _csv.DictReader(f)
                latencies = []
                cpu_usages = []
                def _float_or_none(v):
                    try:
                        return float(str(v).replace(',', '.'))
                    except Exception:
                        return None
                for row in reader:
                    # Polskie nazwy: 'opoznienie_decyzji_ms', 'wykorzystanie_cpu_proc'
                    lat = row.get('opoznienie_decyzji_ms') or row.get('decision_latency_ms')
                    cpu = row.get('wykorzystanie_cpu_proc') or row.get('cpu_utilization_pct')
                    fl = _float_or_none(lat)
                    fc = _float_or_none(cpu)
                    if fl is not None:
                        latencies.append(fl)
                    if fc is not None:
                        cpu_usages.append(fc)
            if latencies:
                print(f"    └─ Średnie opóźnienie decyzji: {sum(latencies)/len(latencies):.1f} ms")
            if cpu_usages:
                print(f"    └─ Średnie użycie CPU: {sum(cpu_usages)/len(cpu_usages):.1f}%")
        except Exception:
            pass
    else:
        print("  ⚡ WYDAJNOŚĆ AI: Brak logów ❌")

    if intel_csv:
        print(f"  🕵️ ANALIZA WYWIADU: {intel_csv[0]} ({intel_csv[1]} wpisów)")
        # Pokaż najczęstsze typy informacji wywiadowczych
        try:
            import csv as _csv
            with open(intel_csv[0], 'r', encoding='utf-8') as f:
                reader = _csv.DictReader(f)
                counts = {}
                for row in reader:
                    typ = row.get('typ_informacji') or row.get('intelligence_type')
                    if not typ:
                        continue
                    counts[typ] = counts.get(typ, 0) + 1
            if counts:
                by_freq = sorted(counts.items(), key=lambda x: x[1], reverse=True)
                top_show = by_freq[:3]
                pretty = ', '.join([f"{k}: {v}" for k, v in top_show])
                print(f"    └─ Najczęstsze typy: {pretty}")
        except Exception:
            pass
    else:
        print("  🕵️ ANALIZA WYWIADU: Brak logów ❌")
    
    print("="*60)

if __name__ == "__main__":
    # Obsługa argumentów wiersza poleceń
    parser = argparse.ArgumentParser(description="Auto-test gry AI vs AI (domyślnie 10 tur)")
    parser.add_argument('--clean', action='store_true', 
                       help='Wyczyść stare CSV i żetony przed testem')
    parser.add_argument('--clean-only', action='store_true',
                       help='Tylko wyczyść dane (nie uruchamiaj gry)')
    parser.add_argument('--turns', type=int, default=10,
                       help='Liczba tur do zagrania (domyślnie 10)')
    
    args = parser.parse_args()
    
    # Czyszczenie danych jeśli wybrane
    if args.clean or args.clean_only:
        clean_old_data()
        
        if args.clean_only:
            print("🏁 CZYSZCZENIE ZAKOŃCZONE!")
            sys.exit(0)
    
    # Uruchom test gry
    auto_game_10_turns(max_turns=args.turns)
