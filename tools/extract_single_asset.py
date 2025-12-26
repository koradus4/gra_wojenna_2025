from __future__ import annotations

import argparse
from pathlib import Path

from PIL import Image


def _non_bg_bbox(img: Image.Image, *, bg_rgb: tuple[int, int, int], tol: int) -> tuple[int, int, int, int] | None:
    rgb = img.convert("RGB")
    px = rgb.load()
    w, h = rgb.size

    min_x, min_y = w, h
    max_x, max_y = -1, -1

    br, bg, bb = bg_rgb

    for y in range(h):
        for x in range(w):
            r, g, b = px[x, y]
            if abs(r - br) > tol or abs(g - bg) > tol or abs(b - bb) > tol:
                if x < min_x:
                    min_x = x
                if y < min_y:
                    min_y = y
                if x > max_x:
                    max_x = x
                if y > max_y:
                    max_y = y

    if max_x < 0:
        return None

    return (min_x, min_y, max_x + 1, max_y + 1)


def _tighten(img: Image.Image, *, pad: int, bg_rgb: tuple[int, int, int], tol: int) -> Image.Image:
    bbox = _non_bg_bbox(img, bg_rgb=bg_rgb, tol=tol)
    if bbox is None:
        return img

    left, top, right, bottom = bbox
    left = max(0, left - pad)
    top = max(0, top - pad)
    right = min(img.size[0], right + pad)
    bottom = min(img.size[1], bottom + pad)
    return img.crop((left, top, right, bottom))


def _make_bg_transparent(img: Image.Image, *, bg_rgb: tuple[int, int, int], tol: int) -> Image.Image:
    rgba = img.convert("RGBA")
    data = rgba.getdata()
    br, bg, bb = bg_rgb

    new_data = []
    for r, g, b, a in data:
        if abs(r - br) <= tol and abs(g - bg) <= tol and abs(b - bb) <= tol:
            new_data.append((r, g, b, 0))
        else:
            new_data.append((r, g, b, 255))

    rgba.putdata(new_data)
    return rgba


def main() -> int:
    parser = argparse.ArgumentParser(description="Auto-crop assetu i zamiana tła na przezroczystość (PNG alfa)")
    parser.add_argument("--input", required=True, help="Ścieżka do pliku wejściowego")
    parser.add_argument("--out", required=True, help="Ścieżka do pliku wyjściowego")
    parser.add_argument("--pad", type=int, default=6, help="Margines (px) dookoła po crop")
    parser.add_argument("--tol", type=int, default=18, help="Tolerancja dopasowania tła")
    parser.add_argument("--bg", default="248,235,209", help="Kolor tła jako R,G,B")
    args = parser.parse_args()

    bg_parts = [p.strip() for p in args.bg.split(",") if p.strip()]
    if len(bg_parts) != 3:
        raise SystemExit("--bg musi mieć format R,G,B")
    bg_rgb = (int(bg_parts[0]), int(bg_parts[1]), int(bg_parts[2]))

    input_path = Path(args.input)
    out_path = Path(args.out)
    out_path.parent.mkdir(parents=True, exist_ok=True)

    img = Image.open(input_path)
    img = _tighten(img, pad=args.pad, bg_rgb=bg_rgb, tol=args.tol)
    img = _make_bg_transparent(img, bg_rgb=bg_rgb, tol=args.tol)

    img.save(out_path)
    print(f"OK: {out_path} ({img.size[0]}x{img.size[1]})")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
