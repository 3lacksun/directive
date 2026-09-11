#!/usr/bin/env bash
set -euo pipefail

BASE=support/directive11_startup_surface_runtime_capture_build.sh
ACTIVITYTHREAD_PATCHER=support/patch_directive_activitythread_abort.py
HOOK_PATCHER=support/patch_directive_android16_activitythread_hook.py
GEN=/tmp/directive13_generated_build.sh
for f in "$BASE" "$ACTIVITYTHREAD_PATCHER" "$HOOK_PATCHER"; do test -s "$f"; done

python3 - "$BASE" "$GEN" <<'PY'
from pathlib import Path
import sys
src = Path(sys.argv[1]).read_text(encoding='utf-8')

repls = (
    ("('com.directive.v8','com.directive.v11')", "('com.directive.v8','com.directive.v13')"),
    ("('DIRECTIVE_8','DIRECTIVE_11')", "('DIRECTIVE_8','DIRECTIVE_13')"),
    ("('DIRECTIVE 8','DIRECTIVE 11')", "('DIRECTIVE 8','DIRECTIVE 13')"),
    ("('8.0.0','11.0.0')", "('8.0.0','13.0.0')"),
    ("('8800','9100')", "('8800','9300')"),
    ("('directive8-test.jks','directive11-test.jks')", "('directive8-test.jks','directive13-test.jks')"),
    ("('directive8test','directive11test')", "('directive8test','directive13test')"),
    ("('DIRECTIVE8_','DIRECTIVE11_')", "('DIRECTIVE8_','DIRECTIVE13_')"),
    ('patch_directive_startup_crash_capture.py "$PROJECT_ROOT" 11', 'patch_directive_startup_crash_capture.py "$PROJECT_ROOT" 13'),
    ('DIRECTIVE_11_CRASH_', 'DIRECTIVE_13_CRASH_'),
    ('rm -rf out-v11', 'rm -rf out-v13'),
    ('mv out-v8 out-v11', 'mv out-v8 out-v13'),
    ('out-v11/DIRECTIVE_11_11.0.0_INSTALL_SAFE_TEST.apk', 'out-v13/DIRECTIVE_13_13.0.0_INSTALL_SAFE_TEST.apk'),
    ('out-v11/', 'out-v13/'),
    ("package: name='com.directive.v11' versionCode='9100' versionName='11.0.0'", "package: name='com.directive.v13' versionCode='9300' versionName='13.0.0'"),
    ("application-label:'DIRECTIVE 11'", "application-label:'DIRECTIVE 13'"),
    ('package=com.directive.v11', 'package=com.directive.v13'),
    ('version=11.0.0/9100', 'version=13.0.0/9300'),
    ('candidate=DIRECTIVE 11', 'candidate=DIRECTIVE 13'),
    ('d11_physical_android16_runtime=UNEXECUTED', 'd13_physical_android16_runtime=UNEXECUTED'),
    ('DIRECTIVE11_SHA256_FINAL.txt', 'DIRECTIVE13_SHA256_FINAL.txt'),
    ('PASS: DIRECTIVE 11 startup-process-exit remediated APK built and statically verified', 'PASS: DIRECTIVE 13 startup-process-exit remediated APK built and statically verified'),
)
for old, new in repls:
    if old not in src:
        raise SystemExit(f'D13 required transformation anchor missing: {old}')
    src = src.replace(old, new)

# The startup-surface patcher retains its historical D11 evidence filename; that is
# provenance, not release identity. Insert D13 convergence immediately after it.
anchor = 'cp "$PROJECT_ROOT/DIRECTIVE11_STARTUP_SURFACE_RUNTIME_CAPTURE_REPORT.json" out-v8/evidence/\n'
if src.count(anchor) != 1:
    raise SystemExit(f'D13 convergence insertion anchor count={src.count(anchor)}')
addition = anchor + '''python3 support/patch_directive_activitythread_abort.py "$PROJECT_ROOT" | tee out-v8/evidence/ACTIVITYTHREAD_ABORT_REMEDIATION.txt
cp "$PROJECT_ROOT/DIRECTIVE_ACTIVITYTHREAD_ABORT_REMEDIATION_REPORT.json" out-v8/evidence/
python3 support/patch_directive_android16_activitythread_hook.py "$PROJECT_ROOT" | tee out-v8/evidence/ANDROID16_ACTIVITYTHREAD_HOOK_REMEDIATION.txt
cp "$PROJECT_ROOT/DIRECTIVE_ANDROID16_ACTIVITYTHREAD_HOOK_REMEDIATION_REPORT.json" out-v8/evidence/
'''
src = src.replace(anchor, addition, 1)

final_anchor = "grep -Fq '\"pro_entitlement_guard_preserved\": true' out-v13/evidence/DIRECTIVE_STARTUP_ICON_PROCESS_EXIT_REMEDIATION_REPORT.json\n"
if src.count(final_anchor) != 1:
    raise SystemExit('D13 final remediation gate anchor missing')
final_addition = final_anchor + '''grep -Fq '"activity_thread_abort_capture_added": true' out-v13/evidence/DIRECTIVE11_STARTUP_SURFACE_RUNTIME_CAPTURE_REPORT.json
grep -Fq '"global_uncaught_capture_added": true' out-v13/evidence/DIRECTIVE11_STARTUP_SURFACE_RUNTIME_CAPTURE_REPORT.json
grep -Fq '"framework_exception_process_kill_removed": true' out-v13/evidence/DIRECTIVE_ACTIVITYTHREAD_ABORT_REMEDIATION_REPORT.json
grep -Fq '"framework_exception_system_exit_removed": true' out-v13/evidence/DIRECTIVE_ACTIVITYTHREAD_ABORT_REMEDIATION_REPORT.json
grep -Fq '"user_code_rethrow_checks_preserved": true' out-v13/evidence/DIRECTIVE_ACTIVITYTHREAD_ABORT_REMEDIATION_REPORT.json
grep -Fq '"private_activitythread_hook_disabled_on_api36_plus": true' out-v13/evidence/DIRECTIVE_ANDROID16_ACTIVITYTHREAD_HOOK_REMEDIATION_REPORT.json
grep -Fq '"legacy_hook_preserved_through_api35": true' out-v13/evidence/DIRECTIVE_ANDROID16_ACTIVITYTHREAD_HOOK_REMEDIATION_REPORT.json
grep -Fq '"authentication_licensing_premium_entitlement_logic_changed": false' out-v13/evidence/DIRECTIVE_ANDROID16_ACTIVITYTHREAD_HOOK_REMEDIATION_REPORT.json
grep -Fq '"offline_network_permission_boundary_changed": false' out-v13/evidence/DIRECTIVE_ANDROID16_ACTIVITYTHREAD_HOOK_REMEDIATION_REPORT.json
'''
src = src.replace(final_anchor, final_addition, 1)

project_anchor = '''PROJECT_ROOT="$(sed -n 's/^PROJECT_ROOT=//p' out-v13/evidence/PROJECT_ROOT.txt)"
test -n "$PROJECT_ROOT"
'''
if src.count(project_anchor) != 1:
    raise SystemExit(f'D13 post-move PROJECT_ROOT anchor count={src.count(project_anchor)}')
project_rebased = project_anchor + '''case "$PROJECT_ROOT" in
  out-v8/*) PROJECT_ROOT="out-v13/${PROJECT_ROOT#out-v8/}" ;;
  out-v13/*) : ;;
  *) echo "Unexpected PROJECT_ROOT after D13 output move: $PROJECT_ROOT" >&2; exit 1 ;;
esac
test -d "$PROJECT_ROOT"
'''
src = src.replace(project_anchor, project_rebased, 1)

src = src.replace(
    "'activity_thread_abort_crash_capture=ADDED_BEFORE_EXISTING_KILL' \\",
    "'activity_thread_abort_crash_capture=ADDED' \\\n  'activity_thread_framework_exception_process_abort=REMOVED_STATIC_VERIFIED' \\\n  'android16_private_activitythread_hook=DISABLED_API36_PLUS' \\",
)

Path(sys.argv[2]).write_text(src, encoding='utf-8')
PY
chmod +x "$GEN"
bash "$GEN"

APK=out-v13/DIRECTIVE_13_13.0.0_INSTALL_SAFE_TEST.apk
test -s "$APK"

grep -Fq "package: name='com.directive.v13' versionCode='9300' versionName='13.0.0'" out-v13/evidence/APK_BADGING.txt
grep -Fq "application-label:'DIRECTIVE 13'" out-v13/evidence/APK_BADGING.txt
! grep -Eq 'android.permission.(INTERNET|ACCESS_NETWORK_STATE|ACCESS_WIFI_STATE|CHANGE_NETWORK_STATE|CHANGE_WIFI_STATE)' out-v13/evidence/APK_PERMISSIONS.txt
grep -Fq '16K_ALIGNMENT=PASS' out-v13/evidence/ELF_16K_ALIGNMENT.txt
grep -Fq '"framework_exception_process_kill_removed": true' out-v13/evidence/DIRECTIVE_ACTIVITYTHREAD_ABORT_REMEDIATION_REPORT.json
grep -Fq '"framework_exception_system_exit_removed": true' out-v13/evidence/DIRECTIVE_ACTIVITYTHREAD_ABORT_REMEDIATION_REPORT.json
grep -Fq '"private_activitythread_hook_disabled_on_api36_plus": true' out-v13/evidence/DIRECTIVE_ANDROID16_ACTIVITYTHREAD_HOOK_REMEDIATION_REPORT.json
grep -Fq '"legacy_hook_preserved_through_api35": true' out-v13/evidence/DIRECTIVE_ANDROID16_ACTIVITYTHREAD_HOOK_REMEDIATION_REPORT.json

printf '%s\n' \
  'candidate=DIRECTIVE 13' \
  'package=com.directive.v13' \
  'version=13.0.0/9300' \
  'startup_surface=DIRECTIVE_BACKGROUND_WIRED' \
  'application_oncreate_crash_capture=PRESERVED_RETHROW' \
  'activity_thread_framework_exception_process_abort=REMOVED' \
  'android16_private_activitythread_hook=DISABLED_API36_PLUS' \
  'legacy_private_activitythread_hook=PRESERVED_API35_AND_BELOW' \
  'inherited_java_jni_namespace=PRESERVED' \
  'offline_no_network_permission_boundary=PRESERVED' \
  'authentication_licensing_premium_entitlement_logic=UNCHANGED' \
  'physical_d4_samsung_android16=FAIL' \
  'd13_physical_android16_runtime=UNEXECUTED' \
  'final_go=false' > out-v13/evidence/DIRECTIVE13_RUNTIME_DISPOSITION.txt

sha256sum "$APK" | tee out-v13/evidence/DIRECTIVE13_SHA256_FINAL.txt
echo 'PASS: DIRECTIVE 13 converged Android 16 startup remediation and static package gates complete; physical Android 16 runtime still required; FINAL_GO=false'
