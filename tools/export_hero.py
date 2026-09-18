"""Crop the transparent Blender render and export the homepage image.

Run after tools/render_hero.py --final. Requires Pillow.
"""
from pathlib import Path
import sys

from PIL import Image

ROOT = Path(__file__).resolve().parents[1]
source = ROOT / '.render-work' / ('hibiscus-final-gpu.png' if '--gpu' in sys.argv else 'hibiscus-final.png')
target = ROOT / 'assets' / 'web' / 'hero-hibiscus-3d'
image = Image.open(source).convert('RGBA')
bounds = image.getchannel('A').getbbox()
if bounds is None:
    raise ValueError('The Blender render is empty')
left, top, right, bottom = bounds
image = image.crop((max(0, left - 6), max(0, top - 6),
                    min(image.width, right + 6), min(image.height, bottom + 6)))
image.save(target.with_suffix('.png'), optimize=True)
image.save(target.with_suffix('.webp'), quality=92, method=6)
print(f'{image.width} x {image.height}; WebP: {target.with_suffix(".webp").stat().st_size:,} bytes')
