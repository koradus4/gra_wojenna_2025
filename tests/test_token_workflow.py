#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Test nowego workflow żetonów w Map Editor
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(__file__)))

from pathlib import Path
import json

# Ścieżki testowe
PROJECT_ROOT = Path(__file__).parent.parent
ASSETS_DIR = PROJECT_ROOT / "assets"
TOKENS_INDEX = ASSETS_DIR / "tokens" / "index.json"

def test_token_index():
    """Test ładowania indeksu żetonów"""
    print("🧪 Test 1: Ładowanie indeksu żetonów")
    
    if not TOKENS_INDEX.exists():
        print("❌ Brak pliku index.json")
        return False
        
    try:
        with open(TOKENS_INDEX, "r", encoding="utf-8") as f:
            tokens = json.load(f)
        
        print(f"✅ Załadowano {len(tokens)} żetonów")
        
        # Sprawdź strukturę pierwszego żetonu
        if tokens:
            first_token = tokens[0]
            required_fields = ["id", "nation", "unitType", "unitSize", "image"]
            missing = [field for field in required_fields if field not in first_token]
            
            if missing:
                print(f"⚠️  Brakuje pól: {missing}")
            else:
                print("✅ Struktura żetonu OK")
                
            print(f"📋 Pierwszy żeton: {first_token['id']} ({first_token.get('nation', 'N/A')})")
        
        return True
        
    except Exception as e:
        print(f"❌ Błąd ładowania: {e}")
        return False

def test_nations():
    """Test dostępnych nacji"""
    print("\n🧪 Test 2: Analiza nacji")
    
    try:
        with open(TOKENS_INDEX, "r", encoding="utf-8") as f:
            tokens = json.load(f)
        
        nations = set(token.get("nation", "Nieznana") for token in tokens)
        print(f"🏳️  Dostępne nacje: {sorted(nations)}")
        
        # Policz żetony per nacja
        nation_counts = {}
        for token in tokens:
            nation = token.get("nation", "Nieznana")
            nation_counts[nation] = nation_counts.get(nation, 0) + 1
        
        for nation, count in sorted(nation_counts.items()):
            print(f"   {nation}: {count} żetonów")
        
        return True
        
    except Exception as e:
        print(f"❌ Błąd: {e}")
        return False

def test_unit_types():
    """Test typów jednostek"""
    print("\n🧪 Test 3: Typy jednostek")
    
    try:
        with open(TOKENS_INDEX, "r", encoding="utf-8") as f:
            tokens = json.load(f)
        
        unit_types = set(token.get("unitType", "N/A") for token in tokens)
        print(f"⚔️  Typy jednostek: {sorted(unit_types)}")
        
        unit_sizes = set(token.get("unitSize", "N/A") for token in tokens)
        print(f"📏 Rozmiary: {sorted(unit_sizes)}")
        
        return True
        
    except Exception as e:
        print(f"❌ Błąd: {e}")
        return False

def test_image_paths():
    """Test ścieżek do obrazów"""
    print("\n🧪 Test 4: Ścieżki obrazów")
    
    try:
        with open(TOKENS_INDEX, "r", encoding="utf-8") as f:
            tokens = json.load(f)
        
        missing_images = []
        valid_images = 0
        
        for token in tokens:
            image_path = token.get("image", "")
            if image_path:
                # Sprawdź czy ścieżka jest względna
                if image_path.startswith("assets/"):
                    full_path = PROJECT_ROOT / image_path
                else:
                    full_path = ASSETS_DIR / image_path
                
                if full_path.exists():
                    valid_images += 1
                else:
                    missing_images.append(image_path)
        
        print(f"✅ Prawidłowe obrazy: {valid_images}")
        if missing_images:
            print(f"❌ Brakujące obrazy: {len(missing_images)}")
            for img in missing_images[:3]:  # Pokaż pierwsze 3
                print(f"   • {img}")
            if len(missing_images) > 3:
                print(f"   • +{len(missing_images)-3} więcej...")
        
        return len(missing_images) == 0
        
    except Exception as e:
        print(f"❌ Błąd: {e}")
        return False

def test_filter_simulation():
    """Test symulacji filtrów"""
    print("\n🧪 Test 5: Symulacja filtrów")
    
    try:
        with open(TOKENS_INDEX, "r", encoding="utf-8") as f:
            tokens = json.load(f)
        
        # Test filtru nacji
        polish_tokens = [t for t in tokens if t.get("nation") == "Polska"]
        german_tokens = [t for t in tokens if t.get("nation") == "Niemcy"]
        
        print(f"🇵🇱 Filtr Polska: {len(polish_tokens)} żetonów")
        print(f"🇩🇪 Filtr Niemcy: {len(german_tokens)} żetonów")
        
        # Test filtru typu
        if polish_tokens:
            infantry = [t for t in polish_tokens if t.get("unitType") == "P"]
            print(f"👥 Polska piechota: {len(infantry)} żetonów")
        
        # Test wyszukiwania
        search_results = [t for t in tokens if "artyl" in t.get("label", "").lower()]
        print(f"🔍 Wyszukiwanie 'artyl': {len(search_results)} wyników")
        
        return True
        
    except Exception as e:
        print(f"❌ Błąd: {e}")
        return False

def main():
    """Główna funkcja testowa"""
    print("🚀 Test nowego workflow żetonów")
    print("=" * 50)
    
    tests = [
        test_token_index,
        test_nations,
        test_unit_types,
        test_image_paths,
        test_filter_simulation
    ]
    
    passed = 0
    total = len(tests)
    
    for test in tests:
        if test():
            passed += 1
    
    print("\n" + "=" * 50)
    print(f"📊 Wynik testów: {passed}/{total} zaliczonych")
    
    if passed == total:
        print("🎉 Wszystkie testy przeszły! Workflow żetonów gotowy do użycia.")
    else:
        print("⚠️  Niektóre testy nie przeszły. Sprawdź powyższe błędy.")
    
    return passed == total

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
