#!/usr/bin/env python3
"""
Builds data/web/css/themes/neuraal-bootstrap.css from the stock lumen Bootstrap
theme by recolouring the lumen accent family (#158cba) to the Neuraal navy
(#061649), keeping every shade/tint relationship intact.

The result is a brand-new file, so `update.sh` (which merges with -X theirs)
can never overwrite it. Activate it with $UI_THEME = 'neuraal' in
data/web/inc/vars.local.inc.php.

Run from the repository root:
  python3 helper-scripts/neuraal-branding/build_theme.py
"""

import colorsys
import os
import re

REPO = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
THEMES = os.path.join(REPO, "data", "web", "css", "themes")
SRC = os.path.join(THEMES, "lumen-bootstrap.css")
DST = os.path.join(THEMES, "neuraal-bootstrap.css")

LUMEN = (0x15, 0x8C, 0xBA)    # lumen accent  -> hue ~197deg, lightness ~41%
NEURAAL = (0x06, 0x16, 0x49)  # Neuraal navy

HUE_RANGE = (175, 220)        # hues counted as "the lumen accent family"
MIN_SATURATION = 0.20         # above Bootstrap's near-neutral grey ramp (~0.14)


def to_hsl(rgb):
    h, l, s = colorsys.rgb_to_hls(*[c / 255.0 for c in rgb])
    return h * 360.0, s, l


def mix(color, target, ratio):
    return tuple(round(c + (t - c) * ratio) for c, t in zip(color, target))


ANCHOR_L = to_hsl(LUMEN)[2]   # lightness of the lumen accent


def remap(rgb):
    """Map a lumen accent shade/tint onto the equivalent point of the Neuraal ramp.

    The Neuraal ramp runs black -> #061649 -> white and is indexed by the
    lightness of the original colour, so every shade/tint keeps its role
    (hover states stay darker, focus rings and backgrounds stay lighter).
    """
    hue, sat, light = to_hsl(rgb)
    if sat < MIN_SATURATION or not (HUE_RANGE[0] <= hue <= HUE_RANGE[1]):
        return None
    if light <= ANCHOR_L:
        return mix((0, 0, 0), NEURAAL, light / ANCHOR_L)
    return mix(NEURAAL, (255, 255, 255), (light - ANCHOR_L) / (1.0 - ANCHOR_L))


def main():
    css = open(SRC, encoding="utf-8").read()
    remapped = {}

    def hex_sub(match):
        value = match.group(0)
        digits = value[1:]
        if len(digits) == 3:
            digits = "".join(d * 2 for d in digits)
        rgb = tuple(int(digits[i:i + 2], 16) for i in (0, 2, 4))
        new = remap(rgb)
        if new is None:
            return value
        out = "#%02x%02x%02x" % new
        remapped[value.lower()] = out
        return out

    css = re.sub(r"#[0-9a-fA-F]{6}\b|#[0-9a-fA-F]{3}\b", hex_sub, css)

    def rgb_sub(match):
        prefix = match.group(1)
        rgb = tuple(int(match.group(i)) for i in (2, 3, 4))
        new = remap(rgb)
        if new is None:
            return match.group(0)
        remapped["rgb(%d, %d, %d)" % rgb] = "rgb(%d, %d, %d)" % new
        return "%s%d, %d, %d" % (prefix, new[0], new[1], new[2])

    # only touch rgb()/rgba() functions and Bootstrap's --bs-*-rgb custom properties
    css = re.sub(r"(rgba?\(|--bs-[a-z0-9-]+-rgb:\s*)(\d{1,3}),\s*(\d{1,3}),\s*(\d{1,3})",
                 rgb_sub, css)

    header = ("/* Neuraal brand theme - generated from lumen-bootstrap.css by\n"
              "   helper-scripts/neuraal-branding/build_theme.py. Do not edit by hand. */\n")
    with open(DST, "w", encoding="utf-8", newline="\n") as fh:
        fh.write(header + css)

    print("wrote", os.path.relpath(DST, REPO))
    for old, new in sorted(remapped.items()):
        print("  %-22s -> %s" % (old, new))


if __name__ == "__main__":
    main()
