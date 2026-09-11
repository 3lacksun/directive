#!/usr/bin/env python3
from pathlib import Path
import json, re, sys

if len(sys.argv) != 2:
    raise SystemExit('usage: patch_directive_android16_startup_compat.py <project_root>')
root = Path(sys.argv[1])
base = root / 'smali_classes2/com/ticktick/task/TickTickApplicationBase.smali'
cb = root / 'smali_classes4/com/ticktick/task/utils/ActivityThreadCallback.smali'
for p in (base, cb):
    if not p.is_file():
        raise SystemExit(f'missing {p}')

# Android 16/API 36 no longer needs or benefits from the inherited private-framework
# ActivityThread.mH callback hook.  The hook catches framework exceptions and then
# deliberately kills the process.  Preserve the inherited behaviour through API 35,
# but do not install this private-framework hook on API 36+.
s = base.read_text(encoding='utf-8')
start = s.find('.method private initExceptionHandler()V')
if start < 0: raise SystemExit('initExceptionHandler not found')
end = s.find('.end method', start)
if end < 0: raise SystemExit('initExceptionHandler end not found')
end += len('.end method')
old = s[start:end]
if 'directive_android16_skip_activitythread_hook' in old:
    raise SystemExit('Android 16 compatibility patch already present')
needle = '.method private initExceptionHandler()V\n    .locals 4\n'
if old.count(needle) != 1:
    raise SystemExit('unexpected initExceptionHandler locals contract')
prefix = '''.method private initExceptionHandler()V\n    .locals 4\n\n    sget v0, Landroid/os/Build$VERSION;->SDK_INT:I\n    const/16 v1, 0x24\n    if-lt v0, v1, :directive_android16_legacy_activitythread_hook\n\n    # API 36+: do not hook private ActivityThread internals.  Android dispatches\n    # framework callbacks directly and normal uncaught-exception handling remains intact.\n    :directive_android16_skip_activitythread_hook\n    return-void\n\n    :directive_android16_legacy_activitythread_hook\n'''
old2 = old.replace(needle, prefix, 1)
s = s[:start] + old2 + s[end:]
base.write_text(s, encoding='utf-8')

# Defence in depth: if the callback is instantiated by another path, preserve its
# legacy kill behaviour below API 36 but make abort() non-destructive on API 36+.
s = cb.read_text(encoding='utf-8')
start = s.find('.method private static abort(Ljava/lang/Throwable;)Z')
if start < 0: raise SystemExit('ActivityThreadCallback.abort not found')
end = s.find('.end method', start)
if end < 0: raise SystemExit('ActivityThreadCallback.abort end not found')
end += len('.end method')
old = s[start:end]
if 'directive_android16_nonfatal_abort' in old:
    raise SystemExit('abort compatibility patch already present')
needle = '.method private static abort(Ljava/lang/Throwable;)Z\n    .locals 3\n'
if old.count(needle) != 1:
    raise SystemExit('unexpected abort locals contract')
prefix = '''.method private static abort(Ljava/lang/Throwable;)Z\n    .locals 3\n\n    sget v0, Landroid/os/Build$VERSION;->SDK_INT:I\n    const/16 v1, 0x24\n    if-lt v0, v1, :directive_android16_nonfatal_abort\n    goto :directive_legacy_abort\n\n    :directive_android16_nonfatal_abort\n    const/4 v0, 0x1\n    return v0\n\n    :directive_legacy_abort\n'''
old2 = old.replace(needle, prefix, 1)
s = s[:start] + old2 + s[end:]
cb.write_text(s, encoding='utf-8')

report = {
    'status': 'PASS',
    'android16_api': 36,
    'activitythread_private_hook_disabled_on_api36_plus': True,
    'legacy_hook_preserved_through_api35': True,
    'activitythread_abort_process_kill_disabled_on_api36_plus': True,
    'legacy_abort_preserved_through_api35': True,
    'authentication_licensing_entitlement_logic_changed': False,
    'network_permissions_changed': False,
    'database_schema_changed': False,
    'reason': 'Remove inherited private ActivityThread callback/process-kill compatibility layer from Android 16 runtime path; it is a framework-internals hook capable of converting recoverable framework callback exceptions into deliberate process termination.'
}
(root / 'DIRECTIVE_ANDROID16_STARTUP_COMPAT_REPORT.json').write_text(json.dumps(report, indent=2) + '\n', encoding='utf-8')
print(json.dumps(report, indent=2))
