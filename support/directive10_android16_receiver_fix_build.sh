#!/usr/bin/env bash
set -euo pipefail

BASE=support/directive8_startup_runtime_fix_build.sh
CRASH_PATCHER=support/patch_directive_startup_crash_capture.py
RECEIVER_PATCHER=support/patch_directive_android14_receiver_flags.py
GEN=/tmp/directive10_generated_build.sh
for f in "$BASE" "$CRASH_PATCHER" "$RECEIVER_PATCHER"; do test -s "$f"; done

python3 - "$BASE" "$GEN" <<'PY'
from pathlib import Path
import sys
src=Path(sys.argv[1]).read_text(encoding='utf-8')
for old,new in (
 ('com.directive.v8','com.directive.v10'),
 ('DIRECTIVE_8','DIRECTIVE_10'),
 ('DIRECTIVE 8','DIRECTIVE 10'),
 ('8.0.0','10.0.0'),
 ('8800','9000'),
 ('directive8-test.jks','directive10-test.jks'),
 ('directive8test','directive10test'),
 ('DIRECTIVE8_','DIRECTIVE10_'),
):
    src=src.replace(old,new)
anchor='cp "$PROJECT_ROOT/DIRECTIVE_STARTUP_ICON_PROCESS_EXIT_REMEDIATION_REPORT.json" out-v8/evidence/\n'
if src.count(anchor)!=1:
    raise SystemExit(f'D10 source-remediation insertion anchor count={src.count(anchor)}')
addition=anchor+'''python3 support/patch_directive_startup_crash_capture.py "$PROJECT_ROOT" 10 | tee out-v8/evidence/STARTUP_CRASH_CAPTURE.txt
cp "$PROJECT_ROOT/DIRECTIVE_STARTUP_CRASH_CAPTURE_REPORT.json" out-v8/evidence/
python3 support/patch_directive_android14_receiver_flags.py "$PROJECT_ROOT" | tee out-v8/evidence/ANDROID14_RECEIVER_FLAGS_REMEDIATION.txt
cp "$PROJECT_ROOT/DIRECTIVE_ANDROID14_RECEIVER_FLAGS_REPORT.json" out-v8/evidence/
'''
src=src.replace(anchor,addition,1)
src=src.replace("'physical_samsung_android16_acceptance=UNEXECUTED'", "'physical_samsung_android16_acceptance=UNEXECUTED_D10;D8=FAIL'")
old_echo="echo 'PASS: DIRECTIVE 10 startup-process-exit remediated APK built and statically verified'"
new_echo="""grep -Fq '\"startup_throwable_rethrown\": true' out-v8/evidence/DIRECTIVE_STARTUP_CRASH_CAPTURE_REPORT.json
grep -Fq '\"authentication_licensing_entitlement_logic_changed\": false' out-v8/evidence/DIRECTIVE_STARTUP_CRASH_CAPTURE_REPORT.json
grep -Fq '\"legacy_two_arg_startup_registration_removed\": true' out-v8/evidence/DIRECTIVE_ANDROID14_RECEIVER_FLAGS_REPORT.json
grep -Fq '\"receiver_not_exported_flag\": \"0x4\"' out-v8/evidence/DIRECTIVE_ANDROID14_RECEIVER_FLAGS_REPORT.json
grep -Fq '\"authentication_licensing_premium_entitlement_logic_changed\": false' out-v8/evidence/DIRECTIVE_ANDROID14_RECEIVER_FLAGS_REPORT.json
echo 'PASS: DIRECTIVE 10 Android 16 startup receiver remediation built and statically verified; FINAL_GO=false'"""
if old_echo not in src:
    raise SystemExit('D10 terminal build message anchor missing')
src=src.replace(old_echo,new_echo,1)
Path(sys.argv[2]).write_text(src,encoding='utf-8')
PY
chmod +x "$GEN"
bash "$GEN"

rm -rf out-v10
mv out-v8 out-v10
APK=out-v10/DIRECTIVE_10_10.0.0_INSTALL_SAFE_TEST.apk
test -s "$APK"

# Confirm packaged dex contains the diagnostic marker and the compatibility helper contract.
for dex in classes.dex classes2.dex classes3.dex classes4.dex classes5.dex classes6.dex; do
  unzip -p "$APK" "$dex" 2>/dev/null || true
done | strings > out-v10/evidence/APK_D10_DEX_STRINGS.txt
grep -Fq 'DIRECTIVE_STARTUP_CRASH' out-v10/evidence/APK_D10_DEX_STRINGS.txt
grep -Fq 'DIRECTIVE_10_CRASH_' out-v10/evidence/APK_D10_DEX_STRINGS.txt

# Static acceptance gates inherited from D8 plus exact D10 remediation evidence.
grep -Fq "package: name='com.directive.v10' versionCode='9000' versionName='10.0.0'" out-v10/evidence/APK_BADGING.txt
grep -Fq "application-label:'DIRECTIVE 10'" out-v10/evidence/APK_BADGING.txt
! grep -Eq 'android.permission.(INTERNET|ACCESS_NETWORK_STATE|ACCESS_WIFI_STATE|CHANGE_NETWORK_STATE|CHANGE_WIFI_STATE)' out-v10/evidence/APK_PERMISSIONS.txt
grep -Fq '16K_ALIGNMENT=PASS' out-v10/evidence/ELF_16K_ALIGNMENT.txt
grep -Fq '"inherited_ticktick_class_namespace_preserved": true' out-v10/evidence/DIRECTIVE_ANDROID14_RECEIVER_FLAGS_REPORT.json
grep -Fq '"offline_network_permission_boundary_changed": false' out-v10/evidence/DIRECTIVE_ANDROID14_RECEIVER_FLAGS_REPORT.json
grep -Fq '"system_only_global_receiver_registration_changed": false' out-v10/evidence/DIRECTIVE_ANDROID14_RECEIVER_FLAGS_REPORT.json

printf '%s\n' \
  'candidate=DIRECTIVE 10' \
  'package=com.directive.v10' \
  'version=10.0.0/9000' \
  'root_cause_candidate=legacy_unflagged_dynamic_settings_receiver_on_application_onCreate' \
  'android13plus_receiver_flags_remediation=PASS_STATIC' \
  'receiver_visibility=RECEIVER_NOT_EXPORTED' \
  'startup_crash_capture=PRESERVED_DIAGNOSTIC' \
  'inherited_java_jni_namespace=PRESERVED' \
  'offline_no_network_permission_boundary=PRESERVED' \
  'authentication_licensing_premium_entitlement_logic=UNCHANGED' \
  'physical_d8_samsung_android16=FAIL' \
  'd10_physical_android16_runtime=UNEXECUTED' \
  'final_go=false' > out-v10/evidence/DIRECTIVE10_RUNTIME_DISPOSITION.txt
sha256sum "$APK" | tee out-v10/evidence/DIRECTIVE10_SHA256_FINAL.txt
