#!/usr/bin/env python3
"""
Skrypt naprawiający owner żetonów kawalerii w index.json
"""

import json

def fix_cavalry_owners():
    """Naprawia owner żetonów kawalerii w index.json"""
    
    print("=== NAPRAWA OWNER ŻETONÓW KAWALERII ===")
    
    # Wczytaj index.json
    with open('assets/tokens/index.json', 'r', encoding='utf-8') as f:
        data = json.load(f)

    changed = 0
    for token in data:
        if 'Kawaleria' in token.get('id', ''):
            old_owner = token.get('owner', '')
            nation = token.get('nation', '')
            
            # Jeśli owner to tylko ID gracza (np. '3'), dodaj nację
            if old_owner and nation and '(' not in old_owner:
                new_owner = f'{old_owner} ({nation})'
                token['owner'] = new_owner
                print(f'Naprawiono: {token["id"]} -> owner: "{old_owner}" -> "{new_owner}"')
                changed += 1

    print(f'\nZmieniono {changed} żetonów kawalerii')

    # Zapisz poprawiony plik
    with open('assets/tokens/index.json', 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=2, ensure_ascii=False)

    print('✅ Zapisano poprawiony index.json')
    return changed

if __name__ == "__main__":
    fix_cavalry_owners()
