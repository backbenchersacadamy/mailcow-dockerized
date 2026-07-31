#!/usr/bin/env python3
"""
Regenerates the Neuraal UI brand assets used by the mailcow web UI.

Source (already provided for SOGo):
  data/conf/sogo/custom-fulllogo.svg   -> icon mark + "NEURAAL" wordmark

Outputs:
  data/web/img/neuraal-logo.svg        -> horizontal lockup, navy   (light mode)
  data/web/img/neuraal-logo-dark.svg   -> horizontal lockup, white  (dark mode)
  data/web/img/neuraal-mark.svg        -> icon only, navy
  data/web/img/neuraal-mark-dark.svg   -> icon only, white
  data/web/img/neuraal-favicon.svg     -> mark on a navy rounded square (favicon master)

data/web/favicon.png is rasterised from neuraal-favicon.svg at 128x128.

Run from the repository root:  python3 helper-scripts/neuraal-branding/generate_assets.py
"""

import os
import re
import xml.etree.ElementTree as ET

REPO = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
SRC_SVG = os.path.join(REPO, "data", "conf", "sogo", "custom-fulllogo.svg")
IMG_DIR = os.path.join(REPO, "data", "web", "img")

BRAND = "#061649"
BRAND_ON_DARK = "#FFFFFF"

# Bounding boxes of the source artwork, recomputed at runtime by source_geometry().
MARK = (3004.0, 4846.0, 5147.0, 6148.0)   # icon mark
WORD = (2071.0, 6443.0, 6197.0, 6774.0)   # "NEURAAL" wordmark

WORD_SCALE = 1.25   # wordmark cap height relative to source
GAP = 350.0         # space between mark and wordmark


NUM_RE = re.compile(r"[-+]?(?:\d*\.\d+|\d+)(?:[eE][-+]?\d+)?")
CMD_RE = re.compile(r"([MmLlHhVvCcSsQqTtAaZz])")
ARGC = {"M": 2, "L": 2, "H": 1, "V": 1, "C": 6, "S": 4, "Q": 4, "T": 2, "A": 7, "Z": 0}


def path_points(d):
    """Absolute anchor/control points of a path - a safe superset of its bounding box."""
    tokens = [t for t in CMD_RE.split(d) if t.strip()]
    pts, cx, cy, sx, sy, i, cmd = [], 0.0, 0.0, 0.0, 0.0, 0, None
    while i < len(tokens):
        token = tokens[i]
        if CMD_RE.fullmatch(token):
            cmd = token
            i += 1
            if cmd in "Zz":
                cx, cy = sx, sy
                continue
            nums = [float(n) for n in NUM_RE.findall(tokens[i])] if i < len(tokens) else []
            i += 1
        else:
            nums = [float(n) for n in NUM_RE.findall(token)]
            i += 1
        if cmd is None:
            continue
        up, rel, n, first = cmd.upper(), cmd.islower(), ARGC[cmd.upper()], True
        if n == 0:
            continue
        for k in range(0, len(nums) - n + 1, n):
            a = nums[k:k + n]
            if up == "H":
                cx = cx + a[0] if rel else a[0]
                pts.append((cx, cy))
            elif up == "V":
                cy = cy + a[0] if rel else a[0]
                pts.append((cx, cy))
            elif up == "A":
                cx = cx + a[5] if rel else a[5]
                cy = cy + a[6] if rel else a[6]
                pts.append((cx, cy))
            else:
                coords = [((cx + a[j] if rel else a[j]), (cy + a[j + 1] if rel else a[j + 1]))
                          for j in range(0, n, 2)]
                pts.extend(coords)
                cx, cy = coords[-1]
            if up == "M":
                if first:
                    sx, sy = cx, cy
                cmd, up, n = ("l" if rel else "L"), "L", 2
            first = False
    return pts


def element_bbox(el):
    tag = el.tag.split("}")[-1]
    if tag == "path":
        pts = path_points(el.get("d"))
    else:
        nums = [float(n) for n in NUM_RE.findall(el.get("points"))]
        pts = list(zip(nums[0::2], nums[1::2]))
    xs = [p[0] for p in pts]
    ys = [p[1] for p in pts]
    return min(xs), min(ys), max(xs), max(ys)


def source_geometry():
    """Return (mark_fragment, wordmark_fragment, mark_bbox, word_bbox) from the source logo."""
    ET.register_namespace("", "http://www.w3.org/2000/svg")
    root = ET.parse(SRC_SVG).getroot()
    mark, word, mark_boxes, word_boxes = [], [], [], []
    for el in root.iter():
        tag = el.tag.split("}")[-1]
        if tag == "path" and el.get("d"):
            frag = '<path d="%s"/>' % re.sub(r"\s+", " ", el.get("d")).strip()
        elif tag in ("polygon", "polyline") and el.get("points"):
            frag = '<%s points="%s"/>' % (tag, re.sub(r"\s+", " ", el.get("points")).strip())
        else:
            continue
        box = element_bbox(el)
        # the icon mark is the only shape taller than the "NEURAAL" cap height
        if box[3] - box[1] > 800:
            mark.append(frag)
            mark_boxes.append(box)
        else:
            word.append(frag)
            word_boxes.append(box)
    return ("\n    ".join(mark), "\n    ".join(word),
            _union(mark_boxes), _union(word_boxes))


def _union(boxes):
    return (min(b[0] for b in boxes), min(b[1] for b in boxes),
            max(b[2] for b in boxes), max(b[3] for b in boxes))


def horizontal_lockup(mark, word, color):
    mw = MARK[2] - MARK[0]
    mh = MARK[3] - MARK[1]
    ww = (WORD[2] - WORD[0]) * WORD_SCALE
    wh = (WORD[3] - WORD[1]) * WORD_SCALE
    total_w = mw + GAP + ww
    dy = (mh - wh) / 2.0
    return f'''<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {total_w:.0f} {mh:.0f}" role="img" aria-label="Neuraal">
  <g fill="{color}" fill-rule="evenodd" clip-rule="evenodd">
    <g transform="translate({-MARK[0]:.0f} {-MARK[1]:.0f})">
    {mark}
    </g>
    <g transform="translate({mw + GAP:.0f} {dy:.0f}) scale({WORD_SCALE}) translate({-WORD[0]:.0f} {-WORD[1]:.0f})">
    {word}
    </g>
  </g>
</svg>
'''


def mark_only(mark, color):
    mw = MARK[2] - MARK[0]
    mh = MARK[3] - MARK[1]
    return f'''<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {mw:.0f} {mh:.0f}" role="img" aria-label="Neuraal">
  <g fill="{color}" fill-rule="evenodd" clip-rule="evenodd" transform="translate({-MARK[0]:.0f} {-MARK[1]:.0f})">
    {mark}
  </g>
</svg>
'''


def favicon_svg(mark):
    """Brand mark knocked out of a navy rounded square, 128x128."""
    size, pad = 128.0, 14.0
    mw = MARK[2] - MARK[0]
    mh = MARK[3] - MARK[1]
    scale = (size - 2 * pad) / mw
    dx = pad
    dy = (size - mh * scale) / 2.0
    return f'''<svg xmlns="http://www.w3.org/2000/svg" width="{size:.0f}" height="{size:.0f}" viewBox="0 0 {size:.0f} {size:.0f}" role="img" aria-label="Neuraal">
  <rect width="{size:.0f}" height="{size:.0f}" rx="26" ry="26" fill="{BRAND}"/>
  <g fill="{BRAND_ON_DARK}" fill-rule="evenodd" clip-rule="evenodd" transform="translate({dx:.2f} {dy:.2f}) scale({scale:.6f}) translate({-MARK[0]:.0f} {-MARK[1]:.0f})">
    {mark}
  </g>
</svg>
'''


def main():
    global MARK, WORD
    mark, word, MARK, WORD = source_geometry()
    os.makedirs(IMG_DIR, exist_ok=True)

    outputs = {
        os.path.join(IMG_DIR, "neuraal-logo.svg"): horizontal_lockup(mark, word, BRAND),
        os.path.join(IMG_DIR, "neuraal-logo-dark.svg"): horizontal_lockup(mark, word, BRAND_ON_DARK),
        os.path.join(IMG_DIR, "neuraal-mark.svg"): mark_only(mark, BRAND),
        os.path.join(IMG_DIR, "neuraal-mark-dark.svg"): mark_only(mark, BRAND_ON_DARK),
        os.path.join(IMG_DIR, "neuraal-favicon.svg"): favicon_svg(mark),
    }
    for path, content in outputs.items():
        with open(path, "w", encoding="utf-8", newline="\n") as fh:
            fh.write(content)
        print("wrote", os.path.relpath(path, REPO))

    print("note: data/web/favicon.png is rasterised from neuraal-favicon.svg "
          "(any SVG->PNG converter at 128x128 works, e.g. `rsvg-convert -w 128 -h 128`)")


if __name__ == "__main__":
    main()
