#!/usr/bin/env python3
"""Turn camera originals into web-sized derivatives for the PC-building gallery.

The originals are 2.5K-4K stills totalling ~19.5 MB; shipping them as-is would
dwarf the rest of the site, which is about 30 KB. Each photo becomes a WebP at
three widths plus one JPEG fallback, and the script prints the intrinsic size of
the largest derivative so the markup can carry width/height and reserve layout
space before the bytes arrive.

Re-run after adding or replacing a source file:  python3 tools/process_photos.py
"""
from pathlib import Path
import json
import sys

from PIL import Image, ImageOps

ROOT = Path(__file__).resolve().parent.parent
SRC = ROOT / "images" / "_originals"
OUT = ROOT / "images" / "pc"

# Widths emitted for srcset. 1600 is the cap: beyond it the gallery gains
# nothing on any realistic viewport and the files get heavy fast.
WIDTHS = [480, 960, 1600]
WEBP_QUALITY = 80
JPEG_QUALITY = 82


def derive(src: Path) -> dict:
    with Image.open(src) as im:
        im = ImageOps.exif_transpose(im)          # honour camera rotation
        im = im.convert("RGB")
        long_edge = max(im.size)
        sizes = []
        for w in WIDTHS:
            if w > long_edge and sizes:
                continue                          # never upscale past the source
            scale = w / im.width
            size = (w, max(1, round(im.height * scale)))
            resized = im.resize(size, Image.LANCZOS)
            resized.save(OUT / f"{src.stem}-{w}.webp", "WEBP", quality=WEBP_QUALITY, method=6)
            sizes.append((w, size[1]))
        # One JPEG so the markup degrades on anything without WebP.
        fallback_w = sizes[-1][0]
        im.resize((fallback_w, sizes[-1][1]), Image.LANCZOS).save(
            OUT / f"{src.stem}-{fallback_w}.jpg", "JPEG", quality=JPEG_QUALITY, optimize=True, progressive=True
        )
        return {"stem": src.stem, "widths": [w for w, _ in sizes],
                "width": sizes[-1][0], "height": sizes[-1][1]}


def main() -> int:
    if not SRC.is_dir():
        print(f"no source directory at {SRC}", file=sys.stderr)
        return 1
    OUT.mkdir(parents=True, exist_ok=True)
    originals = sorted(p for p in SRC.iterdir() if p.suffix.lower() in {".jpg", ".jpeg", ".png"})
    if not originals:
        print(f"no images in {SRC}", file=sys.stderr)
        return 1

    manifest, before, after = [], 0, 0
    for src in originals:
        before += src.stat().st_size
        info = derive(src)
        manifest.append(info)
        produced = sum(p.stat().st_size for p in OUT.glob(f"{src.stem}-*"))
        after += produced
        print(f"  {src.stem:22s} {info['width']}x{info['height']:<5d} "
              f"{src.stat().st_size/1048576:5.1f} MB -> {produced/1024:6.0f} KB")

    (OUT / "manifest.json").write_text(json.dumps(manifest, indent=1) + "\n")
    print(f"\n  {len(manifest)} photos: {before/1048576:.1f} MB -> {after/1024:.0f} KB "
          f"({after/before:.1%} of original)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
