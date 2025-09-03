#!/usr/bin/env python3
"""FAZA 2 - Kompleksowa analiza ulepszeń AI target selection"""

import pandas as pd
import numpy as np
# import matplotlib.pyplot as plt  # Skipped for now
import os
from datetime import datetime
import glob

def load_latest_diagnostic_data():
    """Ładuje najnowsze dane diagnostyczne z logów"""
    print("📂 Wczytywanie najnowszych danych diagnostycznych...")
    
    log_files = glob.glob("logs/ai_commander/actions_*.csv")
    if not log_files:
        print("❌ Brak plików logów!")
        return None
        
    # Znajdź najnowszy plik
    latest_file = max(log_files, key=os.path.getctime)
    print(f"   📄 Analizuje: {os.path.basename(latest_file)}")
    
    try:
        df = pd.read_csv(latest_file)
        print(f"   📊 Wczytano {len(df)} zapisów")
        return df
    except Exception as e:
        print(f"❌ Błąd wczytywania: {e}")
        return None

def analyze_target_selection_improvements(df):
    """Analiza ulepszeń w selekcji celów"""
    print("\n🎯 [PHASE 2 ANALYSIS] Analiza ulepszeń target selection")
    print("=" * 60)
    
    # Filtruj dane target_analysis
    target_df = df[df['action_type'] == 'target_analysis'].copy()
    
    if len(target_df) == 0:
        print("⚠️ Brak danych target_analysis")
        return
        
    print(f"📊 Analizuje {len(target_df)} decyzji wyboru celu")
    
    # === ANALIZA 1: PODSTAWOWE METRYKI ===
    print("\n📈 1. PODSTAWOWE METRYKI SKUTECZNOŚCI")
    print("-" * 40)
    
    # Sukces rate (cel znaleziony)
    successful_targets = target_df['target_search_best_score'] > 0
    success_rate = successful_targets.mean() * 100
    print(f"   ✅ Success rate: {success_rate:.1f}% ({successful_targets.sum()}/{len(target_df)})")
    
    # Fallback rate (używanie mechanizmu awaryjnego)
    fallback_rate = target_df['fallback_used'].mean() * 100
    print(f"   🔄 Fallback rate: {fallback_rate:.1f}%")
    
    # === ANALIZA 2: PATHFINDING PERFORMANCE ===
    print("\n🗺️ 2. ANALIZA PATHFINDINGU")
    print("-" * 40)
    
    # Średnie niepowodzenia pathfindingu
    avg_failures = target_df['pathfinding_failures'].mean()
    max_failures = target_df['pathfinding_failures'].max()
    print(f"   🚫 Średnie niepowodzenia pathfinding: {avg_failures:.2f}")
    print(f"   📊 Max niepowodzenia: {max_failures}")
    
    # Analiza kandydatów
    avg_valid = target_df['valid_candidates'].mean()
    avg_total = target_df['total_candidates'].mean()
    print(f"   🎯 Średnie kandydatów: {avg_valid:.1f} ważnych z {avg_total:.1f} całkowitych")
    
    if avg_total > 0:
        candidate_efficiency = (avg_valid / avg_total) * 100
        print(f"   📈 Efektywność kandydatów: {candidate_efficiency:.1f}%")
    
    # === ANALIZA 3: ZASOBÓW JEDNOSTEK ===
    print("\n⚡ 3. ANALIZA ZASOBÓW JEDNOSTEK")
    print("-" * 40)
    
    # MP i fuel statistics
    mp_stats = target_df['unit_mp_available'].describe()
    fuel_stats = target_df['unit_fuel_available'].describe()
    
    print(f"   🏃 MP dostępne: średnio {mp_stats['mean']:.1f} (min: {mp_stats['min']:.0f}, max: {mp_stats['max']:.0f})")
    print(f"   ⛽ Fuel dostępne: średnio {fuel_stats['mean']:.1f} (min: {fuel_stats['min']:.0f}, max: {fuel_stats['max']:.0f})")
    
    # Korelacja MP z sukcesem
    if successful_targets.sum() > 0:
        success_mp = target_df[successful_targets]['unit_mp_available'].mean()
        fail_mp = target_df[~successful_targets]['unit_mp_available'].mean()
        print(f"   🎯 MP przy sukcesie: {success_mp:.1f} vs niepowodzeniu: {fail_mp:.1f}")
    
    # === ANALIZA 4: DYSTANSE I SCORING ===
    print("\n📏 4. ANALIZA DYSTANSÓW I SCORINGU")
    print("-" * 40)
    
    # Filtruj realistyczne dystanse (999 to fallback)
    realistic_distances = target_df[target_df['target_search_best_distance'] < 900]
    
    if len(realistic_distances) > 0:
        avg_distance = realistic_distances['target_search_best_distance'].mean()
        max_distance = realistic_distances['target_search_best_distance'].max()
        print(f"   📐 Średni dystans do celu: {avg_distance:.1f}")
        print(f"   📊 Max dystans: {max_distance}")
        
        # Score analysis
        avg_score = realistic_distances['target_search_best_score'].mean()
        print(f"   🎖️ Średni score celu: {avg_score:.2f}")
    else:
        print("   ⚠️ Brak realistycznych dystansów (wszystkie fallback)")
    
    # === ANALIZA 5: COMPARISON PRZED/PO ULEPSZENIACH ===
    print("\n🔄 5. PORÓWNANIE ULEPSZEŃ (FAZA 2)")
    print("-" * 40)
    
    # Sprawdź czy mamy nowe kolumny FAZA 2
    phase2_columns = ['pathfinding_failures', 'valid_candidates', 'total_candidates', 'unit_mp_available', 'unit_fuel_available']
    has_phase2 = all(col in target_df.columns for col in phase2_columns)
    
    if has_phase2:
        print("   ✅ FAZA 2 ulepszenia zaimplementowane")
        print(f"   📊 Śledzone pathfinding failures: {target_df['pathfinding_failures'].sum()} łącznie")
        print(f"   🎯 Śledzone kandydaci: {target_df['total_candidates'].sum()} łącznie")
        
        # Efektywność pathfindingu
        total_pathfinding_attempts = target_df['total_candidates'].sum()
        total_pathfinding_failures = target_df['pathfinding_failures'].sum()
        
        if total_pathfinding_attempts > 0:
            pathfinding_success_rate = ((total_pathfinding_attempts - total_pathfinding_failures) / total_pathfinding_attempts) * 100
            print(f"   🗺️ Pathfinding success rate: {pathfinding_success_rate:.1f}%")
    else:
        print("   ❌ FAZA 2 ulepszenia nie wykryte")
    
    return target_df

def generate_recommendations(df):
    """Generuje rekomendacje na podstawie analizy"""
    print("\n💡 [RECOMMENDATIONS] Rekomendacje ulepszeń")
    print("=" * 60)
    
    target_df = df[df['action_type'] == 'target_analysis']
    
    if len(target_df) == 0:
        return
    
    # Analiza problemów
    high_failure_rate = target_df['fallback_used'].mean() > 0.5
    low_candidates = target_df['total_candidates'].mean() < 5
    pathfinding_issues = target_df['pathfinding_failures'].mean() > 0.2
    
    recommendations = []
    
    if high_failure_rate:
        recommendations.append("🔴 PRIORYTET: Wysoki fallback rate - popraw algorytm selekcji celów")
    
    if low_candidates:
        recommendations.append("🟡 ŚREDNI: Mało kandydatów - zwiększ zasięg poszukiwań lub kryteria")
        
    if pathfinding_issues:
        recommendations.append("🟠 ŚREDNI: Problemy z pathfindingiem - zoptymalizuj find_path")
    
    # MP analysis recommendations
    mp_avg = target_df['unit_mp_available'].mean()
    if mp_avg < 3:
        recommendations.append("🔵 INFO: Niskie MP jednostek - rozważ lepsze zarządzanie ruchem")
    
    if not recommendations:
        recommendations.append("✅ DOBRA WIADOMOŚĆ: Brak krytycznych problemów wykrytych")
    
    for i, rec in enumerate(recommendations, 1):
        print(f"   {i}. {rec}")
    
    return recommendations

def create_diagnostic_summary():
    """Tworzy podsumowanie diagnostyczne"""
    print("\n📋 [SUMMARY] Podsumowanie FAZA 2")
    print("=" * 60)
    
    df = load_latest_diagnostic_data()
    if df is None:
        return
    
    # Analiza główna
    target_analysis = analyze_target_selection_improvements(df)
    
    # Rekomendacje
    recommendations = generate_recommendations(df)
    
    # Zapisz podsumowanie
    summary_file = f"logs/ai_commander/phase2_summary_{datetime.now().strftime('%Y%m%d_%H%M')}.txt"
    
    try:
        with open(summary_file, 'w', encoding='utf-8') as f:
            f.write("FAZA 2 AI IMPROVEMENTS - DIAGNOSTIC SUMMARY\\n")
            f.write("=" * 50 + "\\n\\n")
            f.write(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\\n")
            f.write(f"Data source: Latest logs\\n")
            f.write(f"Records analyzed: {len(df)}\\n\\n")
            
            if target_analysis is not None:
                f.write("TARGET SELECTION METRICS:\\n")
                f.write(f"- Success rate: {(target_analysis['target_search_best_score'] > 0).mean()*100:.1f}%\\n")
                f.write(f"- Fallback rate: {target_analysis['fallback_used'].mean()*100:.1f}%\\n")
                f.write(f"- Avg pathfinding failures: {target_analysis['pathfinding_failures'].mean():.2f}\\n")
                f.write(f"- Avg candidates: {target_analysis['total_candidates'].mean():.1f}\\n\\n")
            
            f.write("RECOMMENDATIONS:\\n")
            for i, rec in enumerate(recommendations, 1):
                f.write(f"{i}. {rec}\\n")
        
        print(f"📄 Podsumowanie zapisane: {summary_file}")
        
    except Exception as e:
        print(f"❌ Błąd zapisu podsumowania: {e}")

def main():
    """Główna funkcja analizy FAZA 2"""
    print("🚀 [PHASE 2] Kompleksowa analiza ulepszeń AI")
    print("Analiza pathfindingu, target selection i resource management")
    print("=" * 70)
    
    create_diagnostic_summary()
    
    print("\\n✅ Analiza FAZA 2 zakończona!")
    print("📊 Sprawdź szczegółowe wyniki w logs/ai_commander/")

if __name__ == "__main__":
    main()
