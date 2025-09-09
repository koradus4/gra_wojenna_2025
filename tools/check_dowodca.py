import json
from pathlib import Path

print('=== SPRAWDZENIE ZETONOW DOWODCY ===')

# 1. start_tokens.json
start_path = Path('assets/start_tokens.json')
if start_path.exists():
    with open(start_path, 'r', encoding='utf-8') as f:
        start_tokens = json.load(f)
    print(f'start_tokens.json: {len(start_tokens)} zetonow')
    
    dowodca_tokens = [t for t in start_tokens if 'D_' in t['id'] or 'Dowodztwo' in t['id']]
    print(f'Zetony dowodcy w start_tokens: {len(dowodca_tokens)}')
    for t in dowodca_tokens:
        print(f'  - {t["id"]}')
else:
    print('Brak start_tokens.json')

# 2. index.json  
index_path = Path('assets/tokens/index.json')
if index_path.exists():
    with open(index_path, 'r', encoding='utf-8') as f:
        index_tokens = json.load(f)
    print(f'\nindex.json: {len(index_tokens)} zetonow')
    
    dowodca_in_index = [t for t in index_tokens if t.get('unitType') == 'D']
    print(f'Zetony dowodcy w index: {len(dowodca_in_index)}')
    for t in dowodca_in_index:
        print(f'  - {t["id"]} owner: {t.get("owner", "brak")}')
else:
    print('Brak index.json')

# 3. aktualne/ folder
aktualne_dir = Path('assets/tokens/aktualne')  
if aktualne_dir.exists():
    dowodca_files = list(aktualne_dir.glob('*D_*.json'))
    print(f'\naktualne/ folder: {len(dowodca_files)} plikow dowodcy')
    for f in dowodca_files:
        with open(f, 'r', encoding='utf-8') as file:
            data = json.load(file)
        print(f'  - {data["id"]} owner: {data.get("owner", "brak")}')
else:
    print('Brak folderu aktualne/')

# 4. Sprawdź czy może gra ładuje z pamięci lub cache
print('\n=== DODATKOWE SPRAWDZENIA ===')

# Wszystkie żetony z id zawierającym "6"
print('Wszystkie żetony z "6" w start_tokens:')
if start_path.exists():
    with open(start_path, 'r', encoding='utf-8') as f:
        start_tokens = json.load(f)
    tokens_6 = [t for t in start_tokens if '6' in t['id']]
    print(f'Znaleziono {len(tokens_6)} żetonów:')
    for t in tokens_6[:10]:  # pierwszych 10
        print(f'  - {t["id"]}')
