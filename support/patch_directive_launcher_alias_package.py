#!/usr/bin/env python3
from __future__ import annotations

import json
import re
import sys
from pathlib import Path

if len(sys.argv) != 3:
    raise SystemExit("usage: patch_directive_launcher_alias_package.py PROJECT_ROOT TARGET_PACKAGE")

root = Path(sys.argv[1]).resolve()
target = sys.argv[2].strip()
manifest = root / "AndroidManifest.xml"
launcher_code = root / "smali_classes4/yf/t.smali"

if not re.fullmatch(r"com\.directive\.v\d+", target):
    raise SystemExit(f"unexpected target package: {target}")
if not manifest.is_file() or not launcher_code.is_file():
    raise SystemExit("required manifest/launcher runtime source missing")

src = manifest.read_text(encoding="utf-8")
manifest_pkg = re.search(r'<manifest\b[^>]*\bpackage="([^"]+)"', src)
if not manifest_pkg or manifest_pkg.group(1) != target:
    raise SystemExit(f"manifest package is not target: {manifest_pkg.group(1) if manifest_pkg else None}")

# LauncherIcon.kt derives ComponentName class names as getPackageName() + '.HomeAlia_*'.
# Therefore alias component class names must live under the installed application package,
# while targetActivity remains the inherited com.ticktick.task Java class namespace.
code = launcher_code.read_text(encoding="utf-8", errors="replace")
required_runtime_markers = [
    'Landroid/content/Context;->getPackageName()Ljava/lang/String;',
    'HomeAlia_default',
    'Landroid/content/pm/PackageManager;->setComponentEnabledSetting',
]
for marker in required_runtime_markers:
    if marker not in code:
        raise SystemExit(f"launcher runtime contract marker missing: {marker}")

alias_rx = re.compile(r'(android:name=")com\.ticktick\.task\.(HomeAlia_[^"]+)(")')
patched, count = alias_rx.subn(lambda m: m.group(1) + target + '.' + m.group(2) + m.group(3), src)
if count < 2:
    raise SystemExit(f"expected launcher aliases to patch, found {count}")

# Fail closed: every HomeAlia alias must now be current-package, but inherited targetActivity
# class names must remain com.ticktick.task.* for binary compatibility.
remaining_old_aliases = re.findall(r'android:name="com\.ticktick\.task\.(HomeAlia_[^"]+)"', patched)
if remaining_old_aliases:
    raise SystemExit(f"legacy launcher aliases remain: {remaining_old_aliases[:5]}")
current_aliases = re.findall(rf'android:name="{re.escape(target)}\.(HomeAlia_[^"]+)"', patched)
if len(current_aliases) != count:
    raise SystemExit("patched launcher alias count mismatch")
if 'android:targetActivity="com.ticktick.task.activity.MeTaskActivity"' not in patched:
    raise SystemExit("inherited launcher target activity namespace was unexpectedly changed")

manifest.write_text(patched, encoding="utf-8")
report = {
    "status": "PASS",
    "target_package": target,
    "launcher_aliases_retargeted": count,
    "runtime_contract": "LauncherIcon.kt derives getPackageName() + .HomeAlia_*",
    "inherited_target_activity_namespace_preserved": True,
    "auth_licensing_entitlement_modified": False,
}
(root / "DIRECTIVE_LAUNCHER_ALIAS_PACKAGE_REMEDIATION_REPORT.json").write_text(
    json.dumps(report, indent=2) + "\n", encoding="utf-8"
)
print(json.dumps(report, indent=2))
