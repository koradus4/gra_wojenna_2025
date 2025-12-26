from pathlib import Path
import json

# Sprawdź najnowszy żeton kawalerii
token_path = Path('assets/tokens/aktualne/nowy_K_Pluton__5_Niemcy Kawaleria Pluton ____20250909230214.json')
if token_path.exists():
    with open(token_path, 'r', encoding='utf-8') as f:
        token_data = json.load(f)
    print('=== NAJNOWSZY ZETON KAWALERII ===')
    print(f'ID: {token_data.get("id", "brak")}')
    print(f'Owner: {token_data.get("owner", "brak")}')
    print(f'Nation: {token_data.get("nation", "brak")}')
    print(f'UnitType: {token_data.get("unitType", "brak")}')
    print('')
    
    # Sprawdź czy to jest z AI czy Human
    if 'nowy_K_Pluton__5_' in token_data.get('id', ''):
        print('To jest zeton dla dowodcy 5 (Niemcy)')
        print('Powinien miec owner: "5 (Niemcy)"')
        print(f'Ma owner: "{token_data.get("owner", "brak")}"')
        if token_data.get('owner') == '5':
            print('❌ BLEDNY FORMAT OWNER!')
        else:
            print('✅ POPRAWNY FORMAT')
            
    # Sprawdź czy jest w start_tokens.json
    start_path = Path('assets/start_tokens.json')
    if start_path.exists():
        with open(start_path, 'r', encoding='utf-8') as f:
            start_tokens = json.load(f)
        
        token_id = token_data.get('id')
        has_position = any(t['id'] == token_id for t in start_tokens)
        print(f'W start_tokens.json: {"✅" if has_position else "❌"}')
        
    # Sprawdź czy jest w index.json
    index_path = Path('assets/tokens/index.json')
    if index_path.exists():
        with open(index_path, 'r', encoding='utf-8') as f:
            index_tokens = json.load(f)
        
        token_id = token_data.get('id')
        has_index = any(t.get('id') == token_id for t in index_tokens)
        print(f'W index.json: {"✅" if has_index else "❌"}')
        
else:
    print('Nie znaleziono najnowszego zetonu')
