#!/usr/bin/env python3
from __future__ import annotations

import json
import re
import sys
from pathlib import Path

if len(sys.argv) != 3:
    raise SystemExit("usage: patch_directive_provider_authority_namespace.py PROJECT_ROOT TARGET_PACKAGE")

root = Path(sys.argv[1]).resolve()
target = sys.argv[2].strip()
if not root.is_dir():
    raise SystemExit(f"missing project root: {root}")
if not re.fullmatch(r"com\.directive\.v\d+", target):
    raise SystemExit(f"unexpected target package: {target}")

wear_old = "com.ticktick.task.provider.weardataprovider"
wear_new = f"{target}.provider.weardataprovider"
suggestion_old = "com.ticktick.task.provider.TaskSuggestionProvider"
suggestion_new = f"{target}.provider.TaskSuggestionProvider"

files = {
    Path("smali_classes4/com/ticktick/task/wearableprovider/WearContentProvider.smali"): (wear_old, wear_new, 12),
    Path("smali_classes4/dh/a.smali"): (wear_old, wear_new, 1),
    Path("smali_classes4/com/ticktick/task/provider/TaskSuggestionProvider.smali"): (suggestion_old, suggestion_new, 1),
}

report = {
    "status": "PASS",
    "target_package": target,
    "files": {},
    "total_replacements": 0,
    "manifest_authorities_verified": [],
    "provider_runtime_authority_contract_verified": False,
    "inherited_provider_class_namespace_preserved": True,
    "auth_billing_entitlement_logic_changed": False,
}

for rel, (old, new, expected) in files.items():
    p = root / rel
    if not p.is_file():
        raise SystemExit(f"required provider runtime file missing: {rel}")
    src = p.read_text(encoding="utf-8")
    count = src.count(old)
    if count != expected:
        raise SystemExit(f"{rel}: expected {expected} occurrences of {old!r}, found {count}")
    patched = src.replace(old, new)
    p.write_text(patched, encoding="utf-8")
    report["files"][str(rel)] = {"from": old, "to": new, "replacements": count}
    report["total_replacements"] += count

manifest = (root / "AndroidManifest.xml").read_text(encoding="utf-8", errors="replace")
for authority in (wear_new, suggestion_new):
    if f'android:authorities="{authority}"' not in manifest:
        raise SystemExit(f"numbered manifest authority missing after package remediation: {authority}")
    report["manifest_authorities_verified"].append(authority)

# Fail closed if the old app-owned authorities remain in the exact runtime files handled here.
for rel in files:
    text = (root / rel).read_text(encoding="utf-8")
    if wear_old in text or suggestion_old in text:
        raise SystemExit(f"legacy provider authority remains in {rel}")

# Preserve inherited class descriptors: only Android authority strings are changed.
for rel in (
    Path("smali_classes4/com/ticktick/task/wearableprovider/WearContentProvider.smali"),
    Path("smali_classes4/com/ticktick/task/provider/TaskSuggestionProvider.smali"),
):
    text = (root / rel).read_text(encoding="utf-8")
    if "Lcom/ticktick/task/" not in text:
        raise SystemExit(f"inherited provider class namespace unexpectedly absent in {rel}")

report["provider_runtime_authority_contract_verified"] = True
out = root / "DIRECTIVE_PROVIDER_AUTHORITY_NAMESPACE_REPORT.json"
out.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
print(json.dumps(report, indent=2))
