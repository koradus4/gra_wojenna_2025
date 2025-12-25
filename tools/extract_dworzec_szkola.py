from __future__ import annotations

import argparse
from pathlib import Path

from PIL import Image


def _non_black_bbox(img: Image.Image, *, threshold: int = 12) -> tuple[int, int, int, int] | None:
    """Return bounding box of pixels that are not near-black."""
    if img.mode != "RGB":
        img = img.convert("RGB")

    px = img.load()
    w, h = img.size

    min_x, min_y = w, h
    max_x, max_y = -1, -1

    for y in range(h):
        for x in range(w):
            r, g, b = px[x, y]
            if r > threshold or g > threshold or b > threshold:
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

    # PIL crop uses (left, upper, right, lower) where right/lower are exclusive
    return (min_x, min_y, max_x + 1, max_y + 1)


def _crop_quadrant(img: Image.Image, quadrant: str) -> Image.Image:
    w, h = img.size
    half_w, half_h = w // 2, h // 2

    if quadrant == "top_left":
        box = (0, 0, half_w, half_h)
    elif quadrant == "top_right":
        box = (half_w, 0, w, half_h)
    elif quadrant == "bottom_left":
        box = (0, half_h, half_w, h)
    elif quadrant == "bottom_right":
        box = (half_w, half_h, w, h)
    else:
        raise ValueError(f"Unknown quadrant: {quadrant}")

    return img.crop(box)


def _add_transparency_by_black(bg: Image.Image, *, threshold: int = 10) -> Image.Image:
    """Convert near-black background to transparency."""
    rgba = bg.convert("RGBA")
    data = rgba.getdata()

    new_data = []
    for r, g, b, a in data:
        if r <= threshold and g <= threshold and b <= threshold:
            new_data.append((r, g, b, 0))
        else:
            new_data.append((r, g, b, 255))

    rgba.putdata(new_data)
    return rgba


def _tighten(img: Image.Image, *, pad: int = 6) -> Image.Image:
    bbox = _non_black_bbox(img)
    if bbox is None:
        return img

    left, top, right, bottom = bbox
    left = max(0, left - pad)
    top = max(0, top - pad)
    right = min(img.size[0], right + pad)
    bottom = min(img.size[1], bottom + pad)
    return img.crop((left, top, right, bottom))


def main() -> int:
    parser = argparse.ArgumentParser(description="Wytnij dworzec i szkołę z pliku szkoladzweorzec.png")
    parser.add_argument(
        "--input",
        default=str(Path("edytory") / "wzory_pixelart" / "szkoladzweorzec.png"),
        help="Ścieżka do pliku wejściowego",
    )
    parser.add_argument(
        "--outdir",
        default=str(Path("edytory") / "wzory_pixelart"),
        help="Folder wyjściowy",
    )
    args = parser.parse_args()

    input_path = Path(args.input)
    outdir = Path(args.outdir)
    outdir.mkdir(parents=True, exist_ok=True)

    img = Image.open(input_path)

    # Zakładamy układ 2x2: dworzec (prawy-górny), szkoła (lewy-dolny)
    dworzec = _tighten(_crop_quadrant(img, "top_right"))
    szkola = _tighten(_crop_quadrant(img, "bottom_left"))

    dworzec = _add_transparency_by_black(dworzec)
    szkola = _add_transparency_by_black(szkola)

    dworzec_out = outdir / "dworzec.png"
    szkola_out = outdir / "szkola.png"

    dworzec.save(dworzec_out)
    szkola.save(szkola_out)

    print(f"OK: zapisano {dworzec_out} ({dworzec.size[0]}x{dworzec.size[1]})")
    print(f"OK: zapisano {szkola_out} ({szkola.size[0]}x{szkola.size[1]})")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
