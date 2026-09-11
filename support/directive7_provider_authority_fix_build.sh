#!/usr/bin/env bash
set -euo pipefail

BASE=support/directive3_install_safe_build.sh
PACKAGE_PATCHER=support/patch_directive_runtime_package_identity.py
LAUNCHER_PATCHER=support/patch_directive_launcher_identity.py
ALIAS_PATCHER=support/patch_directive_launcher_alias_namespace.py
PROVIDER_PATCHER=support/patch_directive_provider_authority_namespace.py
GEN=/tmp/directive7_generated_build.sh

for f in "$BASE" "$PACKAGE_PATCHER" "$LAUNCHER_PATCHER" "$ALIAS_PATCHER" "$PROVIDER_PATCHER"; do test -s "$f"; done

python3 - "$BASE" "$GEN" <<'PY'
from pathlib import Path
import sys
src = Path(sys.argv[1]).read_text(encoding='utf-8')
for old, new in (
    ('com.directive.v3', 'com.directive.v7'),
    ('DIRECTIVE_3', 'DIRECTIVE_7'),
    ('DIRECTIVE 3', 'DIRECTIVE 7'),
    ('3.0.0', '7.0.0'),
    ('8300', '8700'),
    ('directive3-test.jks', 'directive7-test.jks'),
    ('directive3test', 'directive7test'),
):
    src = src.replace(old, new)
needle = 'cp "$PROJECT_ROOT/DIRECTIVE_INSTALL_COLLISION_REMEDIATION_REPORT.json" out-v8/evidence/'
insert = '''python3 support/patch_directive_runtime_package_identity.py "$PROJECT_ROOT" com.directive.v7 | tee out-v8/evidence/RUNTIME_PACKAGE_IDENTITY_REMEDIATION.txt
cp "$PROJECT_ROOT/DIRECTIVE_RUNTIME_PACKAGE_IDENTITY_REMEDIATION_REPORT.json" out-v8/evidence/
python3 support/patch_directive_launcher_alias_namespace.py "$PROJECT_ROOT" com.directive.v7 | tee out-v8/evidence/LAUNCHER_ALIAS_NAMESPACE_REMEDIATION.txt
cp "$PROJECT_ROOT/DIRECTIVE_LAUNCHER_ALIAS_NAMESPACE_REPORT.json" out-v8/evidence/
python3 support/patch_directive_provider_authority_namespace.py "$PROJECT_ROOT" com.directive.v7 | tee out-v8/evidence/PROVIDER_AUTHORITY_NAMESPACE_REMEDIATION.txt
cp "$PROJECT_ROOT/DIRECTIVE_PROVIDER_AUTHORITY_NAMESPACE_REPORT.json" out-v8/evidence/
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

APK=out-v8/DIRECTIVE_7_7.0.0_INSTALL_SAFE_TEST.apk
test -s "$APK"

grep -Fq '"critical_variant_discriminator_fixed": true' out-v8/evidence/DIRECTIVE_RUNTIME_PACKAGE_IDENTITY_REMEDIATION_REPORT.json
grep -Fq '"launcher_manager_dynamic_package_contract_verified": true' out-v8/evidence/DIRECTIVE_LAUNCHER_ALIAS_NAMESPACE_REPORT.json
grep -Fq '"provider_runtime_authority_contract_verified": true' out-v8/evidence/DIRECTIVE_PROVIDER_AUTHORITY_NAMESPACE_REPORT.json
grep -Fq '"total_replacements": 14' out-v8/evidence/DIRECTIVE_PROVIDER_AUTHORITY_NAMESPACE_REPORT.json
grep -Fq '"inherited_provider_class_namespace_preserved": true' out-v8/evidence/DIRECTIVE_PROVIDER_AUTHORITY_NAMESPACE_REPORT.json
grep -Fq '"inherited_ticktick_launcher_replaced": true' out-v8/evidence/DIRECTIVE_LAUNCHER_IDENTITY_REMEDIATION_REPORT.json

grep -Fq "package: name='com.directive.v7' versionCode='8700' versionName='7.0.0'" out-v8/evidence/APK_BADGING.txt
grep -Fq "application-label:'DIRECTIVE 7'" out-v8/evidence/APK_BADGING.txt
! grep -Eq 'android.permission.(INTERNET|ACCESS_NETWORK_STATE|ACCESS_WIFI_STATE|CHANGE_NETWORK_STATE|CHANGE_WIFI_STATE)' out-v8/evidence/APK_PERMISSIONS.txt

BT="${ANDROID_HOME:-/usr/local/lib/android/sdk}/build-tools/${BUILD_TOOLS_VERSION:-35.0.0}"
"$BT/aapt" dump xmltree "$APK" AndroidManifest.xml > out-v8/evidence/APK_MANIFEST_XMLTREE.txt
for authority in com.directive.v7.provider.weardataprovider com.directive.v7.provider.TaskSuggestionProvider; do
  grep -Fq "$authority" out-v8/evidence/APK_MANIFEST_XMLTREE.txt
done
for alias in HomeAlia_default HomeAlia_tick HomeAlia_1 HomeAlia_12 CreateShortcut; do
  grep -Fq "com.directive.v7.$alias" out-v8/evidence/APK_MANIFEST_XMLTREE.txt
done

# Inspect final DEX string tables so the legacy app-owned provider authorities cannot silently survive repackaging.
for dex in classes.dex classes2.dex classes3.dex classes4.dex classes5.dex classes6.dex; do
  unzip -p "$APK" "$dex" 2>/dev/null || true
done | strings > out-v8/evidence/APK_DEX_STRINGS.txt
! grep -Fq 'com.ticktick.task.provider.TaskSuggestionProvider' out-v8/evidence/APK_DEX_STRINGS.txt
! grep -Fq 'content://com.ticktick.task.provider.weardataprovider/query_task' out-v8/evidence/APK_DEX_STRINGS.txt
grep -Fq 'com.directive.v7.provider.TaskSuggestionProvider' out-v8/evidence/APK_DEX_STRINGS.txt
grep -Fq 'content://com.directive.v7.provider.weardataprovider/query_task' out-v8/evidence/APK_DEX_STRINGS.txt

printf '%s\n' \
  'build=PASS' \
  'static_verification=PASS' \
  'package=com.directive.v7' \
  'label=DIRECTIVE 7' \
  'version=7.0.0/8700' \
  'runtime_package_identity=PASS' \
  'launcher_alias_namespace=PASS' \
  'provider_authority_namespace=PASS' \
  'inherited_java_jni_namespace=PRESERVED' \
  'offline_no_network_permission_boundary=PRESERVED' \
  'auth_billing_entitlement_logic=UNCHANGED' \
  'physical_samsung_android16_acceptance=UNEXECUTED' \
  'final_go=false' > out-v8/evidence/DIRECTIVE7_STATUS.txt

sha256sum "$APK" | tee out-v8/evidence/DIRECTIVE7_SHA256.txt
echo 'PASS: DIRECTIVE 7 provider-authority namespace-remediated APK built and statically verified'
