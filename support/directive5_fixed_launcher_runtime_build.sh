#!/usr/bin/env bash
set -euo pipefail

# DIRECTIVE 5 is a side-by-side diagnostic/runtime candidate.
# It preserves the inherited Java/JNI namespace while making Android package-owned
# launcher aliases coherent with the numbered applicationId and disabling the inherited
# cosmetic launcher-icon mutator that intentionally calls System.exit().

BUILD_TOOLS_VERSION="${BUILD_TOOLS_VERSION:-35.0.0}"
ANDROID_HOME="${ANDROID_HOME:-/usr/local/lib/android/sdk}"
export BUILD_TOOLS_VERSION ANDROID_HOME ANDROID_SDK_ROOT="$ANDROID_HOME"

BASE=support/directive3_install_safe_build.sh
PACKAGE_PATCHER=support/patch_directive_runtime_package_identity.py
LAUNCHER_ART_PATCHER=support/patch_directive_launcher_identity.py
FIXED_LAUNCHER_PATCHER=support/patch_directive_fixed_launcher_runtime.py
GEN=/tmp/directive5_generated_build.sh

for f in "$BASE" "$PACKAGE_PATCHER" "$LAUNCHER_ART_PATCHER" "$FIXED_LAUNCHER_PATCHER"; do
  test -s "$f"
done

python3 - "$BASE" "$GEN" <<'PY'
from pathlib import Path
import sys
src = Path(sys.argv[1]).read_text(encoding='utf-8')
for old, new in (
    ('com.directive.v3', 'com.directive.v5'),
    ('DIRECTIVE_3', 'DIRECTIVE_5'),
    ('DIRECTIVE 3', 'DIRECTIVE 5'),
    ('3.0.0', '5.0.0'),
    ('8300', '8500'),
):
    src = src.replace(old, new)
needle = 'cp "$PROJECT_ROOT/DIRECTIVE_INSTALL_COLLISION_REMEDIATION_REPORT.json" out-v8/evidence/'
insert = '''python3 support/patch_directive_runtime_package_identity.py "$PROJECT_ROOT" com.directive.v5 | tee out-v8/evidence/RUNTIME_PACKAGE_IDENTITY_REMEDIATION.txt
cp "$PROJECT_ROOT/DIRECTIVE_RUNTIME_PACKAGE_IDENTITY_REMEDIATION_REPORT.json" out-v8/evidence/
python3 support/patch_directive_launcher_identity.py "$PROJECT_ROOT" | tee out-v8/evidence/LAUNCHER_IDENTITY_REMEDIATION.txt
cp "$PROJECT_ROOT/DIRECTIVE_LAUNCHER_IDENTITY_REMEDIATION_REPORT.json" out-v8/evidence/
python3 support/patch_directive_fixed_launcher_runtime.py "$PROJECT_ROOT" com.directive.v5 | tee out-v8/evidence/FIXED_LAUNCHER_RUNTIME_REMEDIATION.txt
cp "$PROJECT_ROOT/DIRECTIVE_FIXED_LAUNCHER_RUNTIME_REPORT.json" out-v8/evidence/
'''
if src.count(needle) != 1:
    raise SystemExit(f'expected one build-chain insertion point, found {src.count(needle)}')
src = src.replace(needle, insert + needle, 1)
Path(sys.argv[2]).write_text(src, encoding='utf-8')
PY
chmod +x "$GEN"

for token in \
  'com.directive.v5' \
  'DIRECTIVE 5' \
  '5.0.0' \
  '8500' \
  'patch_directive_runtime_package_identity.py' \
  'patch_directive_launcher_identity.py' \
  'patch_directive_fixed_launcher_runtime.py'; do
  grep -Fq "$token" "$GEN"
done

bash "$GEN"

test -s out-v8/DIRECTIVE_5_5.0.0_INSTALL_SAFE_TEST.apk

grep -Fq '"critical_variant_discriminator_fixed": true' out-v8/evidence/DIRECTIVE_RUNTIME_PACKAGE_IDENTITY_REMEDIATION_REPORT.json
grep -Fq '"inherited_ticktick_launcher_replaced": true' out-v8/evidence/DIRECTIVE_LAUNCHER_IDENTITY_REMEDIATION_REPORT.json
grep -Fq '"launcher_aliases_migrated": 26' out-v8/evidence/DIRECTIVE_FIXED_LAUNCHER_RUNTIME_REPORT.json
grep -Fq '"launcher_mutator_system_exit_removed": true' out-v8/evidence/DIRECTIVE_FIXED_LAUNCHER_RUNTIME_REPORT.json
grep -Fq '"authentication_or_entitlement_logic_modified": false' out-v8/evidence/DIRECTIVE_FIXED_LAUNCHER_RUNTIME_REPORT.json

# The packaged manifest must expose the numbered launcher alias, while the actual inherited
# Activity/Application classes remain in their original Java/JNI namespace.
"$ANDROID_HOME/build-tools/$BUILD_TOOLS_VERSION/aapt" dump xmltree \
  out-v8/DIRECTIVE_5_5.0.0_INSTALL_SAFE_TEST.apk AndroidManifest.xml \
  > out-v8/evidence/APK_MANIFEST_XMLTREE.txt
grep -Fq 'com.directive.v5.HomeAlia_default' out-v8/evidence/APK_MANIFEST_XMLTREE.txt
grep -Fq 'com.ticktick.task.activity.MeTaskActivity' out-v8/evidence/APK_MANIFEST_XMLTREE.txt
! grep -Fq 'com.ticktick.task.HomeAlia_default' out-v8/evidence/APK_MANIFEST_XMLTREE.txt

printf '%s\n' \
  'runtime_package_identity_remediation=PASS' \
  'launcher_alias_package_migration=PASS_26_OF_26' \
  'fixed_directive_launcher_identity=PASS' \
  'dynamic_launcher_icon_mutation=DISABLED' \
  'launcher_icon_system_exit=REMOVED_FROM_MUTATOR' \
  'internal_com.ticktick.task_JNI_namespace=PRESERVED' \
  'billing_auth_entitlement_logic=UNCHANGED' \
  'physical_samsung_android16_acceptance=UNEXECUTED' \
  'final_go=false' \
  > out-v8/evidence/DIRECTIVE5_RUNTIME_FIX_STATUS.txt

sha256sum out-v8/DIRECTIVE_5_5.0.0_INSTALL_SAFE_TEST.apk | tee out-v8/evidence/DIRECTIVE5_SHA256.txt

echo 'PASS: DIRECTIVE 5 fixed-launcher runtime candidate built and statically verified'
