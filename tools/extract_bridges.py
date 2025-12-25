from __future__ import annotations

import argparse
from pathlib import Path

from PIL import Image


def _non_bg_bbox(img: Image.Image, *, bg_rgb: tuple[int, int, int] = (248, 235, 209), tol: int = 18) -> tuple[int, int, int, int] | None:
    """BBox of pixels that differ from background color by more than tol."""
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


def _crop_half(img: Image.Image, which: str) -> Image.Image:
    w, h = img.size
    mid = w // 2
    if which == "left":
        return img.crop((0, 0, mid, h))
    if which == "right":
        return img.crop((mid, 0, w, h))
    raise ValueError(which)


def _make_bg_transparent(img: Image.Image, *, bg_rgb: tuple[int, int, int] = (248, 235, 209), tol: int = 18) -> Image.Image:
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


def _tighten(img: Image.Image, *, pad: int = 6, bg_rgb: tuple[int, int, int] = (248, 235, 209), tol: int = 18) -> Image.Image:
    bbox = _non_bg_bbox(img, bg_rgb=bg_rgb, tol=tol)
    if bbox is None:
        return img

    left, top, right, bottom = bbox
    left = max(0, left - pad)
    top = max(0, top - pad)
    right = min(img.size[0], right + pad)
    bottom = min(img.size[1], bottom + pad)
    return img.crop((left, top, right, bottom))


def main() -> int:
    parser = argparse.ArgumentParser(description="Wytnij dwa mosty (lewy/prawy) z obrazka i zapisz jako PNG z alfa.")
    parser.add_argument(
        "--input",
        default=str(Path("edytory") / "wzory_pixelart" / "mostystalowomurowane.png"),
        help="Ścieżka do obrazka wejściowego",
    )
    parser.add_argument(
        "--outdir",
        default=str(Path("assets") / "terrain" / "presets" / "custom"),
        help="Folder wyjściowy",
    )
    parser.add_argument("--prefix", default="most_stalowo_murowany", help="Prefiks nazw plików wyjściowych")
    args = parser.parse_args()

    input_path = Path(args.input)
    outdir = Path(args.outdir)
    outdir.mkdir(parents=True, exist_ok=True)

    img = Image.open(input_path)

    left = _tighten(_crop_half(img, "left"))
    right = _tighten(_crop_half(img, "right"))

    left = _make_bg_transparent(left)
    right = _make_bg_transparent(right)

    left_out = outdir / f"{args.prefix}_lewy.png"
    right_out = outdir / f"{args.prefix}_prawy.png"

    left.save(left_out)
    right.save(right_out)

    print(f"OK: {left_out} ({left.size[0]}x{left.size[1]})")
    print(f"OK: {right_out} ({right.size[0]}x{right.size[1]})")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
