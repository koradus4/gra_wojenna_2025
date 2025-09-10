"""
Ujednolicony system deploymentu dla Human i AI używający sprawdzonego systemu human.
Zastępuje deployment_ai.py prostym, niezawodnym rozwiązaniem.
"""
from __future__ import annotations
from typing import Any, Optional, Tuple
from pathlib import Path
import json, os, glob, shutil
from engine.token import Token
from ai.logowanie_ai import log_commander_action
from ai.smart_deployment import find_optimal_spawn_position

__all__ = ['unified_deploy_purchased_units']

def unified_deploy_purchased_units(game_engine, player_id):
    """
    Ujednolicony system deploymentu używający sprawdzonej logiki human z panel_mapa.py
    Zastępuje skomplikowany system AI prostym, działającym kodem.
    """
    try:
        current_player = getattr(game_engine, 'current_player_obj', None)
        if not current_player:
            print(f"⚠️ [UNIFIED_DEPLOY] Brak current_player_obj")
            return 0
            
        nation = getattr(current_player, 'nation', 'Unknown')
        assets_path = Path('assets/tokens')
        commander_folder = assets_path / f"nowe_dla_{player_id}"
        
        if not commander_folder.exists():
            print(f"ℹ️ [UNIFIED_DEPLOY] Brak foldera: {commander_folder}")
            return 0
        
        # Znajdź wszystkie token.json w podfolderach (jak w AI)
        token_files = list(commander_folder.glob('*/token.json'))
        if not token_files:
            print(f"ℹ️ [UNIFIED_DEPLOY] Brak plików token.json w: {commander_folder}")
            return 0
        
        deployed = 0
        for token_file in token_files[:50]:  # safety limit
            try:
                # Sprawdź czy już wdrożony (marker system z AI)
                deployed_marker = token_file.parent / '.deployed'
                if deployed_marker.exists():
                    continue
                
                # === SEKCJA HUMAN: Wczytanie i przygotowanie danych ===
                with open(token_file, encoding="utf-8") as f:
                    token_data = json.load(f)
                
                # Ustaw owner na aktualnego gracza (logika human)
                token_owner = f"{player_id} ({nation})"
                token_data["owner"] = token_owner
                
                # === SEKCJA AI: Znajdź pozycję deployment ===
                # Użyj inteligentnego systemu pozycjonowania z AI
                position = find_optimal_spawn_position(token_data, game_engine, player_id)
                if not position:
                    print(f"⚠️ [UNIFIED_DEPLOY] Nie znaleziono pozycji dla tokenu: {token_file}")
                    continue
                
                q, r = position
                
                # === SEKCJA HUMAN: Utworzenie tokenu ===
                # Użyj sprawdzonej metody Token.from_json() z human
                new_token = Token.from_json(token_data)
                new_token.set_position(q, r)
                new_token.owner = token_owner
                
                # Resetuj punkty ruchu i paliwa po wystawieniu (logika human)
                new_token.apply_movement_mode(reset_mp=True)
                new_token.currentFuel = new_token.maxFuel
                
                # === SEKCJA HUMAN: Kopiowanie plików ===
                token_folder = token_file.parent
                png_src = os.path.join(token_folder, "token.png")
                json_src = str(token_file)
                
                if os.path.exists(png_src):
                    dest_dir = os.path.join("assets", "tokens", "aktualne")
                    os.makedirs(dest_dir, exist_ok=True)
                    base_name = os.path.basename(token_folder)
                    
                    # Kopiuj PNG (logika human)
                    png_dst = os.path.join(dest_dir, base_name + ".png")
                    shutil.copy2(png_src, png_dst)
                    
                    # Ustaw nową ścieżkę do obrazka w stats['image']
                    new_token.stats['image'] = png_dst.replace('\\', '/')
                
                # Skopiuj również token.json do katalogu aktualne (logika human)
                if os.path.exists(json_src):
                    json_dst = os.path.join(dest_dir, base_name + ".json")
                    shutil.copy2(json_src, json_dst)
                
                # === SEKCJA HUMAN: Dodanie do runtime ===
                # Natychmiastowe dodanie do game_engine.tokens (kluczowe!)
                game_engine.tokens.append(new_token)
                
                # Synchronizacja z board
                game_engine.board.set_tokens(game_engine.tokens)
                
                # === SEKCJA AI: Cleanup i logging ===
                # Utwórz marker .deployed (system AI)
                deployed_marker.touch()
                
                # Log action (AI logging)
                try:
                    log_commander_action(
                        unit_id=new_token.id,
                        action_type='unified_deploy',
                        from_pos=None,
                        to_pos=(q, r),
                        details={'system': 'unified_human_ai', 'nation': nation}
                    )
                except Exception:
                    pass  # Logging nie może przerywać deploymentu
                
                deployed += 1
                print(f"✅ [UNIFIED_DEPLOY] Wdrożono token: {new_token.id} na {(q, r)}")
                
            except Exception as e:
                print(f"❌ [UNIFIED_DEPLOY] Błąd wdrażania tokenu {token_file}: {e}")
                continue
        
        if deployed > 0:
            print(f"🎯 [UNIFIED_DEPLOY] Wdrożono {deployed} nowych jednostek dla gracza {player_id}")
        
        return deployed
        
    except Exception as e:
        print(f"❌ [UNIFIED_DEPLOY] Błąd główny: {e}")
        return 0


def validate_spawn_position(game_engine, q, r, nation):
    """
    Walidacja pozycji spawn (z logiki human)
    """
    try:
        tile = game_engine.board.get_tile(q, r)
        if not tile or not tile.spawn_nation:
            return False
        
        nation_clean = str(nation).strip().lower()
        spawn_nation_clean = str(tile.spawn_nation).strip().lower()
        
        return spawn_nation_clean == nation_clean
    except:
        return False


# === FUNKCJA INTEGRACJI ===
def replace_ai_deployment_with_unified():
    """
    Instrukcja zastąpienia deployment_ai.py systemem unified
    """
    instructions = """
    PLAN MIGRACJI NA UJEDNOLICONY SYSTEM:
    
    1. W ai_commander.py:
       ZAMIEŃ: from ai.deployment_ai import deploy_purchased_units
       NA:     from ai.unified_deployment import unified_deploy_purchased_units
       
    2. W ai_commander.py:
       ZAMIEŃ: deploy_purchased_units(self.game_engine, self.player_id)
       NA:     unified_deploy_purchased_units(self.game_engine, self.player_id)
    
    3. Zalety ujednoliconego systemu:
       ✅ Używa sprawdzonej logiki Token.from_json() z human
       ✅ Kopiuje pliki tak jak human (nie przesuwa)
       ✅ Natychmiastowe dodanie do game_engine.tokens
       ✅ Proper reset statów jednostek
       ✅ Zachowuje inteligentne pozycjonowanie AI
       ✅ Zachowuje marker system AI
       ✅ Jeden kod dla human i AI - łatwiejszy maintenance
    
    4. Co zostaje z AI:
       ✅ find_optimal_spawn_position() - inteligentne pozycjonowanie
       ✅ Marker .deployed system
       ✅ AI logging
       
    5. Co bierze z Human:
       ✅ Token.from_json() - niezawodne tworzenie obiektów
       ✅ shutil.copy2() - kopiowanie plików
       ✅ apply_movement_mode() - reset statów
       ✅ Natychmiastowa synchronizacja runtime
    """
    return instructions
