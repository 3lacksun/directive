#!/usr/bin/env python3
from __future__ import annotations

import json
import re
import sys
from pathlib import Path

if len(sys.argv) != 3:
    raise SystemExit('usage: patch_directive_launcher_alias_namespace.py PROJECT_ROOT TARGET_PACKAGE')

root = Path(sys.argv[1]).resolve()
target = sys.argv[2].strip()
if not root.is_dir():
    raise SystemExit(f'missing project root: {root}')
if not re.fullmatch(r'com\.directive\.v\d+', target):
    raise SystemExit(f'unexpected target package: {target}')

manifest = root / 'AndroidManifest.xml'
if not manifest.is_file():
    raise SystemExit('AndroidManifest.xml missing')

m = manifest.read_text(encoding='utf-8')

# LauncherIconChanger builds component names as:
#   context.getPackageName() + '.' + HomeAlia_*
# The decoded app had been migrated to com.directive.vN while the alias component names
# remained com.ticktick.task.HomeAlia_*. That makes every dynamically constructed alias
# point to a component that does not exist in the numbered DIRECTIVE package.
# Rename ONLY activity-alias component identities. Target activities remain the inherited
# com.ticktick.task Java classes because those class/JNI namespaces are intentionally kept.

alias_tag_rx = re.compile(r'<activity-alias\b[^>]*>', re.S)
renamed = []
create_shortcut = False

def patch_alias(tag: str) -> str:
    global create_shortcut
    mm = re.search(r'android:name="(com\.ticktick\.task\.(?:HomeAlia_[^"]+|CreateShortcut))"', tag)
    if not mm:
        return tag
    old = mm.group(1)
    suffix = old[len('com.ticktick.task.'):]
    new = target + '.' + suffix
    renamed.append((old, new))
    if suffix == 'CreateShortcut':
        create_shortcut = True
    return tag[:mm.start(1)] + new + tag[mm.end(1):]

m = alias_tag_rx.sub(lambda x: patch_alias(x.group(0)), m)

home_aliases = [x for x in renamed if '.HomeAlia_' in x[0]]
if len(home_aliases) != 26:
    raise SystemExit(f'expected 26 HomeAlia_* aliases, renamed {len(home_aliases)}')
if not create_shortcut:
    raise SystemExit('CreateShortcut activity-alias was not renamed')
if len(renamed) != 27:
    raise SystemExit(f'expected 27 total alias identities, renamed {len(renamed)}')

# Task affinities are package-instance identities, not Java class names. Keep them isolated
# per numbered DIRECTIVE install so side-by-side test packages cannot share inherited tasks.
affinity_map = {
    'com.ticktick.task.external': target + '.external',
    'com.ticktick.task.second': target + '.second',
    'com.ticktick.task.widget.external': target + '.widget.external',
}
affinity_counts = {}
for old, new in affinity_map.items():
    n = m.count(f'android:taskAffinity="{old}"')
    if n != 1:
        raise SystemExit(f'expected one taskAffinity {old}, found {n}')
    m = m.replace(f'android:taskAffinity="{old}"', f'android:taskAffinity="{new}"')
    affinity_counts[old] = n

manifest.write_text(m, encoding='utf-8')

# Cross-check the inherited launcher manager contract. This is the critical static proof:
# it dynamically uses the runtime package + simple HomeAlia_* suffixes.
launcher = root / 'smali_classes4/yf/t.smali'
if not launcher.is_file():
    raise SystemExit('LauncherIconChanger smali missing')
ls = launcher.read_text(encoding='utf-8')
if 'invoke-virtual {p0}, Landroid/content/Context;->getPackageName()Ljava/lang/String;' not in ls:
    raise SystemExit('launcher manager no longer derives package name dynamically')
for suffix in ['HomeAlia_default', 'HomeAlia_tick', 'HomeAlia_1', 'HomeAlia_12']:
    if f'"{suffix}"' not in ls:
        raise SystemExit(f'launcher suffix missing from manager: {suffix}')

post = manifest.read_text(encoding='utf-8')
for old, new in renamed:
    if f'android:name="{old}"' in post:
        raise SystemExit(f'legacy alias name remains: {old}')
    if f'android:name="{new}"' not in post:
        raise SystemExit(f'new alias name missing: {new}')

# Alias targets must continue to reference actual inherited activity classes.
if post.count('android:targetActivity="com.ticktick.task.activity.MeTaskActivity"') < 26:
    raise SystemExit('inherited MeTaskActivity alias targets were unexpectedly renamed')
if 'android:targetActivity="com.ticktick.task.activity.preference.ShortcutPreferences"' not in post:
    raise SystemExit('CreateShortcut inherited target was unexpectedly renamed')

report = {
    'status': 'PASS',
    'target_package': target,
    'home_launcher_aliases_renamed': len(home_aliases),
    'total_activity_alias_identities_renamed': len(renamed),
    'create_shortcut_alias_renamed': create_shortcut,
    'task_affinities_rebased': affinity_counts,
    'launcher_manager_dynamic_package_contract_verified': True,
    'inherited_activity_class_namespace_preserved': True,
    'auth_billing_entitlement_logic_changed': False,
    'reason': 'Fix numbered-package launcher alias namespace mismatch that can make LauncherIconChanger address nonexistent components during startup/badge handling.'
}
(root / 'DIRECTIVE_LAUNCHER_ALIAS_NAMESPACE_REPORT.json').write_text(json.dumps(report, indent=2) + '\n', encoding='utf-8')
print(json.dumps(report, indent=2))
