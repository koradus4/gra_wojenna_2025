from PIL import Image
from pathlib import Path

forest_dir = Path(r"C:\Users\klif\OneDrive\Pulpit\gra wojenna 17082025\assets\terrain\hex_painted\forest_tool")
files = sorted(forest_dir.glob("forest_*.png"), key=lambda p: p.stat().st_mtime)[-5:]

for filepath in files:
    img = Image.open(filepath)
    pixels = img.load()
    count = sum(1 for y in range(img.height) for x in range(img.width) if len(pixels[x, y]) >= 4 and pixels[x, y][3] > 10)
    coverage = 100 * count / (img.width * img.height)
    print(f"{filepath.name}: {count} px = {coverage:.2f}%")
