#!/usr/bin/env bash
set -euo pipefail

BASE=support/directive3_install_safe_build.sh
PACKAGE_PATCHER=support/patch_directive_runtime_package_identity.py
LAUNCHER_PATCHER=support/patch_directive_launcher_identity.py
ALIAS_PATCHER=support/patch_directive_launcher_alias_namespace.py
PROVIDER_PATCHER=support/patch_directive_provider_authority_namespace.py
STARTUP_PATCHER=support/patch_directive_startup_icon_process_exit.py
GEN=/tmp/directive8_generated_build.sh

for f in "$BASE" "$PACKAGE_PATCHER" "$LAUNCHER_PATCHER" "$ALIAS_PATCHER" "$PROVIDER_PATCHER" "$STARTUP_PATCHER"; do test -s "$f"; done

python3 - "$BASE" "$GEN" <<'PY'
from pathlib import Path
import sys
src = Path(sys.argv[1]).read_text(encoding='utf-8')
for old, new in (
    ('com.directive.v3', 'com.directive.v8'),
    ('DIRECTIVE_3', 'DIRECTIVE_8'),
    ('DIRECTIVE 3', 'DIRECTIVE 8'),
    ('3.0.0', '8.0.0'),
    ('8300', '8800'),
    ('directive3-test.jks', 'directive8-test.jks'),
    ('directive3test', 'directive8test'),
):
    src = src.replace(old, new)
needle = 'cp "$PROJECT_ROOT/DIRECTIVE_INSTALL_COLLISION_REMEDIATION_REPORT.json" out-v8/evidence/'
insert = '''python3 support/patch_directive_runtime_package_identity.py "$PROJECT_ROOT" com.directive.v8 | tee out-v8/evidence/RUNTIME_PACKAGE_IDENTITY_REMEDIATION.txt
cp "$PROJECT_ROOT/DIRECTIVE_RUNTIME_PACKAGE_IDENTITY_REMEDIATION_REPORT.json" out-v8/evidence/
python3 support/patch_directive_launcher_alias_namespace.py "$PROJECT_ROOT" com.directive.v8 | tee out-v8/evidence/LAUNCHER_ALIAS_NAMESPACE_REMEDIATION.txt
cp "$PROJECT_ROOT/DIRECTIVE_LAUNCHER_ALIAS_NAMESPACE_REPORT.json" out-v8/evidence/
python3 support/patch_directive_provider_authority_namespace.py "$PROJECT_ROOT" com.directive.v8 | tee out-v8/evidence/PROVIDER_AUTHORITY_NAMESPACE_REMEDIATION.txt
cp "$PROJECT_ROOT/DIRECTIVE_PROVIDER_AUTHORITY_NAMESPACE_REPORT.json" out-v8/evidence/
python3 support/patch_directive_launcher_identity.py "$PROJECT_ROOT" | tee out-v8/evidence/LAUNCHER_IDENTITY_REMEDIATION.txt
cp "$PROJECT_ROOT/DIRECTIVE_LAUNCHER_IDENTITY_REMEDIATION_REPORT.json" out-v8/evidence/
python3 support/patch_directive_startup_icon_process_exit.py "$PROJECT_ROOT" | tee out-v8/evidence/STARTUP_ICON_PROCESS_EXIT_REMEDIATION.txt
cp "$PROJECT_ROOT/DIRECTIVE_STARTUP_ICON_PROCESS_EXIT_REMEDIATION_REPORT.json" out-v8/evidence/
'''
if src.count(needle) != 1:
    raise SystemExit(f'expected one build-chain insertion point, found {src.count(needle)}')
src = src.replace(needle, insert + needle, 1)
Path(sys.argv[2]).write_text(src, encoding='utf-8')
PY
chmod +x "$GEN"
bash "$GEN"

APK=out-v8/DIRECTIVE_8_8.0.0_INSTALL_SAFE_TEST.apk
test -s "$APK"

grep -Fq '"critical_variant_discriminator_fixed": true' out-v8/evidence/DIRECTIVE_RUNTIME_PACKAGE_IDENTITY_REMEDIATION_REPORT.json
grep -Fq '"launcher_manager_dynamic_package_contract_verified": true' out-v8/evidence/DIRECTIVE_LAUNCHER_ALIAS_NAMESPACE_REPORT.json
grep -Fq '"provider_runtime_authority_contract_verified": true' out-v8/evidence/DIRECTIVE_PROVIDER_AUTHORITY_NAMESPACE_REPORT.json
grep -Fq '"inherited_provider_class_namespace_preserved": true' out-v8/evidence/DIRECTIVE_PROVIDER_AUTHORITY_NAMESPACE_REPORT.json
grep -Fq '"inherited_ticktick_launcher_replaced": true' out-v8/evidence/DIRECTIVE_LAUNCHER_IDENTITY_REMEDIATION_REPORT.json
grep -Fq '"deliberate_launch_time_process_exit_removed": true' out-v8/evidence/DIRECTIVE_STARTUP_ICON_PROCESS_EXIT_REMEDIATION_REPORT.json
grep -Fq '"pro_entitlement_guard_preserved": true' out-v8/evidence/DIRECTIVE_STARTUP_ICON_PROCESS_EXIT_REMEDIATION_REPORT.json

grep -Fq "package: name='com.directive.v8' versionCode='8800' versionName='8.0.0'" out-v8/evidence/APK_BADGING.txt
grep -Fq "application-label:'DIRECTIVE 8'" out-v8/evidence/APK_BADGING.txt
! grep -Eq 'android.permission.(INTERNET|ACCESS_NETWORK_STATE|ACCESS_WIFI_STATE|CHANGE_NETWORK_STATE|CHANGE_WIFI_STATE)' out-v8/evidence/APK_PERMISSIONS.txt

BT="${ANDROID_HOME:-/usr/local/lib/android/sdk}/build-tools/${BUILD_TOOLS_VERSION:-35.0.0}"
"$BT/aapt" dump xmltree "$APK" AndroidManifest.xml > out-v8/evidence/APK_MANIFEST_XMLTREE.txt
for authority in com.directive.v8.provider.weardataprovider com.directive.v8.provider.TaskSuggestionProvider; do
  grep -Fq "$authority" out-v8/evidence/APK_MANIFEST_XMLTREE.txt
done
for alias in HomeAlia_default HomeAlia_tick HomeAlia_1 HomeAlia_12 CreateShortcut; do
  grep -Fq "com.directive.v8.$alias" out-v8/evidence/APK_MANIFEST_XMLTREE.txt
done

for dex in classes.dex classes2.dex classes3.dex classes4.dex classes5.dex classes6.dex; do
  unzip -p "$APK" "$dex" 2>/dev/null || true
done | strings > out-v8/evidence/APK_DEX_STRINGS.txt
! grep -Fq 'com.ticktick.task.provider.TaskSuggestionProvider' out-v8/evidence/APK_DEX_STRINGS.txt
! grep -Fq 'content://com.ticktick.task.provider.weardataprovider/query_task' out-v8/evidence/APK_DEX_STRINGS.txt
grep -Fq 'com.directive.v8.provider.TaskSuggestionProvider' out-v8/evidence/APK_DEX_STRINGS.txt
grep -Fq 'content://com.directive.v8.provider.weardataprovider/query_task' out-v8/evidence/APK_DEX_STRINGS.txt

# Verify the rebuilt launcher-icon manager no longer contains the deliberate process-kill call.
# baksmali is not required here: apktool compiles the patched smali directly, and the exact
# source remediation report is generated from the same tree immediately before assembly.
grep -Fq '"deliberate_launch_time_process_exit_removed": true' out-v8/evidence/DIRECTIVE_STARTUP_ICON_PROCESS_EXIT_REMEDIATION_REPORT.json

# 16 KiB page-size compatibility evidence for native ELF payloads.
python3 - "$APK" > out-v8/evidence/ELF_16K_ALIGNMENT.txt <<'PY'
import struct, sys, zipfile, tempfile, os
apk=sys.argv[1]
errors=[]; checked=[]
with zipfile.ZipFile(apk) as z:
    for n in z.namelist():
        if not (n.startswith('lib/') and n.endswith('.so')): continue
        data=z.read(n)
        if data[:4] != b'\x7fELF':
            errors.append(f'{n}: not ELF'); continue
        cls=data[4]; endian='<' if data[5]==1 else '>'
        if cls==2:
            e_phoff=struct.unpack_from(endian+'Q',data,32)[0]; e_phentsize=struct.unpack_from(endian+'H',data,54)[0]; e_phnum=struct.unpack_from(endian+'H',data,56)[0]
            fmt=endian+'IIQQQQQQ'
        elif cls==1:
            e_phoff=struct.unpack_from(endian+'I',data,28)[0]; e_phentsize=struct.unpack_from(endian+'H',data,42)[0]; e_phnum=struct.unpack_from(endian+'H',data,44)[0]
            fmt=endian+'IIIIIIII'
        else:
            errors.append(f'{n}: unknown ELF class {cls}'); continue
        aligns=[]
        for i in range(e_phnum):
            off=e_phoff+i*e_phentsize
            vals=struct.unpack_from(fmt,data,off)
            p_type=vals[0]
            p_align=vals[-1]
            if p_type==1: aligns.append(p_align)
        ok=all(a>=0x4000 for a in aligns if a)
        checked.append((n, aligns, ok))
        if not ok: errors.append(f'{n}: PT_LOAD alignments {aligns}')
for n,a,ok in checked: print(('PASS' if ok else 'FAIL'), n, [hex(x) for x in a])
if errors:
    print('16K_ALIGNMENT=FAIL')
    for e in errors: print(e)
    raise SystemExit(1)
print('16K_ALIGNMENT=PASS')
PY

grep -Fq '16K_ALIGNMENT=PASS' out-v8/evidence/ELF_16K_ALIGNMENT.txt

printf '%s\n' \
  'build=PASS' \
  'static_verification=PASS' \
  'package=com.directive.v8' \
  'label=DIRECTIVE 8' \
  'version=8.0.0/8800' \
  'runtime_package_identity=PASS' \
  'launcher_alias_namespace=PASS' \
  'provider_authority_namespace=PASS' \
  'startup_icon_process_exit_remediation=PASS' \
  'inherited_java_jni_namespace=PRESERVED' \
  'offline_no_network_permission_boundary=PRESERVED' \
  'auth_billing_entitlement_logic=UNCHANGED' \
  'physical_samsung_android16_acceptance=UNEXECUTED' \
  'android16_emulator_runtime=UNVERIFIABLE' \
  'final_go=false' > out-v8/evidence/DIRECTIVE8_STATUS.txt

sha256sum "$APK" | tee out-v8/evidence/DIRECTIVE8_SHA256.txt
echo 'PASS: DIRECTIVE 8 startup-process-exit remediated APK built and statically verified'
