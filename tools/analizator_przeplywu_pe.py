#!/usr/bin/env python3
"""
Analizator przepływu PE - generuje krótki raport co rundę.
Każda runda to 2 linie:
1. Generał na start | przychód total | [dowódca1: transfer/wydane/rezerwa] [dowódca2: transfer/wydane/rezerwa] 
2. Generał na koniec
"""

import pandas as pd
import glob
import os
from datetime import datetime

def analyze_pe_flow():
    """Analizuje przepływ PE na podstawie logów CSV"""
    
    print("🔍 ANALIZATOR PRZEPŁYWU PE")
    print("=" * 60)
    
    # Znajdź najnowsze logi
    economy_files = glob.glob("logs/ai_general/ai_economy_*_*.csv")
    if not economy_files:
        print("❌ Brak plików ekonomii!")
        return
    
    # Sortuj po nazwie (data w nazwie)
    economy_files.sort(reverse=True)
    
    for file in economy_files[:2]:  # Analizuj 2 najnowsze sesje
        nation = "Niemcy" if "niemcy" in file.lower() else "Polska"
        print(f"\n📊 {nation.upper()} - {file}")
        print("-" * 40)
        
        try:
            df = pd.read_csv(file)
            
            for index, row in df.iterrows():
                # Pomiń puste wiersze lub bez numeru tury  
                if pd.isna(row.get('turn')) or row.get('turn') == '':
                    continue
                    
                try:
                    runda = index + 1
                    pe_start = int(row['pe_start']) if pd.notna(row['pe_start']) else 0
                    pe_allocated = int(row['pe_allocated']) if pd.notna(row['pe_allocated']) else 0
                    pe_spent_purchases = int(row['pe_spent_purchases']) if pd.notna(row['pe_spent_purchases']) else 0
                    pe_remaining = int(row['pe_remaining']) if pd.notna(row['pe_remaining']) else 0
                    econ_after = int(row['econ_after']) if pd.notna(row['econ_after']) else 0
                    
                    # Oblicz przychód (różnica względem poprzedniej rundy)
                    if index == 0:
                        income = 0  # Pierwsza runda - nie ma poprzedniej
                    else:
                        prev_econ = int(df.iloc[index-1]['econ_after']) if pd.notna(df.iloc[index-1]['econ_after']) else 0
                        income = pe_start - prev_econ
                        if income < 0:
                            income = 0  # Zabezpieczenie przed błędnymi danymi
                    
                    # Linia 1: Stan na start rundy
                    print(f"R{runda:2d} START: {pe_start:3d} PE | przychód: +{income:2d} | alokacja→dowódcy: {pe_allocated:2d} | zakupy: {pe_spent_purchases:2d}")
                    print(f"     KONIEC: {econ_after:3d} PE (pozostało)")
                    print()
                    
                except Exception as e:
                    print(f"❌ Błąd przetwarzania wiersza {index}: {e}")
                    continue
                
        except Exception as e:
            print(f"❌ Błąd analizy {file}: {e}")

def analyze_commanders_pe():
    """Próbuje znaleźć informacje o PE dowódców w logach"""
    
    print("\n🔍 ANALIZA PE DOWÓDCÓW")
    print("=" * 60)
    
    # Sprawdź logi actions - może tam są transfery
    action_files = glob.glob("logs/ai_commander/actions_*.csv")
    if not action_files:
        print("❌ Brak logów akcji dowódców!")
        return
        
    action_files.sort(reverse=True)
    latest_action = action_files[0]
    
    print(f"📁 Analizuję: {latest_action}")
    
    try:
        df = pd.read_csv(latest_action)
        
        # Szukaj wpisów związanych z PE
        pe_related = df[df['action_type'].str.contains('resupply|transfer|pe|PE', case=False, na=False)]
        
        if len(pe_related) > 0:
            print("🔍 Znalezione wpisy PE:")
            for _, row in pe_related.head(10).iterrows():
                timestamp = row['timestamp'][:19] if pd.notna(row['timestamp']) else 'N/A'
                nation = row['nation'] if pd.notna(row['nation']) else 'N/A'
                unit = row['unit_id'] if pd.notna(row['unit_id']) else 'N/A'
                action = row['action_type'] if pd.notna(row['action_type']) else 'N/A'
                details = row['reason'] if pd.notna(row['reason']) else 'N/A'
                print(f"  {timestamp} | {nation} | {unit} | {action} | {details}")
        else:
            print("❌ Brak wpisów PE w logach akcji")
            
    except Exception as e:
        print(f"❌ Błąd analizy akcji: {e}")

def analizuj_przeplyw_pe():
    """Szybki raport PE z dostępnych danych"""
    
    print("\n📋 SZYBKI RAPORT PE")
    print("=" * 60)
    
    analyze_pe_flow()
    analyze_commanders_pe()

if __name__ == "__main__":
    analizuj_przeplyw_pe()
