#!/usr/bin/env python3
from __future__ import annotations

import json
import re
import sys
from pathlib import Path

if len(sys.argv) != 2:
    raise SystemExit("usage: patch_directive_launcher_identity.py PROJECT_ROOT")

root = Path(sys.argv[1]).resolve()
res = root / "res"
manifest = root / "AndroidManifest.xml"
if not res.is_dir() or not manifest.is_file():
    raise SystemExit("decoded Android project root not found")

# Vector traced from the authoritative DIRECTIVE_APPROVED_BRAND_UI_REFERENCE_01092026140811.png.
# The approved identity is the violet geometric spear/chevron insignia inside a reticle.
VIOLET = "#7B2AFF"
RING = "#6424CC"
BLACK = "#010106"

ring = "M32.40,34.20 L32.85,35.10 L27.90,40.50 L25.20,45.90 L23.85,50.85 L23.85,54.00 L21.15,54.45 L20.70,55.35 L23.85,55.80 L23.85,59.40 L25.65,65.70 L29.25,71.55 L33.30,75.60 L33.75,75.60 L27.45,68.40 L24.75,61.65 L24.30,55.80 L27.45,55.35 L27.45,54.45 L24.30,54.00 L25.65,45.90 L30.15,38.25 L33.30,35.10 L34.65,36.45 L33.75,35.10 L35.55,33.30 L43.20,29.25 L49.50,27.90 L52.65,27.90 L53.55,30.60 L54.45,30.60 L54.90,27.90 L63.00,28.80 L67.95,30.60 L72.45,33.30 L74.25,35.10 L73.80,36.00 L74.70,35.10 L79.20,40.05 L82.35,45.90 L83.70,51.30 L83.70,54.45 L83.25,54.90 L81.00,54.45 L80.55,55.35 L83.70,55.80 L83.70,59.40 L82.80,63.45 L80.55,68.40 L74.70,75.60 L79.20,71.10 L83.25,63.45 L84.60,55.80 L87.30,55.35 L87.30,54.90 L84.60,54.45 L83.70,48.15 L81.90,43.65 L80.10,40.50 L75.15,34.65 L71.10,31.95 L63.00,28.35 L58.95,27.45 L55.35,27.45 L54.45,26.55 L54.00,24.30 L52.65,27.00 L46.35,27.90 L37.35,31.50 L33.30,34.65 Z"
glyph = "M53.55,32.85 L51.30,39.15 L47.70,39.60 L47.70,40.50 L50.40,42.75 L46.35,56.70 L47.25,57.15 L48.60,56.70 L50.40,48.60 L51.75,46.80 L52.20,47.25 L52.20,62.55 L51.75,63.00 L43.20,56.25 L44.10,54.90 L43.20,54.45 L44.10,55.35 L42.75,56.25 L42.30,54.90 L41.85,55.35 L35.10,50.40 L34.65,50.85 L45.45,72.90 L48.15,70.65 L48.60,71.10 L48.15,73.35 L52.20,81.00 L54.00,83.25 L59.85,72.90 L57.60,71.10 L55.35,75.15 L54.45,68.40 L53.55,67.95 L65.25,58.95 L65.70,59.85 L62.55,66.60 L61.65,67.50 L60.30,66.15 L58.50,69.30 L62.10,72.90 L73.35,50.40 L70.65,51.75 L66.15,55.35 L65.25,54.90 L65.70,55.35 L64.35,56.70 L60.75,58.95 L60.30,58.50 L60.75,58.05 L59.85,57.60 L61.20,56.70 L59.85,53.55 L59.85,50.85 L57.15,42.75 L60.30,40.05 L56.25,39.15 L54.00,32.85 Z"
holes = [
    "M53.10,75.15 L54.45,76.50 L54.00,77.85 L52.65,76.05 Z",
    "M42.30,58.95 L45.00,61.20 L44.55,61.65 L45.00,61.20 L45.90,61.65 L45.00,63.00 L45.90,64.35 L46.35,63.90 L46.80,64.80 L47.25,63.90 L48.60,64.80 L48.15,64.35 L49.05,63.90 L50.40,65.25 L49.95,65.70 L50.40,66.15 L49.95,65.70 L50.85,65.25 L53.55,67.50 L52.65,75.60 L50.40,71.55 L49.05,70.65 L47.70,66.15 L46.80,65.70 L47.25,66.60 L46.35,67.50 L45.45,66.60 L41.85,59.85 Z",
    "M55.80,46.80 L57.15,48.60 L57.15,50.85 L58.50,54.00 L59.40,58.95 L60.30,59.40 L55.80,63.00 L55.35,62.55 L55.35,47.25 Z",
    "M53.55,39.60 L54.45,40.05 L55.35,43.20 L54.90,44.55 L54.00,43.20 L52.65,42.75 Z",
]

foreground = ['<?xml version="1.0" encoding="utf-8"?>', '<vector xmlns:android="http://schemas.android.com/apk/res/android" android:width="108dp" android:height="108dp" android:viewportWidth="108" android:viewportHeight="108">']
foreground.append(f'    <path android:fillColor="{RING}" android:pathData="{ring}"/>')
foreground.append(f'    <path android:fillColor="{VIOLET}" android:pathData="{glyph}"/>')
for hole in holes:
    foreground.append(f'    <path android:fillColor="{BLACK}" android:pathData="{hole}"/>')
foreground.append('</vector>')
foreground_xml = "\n".join(foreground) + "\n"

drawable = res / "drawable"
drawable.mkdir(parents=True, exist_ok=True)
(drawable / "directive_launcher_foreground.xml").write_text(foreground_xml, encoding="utf-8")

# Adaptive launcher icon for API 26+. No monochrome inherited TickTick drawable is retained.
adaptive = '''<?xml version="1.0" encoding="utf-8"?>
<adaptive-icon xmlns:android="http://schemas.android.com/apk/res/android">
    <background android:drawable="@color/ic_launcher_background"/>
    <foreground android:drawable="@drawable/directive_launcher_foreground"/>
</adaptive-icon>
'''
any26 = res / "mipmap-anydpi-v26"
any26.mkdir(parents=True, exist_ok=True)
(any26 / "ic_launcher.xml").write_text(adaptive, encoding="utf-8")
(any26 / "ic_launcher_round.xml").write_text(adaptive, encoding="utf-8")

# Vector-backed launcher for API 21-25. anydpi-v21 outranks the inherited density bitmaps.
legacy = f'''<?xml version="1.0" encoding="utf-8"?>
<layer-list xmlns:android="http://schemas.android.com/apk/res/android">
    <item android:drawable="@color/ic_launcher_background"/>
    <item android:drawable="@drawable/directive_launcher_foreground"/>
</layer-list>
'''
any21 = res / "mipmap-anydpi-v21"
any21.mkdir(parents=True, exist_ok=True)
(any21 / "ic_launcher.xml").write_text(legacy, encoding="utf-8")
(any21 / "ic_launcher_round.xml").write_text(legacy, encoding="utf-8")

# Replace the inherited blue/yellow adaptive background colour wherever defined.
colour_rx = re.compile(r'(<color\b[^>]*\bname=["\']ic_launcher_background["\'][^>]*>)(.*?)(</color>)', re.S)
found = 0
for p in sorted(res.glob("values*/colors*.xml")):
    text = p.read_text(encoding="utf-8", errors="replace")
    patched, count = colour_rx.subn(r'\g<1>#010106\g<3>', text)
    if count:
        p.write_text(patched, encoding="utf-8")
        found += count
if not found:
    values = res / "values"
    values.mkdir(parents=True, exist_ok=True)
    (values / "directive_launcher_colors.xml").write_text('<?xml version="1.0" encoding="utf-8"?>\n<resources><color name="ic_launcher_background">#010106</color></resources>\n', encoding="utf-8")

m = manifest.read_text(encoding="utf-8", errors="replace")
icon = re.search(r'<application\b[^>]*\bandroid:icon="([^"]+)"', m, re.S)
round_icon = re.search(r'<application\b[^>]*\bandroid:roundIcon="([^"]+)"', m, re.S)
if not icon or icon.group(1) != "@mipmap/ic_launcher":
    raise SystemExit(f"unexpected application icon reference: {icon.group(1) if icon else None}")
if not round_icon or round_icon.group(1) != "@mipmap/ic_launcher_round":
    raise SystemExit(f"unexpected application roundIcon reference: {round_icon.group(1) if round_icon else None}")

report = {
    "status": "PASS",
    "source_reference": "DIRECTIVE_APPROVED_BRAND_UI_REFERENCE_01092026140811.png",
    "launcher_identity": "approved geometric violet DIRECTIVE insignia",
    "background": BLACK,
    "adaptive_icon": "res/mipmap-anydpi-v26/ic_launcher.xml",
    "adaptive_round_icon": "res/mipmap-anydpi-v26/ic_launcher_round.xml",
    "foreground": "res/drawable/directive_launcher_foreground.xml",
    "legacy_vector_icons": ["res/mipmap-anydpi-v21/ic_launcher.xml", "res/mipmap-anydpi-v21/ic_launcher_round.xml"],
    "inherited_ticktick_launcher_replaced": True,
}
(root / "DIRECTIVE_LAUNCHER_IDENTITY_REMEDIATION_REPORT.json").write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
print(json.dumps(report, indent=2))
