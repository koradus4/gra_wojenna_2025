import json
from pathlib import Path

print("=== SPRAWDZENIE ZETONOW NOWY_ W SYSTEMIE ===")

# Sprawdź index.json
index_path = Path('assets/tokens/index.json')
if index_path.exists():
    with open(index_path, 'r', encoding='utf-8') as f:
        index_data = json.load(f)
    nowy_in_index = [t for t in index_data if t.get('id', '').startswith('nowy_')]
    print(f'Zetony nowy_* w index.json: {len(nowy_in_index)}')
    for t in nowy_in_index[:3]:
        print(f'  - {t["id"]}')
else:
    print('Brak index.json')

# Sprawdź start_tokens.json
start_path = Path('assets/start_tokens.json')
if start_path.exists():
    with open(start_path, 'r', encoding='utf-8') as f:
        start_data = json.load(f)
    nowy_in_start = [t for t in start_data if t.get('id', '').startswith('nowy_')]
    print(f'Zetony nowy_* w start_tokens.json: {len(nowy_in_start)}')
    for t in nowy_in_start[:3]:
        print(f'  - {t["id"]}')
else:
    print('Brak start_tokens.json')

# Sprawdź aktualne/ folder
aktualne_dir = Path('assets/tokens/aktualne')
if aktualne_dir.exists():
    nowy_files = list(aktualne_dir.glob('nowy_*.json'))
    print(f'Pliki nowy_*.json w aktualne/: {len(nowy_files)}')
    for f in nowy_files[:3]:
        print(f'  - {f.name}')
else:
    print('Brak folderu aktualne/')
