#!/usr/bin/env python3
from __future__ import annotations

import json
import re
import sys
from pathlib import Path

if len(sys.argv) != 3:
    raise SystemExit("usage: patch_directive_fixed_launcher_runtime.py PROJECT_ROOT TARGET_PACKAGE")

root = Path(sys.argv[1]).resolve()
target = sys.argv[2].strip()
if not re.fullmatch(r"com\.directive\.v\d+", target):
    raise SystemExit(f"unexpected target package: {target}")

manifest = root / "AndroidManifest.xml"
changer = root / "smali_classes4/yf/t.smali"
if not manifest.is_file() or not changer.is_file():
    raise SystemExit("required decoded source files are missing")

# Launcher aliases are app-owned Android component identifiers, not Java/JNI class names.
# The inherited launcher changer builds these identifiers from Context.getPackageName(),
# so after applicationId migration the aliases must use the numbered DIRECTIVE package.
m = manifest.read_text(encoding="utf-8")
alias_rx = re.compile(r'android:name="com\.ticktick\.task\.(HomeAlia_[^"]+)"')
m2, alias_count = alias_rx.subn(lambda x: f'android:name="{target}.{x.group(1)}"', m)
if alias_count != 26:
    raise SystemExit(f"expected 26 launcher aliases to migrate, found {alias_count}")
manifest.write_text(m2, encoding="utf-8")

# Dynamic launcher-icon switching is cosmetic. Its inherited implementation enables/disables
# aliases and then intentionally calls System.exit(), which is unsafe during a migrated cold
# launch. DIRECTIVE uses one fixed approved launcher identity, so make the mutator a no-op.
s = changer.read_text(encoding="utf-8")n
