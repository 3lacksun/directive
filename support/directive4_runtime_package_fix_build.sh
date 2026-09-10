#!/usr/bin/env bash
set -euo pipefail

# DIRECTIVE 4 is a side-by-side diagnostic successor. It reuses the DIRECTIVE 3
# install-safe build chain, applies the targeted runtime package-identity repair,
# and restores the approved DIRECTIVE launcher identity before Apktool compilation.
# It does NOT rename inherited com.ticktick.task Java/JNI class namespaces and does
# NOT modify billing, authentication, premium or entitlement logic.

BASE=support/directive3_install_safe_build.sh
PACKAGE_PATCHER=support/patch_directive_runtime_package_identity.py
LAUNCHER_PATCHER=support/patch_directive_launcher_identity.py
GEN=/tmp/directive4_generated_build.sh

test -s "$BASE"
test -s "$PACKAGE_PATCHER"
test -s "$LAUNCHER_PATCHER"

python3 - "$BASE" "$GEN" <<'PY'
from pathlib import Path
import sys
src = Path(sys.argv[1]).read_text(encoding='utf-8')
for old, new in (
    ('com.directive.v3', 'com.directive.v4'),
    ('DIRECTIVE_3', 'DIRECTIVE_4'),
    ('DIRECTIVE 3', 'DIRECTIVE 4'),
    ('3.0.0', '4.0.0'),
    ('8300', '8400'),
):
    src = src.replace(old, new)
needle = 'cp "$PROJECT_ROOT/DIRECTIVE_INSTALL_COLLISION_REMEDIATION_REPORT.json" out-v8/evidence/'
insert = '''python3 support/patch_directive_runtime_package_identity.py "$PROJECT_ROOT" com.directive.v4 | tee out-v8/evidence/RUNTIME_PACKAGE_IDENTITY_REMEDIATION.txt
cp "$PROJECT_ROOT/DIRECTIVE_RUNTIME_PACKAGE_IDENTITY_REMEDIATION_REPORT.json" out-v8/evidence/
python3 support/patch_directive_launcher_identity.py "$PROJECT_ROOT" | tee out-v8/evidence/LAUNCHER_IDENTITY_REMEDIATION.txt
cp "$PROJECT_ROOT/DIRECTIVE_LAUNCHER_IDENTITY_REMEDIATION_REPORT.json" out-v8/evidence/
'''
if src.count(needle) != 1:
    raise SystemExit(f'expected one build-chain insertion point, found {src.count(needle)}')
src = src.replace(needle, insert + needle, 1)
Path(sys.argv[2]).write_text(src, encoding='utf-8')
PY
chmod +x "$GEN"

grep -Fq 'com.directive.v4' "$GEN"
grep -Fq 'DIRECTIVE 4' "$GEN"
grep -Fq '4.0.0' "$GEN"
grep -Fq '8400' "$GEN"
grep -Fq 'patch_directive_runtime_package_identity.py' "$GEN"
grep -Fq 'patch_directive_launcher_identity.py' "$GEN"

bash "$GEN"

test -s out-v8/DIRECTIVE_4_4.0.0_INSTALL_SAFE_TEST.apk

grep -Fq '"critical_variant_discriminator_fixed": true' out-v8/evidence/DIRECTIVE_RUNTIME_PACKAGE_IDENTITY_REMEDIATION_REPORT.json
grep -Fq '"total_replacements": 11' out-v8/evidence/DIRECTIVE_RUNTIME_PACKAGE_IDENTITY_REMEDIATION_REPORT.json
grep -Fq '"inherited_ticktick_launcher_replaced": true' out-v8/evidence/DIRECTIVE_LAUNCHER_IDENTITY_REMEDIATION_REPORT.json

grep -Fq "application-icon-" out-v8/evidence/APK_BADGING.txt
grep -Fq "res/mipmap-anydpi-v26/ic_launcher.xml" out-v8/evidence/APK_BADGING.txt

printf '%s\n' \
  'runtime_package_identity_remediation=PASS' \
  'approved_directive_launcher_identity=PASS_SOURCE_AND_BUILD' \
  'inherited_ticktick_launcher=REPLACED' \
  'critical_Le7_a_m_discriminator=RETARGETED_TO_com.directive.v4' \
  'internal_com.ticktick.task_JNI_namespace=PRESERVED' \
  'billing_auth_entitlement_logic=UNCHANGED' \
  'physical_samsung_android16_acceptance=UNEXECUTED' \
  'final_go=false' \
  > out-v8/evidence/DIRECTIVE4_RUNTIME_FIX_STATUS.txt

sha256sum out-v8/DIRECTIVE_4_4.0.0_INSTALL_SAFE_TEST.apk | tee out-v8/evidence/DIRECTIVE4_SHA256.txt

echo 'PASS: DIRECTIVE 4 package-identity and launcher-remediated APK built and statically verified'
