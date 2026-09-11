#!/usr/bin/env bash
set -euo pipefail
BASE=support/directive8_startup_runtime_fix_build.sh
CRASH_PATCHER=support/patch_directive_startup_crash_capture.py
ANDROID16_PATCHER=support/patch_directive_android16_startup_compat.py
GEN=/tmp/directive10_generated_build.sh
for f in "$BASE" "$CRASH_PATCHER" "$ANDROID16_PATCHER"; do test -s "$f"; done

python3 - "$BASE" "$GEN" <<'PY'
from pathlib import Path
import sys
src=Path(sys.argv[1]).read_text(encoding='utf-8')
# Preserve inherited out-v8 working-directory contract because the D8 generator
# matches those paths inside its base script. Product identity changes only.
for old,new in (
 ('com.directive.v8','com.directive.v10'),
 ('DIRECTIVE_8','DIRECTIVE_10'),
 ('DIRECTIVE 8','DIRECTIVE 10'),
 ('8.0.0','10.0.0'),
 ('8800','9000'),
 ('directive8-test.jks','directive10-test.jks'),
 ('directive8test','directive10test'),
 ('DIRECTIVE8_','DIRECTIVE10_'),
): src=src.replace(old,new)
anchor='cp "$PROJECT_ROOT/DIRECTIVE_STARTUP_ICON_PROCESS_EXIT_REMEDIATION_REPORT.json" out-v8/evidence/\n'
if src.count(anchor)!=1: raise SystemExit(f'Android16 insertion anchor count={src.count(anchor)}')
addition=(anchor+
'python3 support/patch_directive_android16_startup_compat.py "$PROJECT_ROOT" | tee out-v8/evidence/ANDROID16_STARTUP_COMPAT.txt\n'
'cp "$PROJECT_ROOT/DIRECTIVE_ANDROID16_STARTUP_COMPAT_REPORT.json" out-v8/evidence/\n'
'python3 support/patch_directive_startup_crash_capture.py "$PROJECT_ROOT" 10 | tee out-v8/evidence/STARTUP_CRASH_CAPTURE.txt\n'
'cp "$PROJECT_ROOT/DIRECTIVE_STARTUP_CRASH_CAPTURE_REPORT.json" out-v8/evidence/\n')
src=src.replace(anchor,addition,1)
src=src.replace("'physical_samsung_android16_acceptance=UNEXECUTED'", "'physical_samsung_android16_acceptance=UNEXECUTED_D10;D9=FAIL'")
old_echo="echo 'PASS: DIRECTIVE 10 startup-process-exit remediated APK built and statically verified'"
new_echo=("grep -Fq '\"activitythread_private_hook_disabled_on_api36_plus\": true' out-v8/evidence/DIRECTIVE_ANDROID16_STARTUP_COMPAT_REPORT.json\n"
          "grep -Fq '\"activitythread_abort_process_kill_disabled_on_api36_plus\": true' out-v8/evidence/DIRECTIVE_ANDROID16_STARTUP_COMPAT_REPORT.json\n"
          "grep -Fq '\"authentication_licensing_entitlement_logic_changed\": false' out-v8/evidence/DIRECTIVE_ANDROID16_STARTUP_COMPAT_REPORT.json\n"
          "grep -Fq '\"startup_throwable_rethrown\": true' out-v8/evidence/DIRECTIVE_STARTUP_CRASH_CAPTURE_REPORT.json\n"
          "echo 'PASS: DIRECTIVE 10 Android 16 startup compatibility APK built and statically verified; FINAL_GO=false'")
if old_echo not in src: raise SystemExit('D10 terminal build message anchor missing')
src=src.replace(old_echo,new_echo,1)
Path(sys.argv[2]).write_text(src,encoding='utf-8')
PY
chmod +x "$GEN"
bash "$GEN"

rm -rf out-v10
mv out-v8 out-v10
APK=out-v10/DIRECTIVE_10_10.0.0_INSTALL_SAFE_TEST.apk
test -s "$APK"

# Compiled-artifact checks.
for dex in classes.dex classes2.dex classes3.dex classes4.dex classes5.dex classes6.dex; do unzip -p "$APK" "$dex" 2>/dev/null || true; done | strings > out-v10/evidence/APK_D10_DEX_STRINGS.txt
grep -Fq 'DIRECTIVE_STARTUP_CRASH' out-v10/evidence/APK_D10_DEX_STRINGS.txt
grep -Fq 'DIRECTIVE_10_CRASH_' out-v10/evidence/APK_D10_DEX_STRINGS.txt
! grep -Eq 'android.permission.(INTERNET|ACCESS_NETWORK_STATE|ACCESS_WIFI_STATE|CHANGE_NETWORK_STATE|CHANGE_WIFI_STATE)' out-v10/evidence/APK_PERMISSIONS.txt
grep -Fq "package: name='com.directive.v10' versionCode='9000' versionName='10.0.0'" out-v10/evidence/APK_BADGING.txt
grep -Fq "application-label:'DIRECTIVE 10'" out-v10/evidence/APK_BADGING.txt

# Source-level control-flow evidence from the exact tree compiled into the APK.
grep -Fq ':directive_android16_skip_activitythread_hook' "$PROJECT_ROOT/smali_classes2/com/ticktick/task/TickTickApplicationBase.smali"
grep -Fq 'const/16 v1, 0x24' "$PROJECT_ROOT/smali_classes2/com/ticktick/task/TickTickApplicationBase.smali"
grep -Fq ':directive_android16_nonfatal_abort' "$PROJECT_ROOT/smali_classes4/com/ticktick/task/utils/ActivityThreadCallback.smali"

printf '%s\n' \
  'candidate=DIRECTIVE 10' \
  'purpose=ANDROID16_PRIVATE_ACTIVITYTHREAD_HOOK_COMPATIBILITY_REMEDIATION' \
  'physical_d9_samsung_android16=FAIL' \
  'android16_private_activitythread_hook=DISABLED_API36_PLUS' \
  'legacy_activitythread_hook=PRESERVED_API35_AND_BELOW' \
  'auth_billing_entitlement_logic=UNCHANGED' \
  'network_permission_boundary=PRESERVED_OFFLINE' \
  'd10_runtime=UNEXECUTED' \
  'final_go=false' > out-v10/evidence/DIRECTIVE10_RUNTIME_DISPOSITION.txt
sha256sum "$APK" | tee out-v10/evidence/DIRECTIVE10_SHA256_FINAL.txt
