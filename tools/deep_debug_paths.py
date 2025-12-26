#!/usr/bin/env python3
"""
GŁĘBOKI DEBUG ŚCIEŻEK - sprawdza jak wyglądają ścieżki w str()
"""

from pathlib import Path

def deep_debug():
    """Głęboki debug konwersji ścieżek"""
    
    logs_dir = Path("c:/Users/klif/OneDrive/Pulpit/gra wojenna 17082025/logs")
    
    # Wzorce ochrony
    protected_patterns = [
        "analysis/ml_ready",
        "analysis/raporty", 
        "analysis/statystyki",
        "vp_intelligence/archives"
    ]
    
    # Znajdź pliki w analysis
    analysis_files = list(logs_dir.rglob("analysis/**/*.json"))
    
    print("🔬 GŁĘBOKI DEBUG ŚCIEŻEK")
    print("=" * 50)
    
    for i, file_path in enumerate(analysis_files[:6]):  
        print(f"\n📁 PLIK {i+1}: {file_path.name}")
        
        # Różne sposoby reprezentacji ścieżki
        print(f"   📍 file_path: {file_path}")
        print(f"   📍 str(file_path): {str(file_path)}")
        relative = file_path.relative_to(logs_dir)
        print(f"   📍 relative_to_logs: {relative}")
        print(f"   📍 str(relative): {str(relative)}")
        relative_unix = str(relative).replace("\\", "/")
        print(f"   📍 relative_unix: {relative_unix}")
        
        # Testuj wzorce na różnych reprezentacjach
        print("   🔍 TESTOWANIE WZORCÓW:")
        for pattern in protected_patterns:
            in_str_file = pattern in str(file_path)
            in_relative = pattern in str(relative)
            in_unix = pattern in relative_unix
            
            print(f"      - '{pattern}' in str(file_path) → {in_str_file}")
            print(f"      - '{pattern}' in str(relative) → {in_relative}")  
            print(f"      - '{pattern}' in relative_unix → {in_unix}")
            
            if in_str_file or in_relative or in_unix:
                print(f"      ✅ PASUJE DO: {pattern}")
                break
        else:
            print(f"      ❌ NIE PASUJE DO ŻADNEGO WZORCA")

if __name__ == "__main__":
    deep_debug()