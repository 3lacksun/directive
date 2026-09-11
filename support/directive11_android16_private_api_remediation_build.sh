#!/usr/bin/env bash
set -euo pipefail
BASE=support/directive8_startup_runtime_fix_build.sh
CRASH_PATCHER=support/patch_directive_startup_crash_capture.py
ANDROID16_PATCHER=support/patch_directive_android16_startup_compat.py
GEN=/tmp/directive11_generated_build.sh
for f in "$BASE" "$CRASH_PATCHER" "$ANDROID16_PATCHER"; do test -s "$f"; done

python3 - "$BASE" "$GEN" <<'PY'
from pathlib import Path
import sys
src=Path(sys.argv[1]).read_text(encoding='utf-8')
for old,new in (
 ('com.directive.v8','com.directive.v11'),
 ('DIRECTIVE_8','DIRECTIVE_11'),
 ('DIRECTIVE 8','DIRECTIVE 11'),
 ('8.0.0','11.0.0'),
 ('8800','9100'),
 ('directive8-test.jks','directive11-test.jks'),
 ('directive8test','directive11test'),
 ('DIRECTIVE8_','DIRECTIVE11_'),
): src=src.replace(old,new)
anchor='cp "$PROJECT_ROOT/DIRECTIVE_STARTUP_ICON_PROCESS_EXIT_REMEDIATION_REPORT.json" out-v8/evidence/\n'
if src.count(anchor)!=1: raise SystemExit(f'D11 insertion anchor count={src.count(anchor)}')
addition=(anchor+
'python3 support/patch_directive_android16_startup_compat.py "$PROJECT_ROOT" | tee out-v8/evidence/ANDROID16_STARTUP_COMPAT.txt\n'
'cp "$PROJECT_ROOT/DIRECTIVE_ANDROID16_STARTUP_COMPAT_REPORT.json" out-v8/evidence/\n'
'python3 support/patch_directive_startup_crash_capture.py "$PROJECT_ROOT" 11 | tee out-v8/evidence/STARTUP_CRASH_CAPTURE.txt\n'
'cp "$PROJECT_ROOT/DIRECTIVE_STARTUP_CRASH_CAPTURE_REPORT.json" out-v8/evidence/\n')
src=src.replace(anchor,addition,1)
src=src.replace("'physical_samsung_android16_acceptance=UNEXECUTED'", "'physical_samsung_android16_acceptance=UNEXECUTED_D11;D9=FAIL'")
old_echo="echo 'PASS: DIRECTIVE 11 startup-process-exit remediated APK built and statically verified'"
new_echo=("grep -Fq '\"activitythread_private_hook_disabled_on_api36_plus\": true' out-v8/evidence/DIRECTIVE_ANDROID16_STARTUP_COMPAT_REPORT.json\n"
          "grep -Fq '\"activitythread_abort_process_kill_disabled_on_api36_plus\": true' out-v8/evidence/DIRECTIVE_ANDROID16_STARTUP_COMPAT_REPORT.json\n"
          "grep -Fq '\"legacy_hook_preserved_through_api35\": true' out-v8/evidence/DIRECTIVE_ANDROID16_STARTUP_COMPAT_REPORT.json\n"
          "grep -Fq '\"authentication_licensing_entitlement_logic_changed\": false' out-v8/evidence/DIRECTIVE_ANDROID16_STARTUP_COMPAT_REPORT.json\n"
          "grep -Fq '\"startup_throwable_rethrown\": true' out-v8/evidence/DIRECTIVE_STARTUP_CRASH_CAPTURE_REPORT.json\n"
          "echo 'PASS: DIRECTIVE 11 Android 16 non-SDK startup remediation built and statically verified; FINAL_GO=false'")
if old_echo not in src: raise SystemExit('D11 terminal build message anchor missing')
src=src.replace(old_echo,new_echo,1)
Path(sys.argv[2]).write_text(src,encoding='utf-8')
PY
chmod +x "$GEN"
bash "$GEN"

rm -rf out-v11
mv out-v8 out-v11
APK=out-v11/DIRECTIVE_11_11.0.0_INSTALL_SAFE_TEST.apk
test -s "$APK"
for dex in classes.dex classes2.dex classes3.dex classes4.dex classes5.dex classes6.dex; do unzip -p "$APK" "$dex" 2>/dev/null || true; done | strings > out-v11/evidence/APK_D11_DEX_STRINGS.txt
grep -Fq 'DIRECTIVE_STARTUP_CRASH' out-v11/evidence/APK_D11_DEX_STRINGS.txt
grep -Fq 'DIRECTIVE_11_CRASH_' out-v11/evidence/APK_D11_DEX_STRINGS.txt
! grep -Eq 'android.permission.(INTERNET|ACCESS_NETWORK_STATE|ACCESS_WIFI_STATE|CHANGE_NETWORK_STATE|CHANGE_WIFI_STATE)' out-v11/evidence/APK_PERMISSIONS.txt
grep -Fq "package: name='com.directive.v11' versionCode='9100' versionName='11.0.0'" out-v11/evidence/APK_BADGING.txt
grep -Fq "application-label:'DIRECTIVE 11'" out-v11/evidence/APK_BADGING.txt
grep -Fq '16K_ALIGNMENT=PASS' out-v11/evidence/ELF_16K_ALIGNMENT.txt

# The compatibility patch and exact source-tree checks execute before assembly in the
# generated build.  Recheck the persisted evidence copied from that exact tree here.
grep -Fq '"activitythread_private_hook_disabled_on_api36_plus": true' out-v11/evidence/DIRECTIVE_ANDROID16_STARTUP_COMPAT_REPORT.json
grep -Fq '"activitythread_abort_process_kill_disabled_on_api36_plus": true' out-v11/evidence/DIRECTIVE_ANDROID16_STARTUP_COMPAT_REPORT.json
grep -Fq '"legacy_hook_preserved_through_api35": true' out-v11/evidence/DIRECTIVE_ANDROID16_STARTUP_COMPAT_REPORT.json
grep -Fq '"authentication_licensing_entitlement_logic_changed": false' out-v11/evidence/DIRECTIVE_ANDROID16_STARTUP_COMPAT_REPORT.json

printf '%s\n' \
  'candidate=DIRECTIVE 11' \
  'package=com.directive.v11' \
  'version=11.0.0/9100' \
  'physical_d9_samsung_android16=FAIL' \
  'audit_finding=PRIVATE_ACTIVITYTHREAD_HANDLER_CALLBACK_NON_SDK_HOOK_WITH_PROCESS_KILL' \
  'android16_private_activitythread_hook=DISABLED_API36_PLUS' \
  'android16_deliberate_abort_process_kill=DISABLED_API36_PLUS' \
  'legacy_behavior=PRESERVED_API35_AND_BELOW' \
  'startup_crash_capture=PRESERVED_DIAGNOSTIC' \
  'auth_billing_entitlement_logic=UNCHANGED' \
  'offline_no_network_permission_boundary=PRESERVED' \
  'd11_physical_android16_runtime=UNEXECUTED' \
  'final_go=false' > out-v11/evidence/DIRECTIVE11_RUNTIME_DISPOSITION.txt
sha256sum "$APK" | tee out-v11/evidence/DIRECTIVE11_SHA256_FINAL.txt
