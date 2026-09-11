#!/usr/bin/env bash
set -euo pipefail

BASE=support/directive3_install_safe_build.sh
PACKAGE_PATCHER=support/patch_directive_runtime_package_identity.py
LAUNCHER_PATCHER=support/patch_directive_launcher_identity.py
DIAG_PATCHER=support/patch_directive_startup_diagnostics.py
GEN=/tmp/directive5_generated_build.sh

for f in "$BASE" "$PACKAGE_PATCHER" "$LAUNCHER_PATCHER" "$DIAG_PATCHER"; do test -s "$f"; done

python3 - "$BASE" "$GEN" <<'PY'
from pathlib import Path
import sys
src=Path(sys.argv[1]).read_text(encoding='utf-8')
for old,new in (
    ('com.directive.v3','com.directive.v5'),
    ('DIRECTIVE_3','DIRECTIVE_5'),
    ('DIRECTIVE 3','DIRECTIVE 5'),
    ('3.0.0','5.0.0'),
    ('8300','8500'),
): src=src.replace(old,new)
needle='cp "$PROJECT_ROOT/DIRECTIVE_INSTALL_COLLISION_REMEDIATION_REPORT.json" out-v8/evidence/'
insert='''python3 support/patch_directive_runtime_package_identity.py "$PROJECT_ROOT" com.directive.v5 | tee out-v8/evidence/RUNTIME_PACKAGE_IDENTITY_REMEDIATION.txt
cp "$PROJECT_ROOT/DIRECTIVE_RUNTIME_PACKAGE_IDENTITY_REMEDIATION_REPORT.json" out-v8/evidence/
python3 support/patch_directive_launcher_identity.py "$PROJECT_ROOT" | tee out-v8/evidence/LAUNCHER_IDENTITY_REMEDIATION.txt
cp "$PROJECT_ROOT/DIRECTIVE_LAUNCHER_IDENTITY_REMEDIATION_REPORT.json" out-v8/evidence/
python3 support/patch_directive_startup_diagnostics.py "$PROJECT_ROOT" com.directive.v5 | tee out-v8/evidence/STARTUP_DIAGNOSTICS_PATCH.txt
cp "$PROJECT_ROOT/DIRECTIVE_STARTUP_DIAGNOSTICS_REPORT.json" out-v8/evidence/
'''
if src.count(needle)!=1: raise SystemExit('unexpected build insertion point')
src=src.replace(needle,insert+needle,1)
Path(sys.argv[2]).write_text(src,encoding='utf-8')
PY
chmod +x "$GEN"
bash "$GEN"

test -s out-v8/DIRECTIVE_5_5.0.0_INSTALL_SAFE_TEST.apk
grep -Fq '"startup_exception_capture": true' out-v8/evidence/DIRECTIVE_STARTUP_DIAGNOSTICS_REPORT.json
grep -Fq '"runtime_exception_capture": true' out-v8/evidence/DIRECTIVE_STARTUP_DIAGNOSTICS_REPORT.json
grep -Fq '"critical_variant_discriminator_fixed": true' out-v8/evidence/DIRECTIVE_RUNTIME_PACKAGE_IDENTITY_REMEDIATION_REPORT.json

printf '%s\n' \
 'build=PASS' \
 'static_verification=PASS' \
 'package=com.directive.v5' \
 'label=DIRECTIVE 5' \
 'version=5.0.0/8500' \
 'startup_exception_capture=PASS_SOURCE' \
 'runtime_exception_capture=PASS_SOURCE' \
 'diagnostic_ui=PASS_SOURCE' \
 'auth_billing_entitlement_logic=UNCHANGED' \
 'physical_samsung_android16_acceptance=UNEXECUTED' \
 'final_go=false' > out-v8/evidence/DIRECTIVE5_STATUS.txt

sha256sum out-v8/DIRECTIVE_5_5.0.0_INSTALL_SAFE_TEST.apk | tee out-v8/evidence/DIRECTIVE5_SHA256.txt

echo 'PASS: DIRECTIVE 5 diagnostic APK built and statically verified'
