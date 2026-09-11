#!/usr/bin/env bash
set -euo pipefail

# DIRECTIVE 5 is a side-by-side PHYSICAL STARTUP DIAGNOSTIC build.
# It keeps the inherited Java/JNI class namespace intact but replaces the launcher
# with a package-owned diagnostic activity and captures startup/lifecycle throwables
# on screen. The kill-suppression changes are diagnostic only, not final-release behaviour.

BASE=support/directive3_install_safe_build.sh
PACKAGE_PATCHER=support/patch_directive_runtime_package_identity.py
LAUNCHER_PATCHER=support/patch_directive_launcher_identity.py
DIAG_PATCHER=support/patch_directive_d5_diagnostic_runtime.py
GEN=/tmp/directive5_generated_build.sh

test -s "$BASE"
test -s "$PACKAGE_PATCHER"
test -s "$LAUNCHER_PATCHER"
test -s "$DIAG_PATCHER"

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
    ('directive3-test.jks', 'directive5-test.jks'),
    ('directive3test', 'directive5test'),
):
    src = src.replace(old, new)
needle = 'cp "$PROJECT_ROOT/DIRECTIVE_INSTALL_COLLISION_REMEDIATION_REPORT.json" out-v8/evidence/'
insert = '''python3 support/patch_directive_runtime_package_identity.py "$PROJECT_ROOT" com.directive.v5 | tee out-v8/evidence/RUNTIME_PACKAGE_IDENTITY_REMEDIATION.txt
cp "$PROJECT_ROOT/DIRECTIVE_RUNTIME_PACKAGE_IDENTITY_REMEDIATION_REPORT.json" out-v8/evidence/
python3 support/patch_directive_launcher_identity.py "$PROJECT_ROOT" | tee out-v8/evidence/LAUNCHER_IDENTITY_REMEDIATION.txt
cp "$PROJECT_ROOT/DIRECTIVE_LAUNCHER_IDENTITY_REMEDIATION_REPORT.json" out-v8/evidence/
python3 support/patch_directive_d5_diagnostic_runtime.py "$PROJECT_ROOT" com.directive.v5 | tee out-v8/evidence/D5_DIAGNOSTIC_INSTRUMENTATION.txt
cp "$PROJECT_ROOT/DIRECTIVE_D5_DIAGNOSTIC_INSTRUMENTATION_REPORT.json" out-v8/evidence/
'''
if src.count(needle) != 1:
    raise SystemExit(f'expected one build-chain insertion point, found {src.count(needle)}')
src = src.replace(needle, insert + needle, 1)
Path(sys.argv[2]).write_text(src, encoding='utf-8')
PY
chmod +x "$GEN"

grep -Fq 'com.directive.v5' "$GEN"
grep -Fq 'DIRECTIVE 5' "$GEN"
grep -Fq '5.0.0' "$GEN"
grep -Fq '8500' "$GEN"
grep -Fq 'patch_directive_d5_diagnostic_runtime.py' "$GEN"

bash "$GEN"

APK=out-v8/DIRECTIVE_5_5.0.0_INSTALL_SAFE_TEST.apk
test -s "$APK"

grep -Fq '"status": "PASS"' out-v8/evidence/DIRECTIVE_D5_DIAGNOSTIC_INSTRUMENTATION_REPORT.json
grep -Fq '"target_package": "com.directive.v5"' out-v8/evidence/DIRECTIVE_D5_DIAGNOSTIC_INSTRUMENTATION_REPORT.json
grep -Fq '"inherited_launcher_aliases_disabled": 26' out-v8/evidence/DIRECTIVE_D5_DIAGNOSTIC_INSTRUMENTATION_REPORT.json
grep -Fq '"activity_thread_abort_kill_suppressed_for_diagnostic_capture": true' out-v8/evidence/DIRECTIVE_D5_DIAGNOSTIC_INSTRUMENTATION_REPORT.json
grep -Fq '"crash_log_handler_kill_suppressed_for_diagnostic_capture": true' out-v8/evidence/DIRECTIVE_D5_DIAGNOSTIC_INSTRUMENTATION_REPORT.json
grep -Fq '"authentication_billing_entitlement_logic_changed": false' out-v8/evidence/DIRECTIVE_D5_DIAGNOSTIC_INSTRUMENTATION_REPORT.json

grep -Fq "package: name='com.directive.v5' versionCode='8500' versionName='5.0.0'" out-v8/evidence/APK_BADGING.txt
grep -Fq "application-label:'DIRECTIVE 5'" out-v8/evidence/APK_BADGING.txt
! grep -Eq 'android.permission.(INTERNET|ACCESS_NETWORK_STATE|ACCESS_WIFI_STATE|CHANGE_NETWORK_STATE|CHANGE_WIFI_STATE)' out-v8/evidence/APK_PERMISSIONS.txt

grep -Fq 'android.permission.READ_CALENDAR' out-v8/evidence/APK_PERMISSIONS.txt
grep -Fq 'android.permission.WRITE_CALENDAR' out-v8/evidence/APK_PERMISSIONS.txt

printf '%s\n' \
  'build=PASS' \
  'static_verification=PASS' \
  'diagnostic_build=true' \
  'package=com.directive.v5' \
  'label=DIRECTIVE 5' \
  'version=5.0.0/8500' \
  'direct_diagnostic_launcher=PASS' \
  'startup_exception_capture=ENABLED' \
  'inherited_launcher_aliases=DISABLED_FOR_DIAGNOSTIC' \
  'process_kill_handlers=SUPPRESSED_FOR_DIAGNOSTIC_ONLY' \
  'auth_billing_entitlement_logic=UNCHANGED' \
  'physical_samsung_android16_acceptance=UNEXECUTED' \
  'final_go=false' \
  > out-v8/evidence/DIRECTIVE5_DIAGNOSTIC_BUILD_STATUS.txt

sha256sum "$APK" | tee out-v8/evidence/DIRECTIVE5_SHA256.txt

echo 'PASS: DIRECTIVE 5 diagnostic startup-capture APK built and statically verified'
