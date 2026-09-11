#!/usr/bin/env python3
from __future__ import annotations

import json
import sys
from pathlib import Path

if len(sys.argv) != 2:
    raise SystemExit('usage: patch_directive_android16_activitythread_hook.py <project_root>')

root = Path(sys.argv[1]).resolve()
path = root / 'smali_classes2/com/ticktick/task/TickTickApplicationBase.smali'
if not path.is_file():
    raise SystemExit(f'missing {path}')

src = path.read_text(encoding='utf-8')
start = src.find('.method private initExceptionHandler()V')
if start < 0:
    raise SystemExit('TickTickApplicationBase.initExceptionHandler not found')
end = src.find('.end method', start)
if end < 0:
    raise SystemExit('TickTickApplicationBase.initExceptionHandler end not found')
end += len('.end method')
method = src[start:end]

marker = 'directive_android16_skip_private_activitythread_hook'
if marker in method:
    raise SystemExit('Android 16 private ActivityThread hook patch already present')
needle = '.method private initExceptionHandler()V\n    .locals 4\n'
if method.count(needle) != 1:
    raise SystemExit('unexpected initExceptionHandler locals contract')

# The inherited implementation reflects into ActivityThread.mH and replaces the
# framework Handler callback. That is a non-SDK compatibility layer. DIRECTIVE 12
# already makes its framework-only abort path non-destructive; on Android 16/API 36+
# we additionally avoid installing the private framework hook at all. Preserve the
# inherited behaviour on API 35 and below for binary/behavioural compatibility.
prefix = '''.method private initExceptionHandler()V\n    .locals 4\n\n    sget v0, Landroid/os/Build$VERSION;->SDK_INT:I\n    const/16 v1, 0x24\n    if-lt v0, v1, :directive_legacy_private_activitythread_hook\n\n    :directive_android16_skip_private_activitythread_hook\n    return-void\n\n    :directive_legacy_private_activitythread_hook\n'''
patched_method = method.replace(needle, prefix, 1)
patched = src[:start] + patched_method + src[end:]
path.write_text(patched, encoding='utf-8')

verify = path.read_text(encoding='utf-8')
vm_start = verify.find('.method private initExceptionHandler()V')
vm_end = verify.find('.end method', vm_start)
vm = verify[vm_start:vm_end]
checks = {
    'api36_guard_present': 'const/16 v1, 0x24' in vm and 'if-lt v0, v1, :directive_legacy_private_activitythread_hook' in vm,
    'api36_early_return_present': ':directive_android16_skip_private_activitythread_hook\n    return-void' in vm,
    'legacy_activitythread_hook_preserved': 'Landroid/app/ActivityThread;' in vm or 'ActivityThread' in vm,
}
if not all(checks.values()):
    raise SystemExit(f'post-patch verification failed: {checks}')

report = {
    'status': 'PASS',
    'file': str(path.relative_to(root)),
    'method': 'TickTickApplicationBase.initExceptionHandler()',
    'android16_api': 36,
    'private_activitythread_hook_disabled_on_api36_plus': True,
    'legacy_hook_preserved_through_api35': True,
    'd12_non_destructive_abort_expected': True,
    'inherited_ticktick_class_namespace_preserved': True,
    'authentication_licensing_premium_entitlement_logic_changed': False,
    'offline_network_permission_boundary_changed': False,
    'purpose': 'avoid installing inherited private ActivityThread.mH callback hook on Android 16 while preserving legacy behaviour through API 35',
}
out = root / 'DIRECTIVE_ANDROID16_ACTIVITYTHREAD_HOOK_REMEDIATION_REPORT.json'
out.write_text(json.dumps(report, indent=2) + '\n', encoding='utf-8')
print(json.dumps(report, sort_keys=True))
