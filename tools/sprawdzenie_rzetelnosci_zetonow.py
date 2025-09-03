#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Sprawdzenie spójności żetonów - czy wszystkie żetony mają pliki PNG i definicje
"""

import os
import json
from pathlib import Path

def sprawdz_zetony(katalog_assetow):
    """Sprawdza spójność żetonów między plikami JSON a obrazkami PNG"""
    bledy = []
    
    # Wczytaj index.json
    sciezka_index = katalog_assetow / "tokens/index.json"
    if not sciezka_index.exists():
        print(f"Brak pliku: {sciezka_index}")
        return
        
    with open(sciezka_index, encoding="utf-8") as f:
        index = json.load(f)
    
    # Wczytaj start_tokens.json
    sciezka_start = katalog_assetow / "start_tokens.json"
    if not sciezka_start.exists():
        print(f"Brak pliku: {sciezka_start}")
        return
        
    with open(sciezka_start, encoding="utf-8") as f:
        zetony_startowe = json.load(f)
    
    # Sprawdź każdy żeton ze start_tokens
    for zeton in zetony_startowe:
        zeton_id = zeton["id"]
        
        # Szukaj w index.json
        dane_zetona = None
        if isinstance(index, dict):
            dane_zetona = index.get(zeton_id)
        else:
            for z in index:
                if z.get("id") == zeton_id:
                    dane_zetona = z
                    break
        
        if not dane_zetona:
            bledy.append(f"Brak definicji {zeton_id} w index.json")
            continue
        
        # Sprawdź ścieżkę do obrazka
        sciezka_obrazka = dane_zetona.get("image")
        if not sciezka_obrazka:
            # Spróbuj domyślnej ścieżki
            nacja = dane_zetona.get("nation", "")
            sciezka_obrazka = f"assets/tokens/{nacja}/{zeton_id}/token.png"
        
        plik_obrazka = Path(sciezka_obrazka)
        if not plik_obrazka.is_absolute():
            plik_obrazka = katalog_assetow.parent / sciezka_obrazka
        
        if not plik_obrazka.exists():
            bledy.append(f"Brak pliku PNG: {plik_obrazka}")
    
    # Podsumowanie
    if bledy:
        print("\n❌ BŁĘDY SPÓJNOŚCI ŻETONÓW:")
        for blad in bledy:
            print("-", blad)
        print(f"\n📊 Znaleziono {len(bledy)} błędów")
    else:
        print("✅ Wszystkie żetony startowe mają pliki PNG i definicje w index.json!")
        print(f"📊 Sprawdzono {len(zetony_startowe)} żetonów - wszystkie OK")

if __name__ == "__main__":
    katalog_assetow = Path(__file__).parent.parent / "assets"
    print("🔍 SPRAWDZANIE SPÓJNOŚCI ŻETONÓW")
    print("=" * 40)
    sprawdz_zetony(katalog_assetow)
