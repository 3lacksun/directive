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
# The inherited LauncherIconChanger builds these identifiers from Context.getPackageName(),
# so after applicationId migration the aliases must use the numbered DIRECTIVE package.
m = manifest.read_text(encoding="utf-8")
alias_rx = re.compile(r'android:name="com\.ticktick\.task\.(HomeAlia_[^"]+)"')
m2, alias_count = alias_rx.subn(lambda x: f'android:name="{target}.{x.group(1)}"', m)
if alias_count != 26:
    raise SystemExit(f"expected 26 launcher aliases to migrate, found {alias_count}")
manifest.write_text(m2, encoding="utf-8")

# Dynamic launcher-icon switching is cosmetic. Its inherited implementation enables/disables
# aliases and then intentionally calls System.exit(), which is unsafe during a migrated cold
# launch. DIRECTIVE has one fixed approved launcher identity, so make only the mutator a no-op.
s = changer.read_text(encoding="utf-8")
method_rx = re.compile(
    r'^\.method public static a\(Landroid/content/Context;Lyf/s;Z\)V\n.*?^\.end method',
    re.M | re.S,
)
replacement = '''.method public static a(Landroid/content/Context;Lyf/s;Z)V
    .locals 0

    return-void
.end method'''
s2, method_count = method_rx.subn(replacement, s, count=1)
if method_count != 1:
    raise SystemExit(f"expected one LauncherIconChanger mutator, found {method_count}")
changer.write_text(s2, encoding="utf-8")

# Fail-closed verification.
m_final = manifest.read_text(encoding="utf-8")
legacy_aliases = re.findall(r'android:name="com\.ticktick\.task\.HomeAlia_[^"]+"', m_final)
target_aliases = re.findall(rf'android:name="{re.escape(target)}\.HomeAlia_[^"]+"', m_final)
if legacy_aliases:
    raise SystemExit(f"legacy launcher aliases remain: {legacy_aliases[:3]}")
if len(target_aliases) != 26:
    raise SystemExit(f"expected 26 numbered DIRECTIVE launcher aliases, found {len(target_aliases)}")
if f'android:name="{target}.HomeAlia_default"' not in m_final:
    raise SystemExit("numbered DIRECTIVE default launcher alias missing")

s_final = changer.read_text(encoding="utf-8")
match = method_rx.search(s_final)
if not match:
    raise SystemExit("patched launcher mutator missing")
body = match.group(0)
for forbidden in (
    'setComponentEnabledSetting',
    'Ljava/lang/System;->exit(I)V',
    'setChangIconReloadFlag',
    'setAppIcon',
):
    if forbidden in body:
        raise SystemExit(f"launcher mutator still contains {forbidden}")
if 'return-void' not in body:
    raise SystemExit("launcher mutator is not a no-op return")

report = {
    "status": "PASS",
    "target_package": target,
    "launcher_aliases_migrated": alias_count,
    "default_launcher_alias": f"{target}.HomeAlia_default",
    "dynamic_launcher_icon_mutation": "DISABLED_FIXED_DIRECTIVE_IDENTITY",
    "launcher_mutator_system_exit_removed": True,
    "internal_com_ticktick_task_java_jni_namespace_preserved": True,
    "authentication_or_entitlement_logic_modified": False,
    "reason": "Numbered-package aliases must match Context.getPackageName(); inherited cosmetic icon changer intentionally exited the process after alias changes.",
}
out = root / "DIRECTIVE_FIXED_LAUNCHER_RUNTIME_REPORT.json"
out.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
print(json.dumps(report, indent=2))
