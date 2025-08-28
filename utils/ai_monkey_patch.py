#!/usr/bin/env python3
"""
MONKEY PATCH dla AI General i AI Commander
Dodaje szczegółowe logowanie do istniejących metod bez modyfikowania oryginalnego kodu
"""

import sys
import traceback
from pathlib import Path
from typing import Any
import importlib
import functools

# Dodaj ścieżkę do głównego folderu
sys.path.append(str(Path(__file__).parent.parent))

# Dodaj ścieżkę do utils
sys.path.append(str(Path(__file__).parent))
from ai_flow_logger import get_ai_flow_logger

def patch_ai_general_with_logging():
    """Dodaje szczegółowe logowanie do AI General"""
    
    try:
        # Import AI General
        from ai.ai_general import AIGeneral
        
        # Zachowaj oryginalne metody
        original_purchase_unit = AIGeneral.purchase_unit_programmatically
        original_make_turn = AIGeneral.make_turn
        original_analyze_units = AIGeneral.analyze_units
        original_consider_purchase = AIGeneral.consider_unit_purchase
        
        def logged_purchase_unit_programmatically(self, player, purchase_plan):
            """Wersja z logowaniem dla purchase_unit_programmatically"""
            nation = getattr(self, 'display_nation', 'Unknown')
            turn = getattr(self, '_current_turn', 0)
            logger = get_ai_flow_logger(nation)
            
            commander_id = purchase_plan.get('commander_id')
            unit_type = purchase_plan.get('type')
            unit_size = purchase_plan.get('size')
            cost = purchase_plan.get('cost', 0)
            
            # PE przed zakupem
            pe_before = player.economy.get_points().get('economic_points', 0)
            
            # Log rozpoczęcia zakupu
            logger.log_main_event(turn, "PURCHASE", "AIGeneral", "purchase_unit_start", "INFO",
                                 f"Starting purchase: {unit_type} {unit_size} for commander {commander_id}",
                                 {"cost": cost, "pe_before": pe_before})
            
            # Sprawdź czy folder będzie utworzony
            folder_path = Path(f"assets/tokens/nowe_dla_{commander_id}")
            folder_existed_before = folder_path.exists()
            
            try:
                # Wywołaj oryginalną metodę
                result = original_purchase_unit(self, player, purchase_plan)
                
                # PE po zakupie
                pe_after = player.economy.get_points().get('economic_points', 0)
                
                # Sprawdź co zostało utworzone
                folder_created = folder_path.exists() and not folder_existed_before
                
                # Znajdź utworzony token
                json_created = False
                image_created = False
                token_folder = None
                
                if folder_path.exists():
                    token_folders = list(folder_path.glob("*/"))
                    if token_folders:
                        token_folder = token_folders[-1]  # Ostatnio utworzony
                        json_created = (token_folder / "token.json").exists()
                        image_created = (token_folder / "token.png").exists()
                
                # Log szczegółów zakupu
                logger.log_purchase_event(
                    turn=turn,
                    commander_id=commander_id,
                    unit_type=unit_type,
                    unit_size=unit_size,
                    cost=cost,
                    pe_before=pe_before,
                    pe_after=pe_after,
                    folder_created=folder_created,
                    json_created=json_created,
                    image_created=image_created,
                    supports=purchase_plan.get('supports', []),
                    purchase_reason=f"AI decision: {purchase_plan.get('name', 'unknown')}",
                    success=result
                )
                
                # Log plików tokena jeśli utworzono
                if token_folder and json_created:
                    try:
                        import json
                        with open(token_folder / "token.json", 'r', encoding='utf-8') as f:
                            token_data = json.load(f)
                        
                        logger.log_token_creation_details(turn, token_data, {
                            'folder': str(token_folder),
                            'json': str(token_folder / "token.json"),
                            'image': str(token_folder / "token.png")
                        })
                    except Exception as e:
                        logger.log_debug_event(turn, "AIGeneral", "purchase_unit", 
                                             "token_data_read_error", error_msg=str(e))
                
                # Log sukcesu
                logger.log_main_event(turn, "PURCHASE", "AIGeneral", "purchase_unit_complete", 
                                     "SUCCESS" if result else "FAILED",
                                     f"Purchase result: {result}, PE spent: {pe_before - pe_after}",
                                     {"pe_spent": pe_before - pe_after, "success": result})
                
                return result
                
            except Exception as e:
                # Log błędu
                logger.log_main_event(turn, "PURCHASE", "AIGeneral", "purchase_unit_error", "ERROR",
                                     f"Purchase failed: {str(e)}", error_msg=str(e))
                
                logger.log_purchase_event(
                    turn=turn,
                    commander_id=commander_id,
                    unit_type=unit_type,
                    unit_size=unit_size,
                    cost=cost,
                    pe_before=pe_before,
                    pe_after=pe_before,  # Nie zmienione przez błąd
                    folder_created=False,
                    json_created=False,
                    image_created=False,
                    supports=purchase_plan.get('supports', []),
                    purchase_reason="Purchase failed",
                    success=False,
                    error_msg=str(e)
                )
                
                raise
        
        def logged_make_turn(self, game_engine):
            """Wersja z logowaniem dla make_turn"""
            nation = getattr(self, 'display_nation', 'Unknown')
            turn = getattr(game_engine, 'turn_number', None) or getattr(game_engine, 'current_turn', 0)
            logger = get_ai_flow_logger(nation)
            
            # Log rozpoczęcia tury
            logger.log_main_event(turn, "TURN", "AIGeneral", "turn_start", "INFO",
                                 f"AI General turn started for {nation}")
            
            try:
                # Wywołaj oryginalną metodę
                result = original_make_turn(self, game_engine)
                
                # Log zakończenia tury
                logger.log_main_event(turn, "TURN", "AIGeneral", "turn_complete", "SUCCESS",
                                     f"AI General turn completed for {nation}")
                
                # Generuj raport podsumowujący
                logger.generate_summary_report(turn)
                
                return result
                
            except Exception as e:
                # Log błędu
                logger.log_main_event(turn, "TURN", "AIGeneral", "turn_error", "ERROR",
                                     f"AI General turn failed: {str(e)}", error_msg=str(e))
                raise
        
        def logged_analyze_units(self, game_engine, player):
            """Wersja z logowaniem dla analyze_units"""
            nation = getattr(self, 'display_nation', 'Unknown')
            turn = getattr(self, '_current_turn', 0)
            logger = get_ai_flow_logger(nation)
            
            logger.log_main_event(turn, "ANALYSIS", "AIGeneral", "analyze_units_start", "INFO",
                                 "Starting unit analysis")
            
            try:
                result = original_analyze_units(self, game_engine, player)
                
                # Log wyników analizy
                unit_analysis = getattr(self, '_unit_analysis', {})
                logger.log_main_event(turn, "ANALYSIS", "AIGeneral", "analyze_units_complete", "SUCCESS",
                                     "Unit analysis completed", unit_analysis)
                
                return result
                
            except Exception as e:
                logger.log_main_event(turn, "ANALYSIS", "AIGeneral", "analyze_units_error", "ERROR",
                                     f"Unit analysis failed: {str(e)}", error_msg=str(e))
                raise
        
        def logged_consider_unit_purchase(self, game_engine, player, available_points):
            """Wersja z logowaniem dla consider_unit_purchase"""
            nation = getattr(self, 'display_nation', 'Unknown')
            turn = getattr(self, '_current_turn', 0)
            logger = get_ai_flow_logger(nation)
            
            logger.log_main_event(turn, "PLANNING", "AIGeneral", "consider_purchase_start", "INFO",
                                 f"Planning purchases with {available_points} PE")
            
            try:
                result = original_consider_purchase(self, game_engine, player, available_points)
                
                # Log wyników planowania
                context = getattr(self, '_last_decision_context', {})
                units_bought = context.get('units_bought', 0)
                
                logger.log_main_event(turn, "PLANNING", "AIGeneral", "consider_purchase_complete", "SUCCESS",
                                     f"Purchase planning completed, {units_bought} units planned", context)
                
                return result
                
            except Exception as e:
                logger.log_main_event(turn, "PLANNING", "AIGeneral", "consider_purchase_error", "ERROR",
                                     f"Purchase planning failed: {str(e)}", error_msg=str(e))
                raise
        
        # Zastąp metody wersją z logowaniem
        AIGeneral.purchase_unit_programmatically = logged_purchase_unit_programmatically
        AIGeneral.make_turn = logged_make_turn
        AIGeneral.analyze_units = logged_analyze_units
        AIGeneral.consider_unit_purchase = logged_consider_unit_purchase
        
        print("✅ [MONKEY PATCH] AI General patched with enhanced logging")
        
    except Exception as e:
        print(f"❌ [MONKEY PATCH] Failed to patch AI General: {e}")

def patch_ai_commander_with_logging():
    """Dodaje szczegółowe logowanie do AI Commander"""
    
    try:
        # Import funkcji AI Commander
        import ai.ai_commander as ai_commander
        
        # Zachowaj oryginalne funkcje
        original_deploy_purchased = ai_commander.deploy_purchased_units
        original_create_and_deploy = ai_commander.create_and_deploy_token
        original_find_deployment = ai_commander.find_deployment_position
        original_make_tactical_turn = ai_commander.make_tactical_turn
        
        def logged_deploy_purchased_units(game_engine, player_id):
            """Wersja z logowaniem dla deploy_purchased_units"""
            # Pobierz nation z current_player
            current_player = getattr(game_engine, 'current_player_obj', None)
            nation = getattr(current_player, 'nation', 'Unknown') if current_player else 'Unknown'
            turn = getattr(game_engine, 'turn', 0)
            logger = get_ai_flow_logger(nation)
            
            logger.log_main_event(turn, "DEPLOYMENT", "AICommander", "deploy_start", "INFO",
                                 f"Starting deployment for commander {player_id}")
            
            # Skanuj foldery przed deployment
            folder_path = Path(f"assets/tokens/nowe_dla_{player_id}")
            tokens_before = []
            
            if folder_path.exists():
                for token_folder in folder_path.glob("*/"):
                    token_json = token_folder / "token.json"
                    if token_json.exists():
                        tokens_before.append(str(token_json))
            
            logger.log_folder_scan(turn, str(folder_path), {str(player_id): tokens_before})
            
            try:
                result = original_deploy_purchased(game_engine, player_id)
                
                # Sprawdź co zostało po deployment
                tokens_after = []
                if folder_path.exists():
                    for token_folder in folder_path.glob("*/"):
                        token_json = token_folder / "token.json"
                        if token_json.exists():
                            tokens_after.append(str(token_json))
                
                deployed_count = len(tokens_before) - len(tokens_after)
                
                logger.log_main_event(turn, "DEPLOYMENT", "AICommander", "deploy_complete", "SUCCESS",
                                     f"Deployment completed: {deployed_count} units deployed",
                                     {"tokens_before": len(tokens_before), "tokens_after": len(tokens_after),
                                      "deployed": deployed_count})
                
                return result
                
            except Exception as e:
                logger.log_main_event(turn, "DEPLOYMENT", "AICommander", "deploy_error", "ERROR",
                                     f"Deployment failed: {str(e)}", error_msg=str(e))
                raise
        
        def logged_create_and_deploy_token(unit_data, position, game_engine, player_id):
            """Wersja z logowaniem dla create_and_deploy_token"""
            current_player = getattr(game_engine, 'current_player_obj', None)
            nation = getattr(current_player, 'nation', 'Unknown') if current_player else 'Unknown'
            turn = getattr(game_engine, 'turn', 0)
            logger = get_ai_flow_logger(nation)
            
            token_id = unit_data.get('id', 'unknown')
            unit_type = unit_data.get('unitType', 'unknown')
            
            logger.log_main_event(turn, "TOKEN_CREATION", "AICommander", "create_token_start", "INFO",
                                 f"Creating token {token_id} at position {position}")
            
            try:
                # Sprawdź stan board przed
                board_tokens_before = len(getattr(game_engine.board, 'tokens', []))
                
                result = original_create_and_deploy(unit_data, position, game_engine, player_id)
                
                # Sprawdź stan board po
                board_tokens_after = len(getattr(game_engine.board, 'tokens', []))
                board_added = board_tokens_after > board_tokens_before
                
                logger.log_deployment_event(
                    turn=turn,
                    commander_id=player_id,
                    token_id=token_id,
                    unit_type=unit_type,
                    deploy_position=position,
                    source_folder="AI purchase",
                    deployment_reason="Automatic AI deployment",
                    board_added=board_added,
                    folder_cleaned=False,  # Będzie wyczyszczony przez deploy_purchased_units
                    success=result
                )
                
                return result
                
            except Exception as e:
                logger.log_deployment_event(
                    turn=turn,
                    commander_id=player_id,
                    token_id=token_id,
                    unit_type=unit_type,
                    deploy_position=position,
                    source_folder="AI purchase",
                    deployment_reason="Automatic AI deployment",
                    board_added=False,
                    folder_cleaned=False,
                    success=False,
                    error_msg=str(e)
                )
                raise
        
        def logged_make_tactical_turn(game_engine, player_id=None):
            """Wersja z logowaniem dla make_tactical_turn"""
            current_player = getattr(game_engine, 'current_player_obj', None)
            nation = getattr(current_player, 'nation', 'Unknown') if current_player else 'Unknown'
            turn = getattr(game_engine, 'turn', 0)
            logger = get_ai_flow_logger(nation)
            
            actual_player_id = player_id or getattr(current_player, 'id', 0)
            
            logger.log_main_event(turn, "TACTICAL", "AICommander", "tactical_turn_start", "INFO",
                                 f"AI Commander tactical turn for player {actual_player_id}")
            
            try:
                result = original_make_tactical_turn(game_engine, player_id)
                
                logger.log_main_event(turn, "TACTICAL", "AICommander", "tactical_turn_complete", "SUCCESS",
                                     f"Tactical turn completed for player {actual_player_id}")
                
                return result
                
            except Exception as e:
                logger.log_main_event(turn, "TACTICAL", "AICommander", "tactical_turn_error", "ERROR",
                                     f"Tactical turn failed: {str(e)}", error_msg=str(e))
                raise
        
        # Zastąp funkcje wersją z logowaniem
        ai_commander.deploy_purchased_units = logged_deploy_purchased_units
        ai_commander.create_and_deploy_token = logged_create_and_deploy_token
        ai_commander.make_tactical_turn = logged_make_tactical_turn
        
        print("✅ [MONKEY PATCH] AI Commander patched with enhanced logging")
        
    except Exception as e:
        print(f"❌ [MONKEY PATCH] Failed to patch AI Commander: {e}")

def apply_all_ai_patches():
    """Aplikuje wszystkie monkey patches dla AI"""
    print("🐵 [MONKEY PATCH] Applying enhanced logging to AI components...")
    patch_ai_general_with_logging()
    patch_ai_commander_with_logging()
    print("✅ [MONKEY PATCH] All AI components patched successfully!")

if __name__ == "__main__":
    # Test monkey patches
    print("🧪 Testing AI monkey patches...")
    apply_all_ai_patches()
    print("✅ Monkey patches applied successfully!")
