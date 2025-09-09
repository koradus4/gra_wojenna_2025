"""Moduł wdrażania zakupionych jednostek (deployment) wydzielony z ai_commander.
Zawiera funkcje: deploy_purchased_units, find_deployment_position, create_and_deploy_token.
NOWE: Integracja z smart_deployment.py i dodawanie do start_tokens.json
"""
from __future__ import annotations
from typing import Any, Optional, Tuple
from pathlib import Path
import json, os, glob
from ai.logowanie_ai import log_commander_action
from ai.ruch_jednostek import move_towards  # potencjalnie przydatne przyszłościowo
from ai.smart_deployment import find_optimal_spawn_position  # NOWE: Inteligentny spawn

__all__ = [
    'deploy_purchased_units','find_deployment_position','create_and_deploy_token'
]

def deploy_purchased_units(game_engine, player_id):
    try:
        current_player = getattr(game_engine,'current_player_obj',None)
        if not current_player:
            return 0
        nation = getattr(current_player,'nation','Unknown')
        assets_path = Path('assets/tokens')
        commander_folder = assets_path / f"nowe_dla_{player_id}"
        if not commander_folder.exists():
            return 0
        # znajdź wszystkie token.json w podfolderach
        token_files = list(commander_folder.glob('*/token.json'))
        if not token_files:
            return 0
        deployed = 0
        for tf in token_files[:50]:  # safety limit
            try:
                with open(tf,'r',encoding='utf-8') as f:
                    data = json.load(f)
                # sprawdź czy już wdrożony (np. marker file)
                deployed_marker = tf.parent / '.deployed'
                if deployed_marker.exists():
                    continue
                # NOWE: Przekaż dane jednostki do inteligentnego wyboru pozycji
                pos = find_deployment_position(game_engine, player_id, data)
                if not pos:
                    continue
                created = create_and_deploy_token(game_engine, player_id, data, pos)
                if created:
                    deployed += 1
                    # Przenieś pliki do aktualne/ jak robi człowiek
                    print(f"🔧 [DEBUG] Przenoszę token do aktualne/: {tf}")
                    move_token_files_to_aktualne(tf)
                    deployed_marker.touch()
                    print(f"✅ [DEBUG] Token przeniesiony i marker utworzony")
            except Exception:
                continue
        if deployed>0:
            print(f"[DEPLOY] Wdrożono {deployed} nowych jednostek dla gracza {player_id}")
        return deployed
    except Exception as e:
        print(f"❌ [DEPLOY] Błąd: {e}")
        return 0

def find_deployment_position(game_engine, player_id, unit_data=None) -> Optional[Tuple[int,int]]:
    """Znajduje optymalną pozycję deployment używając inteligentnego systemu smart_deployment"""
    try:
        print(f"[DEPLOY] Szukam inteligentnej pozycji spawn dla gracza {player_id}")
        
        # NOWE: Użyj inteligentnego systemu spawn z smart_deployment.py
        optimal_position = find_optimal_spawn_position(unit_data or {}, game_engine, player_id)
        
        if optimal_position:
            print(f"✅ [DEPLOY] Znaleziono optymalną pozycję: {optimal_position}")
            return optimal_position
        
        print(f"⚠️ [DEPLOY] Inteligentny system nie znalazł pozycji, fallback do starego systemu...")
        
        # FALLBACK: Stary system jako backup
        board = getattr(game_engine,'board',None)
        if not board:
            return None
        # heurystyka: znajdź pierwszy mój token i spróbuj w jego sąsiedztwie
        my_tokens = [t for t in getattr(game_engine,'tokens',[]) if str(getattr(t,'owner','')).startswith(str(player_id))]
        if not my_tokens:
            return None
        base = my_tokens[0]
        base_pos = (getattr(base,'q',0), getattr(base,'r',0))
        # sprawdź sąsiadów z ograniczeniem 12 hexów
        for dq in range(-2,3):
            for dr in range(-2,3):
                q = base_pos[0]+dq
                r = base_pos[1]+dr
                if board.is_occupied(q,r):
                    continue
                print(f"✅ [DEPLOY] Fallback pozycja: {(q,r)}")
                return (q,r)
    except Exception as e:
        print(f"❌ [DEPLOY] Błąd wyszukiwania pozycji: {e}")
        return None
    return None

def create_and_deploy_token(game_engine, player_id, token_data:dict, position:Tuple[int,int]):
    try:
        TokenClass = None
        try:
            from engine.token import Token as TokenClass
        except Exception:
            pass
        if not TokenClass:
            return False
        q,r = position
        new_token = TokenClass(
            id=token_data.get('id', f"AI_NEW_{player_id}"),
            owner=f"{player_id} ({getattr(getattr(game_engine,'current_player_obj',None),'nation','AI')})",
            q=q,r=r,
            stats=token_data.get('stats',{}),
        )
        game_engine.tokens.append(new_token)
        try:
            log_commander_action(
                unit_id=getattr(new_token,'id','?'),
                action_type='deploy_new',
                from_pos=None,
                to_pos=(q,r),
                reason='deployment_ai',
                player_nation=getattr(getattr(game_engine,'current_player_obj',None),'nation','AI'),
                extra={'phase':'deployment'}
            )
        except Exception:
            pass
        return True
    except Exception as e:
        print(f"❌ [DEPLOY] Błąd tworzenia tokenu: {e}")
        return False

def move_token_files_to_aktualne(token_json_path):
    """Przenosi pliki tokena z nowe_dla_X/ do aktualne/ i aktualizuje index.json"""
    try:
        import shutil
        import json
        token_folder = token_json_path.parent
        token_name = token_folder.name
        
        aktualne_dir = Path("assets/tokens/aktualne")
        aktualne_dir.mkdir(exist_ok=True)
        
        # Najpierw odczytaj i popraw JSON tokena
        json_src = token_folder / "token.json"
        json_dst = aktualne_dir / f"{token_name}.json"
        
        if json_src.exists():
            # Wczytaj JSON i popraw ścieżkę obrazka
            with open(json_src, 'r', encoding='utf-8') as f:
                token_data = json.load(f)
            
            # Popraw ścieżkę obrazka na aktualne/
            token_data["image"] = f"assets/tokens/aktualne/{token_name}.png"
            
            # Zapisz poprawiony JSON
            with open(json_dst, 'w', encoding='utf-8') as f:
                json.dump(token_data, f, indent=2, ensure_ascii=False)
            
            # Usuń oryginalny JSON
            json_src.unlink()
            
        # Przenieś PNG
        png_src = token_folder / "token.png" 
        png_dst = aktualne_dir / f"{token_name}.png"
        if png_src.exists():
            shutil.move(str(png_src), str(png_dst))
            
        # Usuń pusty folder
        if token_folder.exists() and not list(token_folder.iterdir()):
            token_folder.rmdir()
            
        # KLUCZOWE: Dodaj token do index.json
        print(f"🔧 [DEBUG] Wywołuję update_index_with_new_token dla: {json_dst}")
        update_index_with_new_token(json_dst)
        print(f"🔧 [DEBUG] update_index_with_new_token zakończone")
            
        print(f"✅ [DEPLOY] Przeniesiono {token_name} do aktualne/ i dodano do index.json")
        
    except Exception as e:
        print(f"❌ [DEPLOY] Błąd przenoszenia plików: {e}")

def update_index_with_new_token(token_json_path):
    """Dodaje nowy token do assets/tokens/index.json i start_tokens.json"""
    try:
        print(f"🔧 [DEBUG] update_index_with_new_token WYWOŁANA dla: {token_json_path}")
        import json
        
        # Wczytaj dane tokena
        with open(token_json_path, 'r', encoding='utf-8') as f:
            token_data = json.load(f)
            
        # 1. Dodaj do index.json
        index_path = Path("assets/tokens/index.json")
        if index_path.exists():
            with open(index_path, 'r', encoding='utf-8') as f:
                index_data = json.load(f)
        else:
            index_data = []
            
        token_id = token_data.get("id", "")
        if not any(existing["id"] == token_id for existing in index_data):
            # Dodaj nowy token
            index_data.append(token_data)
            
            # Zapisz zaktualizowany index.json
            with open(index_path, 'w', encoding='utf-8') as f:
                json.dump(index_data, f, indent=2, ensure_ascii=False)
                
            print(f"✅ [DEPLOY] Dodano {token_id} do index.json")
        else:
            print(f"ℹ️  [DEPLOY] Token {token_id} już istnieje w index.json")
        
        # 2. KLUCZOWE: Dodaj do start_tokens.json z pozycją spawn
        print(f"🔧 [DEBUG] Dodawanie do start_tokens.json dla token_id: {token_id}")
        start_tokens_path = Path("assets/start_tokens.json")
        if start_tokens_path.exists():
            with open(start_tokens_path, 'r', encoding='utf-8') as f:
                start_data = json.load(f)
            print(f"🔧 [DEBUG] Wczytano {len(start_data)} istniejących pozycji z start_tokens.json")
        else:
            start_data = []
            print(f"🔧 [DEBUG] start_tokens.json nie istnieje, tworzę nowy")
            
        # Sprawdź czy token już nie ma pozycji
        if not any(existing["id"] == token_id for existing in start_data):
            # Znajdź wolny spawn point dla nacji tokena
            spawn_position = find_free_spawn_point(token_data.get("nation", ""))
            
            if spawn_position:
                # Dodaj token z pozycją
                start_entry = {
                    "id": token_id,
                    "q": spawn_position[0],
                    "r": spawn_position[1]
                }
                start_data.append(start_entry)
                
                # Zapisz zaktualizowany start_tokens.json
                with open(start_tokens_path, 'w', encoding='utf-8') as f:
                    json.dump(start_data, f, indent=2, ensure_ascii=False)
                    
                print(f"✅ [DEPLOY] Dodano {token_id} do start_tokens.json na pozycji {spawn_position}")
            else:
                print(f"⚠️ [DEPLOY] Brak wolnych spawn points dla nacji {token_data.get('nation', '')}")
        else:
            print(f"ℹ️  [DEPLOY] Token {token_id} już ma pozycję w start_tokens.json")
            
    except Exception as e:
        print(f"❌ [DEPLOY] Błąd aktualizacji plików tokenów: {e}")

def find_free_spawn_point(nation):
    """Znajdź wolny spawn point dla danej nacji"""
    try:
        import json
        
        # Wczytaj map_data.json dla spawn points
        map_data_path = Path("data/map_data.json")
        if not map_data_path.exists():
            print(f"❌ [SPAWN] Brak pliku map_data.json")
            return None
            
        with open(map_data_path, 'r', encoding='utf-8') as f:
            map_data = json.load(f)
            
        spawn_points = map_data.get("spawn_points", {}).get(nation, [])
        if not spawn_points:
            print(f"❌ [SPAWN] Brak spawn points dla nacji {nation}")
            return None
            
        # Wczytaj zajęte pozycje z start_tokens.json
        start_tokens_path = Path("assets/start_tokens.json")
        occupied_positions = set()
        if start_tokens_path.exists():
            with open(start_tokens_path, 'r', encoding='utf-8') as f:
                start_data = json.load(f)
            occupied_positions = {(pos["q"], pos["r"]) for pos in start_data}
        
        # Znajdź pierwszy wolny spawn point
        for spawn_str in spawn_points:
            try:
                q, r = map(int, spawn_str.split(','))
                if (q, r) not in occupied_positions:
                    print(f"✅ [SPAWN] Znaleziono wolny spawn point ({q},{r}) dla {nation}")
                    return (q, r)
            except ValueError:
                print(f"⚠️ [SPAWN] Błędny format spawn point: {spawn_str}")
                continue
                
        print(f"⚠️ [SPAWN] Wszystkie spawn points zajęte dla {nation}")
        # Zwróć pierwszy spawn point jako fallback
        try:
            q, r = map(int, spawn_points[0].split(','))
            return (q, r)
        except (ValueError, IndexError):
            return None
            
    except Exception as e:
        print(f"❌ [SPAWN] Błąd wyszukiwania spawn point: {e}")
        return None
