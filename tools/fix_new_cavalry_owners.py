#!/usr/bin/env python3
"""
Fix owner format for newly purchased cavalry tokens
Nowe zetony kawalerii mają format owner "3" zamiast "3 (Polska)"
Ten skrypt naprawia format dla aktualnie wdrożonych żetonów
"""

import json
import os

def fix_new_cavalry_owners():
    index_path = "assets/tokens/index.json"
    
    if not os.path.exists(index_path):
        print(f"❌ Plik {index_path} nie istnieje!")
        return False
    
    print("📋 Wczytywanie index.json...")
    with open(index_path, 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    # Znajdź nowe żetony kawalerii z błędnym formatem owner
    cavalry_tokens_to_fix = []
    for token in data:
        if (token.get('unitType') == 'K' and 
            token.get('nation') == 'Polska' and
            token.get('owner') == '3' and 
            'nowy_K_Pluton__3_Polska Kawaleria' in token.get('id', '')):
            cavalry_tokens_to_fix.append(token)
    
    if not cavalry_tokens_to_fix:
        print("✅ Brak nowych żetonów kawalerii do naprawy!")
        return True
    
    print(f"🔧 Znaleziono {len(cavalry_tokens_to_fix)} nowych żetonów kawalerii do naprawy:")
    
    # Napraw format owner
    changes_made = 0
    for token in cavalry_tokens_to_fix:
        old_owner = token.get('owner')
        token['owner'] = '3 (Polska)'
        print(f"   ✅ {token['id'][:50]}... owner: '{old_owner}' -> '{token['owner']}'")
        changes_made += 1
        
        # Zaktualizuj także odpowiadający plik żetonu
        token_file = token.get('image', '').replace('.png', '.json').replace('assets/tokens/aktualne/', 'assets/tokens/aktualne/')
        if token_file and os.path.exists(token_file):
            try:
                with open(token_file, 'r', encoding='utf-8') as f:
                    token_data = json.load(f)
                
                if token_data.get('owner') == old_owner:
                    token_data['owner'] = '3 (Polska)'
                    with open(token_file, 'w', encoding='utf-8') as f:
                        json.dump(token_data, f, indent=2, ensure_ascii=False)
                    print(f"      📄 Zaktualizowano plik: {token_file}")
            except Exception as e:
                print(f"      ⚠️ Błąd przy aktualizacji pliku {token_file}: {e}")
    
    if changes_made > 0:
        # Zapisz zaktualizowany index.json
        with open(index_path, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
        print(f"✅ Zapisano {changes_made} poprawek do index.json")
        return True
    else:
        print("ℹ️ Brak zmian do zapisania")
        return False

if __name__ == "__main__":
    print("🚀 Naprawianie owner format dla nowych żetonów kawalerii...")
    success = fix_new_cavalry_owners()
    
    if success:
        print("🎉 Proces naprawy zakończony pomyślnie!")
    else:
        print("❌ Wystąpił błąd podczas naprawy!")
