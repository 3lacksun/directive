#!/usr/bin/env python3
from __future__ import annotations

import hashlib
import json
import re
import sys
from pathlib import Path

if len(sys.argv) != 3:
    raise SystemExit("usage: directive4_postbuild_forensic_scan.py PROJECT_ROOT TARGET_PACKAGE")

root = Path(sys.argv[1]).resolve()
target = sys.argv[2].strip()
if not root.is_dir():
    raise SystemExit(f"missing project root: {root}")
if not re.fullmatch(r"com\.directive\.v\d+", target):
    raise SystemExit(f"unexpected target package: {target}")

legacy = "com.ticktick.task"
literal_rx = re.compile(r'const-string(?:/jumbo)?\s+v\d+,\s*"com\.ticktick\.task"')
method_start_rx = re.compile(r"^\.method\s+(.*)$")

risk_tokens = {
    "getPackageName": "runtime package comparison",
    "getPackageManager": "package-manager lookup",
    "getPackageInfo": "package metadata lookup",
    "getApplicationInfo": "application metadata lookup",
    "setPackage": "explicit intent package routing",
    "ComponentName": "explicit component routing",
    "getLaunchIntentForPackage": "launcher package routing",
    "equals(Ljava/lang/Object;)Z": "string/object equality branch",
    "content://": "content-provider authority",
    "permission": "permission identity",
    "FileProvider": "file-provider authority",
    "PendingIntent": "pending-intent identity",
    "WorkManager": "background startup/scheduling",
    "JobScheduler": "background startup/scheduling",
}

def classify(body: str) -> list[dict[str, str]]:
    return [
        {"token": token, "reason": reason}
        for token, reason in risk_tokens.items()
        if token in body
    ]

occurrences: list[dict[str, object]] = []
for path in sorted(root.rglob("*.smali")):
    try:
        lines = path.read_text(encoding="utf-8", errors="replace").splitlines()
    except OSError:
        continue
    current_method = None
    method_start = 0
    for i, line in enumerate(lines):
        m = method_start_rx.match(line)
        if m:
            current_method = m.group(1)
            method_start = i
        if literal_rx.search(line):
            end = i
            while end + 1 < len(lines) and not lines[end + 1].startswith(".end method"):
                end += 1
            if end + 1 < len(lines):
                end += 1
            body = "\n".join(lines[method_start:end + 1]) if current_method else line
            indicators = classify(body)
            occurrences.append({
                "file": str(path.relative_to(root)),
                "line": i + 1,
                "method": current_method,
                "risk_score": len(indicators),
                "indicators": indicators,
                "context": "\n".join(lines[max(0, i - 8):min(len(lines), i + 9)]),
            })
        if line.startswith(".end method"):
            current_method = None

occurrences.sort(key=lambda x: (-int(x["risk_score"]), str(x["file"]), int(x["line"])))

manifest = root / "AndroidManifest.xml"
manifest_text = manifest.read_text(encoding="utf-8", errors="replace") if manifest.is_file() else ""
icon_match = re.search(r'<application\b[^>]*\bandroid:icon="([^"]+)"', manifest_text, re.S)
round_match = re.search(r'<application\b[^>]*\bandroid:roundIcon="([^"]+)"', manifest_text, re.S)
label_match = re.search(r'<application\b[^>]*\bandroid:label="([^"]+)"', manifest_text, re.S)

launcher_patterns = [
    "res/mipmap*/ic_launcher*",
    "res/drawable*/directive*launch*",
    "res/mipmap*/directive*",
    "res/drawable*/directive*icon*",
]
launcher_files: dict[str, dict[str, object]] = {}
seen: set[Path] = set()
for pattern in launcher_patterns:
    for path in sorted(root.glob(pattern)):
        if not path.is_file() or path in seen:
            continue
        seen.add(path)
        data = path.read_bytes()
        item: dict[str, object] = {
            "sha256": hashlib.sha256(data).hexdigest(),
            "size": len(data),
        }
        if path.suffix.lower() in {".xml", ".txt", ".json"}:
            item["text"] = data.decode("utf-8", errors="replace")[:20000]
        launcher_files[str(path.relative_to(root))] = item

non_smali_legacy: list[dict[str, object]] = []
for base in [manifest, root / "res"]:
    paths = [base] if base.is_file() else sorted(base.rglob("*")) if base.is_dir() else []
    for path in paths:
        if not path.is_file() or path.suffix.lower() not in {".xml", ".json", ".txt", ".properties"}:
            continue
        try:
            text = path.read_text(encoding="utf-8", errors="replace")
        except OSError:
            continue
        if legacy in text:
            non_smali_legacy.append({
                "file": str(path.relative_to(root)),
                "count": text.count(legacy),
            })

report = {
    "status": "PASS_SCAN_COMPLETE",
    "target_package": target,
    "legacy_exact_package": legacy,
    "remaining_exact_smali_package_literals": len(occurrences),
    "high_risk_occurrences": sum(1 for x in occurrences if int(x["risk_score"]) > 0),
    "occurrences": occurrences,
    "manifest": {
        "package_target_present": f'package="{target}"' in manifest_text,
        "application_icon": icon_match.group(1) if icon_match else None,
        "application_round_icon": round_match.group(1) if round_match else None,
        "application_label": label_match.group(1) if label_match else None,
        "legacy_exact_package_count": manifest_text.count(legacy),
    },
    "launcher_files": launcher_files,
    "non_smali_resource_legacy_references": non_smali_legacy,
    "interpretation": {
        "purpose": "Identify residual Android package-identity literals and prove which launcher assets DIRECTIVE 4 ships before further remediation.",
        "warning": "Internal Java/JNI class descriptors using com.ticktick.task are intentionally outside this exact-string scan and must not be globally renamed.",
    },
}

out = root / "DIRECTIVE4_POSTBUILD_FORENSIC.json"
out.write_text(json.dumps(report, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")

print(json.dumps({
    "status": report["status"],
    "remaining_exact_smali_package_literals": report["remaining_exact_smali_package_literals"],
    "high_risk_occurrences": report["high_risk_occurrences"],
    "manifest": report["manifest"],
    "launcher_files": list(launcher_files),
}, indent=2))
for item in occurrences[:30]:
    print(f"RISK={item['risk_score']} {item['file']}:{item['line']} {item['method']}")
    for indicator in item["indicators"]:
        print(f"  - {indicator['token']}: {indicator['reason']}")
