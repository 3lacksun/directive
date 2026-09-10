#!/usr/bin/env python3
from __future__ import annotations

import json
import re
import sys
from pathlib import Path

if len(sys.argv) != 3:
    raise SystemExit("usage: patch_directive_runtime_package_identity.py PROJECT_ROOT TARGET_PACKAGE")

root = Path(sys.argv[1]).resolve()
target = sys.argv[2].strip()
if not root.is_dir():
    raise SystemExit(f"missing project root: {root}")
if not re.fullmatch(r"com\.directive\.v\d+", target):
    raise SystemExit(f"unexpected target package: {target}")

# These are Android package-identity literals, not inherited Java/JNI class namespaces.
# Internal class descriptors under com.ticktick.task are intentionally preserved because
# native JNI exports and bytecode link to those class names.
targets = {
    Path("smali_classes2/e7/a.smali"): 1,
    Path("smali_classes3/com/ticktick/task/helper/IntentParamsBuilder.smali"): 9,
    Path("smali_classes4/com/ticktick/task/send/c.smali"): 1,
}

literal_rx = re.compile(r'(?P<prefix>const-string(?:/jumbo)?\s+v\d+,\s*)"com\.ticktick\.task"')
report = {
    "status": "PASS",
    "target_package": target,
    "files": {},
    "total_replacements": 0,
    "critical_variant_discriminator_fixed": False,
    "internal_com_ticktick_task_class_namespace_preserved": True,
    "billing_and_entitlement_models_modified": False,
}

for rel, expected in targets.items():
    path = root / rel
    if not path.is_file():
        raise SystemExit(f"required runtime identity file missing: {rel}")
    src = path.read_text(encoding="utf-8")
    patched, count = literal_rx.subn(lambda m: m.group("prefix") + json.dumps(target), src)
    if count != expected:
        raise SystemExit(f"{rel}: expected {expected} exact package literal replacements, found {count}")
    path.write_text(patched, encoding="utf-8")
    report["files"][str(rel)] = count
    report["total_replacements"] += count

critical = root / "smali_classes2/e7/a.smali"
crit_text = critical.read_text(encoding="utf-8")
method = re.search(r"\.method public static m\(\)Z(?P<body>.*?)\.end method", crit_text, re.S)
if not method:
    raise SystemExit("critical Le7/a;->m()Z method missing")
body = method.group("body")
if f'"{target}"' not in body or 'getPackageName()Ljava/lang/String;' not in body:
    raise SystemExit("critical package discriminator was not correctly retargeted")
if '"com.ticktick.task"' in body:
    raise SystemExit("legacy package identity remains in critical discriminator")
report["critical_variant_discriminator_fixed"] = True

# Fail closed if the explicitly handled internal-intent/permission files still contain
# the old exact Android package literal. Payment/subscription model literals are deliberately
# outside this remediation so authentication/licensing/entitlement truth is not altered.
for rel in targets:
    if '"com.ticktick.task"' in (root / rel).read_text(encoding="utf-8"):
        raise SystemExit(f"legacy exact package identity remains in {rel}")

out = root / "DIRECTIVE_RUNTIME_PACKAGE_IDENTITY_REMEDIATION_REPORT.json"
out.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
print(json.dumps(report, indent=2))
