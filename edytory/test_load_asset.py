import sys
sys.path.insert(0, r"C:\Users\klif\OneDrive\Pulpit\gra wojenna 17082025\edytory")

from generate_forest_hex_tile import _load_tree_asset
from pathlib import Path

json_path = Path(r"C:\Users\klif\OneDrive\Pulpit\gra wojenna 17082025\assets\terrain\presets\user_assets\forest\drzewo_iglaste_3.json")
tree_img, hotspot, meta = _load_tree_asset(json_path, 64)

pixels = tree_img.load()
count = sum(1 for y in range(tree_img.height) for x in range(tree_img.width) if len(pixels[x, y]) >= 4 and pixels[x, y][3] > 10)

print(f"Po _load_tree_asset:")
print(f"  Rozmiar: {tree_img.width}x{tree_img.height}")
print(f"  Hotspot: {hotspot}")
print(f"  Nieprzezroczystych pikseli: {count} / {tree_img.width * tree_img.height}")
