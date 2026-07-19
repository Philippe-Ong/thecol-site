"""Génère des variantes WebP à partir des images de assets/web/.

Stratégie : pour chaque image "lourde" (≥ ~100 KB) référencée par les 10 HTML
statiques, on génère deux tailles redimensionnées en WebP (qualité 82).

Tailles choisies :
  - <width>-sm.webp   → env. 480 px de large (mobile + vignettes)
  - <width>-lg.webp   → env. 960 px de large (desktop 1x, mobile retina 2x
                        sur écrans ≤ 480 CSS px)

Les originaux JPEG/PNG dans assets/web/ sont conservés comme fallback
intacts (jamais modifiés). Aucune image n'est générée pour les fichiers
déjà petits (PNG cut-*, icônes, logo-header, photos d'équipe) — le gain
serait marginal et on conserve un repo léger.

Pré-requis : Pillow (PIL). Aucune autre dépendance.
Usage : python tools/build_webp.py [--dry-run]
"""
from __future__ import annotations

import argparse
import os
import sys
from pathlib import Path

Image = None

ROOT = Path(__file__).resolve().parent.parent
WEB = ROOT / "assets" / "web"

# Images « lourdes » à transformer (≥ ~100 KB), en deux tailles.
# Chaque entrée : (nom de base, largeur_small, largeur_large)
TARGETS = [
    # Photos produit (cartes saveurs, vignettes)
    ("produit-hibiscus", 480, 960),
    ("produit-mures", 480, 960),
    ("produit-sureau", 480, 960),
    ("produit-herbes", 480, 960),
    ("produit-poire", 480, 960),
    # Photos de contenu / sections
    ("photo-groupe", 720, 1280),
    ("photo-production", 720, 1280),
    ("photo-poire-groupe", 720, 1280),
    ("photo-caisse", 600, 1100),
    ("photo-herbes-50", 600, 1100),
    ("photo-mures-100", 600, 1100),
    ("photo-gal-hibiscus", 600, 1100),
    ("photo-gal-mures", 600, 1100),
    ("photo-gal-herbes", 600, 1100),
    ("photo-gal-poire", 600, 1100),
]

WEBP_QUALITY = 82


def find_source(base: str) -> Path:
    for ext in (".jpg", ".jpeg", ".png"):
        p = WEB / (base + ext)
        if p.exists():
            return p
    raise FileNotFoundError(f"Aucune source pour {base} dans {WEB}")


def out_path(src: Path, width: int) -> Path:
    return WEB / f"{src.stem}-{width}.webp"


def make_variant(src: Path, width: int, dry: bool) -> tuple[Path, int]:
    dest = out_path(src, width)
    if dry:
        return dest, -1
    if Image is None:
        raise RuntimeError("Pillow requis : pip install pillow")
    with Image.open(src) as im:
        im.load()
        w, h = im.size
        if width >= w:
            # Source plus petite que la cible : on garde tel quel en WebP
            new_w, new_h = w, h
        else:
            new_w = width
            new_h = round(h * width / w)
        # Mode : les PNG avec alpha restent RGBA, les JPEG en RGB
        if im.mode in ("RGBA", "LA") or (im.mode == "P" and "transparency" in im.info):
            im = im.convert("RGBA")
        else:
            im = im.convert("RGB")
        im = im.resize((new_w, new_h), Image.LANCZOS)
        im.save(dest, "WEBP", quality=WEBP_QUALITY, method=6)
    return dest, dest.stat().st_size


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--dry-run", action="store_true", help="N'écrit rien, affiche le plan")
    args = ap.parse_args()

    # Le mode aperçu ne lit ni ne transforme les pixels : il reste utilisable
    # dans un environnement de validation qui ne possède pas Pillow.
    global Image
    if not args.dry_run:
        try:
            from PIL import Image as PillowImage
        except ImportError:
            sys.stderr.write("Pillow requis pour générer les WebP : pip install pillow\n")
            return 2
        Image = PillowImage

    rows = []
    for base, sm, lg in TARGETS:
        src = find_source(base)
        src_size = src.stat().st_size
        for w in (sm, lg):
            dest, new_size = make_variant(src, w, args.dry_run)
            rows.append((src.name, w, dest.name, src_size, new_size))

    if args.dry_run:
        print("# dry-run : aucune image écrite\n")
    print(f"{'source':28s} {'w':>5s}  {'webp':28s} {'orig KB':>9s}  {'new KB':>9s}  {'gain':>7s}")
    total_orig = total_new = 0
    for src_name, w, dest_name, orig, new in rows:
        new_kb = new / 1024 if new >= 0 else float("nan")
        orig_kb = orig / 1024
        gain = (1 - new / orig) * 100 if new > 0 else 0.0
        total_orig += orig
        total_new += max(new, 0)
        print(f"{src_name:28s} {w:>5d}  {dest_name:28s} {orig_kb:>9.1f}  {new_kb:>9.1f}  {gain:>6.1f}%")
    print("-" * 88)
    if not args.dry_run and total_new > 0:
        gain = (1 - total_new / total_orig) * 100
        print(f"{'TOTAL':28s} {'':>5s}  {'':28s} {total_orig/1024:>9.1f}  {total_new/1024:>9.1f}  {gain:>6.1f}%")
    return 0


if __name__ == "__main__":
    sys.exit(main())
