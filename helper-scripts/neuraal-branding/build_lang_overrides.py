#!/usr/bin/env python3
"""
Builds data/web/lang/lang.local.<locale>.json - sparse overlays that rename the
user-visible "mailcow" strings to "Neuraal", one per shipped language file.

The overlays are merged on top of the active language by the small hook added
to data/web/inc/prerequisites.inc.php, so the upstream language files stay
untouched and keep updating normally.

Technical identifiers are deliberately preserved: container names
(sogo-mailcow, acme-mailcow, ...), documentation/service URLs, example
domains and config file paths must keep working.

Run from the repository root:
  python3 helper-scripts/neuraal-branding/build_lang_overrides.py
"""

import glob
import json
import os
import re

REPO = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
LANG_DIR = os.path.join(REPO, "data", "web", "lang")

BRAND = "Neuraal"

# Substrings that must survive verbatim - replaced by a placeholder first.
PROTECTED = [
    r"[a-z0-9_-]+-mailcow",                 # container names
    r"https?://[^\s\"'<>]*mailcow[^\s\"'<>]*",  # documentation / shop links
    r"(?:ipv4|ipv6)\.mailcow\.email",
    r"hosted\.mailcow\.de",
    r"mailcow\.tld",
    r"mailcow_password",
]


def rebrand(text):
    tokens = []

    def stash(match):
        tokens.append(match.group(0))
        return "\x00%d\x00" % (len(tokens) - 1)

    protected = re.sub("|".join(PROTECTED), stash, text)
    branded = protected
    branded = branded.replace("MAILCOW", BRAND.upper())
    branded = re.sub(r"[Mm]ailcow", BRAND, branded)
    for index, token in enumerate(tokens):
        branded = branded.replace("\x00%d\x00" % index, token)
    return branded


def walk(node):
    """Return a sparse copy of node containing only the rebranded strings."""
    if isinstance(node, dict):
        out = {}
        for key, value in node.items():
            child = walk(value)
            if child is not None:
                out[key] = child
        return out or None
    if isinstance(node, list):
        changed = [walk(v) for v in node]
        return node if any(c is not None for c in changed) else None
    if isinstance(node, str):
        branded = rebrand(node)
        return branded if branded != node else None
    return None


def main():
    sources = sorted(p for p in glob.glob(os.path.join(LANG_DIR, "lang.*.json"))
                     if ".local." not in os.path.basename(p))
    for src in sources:
        locale = os.path.basename(src)[len("lang."):-len(".json")]
        with open(src, encoding="utf-8") as fh:
            lang = json.load(fh)

        overlay = walk(lang)
        dst = os.path.join(LANG_DIR, "lang.local.%s.json" % locale)
        if not overlay:
            if os.path.exists(dst):
                os.remove(dst)
            continue

        with open(dst, "w", encoding="utf-8", newline="\n") as fh:
            json.dump(overlay, fh, indent=2, ensure_ascii=False)
            fh.write("\n")
        count = sum(len(v) for v in overlay.values() if isinstance(v, dict))
        print("wrote %s (%d strings)" % (os.path.relpath(dst, REPO), count))


if __name__ == "__main__":
    main()
