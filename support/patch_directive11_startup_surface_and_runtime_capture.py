#!/usr/bin/env python3
from __future__ import annotations

import json
import re
import sys
from pathlib import Path

if len(sys.argv) != 2:
    raise SystemExit("usage: patch_directive11_startup_surface_and_runtime_capture.py PROJECT_ROOT")

root = Path(sys.argv[1]).resolve()
if not root.is_dir():
    raise SystemExit(f"missing project root: {root}")

# ---------------------------------------------------------------------------
# 1. Correct the actual launcher/startup surface.
# DIRECTIVE launch artwork already exists in the decoded project, but the
# launcher themes still point at the inherited TickTick background.
# ---------------------------------------------------------------------------
launch_bg = root / "res/drawable/directive_launch_background.xml"
launch_mark = root / "res/drawable/directive_launch_mark.xml"
if not launch_bg.is_file() or not launch_mark.is_file():
    raise SystemExit("DIRECTIVE launch artwork is missing")

style_targets = {
    root / "res/values/styles.xml": {"AppTheme.Launcher", "AppTheme.Launcher.Compat"},
    root / "res/values-night/styles.xml": {"AppTheme.Launcher"},
}
style_rx = re.compile(r'(<style\b[^>]*\bname="(?P<name>[^"]+)"[^>]*>)(?P<body>.*?)(</style>)', re.S)
startup_style_replacements = 0
patched_styles: dict[str, list[str]] = {}

for path, wanted in style_targets.items():
    if not path.is_file():
        raise SystemExit(f"required styles file missing: {path.relative_to(root)}")
    src = path.read_text(encoding="utf-8")
    seen: set[str] = set()

    def patch_style(m: re.Match[str]) -> str:
        global startup_style_replacements
        name = m.group("name")
        if name not in wanted:
            return m.group(0)
        seen.add(name)
        body = m.group("body")
        old = '<item name="android:windowBackground">@drawable/ticktick_launcher_bg</item>'
        new = '<item name="android:windowBackground">@drawable/directive_launch_background</item>'
        if body.count(old) != 1:
            raise SystemExit(f"{path.relative_to(root)} style {name}: expected one inherited launcher background")
        body = body.replace(old, new, 1)
        startup_style_replacements += 1
        patched_styles.setdefault(str(path.relative_to(root)), []).append(name)
        return m.group(1) + body + m.group(4)

    out = style_rx.sub(patch_style, src)
    missing = wanted - seen
    if missing:
        raise SystemExit(f"{path.relative_to(root)} missing launcher styles: {sorted(missing)}")
    path.write_text(out, encoding="utf-8")

if startup_style_replacements != 3:
    raise SystemExit(f"expected 3 startup-style replacements, got {startup_style_replacements}")

# ---------------------------------------------------------------------------
# 2. Preserve the system-only PROVIDERS_CHANGED receiver registration.
# Android 14's export-flag requirement explicitly exempts receivers that
# receive only system broadcasts. D10's NOT_EXPORTED change is therefore not
# carried forward as a root-cause fix. Fail closed if the source contract is
# no longer exactly the system-only filter we inspected.
# ---------------------------------------------------------------------------
app = root / "smali_classes2/com/ticktick/task/TickTickApplication.smali"
if not app.is_file():
    raise SystemExit("TickTickApplication.smali missing")
app_text = app.read_text(encoding="utf-8")
clinit = re.search(r'\.method static constructor <clinit>\(\)V(?P<body>.*?)\.end method', app_text, re.S)
if not clinit:
    raise SystemExit("TickTickApplication.<clinit> missing")
clinit_body = clinit.group("body")
if clinit_body.count('"android.location.PROVIDERS_CHANGED"') != 1:
    raise SystemExit("settingsIntentFilter is no longer the expected PROVIDERS_CHANGED system filter")
if clinit_body.count('IntentFilter;->addAction(Ljava/lang/String;)V') != 1:
    raise SystemExit("settingsIntentFilter contains unexpected additional actions")
oncreate = re.search(r'\.method public onCreate\(\)V(?P<body>.*?)\.end method', app_text, re.S)
if not oncreate:
    raise SystemExit("TickTickApplication.onCreate missing")
legacy_receiver = 'Landroid/content/Context;->registerReceiver(Landroid/content/BroadcastReceiver;Landroid/content/IntentFilter;)Landroid/content/Intent;'
if oncreate.group("body").count(legacy_receiver) != 1:
    raise SystemExit("expected original system-only two-argument receiver registration")
if 'Ld0/a;->registerReceiver(Landroid/content/Context;Landroid/content/BroadcastReceiver;Landroid/content/IntentFilter;I)' in oncreate.group("body"):
    raise SystemExit("unexpected D10 flagged receiver registration present in D11 baseline")

# ---------------------------------------------------------------------------
# 3. Capture ActivityThreadCallback fatal exceptions immediately before the
# inherited killProcess/System.exit path. The existing termination semantics
# remain untouched.
# ---------------------------------------------------------------------------
activity_cb = root / "smali_classes4/com/ticktick/task/utils/ActivityThreadCallback.smali"
if not activity_cb.is_file():
    raise SystemExit("ActivityThreadCallback.smali missing")
cb = activity_cb.read_text(encoding="utf-8")
abort_rx = re.compile(r'(?P<head>\.method private static abort\(Ljava/lang/Throwable;\)Z\n)(?P<body>.*?)(?P<tail>^\.end method)', re.M | re.S)
am = abort_rx.search(cb)
if not am:
    raise SystemExit("ActivityThreadCallback.abort(Throwable) missing")
body = am.group("body")
if 'Lcom/directive/diagnostics/CrashRecorder;->record' in body:
    raise SystemExit("ActivityThreadCallback already instrumented")
if body.count('    .locals 3') != 1:
    raise SystemExit("unexpected ActivityThreadCallback.abort locals contract")
anchor = '    if-eqz p0, :cond_0\n'
if body.count(anchor) != 1:
    raise SystemExit("ActivityThreadCallback abort insertion anchor changed")
body = body.replace('    .locals 3', '    .locals 4', 1)
record_block = '''    if-eqz p0, :directive_abort_record_done\n\n    invoke-static {}, Lcom/ticktick/task/TickTickApplicationBase;->getInstance()Lcom/ticktick/task/TickTickApplicationBase;\n    move-result-object v3\n\n    invoke-static {v3, p0}, Lcom/directive/diagnostics/CrashRecorder;->record(Landroid/content/Context;Ljava/lang/Throwable;)V\n\n    :directive_abort_record_done\n'''
body = body.replace(anchor, record_block + anchor, 1)
cb = cb[:am.start("body")] + body + cb[am.end("body"):]
activity_cb.write_text(cb, encoding="utf-8")

# ---------------------------------------------------------------------------
# 4. Capture all remaining uncaught exceptions before delegating to the
# inherited default handler or inherited process-kill fallback. Do not swallow
# or replace the original throwable.
# ---------------------------------------------------------------------------
crash = root / "smali_classes4/com/ticktick/task/utils/CrashLogHandler.smali"
if not crash.is_file():
    raise SystemExit("CrashLogHandler.smali missing")
cs = crash.read_text(encoding="utf-8")
uncaught_rx = re.compile(r'(?P<head>\.method public uncaughtException\(Ljava/lang/Thread;Ljava/lang/Throwable;\)V\n)(?P<body>.*?)(?P<tail>^\.end method)', re.M | re.S)
cm = uncaught_rx.search(cs)
if not cm:
    raise SystemExit("CrashLogHandler.uncaughtException missing")
cbody = cm.group("body")
if 'Lcom/directive/diagnostics/CrashRecorder;->record' in cbody:
    raise SystemExit("CrashLogHandler already instrumented")
if cbody.count('    .locals 2') != 1:
    raise SystemExit("unexpected CrashLogHandler locals contract")
validation = '    invoke-static {p2, v0}, Lkotlin/jvm/internal/n;->e(Ljava/lang/Object;Ljava/lang/String;)V\n'
if cbody.count(validation) != 1:
    raise SystemExit("CrashLogHandler validation anchor changed")
cbody = cbody.replace('    .locals 2', '    .locals 3', 1)
uncaught_record = '''\n    invoke-static {}, Lcom/ticktick/task/TickTickApplicationBase;->getInstance()Lcom/ticktick/task/TickTickApplicationBase;\n    move-result-object v2\n\n    invoke-static {v2, p2}, Lcom/directive/diagnostics/CrashRecorder;->record(Landroid/content/Context;Ljava/lang/Throwable;)V\n'''
cbody = cbody.replace(validation, validation + uncaught_record, 1)
cs = cs[:cm.start("body")] + cbody + cs[cm.end("body"):]
crash.write_text(cs, encoding="utf-8")

report = {
    "status": "PASS",
    "startup_surface": {
        "inherited_ticktick_window_background_removed_from_launcher_styles": True,
        "directive_launch_background_wired": True,
        "style_replacements": startup_style_replacements,
        "patched_styles": patched_styles,
    },
    "android14_receiver_review": {
        "filter": "android.location.PROVIDERS_CHANGED",
        "system_only_filter_verified": True,
        "d10_receiver_flag_hypothesis_carried_forward": False,
        "original_system_broadcast_registration_preserved": True,
    },
    "runtime_capture": {
        "application_oncreate_capture_expected_from_prior_crash_patcher": True,
        "activity_thread_abort_capture_added": True,
        "global_uncaught_capture_added": True,
        "original_throwable_swallowed": False,
        "activity_thread_kill_process_preserved": True,
        "activity_thread_system_exit_preserved": True,
        "default_uncaught_handler_delegation_preserved": True,
        "crash_output": "MediaStore Downloads/DIRECTIVE_11_CRASH_<timestamp>.txt on Android 10+",
    },
    "inherited_ticktick_java_jni_namespace_preserved": True,
    "offline_network_permission_boundary_changed": False,
    "authentication_licensing_premium_entitlement_logic_changed": False,
}
out = root / "DIRECTIVE11_STARTUP_SURFACE_RUNTIME_CAPTURE_REPORT.json"
out.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
print(json.dumps(report, indent=2))
