#!/usr/bin/env python3
from __future__ import annotations

import json
import re
import sys
from pathlib import Path

if len(sys.argv) != 3:
    raise SystemExit('usage: patch_directive_android16_startup_hardening.py PROJECT_ROOT TARGET_PACKAGE')

root = Path(sys.argv[1]).resolve()
target = sys.argv[2].strip()
if not root.is_dir():
    raise SystemExit(f'missing project root: {root}')
if not re.fullmatch(r'com\.directive\.v\d+', target):
    raise SystemExit(f'unexpected target package: {target}')

report = {
    'status': 'PASS',
    'target_package': target,
    'target_sdk': 36,
    'activity_thread_abort_hook_disabled': False,
    'global_dynamic_receiver_startup_registration_disabled': False,
    'settings_provider_changed_receiver_startup_registration_disabled': False,
    'firebase_app_startup_init_disabled': False,
    'startup_providers_disabled': [],
    'task_affinity_retargets': 0,
    'auth_billing_entitlement_logic_modified': False,
}

# 1) Android 16 target alignment. The app is being validated on API 36; targeting API 37
# exposed future behaviour before the Android 16 remediation was complete.
meta = root / 'apktool.json'
if meta.is_file():
    data = json.loads(meta.read_text(encoding='utf-8'))
    data.setdefault('sdkInfo', {})['targetSdkVersion'] = '36'
    meta.write_text(json.dumps(data, indent=2) + '\n', encoding='utf-8')

yml = root / 'apktool.yml'
if yml.is_file():
    s = yml.read_text(encoding='utf-8', errors='replace')
    s, n = re.subn(r'(?m)^(\s*targetSdkVersion:\s*)["\']?\d+["\']?\s*$', r'\g<1>"36"', s, count=1)
    if n:
        yml.write_text(s, encoding='utf-8')

# 2) Disable the legacy ActivityThread mH callback shim. It explicitly killProcess()+System.exit()
# on framework errors. That behaviour masks the real exception and is unsafe on modern Android.
base = root / 'smali_classes2/com/ticktick/task/TickTickApplicationBase.smali'
s = base.read_text(encoding='utf-8')
pat = re.compile(r'\.method private initExceptionHandler\(\)V\n.*?\.end method', re.S)
replacement = '.method private initExceptionHandler()V\n    .locals 0\n\n    return-void\n.end method'
s2, n = pat.subn(replacement, s, count=1)
if n != 1:
    raise SystemExit(f'expected one initExceptionHandler method, found {n}')
base.write_text(s2, encoding='utf-8')
report['activity_thread_abort_hook_disabled'] = True

# 3) Disable startup-only global receiver registration. The receiver only reacts to screen/
# locale/configuration changes; omitting it avoids legacy dynamic-receiver registration during
# cold launch. Core task/calendar/reminder storage remains unaffected.
s = base.read_text(encoding='utf-8')
pat = re.compile(r'\.method private registerGlobalBroadcastReceiver\(\)V\n.*?\.end method', re.S)
replacement = '.method private registerGlobalBroadcastReceiver()V\n    .locals 0\n\n    return-void\n.end method'
s2, n = pat.subn(replacement, s, count=1)
if n != 1:
    raise SystemExit(f'expected one registerGlobalBroadcastReceiver method, found {n}')
base.write_text(s2, encoding='utf-8')
report['global_dynamic_receiver_startup_registration_disabled'] = True

# 4) DIRECTIVE is offline-only. Remove nonessential startup initialisation from the concrete
# application that can invoke SDK/provider compatibility code before the first screen.
app = root / 'smali_classes2/com/ticktick/task/TickTickApplication.smali'
s = app.read_text(encoding='utf-8')
old = '    invoke-virtual {p0, v0, v1}, Landroid/content/Context;->registerReceiver(Landroid/content/BroadcastReceiver;Landroid/content/IntentFilter;)Landroid/content/Intent;'
if s.count(old) != 1:
    raise SystemExit(f'expected one TickTickApplication settings receiver registration, got {s.count(old)}')
s = s.replace(old, '    # DIRECTIVE Android 16: startup settings receiver intentionally disabled\n    nop', 1)
report['settings_provider_changed_receiver_startup_registration_disabled'] = True
old = '    invoke-direct {p0}, Lcom/ticktick/task/TickTickApplication;->initFirebaseApp()V'
if s.count(old) != 1:
    raise SystemExit(f'expected one initFirebaseApp invocation, got {s.count(old)}')
s = s.replace(old, '    # DIRECTIVE offline runtime: Firebase startup init intentionally disabled\n    nop', 1)
report['firebase_app_startup_init_disabled'] = True
app.write_text(s, encoding='utf-8')

# 5) Providers for removed online/telemetry/social stacks must not auto-initialise before
# Application.onCreate. Keep AndroidX Startup because WorkManager/lifecycle are local core deps.
manifest = root / 'AndroidManifest.xml'
m = manifest.read_text(encoding='utf-8', errors='replace')
providers = [
    'com.google.firebase.provider.FirebaseInitProvider',
    'com.facebook.internal.FacebookInitProvider',
    'com.facebook.FacebookContentProvider',
    'com.bugsnag.android.internal.BugsnagContentProvider',
    'com.google.mlkit.common.internal.MlKitInitProvider',
]
for name in providers:
    rx = re.compile(r'(<provider\b(?=[^>]*android:name="' + re.escape(name) + r'")[^>]*)(/?>)', re.S)
    mm = rx.search(m)
    if not mm:
        raise SystemExit(f'required provider not found: {name}')
    tag = mm.group(0)
    if 'android:enabled=' not in tag:
        newtag = mm.group(1) + ' android:enabled="false"' + mm.group(2)
    else:
        newtag = re.sub(r'android:enabled="[^"]+"', 'android:enabled="false"', tag, count=1)
    m = m[:mm.start()] + newtag + m[mm.end():]
    report['startup_providers_disabled'].append(name)

# Retarget task affinities that are application identity, while keeping inherited class names.
for old, new in [
    ('android:taskAffinity="com.ticktick.task.external"', f'android:taskAffinity="{target}.external"'),
    ('android:taskAffinity="com.ticktick.task.second"', f'android:taskAffinity="{target}.second"'),
]:
    count = m.count(old)
    report['task_affinity_retargets'] += count
    m = m.replace(old, new)

manifest.write_text(m, encoding='utf-8')

# Fail-closed verification.
check = base.read_text(encoding='utf-8')
mi = re.search(r'\.method private initExceptionHandler\(\)V(.*?)\.end method', check, re.S)
if not mi or 'killProcess' in mi.group(1) or 'ActivityThreadCallback' in mi.group(1):
    raise SystemExit('legacy ActivityThread abort hook still active')
mg = re.search(r'\.method private registerGlobalBroadcastReceiver\(\)V(.*?)\.end method', check, re.S)
if not mg or 'registerReceiver' in mg.group(1):
    raise SystemExit('legacy global startup receiver still active')
ms = manifest.read_text(encoding='utf-8')
for name in providers:
    mm = re.search(r'<provider\b(?=[^>]*android:name="' + re.escape(name) + r'")[^>]*>', ms, re.S)
    if not mm or 'android:enabled="false"' not in mm.group(0):
        raise SystemExit(f'provider not disabled: {name}')
for forbidden in ['android.permission.INTERNET','android.permission.ACCESS_NETWORK_STATE','android.permission.ACCESS_WIFI_STATE','android.permission.CHANGE_NETWORK_STATE','android.permission.CHANGE_WIFI_STATE']:
    if forbidden in ms:
        raise SystemExit(f'forbidden network permission present: {forbidden}')

out = root / 'DIRECTIVE_ANDROID16_STARTUP_HARDENING_REPORT.json'
out.write_text(json.dumps(report, indent=2) + '\n', encoding='utf-8')
print(json.dumps(report, indent=2))
