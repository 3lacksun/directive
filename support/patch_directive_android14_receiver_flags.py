#!/usr/bin/env python3
from pathlib import Path
import json, sys

if len(sys.argv) != 2:
    raise SystemExit('usage: patch_directive_android14_receiver_flags.py <project_root>')
root = Path(sys.argv[1])
p = root / 'smali_classes2/com/ticktick/task/TickTickApplication.smali'
if not p.is_file():
    raise SystemExit(f'missing {p}')

text = p.read_text(encoding='utf-8')
method_start = text.find('.method public onCreate()V')
if method_start < 0:
    raise SystemExit('TickTickApplication.onCreate not found')
method_end = text.find('.end method', method_start)
if method_end < 0:
    raise SystemExit('TickTickApplication.onCreate end not found')
method_end += len('.end method')
method = text[method_start:method_end]

legacy = '    invoke-virtual {p0, v0, v1}, Landroid/content/Context;->registerReceiver(Landroid/content/BroadcastReceiver;Landroid/content/IntentFilter;)Landroid/content/Intent;'
if method.count(legacy) != 1:
    raise SystemExit(f'expected exactly one legacy startup receiver registration, found {method.count(legacy)}')

replacement = '''    # Android 13+ dynamic receiver compatibility: this settings receiver is app-internal,
    # so register it explicitly as RECEIVER_NOT_EXPORTED through bundled ContextCompat.
    const/4 v2, 0x4

    invoke-static {p0, v0, v1, v2}, Ld0/a;->registerReceiver(Landroid/content/Context;Landroid/content/BroadcastReceiver;Landroid/content/IntentFilter;I)Landroid/content/Intent;'''
method2 = method.replace(legacy, replacement, 1)
if legacy in method2:
    raise SystemExit('legacy startup receiver registration remains')
flagged = 'Ld0/a;->registerReceiver(Landroid/content/Context;Landroid/content/BroadcastReceiver;Landroid/content/IntentFilter;I)Landroid/content/Intent;'
if method2.count(flagged) != 1:
    raise SystemExit('flagged ContextCompat receiver registration verification failed')

text2 = text[:method_start] + method2 + text[method_end:]
p.write_text(text2, encoding='utf-8')

compat = root / 'smali/d0/a.smali'
compat_text = compat.read_text(encoding='utf-8') if compat.is_file() else ''
if '.method public static registerReceiver(Landroid/content/Context;Landroid/content/BroadcastReceiver;Landroid/content/IntentFilter;I)Landroid/content/Intent;' not in compat_text:
    raise SystemExit('bundled ContextCompat receiver helper missing')
if 'const/16 v0, 0x21' not in compat_text:
    raise SystemExit('bundled receiver helper does not expose expected API 33 branch')

report = {
    'patch': 'DIRECTIVE_ANDROID14_RECEIVER_FLAGS',
    'file': str(p.relative_to(root)),
    'startup_receiver': 'settingsChangedReceiver',
    'legacy_two_arg_startup_registration_removed': True,
    'receiver_not_exported_flag': '0x4',
    'bundled_contextcompat_register_receiver_used': True,
    'inherited_ticktick_class_namespace_preserved': True,
    'offline_network_permission_boundary_changed': False,
    'authentication_licensing_premium_entitlement_logic_changed': False,
    'system_only_global_receiver_registration_changed': False,
    'purpose': 'Android 13+/14+/16 dynamic receiver startup compatibility'
}
(root / 'DIRECTIVE_ANDROID14_RECEIVER_FLAGS_REPORT.json').write_text(json.dumps(report, indent=2) + '\n', encoding='utf-8')
print(json.dumps(report, sort_keys=True))
