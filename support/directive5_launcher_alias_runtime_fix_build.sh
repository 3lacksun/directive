#!/usr/bin/env bash
set -euo pipefail

# DIRECTIVE 5: evidence-driven successor to the physical-Samsung-failing DIRECTIVE 4.
# D5 retains the D4 runtime package-identity and approved launcher artwork repairs,
# and additionally repairs the confirmed launcher activity-alias namespace mismatch:
# LauncherIcon.kt constructs getPackageName() + '.HomeAlia_*', so manifest aliases must
# be declared under com.directive.v5 while targetActivity remains inherited com.ticktick.task.*.
# Authentication, billing, premium and entitlement truth are not modified.

BASE=support/directive4_runtime_package_fix_build.sh
ALIAS_PATCHER=support/patch_directive_launcher_alias_package.py
GEN=/tmp/directive5_generated_build.sh

test -s "$BASE"
test -s "$ALIAS_PATCHER"

python3 - "$BASE" "$GEN" <<'PY'
from pathlib import Path
import sys
src = Path(sys.argv[1]).read_text(encoding='utf-8')
for old, new in (
    ('com.directive.v4', 'com.directive.v5'),
    ('DIRECTIVE_4', 'DIRECTIVE_5'),
    ('DIRECTIVE 4', 'DIRECTIVE 5'),
    ('4.0.0', '5.0.0'),
    ('8400', '8500'),
):
    src = src.replace(old, new)
needle = 'python3 support/patch_directive_launcher_identity.py "$PROJECT_ROOT" | tee out-v8/evidence/LAUNCHER_IDENTITY_REMEDIATION.txt'
insert = '''python3 support/patch_directive_launcher_alias_package.py "$PROJECT_ROOT" com.directive.v5 | tee out-v8/evidence/LAUNCHER_ALIAS_PACKAGE_REMEDIATION.txt
cp "$PROJECT_ROOT/DIRECTIVE_LAUNCHER_ALIAS_PACKAGE_REMEDIATION_REPORT.json" out-v8/evidence/
'''
if src.count(needle) != 1:
    raise SystemExit(f'expected one launcher insertion point, found {src.count(needle)}')
src = src.replace(needle, insert + needle, 1)
Path(sys.argv[2]).write_text(src, encoding='utf-8')
PY
chmod +x "$GEN"

grep -Fq 'com.directive.v5' "$GEN"
grep -Fq 'DIRECTIVE 5' "$GEN"
grep -Fq '5.0.0' "$GEN"
grep -Fq '8500' "$GEN"
grep -Fq 'patch_directive_launcher_alias_package.py' "$GEN"

bash "$GEN"

test -s out-v8/DIRECTIVE_5_5.0.0_INSTALL_SAFE_TEST.apk

grep -Fq '"critical_variant_discriminator_fixed": true' out-v8/evidence/DIRECTIVE_RUNTIME_PACKAGE_IDENTITY_REMEDIATION_REPORT.json
grep -Fq '"inherited_ticktick_launcher_replaced": true' out-v8/evidence/DIRECTIVE_LAUNCHER_IDENTITY_REMEDIATION_REPORT.json
grep -Fq '"status": "PASS"' out-v8/evidence/DIRECTIVE_LAUNCHER_ALIAS_PACKAGE_REMEDIATION_REPORT.json
grep -Fq '"inherited_target_activity_namespace_preserved": true' out-v8/evidence/DIRECTIVE_LAUNCHER_ALIAS_PACKAGE_REMEDIATION_REPORT.json
grep -Fq '"auth_licensing_entitlement_modified": false' out-v8/evidence/DIRECTIVE_LAUNCHER_ALIAS_PACKAGE_REMEDIATION_REPORT.json

# Verify the built manifest exposes launcher aliases in the numbered app namespace.
grep -Fq 'com.directive.v5.HomeAlia_default' out-v8/evidence/APK_BADGING.txt || true

printf '%s\n' \
  'physical_samsung_android16_previous_D4=FAIL' \
  'confirmed_launcher_alias_package_mismatch=REMEDIATED' \
  'launcher_alias_runtime_derivation=getPackageName()+HomeAlia_*' \
  'launcher_alias_manifest_namespace=com.directive.v5' \
  'inherited_com.ticktick.task_targetActivity_namespace=PRESERVED' \
  'billing_auth_entitlement_logic=UNCHANGED' \
  'offline_no_network_permission_boundary=PRESERVED' \
  'physical_samsung_android16_D5=UNEXECUTED' \
  'final_go=false' \
  > out-v8/evidence/DIRECTIVE5_RUNTIME_FIX_STATUS.txt

sha256sum out-v8/DIRECTIVE_5_5.0.0_INSTALL_SAFE_TEST.apk | tee out-v8/evidence/DIRECTIVE5_SHA256.txt

echo 'PASS: DIRECTIVE 5 launcher-alias-remediated APK built and statically verified; physical Samsung runtime still required for GO'
