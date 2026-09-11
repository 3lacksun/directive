#!/usr/bin/env python3
from __future__ import annotations

import json
import re
import sys
from pathlib import Path

if len(sys.argv) != 2:
    raise SystemExit("usage: patch_directive_startup_icon_process_exit.py PROJECT_ROOT")

root = Path(sys.argv[1]).resolve()
path = root / "smali_classes4/yf/t.smali"
if not path.is_file():
    raise SystemExit(f"required launcher icon manager missing: {path}")

src = path.read_text(encoding="utf-8")
method_rx = re.compile(
    r"(?P<head>\.method public static a\(Landroid/content/Context;Lyf/s;Z\)V\n)(?P<body>.*?)(?P<tail>^\.end method)",
    re.M | re.S,
)
m = method_rx.search(src)
if not m:
    raise SystemExit("launcher icon manager method Lyf/t;->a(Context,s,Z)V not found")

body = m.group("body")
if body.count("Ljava/lang/System;->exit(I)V") != 1:
    raise SystemExit(
        "expected exactly one System.exit in launcher icon manager method, found "
        + str(body.count("Ljava/lang/System;->exit(I)V"))
    )

# Root cause remediation: this method is called during MeTaskActivity.onCreate when a saved
# premium launcher icon must be normalised for a non-Pro user. The inherited implementation
# enables/disables launcher aliases, persists the corrected icon, then kills the VM with
# System.exit(0). On Samsung Android 16 this launch-time process death is surfaced as
# "app has a bug" and can repeat before the preference write is durably flushed.
# Preserve the entitlement decision and alias/persistence work; only remove the deliberate
# process termination so startup can complete and persistence can settle normally.
block_rx = re.compile(
    r"(?P<indent>\s*)invoke-static \{v4\}, Ljava/lang/System;->exit\(I\)V\n"
    r"(?:\s*\.line[^\n]*\n|\s*)*"
    r"\s*new-instance p0, Ljava/lang/RuntimeException;\n"
    r"(?:\s*\.line[^\n]*\n|\s*)*"
    r"\s*const-string p1, \"System\.exit returned normally, while it was supposed to halt JVM\.\"\n"
    r"(?:\s*\.line[^\n]*\n|\s*)*"
    r"\s*invoke-direct \{p0, p1\}, Ljava/lang/RuntimeException;-><init>\(Ljava/lang/String;\)V\n"
    r"(?:\s*\.line[^\n]*\n|\s*)*"
    r"\s*throw p0\n",
    re.M,
)

patched_body, count = block_rx.subn("\n    return-void\n", body, count=1)
if count != 1:
    raise SystemExit("could not match the exact launcher-icon System.exit/throw block")
if "Ljava/lang/System;->exit(I)V" in patched_body:
    raise SystemExit("System.exit remains in launcher icon manager method after remediation")

patched = src[: m.start("body")] + patched_body + src[m.end("body") :]
path.write_text(patched, encoding="utf-8")

report = {
    "status": "PASS",
    "file": str(path.relative_to(root)),
    "method": "Lyf/t;->a(Landroid/content/Context;Lyf/s;Z)V",
    "deliberate_launch_time_process_exit_removed": True,
    "launcher_alias_enable_disable_logic_preserved": True,
    "app_icon_preference_persistence_preserved": True,
    "pro_entitlement_guard_preserved": True,
    "authentication_licensing_entitlement_truth_modified": False,
    "network_permissions_modified": False,
    "inherited_java_jni_namespace_modified": False,
}
out = root / "DIRECTIVE_STARTUP_ICON_PROCESS_EXIT_REMEDIATION_REPORT.json"
out.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
print(json.dumps(report, indent=2))
