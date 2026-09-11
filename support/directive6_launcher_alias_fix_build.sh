#!/usr/bin/env bash
set -euo pipefail

# DIRECTIVE 6 is the next physical Android 16 candidate.
# It preserves the inherited Java/JNI class namespace but fixes the numbered-package
# launcher alias namespace contract that remained inconsistent in D2-D4.

BASE=support/directive3_install_safe_build.sh
PACKAGE_PATCHER=support/patch_directive_runtime_package_identity.py
LAUNCHER_PATCHER=support/patch_directive_launcher_identity.py
ALIAS_PATCHER=support/patch_directive_launcher_alias_namespace.py
GEN=/tmp/directive6_generated_build.sh

for f in "$BASE" "$PACKAGE_PATCHER" "$LAUNCHER_PATCHER" "$ALIAS_PATCHER"; do test -s "$f"; done

python3 - "$BASE" "$GEN" <<'PY'
from pathlib import Path
import sys
src = Path(sys.argv[1]).read_text(encoding='utf-8')
for old, new in (
    ('com.directive.v3', 'com.directive.v6'),
    ('DIRECTIVE_3', 'DIRECTIVE_6'),
    ('DIRECTIVE 3', 'DIRECTIVE 6'),
    ('3.0.0', '6.0.0'),
    ('8300', '8600'),
    ('directive3-test.jks', 'directive6-test.jks'),
    ('directive3test', 'directive6test'),
):
    src = src.replace(old, new)
needle = 'cp "$PROJECT_ROOT/DIRECTIVE_INSTALL_COLLISION_REMEDIATION_REPORT.json" out-v8/evidence/'
insert = '''python3 support/patch_directive_runtime_package_identity.py "$PROJECT_ROOT" com.directive.v6 | tee out-v8/evidence/RUNTIME_PACKAGE_IDENTITY_REMEDIATION.txt
cp "$PROJECT_ROOT/DIRECTIVE_RUNTIME_PACKAGE_IDENTITY_REMEDIATION_REPORT.json" out-v8/evidence/
python3 support/patch_directive_launcher_alias_namespace.py "$PROJECT_ROOT" com.directive.v6 | tee out-v8/evidence/LAUNCHER_ALIAS_NAMESPACE_REMEDIATION.txt
cp "$PROJECT_ROOT/DIRECTIVE_LAUNCHER_ALIAS_NAMESPACE_REPORT.json" out-v8/evidence/
python3 support/patch_directive_launcher_identity.py "$PROJECT_ROOT" | tee out-v8/evidence/LAUNCHER_IDENTITY_REMEDIATION.txt
cp "$PROJECT_ROOT/DIRECTIVE_LAUNCHER_IDENTITY_REMEDIATION_REPORT.json" out-v8/evidence/
'''
if src.count(needle) != 1:
    raise SystemExit(f'expected one build-chain insertion point, found {src.count(needle)}')
src = src.replace(needle, insert + needle, 1)
Path(sys.argv[2]).write_text(src, encoding='utf-8')
PY
chmod +x "$GEN"

bash "$GEN"

APK=out-v8/DIRECTIVE_6_6.0.0_INSTALL_SAFE_TEST.apk
test -s "$APK"

grep -Fq '"critical_variant_discriminator_fixed": true' out-v8/evidence/DIRECTIVE_RUNTIME_PACKAGE_IDENTITY_REMEDIATION_REPORT.json
grep -Fq '"home_launcher_aliases_renamed": 26' out-v8/evidence/DIRECTIVE_LAUNCHER_ALIAS_NAMESPACE_REPORT.json
grep -Fq '"total_activity_alias_identities_renamed": 27' out-v8/evidence/DIRECTIVE_LAUNCHER_ALIAS_NAMESPACE_REPORT.json
grep -Fq '"launcher_manager_dynamic_package_contract_verified": true' out-v8/evidence/DIRECTIVE_LAUNCHER_ALIAS_NAMESPACE_REPORT.json
grep -Fq '"inherited_activity_class_namespace_preserved": true' out-v8/evidence/DIRECTIVE_LAUNCHER_ALIAS_NAMESPACE_REPORT.json
grep -Fq '"inherited_ticktick_launcher_replaced": true' out-v8/evidence/DIRECTIVE_LAUNCHER_IDENTITY_REMEDIATION_REPORT.json

grep -Fq "package: name='com.directive.v6' versionCode='8600' versionName='6.0.0'" out-v8/evidence/APK_BADGING.txt
grep -Fq "application-label:'DIRECTIVE 6'" out-v8/evidence/APK_BADGING.txt
! grep -Eq 'android.permission.(INTERNET|ACCESS_NETWORK_STATE|ACCESS_WIFI_STATE|CHANGE_NETWORK_STATE|CHANGE_WIFI_STATE)' out-v8/evidence/APK_PERMISSIONS.txt
grep -Fq 'android.permission.READ_CALENDAR' out-v8/evidence/APK_PERMISSIONS.txt
grep -Fq 'android.permission.WRITE_CALENDAR' out-v8/evidence/APK_PERMISSIONS.txt

# Verify the built binary manifest contains the package-owned launcher alias names.
BT="${ANDROID_HOME:-/usr/local/lib/android/sdk}/build-tools/${BUILD_TOOLS_VERSION:-35.0.0}"
"$BT/aapt" dump xmltree "$APK" AndroidManifest.xml > out-v8/evidence/APK_MANIFEST_XMLTREE.txt
for alias in HomeAlia_default HomeAlia_tick HomeAlia_1 HomeAlia_12 CreateShortcut; do
  grep -Fq "com.directive.v6.$alias" out-v8/evidence/APK_MANIFEST_XMLTREE.txt
done
! grep -Fq 'com.ticktick.task.HomeAlia_default' out-v8/evidence/APK_MANIFEST_XMLTREE.txt

printf '%s\n' \
  'build=PASS' \
  'static_verification=PASS' \
  'package=com.directive.v6' \
  'label=DIRECTIVE 6' \
  'version=6.0.0/8600' \
  'runtime_package_identity=PASS' \
  'launcher_alias_namespace=PASS' \
  'launcher_aliases_rebased=26' \
  'shortcut_alias_rebased=PASS' \
  'task_affinity_namespace=PASS' \
  'inherited_java_jni_namespace=PRESERVED' \
  'auth_billing_entitlement_logic=UNCHANGED' \
  'physical_samsung_android16_acceptance=UNEXECUTED' \
  'final_go=false' > out-v8/evidence/DIRECTIVE6_STATUS.txt

sha256sum "$APK" | tee out-v8/evidence/DIRECTIVE6_SHA256.txt

echo 'PASS: DIRECTIVE 6 launcher-alias namespace-remediated APK built and statically verified'
