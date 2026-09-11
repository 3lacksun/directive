#!/usr/bin/env bash
set -euo pipefail

BASE=support/directive11_startup_surface_runtime_capture_build.sh
ACTIVITYTHREAD_PATCHER=support/patch_directive_activitythread_abort.py
GEN=/tmp/directive12_generated_build.sh
for f in "$BASE" "$ACTIVITYTHREAD_PATCHER"; do test -s "$f"; done

python3 - "$BASE" "$GEN" <<'PY'
from pathlib import Path
import sys
src = Path(sys.argv[1]).read_text(encoding='utf-8')

# Retarget the established D11 startup-surface/runtime-capture build to the next
# side-by-side package identity without touching inherited Java/JNI class names.
repls = (
    ("('com.directive.v8','com.directive.v11')", "('com.directive.v8','com.directive.v12')"),
    ("('DIRECTIVE_8','DIRECTIVE_11')", "('DIRECTIVE_8','DIRECTIVE_12')"),
    ("('DIRECTIVE 8','DIRECTIVE 11')", "('DIRECTIVE 8','DIRECTIVE 12')"),
    ("('8.0.0','11.0.0')", "('8.0.0','12.0.0')"),
    ("('8800','9100')", "('8800','9200')"),
    ("('directive8-test.jks','directive11-test.jks')", "('directive8-test.jks','directive12-test.jks')"),
    ("('directive8test','directive11test')", "('directive8test','directive12test')"),
    ("('DIRECTIVE8_','DIRECTIVE11_')", "('DIRECTIVE8_','DIRECTIVE12_')"),
    ('patch_directive_startup_crash_capture.py "$PROJECT_ROOT" 11', 'patch_directive_startup_crash_capture.py "$PROJECT_ROOT" 12'),
    ('rm -rf out-v11', 'rm -rf out-v12'),
    ('mv out-v8 out-v11', 'mv out-v8 out-v12'),
    ('out-v11/DIRECTIVE_11_11.0.0_INSTALL_SAFE_TEST.apk', 'out-v12/DIRECTIVE_12_12.0.0_INSTALL_SAFE_TEST.apk'),
    ("package: name='com.directive.v11' versionCode='9100' versionName='11.0.0'", "package: name='com.directive.v12' versionCode='9200' versionName='12.0.0'"),
    ("application-label:'DIRECTIVE 11'", "application-label:'DIRECTIVE 12'"),
    ('package=com.directive.v11', 'package=com.directive.v12'),
    ('version=11.0.0/9100', 'version=12.0.0/9200'),
    ('candidate=DIRECTIVE 11', 'candidate=DIRECTIVE 12'),
    ('d11_physical_android16_runtime=UNEXECUTED', 'd12_physical_android16_runtime=UNEXECUTED'),
    ('DIRECTIVE11_SHA256_FINAL.txt', 'DIRECTIVE12_SHA256_FINAL.txt'),
    ("PASS: DIRECTIVE 11 built and statically verified; runtime remains UNEXECUTED and FINAL_GO=false", "PASS: DIRECTIVE 12 converged startup/runtime candidate built and statically verified; runtime remains UNEXECUTED and FINAL_GO=false"),
)
for old, new in repls:
    if old not in src:
        raise SystemExit(f'D12 required transformation anchor missing: {old}')
    src = src.replace(old, new)

# Run the already-proven ActivityThread framework-exception remediation after the
# D11 crash-capture instrumentation is installed, so capture remains available but
# the selected framework-only compatibility path no longer deliberately terminates
# the process. This leaves rethrowIfCausedByUser guards intact.
anchor = 'cp "$PROJECT_ROOT/DIRECTIVE11_STARTUP_SURFACE_RUNTIME_CAPTURE_REPORT.json" out-v8/evidence/\n'
if src.count(anchor) != 1:
    raise SystemExit(f'D12 ActivityThread convergence anchor count={src.count(anchor)}')
addition = anchor + '''python3 support/patch_directive_activitythread_abort.py "$PROJECT_ROOT" | tee out-v8/evidence/ACTIVITYTHREAD_ABORT_REMEDIATION.txt
cp "$PROJECT_ROOT/DIRECTIVE_ACTIVITYTHREAD_ABORT_REMEDIATION_REPORT.json" out-v8/evidence/
'''
src = src.replace(anchor, addition, 1)

# Strengthen final gates so the produced APK cannot be accepted merely because the
# pre-remediation capture report says kill/exit existed at instrumentation time.
final_anchor = "grep -Fq '\"pro_entitlement_guard_preserved\": true' out-v12/evidence/DIRECTIVE_STARTUP_ICON_PROCESS_EXIT_REMEDIATION_REPORT.json\n"
if src.count(final_anchor) != 1:
    raise SystemExit('D12 final remediation gate anchor missing')
final_addition = final_anchor + '''grep -Fq '"framework_exception_process_kill_removed": true' out-v12/evidence/DIRECTIVE_ACTIVITYTHREAD_ABORT_REMEDIATION_REPORT.json
grep -Fq '"framework_exception_system_exit_removed": true' out-v12/evidence/DIRECTIVE_ACTIVITYTHREAD_ABORT_REMEDIATION_REPORT.json
grep -Fq '"user_code_rethrow_checks_preserved": true' out-v12/evidence/DIRECTIVE_ACTIVITYTHREAD_ABORT_REMEDIATION_REPORT.json
grep -Fq '"authentication_licensing_premium_entitlement_logic_changed": false' out-v12/evidence/DIRECTIVE_ACTIVITYTHREAD_ABORT_REMEDIATION_REPORT.json
grep -Fq '"offline_network_permission_boundary_changed": false' out-v12/evidence/DIRECTIVE_ACTIVITYTHREAD_ABORT_REMEDIATION_REPORT.json
grep -Fq '"inherited_ticktick_class_namespace_preserved": true' out-v12/evidence/DIRECTIVE_ACTIVITYTHREAD_ABORT_REMEDIATION_REPORT.json
'''
src = src.replace(final_anchor, final_addition, 1)

# Correct the final disposition to describe the assembled candidate, not the
# intermediate capture-instrumentation state.
src = src.replace(
    "'activity_thread_abort_crash_capture=ADDED_BEFORE_EXISTING_KILL' \\",
    "'activity_thread_abort_crash_capture=ADDED' \\\n  'activity_thread_framework_exception_process_abort=REMOVED_STATIC_VERIFIED' \\",
)

Path(sys.argv[2]).write_text(src, encoding='utf-8')
PY
chmod +x "$GEN"
bash "$GEN"

APK=out-v12/DIRECTIVE_12_12.0.0_INSTALL_SAFE_TEST.apk
test -s "$APK"

# Final source/package evidence: no network permission boundary change, 16 KiB
# native alignment, inherited namespace preservation and protected truth unchanged.
grep -Fq "package: name='com.directive.v12' versionCode='9200' versionName='12.0.0'" out-v12/evidence/APK_BADGING.txt
grep -Fq "application-label:'DIRECTIVE 12'" out-v12/evidence/APK_BADGING.txt
! grep -Eq 'android.permission.(INTERNET|ACCESS_NETWORK_STATE|ACCESS_WIFI_STATE|CHANGE_NETWORK_STATE|CHANGE_WIFI_STATE)' out-v12/evidence/APK_PERMISSIONS.txt
grep -Fq '16K_ALIGNMENT=PASS' out-v12/evidence/ELF_16K_ALIGNMENT.txt
grep -Fq '"framework_exception_process_kill_removed": true' out-v12/evidence/DIRECTIVE_ACTIVITYTHREAD_ABORT_REMEDIATION_REPORT.json
grep -Fq '"framework_exception_system_exit_removed": true' out-v12/evidence/DIRECTIVE_ACTIVITYTHREAD_ABORT_REMEDIATION_REPORT.json

sha256sum "$APK" | tee out-v12/evidence/DIRECTIVE12_SHA256_FINAL.txt
echo 'PASS: DIRECTIVE 12 converged source remediation and static package gates complete; Android 16 runtime still required; FINAL_GO=false'
