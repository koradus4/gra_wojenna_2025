"""
Funkcje czyszczące dla nowej gry
"""
import os
import shutil
from pathlib import Path


def clean_strategic_orders():
    """Usuń stare rozkazy strategiczne"""
    try:
        orders_file = Path("data/strategic_orders.json")
        if orders_file.exists():
            orders_file.unlink()
            print("✅ Usunięto stare rozkazy strategiczne")
        else:
            print("ℹ️ Brak starych rozkazów strategicznych")
    except Exception as e:
        print(f"⚠️ Błąd usuwania rozkazów: {e}")


def clean_purchased_tokens():
    """Usuń wszystkie zakupione żetony z poprzedniej gry"""
    try:
        tokens_dir = Path("assets/tokens")
        deleted_count = 0
        
        # Usuń foldery nowe_dla_X
        for folder in tokens_dir.glob("nowe_dla_*"):
            if folder.is_dir():
                shutil.rmtree(folder)
                deleted_count += 1
                print(f"✅ Usunięto folder: {folder.name}")
        
        if deleted_count > 0:
            print(f"✅ Usunięto {deleted_count} folderów z zakupionymi żetonami")
        else:
            print("ℹ️ Brak zakupionych żetonów do usunięcia")
            
    except Exception as e:
        print(f"⚠️ Błąd usuwania żetonów: {e}")


def clean_ai_logs():
    """Usuń logi AI z poprzedniej gry"""
    try:
        logs_dir = Path("logs")
        deleted_count = 0
        
        # Usuń pliki AI
        for log_file in logs_dir.glob("ai_*.csv"):
            log_file.unlink()
            deleted_count += 1
            print(f"✅ Usunięto log AI: {log_file.name}")
        
        # Usuń foldery AI
        for ai_folder in ["ai_commander", "ai_general"]:
            ai_path = logs_dir / ai_folder
            if ai_path.exists() and ai_path.is_dir():
                shutil.rmtree(ai_path)
                deleted_count += 1
                print(f"✅ Usunięto folder logów: {ai_folder}")
        
        if deleted_count > 0:
            print(f"✅ Usunięto {deleted_count} plików/folderów logów AI")
        else:
            print("ℹ️ Brak logów AI do usunięcia")
            
    except Exception as e:
        print(f"⚠️ Błąd usuwania logów AI: {e}")


def clean_game_logs():
    """Usuń logi akcji gracza z poprzedniej gry"""
    try:
        logs_dir = Path("logs")
        deleted_count = 0
        
        # Usuń pliki actions_*.csv
        for log_file in logs_dir.glob("actions_*.csv"):
            log_file.unlink()
            deleted_count += 1
            print(f"✅ Usunięto log akcji: {log_file.name}")
        
        if deleted_count > 0:
            print(f"✅ Usunięto {deleted_count} logów akcji gracza")
        else:
            print("ℹ️ Brak logów akcji do usunięcia")
            
    except Exception as e:
        print(f"⚠️ Błąd usuwania logów akcji: {e}")


def clean_all_for_new_game():
    """Kompletne czyszczenie dla nowej gry"""
    print("🧹 CZYSZCZENIE DANYCH Z POPRZEDNIEJ GRY...")
    print("=" * 50)
    
    clean_strategic_orders()
    clean_purchased_tokens()
    clean_ai_logs()
    clean_game_logs()
    
    print("=" * 50)
    print("✅ CZYSZCZENIE ZAKOŃCZONE - GOTOWY NA NOWĄ GRĘ!")
    print("")


def quick_clean():
    """Szybkie czyszczenie tylko najważniejszych rzeczy"""
    print("🧹 SZYBKIE CZYSZCZENIE...")
    print("-" * 30)
    
    clean_strategic_orders()
    clean_purchased_tokens()
    
    print("-" * 30)
    print("✅ SZYBKIE CZYSZCZENIE ZAKOŃCZONE!")
    print("")


if __name__ == "__main__":
    # Test czyszczenia
    clean_all_for_new_game()
