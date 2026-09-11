#!/usr/bin/env bash
set -euo pipefail
BASE=support/directive8_startup_runtime_fix_build.sh
CRASH_PATCHER=support/patch_directive_startup_crash_capture.py
GEN=/tmp/directive9_generated_build.sh
for f in "$BASE" "$CRASH_PATCHER"; do test -s "$f"; done

python3 - "$BASE" "$GEN" <<'PY'
from pathlib import Path
import sys
src=Path(sys.argv[1]).read_text(encoding='utf-8')
# Preserve the inherited out-v8 working-directory contract because the D8 generator
# matches that path inside directive3_install_safe_build.sh. Only product identity changes here.
for old,new in (
 ('com.directive.v8','com.directive.v9'),
 ('DIRECTIVE_8','DIRECTIVE_9'),
 ('DIRECTIVE 8','DIRECTIVE 9'),
 ('8.0.0','9.0.0'),
 ('8800','8900'),
 ('directive8-test.jks','directive9-test.jks'),
 ('directive8test','directive9test'),
 ('DIRECTIVE8_','DIRECTIVE9_'),
): src=src.replace(old,new)
anchor='cp "$PROJECT_ROOT/DIRECTIVE_STARTUP_ICON_PROCESS_EXIT_REMEDIATION_REPORT.json" out-v8/evidence/\n'
if src.count(anchor)!=1: raise SystemExit(f'crash-capture insertion anchor count={src.count(anchor)}')
addition=anchor+'python3 support/patch_directive_startup_crash_capture.py "$PROJECT_ROOT" 9 | tee out-v8/evidence/STARTUP_CRASH_CAPTURE.txt\ncp "$PROJECT_ROOT/DIRECTIVE_STARTUP_CRASH_CAPTURE_REPORT.json" out-v8/evidence/\n'
src=src.replace(anchor,addition,1)
src=src.replace("'physical_samsung_android16_acceptance=UNEXECUTED'", "'physical_samsung_android16_acceptance=UNEXECUTED_D9;D8=FAIL'")
old_echo="echo 'PASS: DIRECTIVE 9 startup-process-exit remediated APK built and statically verified'"
new_echo="grep -Fq '\"startup_throwable_rethrown\": true' out-v8/evidence/DIRECTIVE_STARTUP_CRASH_CAPTURE_REPORT.json\ngrep -Fq '\"authentication_licensing_entitlement_logic_changed\": false' out-v8/evidence/DIRECTIVE_STARTUP_CRASH_CAPTURE_REPORT.json\necho 'PASS: DIRECTIVE 9 diagnostic startup crash-capture APK built and statically verified; FINAL_GO=false'"
if old_echo not in src: raise SystemExit('D9 terminal build message anchor missing')
src=src.replace(old_echo,new_echo,1)
Path(sys.argv[2]).write_text(src,encoding='utf-8')
PY
chmod +x "$GEN"
bash "$GEN"

rm -rf out-v9
mv out-v8 out-v9
APK=out-v9/DIRECTIVE_9_9.0.0_INSTALL_SAFE_TEST.apk
test -s "$APK"
for dex in classes.dex classes2.dex classes3.dex classes4.dex classes5.dex classes6.dex; do unzip -p "$APK" "$dex" 2>/dev/null || true; done | strings > out-v9/evidence/APK_D9_DEX_STRINGS.txt
grep -Fq 'DIRECTIVE_STARTUP_CRASH' out-v9/evidence/APK_D9_DEX_STRINGS.txt
grep -Fq 'DIRECTIVE_9_CRASH_' out-v9/evidence/APK_D9_DEX_STRINGS.txt
! grep -Eq 'android.permission.(INTERNET|ACCESS_NETWORK_STATE|ACCESS_WIFI_STATE|CHANGE_NETWORK_STATE|CHANGE_WIFI_STATE)' out-v9/evidence/APK_PERMISSIONS.txt
printf '%s\n' 'candidate=DIRECTIVE 9' 'purpose=DIAGNOSTIC_STARTUP_EXCEPTION_CAPTURE' 'physical_d8_samsung_android16=FAIL' 'd9_runtime=UNEXECUTED' 'final_go=false' > out-v9/evidence/DIRECTIVE9_RUNTIME_DISPOSITION.txt
sha256sum "$APK" | tee out-v9/evidence/DIRECTIVE9_SHA256_FINAL.txt
