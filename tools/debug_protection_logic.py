#!/usr/bin/env python3
"""
DEBUG: Sprawdzenie logiki ochrony plików
"""

from pathlib import Path

def debug_protection():
    """Debug logiki ochrony"""
    
    logs_dir = Path("c:/Users/klif/OneDrive/Pulpit/gra wojenna 17082025/logs")
    
    # Wzorce ochrony z kodu
    protected_patterns = [
        "analysis/ml_ready",
        "analysis/raporty", 
        "analysis/statystyki",
        "vp_intelligence/archives"
    ]
    
    # Znajdź pliki w analysis
    analysis_files = list(logs_dir.rglob("analysis/**/*.json"))
    
    print("🔍 DEBUG OCHRONY PLIKÓW")
    print("=" * 40)
    
    for file_path in analysis_files[:8]:  # Sprawdź pierwsze 8
        relative_path = file_path.relative_to(logs_dir)
        relative_str = str(relative_path).replace("\\", "/")  # Windows -> Unix ścieżki
        
        print(f"\n📁 Plik: {file_path.name}")
        print(f"   🗂️ Względna ścieżka: {relative_str}")
        
        matches = []
        for pattern in protected_patterns:
            if pattern in relative_str:
                matches.append(pattern)
        
        if matches:
            print(f"   ✅ CHRONIONY - pasuje do: {matches}")
        else:
            print(f"   ❌ NIE CHRONIONY - żaden wzorzec nie pasuje")
            print(f"   🔍 Sprawdzane wzorce:")
            for pattern in protected_patterns:
                print(f"      - '{pattern}' in '{relative_str}' → {pattern in relative_str}")

if __name__ == "__main__":
    debug_protection()