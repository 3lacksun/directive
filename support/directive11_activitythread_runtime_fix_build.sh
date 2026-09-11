#!/usr/bin/env bash
set -euo pipefail

BASE=support/directive10_android16_receiver_fix_build.sh
HANDLER_PATCHER=support/patch_directive_activitythread_abort.py
GEN=/tmp/directive11_generated_build.sh
for f in "$BASE" "$HANDLER_PATCHER"; do test -s "$f"; done

python3 - "$BASE" "$GEN" <<'PY'
from pathlib import Path
import sys
src = Path(sys.argv[1]).read_text(encoding='utf-8')
for old, new in (
    ('com.directive.v10', 'com.directive.v11'),
    ('DIRECTIVE_10', 'DIRECTIVE_11'),
    ('DIRECTIVE 10', 'DIRECTIVE 11'),
    ('10.0.0', '11.0.0'),
    ('9000', '9100'),
    ('directive10-test.jks', 'directive11-test.jks'),
    ('directive10test', 'directive11test'),
    ('DIRECTIVE10_', 'DIRECTIVE11_'),
    ('out-v10', 'out-v11'),
    ('d10_physical_android16_runtime', 'd11_physical_android16_runtime'),
    ('patch_directive_startup_crash_capture.py "$PROJECT_ROOT" 10', 'patch_directive_startup_crash_capture.py "$PROJECT_ROOT" 11'),
):
    src = src.replace(old, new)

anchor = 'cp "$PROJECT_ROOT/DIRECTIVE_ANDROID14_RECEIVER_FLAGS_REPORT.json" out-v8/evidence/\n'
if src.count(anchor) != 1:
    raise SystemExit(f'D11 ActivityThread insertion anchor count={src.count(anchor)}')
addition = anchor + '''python3 support/patch_directive_activitythread_abort.py "$PROJECT_ROOT" | tee out-v8/evidence/ACTIVITYTHREAD_ABORT_REMEDIATION.txt
cp "$PROJECT_ROOT/DIRECTIVE_ACTIVITYTHREAD_ABORT_REMEDIATION_REPORT.json" out-v8/evidence/
'''
src = src.replace(anchor, addition, 1)
Path(sys.argv[2]).write_text(src, encoding='utf-8')
PY
chmod +x "$GEN"
bash "$GEN"

APK=out-v11/DIRECTIVE_11_11.0.0_INSTALL_SAFE_TEST.apk
test -s "$APK"
grep -Fq '"framework_exception_process_kill_removed": true' out-v11/evidence/DIRECTIVE_ACTIVITYTHREAD_ABORT_REMEDIATION_REPORT.json
grep -Fq '"framework_exception_system_exit_removed": true' out-v11/evidence/DIRECTIVE_ACTIVITYTHREAD_ABORT_REMEDIATION_REPORT.json
grep -Fq '"user_code_rethrow_checks_preserved": true' out-v11/evidence/DIRECTIVE_ACTIVITYTHREAD_ABORT_REMEDIATION_REPORT.json
grep -Fq '"authentication_licensing_premium_entitlement_logic_changed": false' out-v11/evidence/DIRECTIVE_ACTIVITYTHREAD_ABORT_REMEDIATION_REPORT.json
grep -Fq '"offline_network_permission_boundary_changed": false' out-v11/evidence/DIRECTIVE_ACTIVITYTHREAD_ABORT_REMEDIATION_REPORT.json
grep -Fq '"inherited_ticktick_class_namespace_preserved": true' out-v11/evidence/DIRECTIVE_ACTIVITYTHREAD_ABORT_REMEDIATION_REPORT.json
sed -i 's#root_cause_candidate=legacy_unflagged_dynamic_settings_receiver_on_application_onCreate#root_cause_candidates=launch_time_process_exit_and_framework_exception_abort;physical_root_cause_not_yet_runtime_confirmed#' out-v11/evidence/DIRECTIVE11_RUNTIME_DISPOSITION.txt
printf '%s\n' 'activitythread_framework_abort_remediation=PASS_STATIC' >> out-v11/evidence/DIRECTIVE11_RUNTIME_DISPOSITION.txt
sha256sum "$APK" | tee out-v11/evidence/DIRECTIVE11_SHA256_FINAL.txt
echo 'PASS: DIRECTIVE 11 framework-exception process-abort remediation built and statically verified; FINAL_GO=false'
