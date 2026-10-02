"""Shared drawing helpers: theme colors, icons and text outlined from the bundled IBM Plex Sans."""
import json
import os

from fontTools.pens.svgPathPen import SVGPathPen
from fontTools.pens.transformPen import TransformPen
from fontTools.ttLib import TTFont

HERE = os.path.dirname(__file__)
ASSETS = os.path.join(HERE, "..", "assets")
WIDTH = 840

THEMES = {
    "light": {"text": "#1f2328", "muted": "#59636e", "rule": "#d1d9e0", "accent": "#0b7a5c"},
    "dark": {"text": "#f0f6fc", "muted": "#9198a1", "rule": "#3d444d", "accent": "#3fd0a4"},
}

# Simple Icons (CC0) path data on a 24x24 grid, keyed by display name.
with open(os.path.join(HERE, "icons.json"), encoding="utf-8") as f:
    ICONS = json.load(f)

_fonts = {}


def _font(weight):
    if weight not in _fonts:
        font = TTFont(os.path.join(HERE, "fonts", f"IBMPlexSans-{weight}.ttf"))
        _fonts[weight] = (font.getGlyphSet(), font.getBestCmap(), font["hmtx"], font["head"].unitsPerEm)
    return _fonts[weight]


def _num(value):
    return f"{value:.1f}".rstrip("0").rstrip(".")


def measure(s, size, weight="Regular", spacing=0):
    _, cmap, hmtx, upm = _font(weight)
    return sum(hmtx[cmap.get(ord(c), ".notdef")][0] * size / upm + spacing for c in s)


def text(x, y, s, size, fill, weight="Regular", spacing=0, anchor="start"):
    """Outline `s` as one path so it renders the same everywhere; `y` is the baseline."""
    glyphs, cmap, hmtx, upm = _font(weight)
    scale = size / upm
    if anchor == "end":
        x -= measure(s, size, weight, spacing) - spacing
    pen = SVGPathPen(glyphs, ntos=_num)
    for c in s:
        name = cmap.get(ord(c), ".notdef")
        glyphs[name].draw(TransformPen(pen, (scale, 0, 0, -scale, x, y)))
        x += hmtx[name][0] * scale + spacing
    return f'<path d="{pen.getCommands()}" fill="{fill}"/>'


def label(x, y, s, theme, anchor="start"):
    """Small caps section label; pass `s` already uppercased."""
    return text(x, y, s, 11.5, theme["muted"], "Medium", 1.3, anchor)


def icon(x, y, name, fill, size=18):
    """Icon whose bottom edge sits just under the text baseline `y`."""
    if name in ICONS:
        return (f'<svg x="{x}" y="{y - size + 3}" width="{size}" height="{size}" viewBox="0 0 24 24">'
                f'<path d="{ICONS[name]}" fill="{fill}"/></svg>')
    return f'<rect x="{x + 3}" y="{y - 12}" width="12" height="12" rx="2" fill="{fill}"/>'


def write(name, aria, render):
    """Write assets/{name}-{light,dark}.svg; `render(theme)` returns (parts, height)."""
    os.makedirs(ASSETS, exist_ok=True)
    for mode, theme in THEMES.items():
        parts, height = render(theme)
        head = (f'<svg xmlns="http://www.w3.org/2000/svg" width="{WIDTH}" height="{height}" '
                f'viewBox="0 0 {WIDTH} {height}" role="img" aria-label="{aria}">')
        with open(os.path.join(ASSETS, f"{name}-{mode}.svg"), "w", encoding="utf-8") as f:
            f.write("\n".join([head, *parts, "</svg>"]) + "\n")
