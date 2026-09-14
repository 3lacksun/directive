#!/usr/bin/env python3
import argparse
import sys
import xml.etree.ElementTree as ET
from pathlib import Path

ANDROID = '{http://schemas.android.com/apk/res/android}'
HIGH_RISK_PERMISSIONS = {
    'android.permission.REQUEST_INSTALL_PACKAGES',
    'android.permission.MANAGE_EXTERNAL_STORAGE',
    'android.permission.SYSTEM_ALERT_WINDOW',
    'android.permission.WRITE_SETTINGS',
    'android.permission.QUERY_ALL_PACKAGES',
    'android.permission.PACKAGE_USAGE_STATS',
    'android.permission.BIND_ACCESSIBILITY_SERVICE',
    'android.permission.READ_SMS',
    'android.permission.RECEIVE_SMS',
    'android.permission.SEND_SMS',
    'android.permission.CALL_PHONE',
    'android.permission.READ_CALL_LOG',
    'android.permission.WRITE_CALL_LOG',
}
COMPONENT_TAGS = ('activity', 'activity-alias', 'service', 'receiver', 'provider')


def fail(msg: str) -> int:
    print(f'FAIL: {msg}')
    return 1


def parse_allowlist(path: Path):
    if not path.is_file():
        raise ValueError(f'exported component allowlist missing: {path}')
    allowed = set()
    for raw in path.read_text(encoding='utf-8').splitlines():
        line = raw.strip()
        if not line or line.startswith('#'):
            continue
        if ':' not in line:
            raise ValueError(f'invalid allowlist entry: {line}')
        tag, name = line.split(':', 1)
        if tag not in COMPONENT_TAGS or not name:
            raise ValueError(f'invalid allowlist entry: {line}')
        allowed.add((tag, name))
    return allowed


def main() -> int:
    ap = argparse.ArgumentParser(description='Fail-closed DIRECTIVE Android 16 manifest surface gate.')
    ap.add_argument('--manifest-xml', type=Path, required=True,
                    help='Decoded merged APK manifest XML (for example from apkanalyzer manifest print).')
    ap.add_argument('--exported-allowlist', type=Path, required=True,
                    help='Exact allowed exported components, one tag:name per line.')
    args = ap.parse_args()

    if not args.manifest_xml.is_file():
        return fail(f'manifest XML missing: {args.manifest_xml}')
    try:
        allowed = parse_allowlist(args.exported_allowlist)
        root = ET.parse(args.manifest_xml).getroot()
    except (ValueError, ET.ParseError, OSError) as exc:
        return fail(str(exc))

    if root.tag != 'manifest':
        return fail(f'unexpected XML root: {root.tag}')

    requested = {p.get(ANDROID + 'name') for p in root.findall('uses-permission')}
    requested.discard(None)
    blocked = sorted(requested & HIGH_RISK_PERMISSIONS)
    if blocked:
        return fail('high-risk permission(s) present: ' + ','.join(blocked))

    app = root.find('application')
    if app is None:
        return fail('application element missing')
    if app.get(ANDROID + 'debuggable') == 'true':
        return fail('application android:debuggable=true')
    if app.get(ANDROID + 'testOnly') == 'true':
        return fail('application android:testOnly=true')

    exported = set()
    implicit_export = []
    missing_name = []
    for tag in COMPONENT_TAGS:
        for node in app.findall(tag):
            name = node.get(ANDROID + 'name')
            if not name:
                missing_name.append(tag)
                continue
            raw_exported = node.get(ANDROID + 'exported')
            has_filter = node.find('intent-filter') is not None
            if raw_exported is None and has_filter:
                implicit_export.append(f'{tag}:{name}')
            if raw_exported == 'true':
                exported.add((tag, name))

    if missing_name:
        return fail('component(s) missing android:name: ' + ','.join(missing_name))
    if implicit_export:
        return fail('intent-filter component(s) lack explicit android:exported: ' + ','.join(sorted(implicit_export)))

    unexpected = sorted(exported - allowed)
    missing = sorted(allowed - exported)
    if unexpected:
        return fail('unexpected exported component(s): ' + ','.join(f'{t}:{n}' for t, n in unexpected))
    if missing:
        return fail('authorised exported component(s) missing: ' + ','.join(f'{t}:{n}' for t, n in missing))

    print('PASS: DIRECTIVE Android 16 manifest surface gate')
    print(f' exported_components={len(exported)}')
    print(f' requested_permissions={len(requested)}')
    print(' high_risk_permissions=0')
    print(' implicit_exported_intent_filter_components=0')
    return 0


if __name__ == '__main__':
    sys.exit(main())
